"""Interactive ECG visualization with controls."""

import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.animation import FuncAnimation
import numpy as np
from typing import Dict, Any, Optional, List, Union

import matplotlib
matplotlib.use("TkAgg")  # Ensure Tk backend for smooth GUI

from .core import ECGCore, MultiLeadECG
from .waveform_segments import (
    NormalSinusRhythm, AtrialFibrillation, AtrialFlutter,
    VentricularTachycardia, VentricularFibrillation,
    WolffParkinsonWhite, PulselessElectricalActivity
)

# Dynamically collect all rhythm classes from rhythms package
try:
    import inspect
    from . import rhythms as _rhythm_pkg
    _ALL_RHYTHMS = {
        name: getattr(_rhythm_pkg, name)
        for name in getattr(_rhythm_pkg, "__all__", [])
        if (hasattr(_rhythm_pkg, name) and 
            not inspect.isabstract(getattr(_rhythm_pkg, name)) and 
            hasattr(getattr(_rhythm_pkg, name), 'apply_to_ecg'))
    }
except Exception as e:
    print(f"Warning: Could not load all rhythm classes: {e}")
    _ALL_RHYTHMS = {}

# Base rhythms that are known to work
_BASE_RHYTHMS = {
    "Normal Sinus Rhythm": NormalSinusRhythm,
    "Atrial Fibrillation": AtrialFibrillation,
    "Atrial Flutter": AtrialFlutter,
    "Ventricular Tachycardia": VentricularTachycardia,
    "Ventricular Fibrillation": VentricularFibrillation,
    "WPW": WolffParkinsonWhite,
    "PEA": PulselessElectricalActivity
}

