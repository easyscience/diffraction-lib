# Plan: Emcee Minimizer

> This plan follows
> [`.github/copilot-instructions.md`](../../../.github/copilot-instructions.md).
> No deliberate exceptions.

## Prerequisite

This plan **must not start** until
[`minimizer-category-consolidation.md`](minimizer-category-consolidation.md)
is fully implemented, merged, and the ADR is in `accepted/`. The new
`Analysis.minimizer` + `Analysis.minimizer_type` surface is a hard
dependency; without it this plan duplicates work.

## ADR

Implements the emcee follow-on described in §1, §5, §6 and §9
of
[`docs/dev/adrs/accepted/minimizer-category-consolidation.md`](../adrs/accepted/minimizer-category-consolidation.md)
(after the prerequisite plan promotes it). No new ADR is required;
this plan is a direct application of the rules already accepted there.

If implementation uncovers a design question not covered by the ADR
(for example, resume semantics on parameter-set mismatch), stop and
ask before proceeding.

## Branch and PR

- Branch: `feature/emcee-minimizer`. Do not push unless asked.
- Each step in §"Implementation steps (Phase 1)" must be staged with
  explicit paths and committed locally **before** moving to the next
  step.
- After P1.7, stop and wait for the user review gate before starting
  Phase 2.

## Decisions already made (from the ADR)

1. emcee is exposed as a new concrete `minimizer` class
   (`EmceeMinimizer`) registered under
   `MinimizerTypeEnum.EMCEE = 'emcee'`.
2. Sampler settings reuse the verbose attribute names from ADR §5
   (`sampling_steps`, `burn_in_steps`, `thinning_interval`,
   `population_size`, `parallel_workers`, `initialization_method`,
   `random_seed`) with an emcee-specific addition: `proposal_moves`.
3. Resume uses emcee's `HDFBackend` against the `/emcee_chain` group
   of the same `analysis/results.h5` file used by the snapshot writer.
   No separate sidecar file. A non-resume `fit()` follows the
   prerequisite plan's lifecycle and **truncates** `results.h5`
   (after the standard warning); resume opens it in append mode.
4. The `fit()` action accepts an explicit `resume=True, extra_steps=N`
   pair when the active minimizer supports incremental sampling. For
   other minimizers, passing `resume=True` raises immediately.
5. emcee outputs translate to the existing `BayesianFitResults` shape
   exactly as DREAM does — same `PosteriorSamples`,
   `PosteriorParameterSummary`, etc. — so plotting and display code
   needs no specialization.

## Open questions

- **Resume after parameter-set change.** If the user fits, then edits
  which parameters are free, then calls `fit(resume=True, ...)`,
  emcee's HDFBackend will fail because the dimensionality changed.
  Plan default: detect mismatch and raise with a clear message
  asking the user to start a fresh run. Confirm during P1.4.
- **Resume after a non-emcee fit.** If the user runs DREAM, then sets
  `minimizer_type = 'emcee'`, then calls `fit(resume=True, ...)`,
  the `/emcee_chain` group will be missing. Plan default: raise a
  clear `ValueError` pointing at the prerequisite-plan lifecycle
  rule ("a new fit overwrites the file").
- **Move-mix semantics.** emcee supports proposal-move mixtures (e.g.
  70 % stretch + 30 % differential evolution). The ADR exposes
  `proposal_moves` as a single string. Plan default: limit
  `proposal_moves` to single-move strings for v1 (`stretch`, `de`,
  `de_snooker`, `walk`). Mixtures deferred to a later plan. Record
  this in the descriptor's `description=`.

## Concrete files likely to change

Created:

- `src/easydiffraction/analysis/categories/minimizer/emcee.py`
  (concrete `EmceeMinimizer` class).
- `tests/unit/easydiffraction/analysis/categories/minimizer/test_emcee.py`.
- `tests/integration/fitting/test_emcee.py` (cross-check vs DREAM on a
  shared toy fit; assert posterior medians agree to within tolerance).
- `docs/docs/tutorials/ed-23.py` (emcee + resume tutorial).

Modified:

- `src/easydiffraction/analysis/minimizers/enums.py` (add
  `MinimizerTypeEnum.EMCEE`).
- `src/easydiffraction/analysis/categories/minimizer/__init__.py` (add
  the explicit `EmceeMinimizer` import to trigger registration).
- `src/easydiffraction/analysis/categories/minimizer/factory.py` (the
  factory may need no change if registration uses `@Factory.register`).
- `src/easydiffraction/analysis/analysis.py` (`fit()` signature gains
  `resume: bool = False, extra_steps: int | None = None`; route to
  the live engine appropriately).
- `src/easydiffraction/io/results_sidecar.py` (read path: when
  `/emcee_chain` is present, expose a small helper to construct an
  `emcee.backends.HDFBackend(path, name='emcee_chain', read_only=...)`).
- `pyproject.toml` and `pixi.toml` (add `emcee>=3.1` dependency).

## Implementation steps (Phase 1)

- [ ] **P1.1 — Add emcee dependency.**
  Add `emcee>=3.1` to `pyproject.toml` and `pixi.toml`. Run
  `pixi install` locally to verify resolution.
  Commit: `Add emcee dependency`

- [ ] **P1.2 — Register `MinimizerTypeEnum.EMCEE`.**
  Add the enum member with value `'emcee'`. No other code wiring yet.
  Commit: `Register emcee minimizer enum value`

