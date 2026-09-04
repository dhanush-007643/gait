# -*- coding: utf-8 -*-
"""
train_classifier.py
===================
Full 6-class gait abnormality classification pipeline.

Pipeline:
  CSV -> validate -> missing-value handling -> encode labels
  -> subject-wise train/test split -> StandardScaler + RandomForest
  -> accuracy / precision / recall / F1 -> confusion matrix -> save model

Usage (CLI):
    python src/train_classifier.py \
        --csv data/processed/gait_training_dataset.csv \
        --out models/gait_model_v1.pkl

Usage (module):
    from train_classifier import run_pipeline
    metrics = run_pipeline("data/processed/gait_training_dataset.csv",
                           "models/gait_model_v1.pkl")

DISCLAIMER:
  The default dataset (gait_training_dataset.csv) contains SYNTHETIC data
  generated for software pipeline testing only. It is NOT derived from real
  patient measurements and must NOT be used for clinical claims.
  Replace it with a validated public dataset (see DATASET_README.md) before
  making any research conclusions.
"""

import argparse
import json
from datetime import datetime, timezone
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, StandardScaler

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# All 6 valid gait classes (must match gait_class_enum in schema.sql)
VALID_CLASSES = ["normal", "parkinsonian", "hemiplegic", "ataxic", "spastic", "antalgic"]

# Target label column in the CSV
LABEL_COL = "gait_class"

# Metadata columns (not used as ML features)
METADATA_COLS = {"subject_id", "session_id", LABEL_COL}

# Minimum required columns in the CSV
REQUIRED_COLUMNS = [
    "subject_id", "session_id", "gait_class",
    "duration", "step_count", "cadence", "walking_speed",
    "step_length", "stride_length", "step_time", "stride_time",
    "stance_time", "swing_time", "gait_symmetry",
    "mean_acceleration", "acceleration_std", "acceleration_rms",
    "mean_gyroscope", "gyroscope_std",
]

# Columns that are input features to the model (everything except metadata)
FEATURE_COLS = [c for c in REQUIRED_COLUMNS if c not in METADATA_COLS]


# ---------------------------------------------------------------------------
# Step 1 — Load and validate CSV
# ---------------------------------------------------------------------------

def load_and_validate(csv_path: str) -> pd.DataFrame:
    """
    Load the feature CSV and validate columns and class labels.

    Parameters
    ----------
    csv_path : str
        Path to the gait feature CSV file.

    Returns
    -------
    pd.DataFrame
        Validated DataFrame.

    Raises
    ------
    FileNotFoundError, ValueError
    """
    if not Path(csv_path).exists():
        raise FileNotFoundError("CSV not found: {}".format(csv_path))

    df = pd.read_csv(csv_path)
    print("[validate] Loaded {} rows, {} columns.".format(len(df), len(df.columns)))

    # Check all required columns are present
    missing_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_cols:
        raise ValueError(
            "CSV is missing required columns: {}\nFound: {}".format(
                missing_cols, list(df.columns)
            )
        )

    # Validate gait class labels
    invalid = set(df[LABEL_COL].unique()) - set(VALID_CLASSES)
    if invalid:
        raise ValueError(
            "Unknown gait class labels found: {}\nAllowed: {}".format(
                invalid, VALID_CLASSES
            )
        )

    print("[validate] All columns present. Classes found: {}".format(
        sorted(df[LABEL_COL].unique())
    ))
    return df


# ---------------------------------------------------------------------------
# Step 2 — Handle missing values
# ---------------------------------------------------------------------------

def handle_missing(df: pd.DataFrame) -> pd.DataFrame:
    """
    Handle missing values in feature columns.

    Strategy:
        1. Forward-fill, then backward-fill (preserves time ordering).
        2. Fill any remaining NaN with column median (robust to outliers).
        3. Report how many values were imputed.

    Parameters
    ----------
    df : pd.DataFrame

    Returns
    -------
    pd.DataFrame
        DataFrame with no NaN values in feature columns.
    """
    before_nan = df[FEATURE_COLS].isna().sum().sum()

    df = df.copy()
    df[FEATURE_COLS] = df[FEATURE_COLS].ffill().bfill()

    # Fill any columns that were entirely NaN with their median
    for col in FEATURE_COLS:
        if df[col].isna().any():
            median_val = df[col].median()
            df[col] = df[col].fillna(median_val)
            print("[missing] '{}' imputed with median={:.4f}".format(col, median_val))

    after_nan = df[FEATURE_COLS].isna().sum().sum()
    print("[missing] NaN values: {} before -> {} after imputation.".format(
        before_nan, after_nan
    ))
    return df


