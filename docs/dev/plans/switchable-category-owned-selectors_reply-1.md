# Reply to Review 1: Switchable Category Owned Selectors Plan

Reply to
[`switchable-category-owned-selectors_review-1.md`](switchable-category-owned-selectors_review-1.md)
for the plan at
[`switchable-category-owned-selectors.md`](switchable-category-owned-selectors.md).

This reply follows
[`.github/copilot-instructions.md`](../../../.github/copilot-instructions.md).

All four findings are accepted and applied. Per the operating
parameters set by the user when the polling loop was started, every
finding is auto-applied without pausing for discussion.

## Findings

### F1 — Peak canonicalization missing context and naming the wrong helper

**Verdict: agree.** P1.5 named a `_canonicalize_peak_profile_type`
helper that doesn't exist (the actual canonicalization API is
[`PeakFactory._canonical_tag_for(...)`](../../../src/easydiffraction/datablocks/experiment/categories/peak/factory.py))
and would have passed only `beam_mode` into it. Peak aliases need
the full context — `scattering_type` + `beam_mode` for Bragg
profiles, `scattering_type` alone for Total profiles. The current
owner-level setter already collects the full context via
[`self._peak_profile_context()`](../../../src/easydiffraction/datablocks/experiment/item/base.py).

**Action.** Rewrote P1.5's `_canonicalize` bullet to delegate to
`PeakFactory._canonical_tag_for(...)` with
`self._parent._peak_profile_context()` (which returns
`calculator`, `scattering_type`, `beam_mode`, `sample_form`).
Spelled out why beam-mode alone is insufficient. Also fixed the
matching bullet in the "Modified" file list at the top of the plan.

### F2 — Collection-level `_type` should not merge into `parameters`

**Verdict: agree.**
[`CategoryCollection.parameters`](../../../src/easydiffraction/core/category.py)
is documented as "all parameters from all items in this
collection" and is consumed by owner-level parameter scans and
loop-column logic
([`io/cif/serialize.py:254`](../../../src/easydiffraction/io/cif/serialize.py),
[`io/cif/serialize.py:964`](../../../src/easydiffraction/io/cif/serialize.py)).
Merging a collection scalar into `parameters` would alter that
contract across every collection, not just background.

**Action.** Rewrote P1.2 to add a **separate** collection-scalar
access surface (e.g. `CategoryCollection.scalar_descriptors` /
`_collection_scalars`) that is consulted only by the CIF
serializer/deserializer. `CategoryCollection.parameters` stays
unchanged. The serializer emits the scalar above the loop; the
reader peeks the scalar before iterating items. Implementation
notes in the step quote the relevant line numbers
(`category_collection_to_cif` line 244, reader at line 964).

### F3 — Calculator factory naming collision after the rename

**Verdict: agree.** Two factories exist in the area:
- Backend factory:
  [`easydiffraction.analysis.calculators.factory.CalculatorFactory`](../../../src/easydiffraction/analysis/calculators/factory.py)
  — creates the live calculator engine (cryspy/crysfml/pdffit).
- Category factory: currently
  [`easydiffraction.datablocks.experiment.categories.calculation.factory.CalculationFactory`](../../../src/easydiffraction/datablocks/experiment/categories/calculation/factory.py)
  — creates the singleton category instance.

The plan said "use `CalculatorFactory.create(...)`" without
disambiguating; after the rename to `categories/calculator/`, the
two factories would have the same class name.

**Action.** Updated P1.8 to name the category factory
**`CalculatorCategoryFactory`** explicitly, and to document the two
roles side by side (category-factory vs backend-factory). The
backend `CalculatorFactory` keeps its name; only the category
factory is renamed during the move. The `_swap_calculator` body now
uses unambiguous wording — "rebinds the live backend
`experiment._calculator` via the existing **backend**
`CalculatorFactory.create(...)`".

### F4 — P1.9 broke atomic-commit-buildability by deferring consumer migration

**Verdict: agree.** The plan requires each Phase 1 step to land as
a single atomic commit, but P1.9 was going to delete
`project.rendering` while leaving consumers in
[`src/easydiffraction/__main__.py:87`](../../../src/easydiffraction/__main__.py),
[`src/easydiffraction/analysis/analysis.py:1636`](../../../src/easydiffraction/analysis/analysis.py),
and multiple sites in
[`src/easydiffraction/project/display.py`](../../../src/easydiffraction/project/display.py)
pointing at the removed surface, with cleanup deferred to P1.12.
The branch would have been broken between those commits.

**Action.** Expanded P1.9 into a single atomic commit that
explicitly includes the consumer migration. Listed the known
consumer sites verbatim with the translation rule
(`project.rendering.plotter` → `project.chart.plotter` etc.) and
added a pre-stage grep that must return empty before the commit
is staged:

```
git grep -nE '\bproject\.rendering\b|\brendering\.(plotter|tabler|chart_engine|table_engine)\b' src/
```

P1.12's "remove stragglers" line is reduced to a verification step
since P1.9 already does the cleanup.

## Verification

This reply is a static one. No tests, lint, build, formatting, or
`pixi` commands were run, matching the reviewer's own constraint
and the polling-loop operating parameters. Markdown files in this
review cycle were also not run through `prettier`, per
[`.github/copilot-instructions.md`](../../../.github/copilot-instructions.md)
→ **Change Discipline**.

## Summary of files touched by this reply

- [`docs/dev/plans/switchable-category-owned-selectors.md`](switchable-category-owned-selectors.md)
  — P1.2 rewritten for separate scalar access surface; P1.5
  rewritten for full peak-profile context; P1.8 renames the
  category factory to `CalculatorCategoryFactory` and disambiguates
  vs the backend factory; P1.9 expanded to a single atomic commit
  covering consumer migration; the "Modified" file list's peak
  bullet matches the new P1.5 wording; P1.12's `project.rendering`
  bullet reduced to verification.
- [`docs/dev/plans/switchable-category-owned-selectors_reply-1.md`](switchable-category-owned-selectors_reply-1.md)
  — this file.

Both left uncommitted in the worktree per the loop operating
parameters; the user will commit when they choose.
