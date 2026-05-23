# Reply to Review 5: Minimizer Category Consolidation Plan

Reply to
[`minimizer-category-consolidation_review-5.md`](minimizer-category-consolidation_review-5.md)
for the plan at
[`minimizer-category-consolidation.md`](minimizer-category-consolidation.md).

This reply follows
[`.github/copilot-instructions.md`](../../../.github/copilot-instructions.md).

For each finding: judgement, action taken in the updated plan, and a
pointer to the affected plan section.

## Findings

### P1 — P1.1a still contained the strict verification

**Verdict: agree.** Review 4 promised a relaxed two-grep check, but the
editor's auto-format pass between rounds reverted that edit. The plan
still carried the strict
`git grep -n 'PosteriorParameterSummary' src/ …` block, which a correct
implementation would fail (the use-sites in
`analysis/fit_helpers/bayesian.py` are neither the definition nor import
statements).

**Action.** Re-applied the relaxed verification in
[`P1.1a`](minimizer-category-consolidation.md#implementation-steps-phase-1)
and re-verified with `grep` that the new block survived:

1. `git grep -n '^class PosteriorParameterSummary' src/` must list
   exactly one file — `src/easydiffraction/core/posterior.py`.
2. ```
   git grep -l 'PosteriorParameterSummary' src/ \
     | grep -v 'core/posterior\.py$' \
     | xargs -r grep -L 'from easydiffraction.core.posterior import PosteriorParameterSummary'
   ```
   must return empty — every other file that mentions the name also
   imports it from `core.posterior`. Use-sites are explicitly allowed.

I'll spot-check that the two-grep block is still present any time I
respin the plan after a formatter touches it.

### P1 — P1.12 missed private Bayesian owner attributes

**Verdict: agree.** The dedicated `analysis.py` grep covered
`self.bayesian_*` (public) and `self._fitting` /
`self._deterministic_result` (private), but not `self._bayesian_*`. The
current `analysis.py` lines ~451 and ~524–530 carry every one of:

```
self._bayesian_sampler
self._bayesian_result
self._bayesian_convergence
self._bayesian_parameter_posteriors
self._bayesian_distribution_caches
self._bayesian_pair_caches
self._bayesian_predictive_datasets
```

Without them in the grep, the public properties could be removed while
their private storage / reset code silently survives.

**Action.** Extended the dedicated grep in
[`P1.12`](minimizer-category-consolidation.md#implementation-steps-phase-1)
with a
`\bself\._bayesian_(sampler|result|convergence|parameter_posteriors|distribution_caches|pair_caches|predictive_datasets)\b`
alternation, mirroring the public-attribute alternation.

### P2 — Missing "Decisions added after Review 4" section

**Verdict: agree.** Reply 4 said the kept-vs-removed engine-module
decision lived under `Decisions added after Review 4`, and both P1.12
and P2.1a cross-referenced that section by name. The same auto-format
pass that reverted P1.1a also dropped the section heading, so the
cross-references resolved to nothing.

**Action.** Restored the section between
`Decisions added after Review 2` and `Concrete files likely to change`.
Captures the two decisions verbatim:

- The engine module `src/easydiffraction/analysis/fitting.py` is kept;
  the deletion targets the Python category surface only.
- `tests/unit/easydiffraction/analysis/test_fitting.py` is kept and only
  its category-surface assertions are migrated.

Verified with `grep -n 'Decisions added after Review'`:

- Line 73 — Review 2 decisions
- Line 90 — Review 4 decisions
- Lines 493 / 627 — P1.12 / P2.1a cross-references now resolve.

## Verification

This reply is a static one. No tests were run. Phase 2 of the updated
plan runs the standard `pixi run fix`, `check`, `unit-tests`,
`integration-tests`, `script-tests` commands with the zsh-safe
log-capture pattern.
