# Plan: Emcee Minimizer

> This plan follows [`AGENTS.md`](../../../AGENTS.md). No deliberate
> exceptions.

## Prerequisite

This plan depends on three accepted ADRs, all merged on `develop`:

- [`minimizer-category-consolidation`](../adrs/accepted/minimizer-category-consolidation.md)
  — unified `minimizer` category with `BayesianMinimizerBase` and the
  `BumpsDreamMinimizer` Bayesian precedent.
- [`switchable-category-owned-selectors`](../adrs/accepted/switchable-category-owned-selectors.md)
  — `analysis.minimizer.type = 'X'` is the writable surface; no
  owner-level `<owner>.<cat>_type` shims.
- [`minimizer-input-output-split`](../adrs/accepted/minimizer-input-output-split.md)
  — fit-filled outputs live on a paired `analysis.fit_result` instance
  (`LeastSquaresFitResult` or `BayesianFitResult`), not on the
  minimizer.

emcee inherits the entire paired surface for free:
`BayesianMinimizerBase._fit_result_class = BayesianFitResult`, so
`Analysis._swap_minimizer` instantiates both `EmceeMinimizer` (inputs)
and `BayesianFitResult` (outputs) atomically.

## ADR

This plan implements the emcee follow-on described in §1, §5, §6 and §9
of
[`docs/dev/adrs/accepted/minimizer-category-consolidation.md`](../adrs/accepted/minimizer-category-consolidation.md).
No new ADR is required.

If implementation uncovers a design question not covered by the ADRs
(e.g. resume semantics on parameter-set mismatch, or
`InitializationMethodEnum` ↔ `DreamPopulationInitializationEnum`
reconciliation), stop and ask before proceeding.

## Branch and PR

- Branch: `emcee-minimizer`. Do not push unless asked.
- Each step in §"Implementation steps (Phase 1)" must be staged with
  explicit paths and committed locally **before** moving to the next
  step. See `AGENTS.md` → **Commits**.
- After P1.8, stop and wait for the user review gate before starting
  Phase 2.

## Decisions already made (from the accepted ADRs)

1. emcee is a new concrete Bayesian minimizer registered under
   `MinimizerTypeEnum.EMCEE = 'emcee'`. Selected via
   `project.analysis.minimizer.type = 'emcee'`.
2. emcee inherits two paired surfaces from `BayesianMinimizerBase`:
   - **Settings** (writable inputs): `sampling_steps`, `burn_in_steps`,
     `thinning_interval`, `population_size`, `parallel_workers`,
     `initialization_method`, `random_seed` — all declared by
     `BayesianMinimizerBase.__init__`. emcee may override class-level
     defaults (e.g. `sampling_steps=5000`, `population_size=32`) and
     adds one emcee-specific input `proposal_moves`.
   - **Outputs** (fit-filled, internal `_set_*`):
     `acceptance_rate_mean`, `gelman_rubin_max`,
     `effective_sample_size_min`, `best_log_posterior`,
     `point_estimate_name`, `sampler_completed`,
     `credible_interval_inner/outer` — already on `BayesianFitResult`,
     not on the minimizer. emcee's projection writer calls
     `self.fit_result._set_*` (not `self.minimizer._set_*`).
