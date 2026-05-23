# ADR: Minimizer Category Consolidation

## Status

Proposed.

## Date

2026-05-23

## Group

Analysis and fitting.

## Context

Recent Bayesian (DREAM) work introduced seven analysis-level categories
to persist Bayesian fit settings, results, diagnostics, per-parameter
summaries, and plot caches:

- `_bayesian_sampler` (resolved sampler inputs)
- `_bayesian_result` (Bayesian header)
- `_bayesian_convergence` (diagnostics)
- `_bayesian_parameter_posterior` (per-parameter summaries)
- `_bayesian_distribution_cache`, `_bayesian_pair_cache`,
  `_bayesian_predictive_dataset` (plot-ready cache manifests)

This layout is internally consistent but breaks the convention used
everywhere else in the codebase:

1. **One category per concept, plain descriptive name.** Structure and
   experiment categories (`cell`, `peak`, `background`, `instrument`)
   are single-concept and unsuffixed. The Bayesian work introduces a
   parallel naming with prefixes (`bayesian_*`) and a settings/result
   mirror that has no precedent.
2. **Refinement annotates the object in place.** A `Parameter` carries
   both its user-set initial value and its fit-refined value plus
   uncertainty on the same object. The Bayesian work stores per-
   parameter posterior data in a separate loop category instead of on
   the parameter.
3. **Selectors live on the owner.** `experiment.background_type` and
   `experiment.peak_profile_type` are owner-level. The minimizer
   selector lives one level deep at `analysis.fitting.minimizer_type`,
   which has no analogous depth elsewhere.
4. **One user-input surface per concept.** Users today configure the
   sampler at `analysis.fitting.minimizer.<attr>` (live solver instance
   attributes), while the persisted `_bayesian_sampler.*` category is a
   post-run snapshot with no public setters. The same fact lives in two
   places, only one is writable, only the other appears in `help()` and
   CIF.

Adding emcee on top of this layout would entrench the divergence. This
ADR consolidates the design before introducing additional Bayesian
samplers.

## Decision

### 1. Unified `minimizer` category replaces all sampler-input and fit-result categories

Introduce a single switchable category `minimizer` on `Analysis`. Its
concrete class is determined by `Analysis.minimizer_type`. The category
holds both user-writable inputs and fit-filled outputs in one place.

The following categories are removed:

- `bayesian_sampler` — fields move into the Bayesian concrete classes
  of `minimizer`.
- `bayesian_result`, `bayesian_convergence` — fields move into the
  Bayesian concrete classes of `minimizer` (`runtime_seconds`,
  `acceptance_rate_mean`, `gelman_rubin_max`,
  `effective_sample_size_min`, `best_log_posterior`, …).
- `deterministic_result` — fields move into the deterministic concrete
  classes of `minimizer` (`runtime_seconds`, `iterations_performed`,
  `exit_reason`, `negative_log_likelihood`, …).
- `bayesian_parameter_posterior` — replaced by `Parameter.posterior`
  (see §3).
- `bayesian_distribution_cache`, `bayesian_pair_cache`,
  `bayesian_predictive_dataset` — replaced by HDF5 sidecar (see §4).

`fit_result` and `fit_parameter` (analysis-owned bounds, success flag,
reduced chi-square, message, fit time, iterations) remain unchanged as
fit-mode-agnostic header categories.

### 2. Selectors move to the `Analysis` owner

The Python `fitting` category intermediate is dropped. `Analysis`
exposes:

- `analysis.minimizer_type` (was `analysis.fitting.minimizer_type`)
- `analysis.fitting_mode_type` (was `analysis.fitting.fitting_mode_type`)
- `analysis.minimizer` (the swappable category)
- `analysis.show_minimizer_types()`
- `analysis.show_fitting_mode_types()`
- `analysis.joint_fit`, `analysis.sequential_fit` (unchanged
  active-sibling categories per
  [`fit-mode-categories.md`](../accepted/fit-mode-categories.md))

CIF prefixes are unchanged:

- `_fitting.minimizer_type`, `_fitting.mode_type` stay where they are.
- `_bayesian_sampler.*` is removed; the equivalent fields live under
  `_minimizer.*`.

Rationale: matches the
[Switchable Category API](../accepted/switchable-category-api.md)
convention used by `experiment.background_type` etc. — selector on the
owner, category as a read-only attribute that gets swapped.

### 3. Per-parameter posterior data lives on `Parameter.posterior`

Adopt the proposal from
[`parameter-posterior-summary.md`](parameter-posterior-summary.md):
`GenericParameter.posterior` is `None` for deterministic fits and a
`PosteriorParameterSummary` for Bayesian fits. The
`_bayesian_parameter_posterior` CIF loop is removed; posterior summary
columns are added to the existing `_fit_parameter` loop (one row per
refined parameter, mostly-empty columns when the fit was
deterministic):

