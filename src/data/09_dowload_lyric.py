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
# CẤU HÌNH ĐƯỜNG DẪN (Khớp với thư mục của Phúc)
# ======================================================
INPUT_CSV = "data/processed/splits_clean/clean_titles_only_2.csv" 
OUTPUT_CSV = "data/processed/splits_clean/final_dataset_with_lyrics_2.csv"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
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

# --- CÁC NGUỒN CÀO DỮ LIỆU ---

def source_loibaihat_biz(query):
    try:
        url = f"https://loibaihat.biz/search.php?q={urllib.parse.quote(query)}"
        res = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        results = soup.find_all('div', class_='song-item')
        if results:
            link = results[0].find('a')['href']
            s_soup = BeautifulSoup(requests.get(link, headers=HEADERS, timeout=10).text, 'html.parser')
            lyric = s_soup.find('div', id='lyric-content')
            if lyric: return lyric.get_text(separator="\n").strip()
    except: pass
    return None

def source_vlyrics_net(query):
    """Nguồn Vlyrics.net - Rất mạnh về nhạc trẻ V-Pop"""
    try:
        url = f"https://vlyrics.net/search?q={urllib.parse.quote(query)}"
        res = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        link_tag = soup.find('a', class_='song-title')
        if link_tag:
            detail_url = "https://vlyrics.net" + link_tag['href'] if not link_tag['href'].startswith('http') else link_tag['href']
            s_soup = BeautifulSoup(requests.get(detail_url, headers=HEADERS, timeout=10).text, 'html.parser')
            lyric_div = s_soup.find('div', class_='lyric-content')
            if lyric_div: return lyric_div.get_text(separator="\n").strip()
    except: pass
    return None

def source_tkaraoke(query):
    """Nguồn Lyric.tkaraoke.com - Kho lời cực kỳ đồ sộ"""
    try:
        url = f"https://lyric.tkaraoke.com/tim-kiem.html?q={urllib.parse.quote(query)}"
        res = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        link_tag = soup.find('a', href=lambda h: h and "/loi-bai-hat/" in h)
        if link_tag:
            detail_url = "https://lyric.tkaraoke.com" + link_tag['href']
            s_soup = BeautifulSoup(requests.get(detail_url, headers=HEADERS, timeout=10).text, 'html.parser')
            lyric_div = s_soup.find('div', class_='lyric_details')
            if lyric_div: return lyric_div.get_text(separator="\n").strip()
    except: pass
    return None

def source_genius(query):
    try:
        url = f"https://genius.com/api/search/multi?q={urllib.parse.quote(query)}"
        res = requests.get(url, headers=HEADERS, timeout=10).json()
        for hit in res['response']['sections'][1]['hits']:
            if hit['type'] == 'song':
                s_url = hit['result']['url']
                s_soup = BeautifulSoup(requests.get(s_url, headers=HEADERS, timeout=10).text, 'html.parser')
                containers = s_soup.select('div[class*="Lyrics__Container"], .lyrics')
                if containers: return "\n".join([c.get_text(separator="\n") for c in containers]).strip()
                break
    except: pass
    return None

def source_loisong_net(query):
    try:
        url = f"https://loisong.net/search?q={urllib.parse.quote(query)}"
        soup = BeautifulSoup(requests.get(url, headers=HEADERS, timeout=10).text, 'html.parser')
        link_tag = soup.find('a', class_='song-link')
        if link_tag:
            s_soup = BeautifulSoup(requests.get(link_tag['href'], headers=HEADERS, timeout=10).text, 'html.parser')
            lyric = s_soup.find('div', class_='lyric-text')
            if lyric: return lyric.get_text(separator="\n").strip()
    except: pass
    return None

def main():
    if not os.path.exists(INPUT_CSV): return
    df = pd.read_csv(INPUT_CSV)
    if 'Lyric' not in df.columns: df['Lyric'] = ""

    print(f"[*] Đang cào đa nguồn cho: {os.path.basename(INPUT_CSV)}")

    # Danh sách các nguồn theo thứ tự ưu tiên
    sources = [source_loibaihat_biz, source_vlyrics_net, source_tkaraoke, source_genius, source_loisong_net]

    for index, row in df.iterrows():
        if pd.notna(row['Lyric']) and len(str(row['Lyric'])) > 100: continue

        title = clean_for_search(row['Clean_Title'])
        uploader = clean_for_search(row['Uploader'])
        
        print(f"[{index+1}] Tìm: {title}...", end=" ", flush=True)
        
        lyric = None
        for src_func in sources:
            # Thử tìm theo Title + Uploader trước
            lyric = src_func(f"{title} {uploader}")
            if not lyric: 
                # Nếu không ra, thử tìm theo Title đơn thuần
                lyric = src_func(title)
            
            if lyric and len(lyric) > 100:
                break

        if lyric:
            # Làm sạch rác (các thẻ [Verse], [Chorus])
            clean_lyric = "\n".join([l for l in lyric.split('\n') if '[' not in l])
            # Dịch sang tiếng Việt
            df.at[index, 'Lyric'] = translate_lyric(clean_lyric)
            print("✅")
        else:
            print("❌")

        if (index + 1) % 5 == 0:
            df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8-sig')
        
        time.sleep(random.uniform(2.0, 4.0))

    df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8-sig')
    print(f"\n[!] HOÀN THÀNH! Dữ liệu tại: {OUTPUT_CSV}")

if __name__ == "__main__":
    main()