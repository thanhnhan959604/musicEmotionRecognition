import os
import shutil
import json
import whisper
import torch
from tqdm import tqdm

# =============================
# CAU HINH THU MUC
# =============================
AUDIO_DIR = "data/raw/audio"
META_DIR = "data/raw/json"  
OUTPUT_DIR = "data/filtered/audio"
TXT_OUTPUT = "data/filtered/vietnamese_songs.txt"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Bo loc tu khoa rac (da bao gom behind the scenes)
BAD_KEYWORDS = [
    "behind the scenes", "bts", "dance", "choreography", 
    "vlog", "diary", "teaser", "trailer", "reaction", 
    "karaoke", "beat", "instrumental", "making of", "kham pha", "tap tap"
]

# =============================
# KICH HOAT GPU (CUDA)
# =============================
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Dang tai mo hinh Whisper (base) tren: {device.upper()}... Vui long doi.")
model = whisper.load_model("base", device=device)

def is_music_track(video_id):
    json_path = os.path.join(META_DIR, f"{video_id}.info.json")
    if not os.path.exists(json_path):
        return False 
        
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            title = data.get("title", "").lower()
            
            for bad_word in BAD_KEYWORDS:
                if bad_word in title:
                    return False 
            return True
    except Exception:
        return False

# =============================
# HAM NHAN DIEN (NHAY VAO GIUA BAI)
# =============================
def detect_vietnamese(audio_path):
    try:
        audio = whisper.load_audio(audio_path)
        
        # Nhay vao giua bai (bo qua 60s intro, lay 30s diep khuc)
        start_sample = 60 * 16000
        end_sample = 90 * 16000
        
        if len(audio) > start_sample:
            audio_segment = audio[start_sample:end_sample]
        else:
            audio_segment = audio
            
        audio_padded = whisper.pad_or_trim(audio_segment)
        mel = whisper.log_mel_spectrogram(audio_padded, n_mels=model.dims.n_mels).to(model.device)
        _, probs = model.detect_language(mel)
        detected_lang = max(probs, key=probs.get)
        
        return detected_lang == "vi"
    except Exception:
        return False

# =============================
# MAIN
# =============================
def main():
    files = [f for f in os.listdir(AUDIO_DIR) if f.endswith(".mp3")]
    
    if not files:
        print(f"Khong tim thay file .mp3 nao trong {AUDIO_DIR}.")
        return

    print(f"Bat dau quet {len(files)} file am thanh bang {device.upper()}...")
    vi_songs = []

    for file in tqdm(files, desc="Dang xu ly Dataset"):
        video_id = file.replace(".mp3", "")
        audio_path = os.path.join(AUDIO_DIR, file)
        
        # B1: Loc bang chu
        if not is_music_track(video_id):
            continue 
            
        # B2: Loc bang am thanh GPU
        if detect_vietnamese(audio_path):
            vi_songs.append(file)
            shutil.copy(audio_path, os.path.join(OUTPUT_DIR, file))

    with open(TXT_OUTPUT, "w", encoding="utf-8") as f:
        for song in vi_songs:
            f.write(f"{song}\n")

    print("\n" + "=" * 40)
    print("HOAN THANH LOC DU LIEU SACH!")
    print(f"Tong so bai MP3 goc: {len(files)}")
    print(f"So bai Nhac Viet Nam tieu chuan giu lai: {len(vi_songs)}")
    print(f"File danh sach: {TXT_OUTPUT}")
    print("=" * 40)

if __name__ == "__main__":
    main()