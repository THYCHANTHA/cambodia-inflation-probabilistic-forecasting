"""Observation-level provenance and the gate-G2 checks for extending the core series.

An observation table is a ``DataFrame`` indexed by month with columns ``cpi``, ``source_id``, ``source_file`` and
``file_sha256``. Extension observations are appended only if the series definitions are identical and every overlap
month agrees with the core value within a rounding tolerance (protocol v1.0, section 4.3).
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from cambodia_inflation.data.validation import assert_valid_cpi

OBS_COLUMNS = ("cpi", "source_id", "source_file", "file_sha256")


class SeriesCompatibilityError(ValueError):
    """Two sources cannot be combined into one series."""


@dataclass(frozen=True)
class SeriesDefinition:
    """What an index measures. Two sources can be combined only if every field is equal."""

    producer: str
    geography: str
    base_period: str
    weights: tuple[tuple[str, float], ...]

    def differences(self, other: SeriesDefinition) -> list[str]:
        out = []
        for field in ("producer", "geography", "base_period"):
            if getattr(self, field) != getattr(other, field):
                out.append(f"{field}: {getattr(self, field)!r} != {getattr(other, field)!r}")
        if dict(self.weights) != dict(other.weights):
            out.append("group weights differ")
        return out


def make_observations(cpi: pd.Series, source_id: str, source_file: str, file_sha256: str) -> pd.DataFrame:
    """Attach provenance to every value of a validated index series."""
    assert_valid_cpi(cpi)
    if len(file_sha256) != 64:
        raise ValueError("file_sha256 must be a 64-character hex digest")
    return pd.DataFrame(
        {"cpi": cpi.astype(float), "source_id": source_id, "source_file": source_file, "file_sha256": file_sha256},
        index=cpi.index,
    )


@dataclass(frozen=True)
class ExtensionResult:
    observations: pd.DataFrame
    appended: tuple[pd.Period, ...]
    overlap_checked: tuple[pd.Period, ...]
    max_overlap_abs_diff: float | None


def extend_series(
    core: pd.DataFrame,
    core_definition: SeriesDefinition,
    extension: pd.DataFrame,
    extension_definition: SeriesDefinition,
    overlap_tolerance: float = 0.006,
    require_overlap: bool = True,
) -> ExtensionResult:
    """Append extension months after the end of the core series (gate G2).

    Rules: definitions must be identical; overlap months must agree within ``overlap_tolerance`` (the core value is
    kept); new months must start immediately after the core's last month and be contiguous; at least one overlap
    month is required unless ``require_overlap`` is False.
    """
    for frame, name in ((core, "core"), (extension, "extension")):
        missing_cols = set(OBS_COLUMNS) - set(frame.columns)
        if missing_cols:
            raise SeriesCompatibilityError(f"{name} table lacks columns {sorted(missing_cols)}")
        assert_valid_cpi(frame["cpi"])
    diffs = core_definition.differences(extension_definition)
    if diffs:
        raise SeriesCompatibilityError("series definitions differ: " + "; ".join(diffs))

    overlap = core.index.intersection(extension.index)
    if require_overlap and len(overlap) == 0:
        raise SeriesCompatibilityError("no overlap month to check consistency with the core series")
    max_diff = None
    if len(overlap):
        abs_diff = (core.loc[overlap, "cpi"] - extension.loc[overlap, "cpi"]).abs()
        max_diff = float(abs_diff.max())
        bad = abs_diff[abs_diff > overlap_tolerance]
        if len(bad):
            raise SeriesCompatibilityError(
                f"overlap months disagree beyond {overlap_tolerance}: {[str(p) for p in bad.index]}"
            )
    new = extension.loc[extension.index > core.index.max()]
    if len(extension.loc[extension.index < core.index.min()]):
        raise SeriesCompatibilityError("extension contains months before the core series")
    if len(new) and new.index.min() != core.index.max() + 1:
        raise SeriesCompatibilityError(f"gap between core end {core.index.max()} and first new month {new.index.min()}")
    combined = pd.concat([core, new]).sort_index()
    assert_valid_cpi(combined["cpi"])
    return ExtensionResult(combined, tuple(new.index), tuple(overlap), max_diff)
