# Reply to Review 2: Minimizer Input/Output Split Plan

Reply to
[`minimizer-input-output-split_review-2.md`](minimizer-input-output-split_review-2.md)
for the plan at
[`minimizer-input-output-split.md`](minimizer-input-output-split.md).

This reply follows
[`.github/copilot-instructions.md`](../../../.github/copilot-instructions.md).

All three findings agreed. Each was addressed by editing the plan text
in the same commit as this reply.

## Findings

### Finding 1 — Removed output names treated as one-to-one renames

**Verdict: agree — would mis-migrate the two collapsed-name fields.**

The ADR collapses `runtime_seconds` onto the existing
`fit_result.fitting_time` and `iterations_performed` onto
`fit_result.iterations`. The original P1.15 and P2.1 said "replace each
`analysis.minimizer.<output_field>` with
`analysis.fit_result.<output_field>`" and used `_set_runtime_seconds` →
`_set_runtime_seconds` as the fixture example — both are wrong for those
two fields, where the target field and setter already exist under
different names on `FitResultBase`.

**Action taken.** Rewrote P1.15 with an explicit migration table
covering all 19 removed fields. The two collapsed rows are flagged with
a "Collapsed onto existing common field" note and point at the existing
`fit_result._set_fitting_time(...)` / `fit_result._set_iterations(...)`
setters. The other 17 rows are moved-but-keep-the-name relocations (e.g.
`analysis.minimizer.gelman_rubin_max` →
`analysis.fit_result.gelman_rubin_max`).

P2.1 was rewritten to point at the same migration table and to include
both setter-rename examples — moved-but-kept and collapsed — so test
fixtures get the right setter on each side.

**Plan section:** P1.15 (migration table added), P2.1 (examples
updated).

### Finding 2 — `_reset_result_descriptors()` not yet defined on `FitResultBase`

**Verdict: agree — Phase 1 wired a call to a method that did not exist
yet.**

The method lives on `MinimizerCategoryBase`
([`minimizer/base.py:69-74`](../../../src/easydiffraction/analysis/categories/minimizer/base.py))
and the existing `FitResult` class has no equivalent. Adding it only in
P1.2 / P1.3 (on the family classes) wouldn't help, because P1.6 calls it
on the union type `FitResultBase`. If P1.6 ran before the helper was
added, every `_clear_persisted_fit_state` reset would raise
`AttributeError`.

**Action taken.** Extended P1.1 to add two class-level hooks on
`FitResultBase` during the rename:

- `_result_descriptor_names: ClassVar[tuple[str, ...]]` initialised to
  the existing common fields (`success`, `message`, `iterations`,
  `fitting_time`, `reduced_chi_square`, `result_kind`).
- `_reset_result_descriptors()` implemented exactly as on
  `MinimizerCategoryBase` (walk `_result_descriptor_names`, reset to
  `_value_spec.default_value()`).

The family classes (P1.2 / P1.3) extend `_result_descriptor_names` with
their own field names so the inherited helper resets the full descriptor
set on the active paired class. The plan now ensures the helper is in
place before P1.6 wires the swap and reset retargeting.

**Plan section:** P1.1 (added hooks paragraph), P1.6 (already correct
now that the helper is guaranteed present).

### Finding 3 — CIF ordering steps contradicted each other

**Verdict: agree — P1.11 and P1.12 stated incompatible contracts.**

P1.11 claimed the order was enforced by `_serializable_categories`
putting `fit_result` directly after `minimizer`. P1.12 said
`_serializable_categories` already includes `fit_result` via
`_fit_state_categories`. The current code conditionally appends
`fit_result` only when `_has_persisted_fit_state()` is true, so
following P1.11 literally would make pre-fit projects emit a default
`_fit_result.*` block — a regression in CIF compactness.

**Action taken.** Rewrote both steps to pick the conditional contract:

- P1.11 now says the read-side order is **already correct** because
  `_set_minimizer_type` runs before `analysis.minimizer.from_cif` and
  the paired `fit_result` swap fires inside `_set_minimizer_type` after
  P1.6. The emit-side `_serializable_categories()` /
  `_fit_state_categories()` shape is preserved (conditional inclusion);
  explicit "do not promote `fit_result` to unconditional" instruction
  added.
- P1.12 now confirms that `_fit_state_categories()` returns the paired
  instance automatically once P1.6 wires the construction — no method
  body change needed.

**Plan section:** P1.11 (rewritten), P1.12 (rewritten).

## Verification

This is a static reply only. No `pixi run`, lint, build, formatter, or
test command was executed.

## Summary of files touched by this reply

- [`docs/dev/plans/minimizer-input-output-split.md`](minimizer-input-output-split.md)
  — plan updated per all three findings (P1.1, P1.11, P1.12, P1.15,
  P2.1).
- [`docs/dev/plans/minimizer-input-output-split_reply-2.md`](minimizer-input-output-split_reply-2.md)
  — this reply.
