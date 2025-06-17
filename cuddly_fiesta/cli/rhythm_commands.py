"""Rhythm-related CLI commands for the ECG Generator.

This module defines commands for generating different cardiac rhythms.
"""

import click
from typing import Optional
import numpy as np
import matplotlib.pyplot as plt

from ..core import ECGCore
from ..rhythms import (
    NormalSinusRhythm,
    SinusBradycardia,
    SinusTachycardia,
    AtrialFibrillation,
)

# Create a click group for rhythm commands
@click.group()
def rhythm() -> None:
    """Commands for generating different cardiac rhythms."""
    pass

# Helper function to plot rhythm
def plot_rhythm(rhythm, duration_sec: float, sampling_rate: int, title: str) -> None:
    """Plot a rhythm using matplotlib.
    
    Args:
        rhythm: The rhythm instance to plot
        duration_sec: Duration in seconds
        sampling_rate: Sampling rate in Hz
        title: Plot title
    """
    # Generate the signal
    time = np.linspace(0, duration_sec, int(duration_sec * sampling_rate), endpoint=False)
    voltage = np.zeros_like(time)
    
    # Apply rhythm pattern to the signal
    for beat_time, segment, _ in rhythm.segments:
        if beat_time >= duration_sec:
            continue
            
        # Generate segment
        seg_t, seg_v = segment.generate(sampling_rate)
        seg_t += beat_time
        
        # Add to output
        valid = (seg_t < duration_sec) & (seg_t >= 0)
        if not np.any(valid):
            continue
            
        indices = np.clip(
            np.round(seg_t[valid] * sampling_rate).astype(int),
            0,
            len(time) - 1
        )
        np.add.at(voltage, indices, seg_v[valid])
    
    # Plot
    plt.figure(figsize=(15, 4))
    plt.plot(time, voltage)
    plt.title(title)
    plt.xlabel('Time (s)')
    plt.ylabel('Voltage (mV)')
    
    # Add grid
    xlim = plt.xlim()
    ylim = plt.ylim()
    
    # Major grid lines (0.2s = 5mm at 25mm/s)
    for x in np.arange(0, xlim[1], 0.2):
        plt.axvline(x, color='red', alpha=0.2, linestyle='-', zorder=0)
    
    # Minor grid lines (0.04s = 1mm at 25mm/s)
    for x in np.arange(0, xlim[1], 0.04):
        plt.axvline(x, color='gray', alpha=0.1, linestyle=':', zorder=0)
    
    # Horizontal grid lines (0.1mV = 1mm at 10mm/mV)
    for y in np.arange(np.floor(ylim[0] * 10) / 10, np.ceil(ylim[1] * 10) / 10 + 0.1, 0.1):
        plt.axhline(y, color='gray', alpha=0.1, linestyle=':', zorder=0)
    
    plt.xlim(xlim)
    plt.ylim(ylim)
    plt.tight_layout()
    plt.show()

@rhythm.command()
@click.option('--rate', '-r', type=int, default=72, help='Heart rate in BPM (60-100)')
@click.option('--duration', '-d', type=float, default=10.0, help='Duration in seconds')
@click.option('--plot/--no-plot', default=True, help='Show plot')
def normal(rate: int, duration: float, plot: bool) -> None:
    """Generate normal sinus rhythm."""
    if not 60 <= rate <= 100:
        click.echo("Warning: Heart rate outside normal range (60-100 bpm)", err=True)
    
    rhythm = NormalSinusRhythm(heart_rate_bpm=rate, duration_sec=duration)
    
    if plot:
        plot_rhythm(rhythm, duration, 1000, f"Normal Sinus Rhythm ({rate} bpm)")
    
    click.echo(f"Generated {duration} seconds of normal sinus rhythm at {rate} bpm")

@rhythm.command()
@click.option('--rate', '-r', type=int, default=50, help='Heart rate in BPM (<60)')
@click.option('--duration', '-d', type=float, default=10.0, help='Duration in seconds')
@click.option('--plot/--no-plot', default=True, help='Show plot')
def brady(rate: int, duration: float, plot: bool) -> None:
    """Generate sinus bradycardia."""
    if rate >= 60:
        click.echo("Error: Bradycardia requires heart rate < 60 bpm", err=True)
        return
    
    rhythm = SinusBradycardia(heart_rate_bpm=rate, duration_sec=duration)
    
    if plot:
        plot_rhythm(rhythm, duration, 1000, f"Sinus Bradycardia ({rate} bpm)")
    
    click.echo(f"Generated {duration} seconds of sinus bradycardia at {rate} bpm")

