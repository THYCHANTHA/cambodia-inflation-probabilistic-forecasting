import numpy as np
import pandas as pd
import pytest

from cambodia_inflation.data.validation import (
    CPIValidationError,
    assert_valid_cpi,
    find_duplicate_months,
    find_missing_months,
    validate_cpi,
)


def _series(months, values):
    return pd.Series(values, index=pd.PeriodIndex(months, freq="M"), dtype=float)


def test_valid_series_passes(cpi_core_shape):
    report = validate_cpi(cpi_core_shape)
    assert report.ok, report.problems()
    assert report.n_obs == 252
    assert str(report.start) == "2005-01" and str(report.end) == "2025-12"


# 3. Monthly frequency
def test_non_monthly_index_rejected():
    s = pd.Series([100.0, 101.0], index=pd.DatetimeIndex(["2005-01-01", "2005-02-01"]))
    report = validate_cpi(s)
    assert not report.ok and not report.is_monthly
    q = pd.Series([100.0, 101.0], index=pd.PeriodIndex(["2005Q1", "2005Q2"], freq="Q"))
    assert not validate_cpi(q).is_monthly


def test_unsorted_index_rejected():
    s = _series(["2005-02", "2005-01", "2005-03"], [101, 100, 102])
    report = validate_cpi(s)
    assert not report.is_sorted and not report.ok


# 4. Missing months
def test_missing_months_found():
    s = _series(["2005-01", "2005-02", "2005-05", "2005-06"], [100, 101, 102, 103])
    assert [str(p) for p in find_missing_months(s.index)] == ["2005-03", "2005-04"]
    with pytest.raises(CPIValidationError, match="missing months"):
        assert_valid_cpi(s)


def test_missing_month_across_year_boundary():
    s = _series(["2005-11", "2006-01"], [100, 101])
    assert [str(p) for p in find_missing_months(s.index)] == ["2005-12"]


# 5. Duplicate months
def test_duplicate_months_found():
    s = _series(["2005-01", "2005-02", "2005-02", "2005-03"], [100, 101, 101.5, 102])
    assert [str(p) for p in find_duplicate_months(s.index)] == ["2005-02"]
    report = validate_cpi(s)
    assert not report.ok
    assert not report.is_sorted  # a repeated month is also not strictly increasing


# 6. Index positivity and finiteness
@pytest.mark.parametrize("bad", [0.0, -5.0])
def test_non_positive_values_rejected(bad):
    s = _series(["2005-01", "2005-02", "2005-03"], [100.0, bad, 102.0])
    report = validate_cpi(s)
    assert [str(p) for p in report.non_positive] == ["2005-02"]
    with pytest.raises(CPIValidationError, match="non-positive"):
        assert_valid_cpi(s)


@pytest.mark.parametrize("bad", [np.nan, np.inf])
def test_non_finite_values_rejected(bad):
    s = _series(["2005-01", "2005-02"], [100.0, bad])
    assert [str(p) for p in validate_cpi(s).non_finite] == ["2005-02"]


def test_empty_series_rejected():
    s = pd.Series([], index=pd.PeriodIndex([], freq="M"), dtype=float)
    assert not validate_cpi(s).ok
