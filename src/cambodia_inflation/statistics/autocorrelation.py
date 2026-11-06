"""Sample ACF and PACF without statsmodels.

ACF: r_k = sum_{t} (x_t - xbar)(x_{t+k} - xbar) / sum_t (x_t - xbar)^2  (the usual biased estimator).
PACF: Durbin-Levinson recursion on the sample ACF (equals the last Yule-Walker coefficient at each lag).
Bands: +-1.96/sqrt(n), valid only under a white-noise null; for overlapping YoY rates they are a visual guide only.
"""

from __future__ import annotations

import numpy as np


def acf(x, nlags: int) -> np.ndarray:
    """Autocorrelations at lags 0..nlags."""
    x = np.asarray(x, dtype=float)
    if not np.all(np.isfinite(x)):
        raise ValueError("series must be finite (drop missing values first)")
    n = len(x)
    if nlags < 1 or nlags >= n:
        raise ValueError("nlags must be between 1 and n - 1")
    d = x - x.mean()
    denom = float(d @ d)
    if denom == 0:
        raise ValueError("series is constant")
    return np.array([1.0] + [float(d[: n - k] @ d[k:]) / denom for k in range(1, nlags + 1)])


def pacf(x, nlags: int) -> np.ndarray:
    """Partial autocorrelations at lags 0..nlags (lag 0 = 1)."""
    r = acf(x, nlags)
    out = np.zeros(nlags + 1)
    out[0] = 1.0
    phi = np.zeros(nlags + 1)
    v = 1.0
    for k in range(1, nlags + 1):
        num = r[k] - np.dot(phi[1:k], r[k - 1 : 0 : -1])
        a = num / v
        new = phi.copy()
        new[k] = a
        new[1:k] = phi[1:k] - a * phi[k - 1 : 0 : -1]
        phi = new
        v *= 1.0 - a * a
        out[k] = a
    return out


def white_noise_band(n: int) -> float:
    return 1.96 / np.sqrt(n)
