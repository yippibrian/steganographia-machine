from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Protocol

from .models import (
    EmittedStream,
    PipelineValue,
    ProjectionDecision,
    SelectionDecision,
    SourceSpan,
    Text,
    TraceEvent,
    UnitSequence,
)
from .schedules import Schedule


class Stage(Protocol):
    name: str

    def execute(self, value: PipelineValue) -> tuple[PipelineValue, TraceEvent]: ...


def _span(text: str, start: int, end: int) -> SourceSpan:
    line = text.count("\n", 0, start) + 1
    last_newline = text.rfind("\n", 0, start)
    column = start - last_newline
    end_line = text.count("\n", 0, end) + 1
    end_last_newline = text.rfind("\n", 0, end)
    end_column = end - end_last_newline
    return SourceSpan(start, end, line, column, end_line, end_column)


@dataclass(frozen=True)
class UnitizeWordsStage:
    name: str = "unitize_words"

    def execute(self, value: PipelineValue) -> tuple[PipelineValue, TraceEvent]:
        if not isinstance(value, Text):
            raise TypeError("UnitizeWordsStage requires Text input")
        matches = tuple(re.finditer(r"\b[^\W\d_]+(?:['’-][^\W\d_]+)*\b", value.value, re.UNICODE))
        units = tuple(match.group(0) for match in matches)
        spans = tuple(_span(value.value, match.start(), match.end()) for match in matches)
        output = UnitSequence(units=units, unit_type="word", spans=spans)
        return output, TraceEvent(
            self.name,
            type(value).__name__,
            type(output).__name__,
            {"unit_type": "word", "units": units, "spans": spans},
        )


@dataclass(frozen=True)
class UnitizeLinesStage:
    name: str = "unitize_lines"

    def execute(self, value: PipelineValue) -> tuple[PipelineValue, TraceEvent]:
        if not isinstance(value, Text):
            raise TypeError("UnitizeLinesStage requires Text input")
        raw_lines = value.value.splitlines(keepends=True)
        if not raw_lines and value.value == "":
            raw_lines = [""]
        units: list[str] = []
        spans: list[SourceSpan] = []
        offset = 0
        for raw in raw_lines:
            unit = raw.rstrip("\r\n")
            units.append(unit)
            spans.append(_span(value.value, offset, offset + len(unit)))
            offset += len(raw)
        output = UnitSequence(tuple(units), "line", tuple(spans))
        return output, TraceEvent(
            self.name,
            type(value).__name__,
            type(output).__name__,
            {"unit_type": "line", "units": tuple(units), "spans": tuple(spans)},
        )


@dataclass(frozen=True)
class UnitizeCharactersStage:
    include_whitespace: bool = False
    name: str = "unitize_characters"

    def execute(self, value: PipelineValue) -> tuple[PipelineValue, TraceEvent]:
        inherited_spans: tuple[SourceSpan | None, ...] = ()
        if isinstance(value, Text):
            raw = value.value
        elif isinstance(value, EmittedStream):
            raw = value.value
            inherited_spans = value.spans
        else:
            raise TypeError("UnitizeCharactersStage requires Text or EmittedStream input")
        indexed = tuple(
            (index, char)
            for index, char in enumerate(raw)
            if self.include_whitespace or not char.isspace()
        )
        units = tuple(char for _, char in indexed)
        spans = (
            tuple(inherited_spans[index] for index, _ in indexed)
            if inherited_spans
            else tuple(_span(raw, index, index + 1) for index, _ in indexed)
        )
        output = UnitSequence(units=units, unit_type="character", spans=spans)
        return output, TraceEvent(
            self.name,
            type(value).__name__,
            type(output).__name__,
            {"unit_type": "character", "units": units, "spans": spans},
        )


