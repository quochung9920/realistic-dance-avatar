from __future__ import annotations

from collections.abc import Iterable

import numpy as np


def midpoint(a: Iterable[float], b: Iterable[float]) -> list[float]:
    aa = np.asarray(list(a), dtype=float)
    bb = np.asarray(list(b), dtype=float)
    return ((aa + bb) * 0.5).tolist()


def ema_smooth(values: np.ndarray, alpha: float = 0.55) -> np.ndarray:
    """Smooth a T x N x D tensor while preserving NaN gaps."""
    if values.ndim != 3:
        raise ValueError("values must have shape (frames, landmarks, dimensions)")
    if not 0.0 < alpha <= 1.0:
        raise ValueError("alpha must be in (0, 1]")

    out = values.astype(float, copy=True)
    state = np.full(values.shape[1:], np.nan, dtype=float)

    for i in range(values.shape[0]):
        current = values[i]
        valid = np.isfinite(current)
        initial = valid & ~np.isfinite(state)
        state[initial] = current[initial]
        update = valid & np.isfinite(state)
        state[update] = alpha * current[update] + (1.0 - alpha) * state[update]
        out[i] = state

    return out


def point_dict_to_xyz(point: dict) -> list[float]:
    return [float(point["x"]), float(point["y"]), float(point["z"])]