3. Verbose attribute names map to emcee native kwargs via
   `EmceeMinimizer._native_key_map` (overrides the DREAM-style defaults
   on `BayesianMinimizerBase._native_key_map`):

   | Verbose                 | emcee native engine attribute                                                  |
   | ----------------------- | ------------------------------------------------------------------------------ |
   | `sampling_steps`        | `nsteps`                                                                       |
   | `burn_in_steps`         | `nburn`                                                                        |
   | `thinning_interval`     | `thin`                                                                         |
   | `population_size`       | `nwalkers`                                                                     |
   | `parallel_workers`      | `parallel_workers` (engine integer; **not** mapped directly to emcee's `pool`) |
   | `initialization_method` | (custom — see §6)                                                              |
   | `random_seed`           | `random_seed`                                                                  |

   **`parallel_workers` semantics.** The category persists an integer;
   the engine class holds it under the same name. emcee's
   `EnsembleSampler` takes a `pool=` argument that is a pool object
   (anything with a `.map` method) or `None` for serial execution — not
   an integer. The engine builds the actual pool around `run_mcmc`:

   | `parallel_workers` value | Engine behaviour                       |
   | ------------------------ | -------------------------------------- |
   | `1`                      | `pool=None` (serial); single process   |
   | `0`                      | `multiprocessing.Pool(os.cpu_count())` |
   | `N > 1`                  | `multiprocessing.Pool(N)`              |

   The pool is closed in a `finally:` block after `run_mcmc` returns.
   `Analysis._sync_engine_from_minimizer_category` must therefore skip
   `parallel_workers` from the native-attribute sync (it already skips
   `random_seed` for the same "engine handles it" reason; add
   `parallel_workers` to the `_engine_sync_skip_keys` frozenset
   introduced in P1.5).

4. Resume uses emcee's `HDFBackend` against the `/emcee_chain` group of
   the same `analysis/results.h5` file used by the snapshot writer. No
   separate sidecar file. A non-resume `fit()` follows the prerequisite
   plan's lifecycle and **truncates** `results.h5` (after the standard
   warning); resume opens it in append mode.

   **`Project.save()` must not delete `/emcee_chain`.** The current
   `write_analysis_results_sidecar`
   ([`results_sidecar.py:282`](../../../src/easydiffraction/io/results_sidecar.py))
   opens `results.h5` with mode `'w'` (full truncate). Every save after
   a fit will erase the emcee chain unless this writer is modified.
   After this plan, the writer opens the file in append mode (`'a'`) and
   replaces only the EasyDiffraction-canonical groups (`/posterior`,
   `/distribution_cache`, `/pair_cache`, `/predictive`) by deleting them
   first if present, leaving any other top-level groups (currently only
   `/emcee_chain`) untouched.

   **Non-resume truncate must still happen — and explicitly.** The
   current `_warn_results_sidecar_overwrite`
   ([`analysis.py:943-953`](../../../src/easydiffraction/analysis/analysis.py))
   /
   [`warn_analysis_results_sidecar_overwrite`](../../../src/easydiffraction/io/results_sidecar.py)
   only **warns**; it does not delete. With the writer switched to
   append mode, a fresh non-resume emcee fit after an older emcee run
   would otherwise leave the stale `/emcee_chain` group in `results.h5`.
   This plan therefore adds a real preparation step that warns **and
   removes** the file before the engine starts. See P1.5a; the resume
   path bypasses it.

5. `Analysis.fit()` gains an optional `resume=True, extra_steps=N` call
   shape for minimizers that support incremental sampling. For other
   minimizers, passing `resume=True` raises immediately.
6. emcee outputs translate to the existing `BayesianFitResults` runtime
   shape (plural — note the singular `BayesianFitResult` is the
   persistence category, not the runtime object) exactly as DREAM does —
   same `PosteriorSamples`, `PosteriorParameterSummary`, etc. Plotting
   and display code needs no specialization.
7. Two `EmceeMinimizer` classes coexist with the same DREAM precedent:
   - `src/easydiffraction/analysis/categories/minimizer/emcee.py` — the
     persisted **category** class (`BayesianMinimizerBase` subclass)
     used for CIF persistence and the user-facing setter surface.
   - `src/easydiffraction/analysis/minimizers/emcee.py` — the live
     **engine** class registered with the engine `MinimizerFactory`.
     Holds the `emcee.EnsembleSampler` instance and runs the sampler.
     This mirrors the existing `BumpsDreamMinimizer` split between
     `categories/minimizer/bumps_dream.py` and
     `minimizers/bumps_dream.py`.

## Open questions

- **Resume after parameter-set change.** If the user fits, then edits
  which parameters are free, then calls `fit(resume=True, ...)`, emcee's
  `HDFBackend.shape` mismatches the current parameter count. Plan
  default: detect mismatch in P1.5 and raise `ValueError` with a clear
  "start a fresh run" message.
- **Resume after a non-emcee fit.** If the user runs DREAM, switches to
  emcee, and calls `fit(resume=True, ...)`, the `/emcee_chain` group
  will be missing. Plan default: raise `ValueError` pointing at the
  prerequisite ADR's lifecycle rule ("a new fit overwrites the file").
- **`InitializationMethodEnum` ↔ `DreamPopulationInitializationEnum`
  reconciliation** (deferred from review-8 F6 of the consolidation
  work). emcee uses different init methods (`ball`, `uniform`, `prior`);
  DREAM exposes a broader engine-level enum with `EPS`, `COV`, `LHS`,
  `RANDOM`. The persisted user-facing enum (`InitializationMethodEnum`)
  is narrower (`LATIN_HYPERCUBE`, `BALL`, `UNIFORM`, `PRIOR`). P1.3 must
  decide whether to narrow DREAM's engine enum to match, or accept the
  asymmetry. Recommend: keep DREAM's broader engine enum (legacy DREAM
  users may pass `EPS`/`COV`/`RANDOM` directly to the engine) but
  document that only `LATIN_HYPERCUBE` is persistable for DREAM; emcee
  accepts `BALL`/`UNIFORM`/`PRIOR` only.
