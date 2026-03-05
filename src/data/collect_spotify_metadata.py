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
# CONFIG (Rút gọn để test)
# =========================
OUTPUT_DIR = "test_outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
TEST_OUTPUT_FILE = os.path.join(OUTPUT_DIR, f"TEST_VPop_{TIMESTAMP}.csv")

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s | %(message)s",
    handlers=[logging.StreamHandler()]
)

# =========================
# MODEL & FILTER (Giữ nguyên logic của bạn)
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

class EmotionFilter:
    @staticmethod
    def calculate_theta(v, e):
        return np.degrees(np.arctan2(e, v))

    @staticmethod
    def is_octant_0_45(v, e, pop):
        # Bạn có thể hạ thấp tiêu chuẩn ở đây nếu muốn test ra nhiều kết quả hơn
        if pop < 10 or v < 0.40: # Nới lỏng để dễ ra kết quả khi test
            return False
        theta = EmotionFilter.calculate_theta(v, e)
        return 0 <= theta < 45

# =========================
# SPOTIFY SERVICE (Tối ưu để chạy nhanh)
# =========================
class SpotifyService:
    def __init__(self, client_id, client_secret):
        self.sp = spotipy.Spotify(
            auth_manager=SpotifyClientCredentials(
                client_id=client_id,
                client_secret=client_secret
            )
        )

    def get_test_tracks(self, keywords, limit_playlists=2):
        track_ids = set()
        for kw in keywords:
            logging.info(f"Đang tìm playlist cho từ khóa: {kw}")
            res = self.sp.search(q=kw, type='playlist', limit=limit_playlists)
            for item in res['playlists']['items']:
                logging.info(f" -> Đang quét playlist: {item['name']}")
                tracks = self.sp.playlist_tracks(item['id'], limit=30) # Chỉ lấy 30 bài mỗi playlist để test
                for t_item in tracks['items']:
                    if t_item['track'] and t_item['track']['id']:
                        track_ids.add(t_item['track']['id'])
        return list(track_ids)

    def process_test_batch(self, track_ids):
        valid_tracks = []
        # Chia nhỏ để gọi API audio_features (tối đa 100)
        batch = track_ids[:100] 
        logging.info(f"Đang xử lý phân tích cho {len(batch)} bài hát...")
        
        tracks_info = self.sp.tracks(batch)
        features = self.sp.audio_features(batch)

        for info, feat in zip(tracks_info["tracks"], features):
            if not info or not feat: continue
            
            v, e, pop = feat.get("valence"), feat.get("energy"), info.get("popularity")
            if v is not None and e is not None:
                if EmotionFilter.is_octant_0_45(v, e, pop):
                    theta = EmotionFilter.calculate_theta(v, e)
                    valid_tracks.append(Track(info["id"], info["name"], info["artists"][0]["name"], v, e, pop, theta))
        
        return valid_tracks

# =========================
# MAIN TEST
# =========================
def main():
    # THAY THẾ KEY CỦA BẠN VÀO ĐÂY
    CLIENT_ID="1a25940b136a4277a11b9c3b681834c1"
    CLIENT_SECRET="0f2a9d084b694313b130443cb6b45c2f"

    if CLIENT_ID == "YOUR_CLIENT_ID":
        logging.error("Vui lòng điền CLIENT_ID và CLIENT_SECRET để test!")
        return

    service = SpotifyService(CLIENT_ID, CLIENT_SECRET)
    
    # 1. Test tìm kiếm
    test_keywords = ["Vpop 2026", "Nhạc trẻ"]
    logging.info("--- BẮT ĐẦU TEST LUỒNG ---")
    
    ids = service.get_test_tracks(test_keywords)
    logging.info(f"Tìm thấy tổng cộng {len(ids)} ID bài hát để lọc.")

    # 2. Test lọc dữ liệu
    results = service.process_test_batch(ids)
    logging.info(f"Kết quả: Tìm được {len(results)} bài phù hợp với góc 0-45 độ.")

    # 3. Xuất file test
    if results:
        df = pd.DataFrame([t.to_dict() for t in results])
        df.to_csv(TEST_OUTPUT_FILE, index=False, encoding="utf-8-sig")
        logging.info(f"Đã lưu kết quả test vào: {TEST_OUTPUT_FILE}")
    else:
        logging.warning("Không có bài nào thỏa mãn điều kiện lọc trong mẫu test.")

if __name__ == "__main__":
    main()