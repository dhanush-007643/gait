# Gait Abnormality Classification System

Software-based gait analysis system for a B.Tech Biotechnology capstone project.
Accepts accelerometer + gyroscope CSV data and classifies walking patterns into
**6 gait classes** using a Random Forest classifier backed by a PostgreSQL database.

> **Academic project** — outputs are for research and educational purposes only.
> No real patient data is stored or used.

---

## Project Structure

```
gait-abnormality-system/
├── db/
│   ├── schema.sql          # PostgreSQL DDL (6 tables, enum, indexes)
│   ├── seed_data.sql       # SYNTHETIC demo INSERTs for testing
│   └── db_connect.py       # psycopg2 connection helper + session/history helpers
│
├── data/
│   ├── raw/                # Place raw sensor CSV recordings here
│   └── processed/
│       ├── gait_training_dataset.csv  # 120-row SYNTHETIC training dataset
│       └── DATASET_README.md          # Column reference + public dataset guide
│
├── models/                 # Saved .pkl model files (created by training)
│
├── notebooks/
│   └── pipeline_demo.py    # End-to-end runnable demo
│
├── src/
│   ├── preprocessing.py        # Load, clean, filter, normalize
│   ├── gait_detection.py       # Magnitude, step detection, windowing
│   ├── feature_extraction.py   # Statistical + gait features, batch builder
│   ├── train_model.py          # Original binary training pipeline (kept)
│   ├── train_classifier.py     # NEW — full 6-class training pipeline
│   ├── evaluation.py           # Metrics, confusion matrix, importances
│   └── prediction.py           # Load model, run inference
│
├── app/
│   └── app.py              # Flask REST API (8 endpoints)
│
├── reports/                # Saved evaluation outputs
├── requirements.txt
└── README.md
```

---

## Gait Classes

| Class | Characteristics |
|-------|----------------|
| `normal` | Healthy adult walking — symmetric, consistent cadence |
| `parkinsonian` | Short shuffling steps, festination, reduced arm swing |
| `hemiplegic` | Asymmetric gait from unilateral paralysis/weakness |
| `ataxic` | Wide-based, uncoordinated, staggering — high variability |
| `spastic` | Stiff scissor-like gait from increased muscle tone |
| `antalgic` | Pain-avoidance: shortened stance on painful side |

---

## Database Setup (PostgreSQL)

### 1. Install PostgreSQL (if needed)

Download from https://www.postgresql.org/download/

### 2. Create the database

```sql
CREATE DATABASE gait_db;
```

### 3. Apply schema

```bash
psql -U postgres -d gait_db -f db/schema.sql
```

### 4. Load demo data (synthetic only)

```bash
psql -U postgres -d gait_db -f db/seed_data.sql
```

### 5. Set environment variables

```powershell
# Windows PowerShell
$env:PGHOST     = "localhost"
$env:PGPORT     = "5432"
$env:PGDATABASE = "gait_db"
$env:PGUSER     = "postgres"
$env:PGPASSWORD = "yourpassword"
$env:SECRET_KEY = "replace-with-a-long-random-secret"
```

### 6. Test connection

```bash
python database.py
```

---

## Expected CSV Format (Raw Sensor Data)

| Column | Type | Notes |
|--------|------|-------|
| `timestamp` | str/int | ISO datetime or integer milliseconds |
| `acc_x` | float | Accelerometer X axis (m/s²) |
| `acc_y` | float | Accelerometer Y axis |
| `acc_z` | float | Accelerometer Z axis |
| `gyro_x` | float | Gyroscope X axis (rad/s) |
| `gyro_y` | float | Gyroscope Y axis |
| `gyro_z` | float | Gyroscope Z axis |
| `label` | str | Gait class — **training data only** |

---

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Train the 6-class model

```bash
py -3 src/train_classifier.py \
  --csv data/processed/gait_training_dataset.csv \
  --out models/gait_model_v1.pkl
```

Output includes accuracy, precision, recall, F1-score, and confusion matrix.

### 3. Start the API server

```bash
python app/app.py
# → http://localhost:5000
```

### 4. Test with curl

