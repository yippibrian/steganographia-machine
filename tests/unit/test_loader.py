import pytest
from steg import DefinitionError, Text, pipeline_from_dict

def test_new_pipeline_syntax():
    p=pipeline_from_dict({"pipeline":[{"unitize":{"unit":"word"}},{"select":{"schedule":{"type":"mask","values":"10"}}},{"project":{"part":"initial"}},{"concatenate":{}}]})
    assert p.execute(Text("Alpha beta Gamma delta")).value.value == "AG"

def test_old_tokenize_syntax_is_rejected():
    with pytest.raises(DefinitionError): pipeline_from_dict({"pipeline":[{"tokenize":{"unit":"word"}}]})

def test_old_operation_syntax_is_rejected():
    with pytest.raises(DefinitionError): pipeline_from_dict({"pipeline":[{"operation":"tokenize_words"}]})
