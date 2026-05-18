# Analysis CIF Fit State Implementation Plan

This plan follows `.github/copilot-instructions.md`. Deliberate
exceptions: none.

Source ADR: `docs/dev/adrs/suggestions/analysis-cif-fit-state.md`.
Related decisions read while preparing this plan:

- `docs/dev/adrs/accepted/runtime-fit-results.md`
- `docs/dev/adrs/accepted/project-facade-and-persistence.md`
- `docs/dev/adrs/accepted/category-owner-sections.md`
- `docs/dev/adrs/accepted/free-flag-cif-encoding.md`
- `docs/dev/adrs/accepted/loop-category-key-identity.md`
- `docs/dev/adrs/accepted/fit-mode-categories.md`
- `docs/dev/adrs/accepted/test-strategy.md`
- `docs/dev/adrs/suggestions/parameter-correlation-persistence.md`
- `docs/dev/adrs/suggestions/parameter-posterior-summary.md`

## Goal

Persist analysis-owned fit state in `analysis/analysis.cif` and, for
large Bayesian arrays, `analysis/results.h5`. Saved projects should be
able to restore fit bounds, pre-fit snapshots, deterministic result
summaries, Bayesian summaries, posterior manifests, and plot-ready cache
metadata without duplicating committed model parameter values in
structure or experiment CIF files.

## Status Checklist

- [x] Gather planning context from ADRs, source files, and tests.
- [x] Confirm ADR status: implement from the suggestion for now.
- [x] Confirm HDF5 strategy: add `h5py` as a direct dependency.
- [x] Confirm composite-key loop strategy: add persisted `id` columns.
- [x] Confirm public surface: expose read-only `Analysis` properties.
- [x] Confirm predictive cache identity: key by `experiment_name`.
- [x] Phase 1 step 1: update the ADR suggestion with clarifications.
- [x] Phase 1 step 2: add common fit-state category models.
- [x] Phase 1 step 3: add deterministic result category models.
- [x] Phase 1 step 4: add Bayesian metadata category models.
- [x] Phase 1 step 5: add Bayesian cache manifest category models.
- [x] Phase 1 step 6: wire analysis CIF save/load for fit state.
- [x] Phase 1 step 7: capture fit projections after fitting.
- [ ] Phase 1 step 8: add HDF5 sidecar save/load.
- [ ] Phase 1 step 9: restore result objects and display cache inputs.
- [ ] Phase 1 review gate: stop for human review.
- [ ] Phase 2 step 1: add unit tests for new categories.
- [ ] Phase 2 step 2: add CIF and project save/load tests.
- [ ] Phase 2 step 3: add display and sidecar behavior tests.
- [ ] Phase 2 step 4: run the verification commands.

## Clarified Decisions

These questions were answered on 2026-05-18.

1. Implement from `docs/dev/adrs/suggestions/analysis-cif-fit-state.md`
   for now. Do not move the ADR to `accepted/` as part of this plan.
2. Add `h5py` as a direct dependency for `analysis/results.h5`.
3. Add persisted `id` columns for composite-key fit-state loops instead
   of using computed runtime-only keys.
4. Expose all new fit-state categories as public read-only properties on
   `Analysis`.
5. Key `_bayesian_predictive_dataset` rows by `experiment_name`, keeping
   one cached predictive dataset per experiment.

No remaining required gates are known. If implementation uncovers a new
schema conflict, dependency concern, or public API ambiguity, stop and
ask before changing this plan.

## Agent Safety Rules

This plan is written for a less advanced agent. Follow it literally.

- Work on one numbered Phase 1 step at a time.
- Run `git status --short` before each step. If unrelated dirty files
  overlap with the files for that step, stop and ask for guidance.
- Use `apply_patch` for manual edits. Do not write files with shell
  redirection, Python scripts, or ad hoc generated output.
- Do not create or run tests during Phase 1 unless the user explicitly
  asks. Phase 1 is implementation and documentation only.
- After each completed Phase 1 step, inspect the diff for only that
  step, stage explicit paths, and commit locally before moving on.
