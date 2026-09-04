#!/usr/bin/env python
"""
pipeline_demo.py  —  End-to-end pipeline walkthrough
=====================================================
This self-contained script:
  1. Generates synthetic sensor data (two subjects, normal vs. abnormal gait).
  2. Runs the full preprocessing pipeline.
  3. Detects gait events and segments windows.
  4. Extracts features and builds an ML dataset.
  5. Trains a Random Forest classifier.
  6. Evaluates it and prints metrics.
  7. Runs inference on a new (unseen) recording.

No real sensor files are required — run this immediately after cloning
to verify that every module works together.

Usage
-----
    # From the project root (gait-abnormality-system/)
    cd src
    python ../notebooks/pipeline_demo.py
"""

import sys
import os
import tempfile
import json
from pathlib import Path

import numpy as np
import pandas as pd

# ------------------------------------------------------------------
# Make src/ importable regardless of where the script is invoked from
# ------------------------------------------------------------------
SRC_DIR = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC_DIR))

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# ------------------------------------------------------------------
# 1. Synthetic data generator
# ------------------------------------------------------------------

def make_synthetic_recording(
    n_seconds: float,
    label: str,
    sampling_rate: int = 100,
    seed: int = 0,
) -> pd.DataFrame:
    """
    Generate a synthetic 6-axis sensor recording with embedded step events.

    Normal gait  — regular periodic peaks, low variance.
    Abnormal gait — irregular peak timing, higher noise level.
    """
    rng = np.random.default_rng(seed)
    n = int(n_seconds * sampling_rate)
    t = np.arange(n) / sampling_rate                       # seconds

    if label == "normal":
        step_freq   = 1.8                                   # ~108 steps/min
        noise_scale = 0.3
        amp         = 9.81
    else:
        step_freq   = 1.2 + rng.uniform(-0.4, 0.4)        # irregular
        noise_scale = 1.2
        amp         = 9.81 * rng.uniform(0.7, 1.1)

    # Simulated acceleration: dominant vertical axis (acc_z) contains steps
    step_signal = amp * np.abs(np.sin(2 * np.pi * step_freq * t))

    acc_x = rng.normal(0,   noise_scale, n)
    acc_y = rng.normal(0,   noise_scale, n)
    acc_z = step_signal + rng.normal(0, noise_scale * 0.5, n)

    gyro_x = rng.normal(0, 0.5 + (noise_scale * 0.3), n)
    gyro_y = rng.normal(0, 0.5 + (noise_scale * 0.3), n)
    gyro_z = rng.normal(0, 0.3 + (noise_scale * 0.2), n)

    timestamps = pd.date_range("2024-01-01", periods=n, freq=f"{1000//sampling_rate}ms")

    return pd.DataFrame({
        "timestamp": timestamps,
        "acc_x":  acc_x,
        "acc_y":  acc_y,
        "acc_z":  acc_z,
        "gyro_x": gyro_x,
        "gyro_y": gyro_y,
        "gyro_z": gyro_z,
        "label":  label,
    })


def save_csv(df: pd.DataFrame, path: Path) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    return str(path)


# ------------------------------------------------------------------
# 2. Main pipeline
# ------------------------------------------------------------------

