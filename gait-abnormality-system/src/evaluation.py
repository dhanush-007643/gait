"""
evaluation.py
=============
Evaluates a trained gait classification pipeline and reports standard
performance metrics: accuracy, precision, recall, F1-score, confusion matrix,
and (optionally) Random Forest feature importances.

All functions are stateless and independently callable.
"""

from pathlib import Path
from typing import List, Optional, Tuple, Union

import numpy as np
import pandas as pd
import joblib
from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
    classification_report,
    confusion_matrix,
)


# ---------------------------------------------------------------------------
# Model loading helper
# ---------------------------------------------------------------------------

def load_model(model_path: str):
    """
    Load a trained scikit-learn pipeline from a joblib file.

    Parameters
    ----------
    model_path : str
        Path to the ``.pkl`` file saved by ``train_model.train_and_save``.

    Returns
    -------
    sklearn.pipeline.Pipeline
        Loaded pipeline (scaler + classifier).

    Raises
    ------
    FileNotFoundError
        If the file does not exist.
    """
    if not Path(model_path).exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")
    return joblib.load(model_path)


# ---------------------------------------------------------------------------
# Core evaluation
# ---------------------------------------------------------------------------

def evaluate(
    model,
    X_test: pd.DataFrame,
    y_test: Union[pd.Series, np.ndarray, List],
    target_names: Optional[List[str]] = None,
) -> dict:
    """
    Compute classification metrics for a fitted model on a held-out test set.

    Parameters
    ----------
    model : fitted sklearn Pipeline or classifier
        Must implement ``predict`` and (optionally) ``predict_proba``.
    X_test : pd.DataFrame, shape (n_samples, n_features)
        Feature matrix for the test set.
    y_test : array-like, shape (n_samples,)
        True class labels.
    target_names : list of str, optional
        Human-readable class names for the report (e.g., ``["normal", "abnormal"]``).
        If omitted, sklearn infers them from the unique values in ``y_test``.

    Returns
    -------
    dict with keys:
        ``accuracy``          — float
        ``precision``         — array, one value per class
        ``recall``            — array, one value per class
        ``f1``                — array, one value per class
        ``confusion_matrix``  — 2-D np.ndarray
        ``classification_report`` — formatted string (sklearn)
        ``y_pred``            — predicted labels (np.ndarray)
    """
    y_test = np.asarray(y_test)
    y_pred = model.predict(X_test)

    acc = accuracy_score(y_test, y_pred)
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_test, y_pred, average=None, zero_division=0
    )
    cm = confusion_matrix(y_test, y_pred)
    report_str = classification_report(
        y_test, y_pred,
        target_names=target_names,
        zero_division=0,
    )

    return {
        "accuracy":               acc,
        "precision":              precision,
        "recall":                 recall,
        "f1":                     f1,
        "confusion_matrix":       cm,
        "classification_report":  report_str,
        "y_pred":                 y_pred,
    }


# ---------------------------------------------------------------------------
# Pretty printing
# ---------------------------------------------------------------------------

def print_evaluation_report(metrics: dict, class_names: Optional[List[str]] = None) -> None:
    """
    Print a formatted summary of the evaluation metrics dict returned by
    ``evaluate``.

    Parameters
    ----------
    metrics : dict
        Output of ``evaluate``.
    class_names : list of str, optional
        Used to label per-class rows in the table.
    """
    print("=" * 55)
    print("  GAIT CLASSIFICATION — EVALUATION REPORT")
    print("=" * 55)
    print(f"  Overall Accuracy : {metrics['accuracy']:.4f}\n")
    print(metrics["classification_report"])
    print("Confusion Matrix:")
    cm = metrics["confusion_matrix"]
    labels = class_names or [str(i) for i in range(cm.shape[0])]
    header = "         " + "  ".join(f"{l:>8}" for l in labels)
    print(header)
    for i, row in enumerate(cm):
        row_str = "  ".join(f"{v:>8}" for v in row)
        print(f"  {labels[i]:>6}   {row_str}")
    print("=" * 55)


# ---------------------------------------------------------------------------
# Feature importances
# ---------------------------------------------------------------------------

def get_feature_importances(
    model,
    feature_names: List[str],
    top_n: int = 20,
) -> pd.DataFrame:
    """
    Extract and rank feature importances from the Random Forest inside a
    trained Pipeline.

    Parameters
    ----------
    model : fitted sklearn Pipeline
        Must contain a step named ``"classifier"`` that is a tree-based
        estimator exposing ``feature_importances_``.
    feature_names : list of str
        Ordered list of feature column names (same order used during training).
    top_n : int
        Number of top features to return. Default 20.

    Returns
    -------
    pd.DataFrame, shape (min(top_n, n_features), 2)
        Columns: ``feature``, ``importance``, sorted descending.

    Raises
    ------
    AttributeError
        If the pipeline's classifier does not have ``feature_importances_``.
    """
    if hasattr(model, "named_steps"):
        clf = model.named_steps.get("classifier", model)
    else:
        clf = model

    if not hasattr(clf, "feature_importances_"):
        raise AttributeError(
            "The provided model does not expose feature_importances_. "
            "Only tree-based estimators (e.g. RandomForest) support this."
        )

    importances = clf.feature_importances_
    top_n = min(top_n, len(feature_names))

    df_imp = pd.DataFrame({
        "feature":    feature_names,
        "importance": importances,
    }).sort_values("importance", ascending=False).head(top_n).reset_index(drop=True)

    return df_imp


# ---------------------------------------------------------------------------
# Convenience: evaluate from paths
# ---------------------------------------------------------------------------

def evaluate_from_files(
    model_path: str,
    test_csv: str,
    target_names: Optional[List[str]] = None,
    print_report: bool = True,
    print_importances: bool = True,
    top_n_importances: int = 15,
) -> dict:
    """
    End-to-end evaluation convenience wrapper: load model → load test CSV →
    evaluate → print report.

    Parameters
    ----------
    model_path : str
        Path to the trained ``.pkl`` model file.
    test_csv : str
        Path to a feature dataset CSV containing both feature columns and a
        ``label`` column.
    target_names : list of str, optional
        Human-readable class names.
    print_report : bool
        Whether to print the classification report to stdout.
    print_importances : bool
        Whether to print top feature importances (only for RF models).
    top_n_importances : int
        How many top features to show.

    Returns
    -------
    dict
        Evaluation metrics dict (same as ``evaluate``).
    """
    import json

    model = load_model(model_path)

    df = pd.read_csv(test_csv)
    if "label" not in df.columns:
        raise ValueError(f"Test CSV '{test_csv}' must contain a 'label' column.")

    # Load feature column list from companion meta file if available
    meta_path = str(model_path).replace(".pkl", "_meta.json")
    if Path(meta_path).exists():
        with open(meta_path) as f:
            meta = json.load(f)
        feature_cols = meta["feature_columns"]
    else:
        feature_cols = [c for c in df.columns if c not in {"label", "subject_id"}]

    X_test = df[feature_cols]
    y_test = df["label"]

    metrics = evaluate(model, X_test, y_test, target_names=target_names)

    if print_report:
        print_evaluation_report(metrics, class_names=target_names)

    if print_importances:
        try:
            imp_df = get_feature_importances(model, feature_cols, top_n=top_n_importances)
            print(f"\nTop {top_n_importances} Feature Importances:")
            print(imp_df.to_string(index=False))
        except AttributeError as exc:
            print(f"[evaluation] Feature importances not available: {exc}")

    return metrics
