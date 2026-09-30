from __future__ import annotations
from pathlib import Path
from typing import Any
import yaml
from .pipeline import Pipeline
from .schedules import AlternatingBlockSchedule, BoundaryResetSchedule, MaskSchedule
from .stages import ConcatenateStage, NormalizeStage, ProjectStage, SelectStage, TraverseStage, UnitizeCharactersStage, UnitizeLinesStage, UnitizeWordsStage

class DefinitionError(ValueError):
    pass


def _read_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise DefinitionError(f"{path}: expected a mapping")
    return data


def pipeline_from_dict(data: dict[str, Any]) -> Pipeline:
    specs = data.get("pipeline")
    if not isinstance(specs, list) or not specs:
        raise DefinitionError("pipeline must be a non-empty list")
    return Pipeline(tuple(_stage_from_dict(spec, i) for i, spec in enumerate(specs, 1)))


def load_pipeline(path: str | Path) -> Pipeline:
    return pipeline_from_dict(_read_yaml(Path(path)))


def _stage_from_dict(spec: Any, index: int):
    if not isinstance(spec, dict) or len(spec) != 1:
        raise DefinitionError(f"pipeline stage {index} must contain exactly one operation")
    operation, options = next(iter(spec.items()))
    options = {} if options is None else options
    if not isinstance(options, dict):
        raise DefinitionError(f"pipeline stage {index}: options must be a mapping")

    if operation == "unitize":
        _reject_unknown(options, {"unit", "include_whitespace"}, operation, index)
        unit = options.get("unit")
        if unit == "word":
            if "include_whitespace" in options:
                raise DefinitionError(f"pipeline stage {index}: include_whitespace is valid only for character units")
            return UnitizeWordsStage()
        if unit == "character":
            return UnitizeCharactersStage(bool(options.get("include_whitespace", False)))
        if unit == "line":
            if "include_whitespace" in options:
                raise DefinitionError(f"pipeline stage {index}: include_whitespace is valid only for character units")
            return UnitizeLinesStage()
        raise DefinitionError(f"pipeline stage {index}: unsupported unit {unit!r}")

    if operation == "select":
        _reject_unknown(options, {"schedule"}, operation, index)
        schedule = options.get("schedule")
        if not isinstance(schedule, dict):
            raise DefinitionError(f"pipeline stage {index}: select requires schedule")
        return SelectStage(_schedule_from_dict(schedule, index))

    if operation == "traverse":
        _reject_unknown(options, {"direction"}, operation, index)
        direction = options.get("direction", "forward")
        if direction not in {"forward", "reverse"}:
            raise DefinitionError(f"pipeline stage {index}: unsupported traversal {direction!r}")
        return TraverseStage(direction)

    if operation == "project":
        _reject_unknown(options, {"part"}, operation, index)
        part = options.get("part")
        if part not in {"initial", "final", "whole"}:
            raise DefinitionError(f"pipeline stage {index}: unsupported projection {part!r}")
        return ProjectStage(part)

    if operation == "concatenate":
        _reject_unknown(options, {"separator"}, operation, index)
        separator = options.get("separator", "")
        if not isinstance(separator, str):
            raise DefinitionError(f"pipeline stage {index}: separator must be a string")
        return ConcatenateStage(separator)

    if operation == "normalize":
        _reject_unknown(options, {"lowercase", "remove_whitespace", "substitutions"}, operation, index)
        substitutions_raw = options.get("substitutions", {})
        if not isinstance(substitutions_raw, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in substitutions_raw.items()):
            raise DefinitionError(f"pipeline stage {index}: substitutions must be a string mapping")
        return NormalizeStage(
            lowercase=bool(options.get("lowercase", False)),
            remove_whitespace=bool(options.get("remove_whitespace", False)),
            substitutions=tuple(substitutions_raw.items()),
        )

    raise DefinitionError(f"pipeline stage {index}: unknown operation {operation!r}")


def _positive_int(value: Any, label: str, index: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise DefinitionError(f"pipeline stage {index}: {label} must be a positive integer")
    return value


def _schedule_from_dict(spec: dict[str, Any], index: int):
    schedule_type = spec.get("type")
    if schedule_type == "mask":
        _reject_unknown(spec, {"type", "values", "phase"}, "schedule", index)
        values = spec.get("values")
        if isinstance(values, str):
            if not values or any(c not in "01" for c in values):
                raise DefinitionError(f"pipeline stage {index}: mask string must contain only 0 and 1")
            parsed = tuple(int(c) for c in values)
        elif isinstance(values, list) and values and all(v in (0, 1) and not isinstance(v, bool) for v in values):
            parsed = tuple(values)
        else:
            raise DefinitionError(f"pipeline stage {index}: mask values must be a non-empty binary string or list")
        phase = spec.get("phase", 0)
        if isinstance(phase, bool) or not isinstance(phase, int) or phase < 0:
            raise DefinitionError(f"pipeline stage {index}: phase must be a nonnegative integer")
        return MaskSchedule(parsed, phase)

    if schedule_type == "alternating_blocks":
        _reject_unknown(spec, {"type", "idle_run", "significant_run", "starts_with"}, "schedule", index)
        idle_run = _positive_int(spec.get("idle_run"), "idle_run", index)
        significant_run = _positive_int(spec.get("significant_run"), "significant_run", index)
        starts_with = spec.get("starts_with", "idle")
        if starts_with not in {"idle", "significant"}:
            raise DefinitionError(f"pipeline stage {index}: starts_with must be 'idle' or 'significant'")
        return AlternatingBlockSchedule(idle_run, significant_run, starts_with)

    if schedule_type == "boundary_reset_blocks":
        _reject_unknown(
            spec,
            {
                "type", "idle_run", "significant_run", "starts_with",
                "boundary_after_selected", "reset_to_cycle_position",
            },
            "schedule",
            index,
        )
        idle_run = _positive_int(spec.get("idle_run"), "idle_run", index)
        significant_run = _positive_int(spec.get("significant_run"), "significant_run", index)
        starts_with = spec.get("starts_with", "idle")
        boundaries = spec.get("boundary_after_selected")
        if (
            not isinstance(boundaries, list)
            or not all(
                isinstance(value, int) and not isinstance(value, bool) and value > 0
                for value in boundaries
            )
        ):
            raise DefinitionError(
                f"pipeline stage {index}: boundary_after_selected must be a list of positive integers"
            )
        reset = spec.get("reset_to_cycle_position", 0)
        if isinstance(reset, bool) or not isinstance(reset, int) or reset < 0:
            raise DefinitionError(
                f"pipeline stage {index}: reset_to_cycle_position must be a nonnegative integer"
            )
        try:
            return BoundaryResetSchedule(
                idle_run,
                significant_run,
                tuple(boundaries),
                starts_with,
                reset,
            )
        except ValueError as exc:
            raise DefinitionError(f"pipeline stage {index}: {exc}") from exc

    raise DefinitionError(f"pipeline stage {index}: unsupported schedule type {schedule_type!r}")


def _reject_unknown(options: dict[str, Any], allowed: set[str], operation: str, index: int) -> None:
    unknown = set(options) - allowed
    if unknown:
        raise DefinitionError(f"pipeline stage {index}: unknown {operation} option(s): {', '.join(sorted(unknown))}")
