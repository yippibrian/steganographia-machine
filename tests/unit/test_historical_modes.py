import pytest

from steg import (
    AlternatingBlockSchedule,
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


def test_boundary_deviations_are_not_silently_approximated():
    with pytest.raises(DefinitionError, match="stateful modifier execution"):
        compile_historical_mode(
            {
                "name": "Barmiel",
                "family": "block_word_initials",
                "parameters": {
                    "idle_run": 1,
                    "significant_run": 2,
                    "starts_with": "idle",
                },
                "modifiers": [{"type": "hidden_word_boundary_deviation"}],
            }
        )


def test_simple_block_space_has_two_orders_five_by_six():
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
