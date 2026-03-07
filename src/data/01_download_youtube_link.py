import yt_dlp
import os
import re
import time

# =============================
# CAU HINH DATASET MER
# =============================

TARGET = 20000
MIN_DURATION = 150
MAX_DURATION = 360
MIN_VIEWS = 30000

OUTPUT_FILE = "data/raw/metadata/vn_mer_clean_links.txt"
os.makedirs("data/raw/metadata", exist_ok=True)

# =============================
# DANH SACH NGUON HON HOP
# =============================

# 1. Cac mang luoi am nhac lon (Khong bi loi OAC)
CHANNELS = [
    "https://www.youtube.com/@popsmusic/videos",
    "https://www.youtube.com/@VieChannel/videos",
    "https://www.youtube.com/@BHMedia/videos",
    "https://www.youtube.com/@ZingMP3/videos",
    "https://www.youtube.com/@yeah1music/videos",
    "https://www.youtube.com/@SpaceSpeakers/videos",
    "https://www.youtube.com/@ST319Entertainment/videos",
    "https://www.youtube.com/@1989sEntertainment/videos",
    "https://www.youtube.com/@G5RMusic/videos",
    "https://www.youtube.com/@VieONMusic/videos",
    "https://www.youtube.com/@GalaxyStudioOfficial/videos",
    "https://www.youtube.com/@DienQuanMedia/videos",
    "https://www.youtube.com/@POPSWorldwide/videos",
    "https://www.youtube.com/@UniversalMusicVietnam/videos",
    "https://www.youtube.com/@WarnerMusicVietnam/videos",
]

# 2. Tu khoa tim kiem ca si (Giai quyet triet de loi 404 va No Videos Tab)
ARTIST_QUERIES = [
    "Son Tung M-TP official", "Den Vau official", "Hoang Thuy Linh official",
    "MIN official mv", "JustaTee official", "Binz official", "Bich Phuong",
    "Jack J97 official", "ERIK official", "Noo Phuoc Thinh", "My Tam official",
    "Dong Nhi official", "Chi Pu official", "HIEUTHUHAI official", "AMEE official",
    "LyLy official", "Wren Evans", "Tang Duy Tan", "Phan Manh Quynh",
    "Kha official", "Duc Phuc", "Soobin Hoang Son", "Isaac official",
    "Truc Nhan", "Vu Cat Tuong", "Van Mai Huong", "Ho Ngoc Ha",
    "Le Bao Binh", "HKT official", "MCK official", "tlinh official",
    "Obito official", "Rhymastic", "Karik official", 
    "Ngot band", "Chillies band", "Da LAB", "Vu. official",
    "Ca Hoi Hoang", "The Flob", "7UPPERCUTS", "buitruonglinh",
    "Madihu", "Orinn Remix", "Nguyen Hai Phong", "Le Hieu",
    "Phuc Du", "Wxrdie", "Phuc Xp", "GREY D", "Masew",
    "Quang Le official", "Phi Nhung", "Lam Truong", "Le Quyen",
    "Manh Quynh", "Cam Ly", "Dam Vinh Hung", "Duong Hong Loan",
    "Huong Lan", "Truong Vu", "Phuong My Chi", "Vo Ha Tram",
    "Anh Tho", "Hong Nhung", "Thanh Ha"
]

# =============================
# BO LOC RAC
# =============================

BAD_KEYWORDS = [
    "karaoke", "instrumental", "beat",
    "reaction", "trailer", "teaser",
    "concert", "live", "stage",
    "fanmade", "parody", "cover",
    "sped", "slowed", "8d",
    "full album", "playlist",
    "compilation", "remix"
]

def normalize_title(title):
    title = title.lower()
    title = re.sub(r"\(.*?\)", "", title)
    title = re.sub(r"\[.*?\]", "", title) 
    title = re.sub(r"\b(official|mv|lyrics?|video|hd|4k|audio)\b", "", title)
    title = re.sub(r"\d{4}", "", title)
    title = re.sub(r"[^a-z0-9\s]", " ", title)
    title = re.sub(r"\s+", " ", title).strip()
    return title

def is_clean(entry):
    title = entry.get("title", "").lower()
    duration = entry.get("duration")
    views = entry.get("view_count") or 0

    if not title:
        return False

    for bad in BAD_KEYWORDS:
        if bad in title:
            return False

    if duration is None or not (MIN_DURATION <= duration <= MAX_DURATION):
        return False

    if views < MIN_VIEWS:
        return False

    return True

# =============================
# MAIN
# =============================

def main():
    ydl_flat = {
        "quiet": True,
        "no_warnings": True,
        "ignoreerrors": True,
        "extract_flat": True,
        "skip_download": True,
        "playlistend": 1000 # Giam xuong 1000 de chay nhanh hon tren moi nguon
    }

    clean_ids = set()
    title_keys = set()

    print("BAT DAU BUILD DATASET MER SACH (HYBRID MODE)...")

    # Buoc 1: Quet Kenh
    for ch in CHANNELS:
        if len(clean_ids) >= TARGET: break
        print(f"\nDang quet kenh: {ch}")
        
        with yt_dlp.YoutubeDL(ydl_flat) as ydl:
            try:
                info = ydl.extract_info(ch, download=False)
            except Exception as e:
                continue

            if not info or "entries" not in info:
                continue

            for entry in info["entries"]:
                if not entry or not entry.get("id"): continue
                if not is_clean(entry): continue

                vid = entry["id"]
                normalized = normalize_title(entry.get("title", ""))
                if not normalized or normalized in title_keys: continue 

                title_keys.add(normalized)
                clean_ids.add(vid)

                if len(clean_ids) % 100 == 0:
                    print(f"Da loc duoc: {len(clean_ids)} / {TARGET} links")

        time.sleep(1)

    # Buoc 2: Quet tu khoa Ca si (Search)
    print("\nChuyen sang quet tu khoa ca si de bu dap du lieu...")
    for artist in ARTIST_QUERIES:
        if len(clean_ids) >= TARGET: break
        
        # Tim kiem 200 video hang dau cua moi ca si
        search_query = f"ytsearch200:{artist}" 
        print(f"Dang tim kiem: {artist}")

        with yt_dlp.YoutubeDL(ydl_flat) as ydl:
            try:
                info = ydl.extract_info(search_query, download=False)
            except Exception as e:
                continue

            if not info or "entries" not in info:
                continue

            for entry in info["entries"]:
                if not entry or not entry.get("id"): continue
                if not is_clean(entry): continue

                vid = entry["id"]
                normalized = normalize_title(entry.get("title", ""))
                if not normalized or normalized in title_keys: continue 

                title_keys.add(normalized)
                clean_ids.add(vid)

                if len(clean_ids) % 100 == 0:
                    print(f"Da loc duoc: {len(clean_ids)} / {TARGET} links")

        time.sleep(1)

    # Luu link sach
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for vid in clean_ids:
            f.write(f"https://www.youtube.com/watch?v={vid}\n")

    print("\n==============================")
    print("HOAN THANH")
    print(f"Tong bai sach: {len(clean_ids)}")
    print(f"File: {OUTPUT_FILE}")
    print("==============================")

if __name__ == "__main__":
    main()