- Use explicit paths with `git add`. Never stage the whole tree.
- Keep each commit atomic and single-purpose.
- If implementation uncovers a missing requirement, dependency problem,
  schema conflict, or public API ambiguity, stop and ask.

Before each implementation step, write down the exact files you expect
to edit. If a file is not listed in the current step and the edit is not
obviously mechanical, stop and ask before changing it.

For every new category package in Phase 1:

1. Create `factory.py` with a factory class following the neighboring
   analysis category packages.
2. Create `default.py` with concrete `CategoryItem` or
   `CategoryCollection` classes.
3. Decorate every concrete top-level category class with
   `@Factory.register`. Do not decorate row item classes unless a
   neighboring package already does that for the same shape.
4. Create `__init__.py` with explicit imports for the factory and
   concrete classes.
5. Update `src/easydiffraction/analysis/categories/__init__.py` and
   `src/easydiffraction/analysis/__init__.py` with explicit imports.
6. Keep public descriptors read-only unless the category is meant to be
   user-editable. Use private `_set_<name>` helpers for internal restore
   when a public setter would create the wrong user-facing contract.
7. If a collection row has read-only public fields, do not rely on the
   generic `CategoryCollection.create(**kwargs)` path. Add an explicit
   `create(...)` method that builds the row and uses private helpers.

Complexity guardrails:

- Steps 7 and 9 are broad. Start with the smallest central hook, then
  edit individual minimizers or display helpers only when the required
  data is not available through that central hook.
- If one step needs more than six source files, more than one new public
  class family beyond the planned categories, or a public API change not
  named in this plan, stop and ask to split the step.
- When auditing usages or renaming symbols, search code, tests,
  tutorials, and docs with `git grep -n` before editing.
- Do not fix unrelated lint, formatting, typing, or test failures while
  implementing this plan. Mention them at the review gate instead.

Required commit discipline for any AI agent following this plan:

```text
Every completed Phase 1 implementation step must be staged with
explicit paths and committed locally before moving to the next
implementation step or the Phase 1 review gate.
```

Suggested branch name:

```text
feature/analysis-cif-fit-state
```

## Verified Repository Facts

- `Analysis` inherits `CategoryOwner` in
  `src/easydiffraction/analysis/analysis.py`.
- `Analysis._serializable_categories()` currently emits fitting,
  aliases, constraints, and active fit-mode categories.
- `analysis.as_cif` delegates to `analysis_to_cif()` in
  `src/easydiffraction/io/cif/serialize.py`.
- `category_owner_to_cif()` serializes explicit `CategoryItem` and
  `CategoryCollection` instances in the order returned by
  `_serializable_categories()`.
- `analysis_from_cif()` restores fitting configuration, active fit-mode
  sections, aliases, and constraints.
- `Project.save()` writes `analysis/analysis.cif` from
  `self.analysis.as_cif` and lists all files already present under the
  `analysis/` directory.
- `Project.load()` loads structures and experiments before analysis,
  then resolves alias references.
- `GenericParameter` already has `fit_min`, `fit_max`, and
  `fit_bounds_uncertainty_multiplier` runtime state.
- `Fitter.fit()` currently captures only `param._fit_start_value` before
  fitting. It does not capture pre-fit uncertainty.
- `FitResults` and `BayesianFitResults` already contain most scalar
  result information needed by the ADR.
- `project.display.posterior.*` currently reads from runtime
  `analysis.fit_results`, not persisted caches.
- Existing verification tasks include `pixi run fix`, `pixi run check`,
  `pixi run test-structure-check`, `pixi run unit-tests`,
  `pixi run integration-tests`, and `pixi run script-tests`.

## Naming Decisions For Implementation

Use exact CIF category codes from the ADR. For Python attributes on
`Analysis`, use singular names for single-item categories and plural
names for collections:

| Python attribute                  | CIF category                      | Shape       |
| --------------------------------- | --------------------------------- | ----------- |
| `fit_state`                       | `_fit_state`                      | single item |
| `fit_parameters`                  | `_fit_parameter`                  | collection  |
| `fit_result`                      | `_fit_result`                     | single item |
| `fit_parameter_correlations`      | `_fit_parameter_correlation`      | collection  |
| `deterministic_result`            | `_deterministic_result`           | single item |
| `deterministic_parameter_results` | `_deterministic_parameter_result` | collection  |
| `bayesian_result`                 | `_bayesian_result`                | single item |
| `bayesian_sampler`                | `_bayesian_sampler`               | single item |
| `bayesian_convergence`            | `_bayesian_convergence`           | single item |
| `bayesian_parameter_posteriors`   | `_bayesian_parameter_posterior`   | collection  |
| `bayesian_distribution_caches`    | `_bayesian_distribution_cache`    | collection  |
| `bayesian_pair_caches`            | `_bayesian_pair_cache`            | collection  |
| `bayesian_predictive_datasets`    | `_bayesian_predictive_dataset`    | collection  |

If this public surface feels too noisy during implementation, stop and
ask before hiding these properties from `Analysis.help()`. Do not move
the categories under another category; the ADR requires flat analysis
siblings.

## Phase 1: Implementation

Phase 1 is code and documentation only. Do not add or run tests here
unless explicitly instructed by the user.

### Step 1: Update The ADR Suggestion With Clarifications

Files likely to change:

- `docs/dev/adrs/suggestions/analysis-cif-fit-state.md`
- `docs/dev/plans/analysis-cif-fit-state.md`

Actions:

1. Keep the ADR in `suggestions/`; do not move it to `accepted/`.
2. Amend the ADR suggestion so composite-key loops have persisted `id`
   columns. At minimum this applies to `_fit_parameter_correlation` and
   `_bayesian_pair_cache`.
3. Document that `_bayesian_predictive_dataset` remains keyed by
   `experiment_name`.
4. Document that `analysis/results.h5` uses `h5py` as a direct
   dependency.
5. Update this plan checklist for Step 1.

Suggested commit message:

```text
Clarify analysis fit-state ADR schema
```

### Step 2: Add Common Fit-State Categories

Files likely to change:

- `src/easydiffraction/analysis/categories/fit_state/`
- `src/easydiffraction/analysis/categories/fit_parameters/`
- `src/easydiffraction/analysis/categories/fit_result/`
- `src/easydiffraction/analysis/categories/fit_parameter_correlations/`
- `src/easydiffraction/analysis/categories/__init__.py`
- `src/easydiffraction/analysis/__init__.py`
- `src/easydiffraction/analysis/enums.py`
- `docs/dev/plans/analysis-cif-fit-state.md`

Actions:

1. Add `(str, Enum)` classes for closed values: `FitResultKindEnum` with
   `deterministic` and `bayesian`, and `FitCorrelationSourceEnum` with
   `deterministic` and `posterior`.
2. Add category modules following existing analysis category patterns:
   `default.py`, `factory.py`, and `__init__.py` with explicit imports.
3. Add `FitState` as a `CategoryItem` with
   `_category_code = 'fit_state'` and numeric `schema_version` default
   `1`.
4. Add `FitParameterItem` and `FitParameters` for `_fit_parameter`. Use
   `_category_entry_name = 'param_unique_name'`.
5. Add `FitResult` for `_fit_result` with `result_kind`, `success`,
   `message`, `iterations`, `fitting_time`, and `reduced_chi_square`.
6. Add `FitParameterCorrelationItem` and collection for
   `_fit_parameter_correlation`. Include persisted
   `_fit_parameter_correlation.id` and use
   `_category_entry_name = 'id'`. Generate a stable default id from the
   normalized source and parameter pair when callers do not provide one.
7. Normalize correlation pairs so only upper-triangle rows are stored.
8. Use `StringDescriptor`, `NumericDescriptor`, and `BoolDescriptor` as
   appropriate. Avoid raw Python attributes for persisted fields.
9. Do not add JSON fields or loose tags.
10. Update imports in the package `__init__.py` files so concrete
    classes are registered and importable.
11. Update this plan checklist for Step 2.

Implementation notes:

- The collection `add()` path assumes one key. For categories with a
  persisted `id`, set `_category_entry_name = 'id'` on the item and
  generate a stable default `id` before adding the item to the
  collection.
