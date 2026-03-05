import pandas as pd
import re

# =============================
# CAU HINH FILE
# =============================
INPUT_CSV = "data/processed/mer_dataset_chuan.csv"
OUTPUT_GENIUS_LIST = "data/processed/need_genius_lyrics.csv"

def count_words(text):
    if pd.isna(text):
        return 0
    # Xoa cac dau cau de dem tu chinh xac
    clean_text = re.sub(r'[^\w\s]', '', str(text))
    return len(clean_text.split())

def is_noisy_lyric(lyric):
    if pd.isna(lyric):
        return True
    
    text = str(lyric).strip()
    
    # 1. Kiem tra cac chuoi loi mac dinh
    if text == "Không có lời bài hát (Sub)" or text == "Lỗi đọc Lyrics" or text == "":
        return True
        
    # 2. Kiem tra chieu dai (Qua ngan)
    word_count = count_words(text)
    if word_count < 50: # Bai hat it hon 50 tu la bat thuong
        return True
        
    # 3. Kiem tra chua toan ki tu rac cua auto-sub
    if "[âm nhạc]" in text.lower() or "[nhạc nền]" in text.lower() or text.count('♪') > 3:
        return True
        
    return False

def main():
    print("[-] Dang doc file du lieu goc...")
    try:
        df = pd.read_csv(INPUT_CSV)
    except FileNotFoundError:
        print(f"[!] Khong tim thay {INPUT_CSV}. Hay dam bao ban da chay script xuat CSV truoc do.")
        return

    total_songs = len(df)
    
    print("[-] Dang danh gia chat luong tung dong Lyrics...")
    # Tao them cot kiem tra do nhieu
    df['Is_Noisy_Lyric'] = df['Lyrics'].apply(is_noisy_lyric)
    df['Word_Count'] = df['Lyrics'].apply(count_words)
    
    # Loc ra nhung bai bi danh dau nhieu
    df_need_genius = df[df['Is_Noisy_Lyric'] == True].copy()
    
    # Tinh toan thong ke
    noisy_count = len(df_need_genius)
    good_count = total_songs - noisy_count
    
    print("\n" + "=" * 40)
    print("KẾT QUẢ KIỂM ĐỊNH LỜI BÀI HÁT (YOUTUBE VTT)")
    print("=" * 40)
    print(f"Tổng số bài hát: {total_songs}")
    print(f"Số bài có Lyrics xịn (Đủ dài, không nhiễu): {good_count} bài")
    print(f"Số bài MẤT LYRIC hoặc BỊ NHIỄU: {noisy_count} bài")
    print("=" * 40)
    
    if noisy_count > 0:
        # Ghi danh sach can cao tren Genius ra file moi (Chi can giu lai ID va Ten bai)
        # De chuan bi cho con bot Genius tim kiem
        df_need_genius = df_need_genius[['Video_ID', 'Title', 'Uploader']]
        df_need_genius.to_csv(OUTPUT_GENIUS_LIST, index=False, encoding='utf-8-sig')
        print(f"\n[+] Đã xuất danh sách {noisy_count} bài cần cầu cứu Genius ra file:")
        print(f"    -> {OUTPUT_GENIUS_LIST}")

if __name__ == "__main__":
    main()