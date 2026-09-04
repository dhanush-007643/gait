# DATASET_README.md — Gait Training Dataset Documentation

## File: `gait_training_dataset.csv`

> **DISCLAIMER**: The dataset in this file is **100% SYNTHETIC** (computer-generated).
> It was created solely to test the software pipeline. It does NOT represent,
> approximate, or derive from real patient measurements. Do NOT use it for
> clinical conclusions or research publications.

---

## Column Reference

| Column | Role | Type | Unit | Description |
|--------|------|------|------|-------------|
| `subject_id` | Metadata | string | — | Participant code (SYN_xxx = synthetic) |
| `session_id` | Metadata | string | — | Unique session identifier |
| `gait_class` | **Target label** | string | — | One of 6 gait classes (see below) |
| `duration` | Input feature | float | seconds | Length of the walking bout |
| `step_count` | Input feature | int | steps | Total steps detected |
| `cadence` | Input feature | float | steps/min | Step rate |
| `walking_speed` | Input feature | float | m/s | Estimated forward speed |
| `step_length` | Input feature | float | m | Average distance per step |
| `stride_length` | Input feature | float | m | Average distance per stride (2 steps) |
| `step_time` | Input feature | float | s | Average time per step |
| `stride_time` | Input feature | float | s | Average time per stride |
| `stance_time` | Input feature | float | s | Time foot is on ground |
| `swing_time` | Input feature | float | s | Time foot is in the air |
| `gait_symmetry` | Input feature | float | ratio | Left/right symmetry (1.0 = perfect) |
| `mean_acceleration` | Input feature | float | m/s² | Mean magnitude of accelerometer |
| `acceleration_std` | Input feature | float | m/s² | Std dev of accelerometer magnitude |
| `acceleration_rms` | Input feature | float | m/s² | RMS of accelerometer magnitude |
| `mean_gyroscope` | Input feature | float | rad/s | Mean magnitude of gyroscope |
| `gyroscope_std` | Input feature | float | rad/s | Std dev of gyroscope magnitude |

### Column Roles Summary
- **Target label** (1 column): `gait_class` — encoded as integer by LabelEncoder during training
- **Input features** (16 columns): all numeric columns except subject_id, session_id, gait_class
- **Metadata** (2 columns): `subject_id`, `session_id` — used for subject-wise splitting, never fed to the model

---

## Gait Classes

| Class | Description |
|-------|-------------|
| `normal` | Healthy adult walking pattern |
| `parkinsonian` | Short shuffling steps, festination, reduced arm swing |
| `hemiplegic` | Asymmetric gait from unilateral paralysis/weakness |
| `ataxic` | Wide-based, uncoordinated, staggering pattern |
| `spastic` | Stiff scissor-like gait from increased muscle tone |
| `antalgic` | Pain-avoidance: shortened stance on painful side |

---

## Replacing Synthetic Data with a Public Dataset

The synthetic dataset must be replaced with a validated public dataset
before drawing any research conclusions. Recommended datasets:

### Option A — PhysioNet Gait Databases
- **URL**: https://physionet.org/content/gaitpdb/1.0.0/
- **GaitPDB**: Gait in Parkinson's Disease — force sensor data
- **URL**: https://physionet.org/content/gaitndd/1.0.0/
- **GaitNDD**: Gait in Neurodegenerative Disease (Parkinson, Huntington, ALS)
- **License**: Open Data Commons Attribution (ODC-By)

### Option B — UCI HAR Dataset
- **URL**: https://archive.ics.uci.edu/ml/datasets/human+activity+recognition+using+smartphones
- Contains accelerometer/gyroscope data from 30 subjects
- Covers walking, walking_upstairs, walking_downstairs, sitting, standing, laying
- Needs label remapping (see below)

### Option C — WISDM Activity Recognition
- **URL**: https://www.cis.fordham.edu/wisdm/dataset.php
- Accelerometer data, 36 subjects

---

## Mapping Public Dataset Columns to This Schema

Use this mapping process when integrating a public dataset:

