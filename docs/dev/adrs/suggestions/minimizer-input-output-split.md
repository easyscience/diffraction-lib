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
fit-filled output fields move to `analysis.fit_result`, which also
becomes a switchable category that swaps in lockstep with the
minimizer's family so each family can declare its own output schema.

After this ADR:

| Category | Role | Family | Writable |
| -------- | ---- | ------ | -------- |
| `analysis.minimizer` | user-supplied settings | Family A (already) | yes |
| `analysis.fit_result` | scalar fit outputs | Family A (new) | no (internal `_set_*` only) |
| `analysis.fit_parameters` | per-parameter snapshots and posterior summary rows | (loop, unchanged) | no |
| `analysis.fit_parameter_correlations` | upper-triangle correlation rows | (loop, unchanged) | no |

The output split is paired by minimizer family:

- `analysis.minimizer = LmfitLeastsqMinimizer` ↔
  `analysis.fit_result = LeastSquaresFitResult`
- `analysis.minimizer = BumpsDreamMinimizer` ↔
  `analysis.fit_result = BayesianFitResult`

Both swap together when `analysis.minimizer.type` changes, via a single
`Analysis._swap_minimizer` hook that replaces both instances at once.
This preserves the consolidation ADR's "no `_bayesian_*` mirror"
guarantee — there is exactly one output category, not seven — while
making the input/output boundary unambiguous.

### 2. Field assignments

**`analysis.minimizer` after the split** (writable settings only):

- LSQ: `max_iterations`.
- Bayesian: `sampling_steps`, `burn_in_steps`, `thinning_interval`,
  `population_size`, `parallel_workers`, `initialization_method`,
  `random_seed`, `credible_interval_inner`, `credible_interval_outer`.

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
- `minimizer.objective_value` removed;
  `fit_result.reduced_chi_square` is the single source (or the
  per-family `LeastSquaresFitResult.objective_value` if the raw,
  un-normalised value matters separately).

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

A small UX win is added: `analysis.show_fit_summary()` prints settings
and outputs side-by-side, so users do not have to mentally join the
two categories. The method lives on `Analysis`, reads
`self.minimizer.*` and `self.fit_result.*`, and prints one table.

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
`Analysis._swap_minimizer`). The new `fit_result` switchable does
**not** expose its own `type` property — there is no scenario where the
user would set `fit_result.type` independently of `minimizer.type`, and
hiding the selector keeps the convention "one minimizer concept, one
user-facing type" intact.

## Consequences

### Positive

- **Clear writable surface.** `analysis.minimizer.help()` shows only
  settings. Inputs and outputs no longer mix in one namespace.
- **Single source for every output field.** The three current
  duplications (`runtime_seconds`/`fitting_time`,
  `iterations_performed`/`iterations`, `objective_value`/
  `reduced_chi_square`) collapse to one location each.
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
  `analysis.show_fit_summary()` presents both. The current layout
  already requires multi-place reads; this just makes the rule
  consistent.
- **`fit_result` becomes a switchable category.** Switchable-category
  cost is small (one factory + one swap hook on the owner), and the
  swap is co-triggered by `minimizer.type` so no second selector
  appears to the user.
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

## Deferred Work

- **Renaming `analysis.fit_results` (plural runtime object).** The
  plural/singular pair is mildly confusing but the rename has wide
  blast radius (tests, tutorials, every BayesianFitResults reference).
  Track separately if the confusion remains after `show_fit_summary()`
  lands.
- **`fit_result` switchable beyond Family A.** This ADR introduces a
  paired switch only for the minimizer. If future categories grow the
  same input/output asymmetry (e.g. extinction, peak), apply the same
  pattern then; do not generalise pre-emptively.
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
