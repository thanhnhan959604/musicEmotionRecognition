## Hệ thống nhận diện cảm xúc âm nhạc

### (Music Emotion Recognition – Valence & Arousal Space)

---

### 1. Giới thiệu

Dự án xây dựng hệ thống nhận diện cảm xúc trong âm nhạc dựa trên mô hình không gian cảm xúc hai chiều Valence – Arousal theo cấu trúc vòng tròn cảm xúc (Circumplex Model of Affect).

Mô hình dự đoán đầu ra liên tục: `[valence, arousal]`

Tuy nhiên, do không có nhãn liên tục (continuous ground truth), hệ thống áp dụng phương pháp ánh xạ cảm xúc rời rạc (emotion words) sang không gian hai chiều và đánh giá theo chiến lược gần nhất trong không gian vector.

---

### 2. Mục tiêu dự án

* Thu thập dữ liệu âm nhạc (audio, lời bài hát, metadata)
* Trích xuất đặc trưng âm thanh và ngôn ngữ
* Dự đoán tọa độ cảm xúc trong không gian Valence – Arousal
* Ánh xạ cảm xúc rời rạc sang vector trung tâm
* Đánh giá mô hình dưới dạng phân loại 28 lớp
* Báo cáo sai số góc trung bình (Mean Angular Error)

---

### 3. Phương pháp thực hiện

Hệ thống sử dụng Deep Learning đa phương thức:

* **Audio encoder:** BEATs (pretrained audio representation model)
* **Text encoder:** BERT
* **Feature fusion:** Nối embedding audio và text
* **Regression head:** Fully Connected → 2 outputs (Valence, Arousal)

#### 3.1 Không có nhãn liên tục

Do không có giá trị Valence – Arousal thật, hệ thống sử dụng chiến lược sau:

1. Mỗi emotion word (28 từ theo mô hình Russell) được gán một vector trung tâm trong không gian 2D.
2. Sau khi mô hình dự đoán (x, y), tính khoảng cách Euclidean giữa điểm dự đoán và toàn bộ 28 vector trung tâm.
3. Chọn emotion có khoảng cách nhỏ nhất làm nhãn dự đoán.
4. So sánh với emotion ground truth để tính accuracy.

---

### 4. Chiến lược đánh giá mô hình

#### 4.1 Nearest Emotion Center Classification (28 lớp)

* Đối với mỗi dự đoán:
* Tính khoảng cách đến tất cả 28 emotion centers.
* Chọn emotion gần nhất.
* So sánh với ground truth label.



**Chỉ số đánh giá:**

* Accuracy
* Precision
* Recall
* F1-score
* Confusion Matrix

#### 4.2 Mean Angular Error (MAE - góc)

Để phản ánh sai số liên tục trong không gian cảm xúc, tính sai số góc:

$$\theta = arctan2(arousal, valence)$$

$$Angular\ Error = |\theta_{pred} - \theta_{gt}|$$

**Báo cáo:**

* Mean Angular Error
* Standard Deviation của Angular Error

Chỉ số này giúp giảm ảnh hưởng của ranh giới phân lớp cứng.

---

### 5. Pipeline hệ thống

```text
Thu thập dữ liệu
├── Spotify API
├── YouTube
└── Last.fm emotion tags

Tiền xử lý dữ liệu
├── Audio normalization
└── Text cleaning

Trích xuất đặc trưng
├── BEATs embedding
└── BERT embedding

Huấn luyện mô hình
├── Fusion
└── Regression head (2 outputs)

Ánh xạ emotion center
├── Gán vector trung tâm cho 28 emotion words
└── Nearest neighbor search

Đánh giá
├── 28-class classification metrics
└── Mean Angular Error

```

---

### 6. Cấu trúc thư mục dự án

```text
music-emotion-recognition/
│
├── data/
│   ├── raw/
│   │   ├── audio/                  # Audio gốc tải về
│   │   ├── lyrics/                 # Lyrics raw
│   │   ├── tags/                   # Last.fm emotion tags
│   │   └── metadata/               # Spotify metadata
│   │
│   ├── interim/
│   │   ├── cleaned_audio/
│   │   ├── cleaned_lyrics/
│   │   └── filtered_tags/
│   │
│   ├── processed/
│   │   ├── audio_embeddings/       # BEATs embeddings
│   │   ├── text_embeddings/        # BERT embeddings
│   │   ├── emotion_centers/        # 28 emotion vectors
│   │   └── dataset.csv             # Final merged dataset
│   │
│   └── splits/
│       ├── train.csv
│       ├── val.csv
│       └── test.csv
│
├── src/
│   ├── data/
│   │   ├── download_youtube.py
│   │   ├── download_spotify.py
│   │   ├── fetch_lastfm_tags.py
│   │   ├── fetch_lyrics.py
│   │   └── build_dataset.py
│   │
│   ├── preprocessing/
│   │   ├── audio_preprocess.py
│   │   ├── text_preprocess.py
│   │   └── tag_filter.py
│   │
│   ├── features/
│   │   ├── extract_beats.py
│   │   ├── extract_bert.py
│   │   └── build_emotion_centers.py
│   │
│   ├── models/
│   │   ├── audio_encoder.py
│   │   ├── text_encoder.py
│   │   ├── fusion_model.py
│   │   └── regression_head.py
│   │
│   ├── training/
│   │   ├── train.py
│   │   ├── trainer.py
│   │   └── loss.py
│   │
│   ├── evaluation/
│   │   ├── nearest_centroid.py
│   │   ├── metrics_classification.py
│   │   ├── angular_error.py
│   │   └── evaluate.py
│   │
│   └── utils/
│       ├── config.py
│       ├── logger.py
│       ├── visualization.py
│       └── seed.py
│
├── notebooks/
│   ├── 01_data_collection.ipynb
│   ├── 02_preprocessing.ipynb
│   ├── 03_feature_extraction.ipynb
│   ├── 04_training.ipynb
│   └── 05_analysis.ipynb
│
├── outputs/
│   ├── checkpoints/
│   ├── logs/
│   ├── predictions/
│   ├── confusion_matrices/
│   └── plots/
│
├── configs/
│   ├── data_config.yaml
│   ├── model_config.yaml
│   ├── training_config.yaml
│   └── evaluation_config.yaml
│
├── scripts/
│   ├── run_pipeline.sh
│   ├── train.sh
│   └── evaluate.sh
│
├── requirements.txt
├── README.md
└── main.py

```

---

### 7. Kiến trúc mô hình

```text
BEATs Audio Encoder ─┐
                     ├── Concatenate ── Fully Connected ── [Valence, Arousal]
BERT Text Encoder   ─┘

```

---

### 8. Cài đặt

```bash
git clone <repository-url>
cd music-emotion-recognition
pip install -r requirements.txt

```

---

### 9. Huấn luyện mô hình

```bash
python main.py --config configs/training_config.yaml

```

---

### 10. Ví dụ đánh giá

* **Ground Truth Emotion:** happy
* **Predicted Emotion:** delighted
* **Angular Error:** 12.4°

---

### 11. Hạn chế

* Không có nhãn Valence – Arousal liên tục
* Emotion tags có thể chứa nhiễu
* Ánh xạ emotion center phụ thuộc vào giả định cấu trúc vòng tròn



