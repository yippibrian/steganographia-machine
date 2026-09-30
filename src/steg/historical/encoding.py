from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from ..errors import DefinitionError
from .modes import HistoricalMode
from ..text.tokenization import words


@dataclass(frozen=True)
class CarrierConstraint:
    index: int
    classification: str
    required_initial: str | None


@dataclass(frozen=True)
class EncodingPlan:
    mode_name: str
    secret: str
    constraints: tuple[CarrierConstraint, ...]


@dataclass(frozen=True)
class CarrierValidation:
    passed: bool
    consumed_words: int
    errors: tuple[str, ...]


def plan_encoding(
    mode: HistoricalMode,
    secret: str,
    execution_parameters: Mapping[str, Any] | None = None,
) -> EncodingPlan:
    """Compile a secret into mechanical carrier constraints.

    This plans slots; it does not generate natural-language cover prose.
    Boundary-sensitive and reverse-traversal encoders remain explicit gaps.
    """
    if not isinstance(secret, str):
        raise TypeError("secret must be a string")
    if mode.traversal != "forward":
        raise DefinitionError(
            f"mode {mode.name}: reverse-traversal encoding is not yet supported"
        )
    if mode.modifiers:
        raise DefinitionError(
            f"mode {mode.name}: stateful encoding modifiers are not yet supported"
        )

    letters = tuple(char for char in secret if not char.isspace())
    if mode.family == "word_initials":
        constraints = tuple(
            CarrierConstraint(index, "significant", char)
            for index, char in enumerate(letters)
        )
        return EncodingPlan(mode.name, secret, constraints)

    if mode.family == "block_word_initials":
        idle_run = _positive(mode.parameters.get("idle_run"), "idle_run", mode.name)
        significant_run = _positive(
            mode.parameters.get("significant_run"), "significant_run", mode.name
        )
        starts_with = mode.parameters.get("starts_with", "idle")
        if starts_with not in {"idle", "significant"}:
            raise DefinitionError(
                f"mode {mode.name}: starts_with must be 'idle' or 'significant'"
            )
        pattern = (
            ("idle",) * idle_run + ("significant",) * significant_run
            if starts_with == "idle"
            else ("significant",) * significant_run + ("idle",) * idle_run
        )
        constraints: list[CarrierConstraint] = []
        secret_index = 0
        carrier_index = 0
        while secret_index < len(letters):
            classification = pattern[carrier_index % len(pattern)]
            required = None
            if classification == "significant":
                required = letters[secret_index]
                secret_index += 1
            constraints.append(
                CarrierConstraint(carrier_index, classification, required)
            )
            carrier_index += 1
        return EncodingPlan(mode.name, secret, tuple(constraints))

    raise DefinitionError(
        f"mode {mode.name}: encoding planner does not support family {mode.family!r}"
    )


def validate_carrier(plan: EncodingPlan, carrier: str) -> CarrierValidation:
    """Check whether a candidate carrier satisfies an encoding plan."""
    carrier_words = words(carrier)
    errors: list[str] = []
    if len(carrier_words) < len(plan.constraints):
        errors.append(
            f"carrier has {len(carrier_words)} words but plan requires at least "
            f"{len(plan.constraints)}"
        )
    for constraint in plan.constraints:
        if constraint.index >= len(carrier_words):
            break
        if constraint.required_initial is None:
            continue
        actual = carrier_words[constraint.index][0]
        if actual.casefold() != constraint.required_initial.casefold():
            errors.append(
                f"word {constraint.index + 1} begins with {actual!r}; "
                f"expected {constraint.required_initial!r}"
            )
    return CarrierValidation(not errors, min(len(carrier_words), len(plan.constraints)), tuple(errors))


def _positive(value: Any, label: str, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise DefinitionError(f"mode {name}: {label} must be a positive integer")
    return value