@rhythm.command()
@click.option('--rate', '-r', type=int, default=120, help='Heart rate in BPM (>100)')
@click.option('--duration', '-d', type=float, default=10.0, help='Duration in seconds')
@click.option('--plot/--no-plot', default=True, help='Show plot')
def tachy(rate: int, duration: float, plot: bool) -> None:
    """Generate sinus tachycardia."""
    if rate <= 100:
        click.echo("Error: Tachycardia requires heart rate > 100 bpm", err=True)
        return
    
    rhythm = SinusTachycardia(heart_rate_bpm=rate, duration_sec=duration)
    
    if plot:
        plot_rhythm(rhythm, duration, 1000, f"Sinus Tachycardia ({rate} bpm)")
    
    click.echo(f"Generated {duration} seconds of sinus tachycardia at {rate} bpm")

@rhythm.command()
@click.option('--rate', '-r', type=int, default=120, help='Ventricular rate in BPM (100-180)')
@click.option('--duration', '-d', type=float, default=10.0, help='Duration in seconds')
@click.option('--plot/--no-plot', default=True, help='Show plot')
def afib(rate: int, duration: float, plot: bool) -> None:
    """Generate atrial fibrillation."""
    if not 100 <= rate <= 180:
        click.echo("Warning: Ventricular rate outside typical range (100-180 bpm)", err=True)
    
    rhythm = AtrialFibrillation(ventricular_rate_bpm=rate, duration_sec=duration)
    
    if plot:
        plot_rhythm(rhythm, duration, 1000, f"Atrial Fibrillation (VR: {rate} bpm)")
    
    click.echo(f"Generated {duration} seconds of atrial fibrillation with VR {rate} bpm")

@rhythm.command("asystole")
@click.option("--duration-sec", default=10, help="Duration of the ECG signal in seconds.")
@click.option("--show-plot", is_flag=True, help="Show the ECG plot.")
@click.pass_context
def asystole(ctx: click.Context, duration_sec: int, show_plot: bool) -> None:
    """Generate an Asystole (flatline) ECG pattern."""
    ecg = ECGCore(duration_sec=duration_sec, sampling_rate=ctx.obj["sampling_rate"])
    pattern = Asystole()
    pattern.apply_to_ecg(ecg)
    ecg.plot(show=show_plot, title="Asystole (Flatline)")


@rhythm.command("first-degree-av-block")
@click.option("--duration-sec", default=10, help="Duration of the ECG signal in seconds.")
@click.option("--heart-rate-bpm", default=70, help="Heart rate in beats per minute.")
@click.option("--pr-interval-ms", default=240, help="PR interval in milliseconds.")
@click.option("--show-plot", is_flag=True, help="Show the ECG plot.")
@click.pass_context
def first_degree_av_block(
    ctx: click.Context,
    duration_sec: int,
    heart_rate_bpm: int,
    pr_interval_ms: int,
    show_plot: bool,
) -> None:
    """Generate a First-Degree AV Block ECG pattern."""
    ecg = ECGCore(duration_sec=duration_sec, sampling_rate=ctx.obj["sampling_rate"])
    pattern = FirstDegreeAVBlock(
        heart_rate_bpm=heart_rate_bpm, pr_interval_ms=pr_interval_ms
    )
    pattern.apply_to_ecg(ecg)
    ecg.plot(show=show_plot, title="First-Degree AV Block")


@rhythm.command("third-degree-av-block")
@click.option("--duration-sec", default=10, help="Duration of the ECG signal in seconds.")
@click.option("--atrial-rate-bpm", default=75, help="Atrial rate in beats per minute.")
@click.option("--ventricular-rate-bpm", default=40, help="Ventricular rate in beats per minute.")
@click.option("--show-plot", is_flag=True, help="Show the ECG plot.")
@click.pass_context
def third_degree_av_block(
    ctx: click.Context,
    duration_sec: int,
    atrial_rate_bpm: int,
    ventricular_rate_bpm: int,
    show_plot: bool,
) -> None:
    """Generate a Third-Degree AV Block ECG pattern."""
    ecg = ECGCore(duration_sec=duration_sec, sampling_rate=ctx.obj["sampling_rate"])
    pattern = ThirdDegreeAVBlock(
        atrial_rate_bpm=atrial_rate_bpm,
        ventricular_rate_bpm=ventricular_rate_bpm,
    )
    pattern.apply_to_ecg(ecg)
    ecg.plot(show=show_plot, title="Third-Degree AV Block")


