import os
from pathlib import Path


def get_output_dir(base_dir: str | None = None) -> Path:
    """Return a validated output directory.

    The directory is created if it does not exist. The location defaults to the
    ``OUTPUT_DIR`` environment variable or ``output`` within the repository.
    """
    out_dir = Path(base_dir or os.getenv("OUTPUT_DIR", "output")).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir.resolve()


def _is_relative_to(path: Path, base: Path) -> bool:
    try:
        path.relative_to(base)
        return True
    except ValueError:
        return False


def validate_output_path(filename: str, base_dir: str | None = None) -> Path:
    """Return a safe path inside the output directory for ``filename``.

    Raises ``ValueError`` if the resulting path escapes the output directory.
    """
    base = get_output_dir(base_dir)
    target = (base / filename).expanduser().resolve()
    if not _is_relative_to(target, base):
        raise ValueError(f"Illegal path: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    return target

