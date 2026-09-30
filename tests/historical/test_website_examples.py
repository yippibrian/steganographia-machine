from pathlib import Path
from steg.compiler import compile_case
from steg.corpus import load_chapter
from steg.verifier import result_text

ROOT = Path(__file__).resolve().parents[2]

def check(chapter_name, case_id):
    chapter=load_chapter(ROOT/'corpus'/'book1'/chapter_name)
    compiled=compile_case(chapter,case_id)
    actual=result_text(compiled.execute())
    expected=chapter.artifacts[compiled.case.expected_artifact].path.read_text(encoding='utf-8').strip()
    assert actual == expected

def test_all_documented_examples():
    for chapter, case in [
      ('chapter01','chapter-i-sender-conjuration'),
      ('chapter01','chapter-i-receiver-conjuration'),
      ('chapter02','chapter-ii-sender-conjuration'),
      ('chapter02','chapter-ii-receiver-conjuration'),
      ('chapter02','chapter-ii-first-prayer'),
      ('chapter02','chapter-ii-second-prayer'),
    ]:
        check(chapter,case)
