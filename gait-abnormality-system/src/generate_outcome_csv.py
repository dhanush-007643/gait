# -*- coding: utf-8 -*-
"""
generate_outcome_csv.py
=======================
Generates comprehensive classification outcome CSV files for:
  1. Raw sensor recordings in data/raw/*.csv
  2. Training & validation dataset sessions in data/processed/gait_training_dataset.csv
  3. Database recorded sessions

Outputs generated:
  - reports/gait_classification_outcomes.csv
  - data/processed/outcomes.csv
  - outcome.csv (in project root for easy access)
"""

import os
import sys
import glob
import json
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
import numpy as np

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_SYS_DIR = _PROJECT_ROOT / "gait-abnormality-system"

sys.path.insert(0, str(_SYS_DIR / "src"))
sys.path.insert(0, str(_SYS_DIR / "app"))
sys.path.insert(0, str(_SYS_DIR / "db"))

from prediction import predict_from_csv, load_model, load_feature_columns, predict
from feature_extraction import extract_6class_features

def assess_risk(predicted_class: str, confidence: float) -> str:
    if predicted_class.lower() == "normal":
        return "Low Risk / Normal Gait"
    if confidence >= 0.70:
        return f"High Risk - {predicted_class.capitalize()} Pattern"
    return f"Moderate Risk - {predicted_class.capitalize()} Indicators"

