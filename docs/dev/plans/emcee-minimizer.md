# Plan: Emcee Minimizer

> This plan follows
> [`.github/copilot-instructions.md`](../../../.github/copilot-instructions.md).
> No deliberate exceptions.

## Prerequisite

This plan depends on three accepted ADRs, all merged on `develop`:

- [`minimizer-category-consolidation`](../adrs/accepted/minimizer-category-consolidation.md)
  — unified `minimizer` category with `BayesianMinimizerBase` and the
  `BumpsDreamMinimizer` Bayesian precedent.
- [`switchable-category-owned-selectors`](../adrs/accepted/switchable-category-owned-selectors.md)
  — `analysis.minimizer.type = 'X'` is the writable surface; no
  owner-level `<owner>.<cat>_type` shims.
- [`minimizer-input-output-split`](../adrs/accepted/minimizer-input-output-split.md)
  — fit-filled outputs live on a paired `analysis.fit_result`
  instance (`LeastSquaresFitResult` or `BayesianFitResult`), not on
  the minimizer.

emcee inherits the entire paired surface for free:
`BayesianMinimizerBase._fit_result_class = BayesianFitResult`, so
`Analysis._swap_minimizer` instantiates both
`EmceeMinimizer` (inputs) and `BayesianFitResult` (outputs)
atomically.

## ADR

This plan implements the emcee follow-on described in §1, §5, §6 and
§9 of
[`docs/dev/adrs/accepted/minimizer-category-consolidation.md`](../adrs/accepted/minimizer-category-consolidation.md).
No new ADR is required.

If implementation uncovers a design question not covered by the
ADRs (e.g. resume semantics on parameter-set mismatch, or
`InitializationMethodEnum` ↔
`DreamPopulationInitializationEnum` reconciliation), stop and ask
before proceeding.

## Branch and PR

- Branch: `emcee-minimizer`. Do not push unless asked.
- Each step in §"Implementation steps (Phase 1)" must be staged with
  explicit paths and committed locally **before** moving to the next
  step. See `.github/copilot-instructions.md` → **Commits**.
- After P1.8, stop and wait for the user review gate before starting
  Phase 2.

## Decisions already made (from the accepted ADRs)

1. emcee is a new concrete Bayesian minimizer registered under
   `MinimizerTypeEnum.EMCEE = 'emcee'`. Selected via
   `project.analysis.minimizer.type = 'emcee'`.
2. emcee inherits two paired surfaces from `BayesianMinimizerBase`:
   - **Settings** (writable inputs): `sampling_steps`,
     `burn_in_steps`, `thinning_interval`, `population_size`,
     `parallel_workers`, `initialization_method`, `random_seed` — all
     declared by `BayesianMinimizerBase.__init__`. emcee may override
     class-level defaults (e.g. `sampling_steps=5000`,
     `population_size=32`) and adds one emcee-specific input
     `proposal_moves`.
   - **Outputs** (fit-filled, internal `_set_*`): `acceptance_rate_mean`,
     `gelman_rubin_max`, `effective_sample_size_min`,
     `best_log_posterior`, `point_estimate_name`,
     `sampler_completed`, `credible_interval_inner/outer` — already
     on `BayesianFitResult`, not on the minimizer. emcee's projection
     writer calls `self.fit_result._set_*` (not `self.minimizer._set_*`).
3. Verbose attribute names map to emcee native kwargs via
   `EmceeMinimizer._native_key_map` (overrides the DREAM-style
   defaults on `BayesianMinimizerBase._native_key_map`):

   | Verbose | emcee native |
   | --- | --- |
   | `sampling_steps` | `nsteps` |
   | `burn_in_steps` | `nburn` |
   | `thinning_interval` | `thin` |
   | `population_size` | `nwalkers` |
   | `parallel_workers` | `pool` |
   | `initialization_method` | (custom — see §6) |
   | `random_seed` | `random_seed` |
4. Resume uses emcee's `HDFBackend` against the `/emcee_chain` group
   of the same `analysis/results.h5` file used by the snapshot
   writer. No separate sidecar file. A non-resume `fit()` follows
   the prerequisite plan's lifecycle and **truncates** `results.h5`
   (after the standard warning); resume opens it in append mode.
5. `Analysis.fit()` gains an optional `resume=True, extra_steps=N`
   call shape for minimizers that support incremental sampling. For
   other minimizers, passing `resume=True` raises immediately.
