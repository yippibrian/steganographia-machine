from dataclasses import replace
from pathlib import Path

import pytest

from steg import DefinitionError
from steg.compiler import compile_case
from steg.corpus import CipherCase, MethodDefinition, load_chapter


ROOT = Path(__file__).resolve().parents[2]


def test_case_execution_evidence_is_not_reused_for_an_overridden_artifact():
    chapter = load_chapter(ROOT / "corpus/book1/chapter02")
    artifact_ids = tuple(chapter.artifacts)
    assert len(artifact_ids) >= 2

    method = MethodDefinition(
        id="stateful-test",
        title="Stateful test mode",
        pipeline=None,
        mode={
            "name": "Stateful test",
            "family": "block_word_initials",
            "historical_notation": "o..",
            "parameters": {
                "idle_run": 1,
                "significant_run": 2,
                "starts_with": "idle",
            },
            "modifiers": [{"type": "boundary_reset"}],
        },
        evidence=(),
        notes=(),
    )
    case = CipherCase(
        id="stateful-test-case",
        title="Stateful test case",
        method_id=method.id,
        input_artifact=artifact_ids[0],
        expected_artifact=None,
        reading_artifact=None,
        status="unverified",
        evidence=(),
        notes=(),
        execution={"boundary_after_selected": [1]},
    )
    chapter = replace(
        chapter,
        methods={**chapter.methods, method.id: method},
        cases={**chapter.cases, case.id: case},
    )

    # The configured case has the evidence required to compile.
    compile_case(chapter, case.id)

    # Changing the carrier invalidates those recorded boundary positions.
    with pytest.raises(DefinitionError, match="case parameter"):
        compile_case(chapter, case.id, input_artifact_id=artifact_ids[1])

    # A caller may explicitly supply replacement execution evidence.
    compile_case(
        chapter,
        case.id,
        input_artifact_id=artifact_ids[1],
        execution_parameters={"boundary_after_selected": [1]},
    )