- Keep CIF tag names exactly as in the ADR, for example
  `_fit_parameter.param_unique_name`.
- If an enum value from CIF is invalid, warn clearly and keep the
  default. Do not fail silently.

Suggested commit message:

```text
Add common analysis fit-state categories
```

### Step 3: Add Deterministic Result Categories

Files likely to change:

- `src/easydiffraction/analysis/categories/deterministic_result/`
- `src/easydiffraction/analysis/categories/deterministic_parameter_results/`
- `src/easydiffraction/analysis/categories/__init__.py`
- `src/easydiffraction/analysis/__init__.py`
- `docs/dev/plans/analysis-cif-fit-state.md`

Actions:

1. Add `DeterministicResult` as a single-item category with the ADR
   fields: `optimizer_name`, `method_name`, `objective_name`,
   `objective_value`, `n_data_points`, `n_parameters`,
   `n_free_parameters`, `degrees_of_freedom`, `covariance_available`,
   and `correlation_available`.
2. Add `DeterministicParameterResultItem` and collection for
   `_deterministic_parameter_result` with `order_index`,
   `param_unique_name`, `final_value`, `final_uncertainty`,
   `at_lower_bound`, and `at_upper_bound`.
3. Use `_category_entry_name = 'param_unique_name'` for deterministic
   parameter result rows. Keep `order_index` as display and array order.
4. Do not duplicate pre-fit values here; those belong to
   `_fit_parameter`.
5. Add explicit package imports.
6. Update this plan checklist for Step 3.

Suggested commit message:

```text
Add deterministic fit-result categories
```

### Step 4: Add Bayesian Metadata Categories

Files likely to change:

- `src/easydiffraction/analysis/categories/bayesian_result/`
- `src/easydiffraction/analysis/categories/bayesian_sampler/`
- `src/easydiffraction/analysis/categories/bayesian_convergence/`
- `src/easydiffraction/analysis/categories/bayesian_parameter_posteriors/`
- `src/easydiffraction/analysis/categories/__init__.py`
- `src/easydiffraction/analysis/__init__.py`
- `docs/dev/plans/analysis-cif-fit-state.md`

Actions:

1. Add `BayesianResult` as a single-item category with all ADR fields.
2. Add `BayesianSampler` as a single-item category with resolved DREAM
   sampler settings: `steps`, `burn`, `thin`, `pop`, `parallel`, `init`,
   and `random_seed`.
3. Add `BayesianConvergence` as a single-item category with `converged`,
   `max_r_hat`, `min_ess_bulk`, `n_draws`, `n_chains`, and
   `n_parameters`.
4. Add `BayesianParameterPosteriorItem` and collection with all ADR
   posterior summary fields. Use `_category_entry_name = 'unique_name'`.
5. Preserve the repo naming rule from prior Bayesian work: `best_sample`
   and `Best posterior sample` refer to the committed sampled point, not
   a continuous MAP estimate.
6. Add explicit package imports.
7. Update this plan checklist for Step 4.

Suggested commit message:

```text
Add Bayesian fit-result metadata categories
```

### Step 5: Add Bayesian Cache Manifest Categories

Files likely to change:

- `src/easydiffraction/analysis/categories/bayesian_distribution_caches/`
- `src/easydiffraction/analysis/categories/bayesian_pair_caches/`
- `src/easydiffraction/analysis/categories/bayesian_predictive_datasets/`
- `src/easydiffraction/analysis/categories/__init__.py`
- `src/easydiffraction/analysis/__init__.py`
- `docs/dev/plans/analysis-cif-fit-state.md`

Actions:

1. Add distribution cache manifest rows keyed by `param_unique_name`.
2. Add pair cache manifest rows with persisted `_bayesian_pair_cache.id`
   and `_category_entry_name = 'id'`. Generate a stable default id from
   the normalized parameter pair when callers do not provide one.
3. Add predictive dataset manifest rows keyed by `experiment_name`. If
   multiple predictive datasets per experiment become necessary, stop
   and ask before changing the ADR schema.
4. Store only HDF5 dataset paths and shape/count metadata in CIF.
5. Do not write numerical arrays into CIF loops.
6. Add explicit package imports.
7. Update this plan checklist for Step 5.

