<!--
AI CHAPTER-AUTHORING INSTRUCTIONS

When this specification is supplied together with the text of a new chapter
of Johannes Trithemius's Steganographia, use the chapter text and any documented
decipherments to construct a complete executable chapter package.

The goal is to add the chapter primarily through YAML configuration and text
artifacts. Do not add chapter-specific Python code unless the chapter requires
a genuinely new reusable computational operation that cannot be expressed by
the existing pipeline language.

Work in this order:

1. Inventory the chapter's protocol, conjurations, carrier texts, stated secrets,
   documented extractions, unresolved examples, and textual variants.
2. Preserve source texts as separate artifacts. Do not silently alter a
   diplomatic transcription to force a decoding.
3. When a documented decoding depends on a normalized or reconstructed version
   of a text, preserve that version as a separate artifact and describe its
   provenance and normalization in metadata or notes.
4. Represent each reusable decoding procedure as one method YAML file.
5. Represent each application of a method to a particular input artifact as one
   case YAML file.
6. Reuse one method across multiple cases when the operation is the same.
7. Add an expected artifact only when a specific extraction is documented or
   intentionally proposed as a reproducible test.
8. Add a reading artifact when human-readable spacing, punctuation, uncertainty
   marks, or editorial presentation differs from the compact machine output.
9. Mark unresolved examples unverified. Never invent a plaintext merely to make
   a case pass.
10. Add tests proving that the chapter loads and that every documented verified
    case reproduces its expected output.
11. Run chapter validation, chapter execution, and the complete test suite before
    treating the package as complete.

Keep these layers separate:

- historical protocol: what the chapter says the operator should do;
- evidence: where a claim or method comes from;
- artifact: a particular source, transcription, normalization, or expected text;
- method: a reusable computational transformation;
- case: one historically or experimentally meaningful use of a method on an artifact;
- verification: whether the actual compact output exactly matches the configured
  expected artifact.
-->

# Steganographia Machine Chapter Package and Authoring Specification

**Status:** Working specification  
**Specification version:** 0.3  
**Implementation target:** `steganographia-machine-v0.9.0`  
**Compatibility:** Breaking replacement for specification version 0.1  
**Scope:** Chapter packages, artifacts, evidence, methods, cases, pipelines, validation, and chapter authoring

## 1. Purpose

This document specifies the configuration format used to represent chapters of Johannes Trithemius's *Steganographia* as executable chapter packages.

A chapter package combines:

- a structured description of the historical protocol;
- evidence supporting protocol and decoding claims;
- textual artifacts, including source variants and normalized fixtures;
- one or more reusable decoding methods;
- one or more cases applying those methods to particular artifacts;
- expected compact outputs and optional human-readable renderings;
- tests showing that documented decipherments can be reproduced.

The principal design goal is:

> A new chapter that uses existing execution primitives should be implementable through configuration and text artifacts without chapter-specific Python code.

The central modeling distinction is:

> A method describes a reusable transformation. A case describes one application of that method to a particular artifact.

This separation allows:

- several ciphers or methods to coexist in one chapter;
- one method to support several examples;
- one historical text to be tested under several methods;
- several editions or normalized variants of the same text to coexist;
- documented, exploratory, falsified, blocked, and unresolved cases to remain reproducible;
- the engine to distinguish software correctness from historical certainty.

## 2. Normative Language

The terms **MUST**, **MUST NOT**, **REQUIRED**, **SHOULD**, **SHOULD NOT**, and **MAY** are used as normative requirements.

Requirements explicitly described as implementation behavior reflect version 0.9.0. Recommendations marked as authoring guidance may be stricter than the current loader.

## 3. Package Layout

A chapter package SHOULD use this layout:

    corpus/
    └── book1/
        └── chapterNN/
            ├── chapter.yaml
            ├── README.md
            ├── methods/
            │   ├── method-one.yaml
            │   └── method-two.yaml
            ├── cases/
            │   ├── example-one.yaml
            │   └── example-two.yaml
            └── sources/
                ├── source-one.txt
                ├── normalized-source-one.txt
                ├── expected-one.txt
                └── reading-one.txt

The directory names `methods`, `cases`, and `sources` are conventions. The loader follows the paths listed in `chapter.yaml`.

All paths declared in a chapter package MUST be relative to the chapter package root.

Version 0.9.0's `run_chapter.py` resolves chapter arguments beneath:

    corpus/book1/

Therefore this command:

    python3 run_chapter.py chapter03

loads:

    corpus/book1/chapter03/chapter.yaml

Additional Book I chapters can use the existing CLI. Selecting another book is not yet exposed by `run_chapter.py` and would require a small general CLI change.

## 4. Conceptual Model

### 4.1 Chapter

A chapter records historical metadata, protocol claims, evidence, artifacts, available methods, and executable cases.

### 4.2 Artifact

An artifact is a named text file used as:

- a diplomatic source;
- a normalized source variant;
- a reconstructed test fixture;
- a carrier text;
- a separately stated secret;
- an expected compact extraction;
- a human-readable rendering;
- another historically or computationally relevant text.

Artifacts are immutable inputs from the perspective of execution. A pipeline does not modify the artifact file.

### 4.3 Evidence

An evidence record links a claim to a source, quotation, and confidence description.

Evidence may support:

- protocol fields;
- a decoding method;
- a case;
- a transcription or normalization decision.

### 4.4 Method

A method is a reusable transformation. It contains no fixed input or expected output and is defined either by a direct pipeline or by a historical mode that compiles to a pipeline.

Examples include:

- take alternating words, then alternating characters;
- take the initial of every word;
- take initials of alternating words.

One method SHOULD be reused for every case that performs the same operation.

### 4.5 Case

A case applies one method to one input artifact. It may also identify:

- an expected compact output;
- a separately formatted reading;
- evidence;
- notes;
- a status;
- case-specific `execution` parameters required by an explicitly stateful historical rule.

A case is the unit executed by `run_chapter.py`.

### 4.6 Verification

Verification compares the exact compact output produced by a case with the exact contents of its expected artifact after removing only the final line ending.

Verification does not establish that a historical interpretation is uniquely correct. It establishes that the configured method and input reproduce the configured expected stream.

## 5. Chapter Manifest

Every chapter package MUST contain `chapter.yaml`.

The file MUST contain a YAML mapping.

### 5.1 Required Top-Level Fields

The following fields are REQUIRED by the version 0.9.0 loader:

    id:
    book:
    chapter:
    title:
    principal:
    protocol:
    provenance:
    artifacts:
    evidence:
    methods:
    cases:

A structural example is:

    id: book1.chapter03
    book: 1
    chapter: 3
    title: Example Chapter
    principal: Example Principal

    protocol:
      address: {}
      authority: {}
      sign: {}
      availability: {}
      message_domain: []
      sender: {}
      recipient: {}
      carrier: {}

    provenance: {}
    artifacts: []
    evidence: []
    methods: []
    cases: []

This example shows shape only. It does not satisfy the complete validation requirements.

### 5.2 Identity Fields

#### `id`

`id` MUST be a string uniquely identifying the chapter package.

The recommended form is:

    bookN.chapterNN

Example:

    id: book1.chapter03

The current loader does not enforce the naming pattern.

#### `book`

`book` MUST be convertible to an integer.

    book: 1

#### `chapter`

`chapter` MUST be convertible to an integer.

    chapter: 3

#### `title`

`title` MUST be a human-readable string.

#### `principal`

`principal` MUST identify the chapter's principal operator, spirit, authority, or corresponding figure.

The current implementation treats `title` and `principal` as descriptive metadata.

## 6. Protocol

The `protocol` field MUST be a mapping describing the operational claims made by the chapter text.

For consistency with the current chapters, every chapter SHOULD contain:

    protocol:
      address:
      authority:
      sign:
      availability:
      message_domain:
      sender:
      recipient:
      carrier:

Version 0.9.0 does not validate the complete internal schema of these sections. It does, however, require provenance entries for six specific protocol paths.

Additional sections and fields MAY be added.

### 6.1 `address`

The `address` section describes spatial, directional, temporal, or coordinate requirements.

Example:

    address:
      coordinate_system: compass
      direction: east-southeast
      mansion_index: 2
      spatial_requirement: required

The path `protocol.address.direction` MUST have provenance.

### 6.2 `authority`

The `authority` section describes the principal and any associated subordinate figures.

Example:

    authority:
      principal: Padiel
      associates: []
      ministers: []

The path `protocol.authority.principal` MUST have provenance.

### 6.3 `sign`

The `sign` section describes a mark, sign, seal, identifier, or routing symbol.

Example:

    sign:
      required_on_carrier: true
      identifier_role: selects_matching_method
      artifact: null

The path `protocol.sign.required_on_carrier` MUST have provenance.

### 6.4 `availability`

The `availability` section describes timing, repetition, or conditions of attempted operation.

Example:

    availability:
      day: unspecified
      night: unspecified
      repetition: until_presence_or_abort

### 6.5 `message_domain`

The `message_domain` section lists the kinds of secrets or messages associated with the chapter.

Example:

    message_domain:
      - general_secret_intention
      - judicial_or_penal_orders

The vocabulary is not currently constrained.

### 6.6 `sender`

The `sender` section describes the sender's actions.

Example:

    sender:
      invocation_artifact: sender-conjuration
      orientation: east-southeast
      secret_supplied: orally_after_carrier_written

The path `protocol.sender.invocation_artifact` MUST have provenance.

The named artifact SHOULD exist in the chapter's artifact declarations. Version 0.9.0 does not directly validate that relationship through the protocol field.

### 6.7 `recipient`

The `recipient` section describes the recipient's actions.

Example:

    recipient:
      invocation_artifact: receiver-conjuration
      orientation: east-southeast
      recognizes_sign: true

The path `protocol.recipient.invocation_artifact` MUST have provenance.

### 6.8 `carrier`

The `carrier` section describes the public text or object through which communication is represented.

Example:

    carrier:
      required: true
      semantics: innocent_and_publicly_readable
      language_constraint: none

The path `protocol.carrier.semantics` MUST have provenance.

## 7. Provenance

The `provenance` field connects protocol paths to evidence records.

It MUST be a mapping whose keys are dotted paths and whose values are either one evidence identifier or a list of evidence identifiers.

Example:

    provenance:
      protocol.address.direction:
        - ch03-direction
      protocol.authority.principal:
        - ch03-authority

### 7.1 Required Provenance Paths

Version 0.9.0 requires all of the following:

    protocol.address.direction
    protocol.authority.principal
    protocol.sign.required_on_carrier
    protocol.sender.invocation_artifact
    protocol.recipient.invocation_artifact
    protocol.carrier.semantics

### 7.2 Current Provenance Validation

For each provenance entry:

1. Every referenced evidence identifier MUST exist.
2. The evidence record's `relation` MUST exactly equal the provenance path.

Version 0.9.0 does not currently verify that every dotted provenance path actually exists in the `protocol` mapping. Authors SHOULD nevertheless ensure that it does.

A provenance list may technically be empty in version 0.9.0, but it SHOULD contain at least one evidence identifier.

## 8. Artifacts

The `artifacts` field MUST be a list.

Each artifact declaration MUST contain:

    id:
    role:
    path:

It MAY also contain:

    language:
    transcription:

Example:

    artifacts:
      - id: sender-conjuration
        role: sender_invocation
        path: sources/sender-conjuration.txt
        language: artificial
        transcription: diplomatic

      - id: sender-conjuration-website-normalized
        role: website_interlinear_normalized_input
        path: sources/sender-conjuration-website-normalized.txt
        language: artificial
        transcription: website_interlinear_normalized

      - id: ch03-sender-expected-compact
        role: expected_compact_extraction
        path: sources/ch03-sender-expected-compact.txt
        language: latin
        transcription: documented_reading

### 8.1 Artifact Requirements

- Artifact identifiers MUST be unique within a chapter.
- Every declared artifact path MUST exist as a file when the chapter is loaded.
- Artifact paths SHOULD remain within the chapter package.
- Artifact files SHOULD be UTF-8 text.
- Artifact files used for exact verification SHOULD contain only the intended comparison text, with no explanatory headings or notes.

The current loader does not enforce path containment. Authors MUST NOT use paths that escape the chapter package.

### 8.2 Source Variants and Normalization

Textual variation belongs primarily in artifacts and case selection, not in chapter-specific parser logic.

When editions, manuscripts, modern transcriptions, or editorial reconstructions differ, preserve separate artifacts such as:

    sender-conjuration-diplomatic
    sender-conjuration-1608
    sender-conjuration-selenus
    sender-conjuration-website-normalized
    sender-conjuration-editorial-reconstruction

Do not silently modify a diplomatic artifact merely to force a documented extraction.

A normalized artifact MAY remove or adjust punctuation, spacing, standalone symbols, damaged readings, or copying errors when needed to reproduce a documented experiment. Such changes SHOULD be disclosed through:

