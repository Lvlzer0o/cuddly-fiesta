import numpy as np
import matplotlib.pyplot as plt
from matplotlib import animation
from ecg_core import ECGCore

class MultiLeadECG:
    """Generate simple multi-lead ECG data by duplicating a single ECGCore."""

    def __init__(self, duration_sec: float = 10, sampling_rate: int = 1000):
        self.ecg_core = ECGCore(duration_sec, sampling_rate)
        self.n_leads = 12

    def generate_leads(self):
        """Return time array and 12 identical lead signals."""
        time = self.ecg_core.time
        base = self.ecg_core.voltage
        leads = np.tile(base, (self.n_leads, 1))
        return time, leads

def animate_ecg(time: np.ndarray, voltage: np.ndarray, interval: int = 20):
    """Create a simple line animation of an ECG signal."""
    fig, ax = plt.subplots()
    line, = ax.plot([], [], lw=1)
    ax.set_xlim(time[0], time[-1])
    ax.set_ylim(float(np.min(voltage)) - 1, float(np.max(voltage)) + 1)

    def init():
        line.set_data([], [])
        return line,

    def update(frame):
        line.set_data(time[:frame], voltage[:frame])
        return line,

    ani = animation.FuncAnimation(fig, update, frames=len(time), init_func=init,
                                  interval=interval, blit=True)
    plt.close(fig)
    return ani
