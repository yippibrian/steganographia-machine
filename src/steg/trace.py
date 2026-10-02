from __future__ import annotations

from .engine.models import ExecutionResult, ProjectionDecision, SelectionDecision


def render_trace(result: ExecutionResult) -> str:
    lines: list[str] = []
    for event in result.trace:
        suffix = ""
        unit_type = event.details.get("unit_type")
        if unit_type:
            suffix = f"({unit_type})"
        lines.append(f"[{event.stage}] {event.input_type} -> {event.output_type}{suffix}")
        decisions = event.details.get("decisions")
        if not decisions:
            continue
        for decision in decisions:
            if isinstance(decision, SelectionDecision):
                mark = "yes" if decision.selected else "no"
                location = ""
                if decision.source_span is not None:
                    location = (
                        f" line={decision.source_span.line}"
                        f" col={decision.source_span.column}"
                    )
                boundary = ""
                if decision.schedule_state.get("boundary_fired"):
                    boundary = " boundary=reset"
                lines.append(
                    f"  {decision.index:>4} cycle={decision.cycle_position:<3} "
                    f"class={decision.classification:<11} selected={mark:<3} "
                    f"unit={decision.unit!r}{location}{boundary}"
                )
            elif isinstance(decision, ProjectionDecision):
                location = ""
                if decision.source_span is not None:
                    location = (
                        f" line={decision.source_span.line}"
                        f" col={decision.source_span.column}"
                    )
                lines.append(
                    f"  {decision.index:>4} {decision.unit!r} -> "
                    f"{decision.projected!r}{location}"
                )
    return "\n".join(lines)
