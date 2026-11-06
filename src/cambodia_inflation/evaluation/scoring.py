"""Proper scoring rules and calibration summaries (protocol v1.0, section 11.2).

Definitions
    pinball   L_tau(q, y) = (1{y < q} - tau) (q - y)
    interval  IS_alpha(l, u; y) = (u - l) + (2/alpha)(l - y) 1{y < l} + (2/alpha)(y - u) 1{y > u}
    WIS       (1 / (K + 1/2)) [ 0.5 |y - m| + sum_k (alpha_k / 2) IS_alpha_k ]
    CRPS      int (F(z) - 1{z >= y})^2 dz = E|X - y| - 0.5 E|X - X'| = 2 int_0^1 L_tau(F^{-1}(tau), y) dtau
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
from scipy import stats

from cambodia_inflation.forecasting.quantiles import central_intervals, check_quantiles, validate_levels


def pinball_loss(q, y, tau):
    """Pinball (quantile) loss; broadcasts over arrays."""
    q = np.asarray(q, dtype=float)
    y = np.asarray(y, dtype=float)
    tau = np.asarray(tau, dtype=float)
    return ((y < q).astype(float) - tau) * (q - y)


def interval_score(lower, upper, y, alpha: float):
    if not 0 < alpha < 1:
        raise ValueError("alpha must be in (0, 1)")
    lower, upper, y = (np.asarray(a, dtype=float) for a in (lower, upper, y))
    if np.any(upper < lower):
        raise ValueError("upper bound below lower bound")
    below = (lower - y) * (y < lower)
    above = (y - upper) * (y > upper)
    return (upper - lower) + (2.0 / alpha) * below + (2.0 / alpha) * above


def wis(quantiles: Sequence[float], levels: Sequence[float], y: float) -> float:
    """Weighted interval score from symmetric central intervals and the median (Bracher et al. 2021 form)."""
    lv = validate_levels(levels)
    q = check_quantiles(quantiles, lv)
    med = np.where(np.isclose(lv, 0.5))[0]
    if len(med) != 1:
        raise ValueError("levels must contain the median")
    intervals = central_intervals(lv)
    n_paired = 2 * len(intervals) + 1
    if n_paired != len(lv):
        raise ValueError("every non-median level must have a symmetric partner")
    total = 0.5 * abs(y - q[med[0]])
    for coverage, (i, j) in intervals.items():
        alpha = 1.0 - coverage
        total += (alpha / 2.0) * float(interval_score(q[i], q[j], y, alpha))
    return float(total / (len(intervals) + 0.5))


def wis_via_pinball(quantiles: Sequence[float], levels: Sequence[float], y: float) -> float:
    """Sum of pinball losses over all levels divided by K + 1/2; equals :func:`wis` for symmetric level sets."""
    lv = validate_levels(levels)
    q = check_quantiles(quantiles, lv)
    k = (len(lv) - 1) // 2
    return float(np.sum(pinball_loss(q, y, lv)) / (k + 0.5))


def crps_gaussian(mu, sigma, y):
    """Closed-form CRPS of N(mu, sigma^2)."""
    mu, sigma, y = (np.asarray(a, dtype=float) for a in (mu, sigma, y))
    if np.any(sigma <= 0):
        raise ValueError("sigma must be positive")
    z = (y - mu) / sigma
    return sigma * (z * (2.0 * stats.norm.cdf(z) - 1.0) + 2.0 * stats.norm.pdf(z) - 1.0 / np.sqrt(np.pi))


def crps_sample(draws, y: float) -> float:
    """CRPS of the empirical distribution of ``draws``: mean|X - y| - 0.5 mean|X - X'| (O(n log n))."""
    x = np.sort(np.asarray(draws, dtype=float))
    n = len(x)
    if n == 0 or not np.all(np.isfinite(x)):
        raise ValueError("draws must be non-empty and finite")
    term1 = np.mean(np.abs(x - y))
    # sum_{i,j} |x_i - x_j| = 2 sum_i (2i - n - 1) x_(i), i = 1..n
    i = np.arange(1, n + 1)
    pair_sum = 2.0 * np.sum((2 * i - n - 1) * x)
    return float(term1 - 0.5 * pair_sum / (n * n))


def coverage(lower, upper, y) -> float:
    lower, upper, y = (np.asarray(a, dtype=float) for a in (lower, upper, y))
    return float(np.mean((y >= lower) & (y <= upper)))


def mean_width(lower, upper) -> float:
    return float(np.mean(np.asarray(upper, dtype=float) - np.asarray(lower, dtype=float)))


def quantile_bin_counts(quantile_matrix, y, levels: Sequence[float]) -> tuple[np.ndarray, np.ndarray]:
    """Counts of outcomes falling between consecutive predictive quantiles, and the expected shares.

    Bin b holds outcomes with q_{b-1} < y <= q_b (q_0 = -inf, q_{n+1} = +inf). Expected shares are the level
    differences (0.05, 0.05, 0.15, 0.25, 0.25, 0.15, 0.05, 0.05 for the protocol levels).
    """
    lv = validate_levels(levels)
    qm = np.atleast_2d(np.asarray(quantile_matrix, dtype=float))
    y = np.asarray(y, dtype=float)
    if qm.shape != (len(y), len(lv)):
        raise ValueError("quantile_matrix must have shape (n_forecasts, n_levels)")
    bins = np.sum(qm < y[:, None], axis=1)
    counts = np.bincount(bins, minlength=len(lv) + 1)
    expected = np.diff(np.concatenate([[0.0], lv, [1.0]]))
    return counts, expected


def pit_values(cdf_values) -> np.ndarray:
    """Validate PIT values F(y) computed by a model with a CDF."""
    u = np.asarray(cdf_values, dtype=float)
    if np.any((u < 0) | (u > 1)) or not np.all(np.isfinite(u)):
        raise ValueError("PIT values must lie in [0, 1]")
    return u
