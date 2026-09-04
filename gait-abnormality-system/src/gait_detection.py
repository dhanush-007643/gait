"""
gait_detection.py
=================
Computes derived signals, detects steps via peak detection, and segments
continuous recordings into fixed-length time windows for windowed analysis
or real-time simulation.

All functions are pure: they accept arrays / DataFrames and return new objects.
No global state is mutated.
"""

import numpy as np
import pandas as pd
from scipy.signal import find_peaks
from typing import List, Tuple


# ---------------------------------------------------------------------------
# Magnitude Computation
# ---------------------------------------------------------------------------

def compute_magnitude(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute the Euclidean (L2) magnitude of the accelerometer and gyroscope
    vectors and append them as new columns.

    New columns added:
        ``acc_mag``  — sqrt(acc_x² + acc_y² + acc_z²)
        ``gyro_mag`` — sqrt(gyro_x² + gyro_y² + gyro_z²)

    Parameters
    ----------
    df : pd.DataFrame
        Sensor DataFrame containing at least
        ``acc_x, acc_y, acc_z, gyro_x, gyro_y, gyro_z`` columns.

    Returns
    -------
    pd.DataFrame
        Copy of ``df`` with two additional columns appended.

    Raises
    ------
    KeyError
        If any of the required sensor columns are absent.
    """
    required = ["acc_x", "acc_y", "acc_z", "gyro_x", "gyro_y", "gyro_z"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise KeyError(f"compute_magnitude: missing columns {missing}")

    df_out = df.copy()
    df_out["acc_mag"] = np.sqrt(
        df_out["acc_x"] ** 2 +
        df_out["acc_y"] ** 2 +
        df_out["acc_z"] ** 2
    )
    df_out["gyro_mag"] = np.sqrt(
        df_out["gyro_x"] ** 2 +
        df_out["gyro_y"] ** 2 +
        df_out["gyro_z"] ** 2
    )
    return df_out


# ---------------------------------------------------------------------------
# Step Detection
# ---------------------------------------------------------------------------

def detect_steps(signal: np.ndarray,
                 height: float = None,
                 distance: int = 30,
                 prominence: float = 0.3) -> Tuple[np.ndarray, dict]:
    """
    Detect footstep peaks in a 1-D acceleration magnitude signal using
    ``scipy.signal.find_peaks``.

    Each dominant peak in the acceleration magnitude typically corresponds
    to a heel-strike or foot-contact event.

    Parameters
    ----------
    signal : np.ndarray, shape (n_samples,)
        1-D array of acceleration magnitudes (e.g., ``df["acc_mag"].values``).
    height : float or None
        Minimum peak height. If ``None``, defaults to the signal mean, which
        works well for gravity-referenced magnitude signals (~9.81 m/s²).
    distance : int
        Minimum number of samples between successive peaks.  At 100 Hz a value
        of 30 enforces at least 0.3 s between steps, preventing double-counts.
        Adjust proportionally for other sampling rates.
    prominence : float
        Minimum peak prominence — guards against detecting noise as steps.

    Returns
    -------
    peaks : np.ndarray, shape (n_steps,)
        Sample indices of detected step peaks.
    properties : dict
        Dictionary of peak properties returned by ``scipy.signal.find_peaks``
        (includes ``prominences``, ``peak_heights``, etc.).

    Raises
    ------
    ValueError
        If ``signal`` is empty or not 1-D.
    """
    signal = np.asarray(signal, dtype=float)
    if signal.ndim != 1 or len(signal) == 0:
        raise ValueError(
            "detect_steps: 'signal' must be a non-empty 1-D array."
        )

    if height is None:
        height = float(np.mean(signal))

    peaks, properties = find_peaks(
        signal,
        height=height,
        distance=distance,
        prominence=prominence
    )
    return peaks, properties


# ---------------------------------------------------------------------------
# Window Segmentation
# ---------------------------------------------------------------------------

def segment_windows(df: pd.DataFrame,
                    window_size_seconds: float = 5.0,
                    sampling_rate_hz: float = 100.0,
                    overlap: float = 0.0) -> List[pd.DataFrame]:
    """
    Split a continuous sensor recording into fixed-length, non-overlapping
    (or overlapping) time windows for windowed feature extraction or
    real-time simulation.

    Parameters
    ----------
    df : pd.DataFrame
        Preprocessed sensor DataFrame. Rows must be ordered by time
        (call ``sort_by_time`` first).
    window_size_seconds : float
        Length of each window in seconds. Default is 5.0 s.
    sampling_rate_hz : float
        Sensor sampling rate in Hz. Used to convert ``window_size_seconds``
        to a sample count. Default is 100 Hz.
    overlap : float
        Fraction of window to overlap with the next window, in [0, 1).
        0.0 means no overlap (default); 0.5 means 50 % overlap.

    Returns
    -------
    List[pd.DataFrame]
        List of window DataFrames.  Each window has ``reset_index(drop=True)``
        applied.  Windows shorter than ``window_size_samples`` (a trailing
        partial window) are **discarded**.

    Raises
    ------
    ValueError
        If ``overlap`` is not in [0, 1) or ``window_size_seconds`` ≤ 0.
    """
    if window_size_seconds <= 0:
        raise ValueError("window_size_seconds must be positive.")
    if not (0.0 <= overlap < 1.0):
        raise ValueError("overlap must be in [0, 1).")

    window_size_samples = int(window_size_seconds * sampling_rate_hz)
    step_samples = int(window_size_samples * (1.0 - overlap))
    step_samples = max(step_samples, 1)  # guard against zero step

    total = len(df)
    windows: List[pd.DataFrame] = []

    start = 0
    while start + window_size_samples <= total:
        window = df.iloc[start: start + window_size_samples].reset_index(drop=True)
        windows.append(window)
        start += step_samples

    return windows


# ---------------------------------------------------------------------------
# Convenience helper
# ---------------------------------------------------------------------------

def get_step_timestamps(df: pd.DataFrame, peak_indices: np.ndarray) -> np.ndarray:
    """
    Retrieve the timestamp values corresponding to detected step peak indices.

    Parameters
    ----------
    df : pd.DataFrame
        Sensor DataFrame (with a ``timestamp`` column) whose rows match the
        signal array from which ``peak_indices`` were derived.
    peak_indices : np.ndarray, shape (n_steps,)
        Sample indices of step peaks (output of ``detect_steps``).

    Returns
    -------
    np.ndarray, shape (n_steps,)
        Timestamp values at the step peak positions.
    """
    return df["timestamp"].iloc[peak_indices].values