- a descriptive artifact identifier;
- the `transcription` field;
- case notes;
- a chapter README;
- evidence records when appropriate.

The engine is an experimental workbench. It is legitimate for several variants to produce several plausible outputs, provided each variant and procedure is explicit.

### 8.3 Expected and Reading Artifacts

An expected artifact contains the compact string used for exact comparison.

Example contents:

    nymdierstenbugstabendeomnyuerbo

A reading artifact contains the human-readable presentation.

Example contents:

    nym di ersten bugstaben de omny uerbo

The reading artifact is display-only. It does not participate in verification.

Use a reading artifact when spacing, punctuation, capitalization, damaged-text marks, or editorial divisions should be shown without changing the compact comparison string.

## 9. Evidence

The `evidence` field MUST be a list.

Each evidence record MUST contain:

    id:
    source:
    relation:

It MAY contain:

    quotation:
    confidence:

Example:

    evidence:
      - id: ch03-direction
        source: chapter_prose
        relation: protocol.address.direction
        quotation: face toward the appropriate mansion
        confidence: explicit

      - id: ch03-decoding-rule
        source: documented_interlinear_and_later_key
        relation: method.alternating-word-initials.pipeline
        quotation: take the first letters alternately
        confidence: historically_reconstructed

If `confidence` is omitted, version 0.9.0 defaults it to `explicit`.

Evidence identifiers MUST be unique within a chapter.

The `source`, `relation`, and `confidence` vocabularies are not currently constrained.

Recommended confidence descriptions include:

    explicit
    historically_reported
    historically_reconstructed
    editorial_reconstruction
    exploratory
    disputed

A method or case may reference any evidence identifier declared in the chapter.

## 10. Method Files

The `methods` field in `chapter.yaml` MUST list paths to method YAML files.

Example:

    methods:
      - methods/alternating-words-then-characters.yaml
      - methods/alternating-word-initials.yaml

Each referenced file MUST contain one YAML mapping.

### 10.1 Required Method Fields

A method file MUST contain:

    id:
    title:

It MUST contain exactly one of:

    pipeline:
    mode:

It MAY contain:

    evidence:
    notes:

Example:

    id: alternating-word-initials
    title: Take initials from alternating words
    evidence:
      - ch03-alternating-initial-rule
    notes:
      - Reused by all carrier examples using the same operation.
    pipeline:
      - unitize: {unit: word}
      - select: {schedule: {type: mask, values: "01", phase: 0}}
      - project: {part: initial}
      - concatenate: {}
      - normalize: {lowercase: true, remove_whitespace: true}

### 10.2 Method Validation

- Method identifiers MUST be unique within a chapter.
- A method MUST define exactly one of `pipeline` or `mode`.
- A direct `pipeline` MUST be a list and MUST be non-empty when compiled.
- A historical `mode` MUST be a mapping accepted by the historical mode compiler.
- Every evidence identifier named by a method MUST exist.
- Every compiled stage and option MUST be accepted by the pipeline loader.

### 10.3 Method Design Rules

A method SHOULD describe only the reusable transformation.

It SHOULD NOT contain:

- a fixed source artifact;
- a fixed expected plaintext;
- chapter-specific Python behavior;
- editorial prose that belongs in a case or README.

Do not create duplicate methods merely because two examples occur in different places. If two examples perform the same operations with the same parameters, they SHOULD use the same method.

A separate method is appropriate when the pipeline or its parameters materially differ.

Examples:

- mask `01` versus mask `001`;
- word initials versus whole selected words;
- forward selection versus a future reverse operation;
- different phase values that represent distinct documented procedures.

## 11. Case Files

The `cases` field in `chapter.yaml` MUST list paths to case YAML files.

Example:

    cases:
      - cases/sender-conjuration-instruction.yaml
      - cases/receiver-conjuration-instruction.yaml
      - cases/first-carrier-prayer.yaml

Each referenced file MUST contain one YAML mapping.

### 11.1 Required Case Fields

A case file MUST contain:

    id:
    title:
    method:
    input_artifact:
    status:

It MAY contain:

    expected_artifact:
    reading_artifact:
    evidence:
    notes:

Example verified case:

    id: chapter-iii-sender-conjuration
    title: Chapter III sender conjuration
    method: alternating-words-then-characters
    input_artifact: sender-conjuration-website-normalized
    expected_artifact: ch03-sender-expected-compact
    reading_artifact: ch03-sender-documented-reading
    status: verified
    evidence:
      - ch03-conjuration-decoding-rule
    notes:
      - Reproduces the extraction documented by the selected source.
      - The diplomatic source is retained separately.

Example unresolved case:

    id: printed-prayer-experiment
    title: Apply the recovered rule to the printed prayer
    method: all-word-initials
    input_artifact: printed-prayer-diplomatic
    expected_artifact: null
    reading_artifact: null
    status: unverified
    evidence:
      - ch03-word-initial-rule
    notes:
      - No accepted plaintext is currently configured.

### 11.2 Allowed Status Values

Version 0.9.0 accepts exactly:

    verified
    unverified
    falsified
    blocked

#### `verified`

Use when the case has a configured expected output and is intended to reproduce it.

A verified case MUST declare `expected_artifact`.

#### `unverified`

Use when the method can be executed but no accepted expected output is configured.

This is appropriate for unresolved historical examples and open experiments.

#### `falsified`

Use for a reproducible hypothesis known not to match its proposed target.

The current CLI still determines displayed `PASS` or `FAIL` from exact output comparison; it does not give `falsified` special runtime behavior. Notes and tests SHOULD make the intended negative result clear.

#### `blocked`

Use when a case is retained descriptively but cannot presently be executed reliably because essential data or an operation is missing.

Version 0.9.0 does not prevent execution solely because the status is `blocked`. Authors SHOULD avoid listing a blocked case as ordinarily runnable until the runner gains explicit blocked-case behavior, or ensure tests and documentation explain the limitation.

### 11.3 Case Validation

- Case identifiers MUST be unique within a chapter.
- `method` MUST identify a declared method.
- `input_artifact` MUST identify a declared artifact.
- `expected_artifact`, when non-null, MUST identify a declared artifact.
- `reading_artifact`, when non-null, MUST identify a declared artifact.
- `status` MUST be one of the allowed values.
- A verified case MUST have an expected artifact.
- Every evidence identifier named by a case MUST exist.

### 11.4 Cases and Textual Variants