Suggested commit message:

```text
Add Bayesian fit-cache manifest categories
```

### Step 6: Wire Analysis CIF Save And Load

Files likely to change:

- `src/easydiffraction/analysis/analysis.py`
- `src/easydiffraction/io/cif/serialize.py`
- `src/easydiffraction/project/project.py`
- `docs/dev/plans/analysis-cif-fit-state.md`

Actions:

1. Instantiate the new fit-state categories in `Analysis.__init__`.
2. Add read-only properties using the names in this plan.
3. Add `Analysis._has_persisted_fit_state()` or an equivalent helper.
4. Update `Analysis._serializable_categories()` so fit-state categories
   are appended only when a fit-state projection exists.
5. Keep the order from the ADR: normal analysis configuration first,
   then `_fit_state`, `_fit_parameter`, `_fit_result`, correlations,
   deterministic categories, Bayesian categories, and cache manifests.
6. Update `analysis_from_cif()` to restore the new categories after
   existing fitting, aliases, constraints, and active mode-specific
   configuration.
7. Make missing fit-state categories a no-op for older saved projects.
8. Add clear warnings for unsupported `_fit_state.schema_version`.
9. Add a project-level helper to build a `{unique_name: parameter}` map
   from structures and experiments. Reuse it for alias and fit-state
   reference restoration if practical.
10. Update this plan checklist for Step 6.

Suggested commit message:

```text
Wire analysis fit-state CIF restore
```

### Step 7: Capture Fit Projections After Fitting

Files likely to change:

- `src/easydiffraction/analysis/analysis.py`
- `src/easydiffraction/analysis/fitting.py`
- `src/easydiffraction/analysis/minimizers/base.py`
- `src/easydiffraction/analysis/minimizers/bumps.py`
- `src/easydiffraction/analysis/minimizers/bumps_dream.py`
- `src/easydiffraction/analysis/minimizers/lmfit.py`
- `src/easydiffraction/analysis/fit_helpers/reporting.py`
- `src/easydiffraction/analysis/fit_helpers/bayesian.py`
- `docs/dev/plans/analysis-cif-fit-state.md`

Actions:

1. Add an analysis-owned method such as
   `_capture_fit_parameter_state(parameters)` that records
   `param_unique_name`, `fit_min`, `fit_max`,
   `fit_bounds_uncertainty_multiplier`, `start_value`, and
   `start_uncertainty` before the minimizer mutates parameters.
2. Do not rely on `GenericParameter._start_value`; it exists but is not
   currently the value used by fit result reporting.
3. Continue supporting existing `_fit_start_value` until a separate
   approved refactor replaces it.
4. Add `_store_fit_result_projection(results)` or equivalent on
   `Analysis` to fill common, deterministic, and Bayesian categories
   from `FitResults` or `BayesianFitResults`.
5. Prefer calling the analysis-owned capture and projection methods from
   `Fitter.fit()` or the existing `Analysis._fit_*` methods. Only edit
   individual minimizer classes when a required result field is missing
   from `FitResults` or `BayesianFitResults`.
6. For deterministic fits, prefer live parameter values for calculations
   and store final values only as display projections.
7. If deterministic projection values disagree with live parameter state
   on load, warn and keep the live parameter state.
8. For Bayesian fits, keep `point_estimate_name = 'best_sample'` unless
   the result object says otherwise.
9. Store upper-triangle parameter correlations only.
10. Clear stale fit-state categories at the start of a new fit so old
    cache manifests cannot survive a new result.
11. Update this plan checklist for Step 7.

Suggested commit message:

```text
Capture persisted fit-state projections
```

### Step 8: Add HDF5 Sidecar Save And Load

The HDF5 dependency decision is approved: add `h5py` directly.

Files likely to change:

- `pyproject.toml`
- `src/easydiffraction/analysis/analysis.py`
- `src/easydiffraction/io/`
- `src/easydiffraction/project/project.py`
- `docs/dev/plans/analysis-cif-fit-state.md`

Actions:

1. Add `h5py` as a direct dependency.
2. Add a small sidecar module for `analysis/results.h5`; keep imports
   local if the package is heavy.
3. Write canonical posterior arrays when available:
   `/posterior/parameter_samples`, `/posterior/log_posterior`, and
   `/posterior/draw_index`.
4. Write cache arrays only when the corresponding manifest rows are
   present.
5. Validate that the HDF5 dataset shape matches manifest metadata.
6. Make the sidecar optional for summary-only restore. If it is missing,
   warn clearly and keep available CIF summaries.
7. Call the sidecar writer from `Project.save()` after `analysis.cif`
   data has been prepared and before analysis directory contents are
   listed.
8. Call the sidecar reader from `Project.load()` after
   `analysis_from_cif()` and before restored display state is used.
9. Do not persist backend runtime objects, DREAM drivers, raw engine
   results, or ArviZ `InferenceData`.
10. Update this plan checklist for Step 8.

Suggested commit message:

```text
Persist Bayesian fit arrays in results sidecar
```

### Step 9: Restore Result Objects And Display Cache Inputs

Files likely to change:

- `src/easydiffraction/analysis/analysis.py`
- `src/easydiffraction/analysis/fit_helpers/reporting.py`
- `src/easydiffraction/analysis/fit_helpers/bayesian.py`
- `src/easydiffraction/project/display.py`
- `src/easydiffraction/display/plotting.py`
- `docs/dev/plans/analysis-cif-fit-state.md`

Actions:

1. Rebuild a lightweight `FitResults` or `BayesianFitResults` from the
   persisted categories after project load.
2. Attach restored live parameter objects where their unique names are
   still present.
3. Keep backend runtime fields such as `engine_result` as `None`.
4. Make `analysis.display.fit_results()` work from the restored result
   projection.
5. First restore non-plotting result behavior and correlation summaries.
   Only then add cache-aware posterior distribution, pair, and
   predictive plotting.
6. Update correlation plotting so it can use
   `_fit_parameter_correlation` when raw covariance or posterior samples
   are not available.
7. Keep correlation heatmaps compact. Do not replace the heatmap path
   with many per-cell Plotly traces.
8. Make posterior distribution, pair, and predictive display methods
   prefer valid persisted cache arrays when available.
9. If a requested cache is unavailable or invalid, warn clearly and use
   the existing recomputation path only when enough runtime data exists.
10. Do not make display methods recompute KDE, contours, or predictive
    bands when valid cache arrays were restored.
11. If cache-aware display requires a new helper object or cache API not
    named in this plan, stop and ask before adding it.
12. Update this plan checklist for Step 9.

Suggested commit message:

```text
Restore fit results from saved analysis state
```

### Phase 1 Review Gate

After Step 9, stop. Present the implementation for human review before
creating or running tests. Mention any deviations from this plan and any
open design questions that appeared during implementation.

Suggested commit message if only the plan checklist changes at the gate:

```text
Update analysis fit-state plan progress
```

## Phase 2: Verification

Only start Phase 2 after the user approves the Phase 1 implementation.

### Step 1: Add Category Unit Tests

Files likely to change:

- `tests/unit/easydiffraction/analysis/categories/`
- `tests/unit/easydiffraction/analysis/test_enums.py`
- `docs/dev/plans/analysis-cif-fit-state.md`

Tests to add:

1. Each new category has the expected CIF tags.
2. Each descriptor validates basic type and enum constraints.
3. Empty collections serialize to an empty string.
4. Collections rebuild indexes after `from_cif()`.
5. Persisted-id collections reject duplicate ids and normalize duplicate
   pair rows.
6. Correlation rows store only the upper triangle excluding the
   diagonal.

### Step 2: Add CIF And Project Save/Load Tests

Files likely to change:

- `tests/unit/easydiffraction/io/cif/`
- `tests/unit/easydiffraction/project/test_project_save.py`
- `tests/unit/easydiffraction/project/test_project_load.py`
- `tests/functional/test_fitting_workflow.py`
- `docs/dev/plans/analysis-cif-fit-state.md`

Tests to add:

1. A project with no fit state does not emit empty fit-state loops.
2. Deterministic fit-state categories round-trip through
   `analysis/analysis.cif`.
3. Fit bounds, bound provenance, start value, and start uncertainty
   round-trip by parameter unique name.
4. Live structure or experiment parameter values remain the calculation
   source of truth after load.
5. Mismatched deterministic result projections warn and keep live
   parameter values.
6. Unknown fit-state schema versions warn clearly.
7. Older projects without fit-state categories still load.

### Step 3: Add Bayesian Sidecar And Display Tests

Files likely to change:

- `tests/unit/easydiffraction/analysis/fit_helpers/`
- `tests/unit/easydiffraction/display/test_plotting.py`
- `tests/unit/easydiffraction/project/test_display.py`
- `tests/unit/easydiffraction/project/test_project_load.py`
- `docs/dev/plans/analysis-cif-fit-state.md`

Tests to add:

1. Bayesian summary-only restore works when `analysis/results.h5` is
   missing and emits a clear warning.
2. Posterior sample arrays round-trip through `analysis/results.h5`.
3. Manifest rows and HDF5 dataset shapes are validated.
4. Posterior distributions use cache arrays when valid.
5. Posterior pair plots use cache arrays when valid and preserve sample
   pairing semantics for contours.
6. Posterior predictive displays use saved predictive arrays when valid.
7. Recompute paths remain available when runtime posterior samples are
   present but caches are absent.

### Step 4: Run Verification Commands

Run in this order from the repository root:

```text
pixi run test-structure-check
pixi run fix
pixi run check
pixi run unit-tests
pixi run integration-tests
pixi run script-tests
```

Notes:

- `pixi run fix` may regenerate `docs/dev/package-structure/full.md` and
  `docs/dev/package-structure/short.md`. Accept those generated changes
  if the command produced them.
- If a command fails for an unrelated existing problem, do not fix
  unrelated code. Record the failure and ask for guidance.

## Files Most Likely To Change

Implementation files:

- `pyproject.toml`
- `src/easydiffraction/analysis/analysis.py`
- `src/easydiffraction/analysis/enums.py`
- `src/easydiffraction/analysis/fitting.py`
- `src/easydiffraction/analysis/categories/`
- `src/easydiffraction/analysis/fit_helpers/reporting.py`
- `src/easydiffraction/analysis/fit_helpers/bayesian.py`
- `src/easydiffraction/analysis/minimizers/base.py`
- `src/easydiffraction/analysis/minimizers/bumps.py`
- `src/easydiffraction/analysis/minimizers/bumps_dream.py`
- `src/easydiffraction/analysis/minimizers/lmfit.py`
- `src/easydiffraction/io/cif/serialize.py`
- `src/easydiffraction/project/project.py`
- `src/easydiffraction/project/display.py`
- `src/easydiffraction/display/plotting.py`

Test files:

- `tests/unit/easydiffraction/analysis/`
- `tests/unit/easydiffraction/io/cif/`
- `tests/unit/easydiffraction/project/`
- `tests/unit/easydiffraction/display/`
- `tests/functional/test_fitting_workflow.py`
- `tests/integration/fitting/`

Documentation files:

- `docs/dev/adrs/suggestions/analysis-cif-fit-state.md`
- `docs/dev/plans/analysis-cif-fit-state.md`

## Do Not Change Without Approval

- Do not serialize posterior summaries inside structure or experiment
  CIF files.
- Do not rename `Project`, `project.cif`, or the existing saved project
  layout.
- Do not remove the legacy `analysis.cif` root fallback in
  `Project.load()`.
- Do not add a generic posterior-minimizer capability abstraction until
  there is a second concrete posterior-capable minimizer.
- Do not change tutorial notebooks directly. Edit tutorial `.py` files
  and run notebook preparation only if the user asks for tutorial work.
- Do not persist raw backend result objects, optimizer instances, DREAM
  drivers, or ArviZ objects.

## Suggested Pull Request

Title: Persist analysis fit state in saved projects

Description: Save fit bounds, result summaries, and Bayesian result
manifests with projects so users can reopen fitted analyses with the
same fit-state and posterior display context available.
