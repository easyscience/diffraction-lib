# Reply to Review 4: Minimizer Category Consolidation Plan

Reply to
[`minimizer-category-consolidation_review-4.md`](minimizer-category-consolidation_review-4.md)
for the plan at
[`minimizer-category-consolidation.md`](minimizer-category-consolidation.md).

This reply follows
[`.github/copilot-instructions.md`](../../../.github/copilot-instructions.md).

For each finding: judgement, action taken in the updated plan, and a
pointer to the affected plan section.

## Findings

### P1 — P1.1a verification was too strict for use-sites

**Verdict: agree.** I asked every remaining
`PosteriorParameterSummary` hit under `src/` to be either the
definition or an import. That fails for legitimate use-sites in
`analysis/fit_helpers/bayesian.py` (the `SummaryList` type alias,
function signatures, the constructor call near line 473) — they are
neither the class definition nor an `import` line, but they are
correct.

**Action.** Rewrote the P1.1a verification block to two greps with
clearer intent:

1. `git grep -n '^class PosteriorParameterSummary' src/` must list
   exactly one file — `src/easydiffraction/core/posterior.py`. No
   second class definition is allowed.
2. For every other file under `src/` that mentions the name, the
   same file must also import it from
   `easydiffraction.core.posterior`:

   ```
   git grep -l 'PosteriorParameterSummary' src/ \
     | grep -v 'core/posterior\.py$' \
     | xargs -r grep -L 'from easydiffraction.core.posterior import PosteriorParameterSummary'
   ```

   must return empty.

Use-sites (annotations, alias declarations, constructor calls) are
allowed; they no longer trip the check. See
[`P1.1a`](minimizer-category-consolidation.md#implementation-steps-phase-1).

### P1/P2 — `analysis.fitting` grep conflated engine module with deleted category

**Verdict: agree.** `src/easydiffraction/analysis/fitting.py` is the
engine module containing the `Fitter` class — distinct from the
Python `analysis.fitting` *category surface* that this ADR removes.
The previous broad `analysis\.fitting\b` grep would have flagged
legitimate engine imports
(`from easydiffraction.analysis.fitting import Fitter`) and the
`test_fitting.py` engine test would have been deleted by mistake.

**Action.** Two changes:

1. Recorded the kept-vs-removed decision under
   [`Decisions added after Review 4`](minimizer-category-consolidation.md#decisions-added-after-review-4)
   in the plan:
   - `src/easydiffraction/analysis/fitting.py` is **kept**; only the
     Python category surface (`Fitting` category, `analysis.fitting`
     property on `Analysis`) is removed.
   - `tests/unit/easydiffraction/analysis/test_fitting.py` is
     **kept** — it exercises the engine. P2.1a's bullet that listed
     it for deletion was wrong and is now corrected to a "Keep"
     bullet with an instruction to update only the assertions that
     touched the removed category surface.
2. Narrowed every `analysis\.fitting\b` grep in P1.12, P1.13, P1.15,
   and P2.1a to the category-surface forms only:

   ```
   \bself\.fitting\b
   \bproject\.analysis\.fitting\b
   \banalysis\.fitting\.(minimizer|show_minimizer_types|minimizer_type)\b
   categories\.fitting\b
   categories/fitting/
   ```

   The CIF tag prefix `_fitting.*` continues to live on (per ADR §2)
   and is not flagged either.

### P1 — Removed-category greps missed internal owner references

**Verdict: agree.** The previous P1.12 patterns covered imports,
category paths, and CIF tags, but not internal owner accesses such
as `self.fitting`, `self.bayesian_sampler`, `self._deterministic_result`.
Those forms appear in `src/easydiffraction/analysis/analysis.py`
today (≥20 hits across lines 446–795). The category property could
be removed at the public surface while internal access points
silently survive.

**Action.** Added a dedicated grep to
[`P1.12`](minimizer-category-consolidation.md#implementation-steps-phase-1)
that scans `src/easydiffraction/analysis/analysis.py` for any stale
`self.<removed>` reference:

```
git grep -nE '\bself\.fitting\b|\bself\._fitting\b|\bself\.bayesian_(sampler|result|convergence|parameter_posteriors|distribution_caches|pair_caches|predictive_datasets)\b|\bself\.deterministic_result\b|\bself\._deterministic_result\b' src/easydiffraction/analysis/analysis.py
```

must return empty. The P1.12 narration explicitly calls out that
this guards the "public removed but private kept" failure mode.

## Verification

This reply is a static one. No tests were run. Phase 2 of the updated
plan runs the standard `pixi run fix`, `check`, `unit-tests`,
`integration-tests`, `script-tests` commands with the zsh-safe
log-capture pattern.
