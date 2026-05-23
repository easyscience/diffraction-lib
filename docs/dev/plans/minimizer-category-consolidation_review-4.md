# Review 4: Minimizer Category Consolidation Plan

Reviewed plan:
[`minimizer-category-consolidation.md`](minimizer-category-consolidation.md)

Reviewed reply:
[`minimizer-category-consolidation_reply-3.md`](minimizer-category-consolidation_reply-3.md)

This review follows
[`.github/copilot-instructions.md`](../../../.github/copilot-instructions.md).

## Findings

### P1: P1.1a verification is too strict for the relocated summary type

P1.1a correctly adds an import from `easydiffraction.core.posterior` to
`analysis/fit_helpers/bayesian.py`, because that module still uses
`PosteriorParameterSummary` in aliases, annotations, and constructor
calls. But the closing verification says every remaining
`PosteriorParameterSummary` hit under `src/` should either be the
definition in `core/posterior.py` or an import from there.

That verification would fail after a correct relocation because
`analysis/fit_helpers/bayesian.py` will still contain legitimate
non-import references to the imported class.

Recommended fix: change the verification to allow use sites in modules
that import the type from `easydiffraction.core.posterior`, and require
only that no class definition remains outside `core/posterior.py`.

### P1/P2: `analysis.fitting` grep and `test_fitting.py` deletion conflate two concepts

The plan removes the Python `analysis.fitting` category surface, but the
repository also has an engine module:

```text
src/easydiffraction/analysis/fitting.py
```

Current unit tests in
`tests/unit/easydiffraction/analysis/test_fitting.py` exercise that
engine module (`easydiffraction.analysis.fitting.Fitter`), not the
category package. The updated stale-reference grep `analysis\.fitting\b`
also catches imports of this engine module.

As written, P1.12 can force removal or renaming of a module the plan
does not list as deleted, and P2.1a deletes engine coverage by calling
`test_fitting.py` an obsolete category test.

Recommended fix: decide explicitly whether
`src/easydiffraction/analysis/fitting.py` is kept, renamed, or deleted.
If kept, narrow stale-reference checks to the removed owner/category
surface (`self.fitting`, `project.analysis.fitting`,
`categories.fitting`, `categories/fitting/`) and keep or migrate
`test_fitting.py`. If renamed/deleted, add that source-file move/removal
and replacement test coverage to the plan.

### P1: Removed-category greps still miss internal owner references

P1.12 targets imports, category paths, and CIF tags, but it can miss
internal owner references that must disappear when the categories are
removed:

- `self.fitting`
- `self.bayesian_result`, `self.bayesian_sampler`, etc.
- `self.deterministic_result`
- `self._deterministic_result`

Current `analysis.py` contains these forms. If any survive the
implementation, the category properties can be removed while stale
internal code remains, and the P1.12 greps may still pass.

Recommended fix: add explicit source checks for internal owner/category
references, for example:

```text
git grep -nE '\bself\.fitting\b|\bself\.bayesian_(sampler|result|convergence|parameter_posteriors|distribution_caches|pair_caches|predictive_datasets)\b|\bself\.deterministic_result\b|_deterministic_result\b' src/easydiffraction/analysis/analysis.py
```

Scope or refine as needed, but make sure owner-level property accesses
and private removed-category attributes are covered.

## Verification

No tests were run. This was a static review of the updated plan, reply
3, `.github/copilot-instructions.md`, and current source/test
references.
