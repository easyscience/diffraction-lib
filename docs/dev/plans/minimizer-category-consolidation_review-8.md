# Review 8: Minimizer Category Consolidation Branch (Post-Phase 2)

Reviewed plan:
[`minimizer-category-consolidation.md`](minimizer-category-consolidation.md)

Reviewed ADR:
[`../adrs/accepted/minimizer-category-consolidation.md`](../adrs/accepted/minimizer-category-consolidation.md)

This review follows
[`.github/copilot-instructions.md`](../../../.github/copilot-instructions.md).

Per the updated reviewer guidance in `.github/copilot-instructions.md`,
**no tests, lint, or check commands were run** for this review. This is
a static read of code, plan, and documentation against `develop`. The
implementer should run `pixi run fix`, `pixi run check`,
`pixi run unit-tests`, `pixi run integration-tests`, and
`pixi run script-tests` before merging if not already done.

Scope: full review of the 36 commits on
`minimizer-category-consolidation` against `develop`. Phase 1
(P1.1a–P1.15) and Phase 2 (P2.1a–P2.5) are both marked complete in the
plan. This pass confirms the Review 7 resolutions, re-runs the static
verification greps, and surfaces new findings that the prior reviews did
not flag.

## Summary

The branch is structurally complete and ready for the final `pixi run`
verification suite (deferred per task instructions).

- All seven Review 7 resolutions are reflected in the code as described:
  - F1, F2 → LSQ descriptor setup folded into
    `LeastSquaresMinimizerBase.__init__` via `@staticmethod` factory
    helpers; the eight LSQ concrete classes are now pure registration
    shells with only `type_info`
    ([lsq_base.py:59-113](src/easydiffraction/analysis/categories/minimizer/lsq_base.py:59),
    [lmfit.py:13-20](src/easydiffraction/analysis/categories/minimizer/lmfit.py:13)).
  - F3 → `Analysis._changed_minimizer_defaults` now compares two fresh
    default instances (not the live customised one) and the warning text
    reads "uses different defaults"
    ([analysis.py:1012-1019](src/easydiffraction/analysis/analysis.py:1012)).
  - F4 → result reset goes through
    `MinimizerCategoryBase._reset_result_descriptors`, which walks the
    active class's `_result_descriptor_names` and reads
    `AttributeSpec.default_value()`
    ([base.py:32-37](src/easydiffraction/analysis/categories/minimizer/base.py:32)).
  - F5 → the `analysis_to_cif` dead-fallback branch is removed;
    `analysis_to_cif` is now ~10 lines that always emits header tags
    plus the owner body
    ([serialize.py:428-439](src/easydiffraction/io/cif/serialize.py:428)).
  - F6 → deferred to the emcee plan (`emcee-minimizer.md`).
  - F7 → `_restore_deterministic_fit_state` and
    `_sync_live_minimizer_from_persisted_fit_state` are gone (grepped
    empty across `src/`).
  - F9 → `Analysis._sync_engine_from_minimizer_category` now warns
    instead of silently dropping; LSQ descriptors pruned to only the
    fields the deterministic engine consumes
    ([analysis.py:1077-1089](src/easydiffraction/analysis/analysis.py:1077),
    [lsq_base.py:23-57](src/easydiffraction/analysis/categories/minimizer/lsq_base.py:23)).
  - F10 → tests under `tests/` are fully migrated; new unit suite
    `tests/unit/easydiffraction/analysis/categories/minimizer/` mirrors
    `src/`.

- All five Phase-1 grep checks from P1.15 / Review 7 still return empty
  for `src/`, `docs/docs/tutorials/`, and now also `tests/` (see
  §"Verification commands run for this review").

- The plan's deletion list (seven Bayesian categories, `fitting/`,
  `deterministic_result/`) matches the source tree; the new `minimizer/`
  package contains exactly the 13 declared modules plus `__init__.py`
  and `factory.py`.

The findings below are not blockers, but most should be acknowledged
before the emcee plan starts so it inherits a clean foundation.

## Findings

