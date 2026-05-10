"""Compatibility wrapper for the canonical ECG visualizer."""

from .ecg_visualizer import ECGVisualizer, run_visualizer

ECGVisualizerFixed = ECGVisualizer
run_visualizer_fixed = run_visualizer

__all__ = ["ECGVisualizerFixed", "run_visualizer_fixed"]