Different source variants SHOULD normally be represented as different cases using the same method.

Example:

    cases:
      - cases/prayer-website-normalized.yaml
      - cases/prayer-1608-diplomatic.yaml
      - cases/prayer-selenus.yaml

This permits comparisons such as:

- same method, different source variants;
- same source, different method parameters;
- same documented target, different degrees of textual reconstruction;
- several plausible outputs associated with different witnesses.

The configuration MUST make clear which input produced which output.

## 12. Pipeline Language

A pipeline is an ordered list of stages.

Each stage mapping MUST contain exactly one operation.

Example:

    pipeline:
      - unitize: {unit: word}
      - select: {schedule: {type: mask, values: "01", phase: 0}}
      - project: {part: initial}
      - concatenate: {}
      - normalize: {lowercase: true, remove_whitespace: true}

Each stage receives the typed output of the preceding stage.

Version 0.9.0 supports five operations:

    unitize
    select
    project
    concatenate
    normalize

Unknown operations and unknown options are rejected.

## 13. Pipeline Value Types

The runtime currently uses:

### `Text`

Raw text loaded from an input artifact.

### `UnitSequence`

An ordered tuple of units with a `unit_type` such as `word` or `character`.

### `EmittedStream`

A joined text stream produced by concatenation or normalization.

The normal data flow is:

    Text
      → unitize
    UnitSequence
      → select and/or project
    UnitSequence
      → concatenate
    EmittedStream
      → normalize or character unitization

## 14. `unitize`

The `unitize` operation converts text into a `UnitSequence`.

### 14.1 Word Units

Configuration:

    - unitize:
        unit: word

Compact form:

    - unitize: {unit: word}

Input type:

    Text

Output type:

    UnitSequence(unit_type="word")

Version 0.9.0 identifies words with a Unicode-aware alphabetic regular expression. It accepts internal apostrophes and hyphens. It excludes standalone digits, punctuation, underscores, whitespace, and symbols such as `&`.

Consequences:

- punctuation does not become a unit;
- standalone numbers do not become units;
- a standalone ampersand does not become a unit;
- alphabetic words containing long-s or other Unicode letters can be units;
- exact historical counting may depend on the supplied artifact variant.

Do not add elaborate parser behavior merely to handle one doubtful witness. Prefer an explicit normalized source artifact when a documented reconstruction requires different counting.

`include_whitespace` is invalid for word units.

### 14.2 Character Units

Configuration:

    - unitize:
        unit: character
        include_whitespace: false

Input types:

    Text
    EmittedStream

Output type:

    UnitSequence(unit_type="character")

`include_whitespace` defaults to `false`.

When false, all Unicode whitespace characters are omitted. Other characters, including punctuation, are retained.

When true, whitespace characters are retained as units.

## 15. `select`

The `select` operation retains units selected by a schedule.

Configuration:

    - select:
        schedule:
          type: mask
          values: "01"
          phase: 0

Input type:

    UnitSequence

Output type:

    UnitSequence with the same `unit_type`

Version 0.9.0 supports only repeating binary mask schedules.

### 15.1 Mask Values

`values` MUST be either:

- a non-empty string containing only `0` and `1`; or
- a non-empty YAML list containing integer `0` and `1` values.

Examples:

    values: "01"

    values: [0, 1]

A mask value of `1` means take the unit. A value of `0` means skip it.

### 15.2 Phase

`phase` MUST be a nonnegative integer. It defaults to `0`.

For unit index `i`, the mask position is:

    (i + phase) mod mask_length

For mask `01`:

- phase `0` skips unit 0, takes unit 1, skips unit 2, and so on;
- phase `1` takes unit 0, skips unit 1, takes unit 2, and so on.

Example selecting alternating units beginning with the second:

    - select: {schedule: {type: mask, values: "01", phase: 0}}

Example selecting alternating units beginning with the first:

    - select: {schedule: {type: mask, values: "01", phase: 1}}

## 16. `project`

The `project` operation transforms each unit while preserving sequence structure.

Input type:

    UnitSequence

Output type:

    UnitSequence

Version 0.9.0 supports:

    initial
    whole

### 16.1 Initial Projection

Configuration:

    - project: {part: initial}

Each non-empty unit becomes its first character.

The output `unit_type` becomes `character`.

This is commonly used after word unitization:

    - unitize: {unit: word}
    - project: {part: initial}

### 16.2 Whole Projection

Configuration:

    - project: {part: whole}

Each unit is preserved unchanged.

The output retains the input `unit_type`.

This operation is currently useful mainly for explicitness and future pipeline composition.

## 17. `concatenate`

The `concatenate` operation joins a `UnitSequence` into an `EmittedStream`.

Configuration:

    - concatenate: {}

or:

    - concatenate:
        separator: " "

Input type:

    UnitSequence

Output type:

    EmittedStream

`separator` defaults to the empty string and MUST be a string.

Examples:

    - concatenate: {}

joins units directly.

    - concatenate: {separator: " "}

joins units with spaces.

## 18. `normalize`

The `normalize` operation performs string normalization.

Configuration:

    - normalize:
        lowercase: true
        remove_whitespace: true
        substitutions:
          "ſ": "s"

Input types:

    Text
    EmittedStream

Output type:

    EmittedStream

Supported options are:

    lowercase
    remove_whitespace
    substitutions

All options are optional.

### 18.1 `lowercase`

When true, Python's Unicode lowercase conversion is applied.

Default:

    false

### 18.2 `substitutions`

`substitutions` MUST be a mapping from strings to strings.

Substitutions are applied in YAML mapping order using ordinary string replacement.

Example:

    substitutions:
      "ſ": "s"
      "æ": "ae"

Use substitutions cautiously. When substitutions represent a source reconstruction rather than a general normalization, prefer a separate normalized artifact so the editorial decision remains visible.

### 18.3 `remove_whitespace`

When true, all whitespace is removed by splitting and rejoining the string.

Default:

    false

### 18.4 Operation Order

Normalization occurs in this order:

1. lowercase;
2. substitutions in declared order;
3. whitespace removal.

## 19. Supported Pipeline Patterns

### 19.1 Every Word Initial

    pipeline:
      - unitize: {unit: word}
      - project: {part: initial}
      - concatenate: {}
      - normalize: {lowercase: true, remove_whitespace: true}

### 19.2 Alternating Word Initials Beginning with the Second Word

    pipeline:
      - unitize: {unit: word}
      - select: {schedule: {type: mask, values: "01", phase: 0}}
      - project: {part: initial}
      - concatenate: {}
      - normalize: {lowercase: true, remove_whitespace: true}

