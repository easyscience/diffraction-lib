# Bayesian Analysis Implementation Plan

**Status:** Planned **Feature name:** `bayesian-analysis` **Suggested
branch:** `feature/bayesian-analysis` **Design doc:**
`docs/dev/bayesian-analysis-design.md`

## Context

This plan follows `.github/copilot-instructions.md`. The instructions
refer to `docs/dev/architecture.md`, but this checkout does not contain
that file. The matching living architecture document used for this plan
is `docs/dev/architecture.md`.

Relevant current seams:

- `src/easydiffraction/analysis/categories/fit/default.py`
- `src/easydiffraction/analysis/analysis.py`
- `src/easydiffraction/analysis/fitting.py`
- `src/easydiffraction/analysis/minimizers/base.py`
- `src/easydiffraction/analysis/minimizers/bumps.py`
- `src/easydiffraction/analysis/minimizers/enums.py`
- `src/easydiffraction/analysis/minimizers/factory.py`
- `src/easydiffraction/analysis/minimizers/__init__.py`
- `src/easydiffraction/analysis/fit_helpers/reporting.py`
- `src/easydiffraction/display/plotting.py`

## Decisions

- Add Bayesian sampling as a normal minimizer tag: `'bumps (dream)'`.
- Keep `project.analysis.fit()` as the execution entry point.
- Keep posterior chains runtime-only in `BayesianFitResults`.
- Do not add posterior chain export in phase 1.
- Add `plot_posterior_predictive(...)` in phase 1.
- Add optional `random_seed` support for `'bumps (dream)'`.
- Generate and record a seed when the user does not provide one.
- Reject non-`None` `random_seed` for deterministic minimizers.
- Treat sampler completion and convergence quality separately.
- Use `success=False` only when DREAM fails or no usable posterior
  samples exist.
- Store and display convergence diagnostics; warn on poor convergence.
- Start with an internal posterior predictive draw cap of 200.

## Scope

Phase 1 delivers implementation only. Do not add or run tests in phase 1
unless the user explicitly asks. Stop after phase 1 and request review.

Phase 2 delivers verification only. Add/update tests, then run the
commands listed in this plan.

## Agent Execution Rule

When an AI agent follows this plan, every completed phase 1
implementation step must be staged with explicit paths and committed
locally before moving to the next implementation step or the phase 1
review gate. Commits must be atomic, single-purpose, and aligned with
the step just completed.

If implementation uncovers a serious requirement, risk, design issue, or
scope change not covered by this plan, stop and ask for clarification or
approval before proceeding.

## Status Checklist

- [x] Repository context gathered.
- [x] Design decisions recorded.
- [ ] Phase 1 implementation complete.
- [ ] Phase 1 review approved.
- [ ] Phase 2 tests added.
- [ ] Phase 2 verification commands completed.

## Phase 1: Implementation

### Step 1: Register The DREAM Minimizer

- [ ] Add `BUMPS_DREAM = 'bumps (dream)'` to `MinimizerTypeEnum`.
- [ ] Add a human-readable enum description.
- [ ] Add `src/easydiffraction/analysis/minimizers/bumps_dream.py`.
- [ ] Register `BumpsDreamMinimizer` with `MinimizerFactory`.
- [ ] Import `BumpsDreamMinimizer` from
      `src/easydiffraction/analysis/minimizers/__init__.py`.
- [ ] Update `docs/dev/architecture.md` minimizer tag tables if the
      implementation changes the documented supported tags.

Likely files:

- `src/easydiffraction/analysis/minimizers/enums.py`
- `src/easydiffraction/analysis/minimizers/bumps_dream.py`
- `src/easydiffraction/analysis/minimizers/__init__.py`
- `docs/dev/architecture.md`

Suggested commit message:

```text
Register BUMPS DREAM minimizer
```

### Step 2: Add Bayesian Result Models

- [ ] Add `BayesianFitResults`.
- [ ] Add `PosteriorSamples`.
- [ ] Add `PosteriorParameterSummary`.
- [ ] Add `PosteriorPredictiveSummary`.
- [ ] Keep public constructors explicit; do not use `**kwargs`.
- [ ] Add NumPy-style docstrings for public classes and methods.
- [ ] Provide `PosteriorSamples.to_arviz()` for plotting integration.

