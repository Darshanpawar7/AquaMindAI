"""
Linear regression risk predictor for AquaMind AI.

Predicts failure probability for a water infrastructure node based on:
- alert_frequency_7d: number of alerts in the past 7 days
- anomaly_severity_avg: average anomaly severity score (already in [0, 1])
- pipe_age_years: age of the pipe in years
"""

from typing import Optional


def predict_failure_probability(
    alert_frequency_7d: Optional[float],
    anomaly_severity_avg: Optional[float],
    pipe_age_years: Optional[float],
) -> dict:
    """
    Predict failure probability using a simple linear regression formula.

    Formula (when all features present):
        prob = 0.3 * norm(alert_freq) + 0.4 * anomaly_severity + 0.3 * norm(pipe_age)

    Normalization:
        - alert_frequency_7d / 10, capped at 1.0
        - pipe_age_years / 50, capped at 1.0
        - anomaly_severity_avg is already in [0, 1]

    Returns:
        {
            "failure_probability": float in [0.0, 1.0],
            "data_quality_warning": str | None
        }
    """
    missing_fields = []
    if alert_frequency_7d is None:
        missing_fields.append("alert_frequency_7d")
    if anomaly_severity_avg is None:
        missing_fields.append("anomaly_severity_avg")
    if pipe_age_years is None:
        missing_fields.append("pipe_age_years")

    data_quality_warning = None
    if missing_fields:
        data_quality_warning = (
            f"Missing input features: {', '.join(missing_fields)}. "
            "Prediction is based on available features only and may be less accurate."
        )

    # Normalize available features; default missing ones to 0 (neutral contribution)
    norm_alert_freq = min(alert_frequency_7d / 10.0, 1.0) if alert_frequency_7d is not None else 0.0
    norm_severity = float(anomaly_severity_avg) if anomaly_severity_avg is not None else 0.0
    norm_pipe_age = min(pipe_age_years / 50.0, 1.0) if pipe_age_years is not None else 0.0

    # Adjust weights when features are missing so available features carry full weight
    present_weights = {
        "alert_freq": 0.3 if alert_frequency_7d is not None else 0.0,
        "severity": 0.4 if anomaly_severity_avg is not None else 0.0,
        "pipe_age": 0.3 if pipe_age_years is not None else 0.0,
    }

    total_weight = sum(present_weights.values())

    if total_weight == 0.0:
        # No features available at all
        prob = 0.0
    else:
        raw = (
            present_weights["alert_freq"] * norm_alert_freq
            + present_weights["severity"] * norm_severity
            + present_weights["pipe_age"] * norm_pipe_age
        )
        # Re-scale so weights sum to 1
        prob = raw / total_weight

    # Clamp to [0.0, 1.0]
    failure_probability = max(0.0, min(1.0, prob))

    return {
        "failure_probability": failure_probability,
        "data_quality_warning": data_quality_warning,
    }