class ECGVisualizer:
    """Interactive ECG visualization with controls."""
    
    # Start with base rhythms and update with dynamically loaded ones
    RHYTHM_TYPES = {**_BASE_RHYTHMS, **_ALL_RHYTHMS}
    
    def __init__(self, master):
        """Initialize the ECG visualizer."""
        self.master = master
        self.master.title("ECG Visualizer")
        
        # ECG parameters
        self.sampling_rate = 1000
        self.duration_sec = 10
        self.heart_rate = 72
        self.current_rhythm = "Normal Sinus Rhythm"
        self.animation = None
        self.is_playing = False
        self.show_12_lead = False  # Toggle for 12-lead view
        
        # Additional parameters
        self.show_grid = tk.BooleanVar(value=True)
        self.speed = tk.DoubleVar(value=1.0)  # 1x speed
        
        # Initialize ECG first
        self.update_ecg()
        
        # Initialize multi-lead ECG
        self.multi_lead = None
        
        # Setup UI
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the user interface."""
        # Main frame
        main_frame = ttk.Frame(self.master, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Control panel
        control_frame = ttk.LabelFrame(main_frame, text="Controls", padding="5")
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        
        # Rhythm selection
        ttk.Label(control_frame, text="Rhythm:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.rhythm_var = tk.StringVar(value=self.current_rhythm)
        rhythm_menu = ttk.Combobox(
            control_frame, 
            textvariable=self.rhythm_var,
            values=list(self.RHYTHM_TYPES.keys()),
            state="readonly"
        )
        rhythm_menu.grid(row=0, column=1, sticky=tk.EW, pady=2)
        rhythm_menu.configure(width=25)
        rhythm_menu.bind("<<ComboboxSelected>>", self.on_rhythm_change)
        
        # Heart rate control
        ttk.Label(control_frame, text="Heart Rate (bpm):").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.hr_var = tk.IntVar(value=self.heart_rate)
        hr_scale = ttk.Scale(
            control_frame, 
            from_=30, 
            to=220, 
            orient=tk.HORIZONTAL,
            variable=self.hr_var,
            command=self.on_hr_change
        )
        hr_scale.grid(row=1, column=1, sticky=tk.EW, pady=2)
        self.hr_label = ttk.Label(control_frame, text=f"{self.heart_rate} bpm")
        self.hr_label.grid(row=1, column=2, sticky=tk.W)
        
        # Duration control
        ttk.Label(control_frame, text="Duration (s):").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.duration_var = tk.IntVar(value=self.duration_sec)
        duration_scale = ttk.Scale(
            control_frame, 
            from_=5, 
            to=30, 
            orient=tk.HORIZONTAL,
            variable=self.duration_var,
            command=lambda _: self.on_parameter_change()
        )
        duration_scale.grid(row=2, column=1, sticky=tk.EW, pady=2)
        
        # Speed control
        ttk.Label(control_frame, text="Speed (0.5x-10x):").grid(row=3, column=0, sticky=tk.W, pady=2)
        speed_scale = ttk.Scale(
            control_frame,
            from_=0.5,
            to=10.0,
            orient=tk.HORIZONTAL,
            variable=self.speed,
            command=self.on_speed_change
        )
        speed_scale.grid(row=3, column=1, sticky=tk.EW, pady=2)
        self.speed_label = ttk.Label(control_frame, text="1.0x")
        self.speed_label.grid(row=3, column=2, sticky=tk.W)
        
        # Grid toggle
        grid_check = ttk.Checkbutton(
            control_frame,
            text="Show Grid",
            variable=self.show_grid,
            command=self.on_grid_toggle
        )
        grid_check.grid(row=4, column=0, columnspan=2, sticky=tk.W, padx=2, pady=4)
        
        # 12-lead view toggle
        self.lead_view_var = tk.BooleanVar(value=self.show_12_lead)
        lead_view_check = ttk.Checkbutton(
            control_frame, 
            text="12-Lead View", 
            variable=self.lead_view_var,
            command=self.toggle_lead_view
        )
        lead_view_check.grid(row=5, column=0, columnspan=2, sticky=tk.W, padx=2, pady=4)
        
        # Control buttons
        btn_frame = ttk.Frame(control_frame)
        btn_frame.grid(row=6, column=0, columnspan=2, pady=10)
        
        self.play_btn = ttk.Button(btn_frame, text="▶", width=3, command=self.toggle_animation)
        self.play_btn.pack(side=tk.LEFT, padx=2)
        
        ttk.Button(btn_frame, text="⟳", width=3, command=self.reset_animation).pack(side=tk.LEFT, padx=2)
        
        # Plot area
        self.fig, self.ax = plt.subplots(figsize=(10, 4))
        self.canvas = FigureCanvasTkAgg(self.fig, master=main_frame)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # Navigation toolbar
        self.toolbar = NavigationToolbar2Tk(self.canvas, main_frame)
        self.toolbar.update()
        
        # Initialize plot
        self.line, = self.ax.plot([], [], 'b-')
        self.ax.set_xlim(0, self.duration_sec)
        self.ax.set_ylim(-2, 2)
        self.ax.set_xlabel('Time (s)')
        self.ax.set_ylabel('Amplitude (mV)')
        self.ax.set_title('ECG Waveform')
        self.ax.grid(self.show_grid.get())
        
        # Initialize animation
        self.reset_animation()
    
    def update_ecg(self):
        """Update the ECG with current parameters."""
        import inspect
        rhythm_class = self.RHYTHM_TYPES[self.current_rhythm]
        self.ecg = ECGCore(
            duration_sec=self.duration_sec,
            sampling_rate=self.sampling_rate
        )
        # Prepare kwargs only if the rhythm supports them
        kwargs = {}
        try:
            sig = inspect.signature(rhythm_class.__init__)
            if "heart_rate_bpm" in sig.parameters:
                kwargs["heart_rate_bpm"] = self.heart_rate
        except (ValueError, TypeError):
            # Fallback if signature inspection fails
            pass
        try:
            rhythm_instance = rhythm_class(**kwargs)
        except TypeError:
            # Constructor didn't accept kwargs; instantiate without
            rhythm_instance = rhythm_class()
        rhythm_instance.apply_to_ecg(self.ecg)
        
        # Reset multi_lead to force regeneration on next plot
        self.multi_lead = None
    
    def on_rhythm_change(self, event=None):
        """Handle rhythm type change."""
        self.current_rhythm = self.rhythm_var.get()
        self.on_parameter_change()
    
    def toggle_lead_view(self):
        """Toggle between single lead and 12-lead view."""
        self.show_12_lead = self.lead_view_var.get()
        self.update_plot()
    
    def on_parameter_change(self):
        """Handle parameter changes."""
        self.heart_rate = self.hr_var.get()
        self.duration_sec = self.duration_var.get()
        self.update_ecg()
        self.reset_animation()
    
    def update_plot(self, frame=None):
        """Update the plot with current ECG data."""
        self.fig.clear()
        
        if self.ecg is None or not hasattr(self.ecg, 'time') or not hasattr(self.ecg, 'voltage'):
            ax = self.fig.add_subplot(111)
            ax.text(0.5, 0.5, 'No ECG data', 
                   horizontalalignment='center',
                   verticalalignment='center',
                   transform=ax.transAxes)
            self.canvas.draw()
            return
            
        time = self.ecg.time
        
        if self.show_12_lead:
            # Create 12-lead view
            if self.multi_lead is None:
                self.multi_lead = MultiLeadECG.from_ecg(self.ecg)
                
            # Define the layout for 12-lead ECG
            leads = ['I', 'II', 'III', 'aVR', 'aVL', 'aVF', 'V1', 'V2', 'V3', 'V4', 'V5', 'V6']
            
            # Create subplots with shared x-axis for synchronized scrolling
            axes = []
            for i in range(12):
                ax = self.fig.add_subplot(6, 2, i+1)
                axes.append(ax)
                
                # Plot each lead
                lead_data = getattr(self.multi_lead, f'lead_{leads[i].lower()}')
                ax.plot(time, lead_data, 'b-', linewidth=0.8)
                
                # Add lead label
                ax.text(0.02, 0.9, leads[i], transform=ax.transAxes, fontweight='bold')
                
                # Only show x-axis on bottom row
                if i < 10:
                    ax.set_xticklabels([])
                else:
                    ax.set_xlabel('Time (s)')
                    
                # Set y-axis limits
                ax.set_ylim(-2, 2)
                ax.grid(self.show_grid.get())
                
            # Adjust spacing between subplots
            self.fig.subplots_adjust(hspace=0.4, wspace=0.3)
            self.fig.suptitle(f'12-Lead ECG - {self.current_rhythm}', y=0.98)
            
        else:
            # Single lead view
            ax = self.fig.add_subplot(111)
            voltage = self.ecg.voltage
            
            # Plot the ECG
            ax.plot(time, voltage, 'b-', linewidth=1.5)
            
            # Set labels and title
            ax.set_xlabel('Time (s)')
            ax.set_ylabel('Amplitude (mV)')
            ax.set_title(f'ECG - {self.current_rhythm}')
            
            # Set grid if enabled
            ax.grid(self.show_grid.get())
            
            # Adjust y-axis to show full signal
            ax.set_ylim(min(voltage) - 0.5, max(voltage) + 0.5)
        
        self.canvas.draw()
    
    def toggle_animation(self):
        """Toggle animation play/pause."""
        if self.is_playing:
            self.animation.event_source.stop()
            self.play_btn.config(text="▶")
        else:
            self.animation.event_source.start()
            self.play_btn.config(text="⏸")
        self.is_playing = not self.is_playing
    
    def on_speed_change(self, val=None):
        """Handle changes in playback speed."""
        if self.animation is not None:
            interval_ms = int(20 / self.speed.get())
            self.animation.event_source.interval = max(1, interval_ms)
        self.speed_label.config(text=f"{self.speed.get():.1f}x")
    
    def on_grid_toggle(self):
        """Toggle grid visibility."""
        self.ax.grid(self.show_grid.get())
        self.canvas.draw_idle()
    
    def on_hr_change(self, val):
        """Handle HR slider movement."""
        bpm = int(float(val))
        self.hr_var.set(bpm)
        self.hr_label.config(text=f"{bpm} bpm")
        self.on_parameter_change()
    
    def reset_animation(self):
        """Reset the animation to the beginning."""
        # Ensure we have an ECG generated
        if not hasattr(self, "ecg"):
            self.update_ecg()
        
        if hasattr(self, 'animation') and self.animation is not None:
            try:
                self.animation.event_source.stop()
            except Exception:
                pass
            self.animation._stop()
            self.animation = None
        
        self.line.set_data([], [])
        self.ax.set_xlim(0, self.duration_sec)
        self.ax.grid(self.show_grid.get())
        self.canvas.draw()
        
        interval_ms = int(20 / self.speed.get())
        self.animation = FuncAnimation(
            self.fig,
            self.update_plot,
            frames=len(self.ecg.time),
            interval=interval_ms,
            blit=True,
            repeat=False,
            cache_frame_data=False
        )
        self.is_playing = False
        self.play_btn.config(text="▶")

def run_visualizer():
    """Run the ECG visualizer application."""
    root = tk.Tk()
    root.title("ECG Visualizer")
    app = ECGVisualizer(root)
    root.mainloop()

if __name__ == "__main__":
    run_visualizer()
