"""Regenerate exploratory figures 1-5 from the core Data EF file (NIS CPI, Phnom Penh).

Usage:  python scripts/make_eda_figures.py [--data PATH] [--out DIR]

The data file is read from outside the repository and checked against configs/data_manifest.toml. Figures are written
to reports/figures/eda/ (git-ignored: real-data outputs are not committed until publication rights are confirmed).
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

import pandas as pd

from cambodia_inflation.data.loader import data_dir, load_dataef_csv, manifest_entry
from cambodia_inflation.statistics.transforms import monthly_log_change, yoy_simple
from cambodia_inflation.visualization.eda import all_eda_figures

ROOT = Path(__file__).resolve().parents[1]
log = logging.getLogger("make_eda_figures")


def describe(s: pd.Series) -> str:
    return (
        f"n={len(s)} mean={s.mean():.3f} median={s.median():.3f} sd={s.std(ddof=1):.3f} "
        f"min={s.min():.3f} ({s.idxmin()}) max={s.max():.3f} ({s.idxmax()})"
    )


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    entry = manifest_entry("core_dataef")
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, default=data_dir() / entry["file"])
    ap.add_argument("--out", type=Path, default=ROOT / "reports" / "figures" / "eda")
    args = ap.parse_args()

    res = load_dataef_csv(args.data, expected_sha256=entry["sha256"])
    cpi = res.cpi
    log.info("loaded %d months %s to %s, sha256 ok", len(cpi), cpi.index.min(), cpi.index.max())
    paths = all_eda_figures(cpi, args.out)

    y = yoy_simple(cpi).dropna()
    x = monthly_log_change(cpi).dropna()
    post = pd.Period("2010-01", freq="M")
    lines = [
        "# Exploratory summary, core sample (NIS CPI, Phnom Penh, Oct-Dec 2006 = 100). Descriptive only.",
        f"data file sha256: {res.sha256} (matches manifest)",
        f"index months: {cpi.index.min()} to {cpi.index.max()} ({len(cpi)})",
        "portal-column cross-checks (tolerance 0.06):",
        *[
            f"  {c.column}: compared {c.n_compared}, mismatches {c.n_mismatch}, max |diff| {c.max_abs_diff:.4f}"
            for c in res.checks
        ],
        f"YoY y_t, {y.index.min()} to {y.index.max()}: {describe(y)}",
        f"YoY y_t, {post} to {y.index.max()}: {describe(y.loc[post:])}",
        f"monthly log change x_t, {x.index.min()} to {x.index.max()}: {describe(x)}",
        f"monthly log change x_t, {post} to {x.index.max()}: {describe(x.loc[post:])}",
        "figures:",
        *[f"  {p.relative_to(ROOT).as_posix()}" for p in paths],
    ]
    summary = ROOT / "reports" / "eda_summary.txt"
    summary.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
