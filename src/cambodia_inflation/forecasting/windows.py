"""Rolling-origin forecast windows (protocol v1.0, section 8).

Terminology. ``estimation_start``: first YoY month used for estimation. ``initial_window``: number of YoY observations
available at the first cutoff. ``cutoff`` C: last month whose index is in the information set. ``origin``: the month at
which the forecast is made, origin = C + publication_lag. ``horizon`` h: target = origin + h, so steps after the
cutoff k = h + publication_lag.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Literal

import pandas as pd

from cambodia_inflation.data.validation import assert_valid_cpi
from cambodia_inflation.statistics.transforms import WINDOW

Scheme = Literal["expanding", "rolling"]


@dataclass(frozen=True)
class WindowSpec:
    name: str
    estimation_start: pd.Period
    initial_window: int
    scheme: Scheme = "expanding"
    publication_lag: int = 0

    def __post_init__(self) -> None:
        if self.initial_window < 1:
            raise ValueError("initial_window must be positive")
        if self.scheme not in ("expanding", "rolling"):
            raise ValueError(f"unknown scheme {self.scheme!r}")
        if self.publication_lag < 0:
            raise ValueError("publication_lag must be >= 0")


@dataclass(frozen=True)
class ForecastOrigin:
    spec: str
    origin: pd.Period
    cutoff: pd.Period
    train_start: pd.Period
    horizon: int
    target: pd.Period

    @property
    def steps_ahead(self) -> int:
        """k = number of months from the cutoff to the target."""
        return int((self.target - self.cutoff).n)

    @property
    def n_train_targets(self) -> int:
        return int((self.cutoff - self.train_start).n) + 1


def first_cutoff(index: pd.PeriodIndex, spec: WindowSpec) -> pd.Period:
    first_yoy = index.min() + WINDOW
    start = max(first_yoy, spec.estimation_start)
    return start + (spec.initial_window - 1)


def forecast_origins(
    index: pd.PeriodIndex,
    spec: WindowSpec,
    horizon: int,
    last_target: pd.Period | None = None,
) -> list[ForecastOrigin]:
    """All origins for one horizon whose target lies at or before ``last_target`` (default: last month of ``index``)."""
    if horizon < 1:
        raise ValueError("horizon must be >= 1")
    end = index.max() if last_target is None else last_target
    first_yoy = index.min() + WINDOW
    est_start = max(first_yoy, spec.estimation_start)
    cutoff = first_cutoff(index, spec)
    out = []
    while True:
        origin = cutoff + spec.publication_lag
        target = origin + horizon
        if target > end:
            break
        train_start = est_start if spec.scheme == "expanding" else cutoff - (spec.initial_window - 1)
        out.append(ForecastOrigin(spec.name, origin, cutoff, train_start, horizon, target))
        cutoff = cutoff + 1
    return out


def information_set(cpi: pd.Series, fo: ForecastOrigin) -> pd.Series:
    """Index values a model may use: months train_start - 12 to the cutoff (12 earlier months give the first YoY)."""
    assert_valid_cpi(cpi)
    lo = fo.train_start - WINDOW
    if lo < cpi.index.min() or fo.cutoff > cpi.index.max():
        raise ValueError("information set extends outside the available series")
    view = cpi.loc[lo : fo.cutoff].copy()
    view.attrs = dict(cpi.attrs)
    return view


def split_of(fo: ForecastOrigin, dev_target_end: pd.Period, test_origin_start: pd.Period) -> str:
    """'dev' if the target is at or before dev_target_end, 'test' if the origin is at or after test_origin_start."""
    if fo.target <= dev_target_end:
        return "dev"
    if fo.origin >= test_origin_start:
        return "test"
    return "excluded"


def count_by_split(
    origins: Iterable[ForecastOrigin], dev_target_end: pd.Period, test_origin_start: pd.Period
) -> dict[str, int]:
    counts = {"dev": 0, "test": 0, "excluded": 0}
    for fo in origins:
        counts[split_of(fo, dev_target_end, test_origin_start)] += 1
    return counts
