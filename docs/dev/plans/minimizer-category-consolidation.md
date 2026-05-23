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

## Decisions added after Review 2

- **All nine `MinimizerTypeEnum` tags get a dedicated concrete class.**
  P1.4 declares one class per tag: `lmfit`, `lmfit (leastsq)`,
  `lmfit (least_squares)`, `dfols`, `bumps`, `bumps (lm)`,
  `bumps (dream)`, `bumps (amoeba)`, `bumps (de)`. The bare `lmfit`
  and `bumps` tags stay as separate classes (each tag is its own CIF
  surface, matching the PR claim "no fitting capability is removed").
  Folding them into `lmfit (leastsq)` / `bumps (lm)` aliases is out
  of scope for this plan; raise a separate suggestion ADR if wanted
  later.
- **Intermediates are behavior-only.** Per ADR §8 "no mixins",
  `LeastSquaresMinimizerBase` and `BayesianMinimizerBase` carry
  helper methods and expected-descriptor-name class constants only;
  no descriptor instances. Every concrete class repeats its own
  descriptor declarations with class-specific defaults.

## Decisions added after Review 4

- **The engine module `src/easydiffraction/analysis/fitting.py` is
  kept.** It exposes the `Fitter` class that wraps the underlying
  minimizer engines and runs the solver loop. This ADR removes the
  Python `analysis.fitting` *category surface* (the intermediate
  `Fitting` category that exposed `minimizer_type` and `minimizer`
  one level deep on `Analysis`), not the engine module. Stale-
  reference greps therefore target the category surface only:
  `self.fitting`, `analysis.fitting.<member>`, `categories.fitting`,
  `categories/fitting/`. Engine imports of the form
  `from easydiffraction.analysis.fitting import Fitter` are kept and
  are not flagged. P1.6 keeps the existing
  `self._fitter = Fitter(...)` plumbing internally but reroutes it
  through `self._minimizer` instead of `self._fitting.minimizer_type`.
- **`tests/unit/easydiffraction/analysis/test_fitting.py` is kept.**
  It exercises the engine (`Fitter`) and not the deleted category.
  P2.1a only updates the assertions that touched the removed
  `analysis.fitting.<member>` surface.

## Concrete files likely to change

Created:

- `src/easydiffraction/analysis/categories/minimizer/__init__.py`
- `src/easydiffraction/analysis/categories/minimizer/base.py`
  (`MinimizerCategoryBase`)
- `src/easydiffraction/analysis/categories/minimizer/lsq_base.py`
  (`LeastSquaresMinimizerBase` — behavior-only: shared
  `_native_kwargs()` / `_run_solver()` plumbing, expected LSQ
  descriptor _names_ declared as class constants for the factory to
  introspect. No descriptor instances on the base — per ADR §8 "no
  mixins", every concrete class declares its own descriptors with
  class-specific defaults.)
- `src/easydiffraction/analysis/categories/minimizer/bayesian_base.py`
  (`BayesianMinimizerBase` — same convention: behavior-only helpers
  for sampler lifecycle, expected Bayesian descriptor _names_ as
  class constants, no inherited descriptor instances.)
- One concrete class per `MinimizerTypeEnum` tag:
  - `lmfit.py` (tag `lmfit`)
  - `lmfit_leastsq.py` (tag `lmfit (leastsq)`)
  - `lmfit_least_squares.py` (tag `lmfit (least_squares)`)
  - `dfols.py` (tag `dfols`)
  - `bumps.py` (tag `bumps`)
  - `bumps_lm.py` (tag `bumps (lm)`)
  - `bumps_dream.py` (tag `bumps (dream)`)
  - `bumps_amoeba.py` (tag `bumps (amoeba)`)
  - `bumps_de.py` (tag `bumps (de)`)
- `src/easydiffraction/analysis/categories/minimizer/factory.py`
- `src/easydiffraction/core/posterior.py` (relocated
  `PosteriorParameterSummary` value object — see P1.1a).
- New `InitializationMethodEnum` in
  `src/easydiffraction/analysis/minimizers/enums.py` (next to
  `MinimizerTypeEnum`).
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
- `src/easydiffraction/analysis/categories/deterministic_result/`
  (per ADR §1 — fields absorbed into the concrete LSQ minimizer
  classes; see P1.10a).

