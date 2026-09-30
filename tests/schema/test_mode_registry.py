from pathlib import Path

from steg.corpus import load_mode_registry

ROOT = Path(__file__).resolve().parents[2]


def test_mode_registry_records_catalogue_without_claiming_all_modes_are_understood():
    registry = load_mode_registry(ROOT / "corpus/mode_registry.yaml")
    assert registry.expected_catalogue_size == 67
    assert registry.entries["Padiel"].historical_notation == ".o"
    assert registry.entries["Padiel"].implementation_status == "verified"
    assert registry.entries["Barmiel"].implementation_status == "requires_stateful_rules"
    assert len(registry.entries) < registry.expected_catalogue_size
