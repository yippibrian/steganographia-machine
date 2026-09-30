# Historical Mode Architecture

The linear pipeline remains the execution kernel. Historical descriptions compile into it.

## Layers

1. **Primitive stages** — `unitize`, `select`, `project`, `concatenate`, `normalize`.
2. **Schedules** — low-level masks or semantic schedules such as alternating idle/significant blocks.
3. **Mode families** — reusable historical structures such as `word_initials` and `block_word_initials`.
4. **Named historical modes** — configurations such as Padiel that bind family parameters.
5. **Methods** — a corpus method may contain either a direct pipeline or a historical `mode` definition.
6. **Cases** — bind a method to source and expected artifacts.

A historical mode is compiled before execution. This keeps the runtime small while preserving historically meaningful structure in corpus data.

## Example

```yaml
mode:
  name: Padiel
  family: block_word_initials
  parameters:
    idle_run: 1
    significant_run: 1
    starts_with: significant
  normalization:
    lowercase: true
    remove_whitespace: true
```

This compiles to the equivalent of:

```yaml
pipeline:
  - unitize: {unit: word}
  - select:
      schedule:
        type: alternating_blocks
        idle_run: 1
        significant_run: 1
        starts_with: significant
  - project: {part: initial}
  - concatenate: {}
  - normalize: {lowercase: true, remove_whitespace: true}
```

The semantic form is preferred when the historical evidence describes a mode as a member of a family. A literal `mask` remains available for low-level or source-neutral work.

## Trace semantics

Selection trace entries now distinguish:

- `significant`
- `idle`

and carry schedule state such as family, run lengths, and starting order. This makes the trace an evidentiary explanation rather than only a list of booleans.

## Boundary-sensitive deviations

Selenus describes later modes whose schedule changes when a hidden word ends. These are **not** represented as fixed masks. The schema may record modifiers, but compilation currently rejects them with an explicit error until stateful boundary execution is implemented.

That refusal is intentional. It prevents the corpus from silently approximating a historically stateful rule with a periodic mask.

## Migration rule

Existing direct-pipeline methods remain valid. Migrate a method to `mode` only when the historical source supports the higher-level structure. Do not rewrite every method merely for consistency.

## Next execution layer

The next extension should introduce boundary events and stateful modifiers while keeping hidden-word segmentation provenance explicit. A case must declare whether boundaries are:

- independently recoverable from the carrier,
- supplied by a historical key or reading,
- supplied only for encoding reconstruction,
- or unresolved.

Expected plaintext must never silently become decoder input.