### F1 — Duplicate predictive-cache-key helpers in `analysis.py` and `plotting.py`

Two helpers produce the exact same cache-key string:

- `Analysis._predictive_cache_key`
  ([analysis.py:478-487](src/easydiffraction/analysis/analysis.py:478))
- `Plotter._posterior_predictive_key`
  ([plotting.py:3795-3804](src/easydiffraction/display/plotting.py:3795))

Both return `f'{name}:{x_axis_name}:{suffix}'` where `suffix` is
`'draws'` or `'band'`. They are called from each other's neighbours —
`Analysis._restored_predictive_summaries` and
`Analysis._store_posterior_predictive_projection` use the analysis copy,
while `Plotter._posterior_predictive` and
`PosteriorDisplay._predictive_needs_processing_indicator` use the
plotter copy — and the runtime cache is keyed by whichever helper
populated it. The strings are identical today; a future refactor that
changes one will silently break lookup against the other.

Suggested follow-up: collapse to a single helper. Either:

- Move the canonical helper to a shared module (e.g.
  `analysis/fit_helpers/bayesian.py` already exports cache types) and
  import it from both callers.
- Or keep `Plotter._posterior_predictive_key` as the canonical and have
  `Analysis._store_posterior_predictive_projection` /
  `_restored_predictive_summaries` import it from
  `project.rendering.plotter` (which is already accessed in adjacent
  code).

Either pick avoids the "two definitions, no compile-time check" state.

### F2 — Sidecar enum comparison is string-based

`results_sidecar.py:43-46` `_should_use_sidecar` reads:

```python
return analysis.fit_result.result_kind.value == 'bayesian'
```

`FitResultKindEnum.BAYESIAN.value` is `'bayesian'`, but the literal
`'bayesian'` is hard-coded rather than dereferenced from the enum.
[`.github/copilot-instructions.md`](../../../.github/copilot-instructions.md)
→ **Architecture** says "Every finite, closed set of values […] is a
`(str, Enum)`; compare against members, not raw strings."

Suggested follow-up: import `FitResultKindEnum` in `results_sidecar.py`
and use `FitResultKindEnum.BAYESIAN.value` (or compare to the enum
member directly after coercing the raw string with
`FitResultKindEnum(...)`). The same fix in
`_restore_fit_results_from_projection`
([analysis.py:649](src/easydiffraction/analysis/analysis.py:649)) is
already enum-based.

### F3 — Swap warning text shows `'<not available>'` across families

`Analysis._changed_minimizer_defaults`
([analysis.py:1037-1052](src/easydiffraction/analysis/analysis.py:1037))
unions the old and new `_setting_descriptor_names` and renders missing
fields as the string `'<not available>'`. Switching `lmfit` →
`bumps (dream)` produces:

```
Switching minimizer type uses different defaults:
  burn_in_steps '<not available>'->600,
  initialization_method '<not available>'->'latin_hypercube',
  max_iterations 1000->'<not available>',
  parallel_workers '<not available>'->0,
  population_size '<not available>'->4,
  random_seed '<not available>'->None,
  sampling_steps '<not available>'->3000,
  thinning_interval '<not available>'->1.
```

For the project's stated audience (scientists, often non-programmers —
see CLAUDE.md → Project Context), the `'<not available>'` token will
read as a bug. The fix is small: split the warning into two lines, one
per family, e.g. "Settings removed: max_iterations" and "Settings added
with defaults: sampling_steps=3000, …".

This is cosmetic but high-visibility — the warning fires on every
inter-family swap.

### F4 — `_fit_state_categories` has both branches returning the same list

[analysis.py:1135-1148](src/easydiffraction/analysis/analysis.py:1135):

```python
if result_kind is FitResultKindEnum.DETERMINISTIC:
    return categories

return categories
```

The conditional is dead. Either:

- The conditional was meant to filter Bayesian-only categories before
  P1.10 absorbed them; the body never got cleaned up.
- Or it is a placeholder for future Bayesian-only categories that the
  Bayesian projection no longer needs because everything is on the
  minimizer or in the sidecar.

