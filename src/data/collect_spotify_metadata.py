import spotipy
import pandas as pd
import numpy as np
import time
import os
import logging
from datetime import datetime
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy.exceptions import SpotifyException


# =========================
# CONFIG
# =========================
OUTPUT_DIR = "data/raw/outputs"
CHECKPOINT_DIR = "data/raw/checkpoints"
LOG_DIR = "logs"

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(CHECKPOINT_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
CHECKPOINT_FILE = os.path.join(CHECKPOINT_DIR, "vpop_checkpoint.csv")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, f"VPop_Octant_0_45_{TIMESTAMP}.csv")


# =========================
# LOGGING
# =========================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, f"crawl_{TIMESTAMP}.log")),
        logging.StreamHandler()
    ]
)


# =========================
# MODEL
# =========================
class Track:
    def __init__(self, track_id, name, artist, valence, energy, popularity, theta):
        self.track_id = track_id
        self.name = name
        self.artist = artist
        self.valence = valence
        self.energy = energy
        self.popularity = popularity
        self.theta = theta

    def to_dict(self):
        return {
            "id": self.track_id,
            "name": self.name,
            "artist": self.artist,
            "valence": self.valence,
            "energy": self.energy,
            "theta": round(self.theta, 2),
            "popularity": self.popularity
        }


# =========================
# EMOTION FILTER
# =========================
class EmotionFilter:
    @staticmethod
    def calculate_theta(v, e):
        return np.degrees(np.arctan2(e, v))

    @staticmethod
    def is_octant_0_45(v, e, pop):
        if pop < 45 or v < 0.60 or e < 0.35:
            return False
        if e >= v:
            return False

        theta = EmotionFilter.calculate_theta(v, e)
        return 0 <= theta < 45


# =========================
# SPOTIFY SERVICE
# =========================
class SpotifyService:

    def __init__(self, client_id, client_secret):
        self.sp = spotipy.Spotify(
            auth_manager=SpotifyClientCredentials(
                client_id=client_id,
                client_secret=client_secret
            ),
            retries=5
        )

    # ---- SAFE CALL ----
    def safe_call(self, func, *args, **kwargs):
        max_retry = 5
        for attempt in range(max_retry):
            try:
                return func(*args, **kwargs)
            except SpotifyException as e:
                if e.http_status == 429:
                    retry_after = int(e.headers.get("Retry-After", 5))
                    logging.warning(f"Rate limit. Sleeping {retry_after}s...")
                    time.sleep(retry_after)
                else:
                    logging.error(f"Spotify API error: {e}")
                    return None
            except Exception as e:
                logging.error(f"Network error: {e}")
                time.sleep(3)

        logging.error("Max retry exceeded.")
        return None

    # ---- SEARCH PLAYLISTS ----
    def search_playlists_by_keywords(self, keywords, limit_per_keyword=20):
        playlist_ids = set()

        for kw in keywords:
            logging.info(f"Searching playlists: '{kw}'")
            results = self.safe_call(self.sp.search, q=kw, type='playlist', limit=limit_per_keyword)

            if results and results.get('playlists'):
                for item in results['playlists']['items']:
                    if item and item.get('id'):
                        playlist_ids.add(item['id'])

        logging.info(f"Found {len(playlist_ids)} playlists from search.")
        return list(playlist_ids)

    # ---- GET TRACK IDS ----
    def get_track_ids_from_playlists(self, playlist_ids):
        unique_ids = set()

        for pid in playlist_ids:
            logging.info(f"Scanning playlist {pid}")

            results = self.safe_call(
                self.sp.playlist_tracks,
                pid,
                fields="items(track(id)),next",
                limit=100
            )

            while results:
                for item in results.get('items', []):
                    track = item.get('track')
                    if track and track.get('id'):
                        unique_ids.add(track['id'])

                results = self.safe_call(self.sp.next, results) if results.get('next') else None

        logging.info(f"Collected {len(unique_ids)} unique track IDs.")
        return list(unique_ids)

    # ---- PROCESS BATCHES ----
    def process_batches(self, track_ids):

        batch_size = 50
        save_every_n_batches = 3   # Giảm IO
        sleep_between_batches = 0.15  #  Giảm áp lực API

        valid_tracks = []
        processed_ids = set()

        # Resume checkpoint
        if os.path.exists(CHECKPOINT_FILE):
            try:
                df_cp = pd.read_csv(CHECKPOINT_FILE)
                processed_ids = set(df_cp["id"])
                valid_tracks = [
                    Track(r["id"], r["name"], r["artist"],
                          r["valence"], r["energy"],
                          r["popularity"], r["theta"])
                    for _, r in df_cp.iterrows()
                ]
                logging.info(f"Resumed {len(valid_tracks)} tracks from checkpoint.")
            except Exception:
                logging.warning("Checkpoint corrupted. Starting fresh.")

        remaining = [tid for tid in track_ids if tid not in processed_ids]

        total_batches = (len(remaining) + batch_size - 1) // batch_size

        for batch_index in range(total_batches):

            start = batch_index * batch_size
            end = start + batch_size
            batch = remaining[start:end]

            logging.info(f"Processing batch {batch_index + 1}/{total_batches}")

            tracks_info = self.safe_call(self.sp.tracks, batch)
            features = self.safe_call(self.sp.audio_features, batch)

            if not tracks_info or "tracks" not in tracks_info or not features:
                continue

            for info, feat in zip(tracks_info["tracks"], features):
                if not info or not feat:
                    continue

                v = feat.get("valence")
                e = feat.get("energy")
                pop = info.get("popularity")

                if v is None or e is None or pop is None:
                    continue

                if EmotionFilter.is_octant_0_45(v, e, pop):
                    theta = EmotionFilter.calculate_theta(v, e)
                    valid_tracks.append(
                        Track(
                            info["id"],
                            info["name"],
                            info["artists"][0]["name"],
                            v, e, pop, theta
                        )
                    )

            # Save checkpoint mỗi N batch
            if batch_index % save_every_n_batches == 0:
                self.atomic_save(valid_tracks, CHECKPOINT_FILE)

            time.sleep(sleep_between_batches)

        # Save cuối cùng
        self.atomic_save(valid_tracks, CHECKPOINT_FILE)

        return valid_tracks

    # ---- ATOMIC SAVE ----
    def atomic_save(self, tracks, filepath):
        temp_file = filepath + ".tmp"
        pd.DataFrame([t.to_dict() for t in tracks]).to_csv(
            temp_file, index=False, encoding="utf-8-sig"
        )
        os.replace(temp_file, filepath)


