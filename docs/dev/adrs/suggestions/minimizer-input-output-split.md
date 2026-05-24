# ADR: Minimizer Input/Output Split

**Status:** Proposed **Date:** 2026-05-24

## Status Note

This proposal revisits and supersedes Alternative D in
[`minimizer-category-consolidation.md`](../accepted/minimizer-category-consolidation.md)
("Strict input-only `minimizer` plus a separate `fit_result`"), which
was rejected during the consolidation work on the assumption that the
input/output mix on `analysis.minimizer` was symmetric with the
input/output mix on `Parameter`. Implementation experience shows that
analogy does not hold and the mix has produced measurable UX and
duplication problems documented below.

## Context

After
[`minimizer-category-consolidation.md`](../accepted/minimizer-category-consolidation.md)
landed, `analysis.minimizer` holds both writable user inputs and
fit-filled outputs in a single namespace. A user typing
`analysis.minimizer.help()` before any fit sees roughly twenty
properties, the majority of which are `None`, `0`, or empty strings,
with no signal which they may write and which the fit fills in.

The current shape on the live category surfaces:

- **Writable inputs:** `max_iterations` (LSQ); `sampling_steps`,
  `burn_in_steps`, `thinning_interval`, `population_size`,
  `parallel_workers`, `initialization_method`, `random_seed`,
  `credible_interval_inner`, `credible_interval_outer` (Bayesian).
- **Fit-filled outputs (no public setter, only `_set_*` internals):**
  `objective_name`, `objective_value`, `n_data_points`, `n_parameters`,
  `n_free_parameters`, `degrees_of_freedom`, `covariance_available`,
  `correlation_available`, `runtime_seconds`, `iterations_performed`,
  `exit_reason` (LSQ); `runtime_seconds`, `point_estimate_name`,
  `sampler_completed`, `acceptance_rate_mean`, `gelman_rubin_max`,
  `effective_sample_size_min`, `best_log_posterior` (Bayesian).

Three of the output fields already overlap with `analysis.fit_result`:

| Concept | Field on `analysis.minimizer` | Field on `analysis.fit_result` |
| ------- | ----------------------------- | ------------------------------ |
| Wall time | `runtime_seconds` | `fitting_time` |
| Iteration count | `iterations_performed` (LSQ) | `iterations` |
| χ² | `objective_value` | `reduced_chi_square` |

So a reader who wants "how long did the fit take" must already pick
between two places. The current layout has both **input/output mixed
inside `minimizer`** and **output duplication between `minimizer` and
`fit_result`**.

The consolidation ADR's two-line argument for keeping inputs and outputs
together was:

1. **Symmetry with `Parameter`.** A `Parameter` holds both its
   user-set initial value and its refined value plus uncertainty.
2. **One-place discoverability** > strict purity.

The symmetry argument does not actually transfer.
`Parameter.value` and `Parameter.uncertainty` describe the *same scalar
quantity* before and after refinement; they share a name, semantics,
and lifecycle. `minimizer.sampling_steps` (a user request) and
`minimizer.gelman_rubin_max` (a diagnostic the sampler reports) are
about completely different things and only share a namespace because
the consolidation ADR put them there. "One-place" is also already
broken: scalar fit outputs are split across `minimizer`, `fit_result`,
`fit_parameters`, and `fit_parameter_correlations` today.

## Decision

### 1. Split `analysis.minimizer` into inputs and outputs

`analysis.minimizer` keeps only **writable user settings**. The
fit-filled output fields move to `analysis.fit_result`, which gets a
class hierarchy parallel to `minimizer` so each minimizer family can
declare its own output schema.

After this ADR:

| Category | Role | Writable |
| -------- | ---- | -------- |
| `analysis.minimizer` | user-supplied settings | yes |
| `analysis.fit_result` | scalar fit outputs | no (internal `_set_*` only) |
| `analysis.fit_parameters` | per-parameter snapshots and posterior summary rows | no |
| `analysis.fit_parameter_correlations` | upper-triangle correlation rows | no |

**`fit_result` is not a user-facing switchable category.** It is an
internal projection paired with the active `minimizer`. It does not
expose `fit_result.type` or `fit_result.show_supported()`; the only way
the user changes the active `fit_result` class is by setting
`analysis.minimizer.type`, which the owner's `_swap_minimizer` hook
uses to instantiate both `self._minimizer` and `self._fit_result`
atomically. This is an explicit, documented exception to the global
selector contract from
[`switchable-category-owned-selectors.md`](../accepted/switchable-category-owned-selectors.md)
§1 because there is no user choice involved at the `fit_result` level
— the minimizer family fully determines the result schema. See the
new exception text added to that ADR (listed under §"ADRs amended").

**Family mapping is one-to-one between minimizer family and result
class.** Every minimizer registered under
`MinimizerTypeEnum` maps to exactly one `FitResult` concrete class
according to its family:

