"""Shared figure style (light print theme).

Colours: categorical slots 1-2 of the reference palette (blue #2a78d6, orange #eb6834), validated as a pair on the
light surface (CVD dE 24.7, normal-vision dE 33.6, contrast >= 3:1). At most two series per panel.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

SURFACE = "#fcfcfb"
TEXT_PRIMARY = "#0b0b0b"
TEXT_SECONDARY = "#52514e"
GRID = "#e4e3de"
SERIES_1 = "#2a78d6"
SERIES_2 = "#eb6834"
REFERENCE = "#8a8984"

SOURCE_NOTE = (
    "Source: NIS Consumer Price Index, Phnom Penh (Oct-Dec 2006 = 100), via Data EF (data.mef.gov.kh); "
    "author's calculations."
)
WIDTH_IN = 7.0


def apply_style() -> None:
    plt.rcParams.update(
        {
            "figure.facecolor": SURFACE,
            "axes.facecolor": SURFACE,
            "savefig.facecolor": SURFACE,
            "font.family": "DejaVu Sans",
            "font.size": 9,
            "axes.titlesize": 10,
            "axes.titleweight": "bold",
            "axes.titlelocation": "left",
            "axes.labelsize": 9,
            "axes.labelcolor": TEXT_SECONDARY,
            "axes.edgecolor": GRID,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "axes.grid.axis": "y",
            "grid.color": GRID,
            "grid.linewidth": 0.6,
            "xtick.color": TEXT_SECONDARY,
            "ytick.color": TEXT_SECONDARY,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "text.color": TEXT_PRIMARY,
            "legend.frameon": False,
            "legend.fontsize": 8,
            "lines.linewidth": 1.4,
            "pdf.fonttype": 42,
            "svg.fonttype": "none",
        }
    )


def add_source(fig, extra: str = "", note: str = SOURCE_NOTE) -> None:
    """Source line (always present) plus an optional extra sentence on a second line."""
    text = note if not extra else f"{note}\n{extra}"
    fig.text(0.01, 0.005, text, ha="left", va="bottom", fontsize=6.5, color=TEXT_SECONDARY, linespacing=1.4)


def save(fig, out_dir: Path, stem: str) -> list[Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = [out_dir / f"{stem}.png", out_dir / f"{stem}.pdf"]
    fig.savefig(paths[0], dpi=300, bbox_inches="tight")
    fig.savefig(paths[1], bbox_inches="tight")
    plt.close(fig)
    return paths