# ---------------------------------------------------------------------------
# Step 3 — Encode labels
# ---------------------------------------------------------------------------

def encode_labels(df: pd.DataFrame):
    """
    Encode the gait_class string labels as integers using LabelEncoder.

    The mapping is deterministic because VALID_CLASSES is a fixed ordered list.

    Parameters
    ----------
    df : pd.DataFrame

    Returns
    -------
    (pd.DataFrame, LabelEncoder)
        DataFrame with encoded 'label_encoded' column; LabelEncoder for inverse.
    """
    le = LabelEncoder()
    le.fit(VALID_CLASSES)  # fit on fixed list for stable mapping
    df = df.copy()
    df["label_encoded"] = le.transform(df[LABEL_COL])
    print("[encode] Label mapping:")
    for i, cls in enumerate(le.classes_):
        print("         {} -> {}".format(i, cls))
    return df, le


# ---------------------------------------------------------------------------
# Step 4 — Subject-wise train/test split
# ---------------------------------------------------------------------------

def split_by_subject(df: pd.DataFrame, test_size: float = 0.2,
                     random_state: int = 42):
    """
    Split dataset so that ALL sessions from one subject fall entirely in
    either train OR test — never split across both, while guaranteeing that
    EVERY gait class is present in both train and test sets (Stratified Subject Split).

    Parameters
    ----------
    df           : pd.DataFrame  -- full dataset
    test_size    : float         -- fraction of subjects for test (e.g. 0.2)
    random_state : int

    Returns
    -------
    train_df, test_df : (pd.DataFrame, pd.DataFrame)
    """
    groups = df["subject_id"].values
    unique_subjects = np.unique(groups)
    print("[split] Total subjects: {}".format(len(unique_subjects)))

    # Get subject-to-class mapping
    subj_class_map = df.groupby("subject_id")[LABEL_COL].first().to_dict()
    
    # Stratified selection by subject
    rng = np.random.RandomState(random_state)
    train_subjects = []
    test_subjects = []
    
    class_to_subjects = {}
    for subj, cls in subj_class_map.items():
        class_to_subjects.setdefault(cls, []).append(subj)
        
    for cls, subjs in sorted(class_to_subjects.items()):
        subjs_shuffled = list(subjs)
        rng.shuffle(subjs_shuffled)
        n_test = max(1, int(np.round(len(subjs_shuffled) * test_size)))
        test_subjs = subjs_shuffled[:n_test]
        train_subjs = subjs_shuffled[n_test:]
        test_subjects.extend(test_subjs)
        train_subjects.extend(train_subjs)
        
    train_df = df[df["subject_id"].isin(train_subjects)].copy()
    test_df  = df[df["subject_id"].isin(test_subjects)].copy()

    print("[split] Train subjects: {}".format(sorted(train_subjects)))
    print("[split] Test  subjects: {}".format(sorted(test_subjects)))
    print("[split] Train rows: {} | Test rows: {}".format(
        len(train_df), len(test_df)
    ))
    print("[split] Train classes: {}".format(sorted(train_df[LABEL_COL].unique())))
    print("[split] Test  classes: {}".format(sorted(test_df[LABEL_COL].unique())))

    # Sanity check: no subject appears in both sets
    overlap = set(train_subjects) & set(test_subjects)
    assert len(overlap) == 0, "Data leakage detected! Overlapping subjects: {}".format(overlap)

    return train_df, test_df


# ---------------------------------------------------------------------------
# Step 5 — Build sklearn pipeline
# ---------------------------------------------------------------------------

