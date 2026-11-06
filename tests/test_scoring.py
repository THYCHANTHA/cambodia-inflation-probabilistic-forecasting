import numpy as np
import pandas as pd
import pytest
from scipy import stats

from cambodia_inflation.evaluation.point import mae, mase, mase_scale, rmse
from cambodia_inflation.evaluation.scoring import (
    coverage,
    crps_gaussian,
    crps_sample,
    interval_score,
    mean_width,
    pinball_loss,
    pit_values,
    quantile_bin_counts,
    wis,
    wis_via_pinball,
)


# 14. CRPS / WIS / pinball consistency
def test_pinball_hand_values():
    assert pinball_loss(2.0, 3.0, 0.9) == pytest.approx(0.9)  # y above q: tau * (y - q)
    assert pinball_loss(2.0, 1.0, 0.9) == pytest.approx(0.1)  # y below q: (1 - tau) * (q - y)
    assert pinball_loss(2.0, 2.0, 0.3) == 0.0
    assert pinball_loss(0.0, 4.0, 0.5) == pytest.approx(0.5 * 4.0)


def test_interval_score_hand_values():
    assert interval_score(1.0, 3.0, 2.0, 0.2) == pytest.approx(2.0)
    assert interval_score(1.0, 3.0, 0.0, 0.2) == pytest.approx(2.0 + 10.0 * 1.0)
    assert interval_score(1.0, 3.0, 4.5, 0.1) == pytest.approx(2.0 + 20.0 * 1.5)
    with pytest.raises(ValueError):
        interval_score(3.0, 1.0, 2.0, 0.2)


def test_wis_equals_scaled_sum_of_pinball_losses(levels):
    rng = np.random.default_rng(5)
    for _ in range(2000):
        q = np.sort(rng.normal(2.0, 3.0, len(levels)))
        y = rng.normal(2.0, 4.0)
        assert wis(q, levels, y) == pytest.approx(wis_via_pinball(q, levels, y), abs=1e-12)


def test_wis_of_point_mass_at_truth_is_zero(levels):
    assert wis(np.full(7, 1.5), levels, 1.5) == 0.0


def test_wis_requires_symmetric_levels():
    with pytest.raises(ValueError):
        wis([0.0, 1.0, 2.0], [0.1, 0.5, 0.8], 1.0)


def test_crps_sample_matches_brute_force():
    rng = np.random.default_rng(1)
    x = rng.normal(size=60)
    y = 0.3
    brute = np.mean(np.abs(x - y)) - 0.5 * np.mean(np.abs(x[:, None] - x[None, :]))
    assert crps_sample(x, y) == pytest.approx(brute, abs=1e-12)


def test_crps_of_point_mass_is_absolute_error():
    assert crps_sample(np.full(10, 2.0), 5.0) == pytest.approx(3.0)


@pytest.mark.parametrize(("mu", "sigma", "y"), [(0.0, 1.0, 0.0), (2.0, 0.5, 3.1), (-1.0, 3.0, 4.0)])
def test_gaussian_crps_agrees_with_samples_and_quantile_integral(mu, sigma, y):
    exact = float(crps_gaussian(mu, sigma, y))
    rng = np.random.default_rng(2)
    assert crps_sample(rng.normal(mu, sigma, 200_000), y) == pytest.approx(exact, rel=0.01)
    tau = (np.arange(20_000) + 0.5) / 20_000  # midpoint rule for 2 * int_0^1 pinball dtau
    q = stats.norm.ppf(tau, mu, sigma)
    assert 2 * np.mean(pinball_loss(q, y, tau)) == pytest.approx(exact, rel=1e-3)


def test_gaussian_crps_known_value():
    # CRPS(N(0,1), 0) = 2 phi(0) - 1/sqrt(pi) = (sqrt(2) - 1)/sqrt(pi)
    assert float(crps_gaussian(0.0, 1.0, 0.0)) == pytest.approx((np.sqrt(2) - 1) / np.sqrt(np.pi))
    with pytest.raises(ValueError):
        crps_gaussian(0.0, 0.0, 1.0)


def test_coverage_and_width():
    lo, hi = np.array([0, 0, 0, 0]), np.array([1, 1, 2, 2])
    y = np.array([0.5, 1.0, 2.5, -0.1])  # inside, on boundary (inside), above, below
    assert coverage(lo, hi, y) == 0.5
    assert mean_width(lo, hi) == 1.5


def test_quantile_bins(levels):
    qm = np.tile(np.arange(7.0), (4, 1))  # quantiles 0..6
    y = np.array([-1.0, 0.0, 3.5, 10.0])  # bins 0, 0 (y == q1), 4, 7
    counts, expected = quantile_bin_counts(qm, y, levels)
    assert counts.tolist() == [2, 0, 0, 0, 1, 0, 0, 1]
    np.testing.assert_allclose(expected, [0.05, 0.05, 0.15, 0.25, 0.25, 0.15, 0.05, 0.05])
    assert expected.sum() == pytest.approx(1.0)


def test_calibrated_gaussian_forecasts_cover_nominally(levels):
    # Prediction interval coverage: with correctly specified distributions, empirical coverage ~ nominal.
    rng = np.random.default_rng(9)
    n = 20_000
    mu = rng.normal(0, 2, n)
    y = mu + rng.normal(0, 1, n)
    qm = mu[:, None] + stats.norm.ppf(levels)[None, :]
    assert coverage(qm[:, 0], qm[:, 6], y) == pytest.approx(0.90, abs=0.01)
    assert coverage(qm[:, 1], qm[:, 5], y) == pytest.approx(0.80, abs=0.01)
    assert coverage(qm[:, 2], qm[:, 4], y) == pytest.approx(0.50, abs=0.015)
    counts, expected = quantile_bin_counts(qm, y, levels)
    np.testing.assert_allclose(counts / n, expected, atol=0.012)
    u = pit_values(stats.norm.cdf(y - mu))
    assert stats.kstest(u, "uniform").pvalue > 0.001
    # an overconfident forecaster under-covers
    narrow = mu[:, None] + 0.5 * stats.norm.ppf(levels)[None, :]
    assert coverage(narrow[:, 0], narrow[:, 6], y) < 0.70


def test_pit_values_must_be_probabilities():
    with pytest.raises(ValueError):
        pit_values([0.2, 1.2])


def test_point_metrics():
    e = np.array([1.0, -1.0, 2.0, -2.0])
    assert mae(e) == 1.5
    assert rmse(e) == pytest.approx(np.sqrt(2.5))
    y = pd.Series([0.0, 1.0, 3.0, 6.0])
    assert mase_scale(y, 1) == pytest.approx((1 + 2 + 3) / 3)
    assert mase(e, 2.0) == 0.75
    with pytest.raises(ValueError):
        mase_scale(pd.Series([1.0, 1.0, 1.0]), 1)
