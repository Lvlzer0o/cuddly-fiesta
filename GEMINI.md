# Project Overview
**cuddly-fiesta** (package name: `ecg-generator`) is a modular Python toolkit for generating synthetic ECG-style waveforms, rhythm examples, 12-lead projections, plots, animations, and a Tk-based graphical user interface (GUI). It is designed for software experiments, demonstrations, and synthetic signal generation (not a medical device or diagnostic tool).

## Core Technologies
- **Language**: Python 3.8+
- **Dependencies**: `numpy`, `matplotlib`, `scipy`
- **GUI**: `tkinter` (Requires system Tk support, e.g., `python3-tk` on Debian/Ubuntu)
- **Testing**: `pytest`, `unittest`
- **Linting**: `flake8`

## Architecture & Directory Structure
The main source code is located in the `cuddly_fiesta/` package:
- `core/`: Core ECG logic, grid scaling constants, validation, and multi-lead projection helpers (`MultiLeadECG`).
- `rhythms/`: Implementations of various rhythm patterns (e.g., normal sinus, afib, bundle branch block).
- `segments/`: Reusable waveform segment classes (`PWave`, `QRSComplex`, `TWave`, `UWave`).
- `gui/`: Tkinter GUI application entry points (`ekg_ui.py`).
- `demos/`: Demo-oriented runtime helpers and animations.
- `cli/`: Command-line interface definitions.
- `tests/`: External test suite containing Pytest/unittest cases.

## Building and Running

### Installation
From the repository root, install the package in editable mode:
```bash
python -m pip install --upgrade pip
python -m pip install -e .
```
For development with dependencies:
```bash
python -m pip install -r requirements.txt
python -m pip install -e .
python -m pip install flake8 pytest
```

### Running the Application
The project provides a CLI and a GUI:

**Show available CLI commands:**
```bash
python -m cuddly_fiesta --help
```

**Launch the Tkinter GUI:**
```bash
python -m cuddly_fiesta gui
# Or use the installed console script:
ecg-gui
```

**Run Demos and Animations:**
```bash
python -m cuddly_fiesta baseline
python -m cuddly_fiesta demo normal
python -m cuddly_fiesta demo afib
python -m cuddly_fiesta animate --multi
```

### Docker
To build and run via Docker:
```bash
docker build -t cuddly-fiesta .
docker run --rm cuddly-fiesta python -m cuddly_fiesta --help
```
*(Note: Running the GUI from Docker requires a working display setup)*

## Development Conventions & Testing

### Testing
Tests are located in the top-level `tests/` directory and can be executed via `pytest` or `unittest`:
```bash
python -m pytest -q
# Or using unittest:
python -m unittest discover -s tests
```

### Linting
The project uses `flake8` for linting. Ensure the code passes without errors before committing:
```bash
python -m flake8 .
```

### Code Style
- Use object-oriented design for rhythm and waveform segment generation.
- Favor `pathlib` for file paths and cross-platform compatibility.
- Ensure any new algorithms or features have corresponding tests in the `tests/` directory.
- Avoid introducing external runtime dependencies unless absolutely necessary; stick to `numpy`, `scipy`, and `matplotlib`.