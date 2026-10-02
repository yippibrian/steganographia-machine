from steg import HistoricalMode, plan_encoding, validate_carrier


def test_pamersiel_encoding_plan_requires_every_word_initial():
    mode = HistoricalMode("Pamersiel", "word_initials", {"selection": "all"})
    plan = plan_encoding(mode, "CAB")
    assert [slot.required_initial for slot in plan.constraints] == ["C", "A", "B"]
    assert validate_carrier(plan, "Can All Begin").passed


def test_aseliel_style_plan_leaves_idle_slots_unconstrained():
    mode = HistoricalMode(
        "Aseliel",
        "block_word_initials",
        {"idle_run": 1, "significant_run": 2, "starts_with": "idle"},
        historical_notation="o..",
    )
    plan = plan_encoding(mode, "CODE")
    assert [(s.classification, s.required_initial) for s in plan.constraints] == [
        ("idle", None),
        ("significant", "C"),
        ("significant", "O"),
        ("idle", None),
        ("significant", "D"),
        ("significant", "E"),
    ]
    assert validate_carrier(plan, "Any Clever Oracle may Decode Easily").passed


def test_carrier_validator_reports_wrong_significant_initial():
    mode = HistoricalMode("Pamersiel", "word_initials", {"selection": "all"})
    plan = plan_encoding(mode, "CAB")
    result = validate_carrier(plan, "Can Every Begin")
    assert not result.passed
    assert "expected 'A'" in result.errors[0]
