# Plan: Minimizer Category Consolidation

> This plan follows
> [`.github/copilot-instructions.md`](../../../.github/copilot-instructions.md).
> No deliberate exceptions.

## ADR

Implements
[`docs/dev/adrs/suggestions/minimizer-category-consolidation.md`](../adrs/suggestions/minimizer-category-consolidation.md).
This plan promotes that ADR from Suggestion → Accepted during
implementation (step P1.14).

Affected ADRs that this plan amends or supersedes:

- [`accepted/analysis-cif-fit-state.md`](../adrs/accepted/analysis-cif-fit-state.md)
  — Bayesian projection rewritten.
- [`accepted/fit-mode-categories.md`](../adrs/accepted/fit-mode-categories.md)
  — selectors move from `analysis.fitting` to `analysis` directly.
- [`accepted/selector-families.md`](../adrs/accepted/selector-families.md)
  — reclassify `minimizer_type`.
- [`accepted/runtime-fit-results.md`](../adrs/accepted/runtime-fit-results.md)
  — point at the new ADR.
- [`accepted/switchable-category-api.md`](../adrs/accepted/switchable-category-api.md)
  — append `minimizer` to examples.
- [`suggestions/parameter-posterior-summary.md`](../adrs/suggestions/parameter-posterior-summary.md)
  — absorbed; close with pointer.

## Branch and PR

- Branch: `feature/minimizer-category-consolidation`. Do not push unless
  asked.
- Each step in §"Implementation steps (Phase 1)" must be staged with
  explicit paths and committed locally **before** moving to the next
  step. See `.github/copilot-instructions.md` → **Commits**.
- After P1.15, stop and wait for the user review gate before starting
  Phase 2.

## Decisions already made (from the ADR)

1. Single unified `minimizer` switchable category on `Analysis`. Concrete
   classes per backend with verbose descriptor names declared in the
   class body. No mixins.
2. Selectors `minimizer_type` and `fitting_mode_type` live on `Analysis`
   directly. The Python `fitting` category and all 7 `bayesian_*`
   categories are deleted.
3. Heavy posterior arrays live in `analysis/results.h5`, namespaced
   into top-level groups (`/posterior/`, `/distribution_cache/`,
   `/pair_cache/`, `/predictive/`); emcee adds `/emcee_chain/` later.
   A new fit **overwrites** the whole file (preceded by a warning when
   a populated sidecar already exists). Resume is the only exception,
   handled by Plan 2.
4. `Parameter.posterior` (default `None`) replaces
   `_bayesian_parameter_posterior`. Per-row posterior summary columns
   are appended to `_fit_parameter`.
5. CIF `?` and missing values resolve to the descriptor's static
   default at load time. No callable defaults anywhere.
6. Warn-and-reset on `minimizer_type` swap, matching the
   `background_type` precedent.

## Open questions

- **Tutorial-fixture regeneration.** Saved projects under
  `tmp/tutorials/projects/` are produced by the tutorials themselves
  during `pixi run script-tests`. The plan assumes regeneration falls
  out naturally; if a checked-in CIF fixture exists elsewhere with the
  old layout, capture it during P1.7 and regenerate alongside.
- **Initialization-method enum coverage for DREAM.** DREAM currently
  exposes `init = 'lhs'` only. The plan introduces the unified enum
  with `latin_hypercube` mapped to `lhs`; other enum members raise
  `ValueError` on `DreamMinimizer` until Plan 2 wires emcee.

## Concrete files likely to change

Created:

- `src/easydiffraction/analysis/categories/minimizer/__init__.py`
- `src/easydiffraction/analysis/categories/minimizer/base.py`
- `src/easydiffraction/analysis/categories/minimizer/bumps_lm.py`
- `src/easydiffraction/analysis/categories/minimizer/bumps_least_squares.py`
- `src/easydiffraction/analysis/categories/minimizer/lmfit_least_squares.py`
- `src/easydiffraction/analysis/categories/minimizer/dream.py`
- `src/easydiffraction/analysis/categories/minimizer/factory.py`
- New `InitializationMethodEnum` (location: extend
  `src/easydiffraction/analysis/minimizers/enums.py` or add a new module
  — decide during P1.2; record choice in the step description).