Modified:

- `src/easydiffraction/analysis/analysis.py` (replace `self._fitting` +
  `self._fitter` wiring; new `minimizer_type` selector;
  `show_supported_minimizer_types()` + `show_current_minimizer_type()`;
  rename `show_fitting_mode_types()` →
  `show_supported_fitting_mode_types()` and add
  `show_current_fitting_mode_type()`; migrate
  `_sync_live_minimizer_from_persisted_fit_state`).
- `src/easydiffraction/analysis/__init__.py` (drop deleted-category
  exports; add new minimizer exports).
- `src/easydiffraction/analysis/categories/__init__.py` (same).
- `src/easydiffraction/io/cif/serialize.py` (emit/read `_minimizer.*`;
  drop the 7 `_bayesian_*` dispatch calls; update legacy-tag fallback
  message; map `_fitting.minimizer_type` and `_fitting.mode_type` to
  the relocated selectors).
- `src/easydiffraction/io/results_sidecar.py` (truncate-on-new-fit
  open + namespaced groups; source content from runtime fit_results
  instead of from removed manifest categories; resume-append is owned
  by Plan 2).
- `src/easydiffraction/display/plotting.py` (consumers of
  `analysis.bayesian_*` redirected to `Parameter.posterior` + sidecar
  groups).
- `src/easydiffraction/project/display.py` (same).
- `src/easydiffraction/core/variable.py` (add `posterior` to
  `GenericParameter` with private setter; imports the
  `PosteriorParameterSummary` type from
  `src/easydiffraction/core/posterior.py` so no analysis-layer import
  is added to `core/`).
- `src/easydiffraction/summary/summary.py` (path migration).
- `src/easydiffraction/analysis/sequential.py` (path migration).
- `src/easydiffraction/__main__.py` (path migration if needed).
- All tutorials referencing `analysis.fitting.*`,
  `show_minimizer_types`, or `show_fitting_mode_types`: `ed-2.py`,
  `ed-3.py`, `ed-4.py`, `ed-8.py`, `ed-15.py`, `ed-17.py`,
  `ed-20.py`, `ed-21.py`, `ed-22.py` (full list and the per-file
  rename rules live in P1.13).
- Existing tests calling `analysis.fitting.minimizer*` (see grep
  output: ~15 files under `tests/`).
- The 5 ADR files listed in §"ADR" above + `docs/dev/adrs/index.md`.

Add (Phase 2):

- `tests/unit/easydiffraction/analysis/categories/minimizer/` (one
  `test_<module>.py` per new module, mirroring the source tree per
  `docs/dev/adrs/accepted/test-strategy.md`).

## Implementation steps (Phase 1)

Mark `[x]` as each step lands.

- [ ] **P1.1a — Relocate `PosteriorParameterSummary` to `core/`.**
      Create `src/easydiffraction/core/posterior.py` and move the
      `PosteriorParameterSummary` dataclass from
      `src/easydiffraction/analysis/fit_helpers/bayesian.py` (lines 34–69
      per current grep). The class contains only primitives — no analysis
      logic — and is therefore compatible with
      [`.github/copilot-instructions.md`](../../../.github/copilot-instructions.md)
      → **Architecture** ("Keep `core/` free of domain logic").
      Files to update in this step:
  - `src/easydiffraction/analysis/fit_helpers/bayesian.py` —
    remove the local dataclass definition (current lines 34–69) and
    add `from easydiffraction.core.posterior import
PosteriorParameterSummary` so the existing intra-module
    references (type aliases at line 190, function signatures, the
    constructor call near line 473, …) keep resolving.
  - `src/easydiffraction/analysis/fit_helpers/__init__.py` (line 5) —
    re-export the symbol from `core.posterior` so the old import
    path `analysis.fit_helpers.PosteriorParameterSummary` keeps
    working through the rest of this PR.
  - `src/easydiffraction/analysis/analysis.py` (line 48) — switch the
    import to `easydiffraction.core.posterior` directly.

  Verify with two greps (use-sites such as type aliases,
  annotations, and constructor calls are allowed in any module that
  also imports the symbol):

  ```
  git grep -n '^class PosteriorParameterSummary' src/
  ```

  must list exactly one file —
  `src/easydiffraction/core/posterior.py`. No other module may
  define the class.

  ```
  git grep -l 'PosteriorParameterSummary' src/ \
    | grep -v 'core/posterior\.py$' \
    | xargs -r grep -L 'from easydiffraction.core.posterior import PosteriorParameterSummary'
  ```

  must return empty — i.e. every file under `src/` that mentions
  the name (other than the definition file) also imports it from
  `easydiffraction.core.posterior`.

  Tests deferred to Phase 2.
  Commit: `Move PosteriorParameterSummary to core`