| `MinimizerTypeEnum` member | Minimizer family | Paired `FitResult` class |
| -------------------------- | ---------------- | ------------------------ |
| `LMFIT` | LSQ | `LeastSquaresFitResult` |
| `LMFIT_LEASTSQ` | LSQ | `LeastSquaresFitResult` |
| `LMFIT_LEAST_SQUARES` | LSQ | `LeastSquaresFitResult` |
| `DFOLS` | LSQ | `LeastSquaresFitResult` |
| `BUMPS` | LSQ | `LeastSquaresFitResult` |
| `BUMPS_LM` | LSQ | `LeastSquaresFitResult` |
| `BUMPS_AMOEBA` | LSQ | `LeastSquaresFitResult` |
| `BUMPS_DE` | LSQ | `LeastSquaresFitResult` |
| `BUMPS_DREAM` | Bayesian | `BayesianFitResult` |
| `EMCEE` *(when added)* | Bayesian | `BayesianFitResult` |

The pairing rule is encoded once on the minimizer base classes
(`LeastSquaresMinimizerBase._fit_result_class = LeastSquaresFitResult`,
`BayesianMinimizerBase._fit_result_class = BayesianFitResult`) so
`_swap_minimizer` reads the paired class off the new minimizer instance
and does not need a per-tag dispatch.

This preserves the consolidation ADR's "no `_bayesian_*` mirror"
guarantee — there is exactly one output category, not seven — while
making the input/output boundary unambiguous.

### 2. Field assignments

**`analysis.minimizer` after the split** (writable settings only):

- LSQ: `max_iterations`.
- Bayesian: `sampling_steps`, `burn_in_steps`, `thinning_interval`,
  `population_size`, `parallel_workers`, `initialization_method`,
  `random_seed`, `credible_interval_inner`, `credible_interval_outer`.

`credible_interval_inner` and `credible_interval_outer` are
**promoted from output-only to writable input** by this ADR. Today
they have only an internal `_set_*` and are written from
`_store_posterior_fit_projection`, which makes them effectively
hard-coded to `0.68` / `0.95`. After the split, the user sets them
before `analysis.fit()`; the Bayesian posterior-summary path reads
the two values when generating the per-parameter interval columns
(`posterior_interval_68_low/high`, `posterior_interval_95_low/high`).
The column names stay numeric (`68`, `95`) for backwards compatibility
with deterministic-fit rows that have empty values there; mismatching
user-supplied levels (e.g. `credible_interval_inner = 0.5`) are
warned about at fit time so the column names do not silently lie.

A separate suggestion ADR can later generalise the interval column
naming (e.g. `posterior_interval_low_<level>`); that is deferred work
and not in scope here.

**`analysis.fit_result` after the split** (outputs only). Common fields
live on `FitResultBase`; family-specific fields on the concrete classes:

- `FitResultBase`: `success`, `message`, `iterations`, `fitting_time`,
  `reduced_chi_square`, `result_kind`.
- `LeastSquaresFitResult` adds: `objective_name`, `objective_value`,
  `n_data_points`, `n_parameters`, `n_free_parameters`,
  `degrees_of_freedom`, `covariance_available`, `correlation_available`,
  `exit_reason`.
- `BayesianFitResult` adds: `point_estimate_name`, `sampler_completed`,
  `acceptance_rate_mean`, `gelman_rubin_max`,
  `effective_sample_size_min`, `best_log_posterior`.

The three overlapping pairs from §"Context" are resolved by **dropping
the `minimizer` copy** and keeping the `fit_result` copy:

- `minimizer.runtime_seconds` removed; `fit_result.fitting_time` is the
  single source.
- `minimizer.iterations_performed` removed;
  `fit_result.iterations` is the single source.
- `minimizer.objective_value` removed. `LeastSquaresFitResult` keeps
  **two distinct fields**: `objective_value` (raw χ² returned by the
  minimizer's objective function) and `reduced_chi_square` (= χ² /
  `degrees_of_freedom`). They are not duplicates; the unreduced value
  is what the solver actually optimises and is useful for diagnostics
  on small-dof fits, while the reduced value is what every user-facing
  table and plot displays. `BayesianFitResult` does not carry
  `objective_value` because the Bayesian engine optimises the log
  posterior rather than χ² directly.

### 3. CIF layout follows the Python split

The `_minimizer.*` block becomes settings-only. A new `_fit_result.*`
block (already present today for the common header fields) absorbs
every fit output. The set of `_fit_result.*` tags depends on the active
`_minimizer.type`, matching the same shape-shifting convention that
`_minimizer.*` itself already uses per
[`switchable-category-owned-selectors.md`](../accepted/switchable-category-owned-selectors.md).