# =========================
# MAIN
# =========================
def main():

    CLIENT_ID = "YOUR_CLIENT_ID"
    CLIENT_SECRET = "YOUR_CLIENT_SECRET"

    service = SpotifyService(CLIENT_ID, CLIENT_SECRET)

    seed_playlists = [
        "37i9dQZEVXbLdGSmz6xilI",
        "37i9dQZEVXbMGc3ZQ0UO0P",
        "37i9dQZF1DX4g9pRU3I870"
    ]

    keywords = ["Vpop hot", "Nhạc trẻ 2026", "V-Pop Chill", "Nhạc Việt gây nghiện", "V-Pop 2025"]

    logging.info("Step 1: Expanding playlist pool...")
    searched_playlists = service.search_playlists_by_keywords(keywords, limit_per_keyword=15)

    final_playlist_pool = list(set(seed_playlists + searched_playlists))
    logging.info(f"Total playlists to scan: {len(final_playlist_pool)}")

    logging.info("Step 2: Collecting track IDs...")
    track_ids = service.get_track_ids_from_playlists(final_playlist_pool)

    logging.info("Step 3: Processing and filtering tracks...")
    dataset = service.process_batches(track_ids)

    dataset.sort(key=lambda x: x.popularity, reverse=True)
    final_df = pd.DataFrame([t.to_dict() for t in dataset[:1000]])

    final_df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")

    logging.info("Crawl completed.")
    logging.info(f"Total valid tracks found: {len(dataset)}")
    logging.info(f"Saved top {len(final_df)} tracks to {OUTPUT_FILE}")

    if os.path.exists(CHECKPOINT_FILE):
        os.remove(CHECKPOINT_FILE)
        logging.info("Checkpoint file removed.")


if __name__ == "__main__":
    main()