Suggested follow-up: drop the unreachable second `return`, simplify to
either a one-line return or an unconditional `return categories`. If the
intent was a Bayesian-specific category list, add a TODO and an explicit
branch.

The unused `try/except` on lines 1135-1142 then becomes a pure
warning-emitter; that is still useful, so keep it — but extract the
warning so the function body reads cleanly.

### F5 — Restore path reaches Bayesian-only fields without category-type check

[analysis.py:649-700](src/easydiffraction/analysis/analysis.py:649):

```python
if self.fit_result.result_kind.value == FitResultKindEnum.BAYESIAN.value:
    posterior_samples = self._restored_posterior_samples()
    ...
    sampler_settings = self.minimizer._native_kwargs()
    ...
    self.minimizer.point_estimate_name.value,
    self.minimizer.gelman_rubin_max.value,
    self.minimizer.effective_sample_size_min.value,
    ...
```

These attributes exist only on `BayesianMinimizerBase`. The guard above
keys off `_fit_result.result_kind` (`'bayesian'`), but the CIF persists
`_fitting.minimizer_type` and `_fit_result.result_kind` independently. A
hand-edited or stale CIF with `result_kind = bayesian` but
`minimizer_type = lmfit (leastsq)` will crash with
`AttributeError: 'LmfitLeastsqMinimizer' object has no attribute 'point_estimate_name'`.

Per CLAUDE.md → Project Context ("clear errors, and safe defaults over
developer ergonomics") and ADR §5 ("Loading a CIF whose tags don't match
the minimizer's allowed set raises (clear validation, not silent
ignoring)"), this should be caught explicitly. Two cheap options:

- After `_set_minimizer_type` in `analysis_from_cif`, validate that
  `analysis.minimizer` is `BayesianMinimizerBase` if
  `_fit_result.result_kind == 'bayesian'`, and raise a clear
  `ValueError` if not.
- Or, gate the Bayesian field reads on
  `isinstance(self.minimizer, BayesianMinimizerBase)` and downgrade to a
  deterministic restore with a warning if the pair is inconsistent.

Either makes the failure mode legible.

### F6 — LSQ result descriptors mix `0` and `None` defaults

[lsq_base.py:152-159](src/easydiffraction/analysis/categories/minimizer/lsq_base.py:152)
declares integer result descriptors with `default=0`:

```python
@staticmethod
def _integer_result_descriptor(name: str, description: str) -> NumericDescriptor:
    return NumericDescriptor(
        name=name, description=description,
        value_spec=AttributeSpec(default=0),
        cif_handler=CifHandler(names=[f'_minimizer.{name}']),
    )
```

while the numeric result descriptor uses `default=None, allow_none=True`
([lsq_base.py:135-149](src/easydiffraction/analysis/categories/minimizer/lsq_base.py:135)).
The integer fields (`n_data_points`, `n_parameters`,
`n_free_parameters`, `degrees_of_freedom`, `iterations_performed`) and
the bool fields (`covariance_available`, `correlation_available`)
therefore round-trip through CIF as `0` / `false` rather than `?`.
Effects:

- ADR §7 says "save path always emits the actual value." When no fit has
  happened, the "actual value" is the descriptor default — `0` for
  integers, `false` for booleans, `?`/missing for floats. A CIF written
  before any fit will show `_minimizer.n_data_points 0` and
  `_minimizer.covariance_available false`, which reads to a scientist as
  "the fit produced a degenerate result" rather than "no fit has
  happened yet."
- On read-back, the `0` survives the round-trip with no signal that the
  fit hasn't run.

Suggested follow-up: pick one of:

- Switch all LSQ result descriptors to `default=None, allow_none=True`
  and write `?` to CIF for the no-fit case; readers already handle `?` →
  default via the P1.5 rule.
- Or add a top-level `_minimizer.has_fit_result` boolean (or reuse
  `_fit_result.success`) and document that the result descriptors are
  only meaningful when the flag is true.

