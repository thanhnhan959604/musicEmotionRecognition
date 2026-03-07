import pandas as pd
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import time
import os

# ======================================================
# 1. CẤU HÌNH HỆ THỐNG
# ======================================================
CLIENT_ID = "1b8c529fb5784c9abf5c777709f8b6ae"
CLIENT_SECRET = "e9541f97fd25411cafbc7bc6fce66232"

INPUT_PATH = "data/processed/splits_clean/final_dataset_with_lyrics_1.csv"
OUTPUT_PATH = "data/processed/splits_clean/final_dataset_step1_ids.csv"

# Khởi tạo Spotify API
client_credentials_manager = SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

def get_spotify_id(song_name, uploader):
    """Tìm kiếm kết hợp Tên bài + Người đăng để lấy ID chính xác"""
    try:
        # Làm sạch tên người đăng để tăng độ chính xác tìm kiếm
        clean_artist = str(uploader).replace("Official", "").replace("Channel", "").strip()
        query = f"{song_name} {clean_artist}"
        
        # Tìm kiếm trên thị trường VN để ưu tiên nhạc Việt
        results = sp.search(q=query, limit=1, type='track', market='VN')
        items = results['tracks']['items']
        
        if len(items) > 0:
            return items[0]['id']
    except Exception as e:
        print(f" -> Lỗi API: {e}")
    return None

def main():
    # --- 🔄 LOGIC CHẠY TIẾP (RESUME) ---
    if os.path.exists(OUTPUT_PATH):
        print(f"[*] Phát hiện file đang làm dở. Đang nạp tiếp dữ liệu từ: {OUTPUT_PATH}")
        df = pd.read_csv(OUTPUT_PATH)
    elif os.path.exists(INPUT_PATH):
        print(f"[*] Bắt đầu mới từ file gốc: {INPUT_PATH}")
        df = pd.read_csv(INPUT_PATH)
    else:
        print(f"[!] LỖI: Không tìm thấy file dữ liệu nào tại các đường dẫn đã cấu hình!")
        return
    
    # Đảm bảo cột Spotify_ID tồn tại trong DataFrame
    if 'Spotify_ID' not in df.columns:
        df['Spotify_ID'] = ""

    # Lấy danh sách các bài chưa có ID
    remaining_tasks = df[df['Spotify_ID'].isna() | (df['Spotify_ID'] == "")].index
    print(f"[*] Tổng cộng: {len(df)} bài. Cần xử lý tiếp: {len(remaining_tasks)} bài.")

    for i, index in enumerate(remaining_tasks):
        row = df.loc[index]
        
        # Ưu tiên Clean_Title, nếu trống dùng Raw_Title
        song = str(row['Clean_Title']) if pd.notna(row['Clean_Title']) and str(row['Clean_Title']).strip() != "" else str(row['Raw_Title'])
        uploader = str(row['Uploader']) if pd.notna(row['Uploader']) else ""
        
        print(f"[{index+1}/{len(df)}] Đang tra cứu: {song} ({uploader})...", end=" ", flush=True)
        
        spotify_id = get_spotify_id(song, uploader)
        
        if spotify_id:
            df.at[index, 'Spotify_ID'] = spotify_id
            print(f"✅ ID: {spotify_id}")
        else:
            print("❌ (Không tìm thấy)")

        # --- 💾 LƯU DỰ PHÒNG AN TOÀN ---
        # Lưu mỗi 5 bài một lần để tránh mất dữ liệu nếu xảy ra lỗi giữa chừng
        if (i + 1) % 5 == 0:
            try:
                df.to_csv(OUTPUT_PATH, index=False, encoding='utf-8-sig')
            except PermissionError:
                print(f"\n[!] CẢNH BÁO: Không thể lưu file vì file đang bị khóa (có thể bạn đang mở Excel).")
                print(f"[!] HÃY ĐÓNG FILE '{os.path.basename(OUTPUT_PATH)}' NGAY ĐỂ TIẾP TỤC LƯU!")
        
        time.sleep(0.1) # Nghỉ ngắn để tránh bị rate limit

    # --- 🏁 HOÀN TẤT ---
    try:
        df.to_csv(OUTPUT_PATH, index=False, encoding='utf-8-sig')
        print(f"\n[!] CHÚC MỪNG PHÚC! Toàn bộ Spotify ID đã được lưu tại: {OUTPUT_PATH}")
    except PermissionError:
        print(f"\n[!] LỖI NGHIÊM TRỌNG: Không thể lưu file cuối cùng. Hãy đóng Excel và chạy lại script để cập nhật!")

if __name__ == "__main__":
    main()