- `_fit_parameter.posterior_best_sample_value`
- `_fit_parameter.posterior_median`
- `_fit_parameter.posterior_uncertainty`
- `_fit_parameter.posterior_interval_68_low`,
  `posterior_interval_68_high`
- `_fit_parameter.posterior_interval_95_low`,
  `posterior_interval_95_high`
- `_fit_parameter.posterior_gelman_rubin`
- `_fit_parameter.posterior_effective_sample_size_bulk`

This mirrors `Parameter.uncertainty`: the same column structure is
populated by deterministic or Bayesian fits as appropriate. Per-
parameter posterior order is the order of the `_fit_parameter` rows
themselves; no separate parallel loop is needed.

### 4. Heavy posterior arrays live in `analysis/results.h5`, not in CIF

Posterior chains, KDE / distribution caches, pair-plot caches, and
predictive datasets are large arrays unsuited to CIF. The existing
`analysis/results.h5` sidecar absorbs all of them. The corresponding
manifest categories (`_bayesian_distribution_cache`,
`_bayesian_pair_cache`, `_bayesian_predictive_dataset`) are removed
from CIF entirely — the HDF5 file is self-describing.

There is exactly **one** sidecar file per fit, regardless of
minimizer: `analysis/results.h5`. No CIF tag stores the sidecar path.
The file uses namespaced top-level groups:

```
analysis/results.h5
├── /posterior/            # canonical posterior chains, log-prob (all Bayesian samplers)
├── /distribution_cache/   # KDE / 1-D distribution plots
├── /pair_cache/           # pair-plot grids
├── /predictive/           # posterior-predictive datasets
└── /emcee_chain/          # emcee HDFBackend live state (emcee runs only)
```

