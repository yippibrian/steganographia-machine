# Steganographia Machine 0.8.1

This release packages the Chapter I and Chapter II examples displayed at
`https://trithemius.com/steganographia-english/`.

The project keeps two kinds of source artifact:

- diplomatic transcriptions, retained for later comparison and textual experiments;
- `website-normalized` fixtures, which reproduce the interlinear readings shown on the website.

The normalized fixtures are deliberately explicit test fixtures, not claims that every surviving edition has identical spacing or spelling. Later editions or manuscript variants can be added as additional artifacts and cases.

## Run all documented examples

```bash
python3 run_tests.py
python3 run_chapter.py chapter01
python3 run_chapter.py chapter02
```

## Individual examples

```bash
python3 run_chapter.py chapter01 --case chapter-i-sender-conjuration --trace
python3 run_chapter.py chapter01 --case chapter-i-receiver-conjuration --trace
python3 run_chapter.py chapter02 --case chapter-ii-sender-conjuration --trace
python3 run_chapter.py chapter02 --case chapter-ii-receiver-conjuration --trace
python3 run_chapter.py chapter02 --case chapter-ii-first-prayer --trace
python3 run_chapter.py chapter02 --case chapter-ii-second-prayer --trace
```

`output:` is the compact machine extraction used for verification. `reading:` is the spaced reading displayed on the website.

The long Chapter I carrier prayer remains an unverified experiment because the website explicitly notes that its hidden example has not been identified.