### 19.3 Alternating Words, Then Alternating Characters

    pipeline:
      - unitize: {unit: word}
      - select: {schedule: {type: mask, values: "01", phase: 0}}
      - concatenate: {}
      - unitize: {unit: character, include_whitespace: false}
      - select: {schedule: {type: mask, values: "01", phase: 0}}
      - concatenate: {}
      - normalize: {lowercase: true, remove_whitespace: true}

### 19.4 Different Source Variants Using One Method

Method:

    id: alternating-word-initials
    title: Alternating word initials
    evidence: [ch03-rule]
    notes: []
    pipeline:
      - unitize: {unit: word}
      - select: {schedule: {type: mask, values: "01", phase: 0}}
      - project: {part: initial}
      - concatenate: {}
      - normalize: {lowercase: true, remove_whitespace: true}

Case using a normalized website transcription:

    id: prayer-website-normalized
    title: Prayer using the website-normalized text
    method: alternating-word-initials
    input_artifact: prayer-website-normalized
    expected_artifact: prayer-expected-compact
    reading_artifact: prayer-documented-reading
    status: verified
    evidence: [ch03-rule]
    notes:
      - Reproduces the selected website's documented output.

Case using a diplomatic transcription:

    id: prayer-diplomatic-experiment
    title: Prayer using the diplomatic text
    method: alternating-word-initials
    input_artifact: prayer-diplomatic
    expected_artifact: null
    reading_artifact: null
    status: unverified
    evidence: [ch03-rule]
    notes:
      - Retained to compare the printed witness with the normalized reconstruction.

## 20. Execution

### 20.1 Compilation

A case is compiled by:

1. locating the configured case;
2. locating its method, or an explicit method override;
3. compiling the method's pipeline;
4. locating the case input artifact, or an explicit input override;
5. loading the input artifact as UTF-8 text;
6. executing the pipeline beginning with a `Text` value.

### 20.2 Output Conversion

The CLI converts the final pipeline value to text using `result_text()`.

Chapter methods SHOULD normally end in `concatenate` or `normalize` so the final result is an `EmittedStream` with an unambiguous compact value.

### 20.3 Configured and Overridden Runs

A normal case run is configured and may be verified against its expected artifact.

Example:

    python3 run_chapter.py chapter02 --case chapter-ii-first-prayer

A method or input override creates an experiment:

    python3 run_chapter.py chapter02 \
      --case chapter-ii-first-prayer \
      --input-artifact carrier-prayer-one-latin-1608

or:

    python3 run_chapter.py chapter02 \
      --case chapter-ii-first-prayer \
      --method another-method

Version 0.9.0 intentionally reports an overridden case as `UNVERIFIED`, because the configured expected artifact belongs to the original method and input combination.

### 20.4 Exact Comparison

For a configured case with an expected artifact:

- actual output is compared exactly with expected text;
- only the expected file's final `\r` or `\n` line ending is stripped;
- internal whitespace, punctuation, capitalization, and uncertainty marks remain significant unless the pipeline has normalized them.

The result is:

    PASS

or:

    FAIL

A configured case with no expected artifact is reported:

    UNVERIFIED

### 20.5 Reading Display

When `reading_artifact` is present, the CLI prints:

    reading: ...

This does not affect PASS or FAIL.

## 21. CLI Reference

### Validate a chapter

    python3 run_chapter.py chapter03 --validate-only

Expected form:

    PASS: book1.chapter03

### List methods

    python3 run_chapter.py chapter03 --list-methods

### List cases

    python3 run_chapter.py chapter03 --list-cases

### List artifacts

    python3 run_chapter.py chapter03 --list-artifacts

### Run all cases

    python3 run_chapter.py chapter03

### Run one case

    python3 run_chapter.py chapter03 --case case-id

### Show a trace

    python3 run_chapter.py chapter03 --case case-id --trace

Trace output is written to standard error. The case result is written to standard output.

### Run cases using one configured method

    python3 run_chapter.py chapter03 --method method-id

### Override a case's method

    python3 run_chapter.py chapter03 --case case-id --method method-id

### Override a case's input artifact

    python3 run_chapter.py chapter03 --case case-id --input-artifact artifact-id

An input override requires `--case`.

### Exit Status

`run_chapter.py` exits with status `1` when any executed case reports `FAIL`.

It exits with status `0` when results contain only `PASS` and `UNVERIFIED`.

## 22. Trace Semantics

Every pipeline stage produces a trace event containing:

- stage name;
- input type;
- output type;
- stage-specific details.

Current trace details include:

- unitized units;
- selection masks and per-unit decisions;
- projection decisions;
- concatenated values;
- normalized values.

A trace is intended to make a historical extraction auditable. It allows a researcher to inspect exactly which units were taken or skipped.

A trace proves what the configured pipeline did. It does not prove that the historical author intended that pipeline.

## 23. Validation Rules

A chapter package is invalid when version 0.9.0 detects any of the following.

### 23.1 Manifest Errors

- `chapter.yaml` is missing;
- a YAML file does not contain a mapping;
- a required top-level manifest field is missing.

### 23.2 Artifact Errors

- an artifact identifier is duplicated;
- a declared artifact file does not exist;
- a case references an unknown input artifact;
- a case references an unknown expected artifact;
- a case references an unknown reading artifact.

### 23.3 Evidence Errors

- an evidence identifier is duplicated;
- a method references unknown evidence;
- a case references unknown evidence;
- provenance references unknown evidence;
- provenance evidence has a `relation` that does not exactly match the provenance path.

### 23.4 Method Errors

- a method identifier is duplicated;
- a method pipeline is not a list;
- the pipeline is empty when compiled;
- a pipeline stage is malformed;
- a stage operation is unknown;
- a stage option is unknown;
- a schedule or parameter is invalid.

### 23.5 Case Errors

- a case identifier is duplicated;
- a case uses an unknown status;
- a case references an unknown method;
- a verified case lacks an expected artifact.

### 23.6 Provenance Errors

- any of the six required provenance paths is absent;
- a provenance reference names unknown evidence;
- the evidence relation does not match the provenance key.

## 24. Verification Semantics

Three different questions MUST remain separate.

### 24.1 Did the software execute?

A pipeline may execute successfully and produce a string.

### 24.2 Did the output match the configured expected artifact?

This determines CLI `PASS` or `FAIL` for configured cases with expectations.

### 24.3 Is the historical interpretation correct?

