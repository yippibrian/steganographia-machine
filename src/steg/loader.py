from __future__ import annotations
from pathlib import Path
from typing import Any
import yaml
from .pipeline import Pipeline
from .schedules import MaskSchedule
from .stages import ConcatenateStage, NormalizeStage, ProjectStage, SelectStage, UnitizeCharactersStage, UnitizeWordsStage

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
        raise DefinitionError(f"pipeline stage {index}: unsupported unit {unit!r}")

    if operation == "select":
        _reject_unknown(options, {"schedule"}, operation, index)
        schedule = options.get("schedule")
        if not isinstance(schedule, dict):
            raise DefinitionError(f"pipeline stage {index}: select requires schedule")
        return SelectStage(_schedule_from_dict(schedule, index))

    if operation == "project":
        _reject_unknown(options, {"part"}, operation, index)
        part = options.get("part")
        if part not in {"initial", "whole"}:
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


def _schedule_from_dict(spec: dict[str, Any], index: int) -> MaskSchedule:
    _reject_unknown(spec, {"type", "values", "phase"}, "schedule", index)
    if spec.get("type") != "mask":
        raise DefinitionError(f"pipeline stage {index}: only mask schedules are currently supported")
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


def _reject_unknown(options: dict[str, Any], allowed: set[str], operation: str, index: int) -> None:
    unknown = set(options) - allowed
    if unknown:
        raise DefinitionError(f"pipeline stage {index}: unknown {operation} option(s): {', '.join(sorted(unknown))}")
