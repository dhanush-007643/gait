"""
preprocessing.py
================
Handles loading, cleaning, filtering, and normalizing raw sensor CSV data.

Expected CSV columns:
    timestamp, acc_x, acc_y, acc_z, gyro_x, gyro_y, gyro_z
    (label column is optional — present only in training data)

All functions are pure: they accept a DataFrame and return a new DataFrame.
No global state is mutated.
"""

import pandas as pd
import numpy as np
from scipy.signal import butter, filtfilt


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
REQUIRED_SENSOR_COLUMNS = ["timestamp", "acc_x", "acc_y", "acc_z",
                            "gyro_x", "gyro_y", "gyro_z"]
SENSOR_SIGNAL_COLUMNS = ["acc_x", "acc_y", "acc_z", "gyro_x", "gyro_y", "gyro_z"]


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

def load_csv(filepath: str) -> pd.DataFrame:
    """
    Load a sensor CSV file into a pandas DataFrame.

    Parameters
    ----------
    filepath : str
        Absolute or relative path to the CSV file.

    Returns
    -------
    pd.DataFrame
        Raw DataFrame with at least the required sensor columns present.
        The ``timestamp`` column is parsed to datetime (if possible).

    Raises
    ------
    FileNotFoundError
        If the file does not exist at ``filepath``.
    ValueError
        If the file is empty or is missing any required sensor columns.
    """
    try:
        df = pd.read_csv(filepath)
    except FileNotFoundError:
        raise FileNotFoundError(f"CSV file not found: {filepath}")
    except Exception as exc:
        raise ValueError(f"Could not read CSV file '{filepath}': {exc}") from exc

    if df.empty:
        raise ValueError(f"CSV file is empty: {filepath}")

    missing = [c for c in REQUIRED_SENSOR_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(
            f"CSV file '{filepath}' is missing required columns: {missing}\n"
            f"Found columns: {list(df.columns)}"
        )

    # Parse timestamp — keep as numeric if parsing fails (some datasets use
    # plain integer milliseconds).
    try:
        df["timestamp"] = pd.to_datetime(df["timestamp"])
    except Exception:
        pass  # Leave timestamp as-is; sort_by_time handles both types

    return df


# ---------------------------------------------------------------------------
# Cleaning
# ---------------------------------------------------------------------------

def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Remove exact duplicate rows from the DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        Input sensor DataFrame.

    Returns
    -------
    pd.DataFrame
        DataFrame with duplicate rows dropped; index is reset.
    """
    original_len = len(df)
    df_clean = df.drop_duplicates().reset_index(drop=True)
    removed = original_len - len(df_clean)
    if removed > 0:
        print(f"[preprocessing] Removed {removed} duplicate row(s).")
    return df_clean


def handle_missing(df: pd.DataFrame) -> pd.DataFrame:
    """
    Handle missing (NaN) values in sensor columns.

    Strategy:
        1. Forward-fill then backward-fill short gaps (sensor dropout).
        2. Drop any remaining rows where sensor values are still NaN
           (edge-case: leading NaNs that cannot be forward-filled).

    Parameters
    ----------
    df : pd.DataFrame
        Input sensor DataFrame.

    Returns
    -------
    pd.DataFrame
        DataFrame with NaN values handled; index is reset.
    """
    df_filled = df.copy()
    df_filled[SENSOR_SIGNAL_COLUMNS] = (
        df_filled[SENSOR_SIGNAL_COLUMNS]
        .ffill()
        .bfill()
    )

    before = len(df_filled)
    df_filled = df_filled.dropna(subset=SENSOR_SIGNAL_COLUMNS).reset_index(drop=True)
    dropped = before - len(df_filled)
    if dropped > 0:
        print(f"[preprocessing] Dropped {dropped} row(s) with unfillable NaN values.")

    return df_filled


def sort_by_time(df: pd.DataFrame) -> pd.DataFrame:
    """
    Sort the DataFrame by the ``timestamp`` column in ascending order.

    Parameters
    ----------
    df : pd.DataFrame
        Input sensor DataFrame (must contain a ``timestamp`` column).

    Returns
    -------
    pd.DataFrame
        Sorted DataFrame with a reset index.
    """
    return df.sort_values("timestamp").reset_index(drop=True)


# ---------------------------------------------------------------------------
# Signal Filtering
# ---------------------------------------------------------------------------

def filter_signal(df: pd.DataFrame,
                  cutoff_hz: float = 20.0,
                  sampling_rate_hz: float = 100.0,
                  order: int = 4) -> pd.DataFrame:
    """
    Apply a low-pass Butterworth filter to all sensor signal columns
    to remove high-frequency noise.

    Parameters
    ----------
    df : pd.DataFrame
        Input sensor DataFrame.
    cutoff_hz : float
        Low-pass cutoff frequency in Hz. Default is 20 Hz (covers normal
        human movement bandwidth well within typical wearable sampling rates).
    sampling_rate_hz : float
        Sampling frequency of the sensor data in Hz. Default is 100 Hz.
    order : int
        Butterworth filter order. Default is 4.

    Returns
    -------
    pd.DataFrame
        DataFrame with sensor columns replaced by filtered values.

    Raises
    ------
    ValueError
        If ``cutoff_hz`` is not strictly less than ``sampling_rate_hz / 2``
        (Nyquist constraint).
    """
    nyquist = sampling_rate_hz / 2.0
    if cutoff_hz >= nyquist:
        raise ValueError(
            f"cutoff_hz ({cutoff_hz}) must be less than the Nyquist frequency "
            f"({nyquist} Hz) for sampling_rate_hz={sampling_rate_hz}."
        )

    normalized_cutoff = cutoff_hz / nyquist
    b, a = butter(order, normalized_cutoff, btype="low", analog=False)

    df_filtered = df.copy()
    for col in SENSOR_SIGNAL_COLUMNS:
        if col in df_filtered.columns:
            # filtfilt applies zero-phase (non-causal) filtering — no phase lag
            df_filtered[col] = filtfilt(b, a, df_filtered[col].values)

    return df_filtered


# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------

def normalize(df: pd.DataFrame,
              return_params: bool = False):
    """
    Standardize sensor signal columns to zero mean and unit variance (z-score).

    Parameters
    ----------
    df : pd.DataFrame
        Input sensor DataFrame.
    return_params : bool
        If ``True``, also return a dict containing the per-column
        ``mean`` and ``std`` used for standardization (useful for applying
        the same scaling to unseen test data).

    Returns
    -------
    pd.DataFrame
        DataFrame with standardized sensor columns.
    dict (only if ``return_params=True``)
        ``{"mean": pd.Series, "std": pd.Series}`` keyed by column name.
    """
    df_norm = df.copy()
    cols = [c for c in SENSOR_SIGNAL_COLUMNS if c in df_norm.columns]

    means = df_norm[cols].mean()
    stds = df_norm[cols].std().replace(0, 1)  # avoid division by zero

    df_norm[cols] = (df_norm[cols] - means) / stds

    if return_params:
        return df_norm, {"mean": means, "std": stds}
    return df_norm


# ---------------------------------------------------------------------------
# Convenience pipeline
# ---------------------------------------------------------------------------

def run_preprocessing_pipeline(filepath: str,
                                apply_filter: bool = True,
                                apply_normalization: bool = False,
                                sampling_rate_hz: float = 100.0) -> pd.DataFrame:
    """
    Convenience function that runs the full preprocessing pipeline in order:
    load → deduplicate → handle missing → sort → filter → (normalize).

    Parameters
    ----------
    filepath : str
        Path to the raw CSV file.
    apply_filter : bool
        Whether to apply low-pass filtering. Default is True.
    apply_normalization : bool
        Whether to standardize sensor columns. Default is False
        (normalization is typically applied after feature extraction).
    sampling_rate_hz : float
        Sensor sampling rate used for the Butterworth filter.

    Returns
    -------
    pd.DataFrame
        Cleaned and optionally filtered/normalized DataFrame.
    """
    df = load_csv(filepath)
    df = remove_duplicates(df)
    df = handle_missing(df)
    df = sort_by_time(df)
    if apply_filter:
        df = filter_signal(df, sampling_rate_hz=sampling_rate_hz)
    if apply_normalization:
        df = normalize(df)
    return df