def build_pipeline(n_estimators: int = 200, max_depth=None,
                   random_state: int = 42) -> Pipeline:
    """
    Build a StandardScaler + RandomForestClassifier pipeline.

    RandomForest is not scale-sensitive, but including a StandardScaler
    makes it easy to swap in SVM or Logistic Regression later.

    Parameters
    ----------
    n_estimators : int   -- number of trees
    max_depth    : int or None
    random_state : int

    Returns
    -------
    sklearn.pipeline.Pipeline
    """
    return Pipeline([
        ("scaler", StandardScaler()),
        ("classifier", RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            random_state=random_state,
            n_jobs=-1,
            class_weight="balanced",   # handles class imbalance automatically
        ))
    ])


# ---------------------------------------------------------------------------
# Step 6 — Train and evaluate
# ---------------------------------------------------------------------------

def train_and_evaluate(train_df, test_df, le: LabelEncoder,
                       n_estimators: int = 200, max_depth=None,
                       random_state: int = 42):
    """
    Fit the pipeline on training data and evaluate on test data.

    Returns
    -------
    dict  -- all metrics, feature importances, confusion matrix
    Pipeline -- fitted pipeline
    """
    X_train = train_df[FEATURE_COLS]
    y_train = train_df["label_encoded"].values
    X_test  = test_df[FEATURE_COLS]
    y_test  = test_df["label_encoded"].values

    pipeline = build_pipeline(n_estimators, max_depth, random_state)
    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)

    # Explicit labels for all classes
    all_label_indices = list(range(len(le.classes_)))
    target_names = list(le.classes_)

    # Overall metrics
    acc    = float(accuracy_score(y_test, y_pred))
    prec   = float(precision_score(y_test, y_pred, labels=all_label_indices, average="macro", zero_division=0))
    rec    = float(recall_score(y_test, y_pred, labels=all_label_indices, average="macro", zero_division=0))
    f1_mac = float(f1_score(y_test, y_pred, labels=all_label_indices, average="macro", zero_division=0))

    print("\n" + "="*60)
    print("EVALUATION RESULTS (6-CLASS STRATIFIED)")
    print("="*60)
    print("Accuracy  : {:.4f}".format(acc))
    print("Precision : {:.4f}  (macro)".format(prec))
    print("Recall    : {:.4f}  (macro)".format(rec))
    print("F1-Score  : {:.4f}  (macro)".format(f1_mac))

    # Per-class report across all 6 classes
    print("\nPer-class classification report:")
    print(classification_report(
        y_test, y_pred,
        labels=all_label_indices,
        target_names=target_names,
        zero_division=0
    ))

    # Confusion matrix across all 6 classes
    cm = confusion_matrix(y_test, y_pred, labels=all_label_indices)
    print("Confusion Matrix (rows=actual, cols=predicted):")
    print("Classes:", target_names)
    print(cm)

    # Feature importances from the RF
    rf = pipeline.named_steps["classifier"]
    importances = dict(zip(FEATURE_COLS, rf.feature_importances_))
    top_features = sorted(importances.items(), key=lambda x: x[1], reverse=True)[:5]
    print("\nTop-5 feature importances:")
    for feat, imp in top_features:
        print("  {:25s} {:.4f}".format(feat, imp))

    metrics = {
        "accuracy":           acc,
        "precision_macro":    prec,
        "recall_macro":       rec,
        "f1_macro":           f1_mac,
        "train_samples":      int(len(train_df)),
        "test_samples":       int(len(test_df)),
        "confusion_matrix":   cm.tolist(),
        "class_names":        list(le.classes_),
        "feature_importances": importances,
    }

    # Per-class F1 scores mapped explicitly by label index
    per_class_f1 = f1_score(y_test, y_pred, labels=all_label_indices, average=None, zero_division=0)
    for i, cls in enumerate(le.classes_):
        metrics["f1_{}".format(cls)] = float(per_class_f1[i])

    return metrics, pipeline


# ---------------------------------------------------------------------------
# Step 7 — Generate probabilities for a single feature row
# ---------------------------------------------------------------------------

