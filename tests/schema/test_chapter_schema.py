from pathlib import Path
from steg.corpus import load_chapter
ROOT=Path(__file__).resolve().parents[2]

def test_chapter1_methods_and_cases_load():
    c=load_chapter(ROOT/"corpus/book1/chapter01")
    assert set(c.methods)=={"alternating-words-then-characters","pamersiel-word-initials"}
    assert set(c.cases)=={"chapter-i-sender-conjuration","chapter-i-receiver-conjuration","printed-prayer-word-initials"}

def test_chapter2_uses_new_schema():
    c=load_chapter(ROOT/"corpus/book1/chapter02")
    assert "padiel-alternating-word-initials" in c.methods
    claim = c.claims["padiel-alternating-word-initials"]
    assert claim.status == "reconstructed"
    assert claim.evidence == ("ch02-alternating-initial-rule",)


def test_chapter1_named_pamersiel_rule_uses_historical_mode():
    c = load_chapter(ROOT / "corpus/book1/chapter01")
    method = c.methods["pamersiel-word-initials"]
    assert method.pipeline is None
    assert method.mode["name"] == "Pamersiel"
    assert c.claims["pamersiel-word-initials"].status == "reconstructed"