```python
import pandas as pd

# Example: mapping GaitPDB to this schema
# GaitPDB provides stride time, stance time, swing time directly

def map_gaitpdb_to_schema(raw_df, gait_class_label):
    """
    Map GaitPDB columns to gait_training_dataset.csv schema.
    
    raw_df: DataFrame from PhysioNet GaitPDB
    gait_class_label: str — one of the 6 valid classes
    """
    mapped = pd.DataFrame()
    
    # GaitPDB column -> our schema column
    mapped["stride_time"]   = raw_df["StrideTime"]   # already in seconds
    mapped["stance_time"]   = raw_df["StanceTime"]
    mapped["swing_time"]    = raw_df["SwingTime"]
    mapped["step_time"]     = raw_df["StepTime"]
    mapped["cadence"]       = 60.0 / raw_df["StrideTime"]  # derive cadence
    mapped["gait_symmetry"] = raw_df["SwingTime_L"] / raw_df["SwingTime_R"]
    
    # Columns not in GaitPDB — fill with NaN (will be imputed)
    for col in ["walking_speed", "step_length", "stride_length",
                "mean_acceleration", "acceleration_std", "acceleration_rms",
                "mean_gyroscope", "gyroscope_std"]:
        mapped[col] = float("nan")
    
    mapped["gait_class"]  = gait_class_label
    mapped["subject_id"]  = raw_df["subject_id"]
    mapped["session_id"]  = raw_df["trial_id"]
    mapped["duration"]    = raw_df["duration"]
    mapped["step_count"]  = raw_df["n_steps"]
    
    return mapped
```

---

## Data Leakage Prevention — Subject-wise Splitting

**Why row-level random splitting causes data leakage:**
If subject SYN_001 has 4 sessions and you randomly split rows, some of
their sessions land in training and others in test. The model sees the
subject's gait pattern during training and "recognises" it during testing —
inflating accuracy.

**Correct approach — GroupShuffleSplit by subject_id:**
```python
from sklearn.model_selection import GroupShuffleSplit

gss = GroupShuffleSplit(n_splits=1, test_size=0.20, random_state=42)
train_idx, test_idx = next(gss.split(X, groups=df["subject_id"]))

# Result: every session from subject SYN_001 is entirely in train OR test
```

This guarantees the test set contains subjects the model has NEVER seen.

---

## Class Balancing

The synthetic dataset has exactly 20 rows per class (perfectly balanced).
Real datasets are often imbalanced. Two strategies are used:

1. **`class_weight="balanced"`** in RandomForestClassifier:
   Automatically increases the weight of minority classes during training.

2. **SMOTE** (optional, for severe imbalance):
   ```python
   from imblearn.over_sampling import SMOTE
   sm = SMOTE(random_state=42)
   X_resampled, y_resampled = sm.fit_resample(X_train, y_train)
   ```
   Install: `pip install imbalanced-learn`

---

## Missing Value Handling

Strategy applied in `train_classifier.py`:
1. **Forward-fill** → **Backward-fill**: fills short dropout gaps
2. **Median imputation**: fills any remaining NaN with column median

Median is preferred over mean because it is robust to outliers in gait data
(e.g., an unusually large cadence spike won't skew the imputation value).

---

## Feature Normalization

The pipeline applies **StandardScaler** (zero mean, unit variance):

```
x_scaled = (x - mean) / std
```

- Applied AFTER the train/test split (fit scaler on train only, transform both)
- This prevents test-set statistics from leaking into scaling parameters
- Implemented as `Pipeline([("scaler", StandardScaler()), ("clf", RandomForest())])`

---

## Label Encoding

String class labels are encoded to integers using `LabelEncoder`:

```
antalgic     -> 0
ataxic       -> 1
hemiplegic   -> 2
normal       -> 3
parkinsonian -> 4
spastic      -> 5
```

The LabelEncoder is fit on the fixed `VALID_CLASSES` list (not the data),
so encoding is stable across training runs and model versions.
The mapping is saved to `models/gait_model_v1_meta.json` for use at inference time.
