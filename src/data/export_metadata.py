import os
import json
import re
import pandas as pd
from tqdm import tqdm

# =============================
# CAU HINH THU MUC
# =============================
TXT_LIST = "data/filtered/vietnamese_songs.txt"
META_DIR = "data/raw/json"
OUTPUT_DIR = "data/processed"
OUTPUT_CSV = os.path.join(OUTPUT_DIR, "mer_dataset_chuan.csv")
OUTPUT_EXCEL = os.path.join(OUTPUT_DIR, "mer_dataset_chuan.xlsx")

os.makedirs(OUTPUT_DIR, exist_ok=True)

# =============================
# HAM DOC PHU DE (LYRICS) TU FILE VTT
# =============================
def extract_lyrics(video_id):
    # yt-dlp thuong luu phu de tieng Viet duoi dang .vi.vtt
    vtt_path = os.path.join(META_DIR, f"{video_id}.vi.vtt")
    
    if not os.path.exists(vtt_path):
        return "Không có lời bài hát (Sub)"
        
    lyrics = []
    try:
        with open(vtt_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            for line in lines:
                line = line.strip()
                # Bo qua cac dong timestamp hoac header cua file VTT
                if not line or "WEBVTT" in line or "-->" in line or line.startswith("Kind:") or line.startswith("Language:"):
                    continue
                
                # Xoa cac the HTML/Format an ben trong VTT (VD: <c.color>chu</c>)
                clean_line = re.sub(r'<[^>]+>', '', line)
                
                # Tranh viec them 1 cau bi lap lai lien tuc 
                if clean_line and (not lyrics or lyrics[-1] != clean_line):
                    lyrics.append(clean_line)
                    
        return " | ".join(lyrics)
    except Exception:
        return "Lỗi đọc Lyrics"

# =============================
# MAIN EXECUTOR
# =============================
def main():
    if not os.path.exists(TXT_LIST):
        print(f"Khong tim thay file danh sach {TXT_LIST}!")
        return

    # Doc danh sach ID cac bai hat da pass qua bo loc
    with open(TXT_LIST, "r", encoding="utf-8") as f:
        # File dang luu: abc123xyz.mp3 -> Cat lay ID la abc123xyz
        video_ids = [line.strip().replace(".mp3", "") for line in f if line.strip()]

    print(f"[*] Bat dau trich xuat thong tin cho {len(video_ids)} bai hat...")
    
    dataset = []

    for vid in tqdm(video_ids, desc="Dang xu ly Metadata"):
        json_path = os.path.join(META_DIR, f"{vid}.info.json")
        
        # Thiet lap gia tri mac dinh neu thieu file
        title = "Unknown"
        uploader = "Unknown"
        view_count = 0
        duration = 0
        tags = ""
        
        # 1. Doc thong tin tu JSON
        if os.path.exists(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    title = data.get("title", title)
                    uploader = data.get("uploader", uploader)
                    view_count = data.get("view_count", view_count)
                    duration = data.get("duration", duration)
                    # Gom cac the tag lai de de nhan dien the loai
                    tags = ", ".join(data.get("tags", [])) 
            except Exception:
                pass
                
        # 2. Doc Lyric tu VTT
        lyrics = extract_lyrics(vid)
        
        # 3. Gom vao Dataset
        dataset.append({
            "Video_ID": vid,
            "Title": title,
            "Uploader": uploader,
            "Duration_Sec": duration,
            "Views": view_count,
            "Tags": tags,
            "Lyrics": lyrics,
            "Emotion_Label": "" # Cot nay de trong de ban tu gan nhan sau
        })

    # Chuyen doi sang dang Bang (DataFrame)
    df = pd.DataFrame(dataset)
    
    # Sap xep theo View giam dan (De uu tien gan nhan nhung bai noi tieng truoc)
    df = df.sort_values(by="Views", ascending=False)

    # Xuat ra CSV va Excel
    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
    try:
        df.to_excel(OUTPUT_EXCEL, index=False)
    except Exception:
        print("[!] Can cai dat them thu vien 'openpyxl' de xuat file Excel (.xlsx). Da xuat duoc file .csv")

    print("\n" + "=" * 40)
    print("HOAN THANH RUT TRICH DU LIEU!")
    print(f"So dong du lieu: {len(df)}")
    print(f"File CSV: {OUTPUT_CSV}")
    print(f"File Excel: {OUTPUT_EXCEL}")
    print("Ban co the mo file de bat dau qua trinh Gan Nhan Cam Xuc!")
    print("=" * 40)

if __name__ == "__main__":
    main()