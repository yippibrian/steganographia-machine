from pathlib import Path

from steg.corpus import load_mode_registry

ROOT = Path(__file__).resolve().parents[2]


def test_mode_registry_records_catalogue_without_claiming_all_modes_are_understood():
    registry = load_mode_registry(ROOT / "corpus/mode_registry.yaml")
    assert registry.expected_catalogue_size == 67
    assert registry.entries["b1-c04-m02"].historical_notation == ".o"
    assert registry.entries["b1-c04-m02"].implementation_status == "verified"
    assert registry.entries["b1-c07-m01"].implementation_status == "requires_stateful_rules"
    assert len(registry.entries) < registry.expected_catalogue_size


def test_mode_registry_identity_is_not_the_historical_name():
    registry = load_mode_registry(ROOT / "corpus/mode_registry.yaml")
    padiel = registry.named("Padiel")
    assert len(padiel) == 1
    assert padiel[0].id == "b1-c04-m02"
