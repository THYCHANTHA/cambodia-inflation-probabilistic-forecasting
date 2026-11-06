import json
from datetime import UTC, datetime, timedelta

import pandas as pd
import pytest

from cambodia_inflation.models.benchmarks import KnownComponentSeasonalMean
from cambodia_inflation.prospective.registry import (
    PROJECT_ROOT,
    ForecastRegistry,
    ProspectiveError,
    PublicationCalendar,
    build_issuance,
)

ISSUE_TIME = datetime(2026, 11, 20, 3, 0, tzinfo=UTC)


def _calendar(last_published: str):
    """Synthetic calendar: month m published on the 15th of month m + 2 (illustrative lag only)."""
    months = pd.period_range("2005-01", last_published, freq="M")
    return PublicationCalendar(
        {m: datetime((m + 2).year, (m + 2).month, 15, tzinfo=UTC) for m in months},
        {m: "synthetic test calendar" for m in months},
    )


def _issue(history, calendar, when=ISSUE_TIME, horizons=(1, 3, 6, 12)):
    return build_issuance(
        KnownComponentSeasonalMean(),
        history,
        calendar,
        when,
        list(horizons),
        [0.05, 0.1, 0.25, 0.5, 0.75, 0.9, 0.95],
        20261106,
        "c" * 64,
        "synthetic-v1",
        "test",
        {"note": "synthetic"},
    )


@pytest.fixture
def registry(tmp_path):
    return ForecastRegistry(tmp_path / "prospective")


def test_issuance_records_all_required_fields(cpi_extended_shape):
    cal = _calendar("2026-09")  # Sep 2026 published 2026-11-15, before the issue time
    rec = _issue(cpi_extended_shape, cal)
    for key in (
        "issued_at_utc",
        "latest_published_month",
        "information_cutoff",
        "model_name",
        "model_version",
        "model_parameters",
        "data_sha256",
        "data_version",
        "code_version",
        "horizons",
        "quantile_levels",
        "forecasts",
        "content_sha256",
    ):
        assert key in rec
    assert rec["latest_published_month"] == rec["information_cutoff"] == "2026-09"
    assert rec["forecasts"]["12"]["target_month"] == "2027-09"
    assert set(rec["forecasts"]["3"]["central_intervals"]) == {"0.90", "0.80", "0.50"}


def test_unpublished_month_in_history_is_rejected(cpi_extended_shape):
    cal = _calendar("2026-09")
    early = datetime(2026, 11, 10, tzinfo=UTC)  # before Sep 2026 was published (15 Nov)
    assert cal.latest_published(early) == pd.Period("2026-08", freq="M")
    with pytest.raises(ProspectiveError, match="published"):
        _issue(cpi_extended_shape, cal, when=early)
    rec = _issue(cpi_extended_shape.iloc[:-1], cal, when=early)  # history truncated to Aug 2026 is allowed
    assert rec["information_cutoff"] == "2026-08"


def test_naive_timestamp_rejected(cpi_extended_shape):
    with pytest.raises(ProspectiveError, match="timezone"):
        _issue(cpi_extended_shape, _calendar("2026-09"), when=datetime(2026, 11, 20))


def test_records_are_never_overwritten(registry, cpi_extended_shape):
    rec = _issue(cpi_extended_shape, _calendar("2026-09"))
    issue_id = registry.save_issuance(rec)
    with pytest.raises(ProspectiveError, match="never overwritten"):
        registry.save_issuance(rec)
    assert registry.list_issuances() == [issue_id]
    assert registry.load_issuance(issue_id) == rec


def test_tampering_is_detected(registry, cpi_extended_shape):
    issue_id = registry.save_issuance(_issue(cpi_extended_shape, _calendar("2026-09")))
    path = registry.issuance_dir / f"{issue_id}.json"
    data = json.loads(path.read_text())
    data["forecasts"]["1"]["quantiles"][3] += 1.0
    path.write_text(json.dumps(data))
    with pytest.raises(ProspectiveError, match="hash"):
        registry.load_issuance(issue_id)


def test_outcome_recording_and_rules(registry, cpi_extended_shape):
    rec = _issue(cpi_extended_shape, _calendar("2026-09"))
    issue_id = registry.save_issuance(rec)
    with pytest.raises(ProspectiveError, match="before the forecast"):
        registry.record_outcome(issue_id, 1, 5.0, ISSUE_TIME - timedelta(days=1))
    q = rec["forecasts"]["1"]["quantiles"]
    out = registry.record_outcome(issue_id, 1, q[3], ISSUE_TIME + timedelta(days=60))
    assert out["pinball"]["0.50"] == 0.0
    assert all(out["inside_interval"].values())
    with pytest.raises(ProspectiveError, match="never overwritten"):
        registry.record_outcome(issue_id, 1, q[3], ISSUE_TIME + timedelta(days=61))
    with pytest.raises(ProspectiveError, match="no horizon"):
        registry.record_outcome(issue_id, 2, 1.0, ISSUE_TIME + timedelta(days=60))


def test_registry_inside_repository_refused():
    with pytest.raises(ProspectiveError, match="inside the repository"):
        ForecastRegistry(PROJECT_ROOT / "reports" / "prospective")
