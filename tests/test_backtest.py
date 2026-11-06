import numpy as np
import pandas as pd
import pytest

from cambodia_inflation.config import load_protocol
from cambodia_inflation.forecasting.backtest import quantile_columns, run_backtest
from cambodia_inflation.forecasting.quantiles import QuantileError
from cambodia_inflation.models.benchmarks import KnownComponentSeasonalMean, PersistenceEmpirical
from cambodia_inflation.statistics.transforms import yoy_simple

PROTOCOL = load_protocol()
SEED = PROTOCOL.seed


class SpyModel:
    """Records what it is given and returns random but ordered quantiles."""

    name = "spy"
    version = "test"

    def __init__(self):
        self.calls = []

    def forecast(self, history, steps_ahead, levels, rng):
        self.calls.append((history.index.min(), history.index.max(), steps_ahead, float(history.iloc[-1])))
        return np.sort(rng.normal(0.0, 1.0, len(levels)))


class CrossingModel:
    name = "crossing"
    version = "test"

    def forecast(self, history, steps_ahead, levels, rng):
        return np.linspace(1.0, -1.0, len(levels))


# 11. No future information leakage
@pytest.mark.parametrize("spec_name", ["MAIN", "ROLL", "P2010-96", "LAG2"])
def test_model_never_sees_data_after_cutoff(cpi_core_shape, levels, spec_name):
    spy = SpyModel()
    out = run_backtest(cpi_core_shape, spy, PROTOCOL.windows[spec_name], [1, 12], levels, SEED)
    assert len(spy.calls) == len(out)
    assert (out["history_last"] == out["cutoff"]).all()
    for (_, last, steps, _), (_, row) in zip(spy.calls, out.iterrows(), strict=True):
        assert last == row["cutoff"] < row["target"]
        assert steps == row["steps_ahead"]


@pytest.mark.parametrize("model", [KnownComponentSeasonalMean(), PersistenceEmpirical()])
def test_changing_the_future_does_not_change_past_forecasts(cpi_core_shape, levels, model):
    change_from = pd.Period("2019-07", freq="M")
    altered = cpi_core_shape.copy()
    altered.loc[altered.index >= change_from] *= 1.25  # a large level shift after the change point
    spec = PROTOCOL.windows["MAIN"]
    a = run_backtest(cpi_core_shape, model, spec, [1, 6, 12], levels, SEED)
    b = run_backtest(altered, model, spec, [1, 6, 12], levels, SEED)
    qcols = quantile_columns(a)
    before = a["cutoff"] < change_from
    assert before.sum() > 0 and (~before).sum() > 0
    pd.testing.assert_frame_equal(a.loc[before, qcols], b.loc[before, qcols])
    # and the change is visible once the cutoff includes it
    assert not np.allclose(a.loc[~before, qcols].to_numpy(), b.loc[~before, qcols].to_numpy())


# 12. Forecast-origin alignment of outcomes
def test_outcome_is_yoy_at_target(cpi_core_shape, levels):
    out = run_backtest(cpi_core_shape, SpyModel(), PROTOCOL.windows["LAG2"], [3], levels, SEED)
    y = yoy_simple(cpi_core_shape)
    for _, row in out.iterrows():
        assert row["y_true"] == pytest.approx(y.loc[row["target"]])
        assert row["target"] == row["origin"] + 3 == row["cutoff"] + 5


# 16. Deterministic reproducibility
def test_same_seed_same_results(cpi_core_shape, levels):
    spec = PROTOCOL.windows["MAIN"]
    a = run_backtest(cpi_core_shape, SpyModel(), spec, [1, 12], levels, SEED)
    b = run_backtest(cpi_core_shape, SpyModel(), spec, [1, 12], levels, SEED)
    pd.testing.assert_frame_equal(a, b)
    c = run_backtest(cpi_core_shape, SpyModel(), spec, [1, 12], levels, SEED + 1)
    assert not np.allclose(a[quantile_columns(a)].to_numpy(), c[quantile_columns(c)].to_numpy())


def test_results_do_not_depend_on_horizon_order(cpi_core_shape, levels):
    spec = PROTOCOL.windows["MAIN"]
    a = run_backtest(cpi_core_shape, SpyModel(), spec, [1, 12], levels, SEED)
    b = run_backtest(cpi_core_shape, SpyModel(), spec, [12, 1], levels, SEED)
    key = ["horizon", "origin"]
    pd.testing.assert_frame_equal(a.sort_values(key).reset_index(drop=True), b.sort_values(key).reset_index(drop=True))


def test_crossing_quantiles_are_rejected(cpi_core_shape, levels):
    with pytest.raises(QuantileError, match="crossing"):
        run_backtest(cpi_core_shape, CrossingModel(), PROTOCOL.windows["MAIN"], [1], levels, SEED)


def test_reference_benchmarks_run_on_96_and_120_windows(cpi_core_shape, levels):
    for name in ("P2010-96", "P2010-120"):
        out = run_backtest(cpi_core_shape, KnownComponentSeasonalMean(), PROTOCOL.windows[name], [1, 12], levels, SEED)
        q = out[quantile_columns(out)].to_numpy()
        assert np.all(np.isfinite(q)) and np.all(np.diff(q, axis=1) >= 0)
        assert out["train_start"].eq(pd.Period("2010-01", freq="M")).all()


def test_known_component_benchmark_is_exact_when_series_is_deterministic(levels):
    # Identical calendar pattern every year: seasonal means are exact, so all quantiles collapse onto the truth.
    idx = pd.period_range("2005-01", periods=200, freq="M")
    x = np.tile([0.5, -0.2, 0.3, 0.1, 0.0, 0.4, -0.1, 0.2, 0.3, 0.6, -0.3, 0.2], 17)[:200]
    x[0] = 0.0
    cpi = pd.Series(100 * np.exp(np.cumsum(x) / 100), index=idx)
    spec = PROTOCOL.windows["MAIN"]
    out = run_backtest(cpi, KnownComponentSeasonalMean(), spec, [1, 6, 12], levels, SEED)
    q = out[quantile_columns(out)].to_numpy()
    np.testing.assert_allclose(q, np.repeat(out["y_true"].to_numpy()[:, None], q.shape[1], axis=1), atol=1e-9)
