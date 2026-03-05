import yt_dlp
import os
import re
import json
import time

# =============================
# CAU HINH THU MUC & DIEU KIEN
# =============================
LINKS_FILE = "data/raw/metadata/vn_mer_clean_links.txt"
JSON_DIR = "data/raw/json"

MIN_DURATION = 150
MAX_DURATION = 360
MIN_VIEWS = 30000

# =============================
# BO LOC TU KHOA RAC
# =============================
BAD_KEYWORDS = [
    "behind the scenes", "bts", "dance", "choreography", "vlog", "diary", 
    "teaser", "trailer", "reaction", "karaoke", "beat", "instrumental", 
    "making of", "kham pha", "tap tap", "remix", "cover", "live", "mashup", 
    "1 hour", "1 giờ", "loosed", "slowed", "reverb", "fanmade", "parody", 
    "full album", "playlist", "compilation"
]

# =============================
# 100 TU KHOA TIM KIEM TOAN DIEN V-POP
# =============================
QUERIES = [
    # --- Top Hits & Nhạc Trẻ ---
    "ytsearch50:nhạc trẻ việt nam hot nhất 2024", "ytsearch50:top hit vpop", "ytsearch50:nhạc trẻ hay nhất hiện nay",
    "ytsearch50:vpop hot 100", "ytsearch50:nhạc việt nam thịnh hành", "ytsearch50:ca khúc vpop triệu view",
    "ytsearch50:nhạc trẻ gây nghiện", "ytsearch50:bảng xếp hạng nhạc việt", "ytsearch50:nhạc trẻ tiktok hay nhất",
    "ytsearch50:nhạc trẻ mới ra mắt", "ytsearch50:nhạc việt nam nghe nhiều nhất", "ytsearch50:bản hit nhạc trẻ việt",
    "ytsearch50:nhạc pop việt nam", "ytsearch50:ca khúc nhạc trẻ đình đám", "ytsearch50:nhạc trẻ tuyển chọn",
    
    # --- Ballad & Trữ Tình ---
    "ytsearch50:nhạc pop ballad việt nam", "ytsearch50:nhạc ballad việt buồn", "ytsearch50:nhạc thất tình việt nam",
    "ytsearch50:nhạc sầu vpop", "ytsearch50:nhạc khóc việt nam", "ytsearch50:bài hát chia tay vpop",
    "ytsearch50:nhạc tâm trạng việt nam", "ytsearch50:nhạc đêm khuya việt", "ytsearch50:nhạc mưa buồn việt",
    "ytsearch50:nhạc cô đơn vpop", "ytsearch50:ballad việt nam hay nhất", "ytsearch50:nhạc buồn rơi nước mắt",
    "ytsearch50:nhạc lụi tim vpop", "ytsearch50:tình ca buồn việt nam", "ytsearch50:nhạc trữ tình hiện đại",
    
    # --- Indie & Underground ---
    "ytsearch50:nhạc indie việt nam", "ytsearch50:indie việt hay nhất", "ytsearch50:nhạc indie buồn",
    "ytsearch50:indie chill việt nam", "ytsearch50:nghệ sĩ indie việt", "ytsearch50:indie pop việt",
    "ytsearch50:indie rock việt nam", "ytsearch50:nhạc underground việt", "ytsearch50:bài hát indie nổi bật",
    "ytsearch50:indie việt dễ thương", "ytsearch50:nhạc tự sáng tác việt", "ytsearch50:nhạc mộc mạc indie",
    "ytsearch50:indie việt nhẹ nhàng", "ytsearch50:nhạc indie chữa lành", "ytsearch50:top ca khúc indie việt",
    
    # --- Rap & Hip Hop ---
    "ytsearch50:rap việt nam", "ytsearch50:rap việt hot", "ytsearch50:rap việt underground",
    "ytsearch50:rap love việt", "ytsearch50:nhạc rap buồn việt nam", "ytsearch50:hip hop việt nam",
    "ytsearch50:rap việt old school", "ytsearch50:rap việt new school", "ytsearch50:top rap việt",
    "ytsearch50:rap melody việt", "ytsearch50:nhạc rap yêu đời", "ytsearch50:rap thả thính",
    "ytsearch50:nhạc rap chất", "ytsearch50:rap việt thịnh hành", "ytsearch50:rap acoustic việt",
    
    # --- Acoustic & Lofi ---
    "ytsearch50:nhạc lofi chill việt nam", "ytsearch50:nhạc lofi buồn việt", "ytsearch50:lofi cực chill vpop",
    "ytsearch50:nhạc lofi thư giãn", "ytsearch50:nhạc lofi dễ ngủ việt", "ytsearch50:lofi nhẹ nhàng vpop",
    "ytsearch50:lofi thất tình việt", "ytsearch50:lofi acoustic việt", "ytsearch50:lofi ballad việt nam",
    "ytsearch50:nhạc chill việt nam", "ytsearch50:nhạc acoustic việt nam", "ytsearch50:acoustic guitar việt nam",
    "ytsearch50:nhạc mộc việt nam", "ytsearch50:nhạc acoustic nhẹ nhàng", "ytsearch50:acoustic tình ca việt",
    "ytsearch50:acoustic quán cà phê việt", "ytsearch50:bản mộc vpop", "ytsearch50:nhạc thư giãn việt nam",
    
    # --- Động lực & Tích cực ---
    "ytsearch50:nhạc vui nhộn việt nam", "ytsearch50:nhạc yêu đời việt", "ytsearch50:nhạc truyền động lực việt",
    "ytsearch50:nhạc hạnh phúc vpop", "ytsearch50:nhạc mùa hè việt nam", "ytsearch50:nhạc sôi động vpop",
    "ytsearch50:nhạc chill yêu đời", "ytsearch50:bài hát tích cực vpop", "ytsearch50:nhạc vui vẻ buổi sáng",
    "ytsearch50:nhạc đi phượt việt nam", "ytsearch50:nhạc năng lượng việt", "ytsearch50:nhạc tạo động lực",
    
    # --- Nhạc Phim (OST) ---
    "ytsearch50:nhạc phim việt nam", "ytsearch50:ost phim việt", "ytsearch50:nhạc phim điện ảnh việt",
    "ytsearch50:nhạc phim truyền hình việt", "ytsearch50:ca khúc nhạc phim hay", "ytsearch50:nhạc phim hot việt",
    "ytsearch50:nhạc phim cảm động", "ytsearch50:nhạc phim việt xưa", "ytsearch50:nhạc phim học đường việt",
    "ytsearch50:ost việt nam hay nhất",
    
    # --- Làn sóng xanh & 8x 9x ---
    "ytsearch50:nhạc 8x 9x việt nam", "ytsearch50:hit vpop xưa", "ytsearch50:nhạc trẻ thế hệ 8x 9x",
    "ytsearch50:nhạc việt 2010", "ytsearch50:ca khúc vpop huyền thoại", "ytsearch50:bài hát tuổi thơ việt",
    "ytsearch50:nhạc teen pop việt", "ytsearch50:vpop 2000s", "ytsearch50:làn sóng xanh việt nam",
    "ytsearch50:nhạc thế hệ 9x"
]