def predict_single(pipeline: Pipeline, le: LabelEncoder, features: dict) -> dict:
    """
    Run inference on a single feature row (as a dict).

    Parameters
    ----------
    pipeline : fitted sklearn Pipeline
    le       : fitted LabelEncoder
    features : dict  -- keys matching FEATURE_COLS

    Returns
    -------
    dict  -- {"predicted_class": str, "confidence_score": float,
               "probabilities": {class: float, ...}}
    """
    row = np.array([[features.get(c, 0.0) for c in FEATURE_COLS]])
    pred_encoded  = pipeline.predict(row)[0]
    probs         = pipeline.predict_proba(row)[0]

    predicted_class   = le.inverse_transform([pred_encoded])[0]
    confidence_score  = float(probs[pred_encoded])

    prob_dict = {cls: float(probs[i]) for i, cls in enumerate(le.classes_)}

    return {
        "predicted_class":  predicted_class,
        "confidence_score": round(confidence_score, 4),
        "probabilities":    {k: round(v, 4) for k, v in prob_dict.items()},
    }


# ---------------------------------------------------------------------------
# Step 8 — Save model + metadata
# ---------------------------------------------------------------------------

def save_model(pipeline: Pipeline, le: LabelEncoder, metrics: dict,
               out_path: str):
    """
    Save the fitted pipeline and metadata to disk.

    Saves two files:
        <out_path>          -- the joblib-serialised Pipeline
        <out_path>_meta.json -- label encoder classes + metrics

    Parameters
    ----------
    pipeline : fitted sklearn Pipeline
    le       : fitted LabelEncoder
    metrics  : dict  -- evaluation metrics from train_and_evaluate
    out_path : str   -- e.g. 'models/gait_model_v1.pkl'
    """
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)

    joblib.dump(pipeline, out_path)
    print("\n[save] Model saved to '{}'.".format(out_path))

    meta = {
        "label_classes":  list(le.classes_),
        "feature_columns": FEATURE_COLS,
        "valid_classes":  VALID_CLASSES,
        "metrics":        {k: v for k, v in metrics.items()
                           if not isinstance(v, (list, dict))},
        "model_name":     "random_forest_baseline",
        "model_version":  "1.0.0",
        "training_date":  datetime.now(timezone.utc).isoformat(),
        "confusion_matrix": metrics.get("confusion_matrix", []),
    }
    meta_path = str(out_path).replace(".pkl", "_meta.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    print("[save] Metadata saved to '{}'.".format(meta_path))


# ---------------------------------------------------------------------------
# Full pipeline entry point
# ---------------------------------------------------------------------------

def run_pipeline(csv_path: str, out_path: str = "models/gait_model_v1.pkl",
                 test_size: float = 0.2, n_estimators: int = 200,
                 max_depth=None, random_state: int = 42) -> dict:
    """
    End-to-end training pipeline.

    Steps:
        1. Load + validate CSV
        2. Handle missing values
        3. Encode labels
        4. Subject-wise train/test split
        5. Train Random Forest pipeline
        6. Evaluate (accuracy, precision, recall, F1, confusion matrix)
        7. Save model + metadata

    Returns
    -------
    dict  -- evaluation metrics
    """
    print("\n[pipeline] Starting gait classifier training pipeline ...")
    print("[pipeline] Input: {}".format(csv_path))
    print("[pipeline] Output: {}".format(out_path))

    df = load_and_validate(csv_path)
    df = handle_missing(df)
    df, le = encode_labels(df)

    train_df, test_df = split_by_subject(df, test_size, random_state)

    metrics, pipeline = train_and_evaluate(
        train_df, test_df, le, n_estimators, max_depth, random_state
    )

    save_model(pipeline, le, metrics, out_path)

    print("\n[pipeline] Done.")
    return metrics


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def _parse_args():
    p = argparse.ArgumentParser(
        description="Train a 6-class gait abnormality classifier."
    )
    p.add_argument("--csv",          required=True,
                   help="Path to feature CSV (gait_training_dataset.csv).")
    p.add_argument("--out",          default="models/gait_model_v1.pkl",
                   help="Output path for saved model.")
    p.add_argument("--test-size",    type=float, default=0.2)
    p.add_argument("--n-estimators", type=int,   default=200)
    p.add_argument("--max-depth",    type=int,   default=None)
    p.add_argument("--seed",         type=int,   default=42)
    return p.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    result = run_pipeline(
        csv_path=args.csv,
        out_path=args.out,
        test_size=args.test_size,
        n_estimators=args.n_estimators,
        max_depth=args.max_depth,
        random_state=args.seed,
    )
    print("\nSummary metrics:")
    for k, v in result.items():
        if isinstance(v, float):
            print("  {:25s} {:.4f}".format(k, v))
