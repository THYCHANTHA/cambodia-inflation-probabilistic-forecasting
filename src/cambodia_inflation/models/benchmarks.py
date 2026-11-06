"""Benchmarks B0(b) and B2 of protocol v1.0, section 6.1.

Both use only the ``history`` passed in (index values up to the cutoff). Their error distributions are built from
in-sample errors within the training window, so they are simple reference distributions, not calibrated models.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from cambodia_inflation.forecasting.identity import (
    known_component,
    unknown_component_from_path,
    unknown_window_steps,
)
from cambodia_inflation.statistics.transforms import log_to_simple, monthly_log_change, yoy_simple


class InsufficientHistoryError(ValueError):
    """Too few observations to build the model's error distribution."""


class PersistenceEmpirical:
    """B0(b): y_{C+k} = y_C plus empirical quantiles of past k-step changes y_{s+k} - y_s, s + k <= C."""

    name = "B0b-persistence-empirical"
    version = "0.1"

    def __init__(self, min_errors: int = 24) -> None:
        self.min_errors = min_errors

    def forecast(self, history: pd.Series, steps_ahead: int, levels: np.ndarray, rng: np.random.Generator):
        y = yoy_simple(history).dropna()
        changes = (y - y.shift(steps_ahead)).dropna().to_numpy()
        if len(changes) < self.min_errors:
            raise InsufficientHistoryError(f"{len(changes)} past changes, need {self.min_errors}")
        return float(y.iloc[-1]) + np.quantile(changes, levels)


class KnownComponentSeasonalMean:
    """B2: K_{C,k} plus calendar-month means of x for the future months in the target window.

    Distribution: empirical quantiles of past errors of U (realised U minus seasonal-mean prediction) for every
    in-window cutoff s with s + k <= C. Quantiles are formed in log-YoY space and mapped exactly to simple YoY.
    """

    name = "B2-known-component-seasonal-mean"
    version = "0.1"

    def __init__(self, min_errors: int = 24) -> None:
        self.min_errors = min_errors

    def forecast(self, history: pd.Series, steps_ahead: int, levels: np.ndarray, rng: np.random.Generator):
        k = steps_ahead
        x = monthly_log_change(history).dropna()
        xv = x.to_numpy()
        months = x.index.month.to_numpy()
        means = np.full(13, np.nan)
        for m in range(1, 13):
            sel = xv[months == m]
            if len(sel) == 0:
                raise InsufficientHistoryError(f"no observation for calendar month {m}")
            means[m] = sel.mean()
        steps = unknown_window_steps(k)

        def predicted_u(cutoff_month: int) -> float:
            future = (cutoff_month - 1 + steps) % 12 + 1
            return float(means[future].sum())

        errors = []
        for pos in range(len(xv) - k):
            realised = float(unknown_component_from_path(xv[pos + 1 : pos + k + 1], k))
            errors.append(realised - predicted_u(int(months[pos])))
        if len(errors) < self.min_errors:
            raise InsufficientHistoryError(f"{len(errors)} past errors, need {self.min_errors}")
        centre = known_component(xv, k) + predicted_u(int(months[-1]))
        return log_to_simple(centre + np.quantile(np.asarray(errors), levels))