6. emcee outputs translate to the existing `BayesianFitResults`
   runtime shape (plural — note the singular `BayesianFitResult` is
   the persistence category, not the runtime object) exactly as
   DREAM does — same `PosteriorSamples`, `PosteriorParameterSummary`,
   etc. Plotting and display code needs no specialization.
7. Two `EmceeMinimizer` classes coexist with the same DREAM
   precedent:
   - `src/easydiffraction/analysis/categories/minimizer/emcee.py`
     — the persisted **category** class (`BayesianMinimizerBase`
     subclass) used for CIF persistence and the user-facing setter
     surface.
   - `src/easydiffraction/analysis/minimizers/emcee.py` — the live
     **engine** class registered with the engine
     `MinimizerFactory`. Holds the `emcee.EnsembleSampler` instance
     and runs the sampler.
   This mirrors the existing `BumpsDreamMinimizer` split between
   `categories/minimizer/bumps_dream.py` and
   `minimizers/bumps_dream.py`.

## Open questions

- **Resume after parameter-set change.** If the user fits, then
  edits which parameters are free, then calls
  `fit(resume=True, ...)`, emcee's `HDFBackend.shape` mismatches the
  current parameter count. Plan default: detect mismatch in P1.5 and
  raise `ValueError` with a clear "start a fresh run" message.
- **Resume after a non-emcee fit.** If the user runs DREAM, switches
  to emcee, and calls `fit(resume=True, ...)`, the `/emcee_chain`
  group will be missing. Plan default: raise `ValueError` pointing
  at the prerequisite ADR's lifecycle rule ("a new fit overwrites
  the file").
- **`InitializationMethodEnum` ↔ `DreamPopulationInitializationEnum`
  reconciliation** (deferred from review-8 F6 of the consolidation
  work). emcee uses different init methods (`ball`, `uniform`,
  `prior`); DREAM exposes a broader engine-level enum with `EPS`,
  `COV`, `LHS`, `RANDOM`. The persisted user-facing enum
  (`InitializationMethodEnum`) is narrower
  (`LATIN_HYPERCUBE`, `BALL`, `UNIFORM`, `PRIOR`). P1.3 must decide
  whether to narrow DREAM's engine enum to match, or accept the
  asymmetry. Recommend: keep DREAM's broader engine enum (legacy
  DREAM users may pass `EPS`/`COV`/`RANDOM` directly to the engine)
  but document that only `LATIN_HYPERCUBE` is persistable for DREAM;
  emcee accepts `BALL`/`UNIFORM`/`PRIOR` only.
- **Move-mix semantics.** emcee supports proposal-move mixtures
  (e.g. 70 % stretch + 30 % differential evolution). The
  consolidation ADR §5 exposes `proposal_moves` as a single string
  descriptor. Plan default: limit `proposal_moves` to single-move
  strings for v1 (`stretch`, `de`, `de_snooker`, `walk`). Mixtures
  deferred to a follow-on plan. Record this in the descriptor's
  `description=` text.

## Cleanup opportunities inherited from earlier work

The input/output-split work left four cleanup items still open in
[`docs/dev/issues/open.md`](../issues/open.md) that touch code this
plan modifies. Fold them in opportunistically while the surrounding
code is already being edited; the plan does not block on them.

- **#100 — Collapse duplicate predictive-cache-key helpers.**
  `Analysis._predictive_cache_key`
  ([analysis.py:528](../../../src/easydiffraction/analysis/analysis.py))
  and `Plotter._posterior_predictive_key`
  ([plotting.py:3823](../../../src/easydiffraction/display/plotting.py))
  build the identical string; keep one canonical helper. P1.6 may
  touch the predictive plotting path while validating emcee
  posterior emission.
- **#101 — Remove dead branch in
  `Analysis._fit_state_categories`.** Both branches return the same
  list since the Bayesian categories were absorbed. One-line fix at
  [analysis.py:1184-1205](../../../src/easydiffraction/analysis/analysis.py).
- **#102 — Drop compute-and-ignore `result_kind` validation.**
  `_restore_persisted_fit_state`
  ([serialize.py:590-606](../../../src/easydiffraction/io/cif/serialize.py))
  calls `FitResultKindEnum(result_kind_value)` for its side effect
  only. Move the warning into the descriptor setter, or extract a
  validator helper.