- **Move-mix semantics.** emcee supports proposal-move mixtures (e.g. 70
  % stretch + 30 % differential evolution). The consolidation ADR §5
  exposes `proposal_moves` as a single string descriptor. Plan default:
  limit `proposal_moves` to single-move strings for v1 (`stretch`, `de`,
  `de_snooker`, `walk`). Mixtures deferred to a follow-on plan. Record
  this in the descriptor's `description=` text.

## Cleanup opportunities inherited from earlier work

The input/output-split work left four cleanup items still open in
[`docs/dev/issues/open.md`](../issues/open.md) that touch code this plan
modifies. Fold them in opportunistically while the surrounding code is
already being edited; the plan does not block on them.

- **#100 — Collapse duplicate predictive-cache-key helpers.**
  `Analysis._predictive_cache_key`
  ([analysis.py:528](../../../src/easydiffraction/analysis/analysis.py))
  and `Plotter._posterior_predictive_key`
  ([plotting.py:3823](../../../src/easydiffraction/display/plotting.py))
  build the identical string; keep one canonical helper. P1.6 may touch
  the predictive plotting path while validating emcee posterior
  emission.
- **#101 — Remove dead branch in `Analysis._fit_state_categories`.**
  Both branches return the same list since the Bayesian categories were
  absorbed. One-line fix at
  [analysis.py:1184-1205](../../../src/easydiffraction/analysis/analysis.py).
- **#102 — Drop compute-and-ignore `result_kind` validation.**
  `_restore_persisted_fit_state`
  ([serialize.py:590-606](../../../src/easydiffraction/io/cif/serialize.py))
  calls `FitResultKindEnum(result_kind_value)` for its side effect only.
  Move the warning into the descriptor setter, or extract a validator
  helper.
- **#103 — Make `_sync_engine_from_minimizer_category` skip-keys
  declarative.** This plan adds `proposal_moves` as a second
  engine-level "ambient" key (alongside `random_seed`). The current
  magic-string skip at
  [analysis.py:1138](../../../src/easydiffraction/analysis/analysis.py)
  should become a class-level
  `_engine_sync_skip_keys: ClassVar[frozenset[str]] = frozenset(...)` on
  `MinimizerCategoryBase` before the second member lands. Recommend
  addressing as part of P1.5.

When the matching open-issue is fully resolved, move it to
[`closed.md`](../issues/closed.md) and update
[`adrs/index.md`](../adrs/index.md) if relevant.

## Concrete files likely to change

### Created

- `src/easydiffraction/analysis/categories/minimizer/emcee.py` —
  persisted **category** class `EmceeMinimizer(BayesianMinimizerBase)`
  with class-level defaults, `_engine_metadata`, and the overridden
  `_native_key_map`.
- `src/easydiffraction/analysis/minimizers/emcee.py` — live **engine**
  class `EmceeMinimizer(BayesianMinimizerEngineBase or equivalent)`
  registered with `MinimizerFactory`. Holds `emcee.EnsembleSampler` and
  the `HDFBackend`.
- `tests/unit/easydiffraction/analysis/categories/minimizer/test_emcee.py`.
- `tests/unit/easydiffraction/analysis/minimizers/test_emcee.py`.
- `tests/integration/fitting/test_emcee.py` (cross-check vs DREAM on a
  shared toy fit; assert posterior medians agree to within tolerance).
- `docs/docs/tutorials/ed-25.py` (emcee + resume tutorial). The next
  free tutorial slot — `ed-23` is already the "Co2SiO4 Sequential Fit"
  tutorial and `ed-24` is the "LBCO Bayesian Display" tutorial. Verify
  `ed-25.py` is unused before creating it at P1.7 start; bump if a newer
  slot is already occupied.

### Modified

- `src/easydiffraction/analysis/minimizers/enums.py` — add
  `MinimizerTypeEnum.EMCEE = 'emcee'`.
- `src/easydiffraction/analysis/categories/minimizer/__init__.py` — add
  explicit `EmceeMinimizer` (category) import so registration fires.