Likely files:

- `src/easydiffraction/analysis/fit_helpers/bayesian.py`
- `src/easydiffraction/analysis/fit_helpers/reporting.py`
- `src/easydiffraction/analysis/fit_helpers/__init__.py`

Suggested commit message:

```text
Add Bayesian fit result models
```

### Step 3: Thread Random Seed Through Fit Execution

- [ ] Add optional `random_seed: int | None = None` to `Fit.run(...)`
      and `Fit.__call__(...)`.
- [ ] Thread `random_seed` through `Analysis._run_fit(...)`,
      `_fit_single(...)`, `_fit_joint(...)`, and `Fitter.fit(...)`.
- [ ] Thread `random_seed` through `MinimizerBase.fit(...)`.
- [ ] Reject non-`None` `random_seed` in deterministic minimizers with a
      clear `ValueError`.
- [ ] Let `BumpsDreamMinimizer` generate a seed when `random_seed` is
      `None`.
- [ ] Record the user-provided or generated seed in
      `BayesianFitResults.sampler_settings`.

Likely files:

- `src/easydiffraction/analysis/categories/fit/default.py`
- `src/easydiffraction/analysis/analysis.py`
- `src/easydiffraction/analysis/fitting.py`
- `src/easydiffraction/analysis/minimizers/base.py`
- `src/easydiffraction/analysis/minimizers/bumps_dream.py`

Suggested commit message:

```text
Thread random seed through fitting
```

### Step 4: Implement DREAM Sampling

- [ ] Reuse `_EasyDiffractionFitness` or extract a shared BUMPS helper
      only if needed.
- [ ] Build BUMPS parameters from sampled EasyDiffraction parameters.
- [ ] Validate finite bounds, bound ordering, and start values before
      sampling.
- [ ] Preserve parameter order across BUMPS parameters, posterior
      arrays, summaries, and MAP commit.
- [ ] Run BUMPS DREAM with internal defaults.
- [ ] Commit the MAP or best posterior sample to project parameters.
- [ ] Restore starting values if the sampler fails before producing
      usable samples.
- [ ] Store raw BUMPS output as `engine_result` only after stable fields
      have been normalized into EasyDiffraction-owned result objects.

Likely files:

- `src/easydiffraction/analysis/minimizers/bumps.py`
- `src/easydiffraction/analysis/minimizers/bumps_dream.py`
- `src/easydiffraction/analysis/fit_helpers/bayesian.py`

Suggested commit message:

```text
Implement BUMPS DREAM sampling
```

### Step 5: Add Bayesian Display

- [ ] Make `BayesianFitResults.display_results(...)` render sampler
      status, diagnostics, settings, and posterior parameter summaries.
- [ ] Keep deterministic `FitResults.display_results(...)` unchanged.
- [ ] Ensure `analysis.display.fit_results()` continues to dispatch
      through the active result object.
- [ ] Display poor convergence prominently without hiding usable
      posterior summaries.

Likely files:

- `src/easydiffraction/analysis/fit_helpers/bayesian.py`
- `src/easydiffraction/analysis/fit_helpers/reporting.py`

Suggested commit message:

```text
Display Bayesian fit summaries
```

### Step 6: Add Posterior Correlations

- [ ] Extend `plot_param_correlations()` to detect
      `BayesianFitResults.posterior_samples`.
- [ ] Compute the correlation matrix from flattened posterior samples.
- [ ] Preserve deterministic covariance and engine-derived behavior.
- [ ] Preserve current thresholding and lower-triangle display behavior.

Likely files:

- `src/easydiffraction/display/plotting.py`
- `src/easydiffraction/analysis/fit_helpers/bayesian.py`

Suggested commit message:

```text
Plot posterior parameter correlations
```

### Step 7: Add Bayesian Posterior Plots

- [ ] Add `plot_posterior_pairs(...)`.
- [ ] Add `plot_param_distribution(param, ...)`.
- [ ] Use `PosteriorSamples.to_arviz()` internally where practical.
- [ ] Accept parameter objects, unique names, and user-facing labels for
      one-parameter selection.
