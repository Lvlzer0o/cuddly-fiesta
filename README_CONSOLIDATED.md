# ECG Generator - Consolidated Version

This document describes the single-file variant of the ECG Generator.
The authoritative source remains the modular `cuddly_fiesta` package.
`run.py` in this repository is now a thin wrapper that delegates to the package.

## Installation

1. Ensure you have Python 3.8+ installed
2. Install dependencies:
   ```bash
   pip install numpy matplotlib scipy
   ```
   
3. (Optional) For GUI mode, ensure tkinter is installed:
   - macOS: Usually pre-installed with Python
   - Linux: `sudo apt-get install python3-tk`
   - Windows: Usually pre-installed with Python

## Usage

### Quick Start

```bash
# Generate all demonstration plots
python run.py --demo all

# Run single-lead animation
python run.py --animate

# Run 12-lead animation
python run.py --animate --multi

# Run interactive GUI (requires tkinter)
python run.py --gui
```

### Demo Modes

Generate different types of ECG demonstrations:

```bash
# ECG baseline with grid and calibration
python run.py --demo baseline

# Single heartbeat with P-QRS-T components
python run.py --demo single

# Different arrhythmia patterns
python run.py --demo arrhythmias

# 12-lead ECG display
python run.py --demo 12lead

# All demos at once
python run.py --demo all
```

All demo outputs are saved to the `output/` directory.

### Animation Mode

Run real-time ECG animations:

```bash
# Single-lead animation
python run.py --animate

# 12-lead animation
python run.py --animate --multi

# Custom animation speed (milliseconds)
python run.py --animate --interval 20
```

### GUI Mode

Launch the interactive Tkinter GUI:

```bash
python run.py --gui
```

Features:
- Real-time 12-lead ECG display
- Arrhythmia pattern selection
- Playback speed control
- Lead highlighting

## Features

### Waveform Components
- **P Wave**: Atrial depolarization (80-100ms, 0.1-0.25mV)
- **QRS Complex**: Ventricular depolarization (80-120ms, 1.0mV)
- **T Wave**: Ventricular repolarization (120-160ms, 0.25mV)
- **U Wave**: Post-repolarization (60-110ms, 0.1mV)

### Arrhythmia Patterns
- Normal Sinus Rhythm (50-120 bpm)
- Atrial Fibrillation (irregular RR intervals)
- Ventricular Tachycardia (120-250 bpm)

### Clinical Features
- Standard ECG grid (25mm/sec, 10mm/mV)
- Grid-aligned timing and amplitudes
- 1mV calibration pulse
- Clinical validation framework
- 12-lead ECG generation

## Output Files

When running demos, the following files are created in the `output/` directory:

- `ecg_baseline_demo.png` - Baseline with grid and calibration
- `single_heartbeat_demo.png` - Single P-QRS-T complex
- `normal_sinus_rhythm_demo.png` - NSR pattern
- `atrial_fibrillation_demo.png` - AFib pattern
- `ventricular_tachycardia_demo.png` - VTach pattern
- `12_lead_ecg_demo.png` - 12-lead ECG display
- `12_lead_ecg_data.csv` - Raw ECG data export

## Architecture Summary

The consolidated `run.py` contains:

1. **Core Infrastructure**
   - Grid scaling constants and validation
   - ECG baseline generator
   - Clinical validator

2. **Waveform Generation**
   - Abstract waveform segment base class
   - Individual wave components (P, QRS, T, U)
   - Arrhythmia pattern system

3. **Visualization**
   - Multi-lead ECG display
   - Real-time animation
   - Tkinter GUI application

4. **Utilities**
   - Command-line interface
   - Demo generation functions
   - Data export capabilities

## Changes from Original

1. **Consolidated Structure**: All modules merged into single file
2. **Simplified Imports**: No cross-file imports needed
3. **Added Missing Constants**: Defined constants that were referenced but missing
4. **Tkinter Optional**: GUI works only if tkinter is available
5. **Unified Entry Point**: Single `main()` function with CLI
6. **Maintained Functionality**: All original features preserved

## Troubleshooting

1. **No tkinter**: If GUI mode fails, install tkinter or use other modes
2. **Import errors**: Ensure numpy, matplotlib, scipy are installed
3. **Permission denied**: Make file executable with `chmod +x run.py`
4. **No output**: Check the `output/` directory for generated files

## License

Same as original project (see LICENSE file)
