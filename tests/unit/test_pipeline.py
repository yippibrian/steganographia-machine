import pytest
from steg import ConcatenateStage, MaskSchedule, Pipeline, ProjectStage, SelectStage, Text, UnitSequence, UnitizeCharactersStage, UnitizeWordsStage

def test_selection_is_independent_of_unit_type():
    stage=SelectStage(MaskSchedule((1,0)))
    words,_=stage.execute(UnitSequence(("a","b","c","d"),"word"))
    chars,_=stage.execute(UnitSequence(("a","b","c","d"),"character"))
    assert words.units == chars.units == ("a","c")
    assert words.unit_type=="word" and chars.unit_type=="character"

def test_chapter1_two_level_pipeline():
    pipeline=Pipeline((UnitizeWordsStage(),SelectStage(MaskSchedule((0,1))),ConcatenateStage(),UnitizeCharactersStage(),SelectStage(MaskSchedule((0,1))),ConcatenateStage()))
    assert pipeline.execute(Text("AB cd EF gh")).value.value == "dh"

def test_projection_and_concatenation_are_separate():
    pipeline=Pipeline((UnitizeWordsStage(),ProjectStage("initial"),ConcatenateStage()))
    assert pipeline.execute(Text("Alpha beta gamma")).value.value == "Abg"

def test_invalid_order_fails():
    with pytest.raises(TypeError):
        Pipeline((UnitizeWordsStage(),UnitizeCharactersStage())).execute(Text("abc"))