- **#103 — Make `_sync_engine_from_minimizer_category` skip-keys
  declarative.** This plan adds `proposal_moves` as a second
  engine-level "ambient" key (alongside `random_seed`). The current
  magic-string skip at
  [analysis.py:1138](../../../src/easydiffraction/analysis/analysis.py)
  should become a class-level
  `_engine_sync_skip_keys: ClassVar[frozenset[str]] = frozenset(...)`
  on `MinimizerCategoryBase` before the second member lands.
  Recommend addressing as part of P1.5.

When the matching open-issue is fully resolved, move it to
[`closed.md`](../issues/closed.md) and update
[`adrs/index.md`](../adrs/index.md) if relevant.

## Concrete files likely to change

### Created

- `src/easydiffraction/analysis/categories/minimizer/emcee.py` —
  persisted **category** class `EmceeMinimizer(BayesianMinimizerBase)`
  with class-level defaults, `_engine_metadata`, and the overridden
  `_native_key_map`.
- `src/easydiffraction/analysis/minimizers/emcee.py` — live
  **engine** class `EmceeMinimizer(BayesianMinimizerEngineBase or
  equivalent)` registered with `MinimizerFactory`. Holds
  `emcee.EnsembleSampler` and the `HDFBackend`.
- `tests/unit/easydiffraction/analysis/categories/minimizer/test_emcee.py`.
- `tests/unit/easydiffraction/analysis/minimizers/test_emcee.py`.
- `tests/integration/fitting/test_emcee.py` (cross-check vs DREAM on
  a shared toy fit; assert posterior medians agree to within
  tolerance).
- `docs/docs/tutorials/ed-23.py` (emcee + resume tutorial).

### Modified

- `src/easydiffraction/analysis/minimizers/enums.py` — add
  `MinimizerTypeEnum.EMCEE = 'emcee'`.
- `src/easydiffraction/analysis/categories/minimizer/__init__.py`
  — add explicit `EmceeMinimizer` (category) import so registration
  fires.
