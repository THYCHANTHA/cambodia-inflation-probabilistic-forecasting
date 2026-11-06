"""Synthetic CPI series for software testing.

These series are generated from an arbitrary seasonal AR(1) process. They do NOT represent Phnom Penh or Cambodian
prices, and no result computed on them is a research finding. Every returned series carries
``series.attrs["synthetic"] = True``.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def synthetic_cpi(
    start: str = "2005-01",
    n_months: int = 261,
    seed: int = 0,
    mean_monthly: float = 0.25,
    seasonal_amplitude: float = 0.3,
    ar: float = 0.4,
    noise_sd: float = 0.5,
    base_level: float = 100.0,
) -> pd.Series:
    """Return a synthetic monthly index (default 2005-01 to 2026-09, the shape of the extended sample)."""
    rng = np.random.default_rng(seed)
    index = pd.period_range(start=start, periods=n_months, freq="M")
    month = index.month.to_numpy()
    seasonal = seasonal_amplitude * np.sin(2 * np.pi * (month - 1) / 12)
    x = np.empty(n_months)
    dev = 0.0
    for t in range(n_months):
        dev = ar * dev + rng.normal(0.0, noise_sd)
        x[t] = mean_monthly + seasonal[t] + dev
    x[0] = 0.0
    level = base_level * np.exp(np.cumsum(x) / 100.0)
    series = pd.Series(level, index=index, name="cpi_synthetic")
    series.attrs["synthetic"] = True
    return series
