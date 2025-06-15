"""Core ECG generation package."""

# Expose optional C++ backend
try:  # pragma: no cover - optional dependency
    from . import cpp_backend as _cpp_backend
    __all__ = ["_cpp_backend"]
except Exception:  # pragma: no cover
    _cpp_backend = None
    __all__ = []