- `docs/dev/adrs/accepted/minimizer-category-consolidation.md` (moved
  from `suggestions/`).

Deleted:

- `src/easydiffraction/analysis/categories/fitting/` (whole package).
- `src/easydiffraction/analysis/categories/bayesian_sampler/` (whole
  package).
- `src/easydiffraction/analysis/categories/bayesian_result/`.
- `src/easydiffraction/analysis/categories/bayesian_convergence/`.
- `src/easydiffraction/analysis/categories/bayesian_parameter_posteriors/`.
- `src/easydiffraction/analysis/categories/bayesian_distribution_caches/`.
- `src/easydiffraction/analysis/categories/bayesian_pair_caches/`.
- `src/easydiffraction/analysis/categories/bayesian_predictive_datasets/`.

Modified:

- `src/easydiffraction/analysis/analysis.py` (replace `self._fitting` +
  `self._fitter` wiring; new `minimizer_type` selector;
  `show_minimizer_types()`; migrate `_sync_live_minimizer_from_persisted_fit_state`).
- `src/easydiffraction/analysis/__init__.py` (drop deleted-category
  exports; add new minimizer exports).
- `src/easydiffraction/analysis/categories/__init__.py` (same).
- `src/easydiffraction/io/cif/serialize.py` (emit/read `_minimizer.*`;
  drop the 7 `_bayesian_*` dispatch calls; update legacy-tag fallback
  message; map `_fitting.minimizer_type` and `_fitting.mode_type` to
  the relocated selectors).
- `src/easydiffraction/io/results_sidecar.py` (append-mode open;
  namespaced groups; source content from runtime fit_results instead
  of from removed manifest categories).
- `src/easydiffraction/display/plotting.py` (consumers of
  `analysis.bayesian_*` redirected to `Parameter.posterior` + sidecar
  groups).
- `src/easydiffraction/project/display.py` (same).
- `src/easydiffraction/core/variable.py` (add `posterior` to
  `GenericParameter` with private setter).
- `src/easydiffraction/summary/summary.py` (path migration).
- `src/easydiffraction/analysis/sequential.py` (path migration).
- `src/easydiffraction/__main__.py` (path migration if needed).
- All tutorials referencing `analysis.fitting.minimizer*`: `ed-2.py`,
  `ed-3.py`, `ed-4.py`, `ed-15.py`, `ed-17.py`, `ed-21.py`, `ed-22.py`.
- Existing tests calling `analysis.fitting.minimizer*` (see grep
  output: ~15 files under `tests/`).
- The 5 ADR files listed in §"ADR" above + `docs/dev/adrs/index.md`.

Add (Phase 2):

- `tests/unit/easydiffraction/analysis/categories/minimizer/` (one
  `test_<module>.py` per new module, mirroring the source tree per
  `docs/dev/adrs/accepted/test-strategy.md`).

## Implementation steps (Phase 1)

Mark `[x]` as each step lands.

- [ ] **P1.1 — Add `Parameter.posterior` attribute.**
  In `src/easydiffraction/core/variable.py`, extend `GenericParameter`
  with a read-only `posterior` property (default `None`) and a private
  `_set_posterior(value)` setter accepting `PosteriorParameterSummary
  | None`. Tests deferred to Phase 2.
  Commit: `Add Parameter.posterior attribute`

- [ ] **P1.2 — Add `InitializationMethodEnum`.**
  Add an `(str, Enum)` with members `latin_hypercube`, `ball`,
  `uniform`, `prior`. Place it next to existing minimizer enums
  (`src/easydiffraction/analysis/minimizers/enums.py`).
  Commit: `Add InitializationMethodEnum for samplers`

- [ ] **P1.3 — Add `MinimizerCategoryBase`.**
  New module
  `src/easydiffraction/analysis/categories/minimizer/base.py`
  defining `MinimizerCategoryBase(CategoryItem)` with
  `_category_code = 'minimizer'` and a shared `_native_kwargs()`
  helper that maps verbose-attribute → native-backend-key for each
  concrete subclass via a class-level `_native_key_map: dict[str, str]`.
  Empty `__init__.py` + the base. No factory yet.
  Commit: `Add MinimizerCategoryBase`

