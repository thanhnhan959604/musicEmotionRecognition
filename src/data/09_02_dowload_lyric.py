import os
import time
import requests
import pandas as pd
from bs4 import BeautifulSoup
import urllib.parse
import random
import re
from deep_translator import GoogleTranslator

# ======================================================
# CẤU HÌNH ĐƯỜNG DẪN 
# ======================================================
INPUT_CSV = "data/processed/splits_clean/clean_titles_only_2.csv" 
OUTPUT_CSV = "data/processed/splits_clean/final_dataset_with_lyrics_2_test.csv"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7'
}

def clean_for_search(text):
    if not text: return ""
    text = re.sub(r'\(.*?\)|\[.*?\]', '', str(text))
    text = re.sub(r'[^\w\s]', '', text)
    return text.strip()

def translate_lyric(text):
    """Tự động nhận diện và dịch sang tiếng Việt nếu cần"""
    try:
        translator = GoogleTranslator(source='auto', target='vi')
        if len(text) > 4500:
            parts = [text[i:i+4500] for i in range(0, len(text), 4500)]
            translated_parts = [translator.translate(p) for p in parts]
            return "".join(translated_parts)
        return translator.translate(text)
    except Exception as e:
        return text

# --- CÁC NGUỒN CÀO DỮ LIỆU MỚI ---

def source_nhaccuatui(query):
    """Nguồn NhacCuaTui (NCT)"""
    try:
        url = f"https://www.nhaccuatui.com/tim-kiem/bai-hat?q={urllib.parse.quote(query)}"
        res = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # Tìm link bài hát đầu tiên trong kết quả tìm kiếm
        link_tag = soup.select_one('.sn_search_returns_frame .name_song')
        
        if link_tag:
            detail_url = link_tag['href']
            s_soup = BeautifulSoup(requests.get(detail_url, headers=HEADERS, timeout=10).text, 'html.parser')
            
            # Lấy nội dung trong thẻ div chứa lyric của NCT
            lyric_div = s_soup.find('div', id='divLyric')
            if lyric_div: 
                # NhacCuaTui thường có dòng "Đóng góp:..." ở cuối, có thể xử lý thêm nếu muốn
                return lyric_div.get_text(separator="\n").strip()
    except Exception as e:
        pass
    return None

def source_lyricvn(query):
    """Nguồn Lyricvn.com"""
    try:
        # Lyricvn sử dụng cơ chế tìm kiếm mặc định của WordPress (?s=...)
        url = f"https://lyricvn.com/?s={urllib.parse.quote(query)}"
        res = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # Tìm bài hát đầu tiên (thường nằm trong thẻ h2 class entry-title hoặc tương tự)
        link_tag = soup.select_one('.entry-title a') or soup.select_one('.post-title a')
        
        if link_tag:
            detail_url = link_tag['href']
            s_soup = BeautifulSoup(requests.get(detail_url, headers=HEADERS, timeout=10).text, 'html.parser')
            
            # Khối nội dung bài viết chứa lyric
            lyric_div = s_soup.select_one('.entry-content')
            if lyric_div: 
                # Xóa bớt các đoạn text không liên quan thường có ở cuối bài (như thẻ tags, related posts...)
                for unwanted in lyric_div.select('div, script, style'):
                    unwanted.decompose()
                return lyric_div.get_text(separator="\n").strip()
    except Exception as e: 
        pass
    return None

def main():
    if not os.path.exists(INPUT_CSV): 
        print(f"[!] Không tìm thấy file: {INPUT_CSV}")
        return
        
    df = pd.read_csv(INPUT_CSV)
    if 'Lyric' not in df.columns: df['Lyric'] = ""

    print(f"[*] Đang cào dữ liệu từ NhacCuaTui & Lyricvn cho: {os.path.basename(INPUT_CSV)}")

    # Chỉ ưu tiên 2 nguồn mới yêu cầu
    sources = [source_nhaccuatui, source_lyricvn]

    for index, row in df.iterrows():
        # Bỏ qua nếu đã có lyric đủ dài
        if pd.notna(row['Lyric']) and len(str(row['Lyric'])) > 100: continue

        title = clean_for_search(row['Clean_Title'])
        uploader = clean_for_search(row['Uploader'])
        
        print(f"[{index+1}] Tìm: {title}...", end=" ", flush=True)
        
        lyric = None
        for src_func in sources:
            # Thử tìm theo Title + Uploader để tăng độ chính xác
            lyric = src_func(f"{title} {uploader}")
            
            # Nếu không có kết quả, thử tìm nới lỏng bằng Title đơn thuần
            if not lyric: 
                lyric = src_func(title)
            
            if lyric and len(lyric) > 100:
                break

        if lyric:
            # Làm sạch rác (các thẻ [Verse], [Chorus]...)
            clean_lyric = "\n".join([l for l in lyric.split('\n') if '[' not in l])
            # Dịch sang tiếng Việt nếu cần
            df.at[index, 'Lyric'] = translate_lyric(clean_lyric)
            print("✅")
        else:
            print("❌")

        # Lưu checkpoint sau mỗi 5 bài
        if (index + 1) % 5 == 0:
            df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8-sig')
        
        # Thêm thời gian nghỉ random để tránh bị block IP
        time.sleep(random.uniform(2.0, 4.0))

    df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8-sig')
    print(f"\n[!] HOÀN THÀNH! Dữ liệu được lưu tại: {OUTPUT_CSV}")

if __name__ == "__main__":
    main()