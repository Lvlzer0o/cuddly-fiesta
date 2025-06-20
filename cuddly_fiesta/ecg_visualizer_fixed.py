"""Simple, stable ECG visualizer with dark theme and working animations."""

import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import numpy as np
from typing import Dict, Any, Optional, List, Union
import inspect

import matplotlib
matplotlib.use("TkAgg")  # Ensure Tk backend for smooth GUI

# Set dark theme
plt.style.use('dark_background')

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

class ECGVisualizerFixed:
    """Simple, stable ECG visualization with controls."""
    
    # Start with base rhythms and update with dynamically loaded ones
    RHYTHM_TYPES = {**_BASE_RHYTHMS, **_ALL_RHYTHMS}
    
    def __init__(self, master):
        """Initialize the ECG visualizer."""
        self.master = master
        self.master.title("ECG Visualizer - Medical Monitor")
        self.master.configure(bg='#1a1a1a')  # Dark background
        
        # ECG parameters
        self.sampling_rate = 1000
        self.duration_sec = 10
        self.heart_rate = 72
        self.current_rhythm = "Normal Sinus Rhythm"
        self.animation_timer = None
        self.is_playing = False
        self.show_12_lead = False
        self.current_frame = 0
        
        # Additional parameters
        self.show_grid = tk.BooleanVar(value=True)
        self.speed = tk.DoubleVar(value=1.0)
        
        # Dark theme colors
        self.colors = {
            'bg': '#1a1a1a',
            'fg': '#00ff00',  # Neon green
            'grid': '#333333',
            'text': '#ffffff',
            'accent': '#00aa00'
        }
        
        # Initialize ECG first
        self.update_ecg()
        
        # Initialize multi-lead ECG
        self.multi_lead = None
        
        # Setup UI
        self.setup_dark_theme()
        self.setup_ui()
    
    def setup_dark_theme(self):
        """Configure dark theme for TTK widgets."""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure styles for dark theme
        style.configure('TLabel', background=self.colors['bg'], foreground=self.colors['text'])
        style.configure('TFrame', background=self.colors['bg'])
        style.configure('TLabelFrame', background=self.colors['bg'], foreground=self.colors['text'])
        style.configure('TButton', background='#333333', foreground=self.colors['text'])
        style.configure('TCombobox', background='#333333', foreground=self.colors['text'], fieldbackground='#333333')
        style.configure('TScale', background=self.colors['bg'], troughcolor='#333333')
        style.configure('TCheckbutton', background=self.colors['bg'], foreground=self.colors['text'])
    
    def setup_ui(self):
        """Setup the user interface."""
        # Main frame
        main_frame = ttk.Frame(self.master, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Control panel
        control_frame = ttk.LabelFrame(main_frame, text="ECG Controls", padding="5")
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
        ttk.Label(control_frame, text="Animation Speed:").grid(row=3, column=0, sticky=tk.W, pady=2)
        speed_scale = ttk.Scale(
            control_frame,
            from_=0.5,
            to=5.0,
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
        grid_check.grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=4)
        
        # 12-lead view toggle
        self.lead_view_var = tk.BooleanVar(value=self.show_12_lead)
        lead_view_check = ttk.Checkbutton(
            control_frame, 
            text="12-Lead View", 
            variable=self.lead_view_var,
            command=self.toggle_lead_view
        )
        lead_view_check.grid(row=5, column=0, columnspan=2, sticky=tk.W, pady=4)
        
        # Control buttons
        btn_frame = ttk.Frame(control_frame)
        btn_frame.grid(row=6, column=0, columnspan=3, pady=10)
        
        self.play_btn = ttk.Button(btn_frame, text="▶", width=5, command=self.toggle_animation)
        self.play_btn.pack(side=tk.LEFT, padx=2)
        
        ttk.Button(btn_frame, text="⟳", width=5, command=self.reset_animation).pack(side=tk.LEFT, padx=2)
        
        # Plot area with dark theme
        self.fig, self.ax = plt.subplots(figsize=(12, 6), facecolor=self.colors['bg'])
        self.fig.patch.set_facecolor(self.colors['bg'])
        self.ax.set_facecolor(self.colors['bg'])
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=main_frame)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # Initialize plot
        self.update_plot()
    
    def update_ecg(self):
        """Update the ECG with current parameters."""
        try:
            rhythm_class = self.RHYTHM_TYPES[self.current_rhythm]
            self.ecg = ECGCore(
                duration_sec=self.duration_sec,
                sampling_rate=self.sampling_rate
            )
            
            # Prepare kwargs
            kwargs = {}
            try:
                sig = inspect.signature(rhythm_class.__init__)
                if "heart_rate_bpm" in sig.parameters:
                    kwargs["heart_rate_bpm"] = self.heart_rate
                if "duration_sec" in sig.parameters:
                    kwargs["duration_sec"] = self.duration_sec
                if "ventricular_rate_bpm" in sig.parameters:  # For AFib
                    kwargs["ventricular_rate_bpm"] = self.heart_rate
            except (ValueError, TypeError):
                pass
            
            try:
                rhythm_instance = rhythm_class(**kwargs)
            except TypeError:
                rhythm_instance = rhythm_class()
            
            rhythm_instance.apply_to_ecg(self.ecg)
            
            # Reset multi_lead to force regeneration
            self.multi_lead = None
            
        except Exception as e:
            print(f"Error updating ECG: {e}")
            # Fallback to normal sinus rhythm
            self.ecg = ECGCore(
                duration_sec=self.duration_sec,
                sampling_rate=self.sampling_rate
            )
            nsr = NormalSinusRhythm(heart_rate_bpm=self.heart_rate)
            nsr.apply_to_ecg(self.ecg)
    
    def update_plot(self):
        """Update the plot display."""
        try:
            self.ax.clear()
            self.ax.set_facecolor(self.colors['bg'])
            
            if self.ecg is None or not hasattr(self.ecg, 'time') or not hasattr(self.ecg, 'voltage'):
                self.ax.text(0.5, 0.5, 'No ECG data available', 
                           horizontalalignment='center',
                           verticalalignment='center',
                           transform=self.ax.transAxes,
                           color=self.colors['text'],
                           fontsize=14)
                self.canvas.draw()
                return
                
            time = self.ecg.time
            
            if self.show_12_lead:
                # Create 12-lead view
                if self.multi_lead is None:
                    self.multi_lead = MultiLeadECG.from_ecg(self.ecg)
                    
                # Clear and create subplots
                self.fig.clear()
                leads = ['I', 'II', 'III', 'aVR', 'aVL', 'aVF', 'V1', 'V2', 'V3', 'V4', 'V5', 'V6']
                
                for i in range(12):
                    ax = self.fig.add_subplot(6, 2, i+1)
                    ax.set_facecolor(self.colors['bg'])
                    
                    # Plot each lead
                    lead_data = self.multi_lead.get_lead(leads[i])
                    ax.plot(time, lead_data, color=self.colors['fg'], linewidth=1.5)
                    
                    # Add lead label
                    ax.text(0.02, 0.9, leads[i], transform=ax.transAxes, 
                           fontweight='bold', color=self.colors['text'])
                    
                    # Styling
                    ax.set_ylim(-2, 2)
                    ax.tick_params(colors=self.colors['text'])
                    if self.show_grid.get():
                        ax.grid(True, color=self.colors['grid'], alpha=0.3)
                    
                    if i < 10:
                        ax.set_xticklabels([])
                    else:
                        ax.set_xlabel('Time (s)', color=self.colors['text'])
                
                self.fig.suptitle(f'12-Lead ECG - {self.current_rhythm}', 
                                y=0.98, color=self.colors['text'], fontsize=14)
                
                # Reset ax to the main subplot for animation
                self.ax = self.fig.add_subplot(111, frameon=False)
                self.ax.tick_params(labelcolor='none', top=False, bottom=False, left=False, right=False)
                
            else:
                # Single lead view
                voltage = self.ecg.voltage
                
                # Plot the ECG with neon green
                self.ax.plot(time, voltage, color=self.colors['fg'], linewidth=2.5)
                
                # Set labels and title
                self.ax.set_xlabel('Time (s)', color=self.colors['text'], fontsize=12)
                self.ax.set_ylabel('Amplitude (mV)', color=self.colors['text'], fontsize=12)
                self.ax.set_title(f'ECG Monitor - {self.current_rhythm}', 
                                color=self.colors['text'], fontsize=14, fontweight='bold')
                self.ax.tick_params(colors=self.colors['text'])
                
                # Set grid if enabled
                if self.show_grid.get():
                    self.ax.grid(True, color=self.colors['grid'], alpha=0.4)
                
                # Adjust y-axis to show full signal
                if len(voltage) > 0:
                    self.ax.set_ylim(min(voltage) - 0.3, max(voltage) + 0.3)
            
            self.canvas.draw()
            
        except Exception as e:
            print(f"Error updating plot: {e}")
    
    def animate_step(self):
        """Single animation step."""
        if not self.is_playing or self.ecg is None:
            return
            
        try:
            # Simple scrolling animation
            self.ax.clear()
            self.ax.set_facecolor(self.colors['bg'])
            
            # Animation parameters
            window_duration = 4.0  # Show 4 seconds
            samples_per_frame = 20  # Advance by 20 samples per frame
            
            # Calculate current position
            total_samples = len(self.ecg.time)
            current_sample = (self.current_frame * samples_per_frame) % total_samples
            window_samples = int(window_duration * self.sampling_rate)
            
            # Get data window
            end_sample = min(current_sample + window_samples, total_samples)
            time_window = self.ecg.time[current_sample:end_sample]
            voltage_window = self.ecg.voltage[current_sample:end_sample]
            
            if len(time_window) > 0:
                # Plot ECG trace
                self.ax.plot(time_window, voltage_window, color=self.colors['fg'], linewidth=2.5)
                
                # Set viewing window
                self.ax.set_xlim(time_window[0], time_window[0] + window_duration)
                
                # Auto-scale Y axis
                if len(voltage_window) > 0:
                    y_min, y_max = min(voltage_window), max(voltage_window)
                    y_margin = max(0.3, (y_max - y_min) * 0.1)
                    self.ax.set_ylim(y_min - y_margin, y_max + y_margin)
                else:
                    self.ax.set_ylim(-2, 2)
                
                # Style the plot
                self.ax.set_xlabel('Time (s)', color=self.colors['text'])
                self.ax.set_ylabel('Amplitude (mV)', color=self.colors['text'])
                self.ax.set_title(f'ECG Monitor - {self.current_rhythm} [LIVE]', 
                                color=self.colors['text'], fontweight='bold')
                self.ax.tick_params(colors=self.colors['text'])
                
                if self.show_grid.get():
                    self.ax.grid(True, color=self.colors['grid'], alpha=0.4)
            
            # Update canvas
            self.canvas.draw_idle()
            
            # Update frame counter
            self.current_frame += 1
            
            # Schedule next frame
            interval_ms = max(50, int(200 / self.speed.get()))
            self.animation_timer = self.master.after(interval_ms, self.animate_step)
            
        except Exception as e:
            print(f"Animation error: {e}")
            self.is_playing = False
            self.play_btn.config(text="▶")
    
    def toggle_animation(self):
        """Toggle animation play/pause."""
        if self.is_playing:
            # Stop animation
            self.is_playing = False
            if self.animation_timer:
                self.master.after_cancel(self.animation_timer)
                self.animation_timer = None
            self.play_btn.config(text="▶")
        else:
            # Start animation (only in single lead mode)
            if not self.show_12_lead:
                self.is_playing = True
                self.animate_step()
                self.play_btn.config(text="⏸")
    
    def reset_animation(self):
        """Reset animation."""
        self.is_playing = False
        if self.animation_timer:
            self.master.after_cancel(self.animation_timer)
            self.animation_timer = None
        self.current_frame = 0
        self.play_btn.config(text="▶")
        self.update_plot()
    
    def on_rhythm_change(self, event=None):
        """Handle rhythm change."""
        self.current_rhythm = self.rhythm_var.get()
        self.on_parameter_change()
    
    def on_parameter_change(self):
        """Handle parameter changes."""
        self.heart_rate = self.hr_var.get()
        self.duration_sec = self.duration_var.get()
        self.update_ecg()
        self.reset_animation()
    
    def on_hr_change(self, val):
        """Handle heart rate change."""
        bpm = int(float(val))
        self.hr_var.set(bpm)
        self.hr_label.config(text=f"{bpm} bpm")
        self.on_parameter_change()
    
    def on_speed_change(self, val=None):
        """Handle speed change."""
        self.speed_label.config(text=f"{self.speed.get():.1f}x")
    
    def on_grid_toggle(self):
        """Toggle grid visibility."""
        self.update_plot()
    
    def toggle_lead_view(self):
        """Toggle between single and 12-lead view."""
        self.show_12_lead = self.lead_view_var.get()
        if self.show_12_lead and self.is_playing:
            # Stop animation for 12-lead view
            self.toggle_animation()
        self.update_plot()

def run_visualizer_fixed():
    """Run the fixed ECG visualizer application."""
    root = tk.Tk()
    root.title("ECG Medical Monitor")
    app = ECGVisualizerFixed(root)
    
    # Center the window
    root.geometry("1200x800")
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (1200 // 2)
    y = (root.winfo_screenheight() // 2) - (800 // 2)
    root.geometry(f"1200x800+{x}+{y}")
    
    root.mainloop()

if __name__ == "__main__":
    run_visualizer_fixed()
