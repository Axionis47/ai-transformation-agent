# Exports PitchEngine for callers that import from engines.pitch
from __future__ import annotations


def __getattr__(name: str) -> object:
    if name == "PitchEngine":
        from engines.pitch.engine import PitchEngine
        return PitchEngine
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["PitchEngine"]