- [ ] **P1.1 — Add `Parameter.posterior` attribute.**
      In `src/easydiffraction/core/variable.py`, extend `GenericParameter`
      with a read-only `posterior` property (default `None`) and a private
      `_set_posterior(value)` setter accepting
      `PosteriorParameterSummary | None` imported from
      `easydiffraction.core.posterior` (relocated in P1.1a — keeps
      `core/variable.py` free of analysis imports). Tests deferred to
      Phase 2.
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
      Add nine modules under
      `src/easydiffraction/analysis/categories/minimizer/`, one per
      current `MinimizerTypeEnum` tag, plus two **behavior-only**
      intermediates (`LeastSquaresMinimizerBase`,
      `BayesianMinimizerBase`). Per ADR §8 "no mixins", the
      intermediates contain only shared helpers (`_native_kwargs()`,
      `_run_solver()`, expected-descriptor-name class constants for
      factory/coverage introspection) — **no descriptor instances**.
      Every concrete class declares every one of its descriptors in its
      own class body with backend-specific defaults per ADR §5 / §8 (no
      `__init__` mutation of parent declarations). Two descriptors with
      the same verbose name across two LSQ classes are intentional
      duplication, not an abstraction smell.

  | Concrete class               | `MinimizerTypeEnum` tag | Family   |
  | ---------------------------- | ----------------------- | -------- |
  | `LmfitMinimizer`             | `lmfit`                 | LSQ      |
  | `LmfitLeastsqMinimizer`      | `lmfit (leastsq)`       | LSQ      |
  | `LmfitLeastSquaresMinimizer` | `lmfit (least_squares)` | LSQ      |
  | `DfolsMinimizer`             | `dfols`                 | LSQ      |
  | `BumpsMinimizer`             | `bumps`                 | LSQ      |
  | `BumpsLmMinimizer`           | `bumps (lm)`            | LSQ      |
  | `BumpsAmoebaMinimizer`       | `bumps (amoeba)`        | LSQ      |
  | `BumpsDeMinimizer`           | `bumps (de)`            | LSQ      |
  | `BumpsDreamMinimizer`        | `bumps (dream)`         | Bayesian |

  Add `factory.py` (`MinimizerCategoryFactory(FactoryBase)`)
  registering each concrete class against its `MinimizerTypeEnum`
  member. Update `categories/minimizer/__init__.py` to explicitly
  import every concrete class (per copilot-instructions:
  "explicitly import every concrete class to trigger registration").
  Plain Python only — no wiring to `Analysis` yet.

  Coverage check at the end of the step:
  `git grep -nE "MinimizerTypeEnum\.[A-Z_]+" src/easydiffraction/analysis/categories/minimizer/`
  must list every enum member at least once.

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
    plus the canonical switchable-category `show_*` methods required
    by [`.github/copilot-instructions.md`](../../../.github/copilot-instructions.md)
    → **Architecture**:
    - `show_supported_minimizer_types()` — delegates to
      `MinimizerCategoryFactory.show_supported(...)`.
    - `show_current_minimizer_type()` — prints the active tag.
  - Rename the existing fitting-mode show method to match the same
    convention while we are touching this file:
    - `show_fitting_mode_types()` → `show_supported_fitting_mode_types()`.
    - Add `show_current_fitting_mode_type()`.
      The error message in
      `analysis.py:1045` and the call sites in tests/tutorials follow
      in P1.9 / P1.13 / P2.1a.
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