- `src/easydiffraction/analysis/minimizers/__init__.py` (or the
  factory's package init) — add explicit `EmceeMinimizer` (engine)
  import so engine registration fires.
- `src/easydiffraction/analysis/categories/minimizer/bayesian_base.py` —
  only if review-8 F6 reconciliation (open question above) calls for
  narrowing the persisted enum surface; otherwise unchanged.
- `src/easydiffraction/analysis/analysis.py` — `fit()` signature gains
  `resume: bool = False, extra_steps: int | None = None`; validation +
  dispatch to engine. Wire `_engine_sync_skip_keys` (#103) before adding
  `proposal_moves` to the ambient set.
- `src/easydiffraction/io/results_sidecar.py` — read path: when
  `/emcee_chain` is present, expose a helper to construct an
  `emcee.backends.HDFBackend(path, name='emcee_chain', read_only=True)`
  for inspection/visualisation.
- `pyproject.toml`, `pixi.toml`, and `pixi.lock` — add `emcee>=3.1` as a
  direct runtime dependency and refresh the lockfile via `pixi lock` (CI
  installs from the lockfile, not from the manifest files alone).

### Deleted

- None.

## Implementation steps (Phase 1)

Mark `[x]` as each step lands.

- [ ] **P1.1 — Add emcee dependency and refresh the lockfile.**
  - Add `emcee>=3.1` to `pyproject.toml` (runtime dependencies, not just
    the `doc` extra — the existing lockfile carries emcee only as
    `extra == 'doc'` which CI does not install for runtime).
  - Add the same dependency to `pixi.toml` (runtime feature).
  - Run `pixi lock` to regenerate `pixi.lock` with `emcee` as a direct
    runtime dependency. The refreshed `pixi.lock` is the artifact CI
    consumes; `pixi install` is a local sanity check only.
  - Stage `pyproject.toml`, `pixi.toml`, and `pixi.lock` together.

  Files modified by this step: `pyproject.toml`, `pixi.toml`,
  `pixi.lock`. Commit: `Add emcee runtime dependency`

- [ ] **P1.2 — Register `MinimizerTypeEnum.EMCEE`.** Add the enum member
      with value `'emcee'` to
      `src/easydiffraction/analysis/minimizers/enums.py`. No other code
      wiring yet. Commit: `Register emcee minimizer enum value`

- [ ] **P1.3 — Add `EmceeMinimizer` category class.** New file
      `src/easydiffraction/analysis/categories/minimizer/emcee.py`.
      `EmceeMinimizer(BayesianMinimizerBase)` declares:
  - `type_info` with `tag=MinimizerTypeEnum.EMCEE` and a description.
  - `_engine_metadata: ClassVar[dict[str, str]] = {'optimizer_name': 'emcee', 'method_name': 'stretch'}`
    (matching the `BumpsDreamMinimizer` precedent for the
    `_restore_fit_results_from_projection` lookup).
  - `_native_key_map` override mapping the verbose names to emcee's
    native kwargs (see §"Decisions already made" point 3).
  - Class-level defaults for emcee-specific values:
    `sampling_steps=5000`, `burn_in_steps=1000`, `thinning_interval=5`,
    `population_size=32`, `parallel_workers=0`,
    `proposal_moves='stretch'`.
  - `__init__` constructs descriptors via the inherited helpers
    (`_sampling_steps_descriptor(default)`, etc. from
    `BayesianMinimizerBase`) and adds a new `proposal_moves` descriptor
    with a `MembershipValidator` over the single-move set (`stretch`,
    `de`, `de_snooker`, `walk`).
  - **Decide the `InitializationMethodEnum` reconciliation** (open
    question above) before wiring.
    `EmceeMinimizer._supported_initialization_methods` should list
    `(BALL, UNIFORM, PRIOR)` regardless of the DREAM decision.

  Update `src/easydiffraction/analysis/categories/minimizer/__init__.py`
  to import `EmceeMinimizer` (registration trigger via
  `@MinimizerCategoryFactory.register`).

  The paired `BayesianFitResult` flows automatically because
  `BayesianMinimizerBase._fit_result_class = BayesianFitResult`; no
  wiring needed in this step.

  Commit: `Add EmceeMinimizer category class`

- [ ] **P1.4 — Add `EmceeMinimizer` engine class.** New file
      `src/easydiffraction/analysis/minimizers/emcee.py`. The engine
      class is registered with `MinimizerFactory` and holds the
      `emcee.EnsembleSampler` plus an `HDFBackend` attribute. Mirror the
      shape of
      [`bumps_dream.py BumpsDreamMinimizer`](../../../src/easydiffraction/analysis/minimizers/bumps_dream.py)
      — descriptor attributes (`burn`, `thin`, `pop`, `init`, …) that
      `Analysis._sync_engine_from_minimizer_category` writes to from the
      category's `_native_kwargs()`. The descriptor names on the engine
      must match the keys returned by `EmceeMinimizer._native_kwargs()`,
      which are: `nsteps`, `nburn`, `thin`, `nwalkers`,
      `parallel_workers`, `random_seed`, plus `initialization_method`
      and `proposal_moves` handled by custom hooks (see §3 for the
      mapping table and the `parallel_workers` semantics — the engine
      attribute is an integer; the actual emcee `pool` object is built
      and torn down inside `EmceeMinimizer.fit`, not by the native-key
      sync).

      **Engine-facing contract.** `EmceeMinimizer.fit` matches the
      existing
      [`MinimizerBase.fit`](../../../src/easydiffraction/analysis/minimizers/base.py)
      contract — `Fitter.fit` (the layer that owns `structures`,
      `experiments`, `weights`, and `analysis`) calls every engine
      uniformly. The engine receives only `parameters` and the
      already-built `objective_function`:

      ```python
      MinimizerBase.fit(
          parameters: list[Parameter],
          objective_function: Callable[[dict[str, object]], np.ndarray],
          verbosity: VerbosityEnum = VerbosityEnum.FULL,
          *,
          finalize_tracking: bool = True,
          use_physical_limits: bool = False,
          random_seed: int | None = None,
          resume: bool = False,           # added by P1.5
          extra_steps: int | None = None, # added by P1.5
      ) -> FitResults
      ```

      The base implementation raises `NotImplementedError` only when
      `resume=True` (see P1.5). `EmceeMinimizer.fit` overrides with
      the same signature and honours `resume` / `extra_steps`.

      **Sidecar path.** emcee's `HDFBackend` needs a file path, but
      the engine signature deliberately does not carry one. The
      engine reads it from a private attribute
      `self._sidecar_path: Path | None` that `Fitter.fit` sets on
      the engine before calling `engine.fit(...)`, derived from
      `analysis.project.info.path / 'analysis' / 'results.h5'`.
      Engines that do not need it ignore the attribute; the
      attribute defaults to `None` and `EmceeMinimizer.fit` raises
      `RuntimeError` if it is `None` when needed.

      **Residual-to-log-probability adapter.** emcee expects a
      scalar log probability from a flat walker coordinate
      (`np.ndarray` shape `(ndim,)`), but the `objective_function`
      `Fitter.fit` passes us returns a residual array from an
      `engine_params` dict. The engine class builds an adapter
      `log_prob(theta)` that:

      1. Maps `theta` (the walker vector) onto an `engine_params`
         dict using a fixed ordered list of free-parameter unique
         names captured **once** at sampler construction (from the
         `parameters` argument to `fit`).
      2. Rejects values outside
         `[parameter.fit_min, parameter.fit_max]` by returning
         `-np.inf` immediately — does not call the calculator for
         invalid proposals.
      3. Calls the **passed-in** `objective_function(engine_params)`
         (do **not** call `Fitter._build_objective_function` from
         the engine — that is a `Fitter` helper, not engine API).
      4. Returns Gaussian log likelihood
         `-0.5 * np.sum(r**2)`. The current fit weights are already
         folded into the residuals by the objective function; this
         step does **not** re-weight.
      5. Returns `-np.inf` on calculator exceptions (rare; emcee
         re-proposes).
      6. Treats the prior as flat over the box-bounded parameter
         volume — no informative priors in v1; deferred to a
         follow-on plan.

      The adapter must **not** mutate live `Parameter.value` state
      on `-np.inf` returns. Implement by passing an
      `engine_params` dict to `objective_function` (the existing
      objective writes the values into live parameters internally;
      that mutation only happens once `objective_function` is
      invoked, so the bounds check above must guard every call).

      Engine method shape (sketch):

      ```python
      class EmceeMinimizer(MinimizerBase):
          name = MinimizerTypeEnum.EMCEE
          method = 'stretch'

          # Set by Fitter.fit before this fit() call:
          _sidecar_path: Path | None = None

          def fit(
              self,
              parameters: list[Parameter],
              objective_function: Callable[..., object],
              verbosity: VerbosityEnum = VerbosityEnum.FULL,
              *,
              finalize_tracking: bool = True,
              use_physical_limits: bool = False,
              random_seed: int | None = None,
              resume: bool = False,
              extra_steps: int | None = None,
          ) -> FitResults:
              if self._sidecar_path is None:
                  msg = ('emcee engine requires Fitter.fit to set '
                         '_sidecar_path; was Analysis configured?')
                  raise RuntimeError(msg)

              free_param_names = [p.unique_name for p in parameters]
              param_by_name = {p.unique_name: p for p in parameters}

              def log_prob(theta):
                  for name, value in zip(free_param_names, theta):
                      p = param_by_name[name]
                      if not (p.fit_min <= value <= p.fit_max):
                          return -np.inf
                  engine_params = dict(zip(free_param_names, theta))
                  try:
                      r = objective_function(engine_params)
                  except Exception:
                      return -np.inf
                  return -0.5 * float(np.sum(np.asarray(r) ** 2))

              backend = emcee.backends.HDFBackend(
                  self._sidecar_path, name='emcee_chain',
                  read_only=False,
              )
              pool = self._build_pool(self.parallel_workers)
              try:
                  sampler = emcee.EnsembleSampler(
                      nwalkers=self.nwalkers,
                      ndim=len(free_param_names),
                      log_prob_fn=log_prob,
                      pool=pool,
                      moves=self._resolve_moves(self.proposal_moves),
                      backend=backend,
                  )
                  if resume:
                      self._validate_resume(backend, free_param_names)
                      sampler.run_mcmc(
                          None, nsteps=extra_steps,
                          skip_initial_state_check=True,
                          progress=True,
                      )
                  else:
                      initial_state = self._initial_state(
                          parameters, self.nwalkers,
                          self.init, random_seed,
                      )
                      sampler.run_mcmc(
                          initial_state, nsteps=self.nsteps,
                          progress=True,
                      )
              finally:
                  if pool is not None:
                      pool.close()
                      pool.join()
              return self._build_results(sampler, parameters)
      ```

      Register with the engine `MinimizerFactory` and update
      `src/easydiffraction/analysis/minimizers/__init__.py` (or the
      relevant package init) to import the engine class.

      Commit: `Add EmceeMinimizer engine class`

- [ ] **P1.5 — Wire `fit(resume=True, extra_steps=N)` end-to-end.** The
      current fit stack does not accept `resume` / `extra_steps`
      anywhere. Every signature and call site listed below must be
      updated in this step. Each item is one short edit; the step lands
      as a single commit because the signatures must change in lockstep.

  **`Fitter` stays the layer that owns `structures`, `experiments`,
  `weights`, parameter collection, and objective construction.** Engines
  receive only `parameters` and `objective_function` (already-built) via
  the existing `MinimizerBase.fit` shape. This plan adds `resume` and
  `extra_steps` to the same shape.

  **Signatures (add
  `resume: bool = False, extra_steps: int | None = None`):**
  - `Analysis.fit`
    ([analysis.py:929](../../../src/easydiffraction/analysis/analysis.py)).
    User-facing entry point.
  - `Analysis._run_single`, `Analysis._run_joint`,
    `Analysis._prepare_fit_run`, `Analysis._fit_single`,
    `Analysis._fit_joint` (every internal helper that takes the fit
    through to `Fitter.fit`).
  - `Fitter.fit`
    ([fitting.py:140-150](../../../src/easydiffraction/analysis/fitting.py))
    — adds the keyword pair to its existing signature (`structures`,
    `experiments`, `weights`, `analysis`, `verbosity`,
    `use_physical_limits`, `random_seed`, **+ `resume`,
    `extra_steps`**). Forwards the pair to `self.minimizer.fit(...)`.
  - `MinimizerBase.fit`
    ([base.py:351-360](../../../src/easydiffraction/analysis/minimizers/base.py))
    — adds the keyword pair to its existing engine-facing shape
    (`parameters`, `objective_function`, `verbosity`, _keyword_:
    `finalize_tracking`, `use_physical_limits`, `random_seed`, **+
    `resume`, `extra_steps`**). The base implementation handles
    non-resume calls unchanged and raises
    `NotImplementedError(f"Minimizer '{self.name}' does not support resume.")`
    when `resume=True`. `EmceeMinimizer.fit` overrides with the same
    signature and honours both args.

  **Sidecar-path plumbing.** `Fitter.fit` resolves the sidecar path from
  `analysis.project.info.path` (when both are non-None) and sets
  `self.minimizer._sidecar_path` on the engine before calling
  `self.minimizer.fit(...)`. Engines that do not need it ignore the
  attribute; `EmceeMinimizer.fit` reads it (and raises `RuntimeError` if
  `None` as defence in depth — but normal users never hit that path
  because of the upfront save-required guard in the next bullet).

  **Behaviour rules:**
  - **Single mode only for v1.** `Analysis._run_joint` raises
    `ValueError('Resume is supported in single fit mode only')` when
    `resume=True`. Joint-mode resume is deferred; recorded explicitly in
    §"Open questions".
  - **Validate the active minimizer.** `Analysis.fit` raises
    `ValueError` when `resume=True` and
    `self.minimizer.type != MinimizerTypeEnum.EMCEE.value`. Match the
    clear-error pattern used elsewhere.
  - **Require a saved project for emcee.** Unlike DREAM (which keeps the
    chain in memory), emcee's `HDFBackend` is the sampler's live chain
    store — it needs a real file path. `Analysis.fit` raises
    `ValueError` when
    `self.minimizer.type == MinimizerTypeEnum.EMCEE.value` and
    `self.project.info.path is None`, with a clear scientist-facing
    message that points at the fix:
    `"emcee requires a saved project; call project.save_as(<path>) before analysis.fit()."`
    The check fires for both the initial run and `resume=True`. The
    engine's `_sidecar_path is None` `RuntimeError` (per P1.4) remains
    as defence-in-depth for direct engine calls outside the `Analysis`
    flow but is not reachable from the user-facing path.
  - **Validate `extra_steps`.** Require positive integer when
    `resume=True`. Raise on `None`, `0`, or negative.
  - **Bypass reset.** Skip the new
    `prepare_analysis_results_sidecar_for_new_fit` helper (see P1.5a)
    and `_clear_persisted_fit_state` when `resume=True` — both would
    clobber the chain and the persisted fit state.
  - **Defence in depth.** `MinimizerBase.fit`'s `NotImplementedError` on
    `resume=True` only matters if an engine is called directly outside
    the `Analysis` flow — the `Analysis.fit` guard above fires first in
    normal use.

  **Open issue #103 cleanup.** Introduce
  `_engine_sync_skip_keys: ClassVar[frozenset[str]] = frozenset({'random_seed', 'parallel_workers'})`
  on `MinimizerCategoryBase`, and update
  `_sync_engine_from_minimizer_category`
  ([analysis.py:1134-1146](../../../src/easydiffraction/analysis/analysis.py))
  to use it. `EmceeMinimizer` (category) overrides the frozenset to add
  `'proposal_moves'` if the engine consumes that key differently from
  the category attribute (sketch in P1.4).

  Commit: `Wire emcee resume through fit stack`

- [ ] **P1.5a — Make `results.h5` append-on-save and add an explicit
      truncate-on-new-fit prep step.** Two coordinated changes that land
      in a single commit because they jointly preserve the ADR lifecycle
      (resume keeps `/emcee_chain`; new fit removes it).

  In
  [`src/easydiffraction/io/results_sidecar.py`](../../../src/easydiffraction/io/results_sidecar.py):
  - Replace `h5py.File(sidecar_path, 'w')` (line 282) with
    `h5py.File(sidecar_path, 'a')`. Before writing each
    EasyDiffraction-canonical group (`/posterior`,
    `/distribution_cache`, `/pair_cache`, `/predictive`), delete that
    group first if present so the writer's behaviour for those groups is
    unchanged.
  - Do **not** touch any other top-level group from the writer.
    `/emcee_chain` survives every save.
  - **Add a new helper**
    `prepare_analysis_results_sidecar_for_new_fit(*, analysis_dir: Path) -> None`
    that takes the same `analysis_dir` shape as
    `warn_analysis_results_sidecar_overwrite`, **warns** when the file
    exists (matching the current warning text), and then **removes** the
    file entirely so a fresh fit starts from a clean slate. The old
    `warn_analysis_results_sidecar_overwrite` becomes a thin wrapper
    that delegates to the new helper, or is replaced outright by the new
    helper at every call site.

  In
  [`src/easydiffraction/analysis/analysis.py`](../../../src/easydiffraction/analysis/analysis.py):
  - Replace `_warn_results_sidecar_overwrite` (lines 943-953) with a
    call to the new `prepare_analysis_results_sidecar_for_new_fit`
    helper. Same call sites in `_run_single` and `_run_joint`.
  - **Bypass on resume.** The `resume=True` branch in
    `Analysis._prepare_fit_run` (added by P1.5) must **not** call this
    helper — that is the whole point of resume keeping the chain alive.
    The bypass rule listed in P1.5 "Behaviour rules → Bypass reset"
    therefore now also covers the
    `prepare_analysis_results_sidecar_for_new_fit` call.

  Add focused unit tests in Phase 2 (P2.1) covering:
  - **Append preserves `/emcee_chain`.** Write a sidecar payload, create
    a stub `/emcee_chain` group on the same file, re-write the sidecar —
    the `/emcee_chain` group must survive.
  - **New-fit prep removes the file.** Create a sidecar with a stub
    `/emcee_chain` group; call
    `prepare_analysis_results_sidecar_for_new_fit`; assert the file is
    gone (or empty) and the stale group is unreachable.
  - **Resume bypass.** Set up an `Analysis` with a saved project, invoke
    the resume code path (mocked engine), and assert
    `prepare_analysis_results_sidecar_for_new_fit` was **not** called.

  Commit: `Append-on-save plus explicit truncate-on-new-fit prep`

- [ ] **P1.6 — Route emcee outputs into the existing fit_result and
      sidecar pipeline.** Verify the existing
      `_store_posterior_fit_projection`
      ([analysis.py](../../../src/easydiffraction/analysis/analysis.py))
      writes to `self.fit_result._set_*` (the `BayesianFitResult`
      instance auto-paired with the `EmceeMinimizer`) and that the
      `/posterior`, `/distribution_cache`, `/pair_cache`, `/predictive`
      groups in `results.h5` receive emcee output without modification.
      Adjust only where emcee surfaces data differently from DREAM (e.g.
      `EnsembleSampler.get_chain(flat=False,     discard=burn, thin=thin)`
      vs the DREAM extraction helper). Cache derivations (KDE, pair
      grids) reuse the existing pipeline.

      Opportunistic cleanup: address open issue #100 if the
      predictive plotting path is being touched anyway. Collapse
      `Analysis._predictive_cache_key` and
      `Plotter._posterior_predictive_key` into one canonical helper.

      Commit: `Route emcee posterior through fit_result and sidecar`

- [ ] **P1.7 — Add `ed-25.py` tutorial.** Verify first that
      `docs/docs/tutorials/ed-25.py` is unused. `ed-23.py` is the
      "Co2SiO4 Sequential Fit" tutorial and `ed-24.py` is the "LBCO
      Bayesian Display" tutorial — do **not** overwrite either. If
      `ed-25.py` already exists by the time this step runs, pick the
      next free integer slot and adjust the file name + references below
      to match.

      New notebook source at `docs/docs/tutorials/ed-25.py`
      covering:

  - `project.analysis.minimizer.type = 'emcee'` (post-switchable
    syntax).
  - `project.analysis.minimizer.sampling_steps = 1000` (small for
    tutorial speed).
  - `project.analysis.fit()` and a posterior plot.
  - `project.save()`.
  - `project.analysis.fit(resume=True, extra_steps=500)` continues the
    chain.
  - Final posterior plot after resume.

  Update the docs navigation in the same step:
  - Add an entry under "MCMC / Bayesian" (or the appropriate section) in
    [`docs/docs/tutorials/index.md`](../../docs/tutorials/index.md)
    pointing at `ed-25.ipynb`.
  - Add a navigation entry under the matching section in
    [`docs/mkdocs.yml`](../../../docs/mkdocs.yml).

  Run `pixi run notebook-prepare` to regenerate the `.ipynb`.

  Verification greps:

  ```
  test -f docs/docs/tutorials/ed-25.py
  git grep -nE '\banalysis\.minimizer_type\b|\bminimizer\.runtime_seconds\b|\bminimizer\.gelman_rubin_max\b' docs/docs/tutorials/ed-25.py
  git grep -n 'ed-25' docs/docs/tutorials/index.md docs/mkdocs.yml
  ```

  The first must be true; the second must be empty; the third must
  return at least one hit in each file.

  Commit: `Add ed-25 emcee tutorial`

- [ ] **P1.8 — Phase 1 review gate.** No code change. Stop and request
      user review. After approval, proceed to Phase 2.

## Verification (Phase 2)

Each command captures its log with a zsh-safe exit-code variable as
required by `AGENTS.md` → **Workflow**.

- [ ] **P2.1 — Add unit + integration tests.**
  - `tests/unit/easydiffraction/analysis/categories/minimizer/test_emcee.py`:
    category-class descriptor defaults; `_native_key_map` override;
    pairing with `BayesianFitResult`; swap behavior; resume
    parameter-set-mismatch error path (no real sampler).
  - `tests/unit/easydiffraction/analysis/minimizers/test_emcee.py`:
    engine-class registration, descriptor defaults, native kwargs
    plumbing.
  - `tests/unit/easydiffraction/analysis/test_analysis.py` (or matching
    coverage file): assert `Analysis.fit()` raises `ValueError` with a
    save-prompt message when emcee is the active minimizer and
    `project.info.path is None`, for both initial fits and
    `resume=True`.
  - `tests/unit/easydiffraction/io/test_results_sidecar.py`: the
    save-after-resume invariant from P1.5a — write a sidecar payload,
    then write a stub `/emcee_chain` group on the same file, then
    re-write the sidecar; the `/emcee_chain` group must survive.
  - `tests/integration/fitting/test_emcee.py`: end-to-end fit on a small
    synthetic problem; resume; assert posterior medians agree with a
    DREAM run within tolerance.

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

EasyDiffraction adds emcee — a widely-used affine-invariant MCMC sampler
— as a second Bayesian fitter. It is selected exactly like the existing
samplers, via the uniform switchable-category surface:

```python
project.analysis.minimizer.type = 'emcee'
project.analysis.minimizer.sampling_steps = 5000
project.analysis.fit()
```

Long runs can be **resumed** without starting over:

```python
project.analysis.fit(resume=True, extra_steps=2000)
```

emcee's chain state lives inside the same `analysis/results.h5` file as
the other posterior data, so saving and reopening a project is a
single-file affair. Plots, parameter posteriors, and tables work the
same as for DREAM, so switching between samplers to cross-check results
is straightforward.

A new tutorial (`ed-25`) walks through a short run, saving the project,
and resuming for additional steps.
