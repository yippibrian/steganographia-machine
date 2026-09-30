from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .loader import DefinitionError, pipeline_from_dict
from .pipeline import Pipeline


@dataclass(frozen=True)
class HistoricalMode:
    name: str
    family: str
    parameters: Mapping[str, Any]
    modifiers: tuple[Mapping[str, Any], ...] = ()
    normalization: Mapping[str, Any] | None = None


@dataclass(frozen=True)
class CompiledMode:
    mode: HistoricalMode
    pipeline: Pipeline
    compiled_pipeline: tuple[Mapping[str, Any], ...]


def compile_historical_mode(spec: Mapping[str, Any]) -> CompiledMode:
    name = spec.get("name")
    family = spec.get("family")
    parameters = spec.get("parameters", {})
    modifiers = tuple(spec.get("modifiers", []))
    normalization = spec.get("normalization")

    if not isinstance(name, str) or not name:
        raise DefinitionError("historical mode requires a non-empty name")
    if not isinstance(family, str) or not family:
        raise DefinitionError("historical mode requires a non-empty family")
    if not isinstance(parameters, dict):
        raise DefinitionError("historical mode parameters must be a mapping")
    if not all(isinstance(modifier, dict) for modifier in modifiers):
        raise DefinitionError("historical mode modifiers must be mappings")
    if normalization is not None and not isinstance(normalization, dict):
        raise DefinitionError("historical mode normalization must be a mapping")

    mode = HistoricalMode(name, family, parameters, modifiers, normalization)

    # Keep historically described deviations visible instead of silently
    # approximating them with a fixed mask. Stateful execution comes next.
    if modifiers:
        raise DefinitionError(
            "historical mode modifiers are recorded but stateful modifier execution is not yet supported"
        )

    compiled_pipeline = _compile_family(mode)
    if mode.normalization:
        compiled_pipeline += ({"normalize": dict(mode.normalization)},)

    return CompiledMode(
        mode,
        pipeline_from_dict({"pipeline": list(compiled_pipeline)}),
        compiled_pipeline,
    )


def _compile_family(mode: HistoricalMode) -> tuple[Mapping[str, Any], ...]:
    parameters = mode.parameters

    if mode.family == "word_initials":
        _only(parameters, {"selection"}, mode.name)
        if parameters.get("selection", "all") != "all":
            raise DefinitionError(f"mode {mode.name}: word_initials selection must be 'all'")
        return (
            {"unitize": {"unit": "word"}},
            {"project": {"part": "initial"}},
            {"concatenate": {}},
        )

    if mode.family == "block_word_initials":
        _only(parameters, {"idle_run", "significant_run", "starts_with"}, mode.name)
        schedule = {
            "type": "alternating_blocks",
            "idle_run": parameters.get("idle_run"),
            "significant_run": parameters.get("significant_run"),
            "starts_with": parameters.get("starts_with", "idle"),
        }
        return (
            {"unitize": {"unit": "word"}},
            {"select": {"schedule": schedule}},
            {"project": {"part": "initial"}},
            {"concatenate": {}},
        )

    raise DefinitionError(f"mode {mode.name}: unsupported historical family {mode.family!r}")


def _only(parameters: Mapping[str, Any], allowed: set[str], name: str) -> None:
    unknown = set(parameters) - allowed
    if unknown:
        raise DefinitionError(f"mode {name}: unknown parameter(s): {', '.join(sorted(unknown))}")


def generate_simple_block_space() -> tuple[HistoricalMode, ...]:
    """Generate the 60 structural cells in the two-order, five-by-six table.

    The generator deliberately does not assign historical spirit names to cells.
    Names belong in evidenced corpus records, not in generated structure.
    """
    modes = []
    for starts_with in ("idle", "significant"):
        for significant_run in range(1, 6):
            for idle_run in range(1, 7):
                modes.append(
                    HistoricalMode(
                        name=f"generated-{starts_with}-{idle_run}-{significant_run}",
                        family="block_word_initials",
                        parameters={
                            "idle_run": idle_run,
                            "significant_run": significant_run,
                            "starts_with": starts_with,
                        },
                    )
                )
    return tuple(modes)