- [ ] **P1.10a — Absorb `_deterministic_result.*` into LSQ classes.**
      Per ADR §1, the `deterministic_result` category disappears. Its
      fields move into the concrete LSQ minimizer classes added in P1.4.
      Per the behavior-only-bases decision recorded in
      §"Decisions added after Review 2", the descriptors are **declared
      in each concrete LSQ class body** — not on
      `LeastSquaresMinimizerBase`. The base only gains the expected-name
      constants the factory uses to assert coverage.
  - In each of the eight LSQ concrete classes (`LmfitMinimizer`,
    `LmfitLeastsqMinimizer`, `LmfitLeastSquaresMinimizer`,
    `DfolsMinimizer`, `BumpsMinimizer`, `BumpsLmMinimizer`,
    `BumpsAmoebaMinimizer`, `BumpsDeMinimizer`), declare:
    `optimizer_name`, `method_name`, `objective_name`,
    `objective_value`, `n_data_points`, `n_parameters`,
    `n_free_parameters`, `degrees_of_freedom`, `covariance_available`,
    `correlation_available` with the same defaults the current
    `DeterministicResult` uses, plus the runtime outputs
    (`runtime_seconds`, `iterations_performed`, `exit_reason`,
    `negative_log_likelihood`). CIF tag prefix becomes `_minimizer.*`
    (was `_deterministic_result.*`).
  - Append every new descriptor name to
    `LeastSquaresMinimizerBase._expected_descriptor_names` so the
    P1.4 coverage check still catches accidental drift.
  - Update `src/easydiffraction/io/cif/serialize.py` to stop calling
    `analysis.deterministic_result.from_cif(block)` and to read these
    fields from the active `analysis.minimizer` instance instead.
  - Drop the call site in
    `src/easydiffraction/analysis/analysis.py` that wires
    `self._deterministic_result`.
  - Drop `from easydiffraction.analysis.categories.deterministic_result …`
    imports across `src/` (verify with
    `git grep -n deterministic_result src/`).
    Commit: `Absorb deterministic_result fields into LSQ minimizers`

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
      Remove the 9 directories listed in §"Concrete files likely to
      change" → "Deleted" (`fitting/`, the seven `bayesian_*/`
      packages, and `deterministic_result/`). Update
      `src/easydiffraction/analysis/__init__.py` and
      `src/easydiffraction/analysis/categories/__init__.py` to drop the
      ~20 deleted-category exports.

  Verify there are no remaining references to the **removed
  categories and CIF tags** under `src/` only at this step — the
  ADR removes the `bayesian_*` _categories_, not Bayesian fitting
  concept or its helper functions (e.g.
  `_format_bayesian_overall_status` in
  `src/easydiffraction/analysis/fit_helpers/bayesian.py` is fine and
  stays). The targeted patterns:

  ```
  git grep -nE 'analysis\.bayesian_|categories\.bayesian_|categories/bayesian_|_bayesian_(sampler|result|convergence|parameter_posterior|distribution_cache|pair_cache|predictive_dataset)' src/
  git grep -nE 'analysis\.deterministic_result|categories\.deterministic_result|categories/deterministic_result|_deterministic_result\.' src/
  git grep -nP '\bself\.fitting\b|\bproject\.analysis\.fitting\b|\banalysis\.fitting\.(minimizer|show_minimizer_types|minimizer_type)\b|categories\.fitting\b|categories/fitting/' src/
  ```

  All three must return empty. Notes:
  - The third grep uses `git grep -nP` (PCRE), not `-nE`: `\b`
    word-boundaries are not part of POSIX ERE, and `git grep -nE
    '\b…'` silently returns empty in this repo's environment. The
    same `-nP` switch is used everywhere else `\b` appears below
    (P1.12 internal-owner grep, P1.13 tutorial grep, P2.1a test
    grep).
  - The CIF tags `_fitting.minimizer_type` and `_fitting.mode_type`
    are kept by this ADR (see ADR §2), so no `_fitting\.` grep.
  - The engine module `src/easydiffraction/analysis/fitting.py`
    (`Fitter` class) is **kept** — see
    §"Decisions added after Review 4". Imports of the form
    `from easydiffraction.analysis.fitting import Fitter` are fine
    and are not flagged by the targeted patterns above.

  In addition, scan `src/easydiffraction/analysis/analysis.py` for
  any stale internal owner attributes that map to deleted categories:

  ```
  git grep -nP '\bself\.fitting\b|\bself\._fitting\b|\bself\.bayesian_(sampler|result|convergence|parameter_posteriors|distribution_caches|pair_caches|predictive_datasets)\b|\bself\._bayesian_(sampler|result|convergence|parameter_posteriors|distribution_caches|pair_caches|predictive_datasets)\b|\bself\.deterministic_result\b|\bself\._deterministic_result\b' src/easydiffraction/analysis/analysis.py
  ```

  must return empty. This guards against the case where the
  category property is removed at the public surface but stale
  `self.<removed>` accesses survive in the same module.

  Tutorials and tests are migrated later (P1.13 and P2.1a), so they
  are not checked here.

  Commit: `Remove obsolete Bayesian and fitting categories`