The Bayesian side uses `default=None, allow_none=True` consistently
([bayesian_base.py:212-249](src/easydiffraction/analysis/categories/minimizer/bayesian_base.py:212));
aligning LSQ with that pattern is the lower-friction option.

### F7 — `_restore_persisted_fit_state` computes but does not use `result_kind`

[serialize.py:595-611](src/easydiffraction/io/cif/serialize.py:595):

```python
result_kind_value = analysis.fit_result.result_kind.value
try:
    FitResultKindEnum(result_kind_value)
except ValueError:
    log.warning(...)
```

The `FitResultKindEnum(result_kind_value)` call is for its side effect
(triggering the warning); the result is discarded. After P1.10 absorbed
the Bayesian-specific categories there is nothing else to do per
`result_kind`. The `if FitResultKindEnum.DETERMINISTIC` branch in
`_fit_state_categories` (F4) has the same shape.

Suggested follow-up: replace with a validator helper that takes a string
and logs the warning; or move the warning into `fit_result.result_kind`
setter so invalid values are caught on read. Either removes the "compute
and ignore" pattern.

### F8 — `Analysis` eagerly imports `BayesianFitResults` / `PosteriorSamples`

[analysis.py:30-33](src/easydiffraction/analysis/analysis.py:30):

```python
from easydiffraction.analysis.fit_helpers.bayesian import BayesianFitResults
from easydiffraction.analysis.fit_helpers.bayesian import PosteriorPredictiveSummary
from easydiffraction.analysis.fit_helpers.bayesian import PosteriorSamples
```

These are used in the restore and projection methods, which run only on
Bayesian fits. The plan and ADR did not promise to make them lazy, and
`.github/copilot-instructions.md` → **Architecture** explicitly prefers
eager imports unless avoiding a circular dep — so this is informational,
not a defect. Recording it because the next sampler (emcee) will add a
comparable surface, and "all of `Analysis.__init__` warms the Bayesian
subtree" is worth deciding on consciously rather than by accident.

If a future profile shows `import easydiffraction` is slow for
deterministic-only workflows, this is one of the larger reductions
available.

### F9 — `FitParameterItem.posterior_summary` returns NaN-filled summaries when any single field is set

[fit_parameters/default.py:277-320](src/easydiffraction/analysis/categories/fit_parameters/default.py:277):

```python
def has_posterior_summary(self) -> bool:
    return any(
        value is not None
        for value in (
            self.posterior_best_sample_value.value,
            ...
            self.posterior_gelman_rubin.value,
            self.posterior_effective_sample_size_bulk.value,
        )
    )

def posterior_summary(self, *, display_name: str) -> PosteriorParameterSummary | None:
    if not self.has_posterior_summary():
        return None
    return PosteriorParameterSummary(
        ...
        median=self._posterior_float(self.posterior_median.value),
        standard_deviation=self._posterior_float(self.posterior_uncertainty.value),
        interval_68=(self._posterior_float(...), self._posterior_float(...)),
        ...
    )
```

If a CIF is partially edited or written by a future bug, a row with only
`posterior_gelman_rubin = 1.02` and all other posterior fields unset
will produce a `PosteriorParameterSummary` whose `median`,
`standard_deviation`, and both interval bounds are `NaN`. Downstream
plotting (`plotting.py`) and the `display.fit_results` table will then
render NaN intervals, which is harder to debug than a clean "no
posterior" outcome.

Suggested follow-up: tighten `has_posterior_summary` to require the core
stats (e.g. `posterior_median` and one interval bound) before emitting a
summary, or split the `PosteriorParameterSummary` into
required-statistics and optional-diagnostics components.

The deterministic-fit case is fine: deterministic fits set all the
required fields to `None`, so `has_posterior_summary()` returns `False`
and no summary is emitted.

### F10 — `Analysis._sync_engine_from_minimizer_category` excludes `random_seed`

[analysis.py:1077-1089](src/easydiffraction/analysis/analysis.py:1077):

