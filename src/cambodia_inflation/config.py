"""Load ``configs/protocol.toml`` into typed objects."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from cambodia_inflation.forecasting.windows import WindowSpec

DEFAULT_CONFIG = Path(__file__).resolve().parents[2] / "configs" / "protocol.toml"


@dataclass(frozen=True)
class Sample:
    name: str
    first_index_month: pd.Period
    first_yoy_month: pd.Period
    last_month: pd.Period
    n_yoy: int


@dataclass(frozen=True)
class Protocol:
    version: str
    seed: int
    horizons: tuple[int, ...]
    quantile_levels: tuple[float, ...]
    samples: dict[str, Sample]
    windows: dict[str, WindowSpec]
    dev_target_end: pd.Period
    test_origin_start: pd.Period
    overlap_tolerance: float


def _month(s: str) -> pd.Period:
    return pd.Period(s, freq="M")


def load_protocol(path: Path = DEFAULT_CONFIG) -> Protocol:
    raw = tomllib.loads(Path(path).read_text(encoding="utf-8"))
    p = raw["protocol"]
    samples = {}
    for name, s in raw["samples"].items():
        sample = Sample(
            name, _month(s["first_index_month"]), _month(s["first_yoy_month"]), _month(s["last_month"]), int(s["n_yoy"])
        )
        n = int((sample.last_month - sample.first_yoy_month).n) + 1
        if n != sample.n_yoy:
            raise ValueError(f"sample {name}: n_yoy {sample.n_yoy} but dates span {n} months")
        samples[name] = sample
    windows = {
        name: WindowSpec(
            name, _month(w["estimation_start"]), int(w["initial_window"]), w["scheme"], int(w["publication_lag"])
        )
        for name, w in raw["windows"].items()
    }
    return Protocol(
        version=str(p["version"]),
        seed=int(p["seed"]),
        horizons=tuple(int(h) for h in p["horizons"]),
        quantile_levels=tuple(float(v) for v in p["quantile_levels"]),
        samples=samples,
        windows=windows,
        dev_target_end=_month(raw["split"]["dev_target_end"]),
        test_origin_start=_month(raw["split"]["test_origin_start"]),
        overlap_tolerance=float(raw["extension_validation"]["overlap_tolerance"]),
    )
