# Reply to Review 1: Minimizer Category Consolidation Plan

Reply to
[`minimizer-category-consolidation_review-1.md`](minimizer-category-consolidation_review-1.md)
for the plan at
[`minimizer-category-consolidation.md`](minimizer-category-consolidation.md).

This reply follows
[`.github/copilot-instructions.md`](../../../.github/copilot-instructions.md).

For each finding: judgement, action taken in the updated plan, and a
pointer to the affected plan section.

## Findings

### P1 — Minimizer category coverage gap

**Verdict: agree.** The current `MinimizerTypeEnum` has nine tags
(`lmfit`, `lmfit (leastsq)`, `lmfit (least_squares)`, `dfols`, `bumps`,
`bumps (lm)`, `bumps (dream)`, `bumps (amoeba)`, `bumps (de)`); the plan
listed only four concrete classes. The PR text claims "no fitting
capability is removed", so the plan must back that up.

**Action.** Updated the §"Concrete files likely to change" → "Created"
list to declare one concrete class per enum tag (nine modules under
`src/easydiffraction/analysis/categories/minimizer/`). Step **P1.4** now
spells out the full tag → class mapping and reuses `MinimizerTypeEnum`
as the factory registration key. Where backends share descriptor sets,
the concrete classes share a thin `LeastSquaresMinimizerBase` (LSQ
shared inputs) or `BayesianMinimizerBase` (Bayesian shared inputs)
intermediate; class bodies still declare every descriptor with
class-specific defaults per ADR §8 (no mixins).

**Open question recorded in the plan.** Whether the bare `lmfit` and
`bumps` tags should remain or be folded into `lmfit (leastsq)` /
`bumps (lm)` as aliases is a small product decision; the plan defaults
to keeping all nine tags and asks the user to confirm during the P1
review gate. No tag is removed without an explicit answer.

### P1 — `deterministic_result` removal omitted

**Verdict: agree.** ADR §1 lists `deterministic_result` for removal but
the plan's deleted-package list did not include it. That left the
implementation contradictory with the ADR.

**Action.** Added
`src/easydiffraction/analysis/categories/deterministic_result/` to the
§"Concrete files likely to change" → "Deleted" list. Added a new step
**P1.10a** to migrate `_deterministic_result.*` descriptors into the
concrete LSQ minimizer classes (`runtime_seconds`,
`iterations_performed`, `exit_reason`, `covariance_available`,
`correlation_available`, …) and the obsolete CIF reader/writer. Step
**P1.12** "Delete obsolete category packages" now also removes
`deterministic_result/` and its tests.

### P1 — Switchable-category API naming

**Verdict: agree.** Copilot instructions require
`show_supported_<category>_types()` and `show_current_<category>_type()`
for switchable categories. The plan inherited the legacy
`show_minimizer_types()` name from the existing `analysis.fitting` API.

**Action.** Across the plan:

- `analysis.show_minimizer_types()` →
  `analysis.show_supported_minimizer_types()` plus a new
  `analysis.show_current_minimizer_type()`.
- `analysis.show_fitting_mode_types()` →
  `analysis.show_supported_fitting_mode_types()` plus a new
  `analysis.show_current_fitting_mode_type()`.
- Tutorial migration step **P1.13** picks up the renames.
- ADR amendment step **P1.14** edits
  [`switchable-category-api.md`](../adrs/accepted/switchable-category-api.md)
  and the consolidated ADR §2 to use the canonical names.

No deliberate exception is introduced; the plan now conforms to
[`.github/copilot-instructions.md`](../../../.github/copilot-instructions.md).

### P2 — Sidecar instructions contradiction

**Verdict: agree.** The §"Modified" file list said
`io/results_sidecar.py` (append-mode open), while P1.10 specifies
`h5py.File(path, 'w')` (truncate). Truncate is the lifecycle decision
for this plan; append is owned by the resume work in Plan 2.

**Action.** Edited the §"Modified" bullet for `io/results_sidecar.py` to
drop "append-mode open" and instead say "truncate-on-new-fit open +
namespaced groups; resume append handled by Plan 2". P1.10 wording is
unchanged.

### P2 — Existing test-migration step missing

**Verdict: agree.** Phase 2 added only new unit tests for the new
category modules. Existing tests under `tests/unit/.../fitting/`,
`tests/functional/test_switchable_categories.py`,
`tests/integration/fitting/test_bayesian_dream.py`,
`tests/integration/fitting/test_project_load.py` and ~10 more would fail
after the API moves.

**Action.** Added step **P2.1a — Migrate existing tests** before running
the test suites. Lists each path (or path glob) so an AI agent can
execute them as separate commits. Calls out:

- `tests/unit/easydiffraction/analysis/categories/fitting/` (whole
  directory) → delete after migration.
- `tests/unit/easydiffraction/analysis/categories/test_bayesian_*.py`,
  `test_deterministic_result.py` → delete.
- `tests/unit/easydiffraction/analysis/test_analysis.py`,
  `test_analysis_coverage.py`, `test_fitting.py` → rewrite calls from
  `analysis.fitting.minimizer_type` to `analysis.minimizer_type` and the
  new show-method names.
- `tests/functional/test_switchable_categories.py` → extend with the new
  `minimizer` selector.
- `tests/integration/fitting/test_bayesian_dream.py`,
  `test_analysis_and_fit_category_support.py`,
  `test_analysis_display.py`, `test_project_load.py`,
  `test_powder-diffraction_*.py`, `test_multi.py`, `test_sequential.py`,
  `conftest.py` → migrate calls.
- `tests/unit/easydiffraction/io/test_results_sidecar.py` → reflect new
  namespaced groups and overwrite semantics.
- `tests/unit/easydiffraction/project/test_display.py`,
  `test_project_load.py` → migrate references away from removed Bayesian
  categories.

The step uses `pixi run test-structure-check` to confirm the test-source
mirror is consistent after the moves.

## Residual Risk

### `Parameter.posterior` core-boundary

**Verdict: agree.** Annotating `GenericParameter.posterior` directly
with `PosteriorParameterSummary` from `analysis.fit_helpers.bayesian`
pulls analysis into `core/`, which conflicts with the architecture rule.

**Decision.** Move the `PosteriorParameterSummary` dataclass into
`src/easydiffraction/core/posterior.py`. The class is a pure value
object (six floats and two tuples — no analysis logic), so relocating it
to `core/` is consistent with "base classes and utilities only". The
existing import path
`easydiffraction.analysis.fit_helpers.bayesian.PosteriorParameterSummary`
is preserved by re-exporting it from `analysis.fit_helpers.bayesian`
during the migration; the project is in beta, so the re-export is the
single keep-imports-working bridge inside the same plan, not a
deprecation shim.

**Action.**

- Added step **P1.1a — Relocate `PosteriorParameterSummary` to
  `core/`.** Creates `src/easydiffraction/core/posterior.py`, moves the
  dataclass, updates the one existing import site in
  `analysis/analysis.py` and the re-export in
  `analysis/fit_helpers/__init__.py`.
- **P1.1** now imports the type from `core/posterior.py`, so
  `core/variable.py` stays free of analysis imports.

This avoids the `TYPE_CHECKING` + `Protocol` route, which would have
added indirection without removing the boundary problem at runtime (the
type still needs to be constructible from CIF in
[`io/cif/serialize.py`](../../../src/easydiffraction/io/cif/serialize.py)
during P1.8).

## Verification

This reply is a static one. No tests were run. Phase 2 of the updated
plan runs the standard `pixi run fix`, `check`, `unit-tests`,
`integration-tests`, `script-tests` commands with the zsh-safe
log-capture pattern.
