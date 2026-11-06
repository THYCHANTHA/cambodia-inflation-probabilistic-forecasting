"""Gate G2 checks on synthetic core/extension tables (values are invented, not NIS data)."""

import pandas as pd
import pytest

from cambodia_inflation.data.provenance import (
    SeriesCompatibilityError,
    SeriesDefinition,
    extend_series,
    make_observations,
)

SHA_A = "a" * 64
SHA_B = "b" * 64
WEIGHTS = (("food", 44.775), ("housing", 17.084), ("other", 38.141))
DEF = SeriesDefinition("Synthetic producer", "Synthetic city", "Oct-Dec 2006 = 100", WEIGHTS)


def _obs(start, values, source, sha):
    idx = pd.period_range(start, periods=len(values), freq="M")
    return make_observations(pd.Series(values, index=idx, dtype=float), source, f"{source}.csv", sha)


def _core():
    return _obs("2025-08", [210.00, 210.26, 211.30, 210.31, 211.53], "core", SHA_A)


def test_extension_appended_with_provenance():
    ext = _obs("2025-12", [211.527, 212.330, 213.900], "ext", SHA_B)
    res = extend_series(_core(), DEF, ext, DEF)
    combined = res.observations
    assert [str(p) for p in res.appended] == ["2026-01", "2026-02"]
    assert [str(p) for p in res.overlap_checked] == ["2025-12"]
    assert res.max_overlap_abs_diff == pytest.approx(0.003)
    # core value kept for the overlap month; every row keeps its own source
    assert combined.loc[pd.Period("2025-12", freq="M"), "cpi"] == 211.53
    assert combined.loc[pd.Period("2025-12", freq="M"), "source_id"] == "core"
    assert combined.loc[pd.Period("2026-02", freq="M"), "file_sha256"] == SHA_B
    assert combined["source_id"].value_counts().to_dict() == {"core": 5, "ext": 2}


def test_overlap_disagreement_rejected():
    ext = _obs("2025-12", [211.60, 212.33], "ext", SHA_B)
    with pytest.raises(SeriesCompatibilityError, match="disagree"):
        extend_series(_core(), DEF, ext, DEF)


@pytest.mark.parametrize(
    "other",
    [
        SeriesDefinition("Synthetic producer", "Whole country", "Oct-Dec 2006 = 100", WEIGHTS),
        SeriesDefinition("Synthetic producer", "Synthetic city", "2021 = 100", WEIGHTS),
        SeriesDefinition("Synthetic producer", "Synthetic city", "Oct-Dec 2006 = 100", (("food", 40.0),)),
    ],
)
def test_definition_change_rejected(other):
    ext = _obs("2025-12", [211.53, 212.33], "ext", SHA_B)
    with pytest.raises(SeriesCompatibilityError, match="definitions differ"):
        extend_series(_core(), DEF, ext, other)


def test_gap_after_core_rejected():
    ext = _obs("2025-12", [211.53], "ext", SHA_B)
    gap = pd.concat([ext, _obs("2026-02", [213.9], "ext", SHA_B)])
    with pytest.raises(Exception, match=r"missing months|gap"):
        extend_series(_core(), DEF, gap, DEF)


def test_overlap_required_by_default():
    ext = _obs("2026-01", [212.33], "ext", SHA_B)
    with pytest.raises(SeriesCompatibilityError, match="no overlap"):
        extend_series(_core(), DEF, ext, DEF)
    assert extend_series(_core(), DEF, ext, DEF, require_overlap=False).appended == (pd.Period("2026-01", "M"),)


def test_bad_digest_rejected():
    with pytest.raises(ValueError, match="64"):
        _obs("2025-01", [100.0], "x", "abc")
