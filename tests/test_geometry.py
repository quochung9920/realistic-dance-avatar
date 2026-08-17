import numpy as np
import pytest

from realistic_dance_avatar.geometry import ema_smooth, midpoint


def test_midpoint():
    assert midpoint([0, 0, 0], [2, 4, 6]) == [1.0, 2.0, 3.0]


def test_ema_smooth_shape_and_values():
    values = np.array([[[0.0, 0.0, 0.0]], [[2.0, 2.0, 2.0]]])
    out = ema_smooth(values, alpha=0.5)
    assert out.shape == values.shape
    assert out[0, 0].tolist() == [0.0, 0.0, 0.0]
    assert out[1, 0].tolist() == [1.0, 1.0, 1.0]


def test_ema_rejects_bad_alpha():
    with pytest.raises(ValueError):
        ema_smooth(np.zeros((1, 1, 3)), alpha=0)
