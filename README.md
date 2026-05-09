# ECG Generator

[![CI](https://github.com/Lvlzer0o/cuddly-fiesta/actions/workflows/python-app.yml/badge.svg)](https://github.com/Lvlzer0o/cuddly-fiesta/actions/workflows/python-app.yml)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue)](pyproject.toml)
[![Package](https://img.shields.io/badge/package-ecg--generator%200.1.0-informational)](pyproject.toml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Python tools for generating synthetic ECG-style waveforms, rhythm examples,
12-lead projections, plots, animations, and a Tk-based GUI.

This project is for software experiments, demos, and synthetic signal
generation. It is not a medical device, diagnostic tool, or source of clinical
guidance.

## Features

- Grid scaling constants for standard ECG paper timing and voltage units.
- Reusable waveform segments: P wave, QRS complex, T wave, and U wave.
- Rhythm pattern classes for normal sinus rhythm and several arrhythmia demos.
- 12-lead signal projection through `MultiLeadECG`.
- Matplotlib plotting and animation helpers.
- Tkinter GUI entry points for local interactive use.
- CLI commands for demos, animation, and GUI launch.

## Requirements

- Python 3.8 or newer.
- `numpy`, `matplotlib`, and `scipy`.
- Tk support for GUI commands.

On Debian or Ubuntu, install Tk support before running GUI commands:

```bash
sudo apt-get update
sudo apt-get install python3-tk
```

## Installation

From the repository root:

```bash
python -m pip install --upgrade pip
python -m pip install -e .
```

For development and CI parity:

```bash
python -m pip install -r requirements.txt
python -m pip install -e .
python -m pip install flake8 pytest
```

## Command Line

Show available commands:

```bash
python -m cuddly_fiesta --help
```

Common commands:

```bash
python -m cuddly_fiesta baseline
python -m cuddly_fiesta demo normal
python -m cuddly_fiesta demo afib
python -m cuddly_fiesta animate --multi
python -m cuddly_fiesta gui
```

Installed console scripts:

```bash
ecg-generator --help
ecg-gui
ecg-visualizer
ecg-multilead-demo
```

Some demo utilities write PNG output to the current directory. Utilities that
support `OUTPUT_DIR` can be redirected like this:

```bash
mkdir -p plots
OUTPUT_DIR=./plots ecg-multilead-demo
```

PowerShell:

```powershell
New-Item -ItemType Directory -Force .\plots | Out-Null
$env:OUTPUT_DIR = ".\plots"
ecg-multilead-demo
```

## Python Usage

```python
from cuddly_fiesta import ECGCore, MultiLeadECG, NormalSinusRhythm

ecg = ECGCore(duration_sec=5, sampling_rate=1000)
NormalSinusRhythm(heart_rate_bpm=70, rng_seed=1).apply_to_ecg(ecg)

multi = MultiLeadECG.from_ecg(ecg)
fig, _axes = multi.plot_all_leads(with_grid=True)
fig.savefig("example_12_lead.png", dpi=150, bbox_inches="tight")
```

For lower-level composition, create waveform segment instances and add them to
an `ECGCore` instance:

```python
from cuddly_fiesta import ECGCore, PWave, QRSComplex, TWave

ecg = ECGCore(duration_sec=3, sampling_rate=1000)
ecg.add_waveform_segment(PWave(amplitude_mv=0.15, duration_ms=100), 0.2)
ecg.add_waveform_segment(QRSComplex(r_amplitude_mv=1.0, duration_ms=100), 0.32)
ecg.add_waveform_segment(TWave(amplitude_mv=0.25, duration_ms=160), 0.55)
ecg.plot(show_grid=True)
```

## Repository Layout

```text
cuddly_fiesta/
  core/       Core ECG, grid scaling, validation, and multi-lead helpers
  rhythms/    Rhythm pattern implementations
  segments/   Waveform segment implementations
  demos/      Demo-oriented runtime helpers
  gui/        Tkinter GUI entry points
  tests/      Verification and demo helpers
tests/        Pytest/unittest test suite
```

Top-level files such as `run_demo.py`, `run_manual.py`, and `run_visualizer.py`
are compatibility/demo entry points.

## Docker

Build the image:

```bash
docker build -t cuddly-fiesta .
```

Run a CLI command:

```bash
docker run --rm cuddly-fiesta python -m cuddly_fiesta --help
```

The default container command launches the GUI. GUI use from Docker requires a
working display setup; headless environments should override the command.

## Testing

Run the same checks used by CI:

```bash
python -m flake8 .
python -m pytest -q
```

The test suite can also run through the standard library:

```bash
python -m unittest discover -s tests
```

## License

MIT License. See [LICENSE](LICENSE).
