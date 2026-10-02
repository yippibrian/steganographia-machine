# Steganographia Machine 0.9.0

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


## Historical mode grammar

Version 0.9 adds a historical-mode layer above the linear execution kernel. Named modes can now preserve semantic parameters such as idle/significant run lengths and starting order, then compile to ordinary pipeline stages. Existing direct pipelines remain supported.

Padiel is the first corpus method migrated to this representation. Selection traces now identify units as `idle` or `significant` and include semantic schedule state.

See `docs/HISTORICAL_MODE_ARCHITECTURE.md` for the architecture and the explicit boundary around later stateful deviation modes.


## Executable critical-edition direction

The corpus now preserves more than decoded strings. Units can retain source coordinates; historical modes can preserve printed o/. notation; traversal is explicit; case-specific boundary evidence is separated from reusable mode rules; artifacts can record derivation metadata; and claims/hypotheses are represented separately from executable semantics.

A partial 67-mode catalogue lives in `corpus/mode_registry.yaml`. It is deliberately incomplete where the available transcription is uncertain.

The design rule is that expected plaintext is verification data, never hidden decoder input.


### Internal architecture

The implementation is split by dependency direction rather than by historical chapter:

- `steg.text` — source coordinates and canonical tokenization
- `steg.engine` — generic execution kernel
- `steg.historical` — historical mode semantics and construction constraints
- `steg.corpus` — documentary evidence and corpus records
- `steg.compiler` — binds corpus cases to executable methods

A static test prevents lower-level subsystems from importing higher-level ones. The top-level `steg` module remains the stable convenience API.