Example deterministic fit:

```
_minimizer.type             'lmfit (leastsq)'
_minimizer.max_iterations    1000

_fit_result.result_kind            deterministic
_fit_result.success                true
_fit_result.message                converged
_fit_result.iterations             87
_fit_result.fitting_time           12.34
_fit_result.reduced_chi_square     1.42
_fit_result.objective_name         chi_square
_fit_result.objective_value        1532.4
_fit_result.n_data_points          1024
_fit_result.n_parameters           12
_fit_result.n_free_parameters      8
_fit_result.degrees_of_freedom     1016
_fit_result.covariance_available   true
_fit_result.correlation_available  true
_fit_result.exit_reason            converged
```

Example Bayesian fit:

```
_minimizer.type                       'bumps (dream)'
_minimizer.sampling_steps             3000
_minimizer.burn_in_steps              600
_minimizer.thinning_interval          1
_minimizer.population_size            4
_minimizer.parallel_workers           0
_minimizer.initialization_method      latin_hypercube
_minimizer.random_seed                ?
_minimizer.credible_interval_inner    0.68
_minimizer.credible_interval_outer    0.95

_fit_result.result_kind                bayesian
_fit_result.success                    true
_fit_result.message                    'sampler converged'
_fit_result.iterations                 3000
_fit_result.fitting_time               124.7
_fit_result.reduced_chi_square         1.18
_fit_result.point_estimate_name        best_sample
_fit_result.sampler_completed          true
_fit_result.acceptance_rate_mean       0.27
_fit_result.gelman_rubin_max           1.03
_fit_result.effective_sample_size_min  482
_fit_result.best_log_posterior        -1234.56
```

### 4. The runtime `analysis.fit_results` object is the same data shaped differently

`analysis.fit_results` (plural, runtime) is the rich `FitResults` /
`BayesianFitResults` Python object that holds posterior samples,
predictive summaries, raw engine results, and reporting helpers. This
ADR does **not** rename it. After the split it remains the
"give-me-everything" accessor; `analysis.fit_result.*` (singular, CIF
category) holds the persisted scalar projection of the same fit. The
naming pair stays as today.

A small UX win is added under the accepted display facade
([`display-ux.md`](../accepted/display-ux.md)): the existing
`project.display.fit.results()` entry point gains a "Settings used"
table above the existing results tables, populated from
`analysis.minimizer.*`. No new `Analysis`-level display method is
added; the user-facing surface stays exactly where the display ADR
put it. Internally the helper reads `self.minimizer.*` and
`self.fit_result.*` and renders one combined view.

### 5. Help and discoverability

`analysis.minimizer.help()` after the split lists ~7 properties for
Bayesian and 1 for LSQ — every one writable. The "is this writable"
question disappears.

`analysis.fit_result.help()` lists 6 common output properties plus the
family-specific ones, all clearly read-only.

### 6. No new selector wiring

`analysis.minimizer.type` remains the single user-facing selector. The
swap hook updates **both** `analysis.minimizer` and
`analysis.fit_result` instances atomically (via
`Analysis._swap_minimizer`, which reads the paired
`_fit_result_class` off the new minimizer base). The paired
`fit_result` is not a user-facing switchable: there is no
`fit_result.type` and no `fit_result.show_supported()`, per the
documented exception added to
[`switchable-category-owned-selectors.md`](../accepted/switchable-category-owned-selectors.md)
(see §"ADRs amended"). This keeps "one minimizer concept, one
user-facing type" intact and removes the temptation to swap the result
class independently of the minimizer.

## Consequences

### Positive

- **Clear writable surface.** `analysis.minimizer.help()` shows only
  settings. Inputs and outputs no longer mix in one namespace.
- **Single source for every output field.** The two current real
  duplications (`runtime_seconds`/`fitting_time` and
  `iterations_performed`/`iterations`) collapse to one location each.
  The `objective_value`/`reduced_chi_square` pair is **not** a
  duplication and both stay (see §2 for the distinction).
- **Family-specific outputs have a natural home.** Currently
  `minimizer.gelman_rubin_max` lives on the Bayesian minimizer class;
  after the split it lives on the paired `BayesianFitResult` class.
  The two categories pair symmetrically and emcee inherits the pattern
  for free.
- **CIF stays compact.** No new CIF blocks beyond `_fit_result.*` which
  is already present. The settings/outputs split is reflected in the
  CIF tag prefix.
- **The "are we done with a fit?" check becomes simple.**
  `bool(analysis.fit_result.success.value)` answers it directly without
  scanning a mixed input/output namespace.

### Trade-offs

- **Settings and matching outputs are two-place reads.** Mitigation:
  `project.display.fit.results()` presents both. The current layout
  already requires multi-place reads; this just makes the rule
  consistent.
