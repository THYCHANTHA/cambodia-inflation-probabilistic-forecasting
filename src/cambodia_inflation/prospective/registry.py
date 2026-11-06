"""Append-only registry of prospective forecasts.

Rules enforced here (protocol v1.0, section 10):
- the information cutoff is never later than the latest month published at the issuance time (publication calendar);
- the data passed to the model contain no month after the cutoff;
- an issuance file is created once and never overwritten; outcomes are separate files, also created once;
- an outcome published before the issuance time is rejected;
- every record carries a SHA-256 of its own content, checked on load;
- the registry directory must lie outside the repository (records stay local and private).
"""

from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from cambodia_inflation.evaluation.scoring import pinball_loss, wis
from cambodia_inflation.forecasting.backtest import ForecastModel, forecast_rng
from cambodia_inflation.forecasting.quantiles import central_intervals, check_quantiles, validate_levels

RECORD_TYPE = "prospective"
PROJECT_ROOT = Path(__file__).resolve().parents[3]


class ProspectiveError(ValueError):
    """An issuance or outcome would break a registry rule."""


def default_registry_root() -> Path:
    env = os.environ.get("P11_PROSPECTIVE_DIR")
    if env:
        return Path(env)
    return Path.home() / "portfolio-data" / "p11-inflation" / "prospective"


def _require_utc(ts: datetime) -> datetime:
    if ts.tzinfo is None or ts.utcoffset() is None:
        raise ProspectiveError("timestamps must be timezone-aware")
    return ts.astimezone(UTC)


@dataclass(frozen=True)
class PublicationCalendar:
    """Month -> date-time at which its index was first publicly available, with the evidence for that date."""

    published: Mapping[pd.Period, datetime]
    evidence: Mapping[pd.Period, str] = field(default_factory=dict)

    def latest_published(self, at: datetime) -> pd.Period | None:
        at = _require_utc(at)
        months = [m for m, ts in self.published.items() if _require_utc(ts) <= at]
        return max(months) if months else None

    def published_at(self, month: pd.Period) -> datetime | None:
        ts = self.published.get(month)
        return None if ts is None else _require_utc(ts)


def _canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _with_hash(record: dict) -> dict:
    body = {k: v for k, v in record.items() if k != "content_sha256"}
    return {**body, "content_sha256": hashlib.sha256(_canonical(body).encode()).hexdigest()}


def _verify_hash(record: dict) -> None:
    if _with_hash(record)["content_sha256"] != record.get("content_sha256"):
        raise ProspectiveError("record content hash does not match (file modified?)")


def build_issuance(
    model: ForecastModel,
    history: pd.Series,
    calendar: PublicationCalendar,
    issued_at: datetime,
    horizons: Sequence[int],
    levels: Sequence[float],
    seed: int,
    data_sha256: str,
    data_version: str,
    code_version: str,
    model_parameters: Mapping[str, Any] | None = None,
) -> dict:
    """Run the model at the information cutoff and return a hashed issuance record (not yet saved)."""
    issued_at = _require_utc(issued_at)
    latest = calendar.latest_published(issued_at)
    if latest is None:
        raise ProspectiveError("no CPI month had been published at the issuance time")
    cutoff = history.index.max()
    if cutoff > latest:
        raise ProspectiveError(
            f"history contains {cutoff}, but only months up to {latest} were published at {issued_at.isoformat()}"
        )
    lv = validate_levels(levels)
    intervals = central_intervals(lv)
    forecasts = {}
    for h in horizons:
        q = check_quantiles(model.forecast(history, int(h), lv, forecast_rng(seed, cutoff, int(h))), lv)
        forecasts[str(h)] = {
            "target_month": str(cutoff + int(h)),
            "quantiles": [float(v) for v in q],
            "central_intervals": {f"{c:.2f}": [float(q[i]), float(q[j])] for c, (i, j) in intervals.items()},
        }
    record = {
        "record_type": RECORD_TYPE,
        "issued_at_utc": issued_at.isoformat(),
        "latest_published_month": str(latest),
        "information_cutoff": str(cutoff),
        "publication_evidence": calendar.evidence.get(latest, ""),
        "model_name": model.name,
        "model_version": model.version,
        "model_parameters": dict(model_parameters or {}),
        "data_sha256": data_sha256,
        "data_version": data_version,
        "code_version": code_version,
        "seed": int(seed),
        "horizons": [int(h) for h in horizons],
        "quantile_levels": [float(v) for v in lv],
        "forecasts": forecasts,
    }
    return _with_hash(record)


