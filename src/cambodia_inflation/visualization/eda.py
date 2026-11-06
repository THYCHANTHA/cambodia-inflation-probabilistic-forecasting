"""Exploratory figures 1-5 (brief Part 8): descriptive only, no models."""

from __future__ import annotations

from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from cambodia_inflation.statistics.autocorrelation import acf, pacf, white_noise_band
from cambodia_inflation.statistics.transforms import monthly_log_change, yoy_simple
from cambodia_inflation.visualization.style import (
    REFERENCE,
    SERIES_1,
    SERIES_2,
    TEXT_SECONDARY,
    WIDTH_IN,
    add_source,
    apply_style,
    save,
)

GEO = "Phnom Penh"
OVERLAP_NOTE = "Monthly YoY rates share 11 of 12 monthly changes with their neighbours, so they are not independent."


def _ts(index: pd.PeriodIndex) -> pd.DatetimeIndex:
    return index.to_timestamp(how="start")


def _date_axis(ax) -> None:
    ax.xaxis.set_major_locator(mdates.YearLocator(2))
    ax.xaxis.set_minor_locator(mdates.YearLocator(1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))


def _span(s: pd.Series) -> str:
    return f"{s.index.min().strftime('%b %Y')} to {s.index.max().strftime('%b %Y')}"


def _subtitle(ax, text: str) -> None:
    ax.set_title(text, fontsize=8.5, fontweight="normal", color=TEXT_SECONDARY)


def _suptitle(fig, text: str) -> None:
    fig.suptitle(text, x=0.01, ha="left", fontsize=10, fontweight="bold")


def fig_cpi_index(cpi: pd.Series, out_dir: Path, extra: str = "") -> list[Path]:
    apply_style()
    fig, ax = plt.subplots(figsize=(WIDTH_IN, 3.1))
    t = _ts(cpi.index)
    ax.plot(t, cpi.to_numpy(), color=SERIES_1)
    ax.axhline(100, color=REFERENCE, lw=0.8, ls=(0, (3, 3)))
    ax.annotate(
        "Base: Oct-Dec 2006 = 100",
        (t[-1], 100),
        xytext=(0, 4),
        textcoords="offset points",
        fontsize=7,
        color=TEXT_SECONDARY,
        ha="right",
    )
    ax.set_title(f"Figure 1. Consumer price index (all items), {GEO}, {_span(cpi)}")
    ax.set_ylabel("Index (Oct-Dec 2006 = 100)")
    _date_axis(ax)
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    add_source(fig, extra)
    return save(fig, out_dir, "fig01_cpi_index")


def fig_inflation(cpi: pd.Series, out_dir: Path, extra: str = "") -> list[Path]:
    apply_style()
    y = yoy_simple(cpi).dropna()
    x = monthly_log_change(cpi).dropna()
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(WIDTH_IN, 5.0), sharex=True)
    a1.plot(_ts(y.index), y.to_numpy(), color=SERIES_1)
    a1.axhline(0, color=REFERENCE, lw=0.8)
    _subtitle(a1, f"(a) Year-on-year: 100 (P_t / P_t-12 - 1), {_span(y)}")
    a1.set_ylabel("Percent")
    a2.bar(_ts(x.index), x.to_numpy(), width=24, color=SERIES_1, linewidth=0)
    a2.axhline(0, color=REFERENCE, lw=0.8)
    _subtitle(a2, f"(b) Month-on-month log change: x_t = 100 (ln P_t - ln P_t-1), {_span(x)}")
    a2.set_ylabel("Percent (log points)")
    _date_axis(a2)
    _suptitle(fig, f"Figure 2. Consumer price inflation, {GEO}")
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    add_source(fig, extra)
    return save(fig, out_dir, "fig02_inflation_rate")


