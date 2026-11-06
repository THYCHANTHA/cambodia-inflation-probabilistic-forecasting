"""Validation of a monthly CPI index series.

A valid series is a ``pandas.Series`` with a monthly ``PeriodIndex`` that is strictly increasing, has no duplicate and
no missing month between its first and last observation, and whose values are finite and strictly positive.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


class CPIValidationError(ValueError):
    """The series fails one or more validation checks."""


@dataclass(frozen=True)
class ValidationReport:
    n_obs: int
    start: pd.Period | None
    end: pd.Period | None
    duplicates: tuple[pd.Period, ...]
    missing: tuple[pd.Period, ...]
    non_positive: tuple[pd.Period, ...]
    non_finite: tuple[pd.Period, ...]
    is_sorted: bool
    is_monthly: bool

    @property
    def ok(self) -> bool:
        return (
            self.n_obs > 0
            and self.is_monthly
            and self.is_sorted
            and not self.duplicates
            and not self.missing
            and not self.non_positive
            and not self.non_finite
        )

    def problems(self) -> list[str]:
        out = []
        if self.n_obs == 0:
            out.append("empty series")
        if not self.is_monthly:
            out.append("index is not a monthly PeriodIndex")
        if not self.is_sorted:
            out.append("index is not in increasing order")
        if self.duplicates:
            out.append(f"duplicate months: {[str(p) for p in self.duplicates]}")
        if self.missing:
            out.append(f"missing months: {[str(p) for p in self.missing]}")
        if self.non_positive:
            out.append(f"non-positive index values: {[str(p) for p in self.non_positive]}")
        if self.non_finite:
            out.append(f"non-finite index values: {[str(p) for p in self.non_finite]}")
        return out


def _is_monthly(index: pd.Index) -> bool:
    return isinstance(index, pd.PeriodIndex) and index.freqstr == "M"


def find_duplicate_months(index: pd.PeriodIndex) -> tuple[pd.Period, ...]:
    dup = index[index.duplicated(keep="first")]
    return tuple(sorted(set(dup)))


def find_missing_months(index: pd.PeriodIndex) -> tuple[pd.Period, ...]:
    if len(index) == 0:
        return ()
    full = pd.period_range(index.min(), index.max(), freq="M")
    return tuple(full.difference(index.unique()))


def validate_cpi(series: pd.Series) -> ValidationReport:
    index = series.index
    monthly = _is_monthly(index)
    if not monthly or len(series) == 0:
        return ValidationReport(len(series), None, None, (), (), (), (), True, monthly)
    values = series.to_numpy(dtype=float)
    finite = np.isfinite(values)
    non_finite = tuple(index[~finite])
    non_positive = tuple(index[finite & (values <= 0)])
    ordinals = index.asi8
    is_sorted = bool(np.all(np.diff(ordinals) > 0)) if len(ordinals) > 1 else True
    return ValidationReport(
        n_obs=len(series),
        start=index.min(),
        end=index.max(),
        duplicates=find_duplicate_months(index),
        missing=find_missing_months(index),
        non_positive=non_positive,
        non_finite=non_finite,
        is_sorted=is_sorted,
        is_monthly=monthly,
    )


def assert_valid_cpi(series: pd.Series) -> None:
    report = validate_cpi(series)
    if not report.ok:
        raise CPIValidationError("; ".join(report.problems()))
