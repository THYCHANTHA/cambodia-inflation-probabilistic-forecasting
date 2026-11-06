"""Inflation measures computed from a validated monthly index (protocol v1.0, section 5.1).

x_t      = 100 * (ln P_t - ln P_{t-1})            monthly log change
y_log_t  = 100 * (ln P_t - ln P_{t-12}) = sum_{j=0}^{11} x_{t-j}
y_t      = 100 * (P_t / P_{t-12} - 1)  = g(y_log_t),  g(v) = 100 * (exp(v / 100) - 1)
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from cambodia_inflation.data.validation import assert_valid_cpi

WINDOW = 12


def monthly_log_change(cpi: pd.Series) -> pd.Series:
    assert_valid_cpi(cpi)
    return (100.0 * np.log(cpi.astype(float)).diff()).rename("x")


def yoy_simple(cpi: pd.Series) -> pd.Series:
    assert_valid_cpi(cpi)
    c = cpi.astype(float)
    return (100.0 * (c / c.shift(WINDOW) - 1.0)).rename("yoy")


def yoy_log(cpi: pd.Series) -> pd.Series:
    assert_valid_cpi(cpi)
    lc = np.log(cpi.astype(float))
    return (100.0 * (lc - lc.shift(WINDOW))).rename("yoy_log")


def mom_simple(cpi: pd.Series) -> pd.Series:
    assert_valid_cpi(cpi)
    c = cpi.astype(float)
    return (100.0 * (c / c.shift(1) - 1.0)).rename("mom")


def log_to_simple(v):
    """g(v) = 100 (exp(v/100) - 1); strictly increasing, so it maps quantiles to quantiles exactly."""
    return 100.0 * np.expm1(np.asarray(v, dtype=float) / 100.0)


def simple_to_log(v):
    """Inverse of :func:`log_to_simple`."""
    return 100.0 * np.log1p(np.asarray(v, dtype=float) / 100.0)


def trailing_sum(x: pd.Series, window: int = WINDOW) -> pd.Series:
    """Sum of the last ``window`` values (NaN until ``window`` values exist)."""
    return x.rolling(window, min_periods=window).sum()


def trailing_mean(values: pd.Series, window: int) -> pd.Series:
    return values.rolling(window, min_periods=window).mean()
