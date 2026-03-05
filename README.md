# Hệ thống nhận diện cảm xúc âm nhạc

## (Music Emotion Recognition – Valence & Arousal Space)

---

## 1. Giới thiệu

Dự án xây dựng hệ thống nhận diện cảm xúc trong âm nhạc dựa trên mô hình không gian cảm xúc hai chiều Valence – Arousal.

Mô hình dự đoán đầu ra liên tục:

```
[valence_pred, arousal_pred]
```

Trong đó:

* `valence_pred` đại diện cho mức độ tích cực của bài hát.
* `arousal_pred` đại diện cho mức độ kích thích cảm xúc.

Thay vì ánh xạ từ emotion words, hệ thống sử dụng trực tiếp Spotify Audio Features làm nhãn huấn luyện liên tục:

```
Ground Truth = [valence_spotify, energy_spotify]
```

* `valence_spotify` được dùng làm nhãn Valence.
* `energy_spotify` được sử dụng như đại diện cho Arousal.

---

## 2. Mục tiêu dự án

* Thu thập dữ liệu âm nhạc (audio, lyrics, metadata)
* Trích xuất đặc trưng âm thanh và ngôn ngữ
* Xây dựng mô hình Deep Learning đa phương thức
* Dự đoán giá trị cảm xúc liên tục trong không gian Valence – Arousal
* Đánh giá mô hình bằng các chỉ số hồi quy tiêu chuẩn

---

## 3. Phương pháp thực hiện

Hệ thống sử dụng Deep Learning đa phương thức:

* **Audio encoder:** BEATs (pretrained audio representation model)
* **Text encoder:** BERT
* **Feature fusion:** Nối embedding audio và text
* **Regression head:** Fully Connected → 2 outputs (Valence, Arousal)

### 3.1 Nhãn huấn luyện

Ground truth được lấy từ Spotify Audio Features:

* `valence_spotify` ∈ [0, 1]
* `energy_spotify` ∈ [0, 1]

Mô hình học ánh xạ:

```
(Audio + Lyrics) → [valence_pred, arousal_pred]
```

và được huấn luyện bằng cách tối thiểu hóa sai số giữa:

* `valence_pred` và `valence_spotify`
* `arousal_pred` và `energy_spotify`

Hàm mất mát sử dụng:

```
MSELoss
```

---

## 4. Chiến lược đánh giá mô hình

Vì đây là bài toán hồi quy hai biến liên tục, mô hình được đánh giá bằng các chỉ số sau:

### 4.1 Mean Squared Error (MSE)

```
MSE_valence  = MSE(valence_pred, valence_spotify)
MSE_arousal  = MSE(arousal_pred, energy_spotify)
```

---

### 4.2 Root Mean Squared Error (RMSE)

```
RMSE_valence = sqrt(MSE_valence)
RMSE_arousal = sqrt(MSE_arousal)
```

---

### 4.3 R² Score

Đánh giá mức độ mô hình giải thích phương sai của dữ liệu:

```
R²_valence  = R²(valence_pred, valence_spotify)
R²_arousal  = R²(arousal_pred, energy_spotify)
```

---

### 4.4 Pearson Correlation

Đo mức độ tương quan tuyến tính giữa giá trị dự đoán và ground truth:

```
Pearson_valence  = corr(valence_pred, valence_spotify)
Pearson_arousal  = corr(arousal_pred, energy_spotify)
```

---

## 5. Pipeline hệ thống

```
Thu thập dữ liệu
├── Spotify metadata
├── Spotify audio features (valence, energy)
└── YouTube audio

Tiền xử lý dữ liệu
├── Audio normalization
└── Text cleaning

Trích xuất đặc trưng
├── BEATs embedding
└── BERT embedding

Huấn luyện mô hình
├── Fusion
└── Regression head (2 outputs)

Đánh giá
├── So sánh valence_pred với valence_spotify
└── So sánh arousal_pred với energy_spotify
```

---

## 6. Cấu trúc thư mục dự án

```
music-emotion-recognition/
│
├── data/
│   ├── raw/
│   │   ├── audio/
│   │   ├── lyrics/
│   │   ├── tags/
│   │   └── metadata/
│   │
│   ├── interim/
│   │   ├── cleaned_audio/
│   │   ├── cleaned_lyrics/
│   │   └── filtered_tags/
│   │
│   ├── processed/
│   │   ├── audio_embeddings/
│   │   ├── text_embeddings/
│   │   └── dataset.csv
│   │
│   └── splits/
│       ├── train.csv
│       ├── val.csv
│       └── test.csv
│
├── src/
│   ├── data/
│   ├── preprocessing/
│   ├── features/
│   ├── models/
│   ├── training/
│   ├── evaluation/
│   └── utils/
│
├── notebooks/
├── outputs/
├── configs/
├── scripts/
├── requirements.txt
├── README.md
└── main.py
```

---

## 7. Kiến trúc mô hình

```
BEATs Audio Encoder ─┐
                     ├── Concatenate ── Fully Connected ── [valence_pred, arousal_pred]
BERT Text Encoder   ─┘
```

---

## 8. Cài đặt

```bash
git clone <repository-url>
cd music-emotion-recognition
pip install -r requirements.txt
```

---

## 9. Huấn luyện mô hình

```bash
python main.py --config configs/training_config.yaml
```

---

## 10. Ví dụ đánh giá

```
valence_spotify: 0.72
valence_pred:    0.68

energy_spotify:  0.81
arousal_pred:    0.77

MSE_valence: 0.0016
MSE_arousal: 0.0016
```

---

## 11. Hạn chế

* `energy_spotify` chỉ được sử dụng như đại diện cho Arousal, không phải nhãn tâm lý học chính thức.
* Spotify valence và energy là đặc trưng do hệ thống nội bộ của Spotify tính toán.
* Mô hình học dựa trên Spotify Audio Features thay vì nhãn cảm xúc do con người gán.