- [ ] **P1.3 — Add `EmceeMinimizer` concrete class.**
  Class-body descriptor declarations following the ADR §5 / §8
  template (`sampling_steps=5000`, `population_size=32`, …,
  `proposal_moves='stretch'`). Implement `_native_kwargs()` mapping
  to emcee's `EnsembleSampler.run_mcmc(nsteps=..., progress=...,
  ...)`. Update
  `src/easydiffraction/analysis/categories/minimizer/__init__.py` to
  import `EmceeMinimizer` (registration trigger).
  Commit: `Add EmceeMinimizer concrete class`

- [ ] **P1.4 — Implement run + resume via HDFBackend.**
  In the live solver layer (the new `Analysis._engine` path
  introduced in the prerequisite plan), instantiate
  `emcee.backends.HDFBackend(project.analysis_dir / 'results.h5',
  name='emcee_chain')`. Lifecycle:
  - **New fit** (`fit()` without `resume`): the prerequisite plan's
    `Analysis.fit()` truncates `results.h5` *before* the engine is
    asked to sample (P1.10 in that plan). After truncation, the
    `HDFBackend` is instantiated against the freshly recreated file
    and `EnsembleSampler.run_mcmc(...)` is called.
  - **Resume** (`fit(resume=True, extra_steps=N)`):
    - require the active minimizer's `MinimizerTypeEnum` to support
      resume (currently only `EMCEE`);
    - require `results.h5` to exist and contain a `/emcee_chain`
      group (raise `FileNotFoundError` / `ValueError` with a clear
      message otherwise);
    - reload the backend, validate `backend.shape` matches the
      current parameter count (raise `ValueError` on mismatch with a
      clear message and recommend starting a fresh fit);
    - bypass the truncate-and-warn step;
    - call `run_mcmc(initial_state=None, nsteps=N, progress=True,
      skip_initial_state_check=True)` to extend the chain.
  Translate the sampler's state to `BayesianFitResults` exactly like
  DREAM, populating `Parameter.posterior` via the existing helpers.
  Commit: `Implement emcee run and resume via HDFBackend`

- [ ] **P1.5 — Plug emcee outputs into existing posterior pipeline.**
  Verify the existing sidecar writer for `/posterior`,
  `/distribution_cache`, `/pair_cache`, `/predictive` correctly
  picks up emcee results. Adjust only where emcee surfaces data
  differently from DREAM (e.g. `EnsembleSampler.get_chain(flat=False,
  discard=burn, thin=thin)` vs the DREAM extraction helper). Cache
  derivations (KDE, pair grids) must match the existing format.
  Commit: `Route emcee posterior through sidecar pipeline`

- [ ] **P1.6 — Add `ed-23.py` tutorial.**
  New notebook source at `docs/docs/tutorials/ed-23.py`: demonstrate
  `analysis.minimizer_type = 'emcee'`, a short run, save, resume with
  `extra_steps=`, and a posterior plot. Run
  `pixi run notebook-prepare` to generate the `.ipynb`.
  Commit: `Add ed-23 emcee tutorial`

- [ ] **P1.7 — Phase 1 review gate.**
  Stop and request user review before Phase 2.

## Verification (Phase 2)

Same log-capture pattern as the prerequisite plan; commands repeated
for completeness.

- [ ] **P2.1 — Add unit + integration tests.**
  - `tests/unit/easydiffraction/analysis/categories/minimizer/test_emcee.py`:
    descriptor defaults, native-key mapping, swap behavior, resume
    parameter-set-mismatch error path (no real sampler).
  - `tests/integration/fitting/test_emcee.py`: end-to-end fit on a
    small synthetic problem; resume; assert posterior medians agree
    with a DREAM run within tolerance.

- [ ] **P2.2 — Auto-fixes and static checks.**
  ```
  pixi run fix > /tmp/easydiffraction-fix.log 2>&1; \
    fix_exit_code=$?; \
    tail -n 200 /tmp/easydiffraction-fix.log; \
    exit $fix_exit_code
  ```
  ```
  pixi run check > /tmp/easydiffraction-check.log 2>&1; \
    check_exit_code=$?; \
    tail -n 200 /tmp/easydiffraction-check.log; \
    exit $check_exit_code
  ```

- [ ] **P2.3 — Unit tests.**
  ```
  pixi run unit-tests > /tmp/easydiffraction-unit-tests.log 2>&1; \
    unit_tests_exit_code=$?; \
    tail -n 200 /tmp/easydiffraction-unit-tests.log; \
    exit $unit_tests_exit_code
  ```

- [ ] **P2.4 — Integration tests.**
  ```
  pixi run integration-tests > /tmp/easydiffraction-integration-tests.log 2>&1; \
    integration_tests_exit_code=$?; \
    tail -n 200 /tmp/easydiffraction-integration-tests.log; \
    exit $integration_tests_exit_code
  ```

- [ ] **P2.5 — Script tests.**
  ```
  pixi run script-tests > /tmp/easydiffraction-script-tests.log 2>&1; \
    script_tests_exit_code=$?; \
    tail -n 200 /tmp/easydiffraction-script-tests.log; \
    exit $script_tests_exit_code
  ```

## Suggested Pull Request

**Title:** Add emcee Bayesian sampler with resumable runs

**Description (user-facing):**

EasyDiffraction adds emcee — a widely-used affine-invariant MCMC
sampler — as a second Bayesian fitter. It is selected exactly like the
existing samplers:

- `project.analysis.minimizer_type = 'emcee'`
- `project.analysis.minimizer.sampling_steps = 5000`
- `project.analysis.fit()`

Long runs can be **resumed** without starting over:

- `project.analysis.fit(resume=True, extra_steps=2000)`

emcee's chain state lives inside the same `analysis/results.h5` file
as the other posterior data, so saving and reopening a project is a
single-file affair. Plots, parameter posteriors, and tables work the
same as for the existing DREAM sampler, so switching between samplers
to cross-check results is straightforward.

A new tutorial (`ed-23`) walks through a short run, saving the
project, and resuming for additional steps.
