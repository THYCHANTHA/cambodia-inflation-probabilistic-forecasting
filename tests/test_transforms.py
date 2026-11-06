import numpy as np
import pandas as pd
import pytest

from cambodia_inflation.data.validation import CPIValidationError
from cambodia_inflation.statistics.transforms import (
    log_to_simple,
    mom_simple,
    monthly_log_change,
    simple_to_log,
    trailing_sum,
    yoy_log,
    yoy_simple,
)


def _flat_then_jump():
    idx = pd.period_range("2005-01", periods=25, freq="M")
    values = np.r_[np.full(12, 100.0), np.full(13, 110.0)]
    return pd.Series(values, index=idx)


# 7. YoY inflation
def test_yoy_hand_example():
    y = yoy_simple(_flat_then_jump())
    assert y.iloc[:12].isna().all()
    assert y.loc[pd.Period("2006-01", freq="M")] == pytest.approx(10.0, abs=1e-12)
    assert y.loc[pd.Period("2007-01", freq="M")] == pytest.approx(0.0, abs=1e-12)


def test_yoy_matches_definition(cpi_core_shape):
    y = yoy_simple(cpi_core_shape)
    p = cpi_core_shape.to_numpy()
    expected = 100 * (p[12:] / p[:-12] - 1)
    np.testing.assert_allclose(y.to_numpy()[12:], expected, rtol=0, atol=1e-10)


def test_log_and_simple_yoy_are_exact_transforms(cpi_core_shape):
    np.testing.assert_allclose(
        log_to_simple(yoy_log(cpi_core_shape).dropna()), yoy_simple(cpi_core_shape).dropna(), atol=1e-10
    )
    v = np.array([-5.7, 0.0, 2.5, 35.6])
    np.testing.assert_allclose(log_to_simple(simple_to_log(v)), v, atol=1e-12)


def test_mom_hand_example():
    m = mom_simple(_flat_then_jump())
    assert m.loc[pd.Period("2006-01", freq="M")] == pytest.approx(10.0)


def test_transform_refuses_invalid_series():
    s = pd.Series([100.0, 101.0], index=pd.PeriodIndex(["2005-01", "2005-03"], freq="M"))
    with pytest.raises(CPIValidationError):
        yoy_simple(s)


# 8. Monthly log-change reconstruction
def test_log_changes_reconstruct_index(cpi_core_shape):
    x = monthly_log_change(cpi_core_shape)
    assert np.isnan(x.iloc[0])
    rebuilt = cpi_core_shape.iloc[0] * np.exp(np.r_[0.0, np.cumsum(x.iloc[1:].to_numpy())] / 100)
    np.testing.assert_allclose(rebuilt, cpi_core_shape.to_numpy(), rtol=1e-12)


def test_twelve_log_changes_sum_to_log_yoy(cpi_core_shape):
    x = monthly_log_change(cpi_core_shape)
    np.testing.assert_allclose(trailing_sum(x).dropna(), yoy_log(cpi_core_shape).dropna(), atol=1e-10)