This requires historical and textual evidence beyond software execution.

A `PASS` means:

> This method applied to this exact input artifact produced this exact configured expected output.

It does not necessarily mean:

> This is the only valid reconstruction, every witness produces it, or the historical author applied a perfectly consistent parsing rule.

Textual witnesses may differ because of copying, printing, editorial normalization, or deliberate adjustment. Multiple explicit cases may therefore be historically useful.

## 25. Chapter Authoring Workflow

When converting a new chapter, use the following workflow.

### Step 1: Inventory the Chapter

Identify:

- chapter number and title;
- principal and subordinate figures;
- direction, mansion, timing, or address information;
- sender procedure;
- recipient procedure;
- sign or routing requirements;
- sender and receiver conjurations;
- carrier letters, prayers, or narratives;
- separately stated secrets;
- interlinear decodings;
- documented modern reconstructions;
- unresolved examples;
- known textual variants.

Do not assume every visible text is an executable cipher example.

### Step 2: Separate Artifacts

Create distinct files for materially distinct objects, such as:

    sender-conjuration.txt
    receiver-conjuration.txt
    carrier-prayer-diplomatic.txt
    carrier-prayer-website-normalized.txt
    sender-expected-compact.txt
    sender-documented-reading.txt
    stated-secret.txt

Do not place explanatory prose in files used for exact execution or comparison.

### Step 3: Describe the Protocol

Populate the protocol sections from explicit chapter claims.

Do not turn ritual or narrative language directly into executable behavior unless a method is separately justified.

### Step 4: Add Evidence and Provenance

Create evidence records for the six required protocol paths and for every decoding rule or documented output that materially supports a method or case.

Use quotations that are concise but sufficient to identify the basis of the claim.

### Step 5: Identify Reusable Methods

Group examples by operation.

Ask:

- Do these examples use the same unitization?
- Do they use the same mask and phase?
- Do they project initials or preserve whole units?
- Do they concatenate and then select characters?
- Do they normalize in the same way?

Create one method for each distinct operation, not one method for each source text.

### Step 6: Create Cases

Create one case for each meaningful application:

- each documented conjuration extraction;
- each documented carrier decoding;
- each source variant worth comparing;
- each unresolved but executable experiment;
- each intentionally falsified hypothesis worth preserving.

### Step 7: Configure Expected Output

For a documented decipherment:

1. create a compact expected artifact containing exactly the comparison string;
2. create a reading artifact if human-readable spacing or uncertainty differs;
3. mark the case `verified`;
4. add evidence and notes identifying the documentation source.

For an unresolved example:

1. leave `expected_artifact` null or absent;
2. leave `reading_artifact` null or absent unless a non-verified reading is intentionally displayed;
3. mark the case `unverified`;
4. explain the unresolved status in notes.

### Step 8: Validate

Run:

    python3 run_chapter.py chapterNN --validate-only

Fix every validation error before proceeding.

### Step 9: Inspect the Chapter

Run:

    python3 run_chapter.py chapterNN --list-methods
    python3 run_chapter.py chapterNN --list-cases
    python3 run_chapter.py chapterNN --list-artifacts

Confirm that identifiers, titles, paths, and statuses are sensible.

### Step 10: Execute Every Case

Run:

    python3 run_chapter.py chapterNN

Every documented verified case SHOULD report `PASS`.

Unresolved experiments SHOULD report `UNVERIFIED`, not a manufactured PASS.

### Step 11: Inspect Traces

For each new method, inspect at least one representative trace:

    python3 run_chapter.py chapterNN --case case-id --trace

Confirm that units, mask positions, projections, and output correspond to the intended operation.

### Step 12: Add Tests

At minimum, add tests that:

- load the chapter successfully;
- confirm its expected method and case identifiers;
- execute every documented verified case;
- compare actual compact output with expected artifacts;
- exercise any new pipeline primitive;
- ensure existing chapters continue to pass.

### Step 13: Run the Full Suite

Run:

    python3 run_tests.py

Do not weaken or delete existing tests merely to make a new chapter pass.

## 26. Testing Guidance

A chapter-level historical test may follow this conceptual pattern:

    chapter = load_chapter(ROOT / "corpus" / "book1" / "chapter03")

    for case_id in (
        "chapter-iii-sender-conjuration",
        "chapter-iii-receiver-conjuration",
        "chapter-iii-first-prayer",
    ):
        compiled = compile_case(chapter, case_id)
        actual = result_text(compiled.execute())
        expected_id = chapter.cases[case_id].expected_artifact
        expected = chapter.artifacts[expected_id].path.read_text(
            encoding="utf-8"
        ).rstrip("\r\n")
        assert actual == expected

Tests SHOULD verify behavior, not merely the presence of files.

When adding a new primitive, add focused unit tests for:

- accepted configuration;
- rejected invalid configuration;
- type requirements;
- boundary behavior;
- trace contents;
- composition with existing stages.

## 27. When Python Changes Are Justified

A new chapter SHOULD NOT require changes to the Python engine when its operation can be represented with existing stages.

New Python code is justified when a chapter reveals a genuinely new reusable mechanism, such as:

- non-repeating or computed skip schedules;
- reversal;
- transposition;
- indexed character projection beyond initials;
- numerical tables or symbol mappings;
- branching or grouped extraction;
- operations over lines, syllables, symbols, or other new unit types;
- a general representation conversion not expressible by current stages.

When Python changes are necessary:

1. implement a general primitive, not a function named for one chapter;
2. define its typed input and output;
3. expose it through the pipeline loader;
4. reject unknown or invalid options;
5. produce useful trace details;
6. add unit tests;
7. update this specification;
8. use it from chapter configuration.

Do not add code such as:

    if chapter == 7:
        ...

or:

    def decode_padiel_special_case(...):
        ...

unless the behavior truly cannot be generalized and the limitation is explicitly documented.

## 28. Common Authoring Errors

Another AI or contributor MUST avoid these mistakes.

### 28.1 Creating one method per example

Wrong when several examples use the same operation.

Use one shared method and several cases.

### 28.2 Silently altering source text

Do not overwrite a diplomatic transcription to force a result.

Create a separate normalized artifact and document the change.

### 28.3 Treating execution as verification

A pipeline producing output does not make a case verified.

A verified case requires a documented or intentionally configured expected artifact.

### 28.4 Confusing a stated secret with an extracted plaintext

A chapter may narratively state what a prince wants conveyed without the printed carrier demonstrably encoding that exact message.

Keep separately stated secrets distinct from extracted outputs.