- [ ] **P1.4 — Add concrete minimizer category classes.**
  Add `bumps_lm.py`, `bumps_least_squares.py`,
  `lmfit_least_squares.py`, `dream.py` with class-body descriptors
  carrying static defaults per the ADR §5 / §8 tables. Add
  `factory.py` (`MinimizerCategoryFactory(FactoryBase)`) registering
  each concrete class against its `MinimizerTypeEnum` tag. Update
  `categories/minimizer/__init__.py` to import every concrete class
  (per copilot-instructions: "explicitly import every concrete class
  to trigger registration"). Plain Python only — no wiring to
  `Analysis` yet.
  Commit: `Add concrete minimizer category classes`

- [ ] **P1.5 — Resolve CIF `?` and missing values to descriptor
      defaults.**
  In the central descriptor → CIF read path (locate via
  `CifHandler.read_from_block` / equivalent), treat `?` and missing
  tags as "use `AttributeSpec.default` if present; otherwise emit a
  clear `log.error()` on the original required-field path". Behavior
  unchanged for non-default-bearing descriptors. Save path always
  emits the current value.
  Commit: `Resolve CIF '?' to descriptor default on load`

- [ ] **P1.6 — Wire `Analysis.minimizer_type` and `Analysis.minimizer`.**
  In `src/easydiffraction/analysis/analysis.py`:
  - Replace `self._fitting = Fitting(...)` with
    `self._minimizer = MinimizerCategoryFactory.create('lmfit (leastsq)')`.
  - Add `minimizer` (read-only), `minimizer_type` (getter+setter),
    `show_minimizer_types()`.
  - On `minimizer_type` swap, instantiate new class, compute
    differing-default fields, `log.warn(...)` per the
    `background_type` precedent, replace `self._minimizer`.
  - Move `self._fitter = Fitter(...)` plumbing from `Fitting` to a
    private `Analysis._engine` derived from `self._minimizer`.
  - Move `_sync_live_minimizer_from_persisted_fit_state` to a no-op
    or remove (no `bayesian_sampler` persisted snapshot exists once
    P1.10 lands; the new category is itself the persisted state).
  - Migrate internal references to `self.fitting.minimizer_type` →
    `self.minimizer_type` (4 sites in analysis.py per grep).
  - `Analysis.fitting` Python attribute is removed at the same time.
  Commit: `Wire minimizer selector on Analysis owner`

- [ ] **P1.7 — Update CIF serialize/deserialize for `_minimizer.*`.**
  In `src/easydiffraction/io/cif/serialize.py`:
  - Emit `_minimizer.*` tags from `analysis.minimizer` (replaces the
    `_bayesian_sampler.*` emit path).
  - Read `_fitting.minimizer_type` first; instantiate the matching
    concrete `minimizer`; populate its descriptors from `_minimizer.*`
    tags using the §P1.5 `?`→default rule.
  - Delete the 7 `_bayesian_*` dispatch calls
    (`analysis.bayesian_result.from_cif(block)`, …; lines 624–630).
  - Update the legacy-tag warning message (line 682) accordingly.
  - Update fit-state-detection scalar tags (lines 593–602) to use
    `_minimizer.*` indicators.
  Commit: `Serialize minimizer category to _minimizer.* CIF tags`

- [ ] **P1.8 — Extend `_fit_parameter` with posterior columns.**
  Add the 8 posterior columns from ADR §3 to the existing
  `_fit_parameter` CIF writer/reader. On load, hydrate
  `Parameter.posterior` (a `PosteriorParameterSummary` instance) from
  the row when at least one posterior column is non-empty; leave
  `posterior = None` otherwise. Drop the obsolete
  `_bayesian_parameter_posterior` reader.
  Commit: `Persist parameter posterior via _fit_parameter columns`

- [ ] **P1.9 — Migrate path consumers off `analysis.fitting.*`.**
  Update remaining live-Python references (already covered for
  `analysis.py` in P1.6) in:
  - `src/easydiffraction/summary/summary.py` (line 222).
  - `src/easydiffraction/analysis/sequential.py` (line 650).
  - `src/easydiffraction/__main__.py` (verify line 59 — `fitting_mode_type`
    on `analysis` is already the public location; check no extra
    references slipped in).
  Commit: `Use Analysis.minimizer_type in non-analysis modules`

- [ ] **P1.10 — Rewrite `results_sidecar.py` for overwrite-on-new-fit.**
  - Keep the file basename `results.h5`; resolve it relative to the
    project `analysis/` directory. Drop the
    `_DEFAULT_SIDECAR_FILE_NAME` indirection via CIF.
  - The post-fit snapshot writer (`write_analysis_results_sidecar`)
    opens the file with `h5py.File(path, 'w')` — i.e. **truncate** —
    and writes the four namespaced groups it produces (`/posterior/`,
    `/distribution_cache/`, `/pair_cache/`, `/predictive/`).
  - Before truncating, if the target file exists and is non-empty,
    emit a single `log.warn(...)` line naming the path and stating
    that previous fit results will be overwritten. The warning is
    suppressed when called from the resume path (see Plan 2 P1.4).
  - Drop all references to removed Bayesian categories. Source
    posterior chains / KDE / pair / predictive content from the
    runtime `BayesianFitResults` object directly.
  - On read, populate the runtime in-memory results object from the
    sidecar groups by name. No CIF manifest categories involved.
  - Trigger the truncate-and-warn from `Analysis.fit()` (not from
    `minimizer_type` setter) so swapping the minimizer without
    re-fitting leaves `results.h5` intact and inspectable until the
    user actually starts a new fit.
  Commit: `Overwrite results.h5 on new fit with user warning`

- [ ] **P1.11 — Migrate plotting and display consumers.**
  - `src/easydiffraction/display/plotting.py` line 2662
    (`analysis.bayesian_pair_caches` loop) and any other Bayesian-
    category readers: replace with reads of sidecar groups
    (`/pair_cache/<id>`) loaded into runtime caches, or recompute
    from `BayesianFitResults.posterior_samples` when the sidecar
    cache is absent.
  - `src/easydiffraction/project/display.py` lines 153, 154, 170,
    186: replace with sidecar-availability checks and runtime
    posterior-presence checks.
  Commit: `Read posterior plots from results.h5 groups`

- [ ] **P1.12 — Delete obsolete category packages.**
  Remove the 8 directories listed in §"Concrete files likely to
  change" → "Deleted". Update
  `src/easydiffraction/analysis/__init__.py` and
  `src/easydiffraction/analysis/categories/__init__.py` to drop the
  ~20 deleted-category exports. Verify there are no remaining
  references: `git grep -nE 'bayesian_(sampler|result|convergence|parameter_posteriors|distribution_caches|pair_caches|predictive_datasets)'`
  must return empty under `src/` and `tests/`.
  Commit: `Remove obsolete Bayesian and fitting categories`

- [ ] **P1.13 — Update tutorials and regenerate notebooks.**
  Update Python source files (the `*.ipynb` are generated artifacts —
  do not edit those directly per copilot-instructions):
  - `docs/docs/tutorials/ed-2.py`, `ed-3.py`, `ed-4.py`, `ed-15.py`,
    `ed-17.py`, `ed-21.py`, `ed-22.py`.
  - Replace `analysis.fitting.minimizer_type = '…'` →
    `analysis.minimizer_type = '…'`.
  - Replace `analysis.fitting.minimizer.steps = N` →
    `analysis.minimizer.sampling_steps = N` (and the rest of the
    rename table from ADR §5).
  Run `pixi run notebook-prepare`.
  Commit: `Update tutorials for analysis.minimizer API`

- [ ] **P1.14 — Promote ADR + amend affected ADRs.**
  - Move
    `docs/dev/adrs/suggestions/minimizer-category-consolidation.md`
    → `docs/dev/adrs/accepted/minimizer-category-consolidation.md`
    using `git mv` (file operation in the run-in-terminal tool, NOT
    edited via the file edit tool). Flip Status to `Accepted`.
  - Edit
    [`docs/dev/adrs/accepted/analysis-cif-fit-state.md`](../adrs/accepted/analysis-cif-fit-state.md):
    replace the "Bayesian fit projection" and "Bayesian sidecar"
    sections; remove the 7 `_bayesian_*` category list; add
    `_minimizer.*` + extended `_fit_parameter` description; drop the
    `_bayesian_result.sidecar_file` description.
  - Edit
    [`docs/dev/adrs/accepted/fit-mode-categories.md`](../adrs/accepted/fit-mode-categories.md):
    update §1 and §2 to reflect that selectors live on `Analysis`
    directly; remove the `fitting` Python category sentences.
  - Edit
    [`docs/dev/adrs/accepted/selector-families.md`](../adrs/accepted/selector-families.md):
    move `minimizer_type` from Backend → Switchable-category
    selector row; example becomes `analysis.minimizer_type`.
  - Edit
    [`docs/dev/adrs/accepted/runtime-fit-results.md`](../adrs/accepted/runtime-fit-results.md):
    closing paragraph references the new ADR alongside the existing
    fit-state ADR.
  - Edit
    [`docs/dev/adrs/accepted/switchable-category-api.md`](../adrs/accepted/switchable-category-api.md):
    append `minimizer` to the bullet list of switchable examples.
  - Edit
    [`docs/dev/adrs/suggestions/parameter-posterior-summary.md`](../adrs/suggestions/parameter-posterior-summary.md):
    add a top "Status: Superseded by [minimizer-category-consolidation]"
    block; keep historical context intact.
  - Edit [`docs/dev/adrs/index.md`](../adrs/index.md): move the row
    for the new ADR from Suggestion → Accepted; remove the
    parameter-posterior-summary row (closed) or change its status to
    Superseded.
  - Add a closed-issues entry in
    [`docs/dev/issues/closed.md`](../issues/closed.md) if there was
    an open-issues entry for the consolidation work (check
    `docs/dev/issues/open.md` first).
  Commit: `Promote minimizer-category-consolidation ADR`

- [ ] **P1.15 — Phase 1 review gate.**
  No code change in this step. Stop and request user review. After
  approval, proceed to Phase 2.

## Verification (Phase 2)

Each command captures its log with a zsh-safe exit-code variable as
required by `.github/copilot-instructions.md` → **Workflow**.

- [ ] **P2.1 — Add unit tests mirroring source tree.**
  Create one `test_<module>.py` per file under
  `src/easydiffraction/analysis/categories/minimizer/`. Cover:
  default-value resolution, swap warnings, native-key mapping, CIF
  round-trip via `_minimizer.*` with `?` fallback. Add a
  `test_variable_posterior.py` unit for `Parameter.posterior`.
  Verify layout with:
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
  Iterate `pixi run check` until clean. Do not raise lint thresholds —
  refactor instead (`.github/copilot-instructions.md` → **Code Style**).

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
  This regenerates `tmp/tutorials/projects/*` fixtures with the new
  CIF layout.

## Suggested Pull Request

**Title:** Consolidate minimizer settings into one switchable category

**Description (user-facing):**

EasyDiffraction now exposes every fitter — least-squares solvers and
the Bayesian DREAM sampler alike — through a single, consistent API:

- `project.analysis.minimizer_type = 'bumps (dream)'` selects the
  backend.
- `project.analysis.minimizer.sampling_steps = 3000` (and the other
  named settings) configures it.
- Per-parameter Bayesian posteriors are now attached to the parameter
  itself (`param.posterior`) instead of living in a separate analysis
  table — same idea as `param.uncertainty` for deterministic fits.
- Saved projects produce a single `analysis/results.h5` file containing
  the heavy posterior arrays, with the small CIF file kept compact and
  human-readable.
- A clear warning prints whenever switching minimizer types changes a
  default setting, so users always see what changed.

This is a reorganization for clarity; no fitting capability is removed,
and the next release adds a second Bayesian sampler (emcee) on the
same surface.