@rhythm.command("bundle-branch-block")
@click.option("--duration-sec", default=10, help="Duration of the ECG signal in seconds.")
@click.option("--heart-rate-bpm", default=70, help="Heart rate in beats per minute.")
@click.option("--qrs-duration-ms", default=140, help="QRS duration in milliseconds.")
@click.option("--show-plot", is_flag=True, help="Show the ECG plot.")
@click.pass_context
def bundle_branch_block(
    ctx: click.Context,
    duration_sec: int,
    heart_rate_bpm: int,
    qrs_duration_ms: int,
    show_plot: bool,
) -> None:
    """Generate a Bundle-Branch Block ECG pattern."""
    ecg = ECGCore(duration_sec=duration_sec, sampling_rate=ctx.obj["sampling_rate"])
    pattern = BundleBranchBlock(
        heart_rate_bpm=heart_rate_bpm, qrs_duration_ms=qrs_duration_ms
    )
    pattern.apply_to_ecg(ecg)
    ecg.plot(show=show_plot, title="Bundle-Branch Block")


@rhythm.command("svt")
@click.option("--duration-sec", default=10, help="Duration of the ECG signal in seconds.")
@click.option("--heart-rate-bpm", default=180, help="Heart rate in beats per minute (typically 150-250).")
@click.option("--show-plot", is_flag=True, help="Show the ECG plot.")
@click.pass_context
def svt(
    ctx: click.Context,
    duration_sec: int,
    heart_rate_bpm: int,
    show_plot: bool,
) -> None:
    """Generate a Supraventricular Tachycardia (SVT) ECG pattern."""
    ecg = ECGCore(duration_sec=duration_sec, sampling_rate=ctx.obj["sampling_rate"])
    pattern = SupraventricularTachycardia(
        heart_rate_bpm=heart_rate_bpm
    )
    pattern.apply_to_ecg(ecg)
    ecg.plot(show=show_plot, title="Supraventricular Tachycardia (SVT)")


@rhythm.command("mat")
@click.option("--duration-sec", default=10, help="Duration of the ECG signal in seconds.")
@click.option("--heart-rate-bpm", default=120, help="Average heart rate in beats per minute (typically > 100).")
@click.option("--show-plot", is_flag=True, help="Show the ECG plot.")
@click.pass_context
def mat(
    ctx: click.Context,
    duration_sec: int,
    heart_rate_bpm: int,
    show_plot: bool,
) -> None:
    """Generate a Multifocal Atrial Tachycardia (MAT) ECG pattern."""
    ecg = ECGCore(duration_sec=duration_sec, sampling_rate=ctx.obj["sampling_rate"])
    pattern = MultifocalAtrialTachycardia(
        heart_rate_bpm=heart_rate_bpm
    )
    pattern.apply_to_ecg(ecg)
    ecg.plot(show=show_plot, title="Multifocal Atrial Tachycardia (MAT)")


@rhythm.command("vf")
@click.option("--duration-sec", default=10, help="Duration of the ECG signal in seconds.")
@click.option("--amplitude-mv", default=0.5, help="Average amplitude of the fibrillation waves in mV.")
@click.option("--show-plot", is_flag=True, help="Show the ECG plot.")
@click.pass_context
def vf(
    ctx: click.Context,
    duration_sec: int,
    amplitude_mv: float,
    show_plot: bool,
) -> None:
    """Generate a Ventricular Fibrillation (VF) ECG pattern."""
    ecg = ECGCore(duration_sec=duration_sec, sampling_rate=ctx.obj["sampling_rate"])
    pattern = VentricularFibrillation(amplitude_mv=amplitude_mv)
    pattern.apply_to_ecg(ecg)
    ecg.plot(show=show_plot, title="Ventricular Fibrillation (VF)")


@rhythm.command("torsades")
@click.option("--duration-sec", default=10, help="Duration of the ECG signal in seconds.")
@click.option("--ventricular-rate-bpm", default=200, help="Ventricular rate in beats per minute.")
@click.option("--twist-frequency-hz", default=0.1, help="Frequency of the amplitude modulation in Hz.")
@click.option("--show-plot", is_flag=True, help="Show the ECG plot.")
@click.pass_context
def torsades(
    ctx: click.Context,
    duration_sec: int,
    ventricular_rate_bpm: int,
    twist_frequency_hz: float,
    show_plot: bool,
) -> None:
    """Generate a Torsades de Pointes ECG pattern."""
    ecg = ECGCore(duration_sec=duration_sec, sampling_rate=ctx.obj["sampling_rate"])
    pattern = TorsadesDePointes(
        ventricular_rate_bpm=ventricular_rate_bpm,
        twist_frequency_hz=twist_frequency_hz,
    )
    pattern.apply_to_ecg(ecg)
    ecg.plot(show=show_plot, title="Torsades de Pointes")
