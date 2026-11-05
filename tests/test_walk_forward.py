import pytest

from app.research.walk_forward import generate_walk_forward_windows


def test_walk_forward_windows_are_chronological_and_non_overlapping():
    windows = generate_walk_forward_windows(1000, train_bars=500, test_bars=100, step_bars=100)
    assert len(windows) == 5
    assert all(w.train_start < w.train_end == w.test_start < w.test_end for w in windows)
    assert windows[-1].test_end == 1000


def test_walk_forward_rejects_invalid_sizes():
    with pytest.raises(ValueError):
        generate_walk_forward_windows(100, train_bars=0, test_bars=10)