class ForecastRegistry:
    def __init__(self, root: Path, repo_root: Path = PROJECT_ROOT) -> None:
        root = Path(root).resolve()
        repo_root = Path(repo_root).resolve()
        if root == repo_root or repo_root in root.parents:
            raise ProspectiveError(f"registry {root} is inside the repository {repo_root}; records must stay private")
        self.root = root
        self.issuance_dir = root / "issuances"
        self.outcome_dir = root / "outcomes"

    def save_issuance(self, record: dict) -> str:
        _verify_hash(record)
        if record.get("record_type") != RECORD_TYPE:
            raise ProspectiveError("only prospective records can be saved here")
        ts = datetime.fromisoformat(record["issued_at_utc"]).strftime("%Y%m%dT%H%M%SZ")
        safe_model = "".join(c if c.isalnum() or c in "-_." else "_" for c in record["model_name"])
        issue_id = f"{ts}_{safe_model}_{record['content_sha256'][:12]}"
        self.issuance_dir.mkdir(parents=True, exist_ok=True)
        path = self.issuance_dir / f"{issue_id}.json"
        try:
            with path.open("x", encoding="utf-8") as fh:
                json.dump(record, fh, indent=2, sort_keys=True)
        except FileExistsError as exc:
            raise ProspectiveError(f"issuance {issue_id} already exists; records are never overwritten") from exc
        return issue_id

    def load_issuance(self, issue_id: str) -> dict:
        record = json.loads((self.issuance_dir / f"{issue_id}.json").read_text(encoding="utf-8"))
        _verify_hash(record)
        return record

    def list_issuances(self) -> list[str]:
        if not self.issuance_dir.exists():
            return []
        return sorted(p.stem for p in self.issuance_dir.glob("*.json"))

    def record_outcome(self, issue_id: str, horizon: int, actual: float, published_at: datetime) -> dict:
        issuance = self.load_issuance(issue_id)
        published_at = _require_utc(published_at)
        issued_at = datetime.fromisoformat(issuance["issued_at_utc"])
        if published_at <= issued_at:
            raise ProspectiveError("outcome was published before the forecast was issued; not a prospective test")
        fc = issuance["forecasts"].get(str(horizon))
        if fc is None:
            raise ProspectiveError(f"issuance has no horizon {horizon}")
        if not np.isfinite(actual):
            raise ProspectiveError("actual value must be finite")
        levels = issuance["quantile_levels"]
        q = np.asarray(fc["quantiles"])
        outcome = {
            "record_type": "prospective_outcome",
            "issue_id": issue_id,
            "horizon": int(horizon),
            "target_month": fc["target_month"],
            "actual": float(actual),
            "actual_published_at_utc": published_at.isoformat(),
            "pinball": {f"{lv:.2f}": float(v) for lv, v in zip(levels, pinball_loss(q, actual, levels), strict=True)},
            "wis": wis(q, levels, actual),
            "inside_interval": {c: bool(lo <= actual <= hi) for c, (lo, hi) in fc["central_intervals"].items()},
        }
        outcome = _with_hash(outcome)
        self.outcome_dir.mkdir(parents=True, exist_ok=True)
        path = self.outcome_dir / f"{issue_id}_h{int(horizon)}.json"
        try:
            with path.open("x", encoding="utf-8") as fh:
                json.dump(outcome, fh, indent=2, sort_keys=True)
        except FileExistsError as exc:
            raise ProspectiveError("outcome already recorded; records are never overwritten") from exc
        return outcome
