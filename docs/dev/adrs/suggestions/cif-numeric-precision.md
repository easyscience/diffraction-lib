# ADR: Meaningful Numeric Precision in CIF Serialization

**Status:** Proposed **Date:** 2026-06-02

## Group

Core model.

> This ADR follows [`AGENTS.md`](../../../../AGENTS.md). It is the
> data-side counterpart to
> [`plotting-docs-performance.md`](../accepted/plotting-docs-performance.md), which
> handles **display** precision (downcasting plot arrays to float32).
> This ADR concerns the precision of numbers we **store and serialize**
> in CIF, which is a separate decision because CIF is a data
> source-of-truth, not a throwaway view.

## Context

Numbers written to CIF (and to the figure data derived from them) carry
far more digits than is meaningful. Calculated intensities, profile
points, and derived quantities are serialized at essentially full
float64 precision (~15–17 digits), even though only a few digits are
significant. Two costs follow:

1. **File and payload bloat.** Profile arrays dominate CIF size and the
   embedded plot data (a single powder pattern serialized at full
   precision is hundreds of KB of digits that nobody reads).
2. **Meaningless precision.** A calculated intensity printed as
   `1234.5678901234567` implies a precision the calculation does not
   have, and a _fixed_ number of decimals is wrong at both ends of the
   scale (it over-prints small values and under-prints large ones).

The right notion is **relative precision** — significant figures tied to
the value's actual significance — not a fixed decimal count. For refined
parameters the significance is already known: the standard uncertainty
(s.u.).

**Important boundary.** Precision needed to _restore fit state_
(reload-and-continue) is not the same as precision a human or a
publication needs. Any reduction must not silently break round-tripping
of state files. See **Risks**.

## Options considered

| #   | Option                                                      | Adapts to scale? | Best for                               | Notes                                                                                                                                 |
| --- | ----------------------------------------------------------- | ---------------- | -------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| A   | Status quo — full float64 repr                              | n/a              | nothing                                | Baseline; bloated, meaningless precision.                                                                                             |
| B   | Fixed decimal places (`%.4f`)                               | ❌               | nothing                                | Wrong at both ends of the scale.                                                                                                      |
| C   | Significant figures (`%.Ng`)                                | ✅               | derived/calculated values without s.u. | Simple, relative precision; the elegant default.                                                                                      |
| D   | Uncertainty-aware (IUCr/GUM): quote value to match its s.u. | ✅               | refined parameters **with** s.u.       | `1.2345(12)`; the crystallographic standard.                                                                                          |
| E   | Range/variation-based (per array)                           | ✅               | profile/array data (calc patterns)     | Pick the quantum from the array's dynamic range so the step is below the meaningful/visual threshold. The idea raised in discussion.  |
| F   | Per-tag policy (dictionary-driven)                          | ✅               | everything, centrally                  | Different tags need different precision; drive defaults from the CIF dictionary (`cif_core.dic`) where it specifies a type/precision. |
| G   | float32 for arrays (display only)                           | ✅               | the plot path                          | Already adopted for the docs view in the plotting ADR; not a CIF-storage change.                                                      |

## Decision (proposed — direction, not yet locked)

A layered policy, applied at CIF serialization:

1. **Refined parameters with an s.u. → uncertainty-aware (D).** Print
   the value to the precision implied by its s.u. (IUCr convention).
   This is both correct and concise, and it is what scientists expect.
2. **Derived/calculated scalars without s.u. → significant figures
   (C).** A sensible default (e.g. 6 s.f.), configurable.
3. **Profile/array data → range-aware significant figures (E).** Choose
   the per-array precision from its dynamic range so the quantization is
   invisible (and pair with float32 on the display side, option G).
4. **Central policy object (F).** One place defines the default s.f. and
   per-category/per-tag overrides, seeded from the CIF dictionary where
   it constrains a tag. No scattered `round()` calls. Aligns with the
   memory that the dictionaries (`cif_core.dic`, `cif_pow.dic`) are the
   spec.
5. **Two precision profiles.** A **human/published** profile (concise,
   the above) and a **state-restore** profile (full precision) for files
   whose job is to reproduce a fit exactly. The active profile is chosen
   by the writer, not guessed.

This keeps stored numbers meaningful and small without risking
reproducibility, and gives the docs/plots smaller inputs at the source.

## Consequences

### Positive

- Smaller CIF files and smaller derived plot payloads, at the source.
- Numbers convey real significance (s.u.-matched), aiding readability
  and publication.
- One precision policy instead of ad-hoc formatting.

### Negative / cost

- A precision policy and per-tag configuration to design and maintain.
- Tests that assert exact serialized strings must move to
  tolerance-based comparisons.
- The human-vs-state-restore split must be explicit everywhere CIF is
  written.

## Risks and mitigations

- **Round-trip / fit restart.** Reducing precision on a file used to
  restore state can change results. _Mitigation:_ the state-restore
  profile keeps full precision; only human/published output is reduced.
  Cover with a save→load→save round-trip test on the state profile.
- **Reproducibility / regression diffs.** Existing golden-file tests and
  CIF diffs assume exact digits. _Mitigation:_ update them to the policy
  and tolerance comparisons in the same change.
- **Over-aggressive rounding.** Choosing too few s.f. for coordinates or
  cell parameters loses science. _Mitigation:_ per-tag floors from the
  dictionary; conservative defaults.

## Open questions

1. Default significant-figure count for the human profile (5? 6?).
2. Whether the policy is per-`CategoryItem`, per-tag, or both.
3. How to source per-tag precision from `cif_core.dic` (does it specify
   enough), versus a hand-maintained table.
4. Whether to expose the active profile to users (e.g.
   `project.save(..., precision='full' | 'concise')`).

## Alternatives considered

See **Options A–G**. A (status quo) and B (fixed decimals) are rejected.
G (float32 arrays) is display-only and already handled by the plotting
ADR; it is complementary, not a substitute, for storage precision.

## Deferred work

- Binary/columnar storage for large profile arrays (e.g. HDF5 datasets
  with an explicit dtype) instead of text CIF, where round-tripping
  exact arrays matters and text is the wrong container.
