# -*- coding: utf-8 -*-
"""
generate_upload_csv.py
======================
Generates realistic, calibrated wearable sensor CSV files for the GaitInsight platform.
Produces verified sample CSV files for all 6 gait classes:
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

def generate_signal_for_class(gtype: str, duration_s: float = 30.0, fs: float = 100.0, seed: int = 42) -> pd.DataFrame:
    """
    Generate authentic triaxial accelerometer and gyroscope IMU time series
    for a specific gait pattern.
    """
    n = int(duration_s * fs)
    t = np.linspace(0, duration_s, n)
    rng = np.random.RandomState(seed)
    base_ts = pd.Timestamp("2024-01-01 00:00:00")
    timestamps = [base_ts + pd.Timedelta(milliseconds=i * (1000.0 / fs)) for i in range(n)]
    ts_strings = [ts.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] for ts in timestamps]
    
    if gtype == "normal":
        # Cadence ~112 spm, high symmetry ~0.96, moderate smooth acceleration
        freq = 1.867
        acc_x = 0.55 * np.sin(2 * np.pi * (freq / 2.0) * t) + rng.normal(0, 0.05, n)
        acc_y = 0.40 * np.cos(2 * np.pi * (freq / 2.0) * t) + rng.normal(0, 0.05, n)
        acc_z = 9.81 + 1.25 * np.sin(2 * np.pi * freq * t) + rng.normal(0, 0.08, n)
        gyro_x = 0.25 * np.sin(2 * np.pi * (freq / 2.0) * t) + rng.normal(0, 0.05, n)
        gyro_y = 0.30 * np.cos(2 * np.pi * freq * t) + rng.normal(0, 0.05, n)
        gyro_z = 0.15 * np.sin(2 * np.pi * (freq / 2.0) * t) + rng.normal(0, 0.03, n)
        
    elif gtype == "parkinsonian":
        # Rapid festinating cadence ~132 spm, reduced arm swing, shuffling
        freq = 2.20
        acc_x = 0.60 * np.sin(2 * np.pi * (freq / 2.0) * t) + rng.normal(0, 0.20, n)
        acc_y = 0.50 * np.cos(2 * np.pi * (freq / 2.0) * t) + rng.normal(0, 0.20, n)
        acc_z = 8.83 + 1.80 * np.sin(2 * np.pi * freq * t) + rng.normal(0, 0.45, n)
        gyro_x = 0.45 * np.sin(2 * np.pi * (freq / 2.0) * t) + rng.normal(0, 0.18, n)
        gyro_y = 0.55 * np.cos(2 * np.pi * freq * t) + rng.normal(0, 0.18, n)
        gyro_z = 0.25 * np.sin(2 * np.pi * (freq / 2.0) * t) + rng.normal(0, 0.10, n)
        
    elif gtype == "antalgic":
        # Limp with shortened stance on painful limb, cadence ~84 spm, asymmetric step times
        stride_period = 2.0 / 1.40
        phi = (t % stride_period) / stride_period
        warped_phase = np.where(phi < 0.60, phi / 0.60 * np.pi, np.pi + (phi - 0.60) / 0.40 * np.pi)
        
        acc_x = 0.70 * np.sin(warped_phase) + rng.normal(0, 0.12, n)
        acc_y = 0.55 * np.cos(warped_phase) + rng.normal(0, 0.12, n)
        acc_z = 9.26 + 1.70 * np.sin(2 * warped_phase) + rng.normal(0, 0.25, n)
        gyro_x = 0.40 * np.sin(warped_phase) + rng.normal(0, 0.12, n)
        gyro_y = 0.45 * np.cos(2 * warped_phase) + rng.normal(0, 0.12, n)
        gyro_z = 0.20 * np.sin(warped_phase) + rng.normal(0, 0.08, n)
        
    elif gtype == "ataxic":
        # Uncoordinated cerebellar ataxia, high kinematic variance and high gyro jitter
        freq = 1.24
        jitter = np.cumsum(rng.normal(0, 0.10, n))
        acc_x = 2.50 * np.sin(2 * np.pi * (freq / 2.0) * t + jitter) + rng.normal(0, 1.10, n)
        acc_y = 2.20 * np.cos(2 * np.pi * (freq / 2.0) * t) + rng.normal(0, 1.10, n)
        acc_z = 8.21 + 4.20 * np.sin(2 * np.pi * freq * t + jitter) + rng.normal(0, 1.50, n)
        gyro_x = 1.30 * np.sin(2 * np.pi * (freq / 2.0) * t) + rng.normal(0, 0.60, n)
        gyro_y = 1.50 * np.cos(2 * np.pi * freq * t) + rng.normal(0, 0.60, n)
        gyro_z = 0.90 * np.sin(2 * np.pi * (freq / 2.0) * t) + rng.normal(0, 0.40, n)
        
    elif gtype == "hemiplegic":
        # Unilateral weakness / circumduction, severe step time asymmetry, slow cadence ~66 spm
        stride_period = 2.0 / 1.095
        phi = (t % stride_period) / stride_period
        step1 = np.exp(-((phi - 0.12) ** 2) / (2 * 0.04 ** 2))
        step2 = 0.85 * np.exp(-((phi - 0.77) ** 2) / (2 * 0.06 ** 2))
        z_wave = 5.2 * (step1 + step2) - 1.8
        
        acc_x = 2.40 * np.sin(2 * np.pi * (1.095 / 2.0) * t) * (0.6 + step1) + rng.normal(0, 0.45, n)
        acc_y = 1.90 * np.cos(2 * np.pi * (1.095 / 2.0) * t) + rng.normal(0, 0.40, n)
        acc_z = 8.15 + z_wave + rng.normal(0, 0.50, n)
        gyro_x = 1.20 * np.sin(2 * np.pi * (1.095 / 2.0) * t) + rng.normal(0, 0.35, n)
        gyro_y = 1.35 * np.cos(2 * np.pi * 1.095 * t) + rng.normal(0, 0.35, n)
        gyro_z = 0.75 * np.sin(2 * np.pi * (1.095 / 2.0) * t) + rng.normal(0, 0.25, n)
        
    elif gtype == "spastic":
        # Hypertonic stiffness / scissoring, cadence ~75 spm, reduced swing
        freq = 1.253
        acc_x = 1.50 * np.sin(2 * np.pi * (freq / 2.0) * t) + rng.normal(0, 0.35, n)
        acc_y = 1.20 * np.cos(2 * np.pi * (freq / 2.0) * t) + rng.normal(0, 0.30, n)
        acc_z = 9.37 + 2.50 * np.sin(2 * np.pi * freq * t) + rng.normal(0, 0.55, n)
        gyro_x = 0.80 * np.sin(2 * np.pi * (freq / 2.0) * t) + rng.normal(0, 0.25, n)
        gyro_y = 0.85 * np.cos(2 * np.pi * freq * t) + rng.normal(0, 0.25, n)
        gyro_z = 0.40 * np.sin(2 * np.pi * (freq / 2.0) * t) + rng.normal(0, 0.15, n)
        
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
    
    file_configs = [
        ("sample_normal_gait.csv",           "normal"),
        ("sample_gait_upload.csv",           "normal"),
        ("sample_parkinsonian_gait.csv",     "parkinsonian"),
        ("sample_abnormal_parkinsonian.csv", "parkinsonian"),
        ("sample_antalgic_gait.csv",         "antalgic"),
        ("sample_abnormal_antalgic.csv",      "antalgic"),
        ("sample_ataxic_gait.csv",            "ataxic"),
        ("sample_abnormal_ataxic.csv",        "ataxic"),
        ("sample_hemiplegic_gait.csv",        "hemiplegic"),
        ("sample_abnormal_hemiplegic.csv",    "hemiplegic"),
        ("sample_spastic_gait.csv",           "spastic"),
        ("sample_abnormal_spastic.csv",       "spastic"),
    ]
    
    print("\n" + "="*80)
    print("Generating & Calibrating Sensor CSV Files for All 6 Gait Classes")
    print("="*80)
    
    for fname, gtype in file_configs:
        df = generate_signal_for_class(gtype, duration_s=30.0, fs=100.0)
        
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
        cadence = res.get("features", {}).get("cadence", 0.0)
        symmetry = res.get("features", {}).get("gait_symmetry", 0.0)
        
        status_label = "NORMAL" if pred == "normal" else f"ABNORMAL ({pred.upper()})"
        match_icon = "[OK]" if pred == gtype else "[FAIL]"
        print(f"{match_icon} File: {fname:32s} -> Target: {gtype.upper():12s} | Pred: {status_label:22s} (Conf: {conf:.1%}) [Cad: {cadence:.1f}, Sym: {symmetry:.2f}]")
        
    print("="*80 + "\n")

if __name__ == "__main__":
    create_all_upload_samples()
