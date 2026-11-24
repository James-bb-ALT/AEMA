"""AEMA host-side BatteryStats parsing package."""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from aema.pipeline import PipelineInputs, PipelineResult, parse_inputs

__all__ = ["PipelineInputs", "PipelineResult", "parse_inputs"]
__version__ = "1.0.0"


def __getattr__(name: str) -> Any:
    """Keep the public API while allowing raw capture diagnostics without pandas startup."""
    if name in __all__:
        from aema import pipeline

        return getattr(pipeline, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
