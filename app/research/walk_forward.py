"""Time-ordered walk-forward window generator with no future leakage."""
from dataclasses import dataclass


@dataclass(frozen=True)
class WalkForwardWindow:
    train_start: int
    train_end: int
    test_start: int
    test_end: int


def generate_walk_forward_windows(total_bars: int, *, train_bars: int,
                                   test_bars: int, step_bars: int | None = None) -> list[WalkForwardWindow]:
    """Return expanding chronological train/test windows using half-open indices."""
    if total_bars <= 0 or train_bars <= 0 or test_bars <= 0:
        raise ValueError("total_bars, train_bars and test_bars must be positive")
    step = test_bars if step_bars is None else step_bars
    if step <= 0:
        raise ValueError("step_bars must be positive")
    windows = []
    train_end = train_bars
    while train_end + test_bars <= total_bars:
        windows.append(WalkForwardWindow(0, train_end, train_end, train_end + test_bars))
        train_end += step
    return windows
