# Reply to Review 2: Minimizer Category Consolidation Plan

Reply to
[`minimizer-category-consolidation_review-2.md`](minimizer-category-consolidation_review-2.md)
for the plan at
[`minimizer-category-consolidation.md`](minimizer-category-consolidation.md).

This reply follows
[`.github/copilot-instructions.md`](../../../.github/copilot-instructions.md).

For each finding: judgement, action taken in the updated plan, and a
pointer to the affected plan section.

## Findings

### P1 — P1.12 cannot pass as written

**Verdict: agree.** P1.12 demanded empty greps under `src/`, `tests/`,
and `docs/docs/tutorials/`, but the tutorial migration is P1.13 and
the test migration is P2.1a. The verification could not be satisfied
without doing those later steps prematurely.

**Action.** P1.12 verifications are now scoped to `src/` only. The
step explicitly notes that:

- `docs/docs/tutorials/` is re-checked at the end of **P1.13**.
- `tests/` is re-checked at the end of **P2.1a**.
- **P1.15** (the Phase 1 review gate) is the point where the
  full-project sweep must be clean.

This matches the actual ordering of work without weakening the
guarantee — the same three greps still have to come up empty before
Phase 2 starts.

### P1 — Shared descriptor bases contradicted "no mixins"

**Verdict: agree.** Review 1 prompted me to introduce
`LeastSquaresMinimizerBase` and `BayesianMinimizerBase` with "shared
descriptor declarations". That directly contradicts ADR §8 "No
mixins" and the plan's own statement that each concrete class
declares its descriptors in its own class body.

**Action.** Both intermediates are now **behavior-only**:

- They hold helper methods (`_native_kwargs()`, `_run_solver()`) and
  expected-descriptor-name class constants for the factory and the
  coverage check.
- No descriptor instances live on the bases.
- Every concrete class declares every descriptor in its own class
  body with class-specific defaults. Two LSQ classes ending up with
  identically-named descriptors is deliberate duplication; ADR §8
  rejects the alternative (mixins / inherited declarations).

Affected sections:
[`Decisions added after Review 2`](minimizer-category-consolidation.md#decisions-added-after-review-2),
the *Created* file list (intermediates are described as
behavior-only with the expected-name constants), and step **P1.4**.

### P2 — Stale-reference regex missed singular CIF tags

**Verdict: agree.** The previous greps used only the plural Python
module names (`bayesian_distribution_caches`, etc.). Source code
also references the singular CIF/category codes
(`_bayesian_distribution_cache`, `_bayesian_pair_cache`,
`_bayesian_predictive_dataset`, `_bayesian_parameter_posterior`).
The verification could pass while stale references remained.

**Action.** Both P1.12 and P2.1a now use the broader
`git grep -n 'bayesian_'` term, which catches both plural module
paths and singular category codes in one pass. The P1.12 step
explicitly enumerates the singular forms in the body text so future
reviewers can see that they are intentionally covered.

### P2 — Bare-tag alias decision timed incorrectly

**Verdict: agree.** I wrote "capture the decision at the P1 review
gate before P1.4 lands", but the only review gate is P1.15, after
P1.4. The caveat was therefore unreachable.

**Action.** Removed the caveat and committed to all nine
`MinimizerTypeEnum` tags getting a dedicated concrete class. If
later product feedback prefers aliasing the bare tags into their
explicit variants, that is a separate suggestion ADR rather than a
within-plan decision. Recorded under
[`Decisions added after Review 2`](minimizer-category-consolidation.md#decisions-added-after-review-2)
in the plan.

## Minor

**P1.11a vs P1.10a label in reply-1.**

**Verdict: agree.** The reply-1 file referred to the deterministic-
result migration as P1.11a; the plan calls it P1.10a.

**Action.** Edited
[`minimizer-category-consolidation_reply-1.md`](minimizer-category-consolidation_reply-1.md)
so the cross-reference matches the plan.

## Verification

This reply is a static one. No tests were run. Phase 2 of the updated
plan runs the standard `pixi run fix`, `check`, `unit-tests`,
`integration-tests`, `script-tests` commands with the zsh-safe
log-capture pattern.