### 28.5 Using the readable output for exact machine comparison

Keep compact output and human-readable spacing separate when appropriate.

### 28.6 Inventing plaintext for unresolved material

Use `unverified` and explain the uncertainty.

### 28.7 Hiding editorial judgment in parser code

Prefer explicit source variants over ad hoc tokenization rules added for one text.

### 28.8 Adding unused method files

Every method file SHOULD be listed in `chapter.yaml` or removed.

### 28.9 Duplicating methods under chapter-specific names

If an identical general method already exists within the chapter, reuse it.

Version 0.9.0 stores methods per chapter, so methods are not yet shared across chapter directories. Within a chapter, duplicate definitions SHOULD still be avoided.

### 28.10 Changing old fixtures while adding a new chapter

New work SHOULD preserve existing verified behavior. Add variants rather than rewriting historical fixtures without a documented reason.

## 29. Complete Chapter Template

The following template is intended as a starting point. Replace every placeholder with chapter-specific information.

    id: book1.chapter03
    book: 1
    chapter: 3
    title: Replace with chapter title
    principal: Replace with principal

    protocol:
      address:
        coordinate_system: compass
        direction: replace_me
        mansion_index: 3
        spatial_requirement: required

      authority:
        principal: Replace with principal
        associates: []
        ministers: []

      sign:
        required_on_carrier: true
        identifier_role: selects_matching_method
        artifact: null

      availability:
        day: unspecified
        night: unspecified
        repetition: unspecified

      message_domain:
        - general_secret_intention

      sender:
        invocation_artifact: sender-conjuration
        orientation: replace_me
        secret_supplied: unknown

      recipient:
        invocation_artifact: receiver-conjuration
        orientation: replace_me
        recognizes_sign: true

      carrier:
        required: true
        semantics: innocent_and_publicly_readable
        language_constraint: none

    provenance:
      protocol.address.direction:
        - ch03-direction
      protocol.authority.principal:
        - ch03-authority
      protocol.sign.required_on_carrier:
        - ch03-sign
      protocol.sender.invocation_artifact:
        - ch03-sender-invocation
      protocol.recipient.invocation_artifact:
        - ch03-recipient-invocation
      protocol.carrier.semantics:
        - ch03-carrier

    artifacts:
      - id: sender-conjuration
        role: sender_invocation
        path: sources/sender-conjuration.txt
        language: artificial
        transcription: diplomatic

      - id: receiver-conjuration
        role: recipient_invocation
        path: sources/receiver-conjuration.txt
        language: artificial
        transcription: diplomatic

      - id: carrier-text
        role: public_carrier
        path: sources/carrier-text.txt
        language: latin
        transcription: diplomatic

      - id: sender-conjuration-normalized
        role: normalized_decoding_input
        path: sources/sender-conjuration-normalized.txt
        language: artificial
        transcription: documented_normalization

      - id: sender-expected-compact
        role: expected_compact_extraction
        path: sources/sender-expected-compact.txt
        language: latin
        transcription: documented_reading

      - id: sender-readable
        role: display_reading
        path: sources/sender-readable.txt
        language: latin
        transcription: documented_reading

    evidence:
      - id: ch03-direction
        source: chapter_prose
        relation: protocol.address.direction
        quotation: Replace with relevant passage.
        confidence: explicit

      - id: ch03-authority
        source: chapter_heading
        relation: protocol.authority.principal
        quotation: Replace with relevant passage.
        confidence: explicit

      - id: ch03-sign
        source: chapter_prose
        relation: protocol.sign.required_on_carrier
        quotation: Replace with relevant passage.
        confidence: explicit

      - id: ch03-sender-invocation
        source: chapter_prose
        relation: protocol.sender.invocation_artifact
        quotation: Replace with relevant passage.
        confidence: explicit

      - id: ch03-recipient-invocation
        source: chapter_prose
        relation: protocol.recipient.invocation_artifact
        quotation: Replace with relevant passage.
        confidence: explicit

      - id: ch03-carrier
        source: chapter_prose
        relation: protocol.carrier.semantics
        quotation: Replace with relevant passage.
        confidence: explicit

      - id: ch03-decoding-method
        source: documented_decipherment
        relation: method.chapter03-decoder.pipeline
        quotation: Replace with documented rule.
        confidence: historically_reconstructed

    methods:
      - methods/chapter03-decoder.yaml

    cases:
      - cases/chapter03-sender-conjuration.yaml
      - cases/chapter03-carrier-experiment.yaml

Example method file:

    id: chapter03-decoder
    title: Replace with concise operation title
    evidence:
      - ch03-decoding-method
    notes:
      - Describe only method-wide assumptions here.
    pipeline:
      - unitize: {unit: word}
      - select: {schedule: {type: mask, values: "01", phase: 0}}
      - project: {part: initial}
      - concatenate: {}
      - normalize: {lowercase: true, remove_whitespace: true}

Example verified case file:

    id: chapter-iii-sender-conjuration
    title: Chapter III sender conjuration
    method: chapter03-decoder
    input_artifact: sender-conjuration-normalized
    expected_artifact: sender-expected-compact
    reading_artifact: sender-readable
    status: verified
    evidence:
      - ch03-decoding-method
    notes:
      - State which edition or website documents this extraction.
      - State why the normalized artifact differs from the diplomatic artifact.

Example unverified case file:

    id: chapter-iii-carrier-experiment
    title: Apply the documented method to the carrier text
    method: chapter03-decoder
    input_artifact: carrier-text
    expected_artifact: null
    reading_artifact: null
    status: unverified
    evidence:
      - ch03-decoding-method
      - ch03-carrier
    notes:
      - No accepted plaintext is currently configured.

## 30. Chapter README Guidance

A chapter README is not required by the loader but is strongly recommended.

It SHOULD explain:

- the selected documentary source;
- which artifacts are diplomatic and which are normalized;
- every known normalization or reconstruction decision;
- documented plaintexts and their source;
- unresolved examples;
- competing witnesses or editions;
- commands for listing and running cases;
- any method that required a new engine primitive.

A concise README outline is:

    # Chapter III

    ## Source basis

    Identify the edition, translation, website, manuscript, or secondary source.

    ## Included artifacts

    Explain diplomatic, normalized, expected, and reading files.

    ## Methods

    Explain the reusable operations represented in method YAML.

    ## Cases

    Explain which are verified, unverified, falsified, or blocked.

    ## Known textual issues

    Record copying, printing, punctuation, spacing, or editorial uncertainties.

    ## Commands

        python3 run_chapter.py chapter03 --validate-only
        python3 run_chapter.py chapter03
        python3 run_chapter.py chapter03 --case case-id --trace

