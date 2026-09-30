from pathlib import Path
from steg.compiler import compile_case
from steg.corpus import load_chapter
from steg.verifier import result_text
ROOT=Path(__file__).resolve().parents[2]
def test_sender_conjuration_recovers_expected_stream():
 c=load_chapter(ROOT/'corpus/book1/chapter01')
 x=compile_case(c,'chapter-i-sender-conjuration')
 assert result_text(x.execute()) == c.artifacts[x.case.expected_artifact].path.read_text().strip()
