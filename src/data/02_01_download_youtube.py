import yt_dlp
import os
import concurrent.futures

# =============================
# CAU HINH GIAI DOAN 2 (FULL)
# =============================
INPUT_FILE = "data/raw/metadata/vn_mer_clean_links.txt"
OUTPUT_AUDIO_DIR = "data/raw/audio"
OUTPUT_META_DIR = "data/raw/json"
MAX_WORKERS = 5 

os.makedirs(OUTPUT_AUDIO_DIR, exist_ok=True)
os.makedirs(OUTPUT_META_DIR, exist_ok=True)

# =============================
# HAM TAI FULL AUDIO & LYRIC
# =============================
def download_full_data(url):
    if not url: return

    video_id = url.split("v=")[-1].strip()
    output_mp3 = os.path.join(OUTPUT_AUDIO_DIR, f"{video_id}.mp3")
    output_json = os.path.join(OUTPUT_META_DIR, f"{video_id}.info.json")

    # Resume: Kiem tra neu da tai roi thi bo qua
    if os.path.exists(output_mp3) and os.path.exists(output_json):
        print(f"Da co san, bo qua: {video_id}")
        return

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': {
            'default': os.path.join(OUTPUT_AUDIO_DIR, f"{video_id}.%(ext)s"),
            'infojson': os.path.join(OUTPUT_META_DIR, f"{video_id}.%(ext)s"),
            'subtitle': os.path.join(OUTPUT_META_DIR, f"{video_id}.%(ext)s")
        },
        'postprocessors': [
            {
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            },
            {
                'key': 'FFmpegMetadata',
                'add_metadata': True,
            }
        ],
        
        # Bat tinh nang tai Subtitles (Lyric)
        'writesubtitles': True,
        'subtitleslangs': ['vi'], 
        'writeautomaticsub': False, 
        
        # Bat tinh nang tai Metadata
        'writeinfojson': True,
        
        'quiet': True,
        'no_warnings': True,
        'ignoreerrors': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        print(f"Tai thanh cong Audio va Metadata: {video_id}")
    except Exception as e:
        print(f"Loi tai {video_id}: {e}")

# =============================
# MAIN
# =============================
def main():
    if not os.path.exists(INPUT_FILE):
        print(f"Khong tim thay file {INPUT_FILE}")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip()]

    print(f"BAT DAU TAI FULL {len(urls)} BAI HAT VA LYRIC...")
    print(f"Thu muc Audio: {OUTPUT_AUDIO_DIR}")
    print(f"Thu muc JSON/VTT: {OUTPUT_META_DIR}")
    print("-" * 40)

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        executor.map(download_full_data, urls)

    print("-" * 40)
    print("HOAN THANH TAI DU LIEU THO!")

if __name__ == "__main__":
    main()