# -*- coding: utf-8 -*-
"""
generate_upload_csv.py
======================
Generates realistic, ready-to-upload wearable sensor CSV files for the GaitInsight platform.

Columns:
  timestamp, acc_x, acc_y, acc_z, gyro_x, gyro_y, gyro_z
"""

import os
import sys
from pathlib import Path
import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parent.parent.parent

def generate_sensor_recording(
    duration_s: float = 30.0,
    sampling_rate_hz: float = 100.0,
    gait_type: str = "normal"
) -> pd.DataFrame:
    n_samples = int(duration_s * sampling_rate_hz)
    t = np.linspace(0, duration_s, n_samples)
    
    # Timestamps
    base_ts = pd.Timestamp("2024-01-01 00:00:00")
    timestamps = [base_ts + pd.Timedelta(milliseconds=i * (1000.0 / sampling_rate_hz)) for i in range(n_samples)]
    ts_strings = [ts.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] for ts in timestamps]
    
    rng = np.random.RandomState(42 if gait_type == "normal" else (101 if gait_type == "parkinsonian" else 202))
    
    if gait_type == "normal":
        step_freq = 1.85  # ~111 steps/min
        acc_x = 0.45 * np.sin(2 * np.pi * step_freq * t) + rng.normal(0, 0.08, n_samples)
        acc_y = 0.35 * np.cos(2 * np.pi * step_freq * t) + rng.normal(0, 0.08, n_samples)
        acc_z = 9.81 + 2.2 * np.sin(2 * np.pi * 2 * step_freq * t) + rng.normal(0, 0.15, n_samples)
        
        gyro_x = 0.35 * np.cos(2 * np.pi * step_freq * t) + rng.normal(0, 0.05, n_samples)
        gyro_y = 0.25 * np.sin(2 * np.pi * step_freq * t) + rng.normal(0, 0.05, n_samples)
        gyro_z = 0.15 * np.sin(2 * np.pi * 2 * step_freq * t) + rng.normal(0, 0.03, n_samples)
        
    elif gait_type == "parkinsonian":
        # Festinating gait: higher cadence, lower vertical displacement, shuffling
        step_freq = 2.45  # ~147 steps/min
        acc_x = 0.20 * np.sin(2 * np.pi * step_freq * t) + rng.normal(0, 0.12, n_samples)
        acc_y = 0.15 * np.cos(2 * np.pi * step_freq * t) + rng.normal(0, 0.10, n_samples)
        acc_z = 9.81 + 0.95 * np.sin(2 * np.pi * 2 * step_freq * t) + rng.normal(0, 0.20, n_samples)
        
        gyro_x = 0.15 * np.cos(2 * np.pi * step_freq * t) + rng.normal(0, 0.08, n_samples)
        gyro_y = 0.12 * np.sin(2 * np.pi * step_freq * t) + rng.normal(0, 0.07, n_samples)
        gyro_z = 0.08 * np.sin(2 * np.pi * 2 * step_freq * t) + rng.normal(0, 0.05, n_samples)
        
    else:  # ataxic / irregular
        step_freq = 1.6
        jitter = rng.normal(0, 0.35, n_samples)
        acc_x = 0.85 * np.sin(2 * np.pi * step_freq * t + jitter) + rng.normal(0, 0.25, n_samples)
        acc_y = 0.70 * np.cos(2 * np.pi * step_freq * t) + rng.normal(0, 0.20, n_samples)
        acc_z = 9.81 + 3.1 * np.sin(2 * np.pi * 2 * step_freq * t) + rng.normal(0, 0.40, n_samples)
        
        gyro_x = 0.65 * np.cos(2 * np.pi * step_freq * t) + rng.normal(0, 0.15, n_samples)
        gyro_y = 0.55 * np.sin(2 * np.pi * step_freq * t) + rng.normal(0, 0.12, n_samples)
        gyro_z = 0.35 * np.sin(2 * np.pi * 2 * step_freq * t) + rng.normal(0, 0.10, n_samples)

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
    samples = [
        ("sample_gait_upload.csv", "normal", 30.0),
        ("sample_normal_gait.csv", "normal", 30.0),
        ("sample_parkinsonian_gait.csv", "parkinsonian", 30.0),
        ("sample_ataxic_gait.csv", "ataxic", 30.0),
    ]
    
    created_paths = []
    for fname, gtype, dur in samples:
        df = generate_sensor_recording(duration_s=dur, gait_type=gtype)
        
        # Save to root workspace directory
        root_path = _ROOT / fname
        df.to_csv(root_path, index=False)
        created_paths.append(root_path)
        
        # Also save to data/raw for convenience
        raw_path = _ROOT / "gait-abnormality-system" / "data" / "raw" / fname
        df.to_csv(raw_path, index=False)
        
        print(f"[Upload CSV Generator] Created: {root_path} ({len(df)} rows, ~{dur}s at 100Hz)")
        
    return created_paths

if __name__ == "__main__":
    create_all_upload_samples()
