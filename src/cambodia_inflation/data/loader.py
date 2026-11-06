"""Load the Data EF CSV (NIS CPI, Phnom Penh) with checksum and portal-column cross-checks.

The CSV is supplied by the user and stored outside the repository. Only the index column is used for research; the
portal's MoM, YoY and moving-average columns are recomputed from the index and compared (DATA_SOURCE_AUDIT.md §3).
"""

from __future__ import annotations

import hashlib
import os
import tomllib
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from cambodia_inflation.data.parsing import parse_portal_months
from cambodia_inflation.data.provenance import make_observations
from cambodia_inflation.data.validation import assert_valid_cpi

DATAEF_COLUMNS = (
    "Date",
    "CPI_all_item",
    "MoM_Change_CPI_all_item",
    "YoY_Change_CPI_all_item",
    "CPI_3_Month_Moving_Avg",
    "CPI_12_Month_Moving_Avg",
    "YoY_3_Month_Avg",
    "YoY_12_Month_Avg",
)
DATAEF_SOURCE_ID = "dataef:pd_66a9f36b36d76b00019fe83b"
MANIFEST = Path(__file__).resolve().parents[3] / "configs" / "data_manifest.toml"


class DataIntegrityError(ValueError):
    """The file does not match its manifest or the portal columns disagree with the index."""


@dataclass(frozen=True)
class PortalCheck:
    column: str
    n_compared: int
    n_mismatch: int
    max_abs_diff: float


@dataclass(frozen=True)
class LoadResult:
    observations: pd.DataFrame
    sha256: str
    checks: tuple[PortalCheck, ...]

    @property
    def cpi(self) -> pd.Series:
        return self.observations["cpi"].rename("cpi")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def data_dir() -> Path:
    env = os.environ.get("P11_DATA_DIR")
    return Path(env) if env else Path.home() / "portfolio-data" / "p11-inflation" / "raw"


def manifest_entry(name: str = "core_dataef", manifest: Path = MANIFEST) -> dict:
    return tomllib.loads(Path(manifest).read_text(encoding="utf-8"))[name]


def _compare(column: str, portal: pd.Series, recomputed: pd.Series, tolerance: float) -> PortalCheck:
    both = pd.concat([portal, recomputed], axis=1).dropna()
    diff = (both.iloc[:, 0] - both.iloc[:, 1]).abs()
    return PortalCheck(column, len(both), int((diff > tolerance).sum()), float(diff.max()) if len(diff) else np.nan)


def portal_checks(frame: pd.DataFrame, cpi: pd.Series, tolerance: float) -> tuple[PortalCheck, ...]:
    """Recompute every portal column from the index (2-decimal portal values, so the tolerance covers rounding)."""
    p = {c: pd.Series(pd.to_numeric(frame[c]).to_numpy(), index=cpi.index) for c in DATAEF_COLUMNS[2:]}
    mom = 100 * (cpi / cpi.shift(1) - 1)
    yoy = 100 * (cpi / cpi.shift(12) - 1)
    ma3, ma12 = cpi.rolling(3).mean(), cpi.rolling(12).mean()
    # The portal metadata calls YoY_k_Month_Avg a "moving average of the YoY inflation rate", but the values are the
    # YoY change of the k-month average index, 100 (MA_k(P)_t / MA_k(P)_{t-12} - 1). Verified 2026-11-06 on the core
    # file: max |diff| 0.014 (k=3) and 0.008 (k=12) under this definition, versus up to 0.21 and 1.15 under the
    # metadata's definition (2008-09). See DATA_SOURCE_AUDIT.md section 3. Early rows needing pre-2005 data are skipped.
    return (
        _compare("MoM_Change_CPI_all_item", p["MoM_Change_CPI_all_item"], mom, tolerance),
        _compare("YoY_Change_CPI_all_item", p["YoY_Change_CPI_all_item"], yoy, tolerance),
        _compare("CPI_3_Month_Moving_Avg", p["CPI_3_Month_Moving_Avg"], ma3, tolerance),
        _compare("CPI_12_Month_Moving_Avg", p["CPI_12_Month_Moving_Avg"], ma12, tolerance),
        _compare("YoY_3_Month_Avg", p["YoY_3_Month_Avg"], 100 * (ma3 / ma3.shift(12) - 1), tolerance),
        _compare("YoY_12_Month_Avg", p["YoY_12_Month_Avg"], 100 * (ma12 / ma12.shift(12) - 1), tolerance),
    )


def load_dataef_csv(path: Path, expected_sha256: str | None = None, tolerance: float = 0.06) -> LoadResult:
    path = Path(path)
    digest = sha256_file(path)
    if expected_sha256 is not None and digest != expected_sha256:
        raise DataIntegrityError(f"SHA-256 {digest} does not match the manifest {expected_sha256}")
    frame = pd.read_csv(path, dtype=str, encoding="utf-8-sig")
    if tuple(frame.columns) != DATAEF_COLUMNS:
        raise DataIntegrityError(f"unexpected columns: {list(frame.columns)}")
    index = parse_portal_months(frame["Date"])
    cpi = pd.Series(pd.to_numeric(frame["CPI_all_item"], errors="raise").to_numpy(), index=index, name="cpi")
    assert_valid_cpi(cpi)
    checks = portal_checks(frame, cpi, tolerance)
    bad = [c for c in checks if c.n_mismatch]
    if bad:
        raise DataIntegrityError("portal columns disagree with the index: " + ", ".join(c.column for c in bad))
    return LoadResult(make_observations(cpi, DATAEF_SOURCE_ID, path.name, digest), digest, checks)
