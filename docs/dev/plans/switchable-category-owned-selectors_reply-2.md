# Reply to Review 2: Switchable Category Owned Selectors Plan

Reply to
[`switchable-category-owned-selectors_review-2.md`](switchable-category-owned-selectors_review-2.md)
for the plan at
[`switchable-category-owned-selectors.md`](switchable-category-owned-selectors.md).

This reply follows
[`.github/copilot-instructions.md`](../../../.github/copilot-instructions.md).

All three findings are accepted and applied. Per the operating
parameters set by the user when the polling loop was started, every
finding is auto-applied without pausing for discussion.

## Findings

### F1 — P1.8 created a private-attribute collision between category and live backend

**Verdict: agree.** Reply 1 introduced wording that renamed
`self._calculation` → `self._calculator`, but
[`item/base.py:71`](../../../src/easydiffraction/datablocks/experiment/item/base.py)
already uses `self._calculator = None` for the live backend, and
[`item/base.py:214`](../../../src/easydiffraction/datablocks/experiment/item/base.py)
assigns `self._calculator = CalculatorFactory.create(tag)` when the
backend swaps. Two different responsibilities can't share the slot.

**Action.** P1.8 now spells out the post-rename layout explicitly:

- Public property `experiment.calculator` returns the **category**
  instance.
- Category slot is renamed `self._calculation` →
  **`self._calculator_category`** (note the `_category` suffix that
  disambiguates).
- Live-backend slot stays at `self._calculator` (unchanged).
- The mixin's staleness check `parent.calculator is self` works because
  the property returns the category.

Internal references to `self._calculation` throughout `ExperimentBase`
migrate to `self._calculator_category`. References to `self._calculator`
(the live backend) stay as-is.

### F2 — P1.5 overstated what `_peak_profile_context()` returns

**Verdict: agree.** Reply 1's P1.5 said `_peak_profile_context()`
returns `calculator`, `scattering_type`, `beam_mode`, `sample_form`. The
actual method at
[`item/base.py:618`](../../../src/easydiffraction/datablocks/experiment/item/base.py)
returns only `scattering_type` and `beam_mode`. The current owner-level
setter at
[`item/base.py:532`](../../../src/easydiffraction/datablocks/experiment/item/base.py)
passes those two keys into `PeakFactory._canonical_tag_for(...)`, which
is sufficient for alias canonicalization (Bragg vs Total, CWL vs TOF).
The broader 4-key context is what the **supported-types listing** filter
uses, not canonicalization.

**Action.** P1.5 now separates the two contexts explicitly:

- `_canonicalize(value)` → uses `self._parent._peak_profile_context()`
  (2 keys: `scattering_type`, `beam_mode`). Sufficient for alias
  resolution; matches the current owner-level setter's behavior.
- `_supported_types(filters)` → receives the broader 4-key dict
  (`calculator`, `scattering_type`, `sample_form`, `beam_mode`) from
  `_supported_filters_for(category)` on the owner. Used to filter the
  listing.

The step body and the matching bullet in the "Modified" file list at the
top of the plan both reflect this distinction.

### F3 — P2.1a pointed rendering tests at the wrong package path

**Verdict: agree.** `rendering` is a project category (under
`project/categories/rendering/`), not an experiment category
(`datablocks/experiment/categories/`). Reply 1's P2.1a deleted
`tests/unit/easydiffraction/datablocks/experiment/categories/rendering/`,
which doesn't exist. The real path is
`tests/unit/easydiffraction/project/categories/rendering/`.

**Action.** Updated P2.1a's "Delete" list to:

- Point at `tests/unit/easydiffraction/project/categories/rendering/`
  (the correct existing path) and replace it with sibling `chart/` and
  `table/` test directories.
- Also clarified the calculation tests' move:
  `tests/unit/easydiffraction/datablocks/experiment/categories/calculation/`
  moves to `categories/calculator/` via `git mv`, and
  `CalculationFactory` references become `CalculatorCategoryFactory` per
  P1.8's factory rename.

## Verification

This reply is a static one. No tests, lint, build, formatting, or `pixi`
commands were run. Markdown files in this review cycle were also not run
through `prettier`, per
[`.github/copilot-instructions.md`](../../../.github/copilot-instructions.md)
→ **Change Discipline**.

## Summary of files touched by this reply

- [`docs/dev/plans/switchable-category-owned-selectors.md`](switchable-category-owned-selectors.md)
  — P1.8 disambiguates `_calculator_category` (category) vs
  `_calculator` (live backend); P1.5 splits alias context (2 keys) from
  supported-types filter context (4 keys); P2.1a corrects rendering test
  path and adds calculation test rename note.
- [`docs/dev/plans/switchable-category-owned-selectors_reply-2.md`](switchable-category-owned-selectors_reply-2.md)
  — this file.

Both left uncommitted in the worktree per the loop operating parameters;
the user will commit when they choose.
