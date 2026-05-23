# Review 3: Minimizer Category Consolidation Plan

Reviewed plan:
[`minimizer-category-consolidation.md`](minimizer-category-consolidation.md)

Reviewed reply:
[`minimizer-category-consolidation_reply-2.md`](minimizer-category-consolidation_reply-2.md)

This review follows
[`.github/copilot-instructions.md`](../../../.github/copilot-instructions.md).

## Findings

### P1: P1.10a still contradicts the behavior-only base decision

Reply 2 and the updated plan now say `LeastSquaresMinimizerBase` and
`BayesianMinimizerBase` are behavior-only and contain no descriptor
instances. P1.10a still says to declare `_deterministic_result.*` fields
on `LeastSquaresMinimizerBase` so every LSQ concrete class inherits
them.

That reintroduces inherited descriptor declarations after the plan
explicitly rejected them.

Recommended fix: change P1.10a so every concrete LSQ minimizer class
declares the deterministic-result replacement descriptors in its own
class body. The behavior-only base can keep helper methods or expected
descriptor-name constants, but not descriptor instances.

### P1: P1.15 cannot confirm a full-project sweep before Phase 2

P1.12 now correctly scopes stale-reference checks to `src/`, with
tutorials checked after P1.13 and tests checked after P2.1a. But the
same P1.12 text still says P1.15 confirms the full-project sweep is
clean before Phase 2 starts.

That is impossible if test migration remains in P2.1a.

Recommended fix: either move test migration to Phase 1 before P1.15, or
change P1.15 to confirm only Phase 1 scopes (`src/` and tutorials). Keep
the `tests/` sweep as a P2.1a requirement.

### P1: `git grep -n 'bayesian_' src/` is too broad

The broad P1.12 source grep catches removed category names, but it also
catches valid non-category Bayesian code such as
`_format_bayesian_overall_status` in
`src/easydiffraction/analysis/fit_helpers/bayesian.py`.

The ADR removes `bayesian_*` categories, not the Bayesian fitting
concept or helper functions. This verification would either fail after a
correct implementation or force unrelated renames.

Recommended fix: use a targeted pattern for removed categories and CIF
tags, for example one that includes:

- `analysis\.bayesian_`
- `categories\.bayesian_`
- `categories/bayesian_`
- `_bayesian_(sampler|result|convergence|parameter_posterior|distribution_cache|pair_cache|predictive_dataset)`

### P1: Tutorial migration misses current fitting-mode show-method users

P1.13 renames `analysis.show_fitting_mode_types()` to
`analysis.show_supported_fitting_mode_types()`, but the tutorial file
list does not include every current `.py` user. Current grep shows
`docs/docs/tutorials/ed-8.py` and `docs/docs/tutorials/ed-20.py` also
call `project.analysis.show_fitting_mode_types()`.

P1.12's post-P1.13 tutorial greps also do not check for
`show_fitting_mode_types`, so those stale tutorial calls could survive
the plan until script tests fail.

Recommended fix: add `ed-8.py` and `ed-20.py` to P1.13, and include
`show_fitting_mode_types` / `show_minimizer_types` in the post-P1.13
tutorial grep.

### P1: P1.1a under-specifies the `PosteriorParameterSummary` move

P1.1a says to move `PosteriorParameterSummary` out of
`analysis/fit_helpers/bayesian.py` and update "both existing import
sites", listing only `analysis.py` and
`analysis/fit_helpers/__init__.py`. But
`analysis/fit_helpers/bayesian.py` itself must also import and re-export
the relocated class after the dataclass definition is removed; otherwise
its type aliases, functions, and the preserved old import path break
immediately.

Recommended fix: add
`src/easydiffraction/analysis/fit_helpers/bayesian.py` to the P1.1a
modified-file/update list, with explicit instruction to replace the
local dataclass definition with an import from
`easydiffraction.core.posterior`.

## Verification

No tests were run. This was a static review of the updated plan, reply
2, `.github/copilot-instructions.md`, and current source/tutorial
references.
