"""
ECG Baseline Generator
Generates clinically accurate isoelectric baseline with standard ECG scaling and grid.

Standard ECG Parameters:
- Paper speed: 25 mm/sec
- Voltage calibration: 10 mm/mV (1 mV = 10 mm)
- Small squares: 1mm x 1mm (0.04 sec x 0.1 mV)
- Large squares: 5mm x 5mm (0.2 sec x 0.5 mV)
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

class ECGBaseline:
    def __init__(self, duration_sec=10, sampling_rate=1000):
        """
        Initialize ECG baseline generator.
        
        Parameters:
        -----------
        duration_sec : float
            Duration of ECG strip in seconds
        sampling_rate : int
            Sampling rate in Hz (samples per second)
        """
        self.duration_sec = duration_sec
        self.sampling_rate = sampling_rate
        self.n_samples = int(duration_sec * sampling_rate)
        
        # Standard ECG scaling
        self.paper_speed_mm_per_sec = 25  # 25 mm/sec
        self.voltage_scale_mm_per_mv = 10  # 10 mm/mV
        
        # Grid dimensions
        self.small_square_time_sec = 0.04  # 1mm = 0.04 sec
        self.small_square_voltage_mv = 0.1  # 1mm = 0.1 mV
        self.large_square_time_sec = 0.2   # 5mm = 0.2 sec
        self.large_square_voltage_mv = 0.5  # 5mm = 0.5 mV
        
        # Generate time array
        self.time = np.linspace(0, duration_sec, self.n_samples)
        
        # Generate baseline
        self.baseline = self._generate_baseline()
    
    def _generate_baseline(self):
        """
        Generate isoelectric baseline with minimal physiologic variation.
        
        Returns:
        --------
        baseline : numpy.ndarray
            Baseline voltage values in mV
        """
        # Start with true isoelectric line (0 mV)
        baseline = np.zeros(self.n_samples)
        
        # Add minimal physiologic baseline drift (respiratory influence)
        # Very subtle sinusoidal component (0.2-0.3 Hz respiratory rate)
        respiratory_freq = 0.25  # Hz (15 breaths/min)
        respiratory_amplitude = 0.01  # mV (very subtle)
        respiratory_drift = respiratory_amplitude * np.sin(
            2 * np.pi * respiratory_freq * self.time
        )
        
        # Add very minimal random noise (electrode interface)
        noise_amplitude = 0.005  # mV
        noise = noise_amplitude * np.random.normal(0, 1, self.n_samples)
        
        # Combine components
        baseline = baseline + respiratory_drift + noise
        
        return baseline
    
    def plot_with_grid(self, show_calibration=True, figure_size=(15, 8)):
        """
        Plot baseline with standard ECG grid.
        
        Parameters:
        -----------
        show_calibration : bool
            Whether to show 1mV calibration pulse
        figure_size : tuple
            Figure size (width, height) in inches
        """
        fig, ax = plt.subplots(figsize=figure_size)
        
        # Set background color to standard ECG paper
        fig.patch.set_facecolor('white')
        ax.set_facecolor('white')
        
        # Plot baseline
        ax.plot(self.time, self.baseline, 'k-', linewidth=1.2, label='Baseline')
        
        # Add ECG grid
        self._add_ecg_grid(ax)
        
        # Add calibration pulse if requested
        if show_calibration:
            self._add_calibration_pulse(ax)
        
        # Set axis properties
        ax.set_xlabel('Time (seconds)', fontsize=12)
        ax.set_ylabel('Voltage (mV)', fontsize=12)
        ax.set_title('ECG Baseline - Standard 25mm/sec, 10mm/mV', fontsize=14, fontweight='bold')
        
        # Set axis limits with some padding
        ax.set_xlim(0, self.duration_sec)
        ax.set_ylim(-2, 2)  # Standard ECG viewport
        
        # Remove default grid
        ax.grid(False)
        
        # Add clinical ECG markers
        self._add_ecg_markers(ax)
        
        plt.tight_layout()
        return fig, ax
    
    def _add_ecg_grid(self, ax):
        """Add standard ECG grid to the plot."""
        # Get axis limits
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()
        
        # Small squares (1mm) - light grid
        small_x_lines = np.arange(0, xlim[1] + self.small_square_time_sec, 
                                 self.small_square_time_sec)
        small_y_lines = np.arange(ylim[0], ylim[1] + self.small_square_voltage_mv, 
                                 self.small_square_voltage_mv)
        
        for x in small_x_lines:
            ax.axvline(x, color='#FFB6C1', linewidth=0.5, alpha=0.7)  # Light pink
        
        for y in small_y_lines:
            ax.axhline(y, color='#FFB6C1', linewidth=0.5, alpha=0.7)
        
        # Large squares (5mm) - darker grid
        large_x_lines = np.arange(0, xlim[1] + self.large_square_time_sec, 
                                 self.large_square_time_sec)
        large_y_lines = np.arange(ylim[0], ylim[1] + self.large_square_voltage_mv, 
                                 self.large_square_voltage_mv)
        
        for x in large_x_lines:
            ax.axvline(x, color='#FF69B4', linewidth=1.0, alpha=0.8)  # Darker pink
        
        for y in large_y_lines:
            ax.axhline(y, color='#FF69B4', linewidth=1.0, alpha=0.8)
        
        # Emphasize zero line (isoelectric baseline)
        ax.axhline(0, color='red', linewidth=1.5, alpha=0.9)
    
    def _add_ecg_markers(self, ax):
        """Add clinical ECG markers for paper speed and voltage scale."""
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()
        
        # Add 25 mm/sec marker (time scale) at bottom right
        time_marker_x = xlim[1] - 1.0  # 1 second from right edge
        time_marker_y = ylim[0] + 0.1  # Just above bottom
        
        # Draw horizontal arrow for time scale (1 second = 25mm)
        arrow_length = 1.0  # 1 second
        ax.annotate('', xy=(time_marker_x, time_marker_y), 
                   xytext=(time_marker_x - arrow_length, time_marker_y),
                   arrowprops=dict(arrowstyle='<->', color='black', lw=1.5))
        
        # Add 25 mm/sec label
        ax.text(time_marker_x - arrow_length/2, time_marker_y - 0.15, 
               '25 mm/sec', ha='center', va='top', fontsize=10, weight='bold',
               bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.9))
        
        # Add 10 mm/mV marker (voltage scale) at top left
        voltage_marker_x = xlim[0] + 0.3  # Near left edge
        voltage_marker_y = ylim[1] - 0.3  # Near top
        
        # Draw vertical arrow for voltage scale (1 mV = 10mm)
        arrow_height = 1.0  # 1 mV
        ax.annotate('', xy=(voltage_marker_x, voltage_marker_y), 
                   xytext=(voltage_marker_x, voltage_marker_y - arrow_height),
                   arrowprops=dict(arrowstyle='<->', color='black', lw=1.5))
        
        # Add 10 mm/mV label
        ax.text(voltage_marker_x + 0.15, voltage_marker_y - arrow_height/2, 
               '10 mm/mV', ha='left', va='center', fontsize=10, weight='bold',
               bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.9))
    
    def _add_calibration_pulse(self, ax):
        """Add standard 1mV calibration pulse - perfect rectangle."""
        # Standard calibration: 1mV pulse, 200ms duration
        cal_duration = 0.2  # seconds
        cal_amplitude = 1.0  # mV
        cal_start_time = 0.2  # Start 0.2 seconds from beginning
        
        # Generate perfect rectangular calibration pulse
        cal_time_start = cal_start_time
        cal_time_end = cal_start_time + cal_duration
        
        # Draw calibration pulse with sharp vertical edges
        # Sharp rise
        ax.plot([cal_time_start, cal_time_start], [0, cal_amplitude], 
               'k-', linewidth=2.5, solid_capstyle='butt')
        # Flat top
        ax.plot([cal_time_start, cal_time_end], [cal_amplitude, cal_amplitude], 
               'k-', linewidth=2.5, solid_capstyle='butt')
        # Sharp drop
        ax.plot([cal_time_end, cal_time_end], [cal_amplitude, 0], 
               'k-', linewidth=2.5, solid_capstyle='butt')
        
        # Add calibration label
        ax.annotate('1 mV', xy=(cal_start_time + cal_duration/2, cal_amplitude + 0.1), 
                   fontsize=9, ha='center', va='bottom', weight='bold',
                   bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.9))
    
    def get_baseline_data(self):
        """
        Return baseline data for use in other modules.
        
        Returns:
        --------
        dict : Dictionary containing time and baseline data
        """
        return {
            'time': self.time,
            'baseline': self.baseline,
            'sampling_rate': self.sampling_rate,
            'duration_sec': self.duration_sec,
            'grid_specs': {
                'small_square_time_sec': self.small_square_time_sec,
                'small_square_voltage_mv': self.small_square_voltage_mv,
                'large_square_time_sec': self.large_square_time_sec,
                'large_square_voltage_mv': self.large_square_voltage_mv
            }
        }
    
    def save_plot(self, filename='ecg_baseline.png', dpi=300):
        """Save the baseline plot to file."""
        fig, ax = self.plot_with_grid()
        plt.savefig(f'/Users/trentoncadena/Desktop/maybewithpython/{filename}', 
                   dpi=dpi, bbox_inches='tight', facecolor='white')
        plt.close()
        print(f"Baseline plot saved as {filename}")


def main():
    """Demonstration of ECG baseline generator."""
    print("Generating ECG Baseline...")
    
    # Create 10-second baseline
    ecg_baseline = ECGBaseline(duration_sec=10, sampling_rate=1000)
    
    # Plot with grid
    fig, ax = ecg_baseline.plot_with_grid(show_calibration=True)
    
    # Add some informative text (reduced since markers show the key info)
    info_text = (
        "Standard ECG Grid:\n"
        "• Small squares: 0.04 sec × 0.1 mV\n"
        "• Large squares: 0.2 sec × 0.5 mV"
    )
    
    ax.text(0.02, 0.98, info_text, transform=ax.transAxes,
           fontsize=9, verticalalignment='top',
           bbox=dict(boxstyle='round,pad=0.4', facecolor='lightyellow', alpha=0.8))
    
    # Save the plot
    ecg_baseline.save_plot('ecg_baseline_demo.png')
    
    # Show baseline statistics
    baseline_data = ecg_baseline.get_baseline_data()
    print(f"\nBaseline Statistics:")
    print(f"Duration: {baseline_data['duration_sec']} seconds")
    print(f"Sampling rate: {baseline_data['sampling_rate']} Hz")
    print(f"Number of samples: {len(baseline_data['time'])}")
    print(f"Baseline mean: {np.mean(baseline_data['baseline']):.4f} mV")
    print(f"Baseline std: {np.std(baseline_data['baseline']):.4f} mV")
    print(f"Baseline range: [{np.min(baseline_data['baseline']):.4f}, {np.max(baseline_data['baseline']):.4f}] mV")
    
    plt.show()


if __name__ == "__main__":
    main()
