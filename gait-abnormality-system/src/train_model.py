"""
train_model.py
==============
Trains a Random Forest classifier on the extracted feature dataset and
persists the trained model (and optional scaler) to disk.

Subject-wise (group-based) splitting is used when a ``subject_id`` column
is present, preventing data leakage across recordings from the same participant.

Usage (CLI)
-----------
    python train_model.py --features data/processed/features.csv \
                          --model-out models/gait_model.pkl

Usage (module)
--------------
    from train_model import train_and_save
    report = train_and_save("data/processed/features.csv",
                            "models/gait_model.pkl")
"""

import argparse
import os
import sys
import json
from pathlib import Path
from typing import Tuple, Optional

import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GroupShuffleSplit, train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_feature_dataset(filepath: str) -> pd.DataFrame:
    """
    Load the ML-ready feature CSV produced by ``build_feature_dataset``.

    Parameters
    ----------
    filepath : str
        Path to the feature table CSV. Must contain a ``label`` column.

    Returns
    -------
    pd.DataFrame
        Feature dataset.

    Raises
    ------
    FileNotFoundError, ValueError
        On missing file or absent ``label`` column.
    """
    if not Path(filepath).exists():
        raise FileNotFoundError(f"Feature dataset not found: {filepath}")
    df = pd.read_csv(filepath)
    if "label" not in df.columns:
        raise ValueError(
            f"Feature dataset at '{filepath}' has no 'label' column. "
            "Run build_feature_dataset with labels to produce a training set."
        )
    return df


# ---------------------------------------------------------------------------
# Train / test splitting
# ---------------------------------------------------------------------------

