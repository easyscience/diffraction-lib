# Reply to Review 8: Minimizer Category Consolidation Plan

Reply to
[`minimizer-category-consolidation_review-8.md`](minimizer-category-consolidation_review-8.md)
for the plan at
[`minimizer-category-consolidation.md`](minimizer-category-consolidation.md).

This reply follows
[`.github/copilot-instructions.md`](../../../.github/copilot-instructions.md).

Context: the plan's Phase 1 and Phase 2 are both marked complete and
the branch is structurally ready. Review 8 is a post-Phase-2 static
read of `develop` vs the implemented branch. All findings are agreed,
but none was raised as a blocker. Per the reviewer's own
"Recommended next steps" the actions split into:

- F2, F3, F5, F6 — recommended to address in *this PR* before merge.
- F1, F4, F7, F10 — refactor candidates to fold into the
  [`emcee-minimizer.md`](emcee-minimizer.md) plan while it touches
  surrounding code.
- F8 — informational, leave as-is.
- F9 — corner-case edge bug worth tracking but not urgent.

Action this round (after user direction "Fix all of them — F2, F3, F5,
F6"): the four PR-recommended findings are fixed in this PR as
Phase-2 follow-up steps P2.6–P2.9 (see the plan). The remaining
actionable findings (F1, F4, F7, F9, F10) become priority-tagged
entries in [`docs/dev/issues/open.md`](../issues/open.md);
the four refactor candidates (F1, F4, F7, F10) are also referenced
from the emcee plan.

For each finding: verdict, action taken, and the pointer.

## Findings

### F1 — Duplicate predictive-cache-key helpers

**Verdict: agree.** `Analysis._predictive_cache_key`
([analysis.py:478-487](../../../src/easydiffraction/analysis/analysis.py))
and `Plotter._posterior_predictive_key`
([plotting.py:3795-3804](../../../src/easydiffraction/display/plotting.py))
both build `f'{name}:{x_axis_name}:{suffix}'`. The strings line up
today; a future edit to one would silently break lookup against the
other.

**Action.** Added [open-issue 100](../issues/open.md) and referenced
it from the emcee plan's new "Cleanup opportunities inherited from
the consolidation plan" section.

### F2 — Sidecar enum comparison is string-based

**Verdict: agree.** `results_sidecar.py:43-46` `_should_use_sidecar`
compares `result_kind.value == 'bayesian'` instead of dereferencing
`FitResultKindEnum.BAYESIAN.value`. Violates
[`.github/copilot-instructions.md`](../../../.github/copilot-instructions.md)
→ **Architecture** ("compare against members, not raw strings").

**Action.** Fixed in this PR as **P2.6**. `results_sidecar.py` now
imports `FitResultKindEnum` and `_should_use_sidecar` compares to
`FitResultKindEnum.BAYESIAN.value`.

### F3 — Swap warning text shows `'<not available>'`

**Verdict: agree.** `Analysis._changed_minimizer_defaults`
renders fields that exist on only one family as the literal
`'<not available>'`. Inter-family swaps produce a wall of
`burn_in_steps '<not available>'->600, max_iterations 1000->'<not available>'`
that the scientist audience will read as a bug. The warning fires
on every inter-family swap, so the cosmetic upgrade is
high-visibility.

**Action.** Fixed in this PR as **P2.7**. The warning now reads as
"Settings removed: …" plus "Settings added with defaults: …" on
inter-family swaps; same-family swaps still show the per-field
`old->new` diff.

### F4 — `_fit_state_categories` has both branches returning the same list

**Verdict: agree.** Dead conditional left over from the pre-P1.10
Bayesian-projection shape.

**Action.** Added [open-issue 101](../issues/open.md) and referenced
from the emcee plan's cleanup section (touching adjacent code).

### F5 — Restore path reaches Bayesian-only fields without category-type check

**Verdict: agree.** `_restore_fit_results_from_projection`
gates on `result_kind == 'bayesian'`, but a hand-edited or stale CIF
with `result_kind = bayesian` but `minimizer_type = lmfit (leastsq)`
crashes with
`AttributeError: 'LmfitLeastsqMinimizer' object has no attribute 'point_estimate_name'`.
Violates ADR §5 ("Loading a CIF whose tags don't match the
minimizer's allowed set raises clear validation") and CLAUDE.md →
"clear errors, safe defaults".

**Action.** Fixed in this PR as **P2.8**. CIF restore now raises a
clear `ValueError` if `_fit_result.result_kind == 'bayesian'` but
the active `analysis.minimizer` is not a `BayesianMinimizerBase`.
The error names both the persisted `minimizer_type` and the
expected family.

### F6 — LSQ result descriptors mix `0` and `None` defaults

**Verdict: agree.** `LeastSquaresMinimizerBase._integer_result_descriptor`
uses `default=0` while `_numeric_result_descriptor` uses
`default=None, allow_none=True`. A CIF written before any fit shows
`_minimizer.n_data_points 0` and `_minimizer.covariance_available false`,
which a scientist will read as "the fit produced a degenerate result"
rather than "no fit has happened yet". The Bayesian side already
uses `None` consistently; aligning LSQ is the lower-friction fix.

**Action.** Fixed in this PR as **P2.9**. The integer and boolean
LSQ result descriptors now use `default=None, allow_none=True`
matching the numeric and Bayesian conventions; the CIF round-trip
emits `?` for unset fields, which readers resolve back to the
descriptor's static default (and stays `None` here).

### F7 — `_restore_persisted_fit_state` computes but does not use `result_kind`

**Verdict: agree.** `FitResultKindEnum(result_kind_value)` is called
only for the `ValueError` side effect; the constructed enum is
discarded. Same shape as the F4 dead branch.

**Action.** Added [open-issue 102](../issues/open.md) and referenced
from the emcee plan's cleanup section.

### F8 — `Analysis` eagerly imports `BayesianFitResults` / `PosteriorSamples`

**Verdict: agree (informational).** The reviewer themself flags this
as not a defect — eager imports are the
[`.github/copilot-instructions.md`](../../../.github/copilot-instructions.md)
→ **Architecture** default. Recording the trade-off so the next
sampler can decide consciously.

**Action.** No open-issue entry; no code change. If a future import-
time profile motivates lazy loading, that's a single deferred
follow-up worth its own ADR / plan rather than a tracked TODO.

### F9 — `FitParameterItem.posterior_summary` returns NaN-filled summaries on partial data

**Verdict: agree.** A CIF row with only `posterior_gelman_rubin`
set (e.g. partial hand edit, future bug) builds a
`PosteriorParameterSummary` whose `median`, `standard_deviation`,
and both interval bounds are `NaN`. Downstream plotting and
`display.fit_results` render NaN intervals — harder to debug than a
clean "no posterior".

**Action.** Added [open-issue 104](../issues/open.md) with both
fix shapes (tighten `has_posterior_summary` to require core stats;
or split the dataclass into required vs optional components).
Not flagged for this PR — only fires under corrupted input.

### F10 — `_sync_engine_from_minimizer_category` excludes `random_seed` via magic string

**Verdict: agree.** `if key == 'random_seed': continue` is correct
behaviour but doesn't scale. The emcee plan adds `proposal_moves`,
which is also an engine-level ambient key.

**Action.** Added [open-issue 103](../issues/open.md) (declare
`_engine_sync_skip_keys: ClassVar[frozenset[str]]` on
`MinimizerCategoryBase`) and referenced from the emcee plan's
cleanup section. The emcee plan should introduce the frozenset
before adding the second skip member.

## Verification

This reply is a static one. The reviewer's own §"Verification
commands run for this review" greps all pass (four removed-category
greps return empty across `src/`, `docs/docs/tutorials/`, and
`tests/`; the P1.4 enum-coverage grep lists all nine members).

No `pixi run` was executed for this reply. The implementer must run
`pixi run fix`, `pixi run check`, `pixi run unit-tests`,
`pixi run integration-tests`, and `pixi run script-tests` before
merging, as the reviewer recommends.

## Summary of files touched by this reply

- [`docs/dev/issues/open.md`](../issues/open.md) — added entries 100
  through 104 (F1, F4, F7, F9, F10). F2, F3, F5, F6 are not tracked
  in `open.md`: they are fixed in this PR via plan steps P2.6–P2.9.
  F8 stays unrecorded (informational).
- [`docs/dev/plans/emcee-minimizer.md`](emcee-minimizer.md) — added a
  "Cleanup opportunities inherited from the consolidation plan"
  section listing F1, F4, F7, F10 as fold-in candidates.
- [`docs/dev/plans/minimizer-category-consolidation.md`](minimizer-category-consolidation.md)
  — added Phase-2 follow-up steps P2.6 through P2.9 covering F2, F3,
  F5, F6 (one commit per step, per the
  [`.github/copilot-instructions.md`](../../../.github/copilot-instructions.md)
  → **Commits** atomic-change rule).
- [`docs/dev/plans/minimizer-category-consolidation_reply-8.md`](minimizer-category-consolidation_reply-8.md)
  — this file.