@dataclass(frozen=True)
class TraverseStage:
    direction: str = "forward"
    name: str = "traverse"

    def execute(self, value: PipelineValue) -> tuple[PipelineValue, TraceEvent]:
        if not isinstance(value, UnitSequence):
            raise TypeError("TraverseStage requires UnitSequence input")
        if self.direction not in {"forward", "reverse"}:
            raise ValueError(f"unsupported traversal direction: {self.direction}")
        if self.direction == "forward":
            output = value
        else:
            output = UnitSequence(
                tuple(reversed(value.units)),
                value.unit_type,
                tuple(reversed(value.spans)) if value.spans else (),
            )
        return output, TraceEvent(
            self.name,
            type(value).__name__,
            type(output).__name__,
            {"direction": self.direction, "unit_type": value.unit_type},
        )


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
                    source_span=value.spans[index] if value.spans else None,
                )
            )
        decisions_tuple = tuple(decisions)
        selected_indices = tuple(d.index for d in decisions_tuple if d.selected)
        selected = tuple(value.units[index] for index in selected_indices)
        selected_spans = (
            tuple(value.spans[index] for index in selected_indices)
            if value.spans
            else ()
        )
        output = UnitSequence(selected, value.unit_type, selected_spans)
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
        elif self.part == "final":
            pairs = tuple((unit, unit[-1]) for unit in value.units if unit)
            output_type = "character"
        elif self.part == "whole":
            pairs = tuple((unit, unit) for unit in value.units)
            output_type = value.unit_type
        else:
            raise ValueError(f"unsupported projection part: {self.part}")
        projected = tuple(result for _, result in pairs)
        # Empty units are skipped by initial/final projection. Line unitization can
        # create empty units, so align spans by walking the original units.
        source_indices = tuple(
            i for i, unit in enumerate(value.units)
            if self.part == "whole" or bool(unit)
        )
        projected_spans = (
            tuple(value.spans[i] for i in source_indices)
            if value.spans
            else ()
        )
        decisions = tuple(
            ProjectionDecision(
                i,
                unit,
                result,
                projected_spans[i] if projected_spans else None,
            )
            for i, (unit, result) in enumerate(pairs)
        )
        output = UnitSequence(projected, output_type, projected_spans)
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
        emitted_spans: tuple[SourceSpan | None, ...] = ()
        if value.spans:
            span_buffer: list[SourceSpan | None] = []
            for index, unit in enumerate(value.units):
                if index:
                    span_buffer.extend([None] * len(self.separator))
                span_buffer.extend([value.spans[index]] * len(unit))
            emitted_spans = tuple(span_buffer)
        output = EmittedStream(joined, emitted_spans)
        return output, TraceEvent(
            self.name,
            type(value).__name__,
            type(output).__name__,
            {"separator": self.separator, "value": joined},
        )


@dataclass(frozen=True)
class NormalizeStage:
    lowercase: bool = False
    remove_whitespace: bool = False
    substitutions: tuple[tuple[str, str], ...] = ()
    name: str = "normalize"

    def execute(self, value: PipelineValue) -> tuple[PipelineValue, TraceEvent]:
        inherited_spans: tuple[SourceSpan | None, ...] = ()
        if isinstance(value, Text):
            normalized = value.value
        elif isinstance(value, EmittedStream):
            normalized = value.value
            inherited_spans = value.spans
        else:
            raise TypeError("NormalizeStage requires Text or EmittedStream input")
        if self.lowercase:
            lowered = normalized.lower()
            if inherited_spans and len(lowered) != len(normalized):
                inherited_spans = ()
            normalized = lowered
        if self.substitutions:
            # Arbitrary substitutions can change string length. Until a
            # character-level edit map exists, do not fabricate coordinates.
            for old, new in self.substitutions:
                normalized = normalized.replace(old, new)
            inherited_spans = ()
        if self.remove_whitespace:
            if inherited_spans:
                kept = tuple(
                    (char, span)
                    for char, span in zip(normalized, inherited_spans)
                    if not char.isspace()
                )
                normalized = "".join(char for char, _ in kept)
                inherited_spans = tuple(span for _, span in kept)
            else:
                normalized = "".join(normalized.split())
        output = EmittedStream(normalized, inherited_spans)
        return output, TraceEvent(
            self.name,
            type(value).__name__,
            type(output).__name__,
            {"value": normalized},
        )
