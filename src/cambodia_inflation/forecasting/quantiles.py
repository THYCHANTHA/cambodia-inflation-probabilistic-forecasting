"""Quantile levels, ordering checks and central intervals."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np

PROTOCOL_LEVELS = (0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95)


class QuantileError(ValueError):
    """Quantile levels or values are invalid."""


def validate_levels(levels: Sequence[float]) -> np.ndarray:
    a = np.asarray(levels, dtype=float)
    if a.ndim != 1 or len(a) == 0:
        raise QuantileError("levels must be a non-empty 1-D sequence")
    if np.any((a <= 0) | (a >= 1)):
        raise QuantileError("levels must lie strictly between 0 and 1")
    if np.any(np.diff(a) <= 0):
        raise QuantileError("levels must be strictly increasing")
    return a


def check_quantiles(values: Sequence[float], levels: Sequence[float]) -> np.ndarray:
    """Return the values as an array after checking they are finite, aligned with ``levels`` and non-decreasing."""
    lv = validate_levels(levels)
    q = np.asarray(values, dtype=float)
    if q.shape != lv.shape:
        raise QuantileError(f"{q.shape[0] if q.ndim else 0} quantiles for {len(lv)} levels")
    if not np.all(np.isfinite(q)):
        raise QuantileError("quantiles must be finite")
    if np.any(np.diff(q) < 0):
        raise QuantileError("quantiles are not non-decreasing in the level (crossing)")
    return q


def rearrange(values: Sequence[float]) -> tuple[np.ndarray, int]:
    """Monotone rearrangement by sorting; returns the sorted values and the number of adjacent crossings found."""
    q = np.asarray(values, dtype=float)
    crossings = int(np.sum(np.diff(q) < 0))
    return np.sort(q), crossings


def empirical_quantiles(draws: np.ndarray, levels: Sequence[float]) -> np.ndarray:
    """Quantiles of simulated draws (linear interpolation, numpy default)."""
    lv = validate_levels(levels)
    d = np.asarray(draws, dtype=float)
    if d.size == 0 or not np.all(np.isfinite(d)):
        raise QuantileError("draws must be non-empty and finite")
    return np.quantile(d, lv)


def central_intervals(levels: Sequence[float]) -> dict[float, tuple[int, int]]:
    """Map nominal coverage (e.g. 0.9) to the (lower, upper) positions of symmetric level pairs."""
    lv = validate_levels(levels)
    out = {}
    for i, lo in enumerate(lv):
        if lo >= 0.5:
            break
        matches = np.where(np.isclose(lv, 1.0 - lo))[0]
        if len(matches):
            out[round(1.0 - 2.0 * lo, 10)] = (i, int(matches[0]))
    return out
