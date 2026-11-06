import numpy as np
import pytest

from cambodia_inflation.forecasting.identity import (
    decompose_realised,
    known_component,
    n_known,
    n_unknown,
    quantiles_log_to_simple,
    unknown_window_steps,
    yoy_log_from_paths,
    yoy_simple_from_paths,
)
from cambodia_inflation.statistics.transforms import monthly_log_change, yoy_log, yoy_simple

KS = [1, 2, 3, 6, 11, 12, 13, 15]


# 9. Exact forecast identity
@pytest.mark.parametrize("k", KS)
def test_known_plus_unknown_equals_realised_log_yoy(cpi_core_shape, k):
    x = monthly_log_change(cpi_core_shape).to_numpy()
    ylog = yoy_log(cpi_core_shape).to_numpy()
    ysimple = yoy_simple(cpi_core_shape).to_numpy()
    for cutoff in range(12, len(x) - k):
        known, unknown = decompose_realised(x, cutoff, k)
        assert known + unknown == pytest.approx(ylog[cutoff + k], abs=1e-10)
        future = x[cutoff + 1 : cutoff + k + 1][None, :]
        assert yoy_log_from_paths(x[: cutoff + 1], future, k)[0] == pytest.approx(ylog[cutoff + k], abs=1e-10)
        assert yoy_simple_from_paths(x[: cutoff + 1], future, k)[0] == pytest.approx(ysimple[cutoff + k], abs=1e-9)


def test_quantile_transform_is_exact_for_a_known_distribution():
    # Empirical quantiles of g(V) equal g(empirical quantiles of V) when g is increasing ('lower' interpolation).
    rng = np.random.default_rng(3)
    v = rng.normal(3.0, 2.0, 5001)
    lv = np.array([0.05, 0.25, 0.5, 0.75, 0.95])
    a = quantiles_log_to_simple(np.quantile(v, lv, method="lower"))
    b = np.quantile(quantiles_log_to_simple(v), lv, method="lower")
    np.testing.assert_allclose(a, b, atol=1e-12)


# 10. Known versus unknown monthly components
@pytest.mark.parametrize("k", KS)
def test_component_counts(k):
    if k <= 12:
        assert n_known(k) + n_unknown(k) == 12
    else:
        assert n_known(k) == 0 and n_unknown(k) == 12
    assert n_known(k) == max(12 - k, 0)
    steps = unknown_window_steps(k)
    assert len(steps) == min(k, 12) and steps[-1] == k


def test_known_component_uses_exactly_the_last_12_minus_k_values():
    x_hist = 2.0 ** np.arange(20)  # each subset has a unique sum
    for k in range(1, 12):
        assert known_component(x_hist, k) == x_hist[-(12 - k) :].sum()
        perturbed = x_hist.copy()
        perturbed[-(12 - k) - 1] += 1000.0  # just outside the known window
        assert known_component(perturbed, k) == known_component(x_hist, k)
    assert known_component(x_hist, 12) == 0.0
    assert known_component(x_hist, 14) == 0.0


def test_unknown_component_for_long_horizon_skips_months_outside_window():
    path = np.arange(1.0, 15.0)[None, :]  # steps 1..14
    # k = 14: window covers steps 3..14
    assert yoy_log_from_paths(np.zeros(5), path, 14)[0] == pytest.approx(np.arange(3.0, 15.0).sum())


@pytest.mark.parametrize("bad", [0, -1, 2.5])
def test_invalid_steps_rejected(bad):
    with pytest.raises(ValueError):
        n_known(bad)


def test_known_component_needs_enough_history():
    with pytest.raises(ValueError, match="at least"):
        known_component(np.ones(5), 1)
    with pytest.raises(ValueError, match="finite"):
        known_component(np.r_[np.ones(10), np.nan], 1)
