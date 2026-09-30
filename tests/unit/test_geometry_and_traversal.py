from steg import Text, pipeline_from_dict


def test_word_unitization_retains_source_coordinates_through_projection():
    pipeline = pipeline_from_dict(
        {
            "pipeline": [
                {"unitize": {"unit": "word"}},
                {"project": {"part": "initial"}},
            ]
        }
    )
    result = pipeline.execute(Text("Alpha beta\nGamma"))
    assert result.value.units == ("A", "b", "G")
    assert [(s.line, s.column) for s in result.value.spans] == [(1, 1), (1, 7), (2, 1)]


def test_reverse_traversal_is_first_class_and_preserves_spans():
    pipeline = pipeline_from_dict(
        {
            "pipeline": [
                {"unitize": {"unit": "word"}},
                {"traverse": {"direction": "reverse"}},
                {"project": {"part": "initial"}},
                {"concatenate": {}},
            ]
        }
    )
    result = pipeline.execute(Text("Alpha beta Gamma"))
    assert result.value.value == "GbA"
    traverse = result.trace[1]
    assert traverse.details["direction"] == "reverse"


def test_final_letter_projection():
    pipeline = pipeline_from_dict(
        {
            "pipeline": [
                {"unitize": {"unit": "word"}},
                {"project": {"part": "final"}},
                {"concatenate": {}},
            ]
        }
    )
    assert pipeline.execute(Text("Alpha beta Gamma")).value.value == "aaa"


def test_line_unitization_retains_line_geometry():
    pipeline = pipeline_from_dict({"pipeline": [{"unitize": {"unit": "line"}}]})
    result = pipeline.execute(Text("first line\nsecond line\n"))
    assert result.value.units == ("first line", "second line")
    assert [span.line for span in result.value.spans] == [1, 2]


def test_geometry_survives_concatenate_and_character_reunitization():
    pipeline = pipeline_from_dict(
        {
            "pipeline": [
                {"unitize": {"unit": "word"}},
                {"select": {"schedule": {"type": "mask", "values": "01"}}},
                {"concatenate": {}},
                {"unitize": {"unit": "character"}},
            ]
        }
    )
    result = pipeline.execute(Text("Alpha beta\nGamma delta"))
    assert result.value.units == tuple("betadelta")
    # Characters inherited from beta point to its original word; delta points
    # to the second line rather than to positions in the emitted stream.
    assert result.value.spans[0].line == 1
    assert result.value.spans[-1].line == 2
