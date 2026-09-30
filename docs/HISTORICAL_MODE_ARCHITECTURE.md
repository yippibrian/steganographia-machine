# Historical Mode Architecture

The linear pipeline remains the execution kernel. Historical descriptions compile into it, while evidence and uncertainty remain outside the kernel.

## Layers

1. **Artifacts** preserve documentary witnesses and derivation metadata.
2. **Units** retain source coordinates instead of becoming anonymous strings.
3. **Primitive stages** perform unitization, traversal, selection, projection, concatenation, and normalization.
4. **Schedules** express low-level masks, semantic idle/significant blocks, or explicit boundary-reset behavior.
5. **Mode families** express reusable historical structures such as word initials and block word initials.
6. **Named historical modes** bind family parameters and may preserve the printed o/. notation.
7. **Methods** contain either a direct pipeline or a historical mode definition.
8. **Cases** bind a method to artifacts and may supply case-specific execution evidence.
9. **Claims** record documented, reconstructed, hypothetical, unresolved, or contradicted propositions separately from executable rules.

## Source geometry

Unitization preserves a SourceSpan for each unit:

- character offsets,
- line,
- column,
- ending coordinates.

Word, character, and line units are currently supported. Selection, traversal, and projection preserve aligned spans. Concatenation intentionally collapses geometry only at the final emitted stream.

This is the basis for later alternate-line, half-line, page, glyph, and color operations without forcing them into ad hoc tokenizers.

## Traversal and projection

Traversal is a first-class stage:

    unitize -> traverse -> select -> project -> concatenate

Supported traversal directions are forward and reverse.

Projection currently supports:

- initial,
- final,
- whole.

Syllable projection is intentionally not implemented until a historically defensible segmentation policy is available.

## Historical notation

For the simple block family, the source notation is retained alongside semantic parameters.

In Selenus's table:

- o = Idle / non-significant word
- . = Valid / significant word

Thus:

    Camuel   o.
    Padiel   .o
    Aseliel  o..
    Gediel   oo..

The compiler checks that historical_notation agrees with the semantic parameters. This gives the source notation and executable representation a round-trip consistency check.

## The sixty-cell simple block space

The two orders contain thirty structural cells each.

- five columns vary idle_run from 1 through 5;
- six rows vary significant_run from 1 through 6;
- the two orders reverse which class begins the cycle.

Generated cells are deliberately unnamed. Historical names are attached only in the corpus registry when the source supports the identification.

## Stateful boundaries

Later descriptions change behavior when a hidden word ends. These are not silently reduced to periodic masks.

The engine supports an explicit boundary_reset schedule. Boundaries are represented as 1-based counts of selected/significant units and are supplied as case execution parameters.

A boundary-sensitive historical mode may declare:

    modifiers:
      - type: boundary_reset
        boundary_parameter: boundary_after_selected

A case may then supply:

    execution:
      boundary_after_selected: [4, 9, 15]

If the case does not supply required boundaries, execution fails. The compiler never derives them from expected plaintext.

This distinction is intentional:

- the mode records the reusable historical rule;
- the case records evidence specific to one application;
- expected output remains verification data, never decoder input.

The current boundary-reset primitive is generic machinery. It does not by itself assert that Barmiel, Asiriel, Malgaras, or another named mode has been completely reconstructed.

## Encoding as constraints

The encoder does not attempt to generate plausible Latin or German cover prose.

For supported forward modes it compiles a secret into carrier-slot constraints:

- idle slots have no required initial;
- significant slots carry the next required secret initial.

A candidate carrier can then be checked against that plan. This gives the project an independent construction-side test while keeping natural-language composition outside the mechanical cipher rule.

Stateful boundary-sensitive encoding and reverse-traversal encoding remain deliberate gaps until their construction semantics are modeled explicitly.

## Claims and hypotheses

A chapter may contain structured claims independently of executable methods.

Claim statuses are:

- documented
- reconstructed
- hypothesis
- unresolved
- contradicted

Claims may cite evidence and explicitly contradict other claims. This is where propositions such as a possible operational meaning for day/night, attendants, signs, colors, or numerical fields belong until evidence justifies promoting them into executable historical rules.

## Artifact provenance

Artifacts may now record:

- witness
- locator
- derived_from
- transformations
- evidence

Paths are constrained to the chapter root. Parent artifacts and evidence references are validated.

A normalized or reconstructed artifact should therefore be representable as a derivation rather than merely being described in prose.

## Mode catalogue

corpus/mode_registry.yaml records the historical catalogue independently of implementation.

The registry records the expected catalogue size of 67 but is intentionally partial until clean readings of OCR-corrupted names are checked. Catalogue presence, structural classification, executable support, and verified examples are separate states.

## Migration rule

Existing direct-pipeline methods remain valid. Migrate a method to a historical mode only when the source supports the higher-level structure.

Do not create one Python class per named spirit. If many modes differ only in parameters or modifiers, that compression should be visible in the corpus.

## Remaining deliberate gaps

The architecture has places for, but does not yet claim semantics for:

- syllable segmentation;
- oblique process;
- scattering and transposition parameters;
- half-line selection;
- color/glyph channels;
- day/night effects;
- attendant counts;
- signs and numerical fields;
- the twelve modes Selenus reports not understanding;
- Book III table semantics.

Unknown historical answers should remain explicit holes in the corpus, not implicit guesses in Python.
