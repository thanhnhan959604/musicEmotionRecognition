import pandas as pd
import os
import time
import sys
import requests
import random
from dotenv import load_dotenv

# =============================
# CẤU HÌNH API OPENROUTER
# =============================
load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if not OPENROUTER_API_KEY:
    print("[!] LỖI: Thiếu biến OPENROUTER_API_KEY trong file .env!")
    sys.exit(1)

INPUT_CSV = r"D:\Python\Do An HKII\musicEmotionRecognition\data\processed\splits\audio_metadata_part_6.csv"
OUTPUT_CSV = "data/processed/splits_clean/clean_titles_only_6.csv"

# =============================
# HÀM GỌI OPENROUTER AI ĐỂ DỌN RÁC TIÊU ĐỀ
# =============================
def get_clean_title_only(raw_title, max_retries=3):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "https://localhost", 
        "X-Title": "Music Emotion Scraper", 
        "Content-Type": "application/json"
    }
    
    prompt = f"""
    Nhiệm vụ của bạn là trích xuất ĐÚNG và CHỈ MỖI tên bài hát từ tiêu đề YouTube rác sau.
    Tuyệt đối KHÔNG bao gồm tên ca sĩ, các từ như "Official", "MV", "Lyrics", "Cover", "Nhạc chế", hoặc văn bản trong ngoặc.
    Chỉ in ra đúng 1 dòng là tên bài hát, không giải thích gì thêm, không có dấu ngoặc kép.
    Ví dụ: "[Nhạc chế 16+] - NHỮNG CHỊ ĐẠI HỌC ĐƯỜNG - Hậu Hoàng" -> "Những Chị Đại Học Đường"
    
    Tiêu đề cần xử lý: "{raw_title}"
    """
    
    data = {
        "model": "openrouter/free", # Tự động chọn AI miễn phí khả dụng
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1 
    }

    for attempt in range(max_retries):
        try:
            res = requests.post(url, headers=headers, json=data, timeout=15)
            res.raise_for_status()
            
            clean_text = res.json()["choices"][0]["message"]["content"].strip()
            # Dọn dẹp các dấu nháy kép thừa nếu AI lỡ tay thêm vào
            clean_text = clean_text.replace('"', '').replace("'", "").split('\n')[0].strip()
            
            return clean_text
            
        except requests.exceptions.HTTPError as e:
            if "429" in str(e):
                print(f"[Quá tải OpenRouter, đợi 5s...] ", end="")
                time.sleep(5) 
            else:
                print(f"[Lỗi API: {e}] ", end="")
                return ""
        except Exception as e:
            print(f"[Lỗi mạng: {e}] ", end="")
            time.sleep(2)
            
    return ""

# =============================
# MAIN EXECUTOR
# =============================
def main():
    if not os.path.exists(INPUT_CSV):
        print(f"Không tìm thấy file {INPUT_CSV}")
        return

    df = pd.read_csv(INPUT_CSV)
    
    # Cơ chế Checkpoint
    if os.path.exists(OUTPUT_CSV):
        df_saved = pd.read_csv(OUTPUT_CSV)
        saved_ids = set(df_saved['Video_ID'].tolist())
        print(f"[*] Phát hiện file cũ! Đã dọn rác được {len(saved_ids)} bài trước đó.")
    else:
        saved_ids = set()
        pd.DataFrame(columns=['Video_ID', 'Raw_Title', 'Clean_Title', 'Uploader']).to_csv(OUTPUT_CSV, index=False, encoding='utf-8-sig')

    print(f"[*] Bắt đầu gọi Llama 3.1 dọn rác tiêu đề cho {len(df) - len(saved_ids)} bài hát...")

    batch_data = []
    save_interval = 20 
    
    for index, row in df.iterrows():
        vid = row['Video_ID']
        raw_title = row['Title']
        
        if vid in saved_ids:
            continue
            
        print(f"\n[{index+1}] Gốc: {raw_title}")
        print(" -> Đang cắt... ", end="")
        
        clean_title = get_clean_title_only(raw_title)
        
        if not clean_title or len(clean_title) < 2:
            print("LỖI/BỎ QUA!")
        else:
            print(f"Thành phẩm: '{clean_title}'")
            
        batch_data.append({
            'Video_ID': vid,
            'Raw_Title': raw_title,
            'Clean_Title': clean_title, 
            'Uploader': row['Uploader']
        })
        saved_ids.add(vid)
        
        # Lưu định kỳ
        if len(batch_data) >= save_interval:
            temp_df = pd.DataFrame(batch_data)
            temp_df.to_csv(OUTPUT_CSV, mode='a', header=False, index=False, encoding='utf-8-sig')
            batch_data = [] 
        
        # Ngủ ngắn để tránh lỗi 429 từ OpenRouter
        time.sleep(random.uniform(1.0, 2.0))

    if batch_data:
        pd.DataFrame(batch_data).to_csv(OUTPUT_CSV, mode='a', header=False, index=False, encoding='utf-8-sig')
        
    print("\n" + "=" * 40)
    print("HOÀN THÀNH QUÁ TRÌNH LÀM SẠCH TIÊU ĐỀ!")
    print(f"Kết quả lưu tại: {OUTPUT_CSV}")
    print("=" * 40)

if __name__ == "__main__":
    main()