- `src/easydiffraction/analysis/minimizers/__init__.py` (or the
  factory's package init) — add explicit `EmceeMinimizer` (engine)
  import so engine registration fires.
- `src/easydiffraction/analysis/categories/minimizer/bayesian_base.py`
  — only if review-8 F6 reconciliation (open question above) calls
  for narrowing the persisted enum surface; otherwise unchanged.
- `src/easydiffraction/analysis/analysis.py` — `fit()` signature
  gains `resume: bool = False, extra_steps: int | None = None`;
  validation + dispatch to engine. Wire `_engine_sync_skip_keys`
  (#103) before adding `proposal_moves` to the ambient set.
- `src/easydiffraction/io/results_sidecar.py` — read path: when
  `/emcee_chain` is present, expose a helper to construct an
  `emcee.backends.HDFBackend(path, name='emcee_chain',
  read_only=True)` for inspection/visualisation.
- `pyproject.toml` and `pixi.toml` — add `emcee>=3.1` dependency.

### Deleted

- None.

## Implementation steps (Phase 1)

Mark `[x]` as each step lands.

- [ ] **P1.1 — Add emcee dependency.** Add `emcee>=3.1` to
      `pyproject.toml` and `pixi.toml`. Run `pixi install` locally
      to verify resolution. Commit: `Add emcee dependency`

- [ ] **P1.2 — Register `MinimizerTypeEnum.EMCEE`.** Add the enum
      member with value `'emcee'` to
      `src/easydiffraction/analysis/minimizers/enums.py`. No other
      code wiring yet. Commit:
      `Register emcee minimizer enum value`

- [ ] **P1.3 — Add `EmceeMinimizer` category class.** New file
      `src/easydiffraction/analysis/categories/minimizer/emcee.py`.
      `EmceeMinimizer(BayesianMinimizerBase)` declares:
  - `type_info` with `tag=MinimizerTypeEnum.EMCEE` and a description.
  - `_engine_metadata: ClassVar[dict[str, str]] = {'optimizer_name':
    'emcee', 'method_name': 'stretch'}` (matching the
    `BumpsDreamMinimizer` precedent for the
    `_restore_fit_results_from_projection` lookup).
  - `_native_key_map` override mapping the verbose names to emcee's
    native kwargs (see §"Decisions already made" point 3).
  - Class-level defaults for emcee-specific values:
    `sampling_steps=5000`, `burn_in_steps=1000`,
    `thinning_interval=5`, `population_size=32`,
    `parallel_workers=0`, `proposal_moves='stretch'`.
  - `__init__` constructs descriptors via the inherited helpers
    (`_sampling_steps_descriptor(default)`, etc. from
    `BayesianMinimizerBase`) and adds a new `proposal_moves`
    descriptor with a `MembershipValidator` over the single-move
    set (`stretch`, `de`, `de_snooker`, `walk`).
  - **Decide the `InitializationMethodEnum` reconciliation** (open
    question above) before wiring. `EmceeMinimizer._supported_initialization_methods`
    should list `(BALL, UNIFORM, PRIOR)` regardless of the DREAM
    decision.

  Update
  `src/easydiffraction/analysis/categories/minimizer/__init__.py`
  to import `EmceeMinimizer` (registration trigger via
  `@MinimizerCategoryFactory.register`).

  The paired `BayesianFitResult` flows automatically because
  `BayesianMinimizerBase._fit_result_class = BayesianFitResult`; no
  wiring needed in this step.

  Commit: `Add EmceeMinimizer category class`

- [ ] **P1.4 — Add `EmceeMinimizer` engine class.** New file
      `src/easydiffraction/analysis/minimizers/emcee.py`. The engine
      class is registered with `MinimizerFactory` and holds the
      `emcee.EnsembleSampler` plus an `HDFBackend` attribute. Mirror
      the shape of
      [`bumps_dream.py BumpsDreamMinimizer`](../../../src/easydiffraction/analysis/minimizers/bumps_dream.py)
      — descriptor attributes (`burn`, `thin`, `pop`, `init`, …)
      that `Analysis._sync_engine_from_minimizer_category` writes to
      from the category's `_native_kwargs()`. The descriptor names
      on the engine must match the keys returned by
      `EmceeMinimizer._native_kwargs()` (i.e. emcee's native names —
      `nsteps`, `nburn`, `nwalkers`, `pool`).

      Engine method shape (sketch):

      ```python
      class EmceeMinimizer(BayesianMinimizerEngineBase):
          name = MinimizerTypeEnum.EMCEE
          method = 'stretch'

          def fit(self, *, structures, experiments, analysis,
                  resume=False, extra_steps=None, ...):
              backend = emcee.backends.HDFBackend(
                  path=analysis.project.info.path
                       / 'analysis' / 'results.h5',
                  name='emcee_chain',
                  read_only=False,
              )
              sampler = emcee.EnsembleSampler(
                  nwalkers=self.nwalkers,
                  ndim=len(free_params),
                  log_prob_fn=log_prob,
                  pool=self.pool,
                  moves=...,  # from proposal_moves
                  backend=backend,
              )
              if resume:
                  self._validate_resume(backend, free_params)
                  sampler.run_mcmc(None, nsteps=extra_steps,
                                   skip_initial_state_check=True,
                                   progress=True)
              else:
                  initial_state = self._initial_state(...)
                  sampler.run_mcmc(initial_state,
                                   nsteps=self.nsteps,
                                   progress=True)
              return self._build_results(sampler, ...)
      ```

      Register with the engine `MinimizerFactory` and update
      `src/easydiffraction/analysis/minimizers/__init__.py` (or the
      relevant package init) to import the engine class.

      Commit: `Add EmceeMinimizer engine class`

- [ ] **P1.5 — Wire `fit(resume=True, extra_steps=N)` on
      `Analysis`.** In
      `src/easydiffraction/analysis/analysis.py`:
  - `Analysis.fit()` gains keyword args `resume: bool = False,
    extra_steps: int | None = None`. Default behaviour (no resume)
    is unchanged.
  - When `resume=True`:
    - Validate that `self.minimizer.type ==
      MinimizerTypeEnum.EMCEE.value` (only emcee supports resume in
      v1). Raise `ValueError` with a clear message otherwise.
    - Require `extra_steps` to be a positive integer.
    - **Bypass** the `_warn_results_sidecar_overwrite` step and the
      `_clear_persisted_fit_state` reset — both would clobber the
      backend.
    - Forward `resume=True, extra_steps=N` to the live engine via
      the existing `Fitter` plumbing.

  Also address open issue #103: introduce
  `_engine_sync_skip_keys: ClassVar[frozenset[str]] = frozenset({'random_seed'})`
  on `MinimizerCategoryBase`, and update
  `_sync_engine_from_minimizer_category`
  ([analysis.py:1134-1146](../../../src/easydiffraction/analysis/analysis.py))
  to use it. `BayesianMinimizerBase` (or `EmceeMinimizer`
  directly) overrides the frozenset to include `'proposal_moves'`
  if/when the engine consumes that key under a different name than
  the category attribute.

  Commit: `Wire emcee resume into Analysis.fit`

- [ ] **P1.6 — Route emcee outputs into the existing fit_result and
      sidecar pipeline.** Verify the existing
      `_store_posterior_fit_projection`
      ([analysis.py](../../../src/easydiffraction/analysis/analysis.py))
      writes to `self.fit_result._set_*` (the
      `BayesianFitResult` instance auto-paired with the
      `EmceeMinimizer`) and that the `/posterior`,
      `/distribution_cache`, `/pair_cache`, `/predictive` groups in
      `results.h5` receive emcee output without modification.
      Adjust only where emcee surfaces data differently from
      DREAM (e.g. `EnsembleSampler.get_chain(flat=False,
      discard=burn, thin=thin)` vs the DREAM extraction helper).
      Cache derivations (KDE, pair grids) reuse the existing
      pipeline.

      Opportunistic cleanup: address open issue #100 if the
      predictive plotting path is being touched anyway. Collapse
      `Analysis._predictive_cache_key` and
      `Plotter._posterior_predictive_key` into one canonical helper.

      Commit: `Route emcee posterior through fit_result and sidecar`

- [ ] **P1.7 — Add `ed-23.py` tutorial.** New notebook source at
      `docs/docs/tutorials/ed-23.py` covering:
  - `project.analysis.minimizer.type = 'emcee'` (post-switchable
    syntax).
  - `project.analysis.minimizer.sampling_steps = 1000` (small for
    tutorial speed).
  - `project.analysis.fit()` and a posterior plot.
  - `project.save()`.
  - `project.analysis.fit(resume=True, extra_steps=500)` continues
    the chain.
  - Final posterior plot after resume.

  Run `pixi run notebook-prepare` to regenerate the `.ipynb`.

  Verification grep (must return empty against
  `docs/docs/tutorials/ed-23.py`):

  ```
  git grep -nE '\banalysis\.minimizer_type\b|\bminimizer\.runtime_seconds\b|\bminimizer\.gelman_rubin_max\b' docs/docs/tutorials/ed-23.py
  ```

  Commit: `Add ed-23 emcee tutorial`

- [ ] **P1.8 — Phase 1 review gate.** No code change. Stop and
      request user review. After approval, proceed to Phase 2.

## Verification (Phase 2)

Each command captures its log with a zsh-safe exit-code variable as
required by `.github/copilot-instructions.md` → **Workflow**.

- [ ] **P2.1 — Add unit + integration tests.**
  - `tests/unit/easydiffraction/analysis/categories/minimizer/test_emcee.py`:
    category-class descriptor defaults; `_native_key_map` override;
    pairing with `BayesianFitResult`; swap behavior; resume
    parameter-set-mismatch error path (no real sampler).
  - `tests/unit/easydiffraction/analysis/minimizers/test_emcee.py`:
    engine-class registration, descriptor defaults, native kwargs
    plumbing.
  - `tests/integration/fitting/test_emcee.py`: end-to-end fit on a
    small synthetic problem; resume; assert posterior medians
    agree with a DREAM run within tolerance.

  Layout check:

  ```
  pixi run test-structure-check > /tmp/easydiffraction-test-structure-check.log 2>&1; \
    test_structure_check_exit_code=$?; \
    tail -n 200 /tmp/easydiffraction-test-structure-check.log; \
    exit $test_structure_check_exit_code
  ```

- [ ] **P2.2 — Auto-fixes and static checks.**

  ```
  pixi run fix > /tmp/easydiffraction-fix.log 2>&1; \
    fix_exit_code=$?; \
    tail -n 200 /tmp/easydiffraction-fix.log; \
    exit $fix_exit_code
  ```

  Then:

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
sampler — as a second Bayesian fitter. It is selected exactly like
the existing samplers, via the uniform switchable-category surface:

```python
project.analysis.minimizer.type = 'emcee'
project.analysis.minimizer.sampling_steps = 5000
project.analysis.fit()
```

Long runs can be **resumed** without starting over:

```python
project.analysis.fit(resume=True, extra_steps=2000)
```

emcee's chain state lives inside the same `analysis/results.h5` file
as the other posterior data, so saving and reopening a project is a
single-file affair. Plots, parameter posteriors, and tables work the
same as for DREAM, so switching between samplers to cross-check
results is straightforward.

A new tutorial (`ed-23`) walks through a short run, saving the
project, and resuming for additional steps.