```python
def _sync_engine_from_minimizer_category(self) -> None:
    engine = self.fitter.minimizer
    for key, value in self.minimizer._native_kwargs().items():
        if key == 'random_seed':
            continue
        if not hasattr(engine, key):
            log.warning(...)
            continue
        setattr(engine, key, value)
```

`random_seed` is intentionally excluded because
`_resolved_fit_random_seed`
([analysis.py:1091-1096](src/easydiffraction/analysis/analysis.py:1091))
threads it through the call-time argument instead. This is correct
behaviour, but the magic-string `'random_seed'` in the loop body is the
kind of thing that decays when a second engine-level "ambient" key joins
it.

Suggested follow-up: define a class-level
`_engine_sync_skip_keys: ClassVar[frozenset[str]] = frozenset({'random_seed'})`
on `MinimizerCategoryBase` (or on each family), and filter against it.
Adds explicit, declarative coverage that grows with each new key.

Low-priority. Mentioned because the emcee plan introduces
`proposal_moves` which is also engine-level (and may want the same
ambient handling).

## Documentation

- Plan's status checklist marks all P1._ and P2._ items `[x]`. P2 steps
  include verification commands but, per task instructions, no
  `pixi run` was executed for this review. The implementer must confirm
  P2.2–P2.5 still pass before merging.
- ADR is in `accepted/`. The amended ADRs (`analysis-cif-fit-state.md`,
  `fit-mode-categories.md`, `selector-families.md`,
  `runtime-fit-results.md`, `switchable-category-api.md`) and the
  superseded `parameter-posterior-summary.md` are updated.
- `docs/dev/issues/{open,closed}.md` carry no new entry for this work,
  matching the Review 7 note. The findings above (especially F1, F3, F5,
  F6, F9) are good candidates for `docs/dev/issues/open.md` entries if
  not addressed in this PR.
- The PR description in the plan reads cleanly for a non-developer
  audience.

## Verification commands run for this review

Per the updated reviewer instructions, no `pixi run`, lint, or test
commands were executed. Only static read-only `git grep`s were used:

```text
git grep -nE 'analysis\.bayesian_|categories\.bayesian_|_bayesian_(sampler|result|convergence|parameter_posterior|distribution_cache|pair_cache|predictive_dataset)' src/ docs/docs/tutorials/ tests/
git grep -nE 'analysis\.deterministic_result|_deterministic_result\.' src/ docs/docs/tutorials/ tests/
git grep -nP '\banalysis\.fitting\.(minimizer|show_minimizer_types|minimizer_type)\b|\bproject\.analysis\.fitting\b' src/ docs/docs/tutorials/ tests/
git grep -nE 'show_minimizer_types|show_fitting_mode_types' src/ docs/docs/tutorials/ tests/
git grep -nE "MinimizerTypeEnum\.[A-Z_]+" src/easydiffraction/analysis/categories/minimizer/
```

The first four return empty across `src/`, `docs/docs/tutorials/`, and
`tests/`. The last (P1.4 coverage check) lists all nine enum members
exactly once, one per concrete class.

## Recommended next steps

1. **Before running Phase-2 verification suites**, decide F2, F5, F6. F5
   (Bayesian-restore guard) and F6 (LSQ defaults) shape what a clean CIF
   round-trip looks like; merging without them invites a follow-up
   migration once a hand-edited CIF turns up.
2. **Cosmetic but visible:** F3 (swap warning text) — small change, but
   the warning is the user's first signal that anything happened.
3. **Refactor candidates** for the emcee plan: F1 (duplicate cache-key
   helper), F4 (dead branch), F7 (compute-and-ignore), F10 (skip-keys
   frozenset). None block the current PR; recording them so
   `emcee-minimizer.md` can collapse them while the surrounding code is
   already being touched.
4. **Informational:** F8 (eager Bayesian imports) — leave as-is unless
   import time becomes a problem.
5. **Run `pixi run fix`, `pixi run check`, `pixi run unit-tests`,
   `pixi run integration-tests`, `pixi run script-tests` before
   merging.** These were intentionally not executed for this review.
