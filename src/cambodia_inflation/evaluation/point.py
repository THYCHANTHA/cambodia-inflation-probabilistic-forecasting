"""Point-forecast metrics (protocol v1.0, section 11.1). Point forecasts are predictive medians."""

from __future__ import annotations

import numpy as np
import pandas as pd


def mae(errors) -> float:
    e = np.asarray(errors, dtype=float)
    return float(np.mean(np.abs(e)))


def rmse(errors) -> float:
    e = np.asarray(errors, dtype=float)
    return float(np.sqrt(np.mean(e**2)))


def mase_scale(y: pd.Series, horizon: int) -> float:
    """Mean absolute h-step change of y over the given (fixed) window: the MASE denominator."""
    d = (y - y.shift(horizon)).dropna()
    if len(d) == 0:
        raise ValueError("window too short for this horizon")
    scale = float(np.mean(np.abs(d)))
    if scale <= 0:
        raise ValueError("MASE scale is zero")
    return scale


def mase(errors, scale: float) -> float:
    if scale <= 0:
        raise ValueError("scale must be positive")
    return mae(errors) / scale