- [ ] **P1.13 — Update tutorials and regenerate notebooks.**
      Update Python source files (the `*.ipynb` are generated artifacts —
      do not edit those directly per copilot-instructions). Tutorial list
      is the union of every file currently referencing
      `analysis.fitting.*`, `show_minimizer_types`, or
      `show_fitting_mode_types` (per `git grep` at plan time):
  - `docs/docs/tutorials/ed-2.py`, `ed-3.py`, `ed-4.py`, `ed-8.py`,
    `ed-15.py`, `ed-17.py`, `ed-20.py`, `ed-21.py`, `ed-22.py`.
  - Replace `analysis.fitting.minimizer_type = '…'` →
    `analysis.minimizer_type = '…'`.
  - Replace `analysis.fitting.show_minimizer_types()` →
    `analysis.show_supported_minimizer_types()`.
  - Replace `analysis.show_fitting_mode_types()` →
    `analysis.show_supported_fitting_mode_types()`.
  - Replace `analysis.fitting.minimizer.steps = N` →
    `analysis.minimizer.sampling_steps = N` (and the rest of the
    rename table from ADR §5).

  After edits, run `pixi run notebook-prepare`. Then re-run the
  P1.12 targeted greps against `docs/docs/tutorials/` plus the two
  show-method renames:

  ```
  git grep -nE 'analysis\.bayesian_|categories\.bayesian_|_bayesian_(sampler|result|convergence|parameter_posterior|distribution_cache|pair_cache|predictive_dataset)' docs/docs/tutorials/
  git grep -nE 'analysis\.deterministic_result|_deterministic_result\.' docs/docs/tutorials/
  git grep -nP '\banalysis\.fitting\.(minimizer|show_minimizer_types|minimizer_type)\b|\bproject\.analysis\.fitting\b' docs/docs/tutorials/
  git grep -nE 'show_minimizer_types|show_fitting_mode_types' docs/docs/tutorials/
  ```

  All four must return empty. (The tutorials never import the engine
  module directly, so the narrowed `analysis.fitting` pattern is
  sufficient.)

  Commit: `Update tutorials for analysis.minimizer API`

- [ ] **P1.14 — Promote ADR + amend affected ADRs.**
  - Move
    `docs/dev/adrs/suggestions/minimizer-category-consolidation.md`
    → `docs/dev/adrs/accepted/minimizer-category-consolidation.md`
    using `git mv` (file operation in the run-in-terminal tool, NOT
    edited via the file edit tool). Flip Status to `Accepted`. While
    editing, update the §2 examples to use
    `show_supported_minimizer_types()` /
    `show_current_minimizer_type()` (and the matching fitting-mode
    pair) so the ADR matches the
    [`.github/copilot-instructions.md`](../../../.github/copilot-instructions.md)
    convention.
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
      No code change in this step. Re-run the three targeted greps from
      P1.12, this time against the **Phase 1 scopes only** (`src/` and
      `docs/docs/tutorials/`) — all must return empty. The `tests/`
      sweep is intentionally deferred to P2.1a, which is the step that
      migrates the tests. Then stop and request user review. After
      approval, proceed to Phase 2.

## Verification (Phase 2)

Each command captures its log with a zsh-safe exit-code variable as
required by `.github/copilot-instructions.md` → **Workflow**.

