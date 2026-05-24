# Reply to Review 1: Minimizer Input/Output Split

Reply to
[`minimizer-input-output-split_review-1.md`](minimizer-input-output-split_review-1.md)
for the ADR at
[`minimizer-input-output-split.md`](minimizer-input-output-split.md).

This reply follows
[`.github/copilot-instructions.md`](../../../.github/copilot-instructions.md).

All five findings agreed. Each was addressed by editing the ADR text;
no item is deferred. The ADR is updated in the same commit as this
reply.

## Findings

### Finding 1 — Switchable category contract violation

**Verdict: agree.** The original text used the defined term
"switchable category" (per the accepted selector ADR) but then said
`fit_result` would not expose `type` or `show_supported()` — which is
precisely what the selector contract requires. The selector ADR was
also missing from the amended-ADR list.

**Action taken.** Rewrote §1 so the paired result class is described
as an **internal projection paired with the active minimizer**, not as
a switchable category. Explicit text: "It does not expose
`fit_result.type` or `fit_result.show_supported()`; the only way the
user changes the active `fit_result` class is by setting
`analysis.minimizer.type`." The exception to the global selector
contract is now documented in two places: (a) §1 of this ADR ("This is
an explicit, documented exception …"); (b) the new amended-ADR entry
for `switchable-category-owned-selectors.md`, which records the carve-
out: a category whose active class is fully determined by another
category's `type` may omit `type` and `show_supported()`. §6 ("No new
selector wiring") and §"Trade-offs" updated to match the new wording.

**Plan section:** §1 (rewritten), §6 (updated), §"Trade-offs"
(updated), §"ADRs amended" (added `switchable-category-owned-selectors.md`).

### Finding 2 — `objective_value`/`reduced_chi_square` inconsistency

**Verdict: agree.** The original text said "drop
`minimizer.objective_value`" with `reduced_chi_square` as the single
source, but the LSQ field list and the deterministic CIF example
included **both** — leaving an implementer free to drop or keep
`objective_value` and both claim ADR compliance.

**Action taken.** Rewrote the resolution bullet in §2 to state
explicitly that `objective_value` (raw χ²) and `reduced_chi_square`
(= χ² / `degrees_of_freedom`) are **distinct fields**, both kept on
`LeastSquaresFitResult`. The raw value is what the solver optimises
and is useful for diagnostics on small-dof fits; the reduced value is
what user-facing tables and plots display. `BayesianFitResult` does
not carry `objective_value` because the Bayesian engine optimises the
log posterior. The Positive-consequences bullet about "duplications"
no longer claims this pair was a duplication; only the
`runtime_seconds` and `iterations` pairs are real duplications, and
the bullet now says so.

**Plan section:** §2 (resolution bullet rewritten), §"Positive"
(bullet adjusted).

### Finding 3 — `credible_interval_*` semantics

**Verdict: agree.** The ADR listed
`credible_interval_inner/credible_interval_outer` as current writable
inputs and kept them on the settings-only `minimizer`, but in the
live code they have only internal `_set_*` and live in
`_result_descriptor_names`. The "settings-only minimizer" boundary
needed a clear answer for these two fields.

**Action taken.** Added a paragraph to §2 making the promotion
explicit: the two interval levels are **promoted from output-only to
writable input** by this ADR. They are set before `analysis.fit()`;
the Bayesian posterior-summary path reads them at fit time and
generates the per-parameter interval columns from those levels.
Documented that the column names stay numeric (`68`, `95`) for now —
mismatching user levels are warned about at fit time so the names do
not silently lie — and added a Deferred-Work entry to track a later
ADR that may generalise the column naming.

**Plan section:** §2 (new paragraph), §"Deferred Work" (new entry).

### Finding 4 — `analysis.show_fit_summary()` bypasses display facade

**Verdict: agree.** The accepted Display UX ADR moves user-facing fit
reporting to `project.display.fit.results()`. Adding a new
`analysis.show_fit_summary()` would reintroduce exactly the split that
ADR cleaned up, and `display-ux.md` was missing from the amended-ADR
list.

**Action taken.** Removed the new `analysis.show_fit_summary()`
method entirely. Replaced it with an extension to the existing
`project.display.fit.results()` entry point: it now prints a "Settings
used" block above the result tables, populated from
`analysis.minimizer.*`. No new public entry point is added. Added
`display-ux.md` to the amended-ADR list with a sentence describing
exactly this extension. §4 (runtime-object section) and
§"Trade-offs" updated to reference the display-facade method instead.

**Plan section:** §4 (updated paragraph), §"Trade-offs" (updated),
§"ADRs amended" (added `display-ux.md`).

### Finding 5 — Pairing table only names two classes

**Verdict: agree.** The original §1 paired `LmfitLeastsqMinimizer ↔
LeastSquaresFitResult` and `BumpsDreamMinimizer ↔ BayesianFitResult`
as examples. With nine `MinimizerTypeEnum` members today plus emcee
on the horizon, that left the swap/load behaviour underspecified for
non-default deterministic minimizers.

**Action taken.** Added a full mapping table to §1 listing every
current `MinimizerTypeEnum` member with its family and paired result
class, plus a row for `EMCEE` (when added). Added a sentence
documenting that the pairing rule is encoded once on the minimizer
base classes (`LeastSquaresMinimizerBase._fit_result_class =
LeastSquaresFitResult`, `BayesianMinimizerBase._fit_result_class =
BayesianFitResult`) so the swap hook reads the paired class off the
new minimizer instance and does not need a per-tag dispatch.

**Plan section:** §1 (new mapping table + pairing-rule paragraph).

## Verification

This is a static reply only. No `pixi run`, lint, build, formatter,
or test command was executed.

## Summary of files touched by this reply

- [`docs/dev/adrs/suggestions/minimizer-input-output-split.md`](minimizer-input-output-split.md)
  — ADR updated per all five findings above.
- [`docs/dev/adrs/suggestions/minimizer-input-output-split_reply-1.md`](minimizer-input-output-split_reply-1.md)
  — this reply.
