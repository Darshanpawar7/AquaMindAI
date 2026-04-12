import pytest
from backend.models.priority_scorer import compute_priority_score, assign_priority_level


# --- compute_priority_score ---

def test_all_zeros_returns_one():
    assert compute_priority_score(0.0, 0.0, 0.0) == 1

def test_all_ones_returns_hundred():
    assert compute_priority_score(1.0, 1.0, 1.0) == 100

def test_known_midpoint():
    # weighted_sum = 0.5 → round(0.5*99)+1 = round(49.5)+1 = 50+1 = 51 (banker's rounding)
    assert compute_priority_score(0.5, 0.5, 0.5) == 51

def test_weights_applied_correctly():
    # anomaly_score=1.0 only: weighted_sum=0.5 → 51
    assert compute_priority_score(1.0, 0.0, 0.0) == 51

def test_result_is_integer():
    score = compute_priority_score(0.3, 0.6, 0.1)
    assert isinstance(score, int)


# --- assign_priority_level ---

@pytest.mark.parametrize("prob,expected", [
    (0.75, "Critical"),
    (1.0,  "Critical"),
    (0.99, "Critical"),
    (0.50, "High"),
    (0.74, "High"),
    (0.25, "Medium"),
    (0.49, "Medium"),
    (0.0,  "Low"),
    (0.24, "Low"),
])
def test_assign_priority_level(prob, expected):
    assert assign_priority_level(prob) == expected
