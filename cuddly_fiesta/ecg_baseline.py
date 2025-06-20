"""ECG Baseline implementation with clinical-grade features."""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

class ECGBaseline:
    """Generates a baseline ECG with clinical-grade features."""

    def __init__(self, duration_sec=10, sampling_rate=500):
        """Initialize the ECG baseline generator.

        Args:
            duration_sec: Duration of the ECG in seconds
            sampling_rate: Samples per second
        """
        self.duration_sec = duration_sec
        self.sampling_rate = sampling_rate
        self.time = np.linspace(0, duration_sec, int(duration_sec * sampling_rate))
        self.baseline = np.zeros_like(self.time)
        self._add_calibration_pulse()

    def _add_calibration_pulse(self):
        """Add a perfect rectangular calibration pulse at the start."""
        # Find indices for calibration pulse (200ms to 400ms)
        start_idx = int(0.2 * self.sampling_rate)
        end_idx = int(0.4 * self.sampling_rate)

        # Create perfect rectangular pulse (1mV amplitude)
        self.baseline[start_idx:end_idx] = 1.0

    def get_baseline_data(self):
        """Return the baseline data as a dictionary."""
        return {
            "time": self.time,
            "voltage": self.baseline
        }

    def plot_with_grid(self, show_calibration=True, figure_size=(10, 6)):
        """Plot the ECG baseline with a clinical ECG grid.

        Args:
            show_calibration: Whether to add calibration markers
            figure_size: Size of the figure (width, height) in inches

        Returns:
            fig, ax: The matplotlib figure and axis objects
        """
        fig = plt.figure(figsize=figure_size)
        gs = GridSpec(1, 1, figure=fig)
        ax = fig.add_subplot(gs[0, 0])

        # Plot the ECG baseline
        ax.plot(self.time, self.baseline, 'k-', linewidth=1.0)

        # Add grid lines (5mm small squares, 25mm large squares)
        self._add_grid(ax)

        # Add clinical markers if requested
        if show_calibration:
            self._add_clinical_markers(ax)

        # Set limits and labels
        ax.set_xlim(0, self.duration_sec)
        ax.set_ylim(-1.5, 1.5)
        ax.set_xlabel('Time (seconds)')
        ax.set_ylabel('Amplitude (mV)')

        plt.tight_layout()
        return fig, ax

    def _add_grid(self, ax):
        """Add ECG grid (5mm small squares, 25mm large squares)."""
        # Minor grid lines (1mm)
        ax.grid(which='minor', color='#FFC0C0', linestyle='-', linewidth=0.2)

        # Major grid lines (5mm)
        ax.grid(which='major', color='#FF8080', linestyle='-', linewidth=0.5)

        # Set grid ticks (0.04s = 1mm horizontally, 0.1mV = 1mm vertically)
        ax.xaxis.set_major_locator(plt.MultipleLocator(0.2))
        ax.xaxis.set_minor_locator(plt.MultipleLocator(0.04))
        ax.yaxis.set_major_locator(plt.MultipleLocator(0.5))
        ax.yaxis.set_minor_locator(plt.MultipleLocator(0.1))

    def _add_clinical_markers(self, ax):
        """Add clinical ECG markers (25 mm/sec, 10 mm/mV)."""
        # Add 1mV calibration marker (10mm)
        ax.plot([0.05, 0.05], [-0.5, 0.5], 'k-', linewidth=2)
        ax.text(0.06, 0, "1 mV", fontsize=8, va='center')

        # Add 1 second marker
        ax.plot([1, 2], [-1.2, -1.2], 'k-', linewidth=2)
        ax.text(1.5, -1.3, "1 second", fontsize=8, ha='center', va='top')

        # Add speed/amplitude text
        ax.text(0.05, -1.0, "25 mm/sec  10 mm/mV", fontsize=8)

    def plot(self, show_grid=True):
        """Plot the ECG baseline and display it."""
        fig, ax = self.plot_with_grid(show_calibration=True)
        plt.show()
        return fig, ax
