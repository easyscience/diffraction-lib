# Reply to Review 3: Minimizer Category Consolidation Plan

Reply to
[`minimizer-category-consolidation_review-3.md`](minimizer-category-consolidation_review-3.md)
for the plan at
[`minimizer-category-consolidation.md`](minimizer-category-consolidation.md).

This reply follows
[`.github/copilot-instructions.md`](../../../.github/copilot-instructions.md).

For each finding: judgement, action taken in the updated plan, and a
pointer to the affected plan section.

## Findings

### P1 — P1.10a contradicted the behavior-only-base decision

**Verdict: agree.** I asked the deterministic-result fields to live on
`LeastSquaresMinimizerBase` "so every LSQ concrete class inherits them",
which is exactly the inherited-descriptor-declaration pattern Review 2
(and ADR §8) had just rejected.

**Action.** Rewrote
[`P1.10a`](minimizer-category-consolidation.md#implementation-steps-phase-1).
Each of the eight LSQ concrete classes now declares the absorbed
descriptors (`optimizer_name`, `method_name`, `objective_name`,
`objective_value`, `n_data_points`, `n_parameters`, `n_free_parameters`,
`degrees_of_freedom`, `covariance_available`, `correlation_available`,
plus runtime outputs) directly in its own class body, with the same
defaults the current `DeterministicResult` uses.
`LeastSquaresMinimizerBase` keeps only the `_expected_descriptor_names`
constants the factory uses for the P1.4 coverage assertion — no
descriptor instances. This matches the "behavior-only intermediates"
rule recorded under
[`Decisions added after Review 2`](minimizer-category-consolidation.md#decisions-added-after-review-2).

### P1 — P1.15 cannot confirm a full-project sweep before Phase 2

**Verdict: agree.** P1.12 correctly scopes the source sweep to `src/`
and defers tests to P2.1a, but the closing line of P1.12 still claimed
P1.15 would confirm the full-project sweep — which cannot happen because
P1.15 runs before P2.1a.

**Action.** Edited
[`P1.15`](minimizer-category-consolidation.md#implementation-steps-phase-1):
the review gate now re-runs the targeted greps against the **Phase 1
scopes only** (`src/` and `docs/docs/tutorials/`). The `tests/` sweep
explicitly belongs to P2.1a, which is the step that migrates them. I
also dropped the misleading "before Phase 2 starts" sentence from P1.12.

### P1 — `git grep -n 'bayesian_' src/` was too broad

**Verdict: agree.** The broad term would have flagged legitimate
Bayesian helper symbols such as `_format_bayesian_overall_status` in
`src/easydiffraction/analysis/fit_helpers/bayesian.py` (and a matching
test under `tests/integration/fitting/test_bayesian_helper_support.py`).
The ADR removes the `bayesian_*` _categories_, not the fitting concept
or its helpers.

**Action.** Replaced the broad grep in both P1.12 and P2.1a with three
targeted patterns (and a fourth for the show-method renames in
tutorials/tests):

```
git grep -nE 'analysis\.bayesian_|categories\.bayesian_|categories/bayesian_|_bayesian_(sampler|result|convergence|parameter_posterior|distribution_cache|pair_cache|predictive_dataset)' <scope>
git grep -nE 'analysis\.deterministic_result|categories\.deterministic_result|categories/deterministic_result|_deterministic_result\.' <scope>
git grep -nE 'analysis\.fitting\b|categories\.fitting\b|categories/fitting/' <scope>
git grep -nE 'show_minimizer_types|show_fitting_mode_types' <scope>
```

P1.12 explicitly notes that `_fitting.minimizer_type` and
`_fitting.mode_type` CIF tags are kept by the ADR, so the `fitting` grep
does not chase those.

### P1 — Tutorial migration missed `ed-8.py` and `ed-20.py`

**Verdict: agree.** `git grep` against the live tutorials confirms both
files call `project.analysis.show_fitting_mode_types()`. P1.13 omitted
them, and the post-P1.13 sweep did not look for
`show_fitting_mode_types` / `show_minimizer_types`, so the stale calls
could have survived all the way to script tests.

**Action.** Updated
[`P1.13`](minimizer-category-consolidation.md#implementation-steps-phase-1):

- File list now reads `ed-2.py`, `ed-3.py`, `ed-4.py`, **`ed-8.py`**,
  `ed-15.py`, `ed-17.py`, **`ed-20.py`**, `ed-21.py`, `ed-22.py`.
- Post-edit sweep added a dedicated `show_minimizer_types` /
  `show_fitting_mode_types` grep against `docs/docs/tutorials/` on top
  of the targeted category greps.

### P1 — P1.1a did not handle `fit_helpers/bayesian.py` itself

**Verdict: agree.** Removing the local `PosteriorParameterSummary`
dataclass from `analysis/fit_helpers/bayesian.py` without adding an
import would break every intra-module use of the name (the `SummaryList`
type alias at line 190, the function return-type annotations, the
constructor call near line 473, …).

**Action.** Extended
[`P1.1a`](minimizer-category-consolidation.md#implementation-steps-phase-1)
to list `analysis/fit_helpers/bayesian.py` as one of the files updated
in the same commit, with explicit instruction to replace the local
dataclass definition with
`from easydiffraction.core.posterior import PosteriorParameterSummary`.
Added a closing `git grep -n 'PosteriorParameterSummary' src/`
verification: every remaining hit must either be inside
`core/posterior.py` (the definition) or import it from there.

## Verification

This reply is a static one. No tests were run. Phase 2 of the updated
plan runs the standard `pixi run fix`, `check`, `unit-tests`,
`integration-tests`, `script-tests` commands with the zsh-safe
log-capture pattern.
