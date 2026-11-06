from itertools import pairwise

import pandas as pd
import pytest

from cambodia_inflation.config import load_protocol
from cambodia_inflation.forecasting.windows import (
    WindowSpec,
    count_by_split,
    first_cutoff,
    forecast_origins,
    information_set,
)

M = lambda s: pd.Period(s, freq="M")  # noqa: E731
PROTOCOL = load_protocol()
DEV_END, TEST_START = PROTOCOL.dev_target_end, PROTOCOL.test_origin_start


# 15. Rolling-window boundaries (all specifications of protocol v1.0, table 8.2)
@pytest.mark.parametrize(
    ("spec_name", "first"),
    [("MAIN", "2015-12"), ("ROLL", "2015-12"), ("P2010-96", "2017-12"), ("P2010-120", "2019-12"), ("LAG2", "2015-12")],
)
def test_first_cutoff_per_spec(cpi_core_shape, spec_name, first):
    spec = PROTOCOL.windows[spec_name]
    assert first_cutoff(cpi_core_shape.index, spec) == M(first)
    fo = forecast_origins(cpi_core_shape.index, spec, 1)[0]
    assert fo.cutoff == M(first)
    assert fo.n_train_targets == spec.initial_window


def test_expanding_window_keeps_start_and_grows(cpi_core_shape):
    for name in ("MAIN", "P2010-96", "P2010-120"):
        spec = PROTOCOL.windows[name]
        origins = forecast_origins(cpi_core_shape.index, spec, 3)
        assert {fo.train_start for fo in origins} == {spec.estimation_start}
        sizes = [fo.n_train_targets for fo in origins]
        assert sizes[0] == spec.initial_window
        assert all(b - a == 1 for a, b in pairwise(sizes))


def test_rolling_window_has_fixed_length(cpi_core_shape):
    origins = forecast_origins(cpi_core_shape.index, PROTOCOL.windows["ROLL"], 6)
    assert {fo.n_train_targets for fo in origins} == {120}
    assert origins[1].train_start == origins[0].train_start + 1


def test_96_and_120_post_2010_windows_both_have_test_origins(cpi_core_shape):
    for name in ("P2010-96", "P2010-120"):
        for h in PROTOCOL.horizons:
            counts = count_by_split(
                forecast_origins(cpi_core_shape.index, PROTOCOL.windows[name], h), DEV_END, TEST_START
            )
            assert counts["test"] > 0


def test_last_target_is_end_of_sample(cpi_core_shape):
    for h in PROTOCOL.horizons:
        origins = forecast_origins(cpi_core_shape.index, PROTOCOL.windows["MAIN"], h)
        assert origins[-1].target == M("2025-12")
        assert origins[-1].origin == M("2025-12") - h


def test_window_too_long_for_series_gives_no_origins():
    idx = pd.period_range("2005-01", "2010-12", freq="M")
    spec = WindowSpec("X", M("2006-01"), 120)
    assert forecast_origins(idx, spec, 1) == []


# Counts stated in protocol v1.0 section 8.3 (core and extended samples)
@pytest.mark.parametrize(
    ("fixture", "expected"),
    [("cpi_core_shape", {1: 71, 3: 69, 6: 66, 12: 60}), ("cpi_extended_shape", {1: 80, 3: 78, 6: 75, 12: 69})],
)
def test_test_set_sizes_match_protocol(request, fixture, expected):
    cpi = request.getfixturevalue(fixture)
    for h, n in expected.items():
        counts = count_by_split(forecast_origins(cpi.index, PROTOCOL.windows["MAIN"], h), DEV_END, TEST_START)
        assert counts["test"] == n


@pytest.mark.parametrize(
    ("spec_name", "expected"),
    [
        ("MAIN", {1: 48, 3: 46, 6: 43, 12: 37}),
        ("P2010-96", {1: 24, 3: 22, 6: 19, 12: 13}),
        ("P2010-120", {1: 0, 3: 0, 6: 0, 12: 0}),
    ],
)
def test_dev_set_sizes_match_protocol(cpi_core_shape, spec_name, expected):
    for h, n in expected.items():
        origins = forecast_origins(cpi_core_shape.index, PROTOCOL.windows[spec_name], h)
        assert count_by_split(origins, DEV_END, TEST_START)["dev"] == n


def test_dev_and_test_never_share_information(cpi_core_shape):
    # No dev forecast has a target after the dev period; no test forecast has an origin before the test period.
    for h in PROTOCOL.horizons:
        for fo in forecast_origins(cpi_core_shape.index, PROTOCOL.windows["MAIN"], h):
            if fo.target <= DEV_END:
                assert fo.origin < TEST_START
            if fo.origin >= TEST_START:
                assert fo.target > DEV_END


# 12. Forecast-origin alignment
@pytest.mark.parametrize("spec_name", ["MAIN", "LAG2"])
def test_target_and_steps_alignment(cpi_core_shape, spec_name):
    spec = PROTOCOL.windows[spec_name]
    for h in PROTOCOL.horizons:
        for fo in forecast_origins(cpi_core_shape.index, spec, h):
            assert fo.origin == fo.cutoff + spec.publication_lag
            assert fo.target == fo.origin + h
            assert fo.steps_ahead == h + spec.publication_lag


def test_information_set_bounds(cpi_core_shape):
    fo = forecast_origins(cpi_core_shape.index, PROTOCOL.windows["LAG2"], 6)[10]
    view = information_set(cpi_core_shape, fo)
    assert view.index.max() == fo.cutoff == fo.origin - 2
    assert view.index.min() == fo.train_start - 12
    assert view.attrs.get("synthetic") is True