- **`fit_result` becomes an internally-paired category.** The pairing
  cost is small (one paired-instance assignment in the existing
  `_swap_minimizer` hook) and is invisible to the user — there is no
  second `fit_result.type` selector. The exception to the global
  selector contract is documented explicitly in §"ADRs amended"
  alongside the selector ADR.
- **Saved CIF files from the post-consolidation layout cannot load
  unchanged.** Beta posture (no legacy shims) applies. Tutorial
  fixtures regenerate via `pixi run script-tests`. Tutorial `ed-24`
  already carries a narrow archive normaliser; the new layout would
  extend it once.
- **Reopens a decision from a recently accepted ADR.** Documented
  explicitly above in §"Status Note".

### ADRs amended by this ADR

- [`minimizer-category-consolidation.md`](../accepted/minimizer-category-consolidation.md)
  — §1 ("Unified `minimizer` category replaces all sampler-input and
  fit-result categories") becomes a partial rule: the unified
  `minimizer` holds inputs; outputs move to the paired `fit_result`.
  §"Alternatives Considered → D" updated to record the
  reversal and the implementation evidence that prompted it.
- [`analysis-cif-fit-state.md`](../accepted/analysis-cif-fit-state.md)
  — §"Minimizer fit projection" rewritten to describe the split
  (`_minimizer.*` settings-only, `_fit_result.*` outputs including
  family-specific fields).
- [`runtime-fit-results.md`](../accepted/runtime-fit-results.md)
  — closing paragraph references this ADR alongside the existing two.
- [`switchable-category-owned-selectors.md`](../accepted/switchable-category-owned-selectors.md)
  — §1 ("The category owns its selector") gains a paragraph carving
  out one documented exception: a category that is fully determined by
  another category's `type` (today only `fit_result`, derived from
  `minimizer.type`) is allowed to omit `category.type` and
  `category.show_supported()`. The mechanism is described in §1 of
  this ADR. The user-facing selector convention is otherwise unchanged.
- [`display-ux.md`](../accepted/display-ux.md) — §"Fit results display"
  expanded to mention that `project.display.fit.results()` now prints
  a "Settings used" block above the result tables, sourced from
  `analysis.minimizer.*`. No new public entry point is added.

## Deferred Work

- **Renaming `analysis.fit_results` (plural runtime object).** The
  plural/singular pair is mildly confusing but the rename has wide
  blast radius (tests, tutorials, every BayesianFitResults reference).
  Track separately if the confusion remains after the combined
  display lands.
- **Paired internal categories beyond `minimizer` / `fit_result`.**
  This ADR introduces the paired pattern for the minimizer only. If
  future categories grow the same input/output asymmetry (e.g.
  extinction, peak), apply the same pattern then; do not generalise
  pre-emptively.
- **Generalising the posterior-interval column naming.** Today the
  per-parameter posterior summary uses fixed numeric column names
  (`posterior_interval_68_low`, etc.). Promoting
  `credible_interval_inner/outer` to user settings raises the
  question of whether the column names should follow. Deferred to a
  separate suggestion ADR so this proposal stays focused on the
  input/output split.
- **CIF compatibility helper for ID 35 archive.** The
  `_normalize_id35_archive_for_tutorial` helper in `ed-24.py` already
  has a roadmap to deletion; the new CIF layout extends the rename map
  one more line. No new architecture decision needed.

## Alternatives Considered

### A. Keep current mixed-category layout, fix only the duplications

Drop `minimizer.runtime_seconds`, `.iterations_performed`,
`.objective_value` and route every reader to `fit_result.*`. Rejected
because it leaves the input/output mix on `minimizer` intact and
therefore does not fix the `minimizer.help()` discoverability problem.

### B. Mark fields with metadata, keep one category

Add an `is_input: bool` marker to each descriptor and have
`minimizer.help()` group inputs vs outputs in display. Rejected because
it ships the structural problem unchanged — the CIF still mixes both
under `_minimizer.*`, the duplications with `fit_result` remain, and
the `_set_*` vs writable-setter split is still ad-hoc.

### C. Move outputs into the runtime `fit_results` object, not a CIF category

Persist only settings in CIF; outputs live in `analysis.fit_results` at
runtime and `analysis/results.h5` on disk. Rejected because the small
scalar outputs (success, χ², runtime, R̂) are exactly what users want to
read from CIF without unpacking HDF5, and the consolidation ADR
explicitly puts them in CIF (`_minimizer.*` today).

### D. Rename `fit_result` to mirror minimizer (`minimizer_result`)

Make the pairing rule explicit in the name (`<x>` and `<x>_result`).
Rejected because the recently-accepted
[`switchable-category-owned-selectors.md`](../accepted/switchable-category-owned-selectors.md)
ADR deliberately drops `_type` and other suffixes from category names;
adding `_result` walks the convention back.
