"""The YoY forecast identity (protocol v1.0, section 5.2).

For an information cutoff C and a target C + k:

    y_log_{C+k} = K_{C,k} + U_{C,k}
    K_{C,k} = sum of the last (12 - k) observed monthly changes x_{C-11+k}, ..., x_C   (0 for k >= 12)
    U_{C,k} = sum of the min(k, 12) future monthly changes x_{C+k-min(k,12)+1}, ..., x_{C+k}

Functions take the monthly changes as a 1-D array ending at the cutoff, so they cannot see anything after it.
"""

from __future__ import annotations

import numpy as np

from cambodia_inflation.statistics.transforms import WINDOW, log_to_simple


def n_known(k: int) -> int:
    _check_k(k)
    return max(WINDOW - k, 0)


def n_unknown(k: int) -> int:
    _check_k(k)
    return min(k, WINDOW)


def _check_k(k: int) -> None:
    if not isinstance(k, int | np.integer) or k < 1:
        raise ValueError(f"steps ahead must be a positive integer, got {k!r}")


def known_component(x_hist: np.ndarray, k: int) -> float:
    """K_{C,k}: sum of the last 12 - k observed monthly changes (``x_hist`` ends at the cutoff)."""
    m = n_known(k)
    if m == 0:
        return 0.0
    x_hist = np.asarray(x_hist, dtype=float)
    if len(x_hist) < m:
        raise ValueError(f"need at least {m} observed monthly changes, got {len(x_hist)}")
    tail = x_hist[-m:]
    if not np.all(np.isfinite(tail)):
        raise ValueError("observed monthly changes in the known window must be finite")
    return float(tail.sum())


def unknown_window_steps(k: int) -> np.ndarray:
    """Steps after the cutoff (1-based) whose monthly changes form U_{C,k}."""
    return np.arange(k - n_unknown(k) + 1, k + 1)


def unknown_component_from_path(path: np.ndarray, k: int) -> np.ndarray:
    """U_{C,k} from simulated future monthly changes; ``path`` has shape (..., >= k), column j = step j + 1."""
    path = np.asarray(path, dtype=float)
    if path.shape[-1] < k:
        raise ValueError(f"path has {path.shape[-1]} steps, need {k}")
    steps = unknown_window_steps(k) - 1
    return path[..., steps].sum(axis=-1)


def yoy_log_from_paths(x_hist: np.ndarray, paths: np.ndarray, k: int) -> np.ndarray:
    """Log YoY at C + k for each simulated path: K_{C,k} + U_{C,k}."""
    return known_component(x_hist, k) + unknown_component_from_path(paths, k)


def yoy_simple_from_paths(x_hist: np.ndarray, paths: np.ndarray, k: int) -> np.ndarray:
    return log_to_simple(yoy_log_from_paths(x_hist, paths, k))


def decompose_realised(x_full: np.ndarray, cutoff_pos: int, k: int) -> tuple[float, float]:
    """(K, U) from a complete array of monthly changes, with the cutoff at position ``cutoff_pos``.

    Used for computing realised errors of U and in tests; never pass this a series to a model.
    """
    x_full = np.asarray(x_full, dtype=float)
    known = known_component(x_full[: cutoff_pos + 1], k)
    target_pos = cutoff_pos + k
    if target_pos >= len(x_full):
        raise ValueError("target is beyond the end of the series")
    future = x_full[cutoff_pos + 1 : target_pos + 1]
    return known, float(unknown_component_from_path(future, k))


def quantiles_log_to_simple(log_quantiles: np.ndarray) -> np.ndarray:
    """Exact transformation of log-YoY quantiles to simple-YoY quantiles (g is strictly increasing)."""
    return log_to_simple(log_quantiles)
