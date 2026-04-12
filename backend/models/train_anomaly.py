"""Train and serialize the Isolation Forest anomaly detection model.

Run as a script:
    python backend/models/train_anomaly.py
"""
from __future__ import annotations

import os
import numpy as np
import joblib
from sklearn.ensemble import IsolationForest

MODEL_PATH = os.path.join(os.path.dirname(__file__), "isolation_forest.pkl")


def generate_training_data() -> np.ndarray:
    """Generate synthetic training data (normal + anomalous readings).

    Returns an (N, 2) array with columns [flow_rate, pressure].
    """
    rng = np.random.default_rng(42)

    # Normal readings: flow ~50 m³/h, pressure ~60 psi
    n_normal = 1900
    normal_flow = rng.normal(loc=50.0, scale=5.0, size=n_normal)
    normal_pressure = rng.normal(loc=60.0, scale=4.0, size=n_normal)

    # Anomalous readings: leaks (high flow + low pressure), noise spikes
    n_anomalous = 100
    # Leak pattern: flow spike + pressure drop
    leak_flow = rng.normal(loc=90.0, scale=8.0, size=n_anomalous // 2)
    leak_pressure = rng.normal(loc=30.0, scale=5.0, size=n_anomalous // 2)
    # Noise / degradation: random extremes
    noise_flow = rng.uniform(low=0.0, high=20.0, size=n_anomalous // 2)
    noise_pressure = rng.uniform(low=80.0, high=120.0, size=n_anomalous // 2)

    flow = np.concatenate([normal_flow, leak_flow, noise_flow])
    pressure = np.concatenate([normal_pressure, leak_pressure, noise_pressure])

    return np.column_stack([flow, pressure])


def train(data: np.ndarray) -> IsolationForest:
    """Fit an IsolationForest on the provided feature matrix."""
    model = IsolationForest(contamination=0.05, random_state=42)
    model.fit(data)
    return model


def main() -> None:
    print("Generating training data...")
    data = generate_training_data()
    print(f"  {data.shape[0]} samples, {data.shape[1]} features")

    print("Training IsolationForest (contamination=0.05, random_state=42)...")
    model = train(data)

    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    print(f"Model saved to {MODEL_PATH}")


if __name__ == "__main__":
    main()
