import os
import sys
import spotipy
import pandas as pd
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyClientCredentials


class SpotifyMetadataCollector:
    """
    Lớp chịu trách nhiệm:
    - Khởi tạo kết nối Spotify API
    - Lấy dữ liệu bài hát từ playlist
    - Tìm kiếm bài hát theo từ khóa
    """

    def __init__(self):
        # Khởi tạo Spotify client khi tạo đối tượng
        self.spotify_client = self.initialize_spotify_client()

    def initialize_spotify_client(self):
        """
        Đọc thông tin từ file .env và tạo đối tượng Spotify client
        """

        # Load biến môi trường từ file .env
        load_dotenv()

        client_id = os.getenv("SPOTIPY_CLIENT_ID")
        client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")

        # Kiểm tra nếu thiếu thông tin xác thực
        if client_id is None or client_secret is None:
            print("LỖI: Không tìm thấy SPOTIPY_CLIENT_ID hoặc SPOTIPY_CLIENT_SECRET trong file .env")
            sys.exit(1)

        # Tạo đối tượng xác thực
        auth_manager = SpotifyClientCredentials(
            client_id=client_id,
            client_secret=client_secret
        )

        # Tạo Spotify client
        spotify_instance = spotipy.Spotify(auth_manager=auth_manager)

        print("Kết nối Spotify thành công")
        return spotify_instance

    def extract_tracks_from_playlist(self, playlist_id, max_tracks):
        """
        Lấy danh sách bài hát từ một playlist cụ thể
        """

        collected_tracks = []

        # Lấy 100 bài mỗi lần gọi API
        results = self.spotify_client.playlist_items(
            playlist_id,
            additional_types=["track"],
            limit=100
        )

        # Lặp cho đến khi hết dữ liệu hoặc đạt max_tracks
        while results is not None:

            items = results.get("items", [])

            for item in items:
                track = item.get("track")

                # Bỏ qua nếu track rỗng
                if track is None:
                    continue

                # Chuyển dữ liệu track thành dictionary
                track_data = self.build_track_dictionary(track)
                collected_tracks.append(track_data)

                # Nếu đạt đủ số lượng yêu cầu thì dừng
                if len(collected_tracks) >= max_tracks:
                    print(f"Đã đạt giới hạn {max_tracks} bài từ playlist {playlist_id}")
                    return collected_tracks

            # Nếu còn trang tiếp theo thì lấy tiếp
            if results.get("next"):
                results = self.spotify_client.next(results)
            else:
                break

        return collected_tracks

    def search_tracks_by_query(self, query_text, max_tracks):
        """
        Tìm kiếm bài hát theo từ khóa (ví dụ: 'vpop')
        """

        collected_tracks = []
        offset = 0
        limit_per_request = 50  # Spotify cho phép tối đa 50 mỗi lần

        while len(collected_tracks) < max_tracks:

            results = self.spotify_client.search(
                q=query_text,
                type="track",
                limit=limit_per_request,
                offset=offset
            )

            tracks_block = results.get("tracks", {})
            items = tracks_block.get("items", [])

            # Nếu không còn kết quả thì dừng
            if len(items) == 0:
                break

            for track in items:
                track_data = self.build_track_dictionary(track)
                collected_tracks.append(track_data)

                if len(collected_tracks) >= max_tracks:
                    print(f"Đã đạt giới hạn {max_tracks} bài khi search")
                    return collected_tracks

            # Tăng offset để lấy trang tiếp theo
            offset += limit_per_request

        return collected_tracks

    def build_track_dictionary(self, track):
        """
        Chuyển đối tượng track từ Spotify thành dictionary chuẩn
        """

        artist_names = []

        # Lấy danh sách tên nghệ sĩ
        for artist in track.get("artists", []):
            artist_names.append(artist.get("name"))

        track_dict = {
            "track_id": track.get("id"),
            "title": track.get("name"),
            "artist": ", ".join(artist_names),
            "album": track.get("album", {}).get("name"),
            "popularity": track.get("popularity"),
            "duration_ms": track.get("duration_ms")
        }

        return track_dict


class MetadataPipeline:
    """
    Lớp điều phối toàn bộ quy trình thu thập metadata
    """

    def __init__(self):
        self.collector = SpotifyMetadataCollector()

    def run(self):
        """
        Thực hiện toàn bộ pipeline:
        1. Lấy dữ liệu từ playlist
        2. Search thêm theo từ khóa
        3. Gộp và lưu file CSV
        """

        all_tracks = []

        # Danh sách playlist Việt Nam
        playlist_ids = [
            "37i9dQZF1DX4g8Gs5nUhpp",  # Top 50 Vietnam
            "37i9dQZF1DXe3a8A5X0zL5"   # Viral Vietnam
        ]

        print("Bước 1: Lấy dữ liệu từ playlist")

        for playlist_id in playlist_ids:
            playlist_tracks = self.collector.extract_tracks_from_playlist(
                playlist_id=playlist_id,
                max_tracks=2000
            )

            all_tracks.extend(playlist_tracks)
            print(f"Đã lấy {len(playlist_tracks)} bài từ playlist {playlist_id}")

        print("Bước 2: Tìm kiếm thêm bài Vpop")

        search_tracks = self.collector.search_tracks_by_query(
            query_text="vpop",
            max_tracks=8000
        )

        all_tracks.extend(search_tracks)

        print("Tổng số bài trước khi loại trùng:", len(all_tracks))

        self.save_metadata(all_tracks)

    def save_metadata(self, tracks_list):
        """
        Loại bỏ trùng lặp và lưu thành file CSV
        """

        dataframe = pd.DataFrame(tracks_list)

        before_count = len(dataframe)

        # Loại bỏ trùng theo track_id
        dataframe = dataframe.drop_duplicates(subset=["track_id"])

        after_count = len(dataframe)

        print("Số lượng trước khi loại trùng:", before_count)
        print("Số lượng sau khi loại trùng:", after_count)

        output_directory = "data/raw/metadata"
        os.makedirs(output_directory, exist_ok=True)

        output_path = os.path.join(output_directory, "vpop_10000_raw.csv")

        dataframe.to_csv(output_path, index=False)

        print("Đã lưu metadata tại:", output_path)


if __name__ == "__main__":
    pipeline = MetadataPipeline()
    pipeline.run()