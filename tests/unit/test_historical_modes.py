import pytest

from steg import (
    AlternatingBlockSchedule,
    BoundaryResetSchedule,
    DefinitionError,
    SelectStage,
    Text,
    UnitSequence,
    compile_historical_mode,
    generate_simple_block_space,
    pipeline_from_dict,
)
from steg.compiler import compile_method
from steg.corpus import load_chapter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_camuel_and_padiel_are_opposite_block_phases():
    camuel = AlternatingBlockSchedule(1, 1, "idle")
    padiel = AlternatingBlockSchedule(1, 1, "significant")
    assert camuel.mask == (0, 1)
    assert padiel.mask == (1, 0)


def test_aseliel_and_gediel_are_semantic_block_schedules():
    assert AlternatingBlockSchedule(1, 2, "idle").mask == (0, 1, 1)
    assert AlternatingBlockSchedule(2, 2, "idle").mask == (0, 0, 1, 1)


def test_semantic_block_schedule_executes_without_literal_mask():
    pipeline = pipeline_from_dict(
        {
            "pipeline": [
                {"unitize": {"unit": "word"}},
                {
                    "select": {
                        "schedule": {
                            "type": "alternating_blocks",
                            "idle_run": 2,
                            "significant_run": 2,
                            "starts_with": "idle",
                        }
                    }
                },
                {"project": {"part": "initial"}},
                {"concatenate": {}},
            ]
        }
    )
    assert pipeline.execute(Text("a b Charlie Delta e f Golf Hotel")).value.value == "CDGH"


def test_trace_records_semantic_classification_and_schedule_state():
    _, event = SelectStage(AlternatingBlockSchedule(1, 2, "idle")).execute(
        UnitSequence(("a", "b", "c", "d"), "word")
    )
    assert [decision.classification for decision in event.details["decisions"]] == [
        "idle",
        "significant",
        "significant",
        "idle",
    ]
    assert event.details["decisions"][1].schedule_state["family"] == "alternating_blocks"


def test_historical_mode_compiles_to_linear_kernel():
    compiled = compile_historical_mode(
        {
            "name": "Gediel",
            "family": "block_word_initials",
            "parameters": {
                "idle_run": 2,
                "significant_run": 2,
                "starts_with": "idle",
            },
        }
    )
    assert compiled.pipeline.execute(Text("a b Charlie Delta e f Golf Hotel")).value.value == "CDGH"
    assert compiled.compiled_pipeline[1]["select"]["schedule"]["type"] == "alternating_blocks"


def test_padiel_corpus_method_uses_historical_mode_and_still_compiles():
    chapter = load_chapter(ROOT / "corpus/book1/chapter02")
    method = chapter.methods["padiel-alternating-word-initials"]
    assert method.pipeline is None
    assert method.mode["name"] == "Padiel"
    compiled = compile_method(chapter, method.id)
    assert compiled.historical_mode is not None
    assert compiled.historical_mode.mode.parameters["starts_with"] == "significant"


def test_boundary_deviations_require_explicit_case_evidence():
    spec = {
        "name": "Boundary-sensitive example",
        "family": "block_word_initials",
        "historical_notation": "o..",
        "parameters": {
            "idle_run": 1,
            "significant_run": 2,
            "starts_with": "idle",
        },
        "modifiers": [{"type": "boundary_reset"}],
    }
    with pytest.raises(DefinitionError, match="case parameter"):
        compile_historical_mode(spec)

    compiled = compile_historical_mode(
        spec,
        {"boundary_after_selected": [1]},
    )
    assert (
        compiled.compiled_pipeline[1]["select"]["schedule"]["type"]
        == "boundary_reset_blocks"
    )


def test_simple_block_space_has_two_orders_five_idle_columns_by_six_significant_rows():
    space = generate_simple_block_space()
    coordinates = {
        (
            mode.parameters["starts_with"],
            mode.parameters["idle_run"],
            mode.parameters["significant_run"],
        )
        for mode in space
    }
    assert len(space) == 60
    assert len(coordinates) == 60
    assert {mode.parameters["idle_run"] for mode in space} == {1, 2, 3, 4, 5}
    assert {mode.parameters["significant_run"] for mode in space} == {1, 2, 3, 4, 5, 6}


def test_generated_table_preserves_known_selenus_coordinates():
    space = {
        (
            mode.parameters["starts_with"],
            mode.parameters["idle_run"],
            mode.parameters["significant_run"],
        ): mode
        for mode in generate_simple_block_space()
    }
    assert space[("idle", 1, 2)].historical_notation == "o.."
    assert space[("idle", 2, 2)].historical_notation == "oo.."
    assert space[("idle", 5, 5)].historical_notation == "ooooo....."
    assert space[("significant", 1, 1)].historical_notation == ".o"


def test_historical_notation_must_match_semantic_parameters():
    with pytest.raises(DefinitionError, match="does not match semantic parameters"):
        compile_historical_mode(
            {
                "name": "Bad-Aseliel",
                "family": "block_word_initials",
                "historical_notation": "oo.",
                "parameters": {
                    "idle_run": 1,
                    "significant_run": 2,
                    "starts_with": "idle",
                },
            }
        )


def test_explicit_boundaries_can_reset_a_block_schedule_without_plaintext_inference():
    schedule = BoundaryResetSchedule(
        idle_run=1,
        significant_run=2,
        boundary_after_selected=(1,),
        starts_with="idle",
    )
    decisions = [schedule.decision(i) for i in range(6)]
    assert [d.classification for d in decisions] == [
        "idle", "significant", "idle", "significant", "significant", "idle"
    ]
    assert decisions[1].state["boundary_fired"] is True
