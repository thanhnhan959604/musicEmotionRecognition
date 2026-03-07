import pandas as pd
import requests
import time
import os

# ======================================================
# 1. CẤU HÌNH API & ĐƯỜNG DẪN
# ======================================================
# Sử dụng Key mới bạn vừa cung cấp
RAPID_API_KEY = "f04e83b22cmsh1719d93642ad22bp164371jsnf9de5448c609"
RAPID_API_HOST = "spotify-extended-audio-features-api.p.rapidapi.com"
# Đây chính là endpoint "Several Tracks" khi kết hợp với tham số 'ids'
URL = f"https://{RAPID_API_HOST}/v1/audio-features"

INPUT_PATH = "data/processed/splits_clean/final_dataset_step1_ids.csv"
OUTPUT_PATH = "data/processed/splits_clean/final_dataset_step2_features.csv"

def get_several_audio_features(ids_list):
    """Gọi endpoint 'Several Tracks' với tối đa 5 ID"""
    # Ghép các ID thành chuỗi cách nhau bằng dấu phẩy
    ids_query = ",".join(ids_list)
    querystring = {"ids": ids_query}
    
    headers = {
        "x-rapidapi-key": RAPID_API_KEY,
        "x-rapidapi-host": RAPID_API_HOST
    }
    
    try:
        response = requests.get(URL, headers=headers, params=querystring, timeout=15)
        if response.status_code == 200:
            # API trả về danh sách các object audio_features
            data = response.json()
            return data.get('audio_features', [])
        else:
            print(f"\n❌ Lỗi API (Mã {response.status_code}): {response.text}")
    except Exception as e:
        print(f"\n❌ Lỗi kết nối: {e}")
    return None

def main():
    # Kiểm tra file đầu vào từ Bước 1
    if not os.path.exists(INPUT_PATH):
        print(f"[!] Không tìm thấy file Spotify ID tại: {INPUT_PATH}")
        return

    # Nạp dữ liệu (ưu tiên nạp file đang làm dở nếu có)
    current_file = OUTPUT_PATH if os.path.exists(OUTPUT_PATH) else INPUT_PATH
    df = pd.read_csv(current_file)
    
    # Khởi tạo các cột cảm xúc MER nếu chưa có
    cols = ['valence', 'energy', 'danceability', 'tempo', 'acousticness']
    for col in cols:
        if col not in df.columns: df[col] = None

    # Lọc ra những bài có ID nhưng chưa có dữ liệu Valence
    pending_idx = df[df['Spotify_ID'].notna() & df['valence'].isna()].index.tolist()

    if not pending_idx:
        print("[*] Chúc mừng! Dữ liệu đã đầy đủ 100%.")
        return

    print(f"[*] Đang dùng 'Several Tracks' API để lấy dữ liệu cho {len(pending_idx)} bài...")

    # Chia cụm 5 bài (Giới hạn 'max 5' của serveral endpoint này)
    batch_size = 5
    for i in range(0, len(pending_idx), batch_size):
        current_batch_indices = pending_idx[i : i + batch_size]
        current_ids = df.loc[current_batch_indices, 'Spotify_ID'].tolist()
        
        print(f"[*] Cụm {i//batch_size + 1}: Lấy {len(current_ids)} bài...", end=" ", flush=True)
        
        results = get_several_audio_features(current_ids)
        
        if results:
            for feat in results:
                if feat and 'id' in feat:
                    # Khớp ID trả về với dòng trong DataFrame
                    idx = df[df['Spotify_ID'] == feat['id']].index
                    if not idx.empty:
                        for col in cols:
                            df.at[idx[0], col] = feat.get(col)
            print("✅")
        else:
            print("❌")

        # Lưu dự phòng định kỳ
        if (i//batch_size + 1) % 5 == 0:
            try:
                df.to_csv(OUTPUT_PATH, index=False, encoding='utf-8-sig')
            except PermissionError:
                print(f"\n[!] CẢNH BÁO: Đóng file Excel để máy lưu dữ liệu!")

        time.sleep(0.5) # Nghỉ ngắn để ổn định băng thông

    # Lưu kết quả cuối cùng
    df.to_csv(OUTPUT_PATH, index=False, encoding='utf-8-sig')
    print(f"\n[!] HOÀN THÀNH! Bộ Dataset MER đã sẵn sàng tại: {OUTPUT_PATH}")

if __name__ == "__main__":
    main()