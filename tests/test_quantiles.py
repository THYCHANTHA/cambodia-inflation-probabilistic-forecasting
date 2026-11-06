import numpy as np
import pytest

from cambodia_inflation.forecasting.quantiles import (
    PROTOCOL_LEVELS,
    QuantileError,
    central_intervals,
    check_quantiles,
    empirical_quantiles,
    rearrange,
    validate_levels,
)


# 13. Quantile ordering
def test_protocol_levels_valid_and_symmetric():
    lv = validate_levels(PROTOCOL_LEVELS)
    np.testing.assert_allclose(lv + lv[::-1], 1.0)
    assert central_intervals(lv) == {0.9: (0, 6), 0.8: (1, 5), 0.5: (2, 4)}


@pytest.mark.parametrize("bad", [[0.5, 0.5], [0.0, 0.5], [0.5, 1.0], [0.9, 0.1], []])
def test_invalid_levels_rejected(bad):
    with pytest.raises(QuantileError):
        validate_levels(bad)


def test_ordered_quantiles_accepted_including_ties(levels):
    q = check_quantiles([1, 2, 2, 3, 4, 4, 5], levels)
    assert q.dtype == float


@pytest.mark.parametrize(
    ("values", "match"),
    [([1, 2, 3, 2.9, 4, 5, 6], "crossing"), ([1, 2, 3, np.nan, 4, 5, 6], "finite"), ([1, 2, 3], "levels")],
)
def test_bad_quantiles_rejected(levels, values, match):
    with pytest.raises(QuantileError, match=match):
        check_quantiles(values, levels)


def test_rearrangement_counts_crossings():
    q, n = rearrange([1.0, 3.0, 2.0, 4.0, 3.5])
    assert n == 2
    assert q.tolist() == [1.0, 2.0, 3.0, 3.5, 4.0]


def test_empirical_quantiles_are_ordered(levels):
    rng = np.random.default_rng(0)
    q = empirical_quantiles(rng.standard_t(3, 500), levels)
    assert np.all(np.diff(q) >= 0)
    with pytest.raises(QuantileError):
        empirical_quantiles(np.array([]), levels)
