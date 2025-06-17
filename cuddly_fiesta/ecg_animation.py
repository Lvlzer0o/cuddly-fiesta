import importlib
import os
import sys

ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
run = importlib.import_module("run")


def animate_ecg(ecg_source, interval_ms=40, show_grid=False):
    """Wrapper that ignores the optional ``show_grid`` argument used in tests."""
    return run.animate_ecg(ecg_source, interval_ms=interval_ms)

__all__ = ["animate_ecg"]
