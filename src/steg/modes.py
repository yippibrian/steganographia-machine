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
    historical_notation: str | None = None
    traversal: str = "forward"


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
    historical_notation = spec.get("historical_notation")
    traversal = spec.get("traversal", "forward")

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
    if historical_notation is not None and (
        not isinstance(historical_notation, str)
        or not historical_notation
        or any(symbol not in {"o", "."} for symbol in historical_notation)
    ):
        raise DefinitionError("historical_notation must contain only 'o' and '.'")
    if traversal not in {"forward", "reverse"}:
        raise DefinitionError("historical mode traversal must be 'forward' or 'reverse'")

    mode = HistoricalMode(
        name, family, parameters, modifiers, normalization,
        historical_notation, traversal,
    )

    # Keep historically described deviations visible instead of silently
    # approximating them with a fixed mask. Stateful execution comes next.
    if modifiers:
        raise DefinitionError(
            "historical mode modifiers are recorded but stateful modifier execution is not yet supported"
        )

    compiled_pipeline = _compile_family(mode)
    if mode.traversal == "reverse":
        compiled_pipeline = (
            compiled_pipeline[0],
            {"traverse": {"direction": "reverse"}},
            *compiled_pipeline[1:],
        )
    _validate_historical_notation(mode)
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


def _validate_historical_notation(mode: HistoricalMode) -> None:
    if mode.historical_notation is None or mode.family != "block_word_initials":
        return
    idle_run = mode.parameters.get("idle_run")
    significant_run = mode.parameters.get("significant_run")
    starts_with = mode.parameters.get("starts_with", "idle")
    expected = (
        ("o" * idle_run + "." * significant_run)
        if starts_with == "idle"
        else ("." * significant_run + "o" * idle_run)
    )
    if mode.historical_notation != expected:
        raise DefinitionError(
            f"mode {mode.name}: historical_notation {mode.historical_notation!r} "
            f"does not match semantic parameters (expected {expected!r})"
        )


def _only(parameters: Mapping[str, Any], allowed: set[str], name: str) -> None:
    unknown = set(parameters) - allowed
    if unknown:
        raise DefinitionError(f"mode {name}: unknown parameter(s): {', '.join(sorted(unknown))}")


def generate_simple_block_space() -> tuple[HistoricalMode, ...]:
    """Generate Selenus's two orders of thirty simple block configurations.

    In the printed table, o denotes an Idle word and . a Valid (significant)
    word. The five columns vary idle_run from 1..5, while the six rows vary
    significant_run from 1..6.
    """
    modes = []
    for starts_with in ("idle", "significant"):
        for idle_run in range(1, 6):
            for significant_run in range(1, 7):
                notation = (
                    "o" * idle_run + "." * significant_run
                    if starts_with == "idle"
                    else "." * significant_run + "o" * idle_run
                )
                modes.append(
                    HistoricalMode(
                        name=f"generated-{starts_with}-{idle_run}-{significant_run}",
                        family="block_word_initials",
                        parameters={
                            "idle_run": idle_run,
                            "significant_run": significant_run,
                            "starts_with": starts_with,
                        },
                        historical_notation=notation,
                    )
                )
    return tuple(modes)
