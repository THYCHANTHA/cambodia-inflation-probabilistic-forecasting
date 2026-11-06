"""Historical pseudo-out-of-sample backtest loop.

A model receives only :func:`windows.information_set` for each origin (index values up to the cutoff) and the number of
steps from the cutoff to the target. It returns quantiles of the simple YoY rate at the target. Outcomes are looked up
by the loop after the forecast is made and are never passed to the model.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import Protocol

import numpy as np
import pandas as pd

from cambodia_inflation.forecasting.quantiles import check_quantiles, validate_levels
from cambodia_inflation.forecasting.windows import WindowSpec, forecast_origins, information_set
from cambodia_inflation.statistics.transforms import yoy_simple

log = logging.getLogger(__name__)


class ForecastModel(Protocol):
    name: str
    version: str

    def forecast(
        self, history: pd.Series, steps_ahead: int, levels: np.ndarray, rng: np.random.Generator
    ) -> np.ndarray: ...


def forecast_rng(seed: int, origin: pd.Period, horizon: int) -> np.random.Generator:
    """Generator seeded by (seed, origin, horizon): results do not depend on the order in which forecasts are run."""
    return np.random.default_rng([seed, int(origin.ordinal), horizon])


def run_backtest(
    cpi: pd.Series,
    model: ForecastModel,
    spec: WindowSpec,
    horizons: Sequence[int],
    levels: Sequence[float],
    seed: int,
) -> pd.DataFrame:
    """One row per (origin, horizon) with the quantiles, the realised YoY and window metadata."""
    lv = validate_levels(levels)
    outcome = yoy_simple(cpi)
    rows = []
    for h in horizons:
        origins = forecast_origins(cpi.index, spec, h)
        log.info("%s %s h=%d: %d origins", model.name, spec.name, h, len(origins))
        for fo in origins:
            history = information_set(cpi, fo)
            q = model.forecast(history, fo.steps_ahead, lv, forecast_rng(seed, fo.origin, h))
            q = check_quantiles(q, lv)
            row = {
                "model": model.name,
                "model_version": model.version,
                "spec": spec.name,
                "origin": fo.origin,
                "cutoff": fo.cutoff,
                "train_start": fo.train_start,
                "horizon": h,
                "steps_ahead": fo.steps_ahead,
                "target": fo.target,
                "history_last": history.index.max(),
                "y_true": float(outcome.loc[fo.target]),
            }
            row.update({f"q{lvl:.2f}": float(v) for lvl, v in zip(lv, q, strict=True)})
            rows.append(row)
    return pd.DataFrame(rows)


def quantile_columns(frame: pd.DataFrame) -> list[str]:
    return [c for c in frame.columns if c.startswith("q") and c[1:].replace(".", "", 1).isdigit()]
