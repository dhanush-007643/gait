"""
prediction.py
=============
Inference module: loads a trained pipeline and runs predictions on new,
unseen sensor recordings.

Designed to be called from an API endpoint, a CLI, or a notebook.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
import joblib


# ---------------------------------------------------------------------------
# Model loading
# ---------------------------------------------------------------------------

def load_model(model_path: str):
    """
    Load a trained scikit-learn pipeline from disk.

    Parameters
    ----------
    model_path : str
        Path to the ``.pkl`` file saved by ``train_model.train_and_save``.

    Returns
    -------
    sklearn.pipeline.Pipeline
        Loaded, fitted pipeline ready for inference.

    Raises
    ------
    FileNotFoundError
        If ``model_path`` does not exist.
    """
    if not Path(model_path).exists():
        raise FileNotFoundError(f"Model not found at: {model_path}")
    return joblib.load(model_path)


def load_feature_columns(model_path: str) -> Optional[List[str]]:
    """
    Load the ordered feature column list saved alongside the model.

    During training, ``train_model.train_and_save`` writes a
    ``<model_name>_meta.json`` file next to the ``.pkl`` file with the
    exact feature column names and order used at fit time. This function
    reads that file so that inference input is aligned correctly.

    Parameters
    ----------
    model_path : str
        Path to the ``.pkl`` model file (companion ``_meta.json`` must be
        in the same directory).

    Returns
    -------
    list of str or None
        Ordered feature column names, or ``None`` if the meta file is absent.
    """
    meta_path = str(model_path).replace(".pkl", "_meta.json")
    if not Path(meta_path).exists():
        return None
    with open(meta_path) as f:
        meta = json.load(f)
    return meta.get("feature_columns")


# ---------------------------------------------------------------------------
# Core prediction
# ---------------------------------------------------------------------------

def predict(
    model,
    feature_row: Union[Dict[str, float], pd.Series, pd.DataFrame],
    feature_columns: Optional[List[str]] = None,
) -> Tuple[object, Dict[str, float]]:
    """
    Run prediction on a single feature row (or a batch DataFrame) and return
    the predicted class label(s) together with class probabilities.

    Parameters
    ----------
    model : fitted sklearn Pipeline
        Trained pipeline returned by ``load_model``.
    feature_row : dict, pd.Series, or pd.DataFrame
        * **dict / Series** — a single observation (one recording / window).
          Key / index names must match the training feature columns.
        * **DataFrame** — a batch of observations (rows = samples,
          columns = features).
    feature_columns : list of str, optional
        If provided, reorders / selects columns from ``feature_row`` to
        exactly match the training feature order.  Strongly recommended
        when using a dict or an unordered DataFrame.

    Returns
    -------
    predicted_label : scalar or np.ndarray
        * Scalar class label for a single-row input.
        * 1-D array of labels for a DataFrame batch input.
    probabilities : dict or list of dict
        * For a single row: ``{class_label: probability, ...}``.
        * For a batch: list of such dicts (one per row).

    Raises
    ------
    ValueError
        If required feature columns are missing from ``feature_row``.
    """
    # --- Normalise input to a 2-D DataFrame ---
    if isinstance(feature_row, dict):
        df_input = pd.DataFrame([feature_row])
        single = True
    elif isinstance(feature_row, pd.Series):
        df_input = feature_row.to_frame().T.reset_index(drop=True)
        single = True
    elif isinstance(feature_row, pd.DataFrame):
        df_input = feature_row.reset_index(drop=True)
        single = len(df_input) == 1
    else:
        raise TypeError(
            f"feature_row must be a dict, pd.Series, or pd.DataFrame, "
            f"got {type(feature_row)}."
        )

    # --- Align columns ---
    if feature_columns is not None:
        missing = [c for c in feature_columns if c not in df_input.columns]
        if missing:
            raise ValueError(
                f"predict: feature_row is missing {len(missing)} required "
                f"column(s): {missing[:10]}{'...' if len(missing) > 10 else ''}"
            )
        df_input = df_input[feature_columns]

    # --- Predict ---
    y_pred = model.predict(df_input)

    classes = model.classes_ if hasattr(model, "classes_") else (
        model.named_steps["classifier"].classes_
        if hasattr(model, "named_steps") else None
    )

    if hasattr(model, "predict_proba"):
        proba_matrix = model.predict_proba(df_input)
    else:
        # Fallback: one-hot
        proba_matrix = np.eye(len(classes))[
            [list(classes).index(p) for p in y_pred]
        ]

    # --- Format probabilities ---
    if classes is not None:
        prob_dicts = [
            {str(cls): float(p) for cls, p in zip(classes, row)}
            for row in proba_matrix
        ]
    else:
        prob_dicts = [
            {f"class_{i}": float(p) for i, p in enumerate(row)}
            for row in proba_matrix
        ]

    if single:
        return y_pred[0], prob_dicts[0]
    return y_pred, prob_dicts


# ---------------------------------------------------------------------------
# End-to-end inference from a raw CSV
# ---------------------------------------------------------------------------

def predict_from_csv(
    csv_path: str,
    model_path: str,
    sampling_rate_hz: float = 100.0,
) -> dict:
    """
    Full inference pipeline: load a raw sensor CSV → preprocess → extract
    features → predict.

    Parameters
    ----------
    csv_path : str
        Path to a raw sensor CSV (same format as training data, ``label``
        column optional — ignored if present).
    model_path : str
        Path to the trained ``.pkl`` model file.
    sampling_rate_hz : float
        Sensor sampling rate in Hz.

    Returns
    -------
    dict with keys:
        ``"predicted_label"`` — the predicted class (e.g., ``"normal"``)
        ``"probabilities"``   — ``{class_label: probability}`` dict
        ``"n_steps_detected"``— number of steps detected in the recording
    """
    # Import here to avoid circular imports at module level
    sys.path.insert(0, str(Path(__file__).parent))
    from preprocessing import run_preprocessing_pipeline
    from gait_detection import compute_magnitude, detect_steps
    from feature_extraction import extract_6class_features

    df = run_preprocessing_pipeline(csv_path, sampling_rate_hz=sampling_rate_hz)
    df = compute_magnitude(df)
    features = extract_6class_features(df, sampling_rate_hz=sampling_rate_hz)

    model = load_model(model_path)
    feature_columns = load_feature_columns(model_path)

    label, probs = predict(model, features, feature_columns=feature_columns)

    # In single prediction, label might be integer or string
    meta_path = str(model_path).replace(".pkl", "_meta.json")
    meta = {}
    if Path(meta_path).exists():
        with open(meta_path) as f:
            meta = json.load(f)
            label_classes = meta.get("label_classes", [])
            if isinstance(label, (int, np.integer)) and 0 <= label < len(label_classes):
                label = label_classes[label]

    # Normalize probability keys if classes were integer indices
    formatted_probs = {}
    for k, v in probs.items():
        if str(k).isdigit() and int(k) < len(meta.get("label_classes", [])):
            formatted_probs[meta["label_classes"][int(k)]] = float(v)
        else:
            formatted_probs[str(k)] = float(v)

    confidence = float(max(formatted_probs.values())) if formatted_probs else 1.0

    return {
        "predicted_label":  str(label),
        "predicted_class":  str(label),
        "confidence_score": round(confidence, 4),
        "probabilities":    formatted_probs,
        "features":         features,
        "n_steps_detected": int(features.get("step_count", 0)),
    }



# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Run gait classification inference on a sensor CSV file."
    )
    parser.add_argument("--csv",    required=True, help="Path to input sensor CSV.")
    parser.add_argument("--model",  required=True, help="Path to trained model .pkl.")
    parser.add_argument("--rate",   type=float, default=100.0,
                        help="Sensor sampling rate in Hz (default: 100).")
    args = parser.parse_args()

    result = predict_from_csv(args.csv, args.model, sampling_rate_hz=args.rate)
    print(json.dumps(result, indent=2))