**Lifecycle rule: a new fit overwrites the file.** Mixing partial
results from different minimizers — or from the same minimizer with
different settings or a different free-parameter set — is the most
common source of "stale plot" confusion. To prevent this, calling
`analysis.fit()` truncates `analysis/results.h5` (recreating it with
the new run's groups). The user is shown a `log.warn(...)` message
the first time a fit is started while a populated sidecar exists,
naming the file and stating that previous results will be overwritten.

Resume is the only exception: `analysis.fit(resume=True,
extra_steps=N)` opens the existing file in append mode and extends
the chain. Resume is rejected with a clear error if the active
minimizer does not support it, if `results.h5` is missing, or if the
stored chain's parameter set does not match the current one.

For deterministic runs the Bayesian groups are absent and the sidecar
file may not exist at all. For non-emcee Bayesian runs the
`/emcee_chain` group is absent.

### 5. Unified, verbose attribute names with internal mapping

Each concrete `minimizer` class declares its descriptors in its class
body with verbose, dictionary-style names. Internally, each class maps
these names to its native backend keys.

Stable inputs across Bayesian samplers (shared by DREAM and emcee):

| Tag                       | Native (DREAM)       | Native (emcee)     | Description                                                |
|---------------------------|----------------------|--------------------|------------------------------------------------------------|
| `sampling_steps`          | `steps`              | `nsteps`           | Total MCMC iterations per chain/walker                     |
| `burn_in_steps`           | `burn`               | `nburn`            | Iterations discarded as warm-up                            |
| `thinning_interval`       | `thin`               | `thin`             | Keep every Nth sample                                      |
| `population_size`         | `pop`                | `nwalkers`         | Number of chains / walkers                                 |
| `parallel_workers`        | `parallel` (int)     | `pool`             | `0` = all CPUs; `1` = serial; `N>1` = N worker processes   |
| `initialization_method`   | `init` (enum)        | (custom)           | Single unified enum (see §6)                               |
| `random_seed`             | `random_seed`        | `random_seed`      | Random seed; `None` = system-derived                       |

Bayesian-sampler-specific inputs:

| Tag                | Concrete class | Description                       |
|--------------------|---------------|-----------------------------------|
| `proposal_moves`   | emcee only    | emcee proposal moves (e.g. `stretch`, `de`) |

Deterministic-LSQ inputs:

| Tag                       | Description                                            |
|---------------------------|--------------------------------------------------------|
| `max_iterations`          | Maximum solver iterations                              |
| `convergence_tolerance`   | Convergence tolerance                                  |
| `random_seed`             | Same semantics as Bayesian                             |

Fit-filled outputs (subset varies per class):

| Tag                              | Class                | Description                                  |
|----------------------------------|----------------------|----------------------------------------------|
| `runtime_seconds`                | all                  | Wall time of the fit                         |
| `reduced_chi2`                   | all                  | Reduced χ²                                   |
| `negative_log_likelihood`        | all                  | −log L (replaces `nllf`)                     |
| `iterations_performed`           | LSQ                  | Iterations actually executed                 |
| `exit_reason`                    | LSQ                  | Free-form short string                       |
| `acceptance_rate_mean`           | Bayesian             | Mean acceptance rate across chains/walkers   |
| `gelman_rubin_max`               | Bayesian             | Max R̂ across sampled parameters             |
| `effective_sample_size_min`      | Bayesian             | Min effective sample size across parameters  |
| `best_log_posterior`             | Bayesian             | Best log-posterior value found               |

Verbose CIF tags are user-facing. The canonical MCMC abbreviation
(`r_hat`, `n_eff`, `nllf`) is recorded in the descriptor's
`description` field so it appears in `help()` output but does not
become a Python attribute or a CIF tag.

### 6. Unified `initialization_method` enum

A single `(str, Enum)` `InitializationMethodEnum` with members:

- `latin_hypercube`
- `ball`
- `uniform`
- `prior`

Each concrete class accepts only the subset it supports and maps to its
native init mode (DREAM `lhs` ↔ `latin_hypercube`, emcee starting-state
generators ↔ `ball` / `uniform` / `prior`). Invalid combinations raise
at set time, not at fit time.

### 7. CIF `?` is the universal "use default" marker

Descriptors declare static defaults at class-body level via
`AttributeSpec(default=...)`. CIF behavior:

- **Load.** A missing tag, or a tag with value `?`, resolves to the
  descriptor's static default at load time. The category instance
  carries the concrete default value from that moment on.
- **Save.** Always emit the actual value. Do not emit `?` for fields
  that happen to equal the default. Round-trip is exact for any value
  the user set; for an unset field, round-trip resolves `?` → default
  on first load and emits the default on next save.
- **No callable defaults.** No "auto-resolve at fit time" (today's
  `burn = steps // 5` is replaced by a fixed default `burn_in_steps =
  600`). If a default depends on other settings, the dependency is
  documented; the user sets it explicitly.

This rule applies to every descriptor, not just `minimizer`. For
descriptors that have no sensible default (e.g. `cell.length_a`), the
descriptor declaration omits `default=...` and CIF `?` continues to
mean "unknown" — a load-time error is raised when the field is read.

### 8. Concrete classes carry their own defaults; warn-and-reset on swap

Each concrete `minimizer` class declares descriptors directly in its
class body with class-specific defaults. No mixins.

```python
class DreamMinimizer(BayesianMinimizerBase):
    sampling_steps  = IntegerDescriptor(spec=AttributeSpec(default=3000, ...))
    population_size = IntegerDescriptor(spec=AttributeSpec(default=4,    ...))
    # …

class EmceeMinimizer(BayesianMinimizerBase):
    sampling_steps  = IntegerDescriptor(spec=AttributeSpec(default=5000, ...))
    population_size = IntegerDescriptor(spec=AttributeSpec(default=32,   ...))
    proposal_moves  = StringDescriptor(spec=AttributeSpec(default='stretch', ...))
    # …
```

When `analysis.minimizer_type` changes, the underlying instance is
replaced by a fresh instance of the new class with that class's
defaults. A `log.warn(...)` lists fields whose default values differ
between old and new classes, matching the precedent of `background_type`
swap warnings.

### 9. Example CIF layouts

`bumps (lm)`:

```
data_analysis

_fitting.mode_type        joint
_fitting.minimizer_type  'bumps (lm)'

_minimizer.max_iterations           200
_minimizer.convergence_tolerance    1.0e-6
_minimizer.random_seed              ?
_minimizer.runtime_seconds          12.34
_minimizer.iterations_performed     87
_minimizer.exit_reason              converged
_minimizer.reduced_chi2             1.42
_minimizer.negative_log_likelihood  1532.4
```

`bumps (dream)`:

```
data_analysis

_fitting.mode_type        joint
_fitting.minimizer_type  'bumps (dream)'

_minimizer.sampling_steps             3000
_minimizer.burn_in_steps              600
_minimizer.thinning_interval          1
_minimizer.population_size            4
_minimizer.parallel_workers           0
_minimizer.initialization_method      latin_hypercube
_minimizer.random_seed                ?
_minimizer.runtime_seconds            124.7
_minimizer.acceptance_rate_mean       0.27
_minimizer.gelman_rubin_max           1.03
_minimizer.effective_sample_size_min  482
_minimizer.best_log_posterior        -1234.56
_minimizer.reduced_chi2               1.18
```

`emcee` (added by the follow-up plan):

```
data_analysis

_fitting.mode_type        joint
_fitting.minimizer_type   emcee

_minimizer.sampling_steps             5000
_minimizer.burn_in_steps              1000
_minimizer.thinning_interval          5
_minimizer.population_size            32
_minimizer.proposal_moves             stretch
_minimizer.parallel_workers           0
_minimizer.initialization_method      ball
_minimizer.random_seed                42
_minimizer.runtime_seconds            87.3
_minimizer.acceptance_rate_mean       0.31
_minimizer.gelman_rubin_max           1.02
_minimizer.effective_sample_size_min  612
_minimizer.best_log_posterior        -1237.89
_minimizer.reduced_chi2               1.22
```

emcee's resumable chain state lives in the `/emcee_chain` group of
the same `analysis/results.h5` file (see §4). No sidecar path appears
in CIF.

## Consequences

### Architecture wins

- The analysis layout matches the rest of the codebase: one descriptive
  category per concept, selectors on owners, refinement-in-place.
- The Bayesian / deterministic split stops requiring parallel category
  trees. One swappable `minimizer` covers both worlds.
- Adding new minimizers (emcee, future samplers, future LSQ variants)
  is a one-class change: declare descriptors, register with the
  factory.
- CIF projects shrink: large arrays move to HDF5; redundant manifest
  categories disappear.

### Trade-offs

- `minimizer` is the first category that mixes writable user inputs and
  writable fit-filled outputs in the same scope. This is a small new
  convention but is the natural generalization of how `Parameter`
  already holds both user input and refined value on the same object.
- The set of `_minimizer.*` tags present in CIF depends on the active
  `_fitting.minimizer_type`. Loading a CIF whose tags don't match the
  minimizer's allowed set raises (clear validation, not silent
  ignoring).