```bash
# Health check
curl http://localhost:5000/health

# Classify from feature JSON
curl -X POST http://localhost:5000/predict/features \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_LOGIN_TOKEN" \
  -d "{\"cadence\": 109.3, \"walking_speed\": 1.35, \"step_length\": 0.698}"

# Upload raw CSV
curl -X POST http://localhost:5000/predict \
  -H "Authorization: Bearer YOUR_LOGIN_TOKEN" \
  -F "file=@data/raw/subject_01.csv" \
  -F "sampling_rate=100"
```

---

## REST API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/health` | Liveness check — model + DB status |
| `POST` | `/sessions` | Create a new session record |
| `POST` | `/sessions/<id>/upload` | Upload CSV, run pipeline, store in DB |
| `GET`  | `/sessions/<id>/result` | Get prediction for a session |
| `GET`  | `/users/<id>/history` | All sessions for a user |
| `GET`  | `/model/performance` | Latest model evaluation metrics |
| `POST` | `/predict` | Classify CSV (no DB write) |
| `POST` | `/predict/features` | Classify from JSON features |

All `/api/*` data endpoints except login, registration, health, and model
performance require the bearer token returned by `/api/auth/login`.
Uploaded CSV files are limited to 10 MB by default; override this with
`MAX_UPLOAD_BYTES` when necessary.

### Example: Create session + upload CSV

```bash
# Step 1: create session
curl -X POST http://localhost:5000/sessions \
  -H "Content-Type: application/json" \
  -d '{"user_id":2,"subject_id":"UPLOAD_001","data_source":"uploaded_csv","file_name":"walk.csv"}'

# Step 2: upload CSV for that session (session_id=7 from response)
curl -X POST http://localhost:5000/sessions/7/upload \
  -F "file=@data/raw/walk.csv"
```

### Example JSON response (prediction)

```json
{
  "session_id": 7,
  "predicted_class": "parkinsonian",
  "confidence_score": 0.8741,
  "probabilities": {
    "antalgic":     0.0142,
    "ataxic":       0.0312,
    "hemiplegic":   0.0198,
    "normal":       0.0512,
    "parkinsonian": 0.8741,
    "spastic":      0.0095
  },
  "n_steps_detected": 76,
  "features_stored": true,
  "prediction_id": 12
}
```

---

## ML Training Pipeline

```
CSV → validate columns → handle missing values → encode labels
    → subject-wise GroupShuffleSplit → StandardScaler + RandomForest
    → accuracy / precision / recall / F1 (macro) → confusion matrix
    → save model.pkl + model_meta.json
```

Key design decisions:
- **Subject-wise split**: prevents data leakage across recordings from the same person
- **`class_weight="balanced"`**: handles class imbalance automatically
- **LabelEncoder on fixed class list**: stable integer mapping across runs
- **StandardScaler inside Pipeline**: scaler fit on train only, transform on both

---

## Database Schema (ER Summary)

```
users (user_id PK)
  └── gait_sessions (session_id PK, user_id FK)
        ├── sensor_data    (sensor_id PK, session_id FK)  [1:N]
        ├── gait_features  (feature_id PK, session_id FK) [1:1]
        └── predictions    (prediction_id PK, session_id FK) [1:N]

model_performance (model_id PK)  [standalone audit log]
```

Full Mermaid ER diagram: see `db/schema.sql` comments.

---

## Public Datasets (for replacing synthetic data)

| Dataset | URL | Notes |
|---------|-----|-------|
| PhysioNet GaitPDB | https://physionet.org/content/gaitpdb/1.0.0/ | Parkinson's gait — force sensors |
| PhysioNet GaitNDD | https://physionet.org/content/gaitndd/1.0.0/ | Neurodegenerative diseases |
| UCI HAR | https://archive.ics.uci.edu/ml/datasets/human+activity+recognition+using+smartphones | Smartphone IMU |
| WISDM | https://www.cis.fordham.edu/wisdm/dataset.php | Accelerometer, 36 subjects |

See `data/processed/DATASET_README.md` for column-mapping instructions.

---

## Dependencies

| Library | Purpose |
|---------|---------|
| pandas, numpy | Data handling |
| scipy | Signal filtering, peak detection |
| scikit-learn | ML pipeline, Random Forest, metrics |
| joblib | Model persistence |
| flask | REST API |
| psycopg2-binary | PostgreSQL driver |
| matplotlib, seaborn | Confusion matrix plots |
