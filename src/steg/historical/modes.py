from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from ..errors import DefinitionError
from ..engine.spec import pipeline_from_dict
from ..engine.pipeline import Pipeline
from .patterns import BlockPattern


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


def compile_historical_mode(
    spec: Mapping[str, Any],
    execution_parameters: Mapping[str, Any] | None = None,
    *,
    allow_unbound_modifiers: bool = False,
) -> CompiledMode:
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

    compiled_pipeline = _compile_family(mode)
    if modifiers:
        compiled_pipeline = _apply_modifiers(
            mode,
            compiled_pipeline,
            execution_parameters or {},
            allow_unbound=allow_unbound_modifiers,
        )
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


def _apply_modifiers(
    mode: HistoricalMode,
    pipeline: tuple[Mapping[str, Any], ...],
    execution_parameters: Mapping[str, Any],
    *,
    allow_unbound: bool = False,
) -> tuple[Mapping[str, Any], ...]:
    result = pipeline
    for modifier in mode.modifiers:
        modifier_type = modifier.get("type")
        if modifier_type != "boundary_reset":
            raise DefinitionError(
                f"mode {mode.name}: unsupported modifier {modifier_type!r}"
            )
        if mode.family != "block_word_initials":
            raise DefinitionError(
                f"mode {mode.name}: boundary_reset requires block_word_initials"
            )
        parameter_name = modifier.get(
            "boundary_parameter", "boundary_after_selected"
        )
        boundaries = execution_parameters.get(parameter_name)
        if boundaries is None:
            if allow_unbound:
                continue
            raise DefinitionError(
                f"mode {mode.name}: boundary-sensitive execution requires "
                f"case parameter {parameter_name!r}"
            )
        if (
            not isinstance(boundaries, (list, tuple))
            or not all(
                isinstance(value, int) and not isinstance(value, bool) and value > 0
                for value in boundaries
            )
        ):
            raise DefinitionError(
                f"mode {mode.name}: {parameter_name} must contain positive integers"
            )
        reset = modifier.get("reset_to_cycle_position", 0)
        pattern = BlockPattern.from_parameters(mode.parameters, mode.name)
        schedule = {
            **pattern.schedule_spec,
            "type": "boundary_reset_blocks",
            "boundary_after_selected": list(boundaries),
            "reset_to_cycle_position": reset,
        }
        replaced = False
        stages = []
        for stage in result:
            if not replaced and "select" in stage:
                stages.append({"select": {"schedule": schedule}})
                replaced = True
            else:
                stages.append(stage)
        if not replaced:
            raise DefinitionError(
                f"mode {mode.name}: boundary_reset found no selection stage"
            )
        result = tuple(stages)
    return result


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
        pattern = BlockPattern.from_parameters(parameters, mode.name)
        schedule = pattern.schedule_spec
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
    expected = BlockPattern.from_parameters(mode.parameters, mode.name).notation
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
                pattern = BlockPattern(idle_run, significant_run, starts_with)
                modes.append(
                    HistoricalMode(
                        name=f"generated-{starts_with}-{idle_run}-{significant_run}",
                        family="block_word_initials",
                        parameters={
                            "idle_run": idle_run,
                            "significant_run": significant_run,
                            "starts_with": starts_with,
                        },
                        historical_notation=pattern.notation,
                    )
                )
    return tuple(modes)
