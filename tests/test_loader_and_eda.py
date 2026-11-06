"""Loader, ACF/PACF and figure code, tested on synthetic files only."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from scipy.linalg import solve_toeplitz

from cambodia_inflation.data.loader import DATAEF_COLUMNS, DataIntegrityError, load_dataef_csv, sha256_file
from cambodia_inflation.statistics.autocorrelation import acf, pacf, white_noise_band
from cambodia_inflation.visualization.eda import all_eda_figures


def _write_portal_csv(path: Path, cpi: pd.Series, corrupt_yoy_at: int | None = None) -> Path:
    """Write a synthetic file in the Data EF layout (M/1/YYYY dates, 2-decimal derived columns)."""
    c = cpi.round(2)
    yoy = 100 * (c / c.shift(12) - 1)
    ma3, ma12 = c.rolling(3).mean(), c.rolling(12).mean()
    frame = pd.DataFrame(
        {
            "Date": [f"{p.month}/1/{p.year}" for p in c.index],
            "CPI_all_item": c.to_numpy(),
            "MoM_Change_CPI_all_item": (100 * (c / c.shift(1) - 1)).round(2).to_numpy(),
            "YoY_Change_CPI_all_item": yoy.round(2).to_numpy(),
            "CPI_3_Month_Moving_Avg": ma3.round(2).to_numpy(),
            "CPI_12_Month_Moving_Avg": ma12.round(2).to_numpy(),
            # portal convention (verified on the real file): YoY change of the k-month average index
            "YoY_3_Month_Avg": (100 * (ma3 / ma3.shift(12) - 1)).round(2).to_numpy(),
            "YoY_12_Month_Avg": (100 * (ma12 / ma12.shift(12) - 1)).round(2).to_numpy(),
        }
    ).fillna(0.0)  # the real file has values for early rows (from pre-2005 data); they are not compared
    if corrupt_yoy_at is not None:
        frame.loc[corrupt_yoy_at, "YoY_Change_CPI_all_item"] += 0.5
    assert tuple(frame.columns) == DATAEF_COLUMNS
    frame.to_csv(path, index=False)
    return path


def test_loader_reads_month_first_dates_and_checks_portal_columns(tmp_path, cpi_core_shape):
    f = _write_portal_csv(tmp_path / "synthetic.csv", cpi_core_shape)
    res = load_dataef_csv(f, expected_sha256=sha256_file(f))
    assert str(res.cpi.index[1]) == "2005-02"
    assert len(res.cpi) == 252
    assert all(c.n_mismatch == 0 for c in res.checks)
    yoy_check = next(c for c in res.checks if c.column == "YoY_Change_CPI_all_item")
    assert yoy_check.n_compared == 240  # only months whose YoY is recomputable
    assert res.observations["file_sha256"].eq(res.sha256).all()


def test_loader_rejects_wrong_checksum(tmp_path, cpi_core_shape):
    f = _write_portal_csv(tmp_path / "synthetic.csv", cpi_core_shape)
    with pytest.raises(DataIntegrityError, match="SHA-256"):
        load_dataef_csv(f, expected_sha256="0" * 64)


def test_loader_rejects_inconsistent_portal_column(tmp_path, cpi_core_shape):
    f = _write_portal_csv(tmp_path / "synthetic.csv", cpi_core_shape, corrupt_yoy_at=100)
    with pytest.raises(DataIntegrityError, match="YoY_Change_CPI_all_item"):
        load_dataef_csv(f)


def test_loader_rejects_unexpected_columns(tmp_path):
    f = tmp_path / "bad.csv"
    f.write_text("Date,CPI\n1/1/2005,100\n", encoding="utf-8")
    with pytest.raises(DataIntegrityError, match="columns"):
        load_dataef_csv(f)


def test_acf_matches_definition():
    x = np.array([1.0, 3.0, 2.0, 5.0, 4.0, 6.0])
    d = x - x.mean()
    r = acf(x, 3)
    assert r[0] == 1.0
    assert r[2] == pytest.approx((d[:-2] @ d[2:]) / (d @ d))


def test_pacf_equals_last_yule_walker_coefficient():
    rng = np.random.default_rng(4)
    x = rng.normal(size=300).cumsum() * 0.1 + rng.normal(size=300)
    r = acf(x, 8)
    p = pacf(x, 8)
    assert p[1] == pytest.approx(r[1])
    for k in range(2, 9):
        coef = solve_toeplitz(r[:k], r[1 : k + 1])
        assert p[k] == pytest.approx(coef[-1], abs=1e-10)


def test_ar1_signature():
    rng = np.random.default_rng(8)
    n, phi = 20_000, 0.6
    e = rng.normal(size=n)
    x = np.empty(n)
    x[0] = e[0]
    for t in range(1, n):
        x[t] = phi * x[t - 1] + e[t]
    r, p = acf(x, 4), pacf(x, 4)
    np.testing.assert_allclose(r[1:4], phi ** np.arange(1, 4), atol=0.03)
    assert p[1] == pytest.approx(phi, abs=0.03)
    assert np.all(np.abs(p[2:]) < 0.03)
    assert white_noise_band(400) == pytest.approx(0.098)


def test_acf_input_checks():
    with pytest.raises(ValueError):
        acf([1.0, np.nan, 2.0], 1)
    with pytest.raises(ValueError):
        acf(np.ones(10), 2)


def test_eda_figures_written_as_png_and_pdf(tmp_path, cpi_core_shape):
    paths = all_eda_figures(cpi_core_shape, tmp_path, extra="SYNTHETIC TEST DATA - not Phnom Penh prices.")
    assert len(paths) == 10
    assert {p.suffix for p in paths} == {".png", ".pdf"}
    for p in paths:
        assert p.stat().st_size > 1000
    assert paths[0].read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
    assert paths[1].read_bytes()[:5] == b"%PDF-"
