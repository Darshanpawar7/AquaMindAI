"""Anomaly detection model interface for AquaMind AI.

Loads the pre-trained IsolationForest and exposes a predict() function
that returns anomaly scores in [0, 1] (1 = most anomalous).
"""
from __future__ import annotations

import os
from typing import List

import numpy as np

MODEL_PATH = os.path.join(os.path.dirname(__file__), "isolation_forest.pkl")


class ModelNotAvailableError(Exception):
    """Raised when the isolation_forest.pkl file is missing at load time."""


def _load_model():
    """Attempt to load the serialized IsolationForest.

    Returns the model on success, or None if the file is missing.
    """
    if not os.path.exists(MODEL_PATH):
        return None
    import joblib  # deferred so the module is importable without joblib installed
    return joblib.load(MODEL_PATH)


# Module-level load — happens once at Lambda cold start.
_model = _load_model()
_model_available: bool = _model is not None


def load_model():
    """Reload the model from disk (useful for testing / hot-reload scenarios)."""
    global _model, _model_available
    _model = _load_model()
    _model_available = _model is not None
    return _model


def predict(readings) -> List[float]:
    """Return anomaly scores in [0, 1] for each reading.

    Parameters
    ----------
    readings:
        An iterable of Reading dataclass instances (or any objects with
        ``flow_rate`` and ``pressure`` attributes).

    Returns
    -------
    List[float]
        One score per reading.  1.0 = most anomalous, 0.0 = most normal.

    Raises
    ------
    ModelNotAvailableError
        If the model file was not found at module load time.
    """
    if not _model_available or _model is None:
        raise ModelNotAvailableError(
            f"Isolation Forest model not found at '{MODEL_PATH}'. "
            "Run `python backend/models/train_anomaly.py` to train and save the model."
        )

    features = np.array([[r.flow_rate, r.pressure] for r in readings], dtype=float)

    if features.shape[0] == 0:
        return []

    # decision_function returns higher values for inliers (normal) and
    # lower (more negative) values for outliers (anomalous).
    raw_scores: np.ndarray = _model.decision_function(features)

    # Normalise to [0, 1] where 1 = most anomalous.
    # Invert so that the most anomalous reading maps to 1.
    min_s = raw_scores.min()
    max_s = raw_scores.max()

    if max_s == min_s:
        # All scores identical — return 0.5 for every reading.
        return [0.5] * len(readings)

    # Map: most anomalous (lowest raw) → 1, most normal (highest raw) → 0
    normalised = 1.0 - (raw_scores - min_s) / (max_s - min_s)
    return normalised.tolist()