- [ ] **P2.1a — Migrate existing tests off removed API.**
      Each bullet below is a separate commit, staged with explicit paths
      per `.github/copilot-instructions.md` → **Commits**. The set is
      sized so each commit lands one atomic test migration.

  Delete (obsolete after P1.12):
  - `tests/unit/easydiffraction/analysis/categories/fitting/` (whole
    directory: `test_default.py`, `test_factory.py`).
  - `tests/unit/easydiffraction/analysis/categories/test_bayesian_sampler.py`,
    `test_bayesian_result.py`, `test_bayesian_convergence.py`,
    `test_bayesian_parameter_posteriors.py`,
    `test_bayesian_distribution_caches.py`,
    `test_bayesian_pair_caches.py`,
    `test_bayesian_predictive_datasets.py`.
  - `tests/unit/easydiffraction/analysis/categories/test_deterministic_result.py`.

  Keep — these test the engine, not the deleted category:
  - `tests/unit/easydiffraction/analysis/test_fitting.py` exercises
    `easydiffraction.analysis.fitting.Fitter` (the engine module
    retained per §"Decisions added after Review 4"). Update any
    assertions that reach into `analysis.fitting.<category>` surface,
    but keep the module and its engine tests intact.

  Rewrite call sites (one commit per file or per small cluster):
  - `tests/unit/easydiffraction/analysis/test_analysis.py` &
    `test_analysis_coverage.py` — change
    `a.fitting.show_minimizer_types()` →
    `a.show_supported_minimizer_types()`; change
    `a.fitting.minimizer_type` → `a.minimizer_type`; assert against
    `show_supported_fitting_mode_types()` / `show_current_*` strings.
  - `tests/unit/easydiffraction/analysis/categories/test_fit_state.py`
    — update references to the removed Bayesian categories.
  - `tests/unit/easydiffraction/io/test_results_sidecar.py` — assert
    the truncate-on-new-fit lifecycle and the four namespaced groups.
  - `tests/unit/easydiffraction/project/test_display.py`,
    `test_project_load.py` — drop assertions against the removed
    Bayesian categories; replace with sidecar-availability checks.
  - `tests/functional/test_switchable_categories.py` — add the
    `minimizer` switchable to the parametrized matrix; assert
    `show_supported_minimizer_types()` /
    `show_current_minimizer_type()` exist.
  - `tests/integration/fitting/test_analysis_and_fit_category_support.py`,
    `test_analysis_display.py`, `test_project_load.py`,
    `test_powder-diffraction_constant-wavelength.py`,
    `test_powder-diffraction_time-of-flight.py`,
    `test_powder-diffraction_joint-fit.py`, `test_multi.py`,
    `test_sequential.py`, `conftest.py` — `analysis.fitting.*` →
    `analysis.*`; show-method renames.
  - `tests/integration/fitting/test_bayesian_dream.py` — port
    expectations from the seven Bayesian categories to
    `analysis.minimizer` + sidecar groups.

  After all rewrites, re-run the layout check:

  ```
  pixi run test-structure-check > /tmp/easydiffraction-test-structure-check.log 2>&1; \
    test_structure_check_exit_code=$?; \
    tail -n 200 /tmp/easydiffraction-test-structure-check.log; \
    exit $test_structure_check_exit_code
  ```

  And confirm no stale references remain — using the same targeted
  patterns from P1.12 (so legitimate Bayesian helpers such as
  `_format_bayesian_overall_status` are not flagged):

  ```
  git grep -nE 'analysis\.bayesian_|categories\.bayesian_|_bayesian_(sampler|result|convergence|parameter_posterior|distribution_cache|pair_cache|predictive_dataset)' tests/
  git grep -nE 'analysis\.deterministic_result|_deterministic_result\.' tests/
  git grep -nP '\banalysis\.fitting\.(minimizer|show_minimizer_types|minimizer_type)\b|\bproject\.analysis\.fitting\b|\bself\.fitting\b' tests/
  git grep -nE 'show_minimizer_types|show_fitting_mode_types' tests/
  ```

  All four must return empty. The narrowed `analysis.fitting` pattern
  preserves engine imports
  (`from easydiffraction.analysis.fitting import Fitter`) used in
  `tests/unit/easydiffraction/analysis/test_fitting.py` and friends.

- [ ] **P2.1 — Add unit tests mirroring source tree.**
      Create one `test_<module>.py` per file under
      `src/easydiffraction/analysis/categories/minimizer/`. Cover:
      default-value resolution, swap warnings, native-key mapping, CIF
      round-trip via `_minimizer.*` with `?` fallback. Add a
      `test_variable_posterior.py` unit for `Parameter.posterior` and a
      `test_posterior.py` unit for the relocated
      `PosteriorParameterSummary` (covers P1.1a).
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