## 31. Design Principles

### 31.1 Configuration Drives Chapter Behavior

Chapter-specific historical behavior SHOULD live in:

- `chapter.yaml`;
- method YAML;
- case YAML;
- source artifacts;
- evidence and notes.

It SHOULD NOT live in chapter-specific Python branches.

### 31.2 Methods and Cases Are Separate

A method is reusable computation. A case is a historical or experimental claim about applying that computation to a particular text.

### 31.3 Source Variants Remain Explicit

Diplomatic, normalized, reconstructed, and edition-specific texts SHOULD remain separate artifacts.

### 31.4 Evidence Remains Explicit

Protocol claims, methods, expected outputs, and editorial reconstructions SHOULD identify their evidentiary basis.

### 31.5 Multiple Hypotheses May Coexist

A chapter MAY contain several methods and several cases without implying that every one is endorsed.

### 31.6 Negative and Unresolved Results Remain Reproducible

A failed or unresolved extraction may remain in the package when it is historically or experimentally informative.

### 31.7 New Mechanisms Are Reusable

When a chapter requires a new operation, implement a general primitive that other chapters can use.

### 31.8 Engine Correctness and Historical Correctness Are Distinct

A passing software test proves a reproducible transformation, not unique historical truth.

### 31.9 Do Not Over-Generalize Before Evidence Requires It

Do not build arbitrary recursive transformation machinery, complicated tokenization policy systems, or chapter-independent abstractions merely because they might someday be useful.

Add the smallest reusable capability demanded by an actual chapter.

## 32. Known Limitations of Version 0.9.0

The following limitations are important when authoring new chapters:

- `run_chapter.py` selects only chapters under `corpus/book1/`;
- methods are declared separately inside each chapter and are not yet shared through a global method library;
- word, character, and line unitization are supported, but half-line/page/glyph/color units are not yet modeled;
- word unitization follows one fixed Unicode-aware regular expression;
- repeating masks, semantic alternating blocks, and explicit boundary-reset schedules are supported;
- `initial`, `final`, and `whole` projection are supported; syllable projection is deliberately unresolved;
- forward and reverse traversal are supported; transposition, scattering, indexed projection, and numerical tables are not yet supported;
- blocked and falsified statuses have no special CLI execution semantics;
- the loader does not enforce a controlled vocabulary for roles, languages, transcription types, evidence sources, or confidence values;
- artifact paths are constrained to the chapter root;
- sender, recipient, and sign protocol artifact identifiers are checked against declared artifacts;
- dotted provenance paths are checked against the protocol structure;
- reading artifacts are display-only and are not compared;
- exact output comparison supports one expected artifact per case;
- there is no schema-version field in chapter YAML;
- there is no generated JSON Schema;
- normalized artifact changes are documented by convention rather than a dedicated normalization schema.

These limitations SHOULD be addressed only when real chapter work demonstrates a need.

## 33. Reference Packages

The current reference packages are:

    corpus/book1/chapter01/
    corpus/book1/chapter02/

Together they demonstrate:

- several methods within a chapter;
- several cases using one method;
- diplomatic and website-normalized artifacts;
- exact compact expected output;
- separately displayed readable output;
- verified and unverified cases;
- interlinear conjuration decoding;
- alternating word-initial extraction;
- traceable selection over words and characters.

When this document and the implementation disagree, inspect the implementation and tests. Resolve the disagreement explicitly by correcting either the code or this specification. Do not silently assume that one is authoritative.

## 34. Completion Criteria for a New Chapter

A new chapter package is ready for review when all of the following are true:

- `chapter.yaml` loads successfully;
- every required protocol provenance path is present;
- every declared artifact exists;
- diplomatic and normalized sources are clearly distinguished;
- every reusable decoding operation has one method file;
- every documented example has one case file;
- every documented decipherment has an exact expected compact artifact;
- readable spacing or uncertainty is stored separately when needed;
- unresolved examples are marked unverified rather than forced to pass;
- representative traces have been inspected;
- chapter-specific tests exercise all verified cases;
- the complete existing test suite passes;
- no chapter-specific Python branch was added when existing primitives were sufficient;
- any new primitive is generic, traced, tested, and documented.

## 35. Revision Policy

This is a working specification.

When implementation changes alter the accepted configuration format, one of the following MUST occur:

1. the implementation is corrected to continue satisfying this specification; or
2. this specification is revised and its version is incremented.

Changes SHOULD identify whether they are:

- backward-compatible additions;
- clarifications;
- validation changes;
- deprecated behavior;
- breaking schema changes.

Because version 0.8 intentionally removed the version 0.7 interpretation architecture, specification version 0.2 is a breaking replacement rather than a compatible extension of version 0.1.


## 36. Version 0.9 Historical Representation Extensions

Version 0.9 adds a historical representation layer above the linear pipeline.

A method MUST define exactly one of:

- a direct `pipeline`; or
- a historical `mode` that compiles to a pipeline.

Historical modes MAY preserve:

- a reusable family;
- semantic parameters;
- the source's `o` / `.` notation;
- forward or reverse traversal;
- modifiers requiring case-specific execution evidence.

For the simple block family, `o` denotes an Idle/non-significant word and `.` a Valid/significant word. The compiler MUST reject a historical notation that contradicts the semantic run lengths and starting order.

Cases MAY contain an `execution` mapping. Such values are inputs required by the historical operation for that particular case; they MUST NOT be inferred from the expected output. Boundary-sensitive execution currently uses this mechanism.

Unit streams MAY retain `SourceSpan` coordinates. Stages that preserve unit identity SHOULD preserve those spans. Final concatenation MAY intentionally collapse geometry.

Artifacts MAY declare `witness`, `locator`, `derived_from`, `transformations`, and artifact-level `evidence`. A declared parent artifact and evidence identifier MUST exist.

Chapters MAY contain structured `claims`. Claims are distinct from executable methods and use one of these statuses:

- `documented`
- `reconstructed`
- `hypothesis`
- `unresolved`
- `contradicted`

A hypothesis MUST NOT become executable historical semantics merely because an experiment can instantiate it.

The historical catalogue is maintained separately in `corpus/mode_registry.yaml`. Catalogue membership, structural classification, executability, and verification are separate properties.

See `docs/HISTORICAL_MODE_ARCHITECTURE.md` for the architecture and current deliberate gaps.