def main():
    print("\n" + "=" * 60)
    print("  GAIT ABNORMALITY CLASSIFICATION — END-TO-END DEMO")
    print("=" * 60)

    # ── Step 1: Generate & save synthetic recordings ─────────────
    print("\n[1/7] Generating synthetic sensor recordings …")

    recordings = []
    labels     = []
    subject_ids = []

    raw_dir = PROJECT_ROOT / "data" / "raw"

    config = [
        # (subject_id, label,      seconds, seed)
        (0,  "normal",   60,  10),
        (0,  "normal",   60,  11),
        (1,  "normal",   60,  20),
        (2,  "abnormal", 60,  30),
        (2,  "abnormal", 60,  31),
        (3,  "abnormal", 60,  40),
        (4,  "normal",   60,  50),
        (5,  "abnormal", 60,  60),
    ]

    for subj, lbl, secs, seed in config:
        df = make_synthetic_recording(secs, lbl, seed=seed)
        csv_path = save_csv(df, raw_dir / f"subject_{subj:02d}_{lbl}_{seed}.csv")
        recordings.append(csv_path)
        labels.append(lbl)
        subject_ids.append(subj)
        print(f"   Saved: {csv_path}  ({lbl}, subject={subj}, {secs}s)")

    # ── Step 2: Preprocessing demo ───────────────────────────────
    print("\n[2/7] Preprocessing a single recording (demo) …")
    from preprocessing import run_preprocessing_pipeline

    df_raw = pd.read_csv(recordings[0])
    print(f"   Raw shape        : {df_raw.shape}")

    df_clean = run_preprocessing_pipeline(recordings[0], apply_filter=True)
    print(f"   Preprocessed shape: {df_clean.shape}")
    print(f"   Columns          : {list(df_clean.columns)}")

    # ── Step 3: Gait detection demo ──────────────────────────────
    print("\n[3/7] Running gait detection …")
    from gait_detection import compute_magnitude, detect_steps, segment_windows

    df_mag = compute_magnitude(df_clean)
    peaks, props = detect_steps(df_mag["acc_mag"].values)
    print(f"   acc_mag range    : [{df_mag['acc_mag'].min():.2f}, {df_mag['acc_mag'].max():.2f}]")
    print(f"   Steps detected   : {len(peaks)}")

    windows = segment_windows(df_mag, window_size_seconds=5.0)
    print(f"   Windows (5 s)    : {len(windows)}")

    # ── Step 4: Feature extraction ───────────────────────────────
    print("\n[4/7] Extracting features for all recordings …")
    from feature_extraction import build_feature_dataset

    feature_df = build_feature_dataset(
        recordings,
        labels=labels,
        subject_ids=subject_ids,
    )
    proc_dir = PROJECT_ROOT / "data" / "processed"
    proc_dir.mkdir(parents=True, exist_ok=True)
    features_csv = str(proc_dir / "features.csv")
    feature_df.to_csv(features_csv, index=False)

    print(f"   Feature table shape : {feature_df.shape}")
    print(f"   Feature columns (first 5): {list(feature_df.columns[:5])}")
    print(f"   Label distribution  :\n{feature_df['label'].value_counts().to_string()}")
    print(f"   Saved to: {features_csv}")

    # ── Step 5: Training ─────────────────────────────────────────
    print("\n[5/7] Training Random Forest classifier …")
    from train_model import train_and_save

    models_dir = PROJECT_ROOT / "models"
    model_path = str(models_dir / "gait_model.pkl")

    train_result = train_and_save(
        feature_csv=features_csv,
        model_out=model_path,
        n_estimators=100,
        test_size=0.25,
        use_scaler=True,
    )
    print(f"   Train accuracy : {train_result['train_accuracy']:.4f}")
    print(f"   Test accuracy  : {train_result['test_accuracy']:.4f}")
    print(f"   # features     : {len(train_result['feature_columns'])}")

    # ── Step 6: Evaluation ───────────────────────────────────────
    print("\n[6/7] Evaluating model …")
    from evaluation import evaluate_from_files

    metrics = evaluate_from_files(
        model_path=model_path,
        test_csv=features_csv,
        target_names=["abnormal", "normal"],
        print_report=True,
        print_importances=True,
        top_n_importances=10,
    )

    # Save confusion matrix to reports/
    reports_dir = PROJECT_ROOT / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    cm_path = reports_dir / "confusion_matrix.csv"
    pd.DataFrame(
        metrics["confusion_matrix"],
        index=["True abnormal", "True normal"],
        columns=["Pred abnormal", "Pred normal"],
    ).to_csv(cm_path)
    print(f"\n   Confusion matrix saved to: {cm_path}")

    # ── Step 7: Inference on new recording ───────────────────────
    print("\n[7/7] Running inference on a new unseen recording …")

    # Generate a new recording (not in training set)
    unseen_df = make_synthetic_recording(30, "normal", seed=999)
    unseen_path = PROJECT_ROOT / "data" / "raw" / "unseen_subject_normal.csv"
    save_csv(unseen_df.drop(columns=["label"]), unseen_path)  # no label!

    from prediction import predict_from_csv

    result = predict_from_csv(str(unseen_path), model_path)
    print(f"   Predicted label : {result['predicted_label']}")
    print(f"   Probabilities   : {json.dumps(result['probabilities'], indent=4)}")
    print(f"   Steps detected  : {result['n_steps_detected']}")

    print("\n" + "=" * 60)
    print("  PIPELINE COMPLETED SUCCESSFULLY")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
