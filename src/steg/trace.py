from __future__ import annotations

from .models import ExecutionResult, ProjectionDecision, SelectionDecision


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
                lines.append(
                    f"  {decision.index:>4} cycle={decision.cycle_position:<3} "
                    f"selected={mark:<3} unit={decision.unit!r}"
                )
            elif isinstance(decision, ProjectionDecision):
                lines.append(
                    f"  {decision.index:>4} {decision.unit!r} -> {decision.projected!r}"
                )
    return "\n".join(lines)
