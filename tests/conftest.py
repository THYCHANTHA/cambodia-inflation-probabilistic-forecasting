"""Shared fixtures. All data are synthetic and do not represent Phnom Penh or Cambodian prices."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from cambodia_inflation.data.synthetic import synthetic_cpi
from cambodia_inflation.forecasting.quantiles import PROTOCOL_LEVELS


@pytest.fixture
def levels() -> np.ndarray:
    return np.asarray(PROTOCOL_LEVELS)


@pytest.fixture
def cpi_extended_shape() -> pd.Series:
    """Synthetic index with the date range of the extended sample (2005-01 to 2026-09)."""
    return synthetic_cpi(start="2005-01", n_months=261, seed=11)


@pytest.fixture
def cpi_core_shape(cpi_extended_shape) -> pd.Series:
    """Synthetic index with the date range of the core sample (2005-01 to 2025-12)."""
    s = cpi_extended_shape.loc[: pd.Period("2025-12", freq="M")].copy()
    s.attrs = dict(cpi_extended_shape.attrs)
    return s
