# Review 1: Minimizer Category Consolidation Plan

Reviewed plan:
[`minimizer-category-consolidation.md`](minimizer-category-consolidation.md)

This review follows
[`.github/copilot-instructions.md`](../../../.github/copilot-instructions.md).

## Findings

### P1: The plan drops existing minimizer capabilities while claiming none are removed

The new category list only creates four minimizer classes:

- `bumps_lm.py`
- `bumps_least_squares.py`
- `lmfit_least_squares.py`
- `dream.py`

See
[`minimizer-category-consolidation.md`](minimizer-category-consolidation.md#concrete-files-likely-to-change).
However, the current enum and minimizer registry include additional
tags: `lmfit`, `lmfit (leastsq)`, `dfols`, `bumps`, `bumps (amoeba)`,
and `bumps (de)`.

That conflicts with the suggested PR text saying:

> no fitting capability is removed

Recommended fix: add category coverage for every currently supported
minimizer tag, or explicitly record which tags are removed or aliased
and get approval before implementation.

### P1: The plan omits `deterministic_result`, although the ADR removes it

The ADR being implemented says `deterministic_result` fields move into
the deterministic concrete minimizer classes. The plan's deleted package
list removes the Python `fitting` category and seven Bayesian
categories, but does not remove:

```text
src/easydiffraction/analysis/categories/deterministic_result/
```

Current code still persists `_deterministic_result.*` through that
category. This leaves the implementation inconsistent with the ADR.

Recommended fix: either add `deterministic_result` removal and migration
steps to the plan, or amend the ADR/plan to keep it deliberately.

### P1: The switchable-category API names conflict with repo instructions

The plan adds:

```python
analysis.show_minimizer_types()
```

But `.github/copilot-instructions.md` requires switchable categories to
expose:

```python
show_supported_<category>_types()
show_current_<category>_type()
```

Recommended fix: update the plan, ADR wording, tutorials, and test
migration to use `show_supported_minimizer_types()` and
`show_current_minimizer_type()`, or record a deliberate exception in the
plan and amend the conflicting ADR guidance.

### P2: The sidecar instructions contradict each other

The modified-file list says `results_sidecar.py` should use "append-mode
open", but P1.10 requires:

```python
h5py.File(path, 'w')
```

That truncation behavior is a core lifecycle decision for
overwrite-on-new-fit.

Recommended fix: remove the append-mode wording from this plan, or scope
append mode only to the later resume plan.

### P2: Existing test migration is acknowledged but not planned

The plan notes existing tests call `analysis.fitting.minimizer*`, but
Phase 2 only adds new minimizer-category tests. Existing tests such as:

- `tests/unit/easydiffraction/analysis/categories/fitting/test_default.py`
- `tests/unit/easydiffraction/analysis/categories/test_fit.py`
- `tests/functional/test_switchable_categories.py`
- `tests/integration/fitting/test_bayesian_dream.py`

will fail after the removed API lands unless they are explicitly updated
or deleted.

Recommended fix: add a Phase 2 step to migrate existing unit,
functional, integration, project-load, CIF, display, and tutorial-script
tests from `analysis.fitting.*` and removed Bayesian categories to the
new `analysis.minimizer*` surface.

## Residual Risk

P1.1 needs a dependency-boundary decision. Typing
`GenericParameter.posterior` directly as `PosteriorParameterSummary` in
`core/variable.py` would pull an analysis Bayesian type into `core/`,
which conflicts with:

> Keep `core/` free of domain logic (base classes and utilities only).

Recommended fix: move the posterior summary value object to a neutral
core-safe module, use a protocol/type alias guarded by `TYPE_CHECKING`,
or record an explicit architecture exception before implementation.

## Verification

No tests were run. This was a static review of the plan against
`.github/copilot-instructions.md` and the current source tree.