def split_dataset(
    df: pd.DataFrame,
    test_size: float = 0.2,
    random_state: int = 42,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split the feature dataset into training and test sets.

    Strategy:
        * If a ``subject_id`` column exists, ``GroupShuffleSplit`` is used
          so that all windows / recordings of one subject fall entirely in
          either train or test — preventing data leakage.
        * Otherwise a random split is applied.

    Parameters
    ----------
    df : pd.DataFrame
        Full feature dataset including a ``label`` column.
    test_size : float
        Fraction of data (or subjects) to reserve for testing.
    random_state : int
        Random seed for reproducibility.

    Returns
    -------
    train_df, test_df : (pd.DataFrame, pd.DataFrame)
        Disjoint splits ready for model training and evaluation.
    """
    if "subject_id" in df.columns:
        groups = df["subject_id"].values
        gss = GroupShuffleSplit(
            n_splits=1, test_size=test_size, random_state=random_state
        )
        train_idx, test_idx = next(gss.split(df, groups=groups))
        print(
            f"[train_model] Subject-wise split — "
            f"train subjects: {set(groups[train_idx])}, "
            f"test subjects: {set(groups[test_idx])}"
        )
        return df.iloc[train_idx].copy(), df.iloc[test_idx].copy()

    # Fallback: plain random split
    train_df, test_df = train_test_split(
        df, test_size=test_size, random_state=random_state, stratify=df["label"]
    )
    return train_df.reset_index(drop=True), test_df.reset_index(drop=True)


# ---------------------------------------------------------------------------
# Feature / label extraction helper
# ---------------------------------------------------------------------------

NON_FEATURE_COLS = {"label", "subject_id"}


def _xy(df: pd.DataFrame):
    """Return (X DataFrame, y Series), dropping metadata columns."""
    feature_cols = [c for c in df.columns if c not in NON_FEATURE_COLS]
    return df[feature_cols], df["label"]


# ---------------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------------

def build_pipeline(
    n_estimators: int = 200,
    max_depth: Optional[int] = None,
    random_state: int = 42,
    use_scaler: bool = True,
) -> Pipeline:
    """
    Build a scikit-learn Pipeline containing an optional StandardScaler
    followed by a RandomForestClassifier.

    Parameters
    ----------
    n_estimators : int
        Number of trees in the forest.
    max_depth : int or None
        Maximum depth of each tree. ``None`` = grow until pure leaves.
    random_state : int
        Random seed.
    use_scaler : bool
        If ``True``, prepend a StandardScaler step. Random Forests are not
        sensitive to feature scale, but scaling is useful if other classifiers
        are swapped in later.

    Returns
    -------
    sklearn.pipeline.Pipeline
    """
    steps = []
    if use_scaler:
        steps.append(("scaler", StandardScaler()))
    steps.append((
        "classifier",
        RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            random_state=random_state,
            n_jobs=-1,
            class_weight="balanced",   # handles class imbalance
        )
    ))
    return Pipeline(steps)


def train_and_save(
    feature_csv: str,
    model_out: str = "models/gait_model.pkl",
    test_size: float = 0.2,
    n_estimators: int = 200,
    max_depth: Optional[int] = None,
    use_scaler: bool = True,
    random_state: int = 42,
) -> dict:
    """
    Full training workflow: load → split → train → evaluate → save.

    Parameters
    ----------
    feature_csv : str
        Path to the feature dataset CSV.
    model_out : str
        Destination path for the saved pipeline (joblib pickle).
    test_size : float
        Fraction of data / subjects used for test evaluation.
    n_estimators : int
        Number of Random Forest trees.
    max_depth : int or None
        Max tree depth (``None`` = unlimited).
    use_scaler : bool
        Whether to include a StandardScaler in the pipeline.
    random_state : int
        Global random seed.

    Returns
    -------
    dict
        ``{"train_accuracy": float, "test_accuracy": float,
           "feature_columns": list[str], "model_path": str}``
    """
    # Load
    df = load_feature_dataset(feature_csv)
    print(f"[train_model] Loaded {len(df)} samples, {len(df.columns)} columns.")

    # Split
    train_df, test_df = split_dataset(df, test_size=test_size, random_state=random_state)
    X_train, y_train = _xy(train_df)
    X_test,  y_test  = _xy(test_df)

    feature_columns = list(X_train.columns)
    print(f"[train_model] Features: {len(feature_columns)} | "
          f"Train: {len(X_train)} | Test: {len(X_test)}")

    # Train
    pipeline = build_pipeline(
        n_estimators=n_estimators,
        max_depth=max_depth,
        random_state=random_state,
        use_scaler=use_scaler,
    )
    pipeline.fit(X_train, y_train)

    train_acc = pipeline.score(X_train, y_train)
    test_acc  = pipeline.score(X_test,  y_test)
    print(f"[train_model] Train accuracy: {train_acc:.4f} | Test accuracy: {test_acc:.4f}")

    # Save
    Path(model_out).parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, model_out)
    print(f"[train_model] Model saved to '{model_out}'.")

    # Save feature column list alongside the model (needed at inference time)
    meta_path = str(model_out).replace(".pkl", "_meta.json")
    with open(meta_path, "w") as f:
        json.dump({"feature_columns": feature_columns}, f, indent=2)
    print(f"[train_model] Feature metadata saved to '{meta_path}'.")

    return {
        "train_accuracy":   train_acc,
        "test_accuracy":    test_acc,
        "feature_columns":  feature_columns,
        "model_path":       model_out,
    }


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def _parse_args():
    parser = argparse.ArgumentParser(
        description="Train a gait classification model from a feature CSV."
    )
    parser.add_argument("--features",     required=True,        help="Path to feature dataset CSV.")
    parser.add_argument("--model-out",    default="models/gait_model.pkl")
    parser.add_argument("--test-size",    type=float, default=0.2)
    parser.add_argument("--n-estimators", type=int,   default=200)
    parser.add_argument("--max-depth",    type=int,   default=None)
    parser.add_argument("--no-scaler",    action="store_true")
    parser.add_argument("--seed",         type=int,   default=42)
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    result = train_and_save(
        feature_csv=args.features,
        model_out=args.model_out,
        test_size=args.test_size,
        n_estimators=args.n_estimators,
        max_depth=args.max_depth,
        use_scaler=not args.no_scaler,
        random_state=args.seed,
    )
    print(json.dumps(result, indent=2))
