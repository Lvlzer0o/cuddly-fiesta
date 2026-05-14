# Repository Guidelines

## Project Structure & Module Organization

This repository packages a synthetic ECG generator as `ecg-generator`. Core code lives in `cuddly_fiesta/`: `core/` contains ECG primitives, grid scaling, validation, and multi-lead helpers; `segments/` contains waveform pieces; `rhythms/` contains rhythm implementations; `gui/` and `ecg_visualizer.py` provide the Tk-based interface; `demos/` and top-level `run_*.py` files are demo and compatibility entry points. Tests live in the top-level `tests/` directory and use `test_*.py` naming.

## Build, Test, and Development Commands

Install for local development:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -e .
python -m pip install flake8 pytest
```

Run the CLI and common entry points:

```bash
python -m cuddly_fiesta --help
python -m cuddly_fiesta baseline
python -m cuddly_fiesta gui
ecg-gui
ecg-multilead-demo
```

Build the Docker image with `docker build -t cuddly-fiesta .`; override the default GUI command in headless environments.

## Coding Style & Naming Conventions

Use standard Python style with 4-space indentation. Keep modules and functions in `snake_case`, classes in `PascalCase`, and tests named `test_<behavior>.py`. Match nearby code before introducing a new pattern. The active lint tool is flake8, configured in `.flake8` with a 180-character line limit and project-specific ignores.

## Testing Guidelines

Run CI-equivalent checks before submitting changes:

```bash
python -m flake8 .
python -m pytest -q
```

For standard-library compatibility, `python -m unittest discover -s tests` is also supported. Add or update focused tests when changing ECG math, rhythm behavior, CLI commands, or GUI registry behavior. Avoid importing Tk-backed GUI code at package import time; headless CI must be able to collect tests.

## Commit & Pull Request Guidelines

Recent history uses short, imperative conventional-style subjects such as `fix: harden public repo hygiene and bool coercion` and `refactor: simplify ECG visualizer timer and test stubs`. Keep commits focused and describe the user-visible behavior or maintenance outcome. Pull requests should include a brief summary, commands run, linked issue if applicable, and screenshots only for GUI-visible changes.

## Security & Configuration Tips

This project is for synthetic signal demos only; do not present output as medical advice or diagnostic evidence. Keep generated plots, caches, local environment files, SARIF reports, IDE metadata, and build artifacts out of commits unless explicitly required.