- [ ] Fail ambiguous string matches with a clear list of matches.
- [ ] Warn clearly when Bayesian-only plots are called on deterministic
      results.

Likely files:

- `src/easydiffraction/display/plotting.py`
- `src/easydiffraction/analysis/fit_helpers/bayesian.py`

Suggested commit message:

```text
Add posterior distribution plots
```

### Step 8: Add Posterior Predictive Plots

- [ ] Generate posterior predictive summaries from a capped subset of
      posterior draws.
- [ ] Store summaries in `BayesianFitResults.posterior_predictive`.
- [ ] Add `plot_posterior_predictive(expt_name, style='band', ...)`.
- [ ] Support `style='band'` and `style='draws'` initially.
- [ ] Extend `plot_meas_vs_calc(...)` to show a 95% credible band when
      posterior predictive summaries are available.
- [ ] Keep experiment data categories responsible only for measured,
      current calculated, and current background patterns.

Likely files:

- `src/easydiffraction/display/plotting.py`
- `src/easydiffraction/analysis/minimizers/bumps_dream.py`
- `src/easydiffraction/analysis/fit_helpers/bayesian.py`

Suggested commit message:

```text
Add posterior predictive plotting
```

## Phase 1 Review Gate

- [ ] Inspect `git status --short`.
- [ ] Inspect the diff for unrelated changes.
- [ ] Confirm every phase 1 step has an atomic local commit.
- [ ] Present the implementation summary for review.
- [ ] Do not start phase 2 until the user approves verification work.

## Phase 2: Verification

### Test Additions

- [ ] Add unit tests for enum and factory registration.
- [ ] Add unit tests for finite-bound validation.
- [ ] Add unit tests for start-value-inside-bounds validation.
- [ ] Add unit tests for `random_seed` behavior.
- [ ] Add unit tests for deterministic minimizer seed rejection.
- [ ] Add unit tests for parameter order preservation.
- [ ] Add unit tests for MAP commit and restore-on-failure behavior.
- [ ] Add unit tests for Bayesian display output.
- [ ] Add unit tests for posterior sample correlation calculation.
- [ ] Add unit tests for posterior predictive summary generation.
- [ ] Add plotting smoke tests using small posterior fixtures.
- [ ] Add integration coverage for a small bounded DREAM refinement.
- [ ] Add integration coverage for explicit LM pre-fit followed by
      DREAM.
- [ ] Add serialization coverage proving posterior chains are not saved.

Likely test files:

- `tests/unit/easydiffraction/analysis/minimizers/test_bumps_dream.py`
- `tests/unit/easydiffraction/analysis/minimizers/test_enums.py`
- `tests/unit/easydiffraction/analysis/fit_helpers/test_bayesian.py`
- `tests/unit/easydiffraction/display/test_plotting.py`
- `tests/integration/fitting/test_bayesian_dream.py`
- `tests/integration/fitting/test_project_load.py`

Suggested commit message:

```text
Test Bayesian DREAM workflow
```

### Verification Commands

- [ ] `pixi run test-structure-check`
- [ ] `pixi run fix`
- [ ] `pixi run check`
- [ ] `pixi run unit-tests`
- [ ] `pixi run integration-tests`
- [ ] `pixi run script-tests`

If `pixi run fix` regenerates package-structure docs, accept the
generated changes and include them only in the verification commit where
they were produced.

## Non-Blocking Implementation Discovery

The BUMPS DREAM return object must be inspected during implementation.
If the stable public fields are insufficient for posterior samples,
log-likelihood values, or diagnostics, normalize the available fields
into EasyDiffraction-owned value objects and keep `engine_result`
opaque. If this prevents a required feature, stop and ask before
changing scope.

## Suggested Pull Request

**Title:** Add Bayesian DREAM sampling and posterior plots

**Description:** Adds Bayesian refinement through the BUMPS DREAM
sampler, including reproducible runs, posterior parameter summaries, and
posterior predictive plots so users can inspect uncertainty in fitted
diffraction models.
