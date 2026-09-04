# -*- coding: utf-8 -*-
"""
generate_upload_csv.py
======================
Generates realistic, calibrated wearable sensor CSV files for the GaitInsight platform.
Produces distinct, verified sample CSV files for all 6 gait classes:
  - Normal
  - Parkinsonian
  - Ataxic
  - Hemiplegic
  - Spastic
  - Antalgic
"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parent.parent.parent
_SYS_DIR = _ROOT / "gait-abnormality-system"

sys.path.insert(0, str(_SYS_DIR / "src"))
from feature_extraction import extract_6class_features
from gait_detection import compute_magnitude
from prediction import predict_from_csv, load_model, load_feature_columns, predict

def generate_calibrated_signal(
    target_cadence: float,
    target_symmetry: float,
    target_acc_std: float,
    duration_s: float = 30.0,
    sampling_rate_hz: float = 100.0,
    seed: int = 42
) -> pd.DataFrame:
    n = int(duration_s * sampling_rate_hz)
    t = np.linspace(0, duration_s, n)
    rng = np.random.RandomState(seed)
    
    # Timestamps
    base_ts = pd.Timestamp("2024-01-01 00:00:00")
    timestamps = [base_ts + pd.Timedelta(milliseconds=i * (1000.0 / sampling_rate_hz)) for i in range(n)]
    ts_strings = [ts.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] for ts in timestamps]
    
    # Calculate step intervals
    step_freq = target_cadence / 60.0
    mean_step_time = 1.0 / step_freq
    target_std_step = (1.0 - target_symmetry) * mean_step_time
    delta = target_std_step * 1.414
    
    step_times = []
    cur = 0.5
    toggle = True
    while cur < duration_s - 0.5:
        step_times.append(cur)
        dt = mean_step_time + (delta if toggle else -delta)
        cur += max(0.25, dt)
        toggle = not toggle
        
    # Background baseline signals
    noise_scale = max(0.2, target_acc_std * 0.45)
    acc_x = rng.normal(0, noise_scale * 0.5, n)
    acc_y = rng.normal(0, noise_scale * 0.4, n)
    acc_z = 9.81 + rng.normal(0, noise_scale * 0.8, n)
    
    # Add step impact peaks
    for st in step_times:
        idx = int(st * sampling_rate_hz)
        if 0 <= idx < n:
            acc_z[max(0, idx-2):min(n, idx+3)] += target_acc_std * 2.2
            acc_x[max(0, idx-2):min(n, idx+3)] += target_acc_std * 0.8
            
    gyro_x = rng.normal(0, 0.25, n)
    gyro_y = rng.normal(0, 0.20, n)
    gyro_z = rng.normal(0, 0.15, n)
    
    df = pd.DataFrame({
        "timestamp": ts_strings,
        "acc_x": np.round(acc_x, 6),
        "acc_y": np.round(acc_y, 6),
        "acc_z": np.round(acc_z, 6),
        "gyro_x": np.round(gyro_x, 6),
        "gyro_y": np.round(gyro_y, 6),
        "gyro_z": np.round(gyro_z, 6),
    })
    return df

def create_all_upload_samples():
    model_path = str(_SYS_DIR / "models" / "gait_model_v1.pkl")
    
    # Target biomechanical profiles matching the 6 trained gait patterns
    profiles = [
        ("sample_normal_gait.csv",           112.5, 0.96, 0.95, "normal"),
        ("sample_gait_upload.csv",           112.5, 0.96, 0.95, "normal"),
        ("sample_abnormal_parkinsonian.csv", 135.0, 0.77, 2.35, "parkinsonian"),
        ("sample_abnormal_ataxic.csv",        74.5, 0.64, 3.70, "ataxic"),
        ("sample_abnormal_hemiplegic.csv",    65.0, 0.53, 3.05, "hemiplegic"),
        ("sample_abnormal_spastic.csv",       75.0, 0.68, 2.57, "spastic"),
        ("sample_abnormal_antalgic.csv",      83.5, 0.72, 1.75, "antalgic"),
        ("sample_parkinsonian_gait.csv",     135.0, 0.77, 2.35, "parkinsonian"),
        ("sample_ataxic_gait.csv",            74.5, 0.64, 3.70, "ataxic"),
    ]
    
    print("\n" + "="*75)
    print("Generating & Calibrating Sensor CSV Files for All 6 Gait Classes")
    print("="*75)
    
    for fname, cad, sym, std, target_name in profiles:
        df = generate_calibrated_signal(cad, sym, std, duration_s=30.0, sampling_rate_hz=100.0)
        
        # Save to root workspace directory
        root_path = _ROOT / fname
        df.to_csv(root_path, index=False)
        
        # Also save to data/raw
        raw_path = _SYS_DIR / "data" / "raw" / fname
        df.to_csv(raw_path, index=False)
        
        # Run prediction
        res = predict_from_csv(str(root_path), model_path)
        pred = res.get("predicted_class", "unknown")
        conf = res.get("confidence_score", 0.0)
        
        status_label = "NORMAL" if pred == "normal" else f"ABNORMAL ({pred.upper()})"
        print(f"File: {fname:28s} -> Prediction: {status_label:24s} (Confidence: {conf:.1%})")
        
    print("="*75 + "\n")

if __name__ == "__main__":
    create_all_upload_samples()
