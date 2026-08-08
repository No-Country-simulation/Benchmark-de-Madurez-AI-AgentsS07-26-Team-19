"""Tests for percentile calculation functions."""

from app.services.percentiles import (
    calculate_percentile,
    compute_percentile_thresholds,
    weighted_merge,
)


def test_only_public():
    """When real_weight=0, only the public dataset is used."""
    public_scores = [10, 20, 30, 40, 50]
    real_scores = [100, 200]

    result = weighted_merge(public_scores, real_scores, 1.0, 0.0)

    assert len(result) == len(public_scores)
    assert all(s in public_scores for s in result)


def test_only_real():
    """When public_weight=0, only the real dataset is used."""
    public_scores = [10, 20, 30]
    real_scores = [100, 200, 300, 400]

    result = weighted_merge(public_scores, real_scores, 0.0, 1.0)

    assert len(result) == len(real_scores)
    assert all(s in real_scores for s in result)


def test_fifty_fifty():
    """With 0.5 weight for each, half of each dataset is sampled."""
    public_scores = list(range(100))   # 100 elements
    real_scores = list(range(10))       # 10 elements

    result = weighted_merge(public_scores, real_scores, 0.5, 0.5)

    # 50% of 100 = 50, 50% of 10 = 5 → total 55
    assert len(result) == 55


def test_exact_percentile():
    """Score=30 in [10,20,40,50] → 2 out of 5 are below → 40%"""
    dataset = [10, 20, 40, 50]
    percentile = calculate_percentile(30, dataset)
    assert percentile == 40.0


def test_percentile_max():
    """Score higher than all → percentile = 75% (3 of 4 are below)"""
    percentile = calculate_percentile(100, [10, 20, 30])
    assert percentile == 75.0


def test_percentile_min():
    """Score lower than all → percentile = 0%"""
    percentile = calculate_percentile(5, [10, 20, 30])
    assert percentile == 0.0


def test_empty_dataset():
    """Empty dataset → neutral percentile 50%"""
    percentile = calculate_percentile(50, [])
    assert percentile == 50.0


def test_compute_thresholds_basic():
    """50 scores [0..49] → P50 should be 24, P10 should be 4"""
    scores = list(range(50))  # [0, 1, 2, ..., 49]
    thresholds = compute_percentile_thresholds(scores)
    
    assert thresholds[50] == 24.0   # P50 (median): index 24 → value 24
    assert thresholds[10] == 4.0    # P10: index 4 → value 4


def test_compute_thresholds_empty():
    """Empty list → all thresholds should be 0.0"""
    thresholds = compute_percentile_thresholds([])
    assert all(v == 0.0 for v in thresholds.values())


def test_compute_thresholds_custom_percentiles():
    """Only ask for P25 and P75"""
    scores = [10, 20, 30, 40]
    thresholds = compute_percentile_thresholds(scores, percentiles=[25, 75])
    
    assert 25 in thresholds
    assert 75 in thresholds
    assert 50 not in thresholds