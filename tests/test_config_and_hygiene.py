from pathlib import Path

import pandas as pd

from cambodia_inflation.config import load_protocol
from cambodia_inflation.data.synthetic import synthetic_cpi

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".venv", "__pycache__", ".git", ".ruff_cache", ".pytest_cache"}
DATA_SUFFIXES = {".csv", ".xls", ".xlsx", ".parquet", ".feather", ".pkl", ".pdf", ".dta", ".sav"}


# Real-data outputs live only in this git-ignored folder (see .gitignore) until gate G3 is resolved.
IGNORED_OUTPUT = ("reports", "figures")


def _project_files():
    for p in ROOT.rglob("*"):
        parts = p.relative_to(ROOT).parts
        if p.is_file() and not (SKIP_DIRS & set(parts)) and parts[:2] != IGNORED_OUTPUT:
            yield p


def test_real_data_outputs_are_git_ignored():
    rules = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert "reports/figures/" in rules
    assert "reports/eda_summary.txt" in rules
    assert {"*.csv", "*.xls", "*.xlsx"} <= set(rules)


def test_protocol_config_matches_v1():
    p = load_protocol()
    assert p.version == "1.0"
    assert p.horizons == (1, 3, 6, 12)
    assert p.quantile_levels == (0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95)
    assert p.samples["core"].n_yoy == 240 and p.samples["extended"].n_yoy == 249
    assert p.windows["P2010-96"].initial_window == 96
    assert p.windows["P2010-120"].initial_window == 120
    assert p.windows["LAG2"].publication_lag == 2
    assert p.windows["ROLL"].scheme == "rolling"


def test_no_data_files_in_project():
    found = [str(f.relative_to(ROOT)) for f in _project_files() if f.suffix.lower() in DATA_SUFFIXES]
    assert found == [], f"data files must stay outside the repository: {found}"


def test_no_private_paths_in_project():
    needle = "\\".join(["C:", "Users", "chant"]).lower()
    hits = []
    for f in _project_files():
        if f.suffix.lower() in {".py", ".md", ".toml", ".txt", ".bib", ".cfg", ".ini", ".json"}:
            text = f.read_text(encoding="utf-8", errors="ignore").lower()
            if needle in text or needle.replace("\\", "/") in text:
                hits.append(str(f.relative_to(ROOT)))
    assert hits == []


def test_synthetic_series_is_labelled():
    s = synthetic_cpi(n_months=30)
    assert s.attrs["synthetic"] is True
    assert s.name == "cpi_synthetic"
    assert isinstance(s.index, pd.PeriodIndex)
