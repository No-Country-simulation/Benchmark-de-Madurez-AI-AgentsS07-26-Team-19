"""Tests for the dynamic rebalancing weight formula (issue #23)."""

import pytest

from app.services.rebalancing import MAX_REAL_WEIGHT, compute_weights


def test_zero_responses() -> None:
    """With no real responses all weight goes to the public dataset."""
    pub, real = compute_weights(0)
    assert real == 0.0
    assert pub == 1.0


def test_below_threshold_linear() -> None:
    """For real_count < 20, real_weight = real_count / 100."""
    pub, real = compute_weights(10)
    assert real == pytest.approx(0.10, abs=1e-4)
    assert pub == pytest.approx(0.90, abs=1e-4)


def test_at_threshold_boundary() -> None:
    """At real_count=19 (last linear step) weight is 0.19."""
    pub, real = compute_weights(19)
    assert real == pytest.approx(0.19, abs=1e-4)
    assert pub == pytest.approx(0.81, abs=1e-4)


def test_formula_switches_at_20() -> None:
    """At real_count=20 the formula switches: 0.2 + (20-20)*0.004 = 0.20."""
    pub, real = compute_weights(20)
    assert real == pytest.approx(0.20, abs=1e-4)
    assert pub == pytest.approx(0.80, abs=1e-4)


def test_above_threshold_grows() -> None:
    """For real_count=25: 0.2 + (25-20)*0.004 = 0.22."""
    pub, real = compute_weights(25)
    assert real == pytest.approx(0.22, abs=1e-4)
    assert pub == pytest.approx(0.78, abs=1e-4)


def test_cap_at_max_real_weight() -> None:
    """real_weight is capped at MAX_REAL_WEIGHT regardless of response count."""
    pub, real = compute_weights(10_000)
    assert real == pytest.approx(MAX_REAL_WEIGHT, abs=1e-4)
    assert pub == pytest.approx(1.0 - MAX_REAL_WEIGHT, abs=1e-4)


def test_weights_always_sum_to_one() -> None:
    """public_weight + real_weight must equal 1.0 for all plausible counts."""
    for count in [0, 1, 5, 19, 20, 50, 100, 500, 10_000]:
        pub, real = compute_weights(count)
        assert abs(pub + real - 1.0) < 1e-9, f"Weights do not sum to 1 for count={count}"


def test_negative_count_raises() -> None:
    """Negative real_count is invalid and must raise ValueError."""
    with pytest.raises(ValueError, match="real_count must be >= 0"):
        compute_weights(-1)
