from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Protocol

from .models import (
    EmittedStream,
    PipelineValue,
    ProjectionDecision,
    SelectionDecision,
    Text,
    TraceEvent,
    UnitSequence,
)
from .schedules import Schedule


class Stage(Protocol):
    name: str

    def execute(self, value: PipelineValue) -> tuple[PipelineValue, TraceEvent]: ...


@dataclass(frozen=True)
class UnitizeWordsStage:
    name: str = "unitize_words"

    def execute(self, value: PipelineValue) -> tuple[PipelineValue, TraceEvent]:
        if not isinstance(value, Text):
            raise TypeError("UnitizeWordsStage requires Text input")
        units = tuple(re.findall(r"\b[^\W\d_]+(?:['’-][^\W\d_]+)*\b", value.value, re.UNICODE))
        output = UnitSequence(units=units, unit_type="word")
        return output, TraceEvent(self.name, type(value).__name__, type(output).__name__, {"unit_type": "word", "units": units})


@dataclass(frozen=True)
class UnitizeCharactersStage:
    include_whitespace: bool = False
    name: str = "unitize_characters"

    def execute(self, value: PipelineValue) -> tuple[PipelineValue, TraceEvent]:
        if isinstance(value, Text):
            raw = value.value
        elif isinstance(value, EmittedStream):
            raw = value.value
        else:
            raise TypeError("UnitizeCharactersStage requires Text or EmittedStream input")
        units = tuple(raw if self.include_whitespace else (c for c in raw if not c.isspace()))
        output = UnitSequence(units=units, unit_type="character")
        return output, TraceEvent(self.name, type(value).__name__, type(output).__name__, {"unit_type": "character", "units": units})


@dataclass(frozen=True)
class SelectStage:
    schedule: Schedule
    name: str = "select"

    def execute(self, value: PipelineValue) -> tuple[PipelineValue, TraceEvent]:
        if not isinstance(value, UnitSequence):
            raise TypeError("SelectStage requires UnitSequence input")
        decisions = []
        for index, unit in enumerate(value.units):
            schedule_decision = self.schedule.decision(index)
            decisions.append(
                SelectionDecision(
                    index=index,
                    unit=unit,
                    cycle_position=schedule_decision.cycle_position,
                    selected=schedule_decision.selected,
                    classification=schedule_decision.classification,
                    schedule_state=schedule_decision.state,
                )
            )
        decisions_tuple = tuple(decisions)
        selected = tuple(decision.unit for decision in decisions_tuple if decision.selected)
        output = UnitSequence(units=selected, unit_type=value.unit_type)
        return output, TraceEvent(
            self.name,
            type(value).__name__,
            type(output).__name__,
            {
                "unit_type": value.unit_type,
                "mask": self.schedule.mask,
                "decisions": decisions_tuple,
                "selected": selected,
            },
        )


@dataclass(frozen=True)
class ProjectStage:
    part: str
    name: str = "project"

    def execute(self, value: PipelineValue) -> tuple[PipelineValue, TraceEvent]:
        if not isinstance(value, UnitSequence):
            raise TypeError("ProjectStage requires UnitSequence input")
        if self.part == "initial":
            pairs = tuple((unit, unit[0]) for unit in value.units if unit)
            output_type = "character"
        elif self.part == "whole":
            pairs = tuple((unit, unit) for unit in value.units)
            output_type = value.unit_type
        else:
            raise ValueError(f"unsupported projection part: {self.part}")
        projected = tuple(result for _, result in pairs)
        decisions = tuple(ProjectionDecision(i, unit, result) for i, (unit, result) in enumerate(pairs))
        output = UnitSequence(units=projected, unit_type=output_type)
        return output, TraceEvent(
            self.name,
            type(value).__name__,
            type(output).__name__,
            {"part": self.part, "decisions": decisions, "projected": projected},
        )


@dataclass(frozen=True)
class ConcatenateStage:
    separator: str = ""
    name: str = "concatenate"

    def execute(self, value: PipelineValue) -> tuple[PipelineValue, TraceEvent]:
        if not isinstance(value, UnitSequence):
            raise TypeError("ConcatenateStage requires UnitSequence input")
        joined = self.separator.join(value.units)
        output = EmittedStream(joined)
        return output, TraceEvent(self.name, type(value).__name__, type(output).__name__, {"separator": self.separator, "value": joined})


@dataclass(frozen=True)
class NormalizeStage:
    lowercase: bool = False
    remove_whitespace: bool = False
    substitutions: tuple[tuple[str, str], ...] = ()
    name: str = "normalize"

    def execute(self, value: PipelineValue) -> tuple[PipelineValue, TraceEvent]:
        if isinstance(value, Text):
            normalized = value.value
        elif isinstance(value, EmittedStream):
            normalized = value.value
        else:
            raise TypeError("NormalizeStage requires Text or EmittedStream input")
        if self.lowercase:
            normalized = normalized.lower()
        for old, new in self.substitutions:
            normalized = normalized.replace(old, new)
        if self.remove_whitespace:
            normalized = "".join(normalized.split())
        output = EmittedStream(normalized)
        return output, TraceEvent(self.name, type(value).__name__, type(output).__name__, {"value": normalized})
