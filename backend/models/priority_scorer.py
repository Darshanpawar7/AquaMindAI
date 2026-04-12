def compute_priority_score(
    anomaly_score: float,
    population_factor: float,
    repair_cost_factor: float,
) -> int:
    """
    Compute a priority score in [1, 100] from three normalized [0, 1] inputs.

    Formula: weighted_sum = (anomaly_score * 0.5) + (population_factor * 0.3) + (repair_cost_factor * 0.2)
    Mapped to integer: max(1, min(100, round(weighted_sum * 99) + 1))
    """
    weighted_sum = (anomaly_score * 0.5) + (population_factor * 0.3) + (repair_cost_factor * 0.2)
    return max(1, min(100, round(weighted_sum * 99) + 1))


def assign_priority_level(failure_probability: float) -> str:
    """
    Assign a priority level string based on failure probability.

    Critical  if failure_probability >= 0.75
    High      if 0.50 <= failure_probability < 0.75
    Medium    if 0.25 <= failure_probability < 0.50
    Low       if failure_probability < 0.25
    """
    if failure_probability >= 0.75:
        return "Critical"
    if failure_probability >= 0.50:
        return "High"
    if failure_probability >= 0.25:
        return "Medium"
    return "Low"