def generate_all_outcomes():
    model_path = str(_SYS_DIR / "models" / "gait_model_v1.pkl")
    model = load_model(model_path)
    feature_cols = load_feature_columns(model_path)
    
    rows = []
    
    # 1. Process all raw CSV files
    raw_files = sorted(glob.glob(str(_SYS_DIR / "data" / "raw" / "*.csv")))
    print(f"[Outcome Generator] Found {len(raw_files)} raw sensor recordings.")
    
    for fpath in raw_files:
        fname = os.path.basename(fpath)
        subject_id = "SUB_" + fname.replace(".csv", "").upper()
        if "subject_" in fname:
            parts = fname.split("_")
            if len(parts) >= 2:
                subject_id = f"SUB_{parts[0]}_{parts[1]}".upper()
                
        try:
            res = predict_from_csv(fpath, model_path)
            feat = res.get("features", {})
            probs = res.get("probabilities", {})
            pred_cls = str(res.get("predicted_class", "normal"))
            conf = float(res.get("confidence_score", 0.0))
            
            row = {
                "record_type": "Raw IMU Recording",
                "source_file": fname,
                "subject_id": subject_id,
                "predicted_class": pred_cls,
                "is_abnormal": "Yes" if pred_cls != "normal" else "No",
                "confidence_score": round(conf, 4),
                "risk_assessment": assess_risk(pred_cls, conf),
                "prob_normal": round(float(probs.get("normal", 0.0)), 4),
                "prob_parkinsonian": round(float(probs.get("parkinsonian", 0.0)), 4),
                "prob_hemiplegic": round(float(probs.get("hemiplegic", 0.0)), 4),
                "prob_ataxic": round(float(probs.get("ataxic", 0.0)), 4),
                "prob_spastic": round(float(probs.get("spastic", 0.0)), 4),
                "prob_antalgic": round(float(probs.get("antalgic", 0.0)), 4),
                "duration_seconds": feat.get("duration", 0.0),
                "step_count": int(feat.get("step_count", 0)),
                "cadence_steps_per_min": feat.get("cadence", 0.0),
                "walking_speed_m_per_s": feat.get("walking_speed", 0.0),
                "step_length_m": feat.get("step_length", 0.0),
                "stride_length_m": feat.get("stride_length", 0.0),
                "step_time_s": feat.get("step_time", 0.0),
                "stride_time_s": feat.get("stride_time", 0.0),
                "stance_time_s": feat.get("stance_time", 0.0),
                "swing_time_s": feat.get("swing_time", 0.0),
                "gait_symmetry_ratio": feat.get("gait_symmetry", 0.0),
                "mean_acceleration_m_s2": feat.get("mean_acceleration", 0.0),
                "acceleration_std": feat.get("acceleration_std", 0.0),
                "acceleration_rms": feat.get("acceleration_rms", 0.0),
                "mean_gyroscope_rad_s": feat.get("mean_gyroscope", 0.0),
                "gyroscope_std": feat.get("gyroscope_std", 0.0),
                "evaluation_date": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            }
            rows.append(row)
            print(f"  Processed {fname} -> {pred_cls} ({conf*100:.1f}%)")
        except Exception as exc:
            print(f"  Error processing {fname}: {exc}")
            
    # 2. Process all sessions from dataset
    dataset_path = _SYS_DIR / "data" / "processed" / "gait_training_dataset.csv"
    if dataset_path.exists():
        df_ds = pd.read_csv(dataset_path)
        print(f"\n[Outcome Generator] Evaluating {len(df_ds)} sessions from dataset...")
        for idx, r in df_ds.iterrows():
            feat_dict = {c: r[c] for c in feature_cols if c in r}
            pred_label, probs = predict(model, feat_dict, feature_columns=feature_cols)
            
            # map numeric label if needed
            meta_path = str(model_path).replace(".pkl", "_meta.json")
            meta = {}
            if Path(meta_path).exists():
                with open(meta_path) as mf:
                    meta = json.load(mf)
            label_classes = meta.get("label_classes", ["normal", "parkinsonian", "hemiplegic", "ataxic", "spastic", "antalgic"])
            if isinstance(pred_label, (int, np.integer)) and 0 <= pred_label < len(label_classes):
                pred_cls = label_classes[pred_label]
            else:
                pred_cls = str(pred_label)
                
            formatted_probs = {}
            for k, v in probs.items():
                if str(k).isdigit() and int(k) < len(label_classes):
                    formatted_probs[label_classes[int(k)]] = float(v)
                else:
                    formatted_probs[str(k)] = float(v)
            conf = max(formatted_probs.values()) if formatted_probs else 1.0
            
            row = {
                "record_type": "Dataset Session",
                "source_file": r.get("session_id", f"SES_{idx+1:04d}"),
                "subject_id": r.get("subject_id", f"SUB_{idx+1:03d}"),
                "predicted_class": pred_cls,
                "is_abnormal": "Yes" if pred_cls != "normal" else "No",
                "confidence_score": round(conf, 4),
                "risk_assessment": assess_risk(pred_cls, conf),
                "prob_normal": round(float(formatted_probs.get("normal", 0.0)), 4),
                "prob_parkinsonian": round(float(formatted_probs.get("parkinsonian", 0.0)), 4),
                "prob_hemiplegic": round(float(formatted_probs.get("hemiplegic", 0.0)), 4),
                "prob_ataxic": round(float(formatted_probs.get("ataxic", 0.0)), 4),
                "prob_spastic": round(float(formatted_probs.get("spastic", 0.0)), 4),
                "prob_antalgic": round(float(formatted_probs.get("antalgic", 0.0)), 4),
                "duration_seconds": r.get("duration", 0.0),
                "step_count": int(r.get("step_count", 0)),
                "cadence_steps_per_min": r.get("cadence", 0.0),
                "walking_speed_m_per_s": r.get("walking_speed", 0.0),
                "step_length_m": r.get("step_length", 0.0),
                "stride_length_m": r.get("stride_length", 0.0),
                "step_time_s": r.get("step_time", 0.0),
                "stride_time_s": r.get("stride_time", 0.0),
                "stance_time_s": r.get("stance_time", 0.0),
                "swing_time_s": r.get("swing_time", 0.0),
                "gait_symmetry_ratio": r.get("gait_symmetry", 0.0),
                "mean_acceleration_m_s2": r.get("mean_acceleration", 0.0),
                "acceleration_std": r.get("acceleration_std", 0.0),
                "acceleration_rms": r.get("acceleration_rms", 0.0),
                "mean_gyroscope_rad_s": r.get("mean_gyroscope", 0.0),
                "gyroscope_std": r.get("gyroscope_std", 0.0),
                "evaluation_date": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            }
            rows.append(row)
            
    df_out = pd.DataFrame(rows)
    
    # Save destinations
    destinations = [
        _SYS_DIR / "reports" / "gait_classification_outcomes.csv",
        _SYS_DIR / "data" / "processed" / "classification_outcomes.csv",
        _PROJECT_ROOT / "outcome.csv",
    ]
    
    for dst in destinations:
        dst.parent.mkdir(parents=True, exist_ok=True)
        df_out.to_csv(dst, index=False)
        print(f"[Outcome Generator] Exported: {dst} ({len(df_out)} rows)")
        
    print("\nSummary of outcomes:")
    print(df_out["predicted_class"].value_counts())
    return df_out

if __name__ == "__main__":
    generate_all_outcomes()
