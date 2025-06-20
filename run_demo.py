#!/usr/bin/env python
"""
Simple demo script for the ECG generator app.

This script provides an easy way to run different demonstrations of the ECG generator
functionality without having to use the command-line interface directly.
"""

import matplotlib.pyplot as plt
import matplotlib
from cuddly_fiesta.ecg_core import ECGCore
from cuddly_fiesta.multi_lead import MultiLeadECG
from cuddly_fiesta.ecg_animation import animate_ecg
from cuddly_fiesta.waveform_segments import (
    NormalSinusRhythm,
    AtrialFibrillation,
    AtrialFlutter,
    VentricularTachycardia,
    VentricularFibrillation,
    WolffParkinsonWhite,
    PulselessElectricalActivity
    FirstDegreeAVBlock,
    SecondDegreeAVBlockType1,
    SecondDegreeAVBlockType2,
    ThirdDegreeAVBlock,
)

# Configure matplotlib for interactive mode
matplotlib.use('TkAgg')  # Use TkAgg backend for better interactive support


def demo_normal_ecg(animate=False):
    """Generate and display a normal sinus rhythm ECG."""
    print("Generating normal sinus rhythm ECG...")
    ecg = ECGCore(duration_sec=4, sampling_rate=1000)
    NormalSinusRhythm(heart_rate_bpm=70).apply_to_ecg(ecg)

    if animate:
        animation = animate_ecg(ecg, interval_ms=40, show_grid=True)
        plt.show()
    else:
        ecg.plot(show_grid=True)
        plt.show()


def demo_afib_ecg(animate=False):
    """Generate and display an atrial fibrillation ECG."""
    print("Generating atrial fibrillation ECG...")
    ecg = ECGCore(duration_sec=4, sampling_rate=1000)
    AtrialFibrillation().apply_to_ecg(ecg)

    if animate:
        animation = animate_ecg(ecg, interval_ms=40, show_grid=True)
        plt.show()
    else:
        ecg.plot(show_grid=True)
        plt.show()


def demo_aflutter_ecg(animate=False):
    """Generate and display an atrial flutter ECG."""
    print("Generating atrial flutter ECG...")
    ecg = ECGCore(duration_sec=4, sampling_rate=1000)
    AtrialFlutter().apply_to_ecg(ecg)

    if animate:
        animation = animate_ecg(ecg, interval_ms=40, show_grid=True)
        plt.show()
    else:
        ecg.plot(show_grid=True)
        plt.show()


def demo_vtach_ecg(animate=False):
    """Generate and display a ventricular tachycardia ECG."""
    print("Generating ventricular tachycardia ECG...")
    ecg = ECGCore(duration_sec=4, sampling_rate=1000)
    VentricularTachycardia().apply_to_ecg(ecg)

    if animate:
        animation = animate_ecg(ecg, interval_ms=40, show_grid=True)
        plt.show()
    else:
        ecg.plot(show_grid=True)
        plt.show()


def demo_vfib_ecg(animate=False):
    """Generate and display a ventricular fibrillation ECG."""
    print("Generating ventricular fibrillation ECG...")
    ecg = ECGCore(duration_sec=4, sampling_rate=1000)
    VentricularFibrillation().apply_to_ecg(ecg)

    if animate:
        animation = animate_ecg(ecg, interval_ms=40, show_grid=True)
        plt.show()
    else:
        ecg.plot(show_grid=True)
        plt.show()


def demo_wpw_ecg(animate=False):
    """Generate and display a Wolff-Parkinson-White ECG."""
    print("Generating Wolff-Parkinson-White ECG...")
    ecg = ECGCore(duration_sec=4, sampling_rate=1000)
    WolffParkinsonWhite().apply_to_ecg(ecg)

    if animate:
        animation = animate_ecg(ecg, interval_ms=40, show_grid=True)
        plt.show()
    else:
        ecg.plot(show_grid=True)
        plt.show()


def demo_multilead_ecg(animate=False):
    """Generate and display a multi-lead ECG."""
    print("Generating multi-lead ECG...")
    ecg = ECGCore(duration_sec=4, sampling_rate=1000)
    NormalSinusRhythm(heart_rate_bpm=70).apply_to_ecg(ecg)
    multi_lead = MultiLeadECG.from_ecg(ecg)

    if animate:
        animation = animate_ecg(multi_lead, interval_ms=40, show_grid=True)
        plt.show()
    else:
        fig, axes = plt.subplots(3, 4, figsize=(15, 10))
        leads = list(multi_lead.leads.keys())

        for i, ax in enumerate(axes.flat):
            if i < len(leads):
                lead = leads[i]
                ax.plot(multi_lead.time, multi_lead.leads[lead])
                ax.set_title(f"Lead {lead}")
                ax.grid(True, alpha=0.3)
            else:
                ax.axis('off')

        plt.tight_layout()
        plt.show()


def main():
    """Main entry point for the demo script."""
    print("=== ECG Generator Demo ===\n")
    print("Select a rhythm to display:")
    print("1. Normal Sinus Rhythm")
    print("2. Atrial Fibrillation")
    print("3. Atrial Flutter")
    print("4. Ventricular Tachycardia")
    print("5. Ventricular Fibrillation")
    print("6. Wolff-Parkinson-White")
    print("7. Multi-lead ECG (12-lead display)")

    choice = input("Enter your choice (1-7): ")

    # Ask if animation is desired
    animate_option = input("Show animation? (y/n): ").lower() == 'y'

    # Run the selected demo
    if choice == "1":
        demo_normal_ecg(animate=animate_option)
    elif choice == "2":
        demo_afib_ecg(animate=animate_option)
    elif choice == "3":
        demo_aflutter_ecg(animate=animate_option)
    elif choice == "4":
        demo_vtach_ecg(animate=animate_option)
    elif choice == "5":
        demo_vfib_ecg(animate=animate_option)
    elif choice == "6":
        demo_wpw_ecg(animate=animate_option)
    elif choice == "7":
        demo_multilead_ecg(animate=animate_option)
    else:
        print("Invalid choice. Please enter a number between 1 and 7.")


if __name__ == "__main__":
    main()