- Hand-editing CIF to switch minimizer types requires touching both
  `_fitting.minimizer_type` and the relevant `_minimizer.*` tags.
- Existing projects saved under the seven-category layout cannot load
  unchanged. The project is in beta; per
  `.github/copilot-instructions.md` "no legacy shims" applies. Saved
  fixtures under `tmp/tutorials/projects/` are regenerated by the
  implementation plan.

### ADRs that need to be updated when this ADR is accepted

- [`runtime-fit-results.md`](../accepted/runtime-fit-results.md) —
  amend the closing line to point at this ADR as the canonical
  saved-projection definition (alongside `analysis-cif-fit-state.md`).
- [`analysis-cif-fit-state.md`](../accepted/analysis-cif-fit-state.md)
  — replace §"Bayesian fit projection" entirely. Remove the seven
  `_bayesian_*` categories; describe `_minimizer.*` and the extended
  `_fit_parameter` posterior columns. Remove the sidecar-path CIF
  field; the sidecar name is implicit.
- [`fit-mode-categories.md`](../accepted/fit-mode-categories.md) —
  update §1 and §2 to reflect that `minimizer_type` and
  `fitting_mode_type` live on `Analysis` directly, not on a `fitting`
  Python intermediate. The active-sibling design for `joint_fit` /
  `sequential_fit` is unchanged.
- [`selector-families.md`](../accepted/selector-families.md) —
  reclassify `fitting.minimizer_type` as a switchable-category
  selector (on owner `Analysis`, swaps the `minimizer` category
  instance), no longer a Backend selector.
- [`switchable-category-api.md`](../accepted/switchable-category-api.md)
  — append `minimizer` to the examples list. No mechanical change.
- [`parameter-correlation-persistence.md`](../accepted/parameter-correlation-persistence.md)
  — verify wording still applies (categories `_fit_parameter_correlation`
  are kept by this ADR; should be a no-op).

### Suggestions superseded or absorbed

- [`parameter-posterior-summary.md`](parameter-posterior-summary.md) —
  absorbed by §3 of this ADR. When this ADR is accepted, that
  suggestion can be closed and a pointer added.

## Alternatives Considered

### A. Keep `bayesian_settings` and `least_squares_settings` as separate categories

Two stable input categories, each switchable internally. Rejected
because it (i) introduces the `_settings` suffix convention that has no
precedent in the codebase, (ii) duplicates the input/output mirror
pattern, and (iii) gains nothing over a single owner-level category
whose shape adapts to the active minimizer.

### B. Single flat `fit_settings.<family>_<attr>` category

One namespace, attributes prefixed by family. Rejected because (i) it
forces long attribute names (`fit_settings.bayesian_population_size`),
(ii) breaks the "one category, one focused concept" convention, and
(iii) loses the natural shape-shifting that `background` and
`peak_profile` already exemplify.

### C. Keep the seven-category Bayesian layout and add emcee siblings

Add `_emcee_sampler`, `_emcee_convergence`, …, mirroring the existing
`_bayesian_*` layout per backend. Rejected because it doubles the
category count for each new sampler and entrenches the convention
break.

### D. Strict input-only `minimizer` plus a separate `fit_result`

Keep the categories single-concept (inputs xor outputs) at the cost of
two-place lookup for related info. Rejected in favour of the
one-category-mixes-both shape (§1, §"Trade-offs") because the existing
`Parameter` model already mixes input and refined value on the same
object, and one-place discoverability is more valuable than strict
purity.
