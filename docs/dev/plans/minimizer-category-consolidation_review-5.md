# Review 5: Minimizer Category Consolidation Plan

Reviewed plan:
[`minimizer-category-consolidation.md`](minimizer-category-consolidation.md)

Reviewed reply:
[`minimizer-category-consolidation_reply-4.md`](minimizer-category-consolidation_reply-4.md)

This review follows
[`.github/copilot-instructions.md`](../../../.github/copilot-instructions.md).

## Findings

### P1: P1.1a still contains the strict `PosteriorParameterSummary` check

Reply 4 says P1.1a was rewritten to verify one class definition and then
allow use-sites in files that import `PosteriorParameterSummary` from
`easydiffraction.core.posterior`.

The plan does not yet contain that fix. In
`minimizer-category-consolidation.md` lines 212-214, P1.1a still says:

```text
Verify with `git grep -n 'PosteriorParameterSummary' src/` — every
remaining hit should either be inside `core/posterior.py` (the
definition) or import it from there.
```

That still rejects legitimate post-move use-sites in
`analysis/fit_helpers/bayesian.py`, including the `SummaryList` alias,
annotations, and constructor calls. A correct implementation would fail
this check even though the relocated import is present.

Recommended fix: replace the plan's P1.1a verification block with the
two-step check described in reply 4: exactly one class definition under
`src/`, and every non-definition file that mentions the symbol must also
import it from `easydiffraction.core.posterior`.

### P1: P1.12 still misses private Bayesian owner attributes

The new P1.12 internal owner grep in
`minimizer-category-consolidation.md` line 463 covers public
`self.bayesian_*` accessors and private `_fitting` /
`_deterministic_result` fields, but it does not cover private Bayesian
fields such as:

```text
self._bayesian_result
self._bayesian_sampler
self._bayesian_convergence
self._bayesian_parameter_posteriors
self._bayesian_distribution_caches
self._bayesian_pair_caches
self._bayesian_predictive_datasets
```

Those fields exist today in `src/easydiffraction/analysis/analysis.py`
around lines 451 and 524-530. If implementation removes the public
category properties but leaves private storage or reset code behind, the
P1.12 verification can still pass.

Recommended fix: add `\bself\._bayesian_(sampler|result|convergence|parameter_posteriors|distribution_caches|pair_caches|predictive_datasets)\b`
to the dedicated `analysis.py` grep.

### P2: The plan references a missing "Decisions added after Review 4" section

Reply 4 says the kept-vs-removed `analysis.fitting` decision was recorded
under `Decisions added after Review 4`. The plan also references that
section in P1.12 (`minimizer-category-consolidation.md` line 455) and
P2.1a (line 589).

The plan currently has `Decisions added after Review 2` but no
`Decisions added after Review 4` heading. The kept engine-module decision
is described inline in P1.12 and P2.1a, so this is not a design blocker,
but the cross-reference is dangling.

Recommended fix: add the missing decision section near the existing
decision notes, or change both references to point to the section where
the decision actually lives.

## Verification

No tests were run. This was a static review of the updated plan, reply 4,
`.github/copilot-instructions.md`, and current source references.
