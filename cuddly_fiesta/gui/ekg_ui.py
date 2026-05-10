"""Compatibility wrapper for the canonical ECG visualizer."""

from ..ecg_visualizer import ECGVisualizer, run_visualizer

ECGGui = ECGVisualizer
main = run_visualizer

__all__ = ["ECGGui", "main"]