def fig_distribution(cpi: pd.Series, out_dir: Path, split: str = "2010-01", extra: str = "") -> list[Path]:
    apply_style()
    y = yoy_simple(cpi).dropna()
    late = y.loc[pd.Period(split, freq="M") :]
    fig, axes = plt.subplots(1, 2, figsize=(WIDTH_IN, 3.2))
    for ax, s, tag, color, width in (
        (axes[0], y, "(a)", SERIES_1, 1.0),
        (axes[1], late, "(b)", SERIES_2, 0.5),
    ):
        bins = np.arange(np.floor(s.min() / width) * width, np.ceil(s.max() / width) * width + width, width)
        ax.hist(s.to_numpy(), bins=bins, color=color, edgecolor="white", linewidth=0.6)
        _subtitle(ax, f"{tag} {_span(s)}, bin width {width:g} pp")
        ax.set_xlabel("Year-on-year inflation (%)")
        stats_text = (
            f"n = {len(s)}\nmean = {s.mean():.2f}\nmedian = {s.median():.2f}\nSD = {s.std(ddof=1):.2f}\n"
            f"min = {s.min():.2f}\nmax = {s.max():.2f}"
        )
        ax.text(
            0.98, 0.95, stats_text, transform=ax.transAxes, ha="right", va="top", fontsize=7.2, color=TEXT_SECONDARY
        )
    axes[0].set_ylabel("Number of months")
    _suptitle(fig, f"Figure 3. Distribution of year-on-year inflation, {GEO}")
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    add_source(fig, " ".join(p for p in (extra, OVERLAP_NOTE) if p))
    return save(fig, out_dir, "fig03_inflation_distribution")


def fig_acf_pacf(cpi: pd.Series, out_dir: Path, nlags: int = 36, extra: str = "") -> list[Path]:
    apply_style()
    series = {
        "monthly log change x_t": monthly_log_change(cpi).dropna().to_numpy(),
        "year-on-year inflation y_t": yoy_simple(cpi).dropna().to_numpy(),
    }
    fig, axes = plt.subplots(2, 2, figsize=(WIDTH_IN, 4.8), sharex=True)
    lags = np.arange(1, nlags + 1)
    for row, (name, v) in enumerate(series.items()):
        band = white_noise_band(len(v))
        for col, (fn, lab) in enumerate(((acf, "ACF"), (pacf, "PACF"))):
            ax = axes[row, col]
            vals = fn(v, nlags)[1:]
            ax.axhspan(-band, band, color=REFERENCE, alpha=0.18, lw=0)
            ax.vlines(lags, 0, vals, color=SERIES_1, lw=1.6)
            ax.plot(lags, vals, "o", ms=3, color=SERIES_1)
            ax.axhline(0, color=REFERENCE, lw=0.8)
            ax.set_ylim(-1.05, 1.05)
            _subtitle(ax, f"{lab}, {name} (n = {len(v)})")
            ax.set_xticks(np.arange(0, nlags + 1, 6))
            if row == 1:
                ax.set_xlabel("Lag (months)")
    _suptitle(fig, f"Figure 4. Sample autocorrelation and partial autocorrelation, {GEO}")
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    band_note = (
        "Shaded band: +-1.96/sqrt(n), valid only under a white-noise null; YoY is autocorrelated by construction."
    )
    add_source(fig, " ".join(p for p in (extra, band_note) if p))
    return save(fig, out_dir, "fig04_acf_pacf")


def fig_rolling_volatility(cpi: pd.Series, out_dir: Path, extra: str = "") -> list[Path]:
    apply_style()
    x = monthly_log_change(cpi).dropna()
    r12 = x.rolling(12, min_periods=12).std(ddof=1).dropna()
    r36 = x.rolling(36, min_periods=36).std(ddof=1).dropna()
    fig, ax = plt.subplots(figsize=(WIDTH_IN, 3.1))
    for s, color, label in ((r12, SERIES_1, "12-month window"), (r36, SERIES_2, "36-month window")):
        ax.plot(_ts(s.index), s.to_numpy(), color=color, label=label)
    ax.set_title(f"Figure 5. Rolling standard deviation of monthly log changes, {GEO}")
    ax.set_ylabel("SD of x_t (percentage points)")
    ax.legend(loc="upper right")
    ax.set_ylim(bottom=0)
    _date_axis(ax)
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    add_source(fig, " ".join(p for p in (extra, "Each value uses the window ending in that month (trailing).") if p))
    return save(fig, out_dir, "fig05_rolling_volatility")


def all_eda_figures(cpi: pd.Series, out_dir: Path, extra: str = "") -> list[Path]:
    paths: list[Path] = []
    for fn in (fig_cpi_index, fig_inflation, fig_distribution, fig_acf_pacf, fig_rolling_volatility):
        paths += fn(cpi, out_dir, extra=extra)
    return paths
