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

class ECGVisualizer:
    """Interactive ECG visualization with controls."""
    
    # Start with base rhythms and update with dynamically loaded ones
    RHYTHM_TYPES = {**_BASE_RHYTHMS, **_ALL_RHYTHMS}
    
    def __init__(self, master):
        """Initialize the ECG visualizer."""
        self.master = master
        self.master.title("ECG Visualizer")
        self.master.configure(bg='#1a1a1a')  # Dark background
        
        # ECG parameters
        self.sampling_rate = 1000
        self.duration_sec = 10
        self.heart_rate = 72
        self.current_rhythm = "Normal Sinus Rhythm"
        self.animation = None
        self.is_playing = False
        self.show_12_lead = False  # Toggle for 12-lead view
        self.current_frame = 0  # Track animation frame
        
        # Additional parameters
        self.show_grid = tk.BooleanVar(value=True)
        self.speed = tk.DoubleVar(value=1.0)  # 1x speed
        
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
        
        # Configure the theme
        style.theme_use('clam')  # Use clam as base theme
        
        # Configure styles for dark theme
        style.configure('TLabel', 
                       background=self.colors['bg'], 
                       foreground=self.colors['text'])
        
        style.configure('TFrame', 
                       background=self.colors['bg'])
        
        style.configure('TLabelFrame', 
                       background=self.colors['bg'], 
                       foreground=self.colors['text'],
                       borderwidth=1,
                       relief='solid')
        
        style.configure('TLabelFrame.Label', 
                       background=self.colors['bg'], 
                       foreground=self.colors['accent'])
        
        style.configure('TButton', 
                       background='#333333', 
                       foreground=self.colors['text'],
                       borderwidth=1,
                       focuscolor='none')
        
        style.map('TButton',
                 background=[('active', '#555555'),
                           ('pressed', '#222222')])
        
        style.configure('TCombobox', 
                       background='#333333', 
                       foreground=self.colors['text'],
                       fieldbackground='#333333',
                       borderwidth=1)
        
        style.configure('TScale', 
                       background=self.colors['bg'],
                       troughcolor='#333333',
                       borderwidth=1)
        
        style.configure('TCheckbutton', 
                       background=self.colors['bg'], 
                       foreground=self.colors['text'],
                       focuscolor='none')
        
        style.map('TCheckbutton',
                 background=[('active', self.colors['bg'])])
    
    def setup_ui(self):
        """Setup the user interface."""
        # Main frame
        main_frame = ttk.Frame(self.master, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Apply dark background to main window
        self.master.configure(bg=self.colors['bg'])
        
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
        
        # Plot area with dark theme
        self.fig, self.ax = plt.subplots(figsize=(10, 4), facecolor=self.colors['bg'])
        self.fig.patch.set_facecolor(self.colors['bg'])
        self.ax.set_facecolor(self.colors['bg'])
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=main_frame)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.canvas.get_tk_widget().configure(bg=self.colors['bg'])
        
        # Navigation toolbar
        self.toolbar = NavigationToolbar2Tk(self.canvas, main_frame)
        self.toolbar.update()
        
        # Initialize plot with neon green color
        self.line, = self.ax.plot([], [], color=self.colors['fg'], linewidth=2)
        self.ax.set_xlim(0, self.duration_sec)
        self.ax.set_ylim(-2, 2)
        self.ax.set_xlabel('Time (s)', color=self.colors['text'])
        self.ax.set_ylabel('Amplitude (mV)', color=self.colors['text'])
        self.ax.set_title('ECG Waveform', color=self.colors['text'])
        self.ax.tick_params(colors=self.colors['text'])
        self.ax.grid(self.show_grid.get(), color=self.colors['grid'], alpha=0.5)
        
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
        if frame is not None:
            self.current_frame = frame
            
        # For animation mode, show progressive ECG trace
        if self.animation is not None and frame is not None:
            return self.animate_frame(frame)
        
        # For static display, show full ECG
        self.fig.clear()
        
        if self.ecg is None or not hasattr(self.ecg, 'time') or not hasattr(self.ecg, 'voltage'):
            ax = self.fig.add_subplot(111)
            ax.set_facecolor(self.colors['bg'])
            ax.text(0.5, 0.5, 'No ECG data', 
                   horizontalalignment='center',
                   verticalalignment='center',
                   transform=ax.transAxes,
                   color=self.colors['text'])
            self.canvas.draw()
            return []
            
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
                ax.set_facecolor(self.colors['bg'])
                axes.append(ax)
                
                # Plot each lead
                lead_data = getattr(self.multi_lead, f'lead_{leads[i].lower()}')
                ax.plot(time, lead_data, color=self.colors['fg'], linewidth=1.2)
                
                # Add lead label
                ax.text(0.02, 0.9, leads[i], transform=ax.transAxes, 
                       fontweight='bold', color=self.colors['text'])
                
                # Only show x-axis on bottom row
                if i < 10:
                    ax.set_xticklabels([])
                else:
                    ax.set_xlabel('Time (s)', color=self.colors['text'])
                    
                # Set y-axis limits and styling
                ax.set_ylim(-2, 2)
                ax.tick_params(colors=self.colors['text'])
                ax.grid(self.show_grid.get(), color=self.colors['grid'], alpha=0.5)
                
            # Adjust spacing between subplots
            self.fig.subplots_adjust(hspace=0.4, wspace=0.3)
            self.fig.suptitle(f'12-Lead ECG - {self.current_rhythm}', 
                            y=0.98, color=self.colors['text'])
            
        else:
            # Single lead view
            ax = self.fig.add_subplot(111)
            ax.set_facecolor(self.colors['bg'])
            voltage = self.ecg.voltage
            
            # Plot the ECG with neon green
            ax.plot(time, voltage, color=self.colors['fg'], linewidth=2)
            
            # Set labels and title with dark theme
            ax.set_xlabel('Time (s)', color=self.colors['text'])
            ax.set_ylabel('Amplitude (mV)', color=self.colors['text'])
            ax.set_title(f'ECG - {self.current_rhythm}', color=self.colors['text'])
            ax.tick_params(colors=self.colors['text'])
            
            # Set grid if enabled
            ax.grid(self.show_grid.get(), color=self.colors['grid'], alpha=0.5)
            
            # Adjust y-axis to show full signal
            ax.set_ylim(min(voltage) - 0.5, max(voltage) + 0.5)
        
        self.canvas.draw()
        return []
    
    def animate_frame(self, frame):
        """Animate a single frame for the scrolling ECG."""
        if self.ecg is None or not hasattr(self.ecg, 'time') or not hasattr(self.ecg, 'voltage'):
            return
        
        # Clear the current plot
        self.ax.clear()
        self.ax.set_facecolor(self.colors['bg'])
        
        # Calculate how much data to show (scrolling window)
        window_size = int(self.sampling_rate * 3)  # 3 seconds of data
        end_idx = min(frame * 20, len(self.ecg.time))
        start_idx = max(0, end_idx - window_size)
        
        # Get the data window
        time_window = self.ecg.time[start_idx:end_idx]
        voltage_window = self.ecg.voltage[start_idx:end_idx]
        
        if len(time_window) > 0:
            # Plot the ECG trace
            self.ax.plot(time_window, voltage_window, color=self.colors['fg'], linewidth=2)
            
            # Set the viewing window
            time_range = time_window[-1] - time_window[0] if len(time_window) > 1 else 3
            self.ax.set_xlim(time_window[0], time_window[0] + max(time_range, 3))
            self.ax.set_ylim(min(voltage_window) - 0.5, max(voltage_window) + 0.5)
            
            # Style the plot
            self.ax.set_xlabel('Time (s)', color=self.colors['text'])
            self.ax.set_ylabel('Amplitude (mV)', color=self.colors['text'])
            self.ax.set_title(f'ECG - {self.current_rhythm} (Live)', color=self.colors['text'])
            self.ax.tick_params(colors=self.colors['text'])
            self.ax.grid(self.show_grid.get(), color=self.colors['grid'], alpha=0.5)
        
        # Don't return anything since blit=False
    
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
        self.ax.grid(self.show_grid.get(), color=self.colors['grid'], alpha=0.5)
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
        
        # Properly cleanup old animation
        if hasattr(self, 'animation') and self.animation is not None:
            try:
                self.animation.event_source.stop()
            except Exception:
                pass
            try:
                if hasattr(self.animation, '_stop'):
                    self.animation._stop()
            except Exception:
                pass
            self.animation = None
        
        # Reset current frame
        self.current_frame = 0
        
        # Update plot to show initial state
        self.update_plot()
        
        # Create new animation WITHOUT blitting to avoid axis issues
        try:
            interval_ms = max(1, int(50 / self.speed.get()))  # Slower for stability
            frames = len(self.ecg.time) // 20  # Even fewer frames
            
            self.animation = FuncAnimation(
                self.fig,
                self.animate_frame,
                frames=frames,
                interval=interval_ms,
                blit=False,  # Disable blitting to avoid axis issues
                repeat=True,
                cache_frame_data=False
            )
            self.is_playing = False
            self.play_btn.config(text="▶")
        except Exception as e:
            print(f"Animation setup error: {e}")
            # Fallback to static display
            self.update_plot()

def run_visualizer():
    """Run the ECG visualizer application."""
    root = tk.Tk()
    root.title("ECG Visualizer")
    app = ECGVisualizer(root)
    root.mainloop()

if __name__ == "__main__":
    run_visualizer()