# =============================
# HAM CHUAN HOA TEN BAI HAT
# =============================
def normalize_title(title):
    title = str(title).lower()
    title = re.sub(r'\(.*?\)|\[.*?\]', '', title)
    title = re.sub(r"\b(official|mv|lyrics?|video|hd|4k|audio)\b", "", title)
    title = re.sub(r'[^a-z0-9àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ\s]', ' ', title)
    return " ".join(title.split())

# =============================
# HAM QUET DU LIEU CU 
# =============================
def load_existing_data():
    existing_ids = set()
    seen_titles = set()
    
    if os.path.exists(LINKS_FILE):
        with open(LINKS_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                if "v=" in line:
                    vid_id = line.strip().split('v=')[-1]
                    existing_ids.add(vid_id)
                    
    if os.path.exists(JSON_DIR):
        for file in os.listdir(JSON_DIR):
            if file.endswith(".info.json"):
                try:
                    with open(os.path.join(JSON_DIR, file), "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if "title" in data:
                            seen_titles.add(normalize_title(data["title"]))
                except Exception:
                    continue
                    
    return existing_ids, seen_titles

# =============================
# HAM KIEM TRA DIEU KIEN (TICH HOP TU CODE CUA BAN)
# =============================
def is_clean(entry):
    title = entry.get("title", "").lower()
    duration = entry.get("duration")
    views = entry.get("view_count") or 0

    if not title: return False

    for bad in BAD_KEYWORDS:
        if bad in title: return False

    # Chặn thời lượng và View theo chuẩn của bạn
    if duration is None or not (MIN_DURATION <= duration <= MAX_DURATION):
        return False
    if views < MIN_VIEWS:
        return False

    return True

# =============================
# MAIN EXECUTOR
# =============================
def main():
    existing_ids, seen_titles = load_existing_data()
    print(f"[*] Da load an toan {len(existing_ids)} ID cu.")
    print(f"[*] Da load {len(seen_titles)} Tieu de cu de chong trung lap.")
    print("-" * 40)

    new_links = []
    
    ydl_opts = {
        'extract_flat': True,
        'quiet': True,
        'no_warnings': True,
        'ignoreerrors': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        for idx, query in enumerate(QUERIES):
            print(f"[{idx+1}/{len(QUERIES)}] Dang quet: {query.replace('ytsearch50:', '')}")
            try:
                info = ydl.extract_info(query, download=False)
                
                if not info or 'entries' not in info: continue
                
                for entry in info['entries']:
                    if not entry or not entry.get('id'): continue
                    
                    vid_id = entry['id']
                    
                    # 1. Check ID da ton tai
                    if vid_id in existing_ids: continue
                    
                    # 2. Check thoi luong, view va tu khoa
                    if not is_clean(entry): continue
                        
                    # 3. Check ten bai hat (Chong Re-up)
                    raw_title = entry.get('title', '')
                    clean_title = normalize_title(raw_title)
                    if len(clean_title) < 3 or clean_title in seen_titles: continue
                        
                    # ĐẠT MỌI ĐIỀU KIỆN
                    new_links.append(f"https://www.youtube.com/watch?v={vid_id}")
                    existing_ids.add(vid_id)
                    seen_titles.add(clean_title)
                        
            except Exception as e:
                continue
            
            time.sleep(1) # Nghi 1s tranh bi Youtube block

    print("-" * 40)
    if new_links:
        # DUNG CHE DO 'a' (APPEND) DE GHI NOI TIEP, BAO VE DU LIEU CU
        with open(LINKS_FILE, 'a', encoding='utf-8') as f:
            for link in new_links:
                f.write(link + '\n')
        print(f"[+] THANH CONG! Vớt thêm được {len(new_links)} BÀI HÁT MỚI TINH.")
        print(f"[*] Tong so link hien tai: {len(existing_ids)}")
    else:
        print("[-] Khong tim them duoc bai moi nao.")

if __name__ == '__main__':
    main()