# Review 7: Minimizer Category Consolidation Branch

Reviewed plan:
[`minimizer-category-consolidation.md`](minimizer-category-consolidation.md)

Reviewed ADR:
[`../adrs/accepted/minimizer-category-consolidation.md`](../adrs/accepted/minimizer-category-consolidation.md)

This review follows
[`.github/copilot-instructions.md`](../../../.github/copilot-instructions.md).

Scope: full review of the 21 commits on
`minimizer-category-consolidation` against `develop`, covering Phase 1
implementation (P1.1a–P1.15). Phase 2 (P2.1a–P2.5) is not yet started
and is not in scope here except where Phase 1 work pre-empts it.

## Summary

Phase 1 is structurally complete and matches the ADR's high-level
shape. All Phase-1 verification greps from P1.12 / P1.13 / P1.15
return empty against `src/` and `docs/docs/tutorials/`:

- no `analysis.bayesian_*`, `categories.bayesian_*`, or `_bayesian_*`
  scalar/loop references remain;
- no `analysis.deterministic_result` or `_deterministic_result.*`
  references remain;
- no `analysis.fitting.minimizer*` or `show_fitting_mode_types` calls
  remain;
- `Analysis.fitting` Python attribute and `self._fitting` are gone;
- the seven Bayesian category packages, the `deterministic_result`
  package, and the `fitting` category package are deleted.

The engine module `analysis/fitting.py` (`Fitter`) is kept, as recorded
in §"Decisions added after Review 4". The five amended ADRs and the
superseded suggestion ADR are updated. The PR description in the plan
matches the user-facing surface.

The risks below are not blockers for Phase 1 review but should be
acknowledged before Phase 2 begins.

## Findings

### F1 — LSQ concrete classes have eight identical `__init__` bodies

ADR §8 and Plan §"Decisions added after Review 2" framed the per-class
descriptor declarations as "intentional duplication" so each class
could carry backend-specific defaults. In the implementation, none of
the eight LSQ classes diverges from the others except in `type_info`
and module docstrings.

Confirmed with:

```text
diff src/easydiffraction/analysis/categories/minimizer/lmfit.py \
     src/easydiffraction/analysis/categories/minimizer/lmfit_leastsq.py
diff src/easydiffraction/analysis/categories/minimizer/lmfit.py \
     src/easydiffraction/analysis/categories/minimizer/dfols.py
diff src/easydiffraction/analysis/categories/minimizer/lmfit.py \
     src/easydiffraction/analysis/categories/minimizer/bumps.py
```

All produce only `type_info` and docstring diffs. The `DEFAULT_*`
constants are identical across files; the descriptor list is identical
across files; the `__init__` bodies are line-for-line equal. About 60
lines × 8 files = ~480 lines of duplicated descriptor setup.

This is a structural maintenance hazard rather than a correctness
issue: every future addition to the LSQ result set must land in eight
places, and accidental divergence between files will be hard to spot
in review. The `_expected_descriptor_names` tuple in
`LeastSquaresMinimizerBase` is the only place that can catch the
"forgot to add it in class N" failure mode, and it is asserted only at
test time via the P1.4 coverage check.

Suggested follow-up (not a Phase 1 blocker):

- If concrete LSQ classes genuinely will diverge in defaults, leave
  the duplication and add a Phase 2 unit test that compares the
  declared descriptor set against `_expected_descriptor_names` for
  every concrete class.
- If they will not diverge, fold the LSQ result descriptors into a
  single `LeastSquaresMinimizerBase.__init__` body and document the
  ADR §8 exception. The base already owns all matching properties and
  `_set_*` helpers, so this is a smaller change than the structural
  decision implies. Capture the exception in the ADR if taken.

### F2 — Descriptors live in `__init__`, not in the class body

Plan P1.4 says: "Every concrete class declares every one of its
descriptors in its own class body with backend-specific defaults per
ADR §5 / §8 (no `__init__` mutation of parent declarations)."

The implementation declares descriptors in `__init__` by calling base-
class `@staticmethod`/`@classmethod` factory helpers
(`_max_iterations_descriptor`, `_sampling_steps_descriptor`, …) and
assigning the result to `self._<name>`. The base also owns all
matching `@property` accessors and `_set_*` setters
(`LeastSquaresMinimizerBase` lines 123–260; `BayesianMinimizerBase`
lines 231–378).

This is functionally equivalent to class-body declarations — each
instance still owns its descriptors, and per-class defaults are passed
through the helper arguments — but it deviates from the plan's literal
"no `__init__` mutation of parent declarations" wording, and it brings
substantial behavior onto the bases (property + setter pairs for every
shared name), which the same plan section described as "behavior-only
helpers… no descriptor instances on the base." The bases now expose
the descriptor *interface* even though they do not hold the descriptor
*instances*.

Two consequences worth noting:

- Hovering on `BumpsDreamMinimizer.sampling_steps` (etc.) lands in
  `bayesian_base.py`, not in `bumps_dream.py`. Class-body declarations
  would put the docstring next to the default.
- A subclass that forgets to set `self._sampling_steps` in `__init__`
  fails only at the first `getattr` call, not at class definition.
  Class-body declarations would surface this at instantiation through
  the descriptor machinery.

Suggested follow-up: either (a) accept the present pattern and reword
the plan's "class body" language so the next reviewer is not misled,
or (b) move the descriptor declarations to class body and keep only
genuinely behavior-only helpers on the base. Either path is fine; the
current state of "documented one way, implemented another" is the
risk.

### F3 — Swap warning compares current values, not defaults

ADR §8 wording: "A `log.warn(...)` lists fields whose default values
differ between old and new classes."

`Analysis._changed_minimizer_defaults` (analysis.py:1062–1077)
compares the *current* values on the in-flight minimizer instance to
the *defaults* on a freshly constructed instance of the target class.
For a user who set `analysis.minimizer.sampling_steps = 8000` and then
switches `minimizer_type`, the warning fires for `sampling_steps`
because `8000 != <new class default>`, not because the two classes
disagree about a default.

Two practical effects:

- The warning is more aggressive than the ADR text promises. It will
  consistently fire for any session that customised the active
  minimizer before switching, which is the common case.
- The warning text reads `'sampling_steps 8000->3000'` and is prefixed
  with `'Switching minimizer type resets defaults: …'`. The "resets
  defaults" framing is misleading: the user customised the value
  rather than took a default, and the value is being reset because
  the category instance is replaced, not because the *defaults*
  differ between classes.

This is also slightly different from the `background_type` precedent
mentioned in the ADR — `background_type` carries only inputs, so the
distinction did not surface there. Here `minimizer` mixes inputs and
fit outputs (see also F4), so the swap warning is louder for the
output fields too, which are always at default before a fit.

Suggested follow-up: either tighten the implementation to compare
defaults-to-defaults across classes (matching the ADR) and add a
separate "lost-customisation" warning, or update the ADR to describe
the current behavior and reword the user message to "Switching
minimizer type resets these values:" without "defaults". Tracking the
change in `docs/dev/issues/open.md` is fine if the choice is deferred.

### F4 — `_clear_minimizer_result_projection` walks a hard-coded list

`Analysis._clear_minimizer_result_projection` (analysis.py:1178–1183)
resets a fixed set of result descriptors named in the module-level
`_MINIMIZER_RESULT_DEFAULTS` dict (analysis.py:59–82). The default
values are duplicated here, separate from the per-class descriptor
declarations.

If a new concrete minimizer adds a result descriptor (e.g. an emcee-
only output added in Plan 2) the developer must remember to extend
`_MINIMIZER_RESULT_DEFAULTS`. Forgetting leaves the new field carrying
state from the previous fit. This is the kind of silent staleness the
ADR §4 lifecycle rule explicitly tries to prevent.

Suggested follow-up: derive the reset set from the active minimizer's
own descriptor declarations rather than a module-level dict — e.g.
each minimizer class exposes a `_result_descriptor_names` tuple, and
the analysis loop reads `AttributeSpec.default` to obtain the value.
Defer to Plan 2 if not urgent, but please record the constraint in
that plan's P1 step list so emcee inherits the rule.

### F5 — `analysis_to_cif` fallback ordering swaps `minimizer` and `aliases`

`io/cif/serialize.py:436–453` (`analysis_to_cif`) builds a fallback
section list `[minimizer, aliases, constraints, …]` when
`category_owner_to_cif(analysis)` returns an empty body. The
`_serializable_categories` source-of-truth path
(`analysis.py:818–837`) emits `[minimizer, aliases, constraints, …]`.

This is consistent in the present code path. However, the fallback
branch is only reachable if `category_owner_to_cif` returns empty,
which happens when `_serializable_categories` returns an empty list —
and `_serializable_categories` never returns empty here because
`self.minimizer` is always present. The fallback is therefore dead
code. Either remove it or document why it exists, otherwise the next
reader will assume there is a code path that relies on it and will
guard a future refactor against a non-existent invariant.

### F6 — `init` string round-trip relies on engine accepting raw `'lhs'`

`BayesianMinimizerBase._native_kwargs` maps the persisted
`initialization_method = 'latin_hypercube'` to a native string
`'lhs'` and returns it under the key `init`. The DREAM engine accepts
the string via
`DreamPopulationInitializationEnum(value)`
(`analysis/minimizers/bumps_dream.py:556`), so this works.

The mapping table is defined twice in the new layout:

- `BayesianMinimizerBase._native_initialization_methods`:
  `LATIN_HYPERCUBE → 'lhs'` (category layer).
- `DreamPopulationInitializationEnum.LHS = 'lhs'` (engine layer).

The legacy enum also still carries `EPS`, `COV`, `RANDOM`. These
remain reachable through direct engine API
(`bumps_dream.minimizer.init = DreamPopulationInitializationEnum.COV`)
but are no longer expressible from the persisted category
(`_supported_initialization_methods = (LATIN_HYPERCUBE,)`). That gap
will surface as soon as Plan 2 adds emcee's `'ball' / 'uniform' /
'prior'` and someone asks why DREAM cannot use `'random'` from CIF.

Suggested follow-up: decide whether the DREAM engine should expose
the same closed set as the persisted category (matching ADR §6's
"single unified enum") or whether the engine's broader set is
deliberate. The current intermediate state is fine for Phase 1 review
but should be resolved before Plan 2 lands the second sampler.

### F7 — Dead code: `_restore_deterministic_fit_state`, `_sync_live_minimizer_from_persisted_fit_state`

Two helpers exist only to preserve historical symmetry:

- `io/cif/serialize.py:614–616` `_restore_deterministic_fit_state`
  body is `del analysis, block`. The function is called from
  `_restore_persisted_fit_state` but does nothing.
- `analysis/analysis.py:547–549`
  `_sync_live_minimizer_from_persisted_fit_state` body is a one-line
  docstring; the function is called from `_prepare_fit_run` and
  `_restore_bayesian_fit_state`.

Per `.github/copilot-instructions.md` → **Change Discipline** "No
defensive checks for unlikely edge cases" and "Don't add features or
refactor unless asked", these are not blockers. But they are
genuinely dead code now that the persisted Bayesian sampler snapshot
lives on the minimizer category itself. Either remove them or add a
one-line comment explaining why they remain as no-ops. Either is
cheap to do during Phase 2 cleanup.

### F8 — `core/variable.py` now imports an analysis-adjacent type

`core/variable.py:12` imports `PosteriorParameterSummary` from
`core.posterior`. The relocation in P1.1a deliberately moved the
class to `core/` so this import is legal per
`.github/copilot-instructions.md` → **Architecture** ("Keep `core/`
free of domain logic"). The relocated dataclass is value-only
(primitives + tuples), so the spirit of the rule is preserved.

This is fine as-is. Recording it here so reviewers do not flag it on
first read. If a future change adds Bayesian-specific behavior to
`PosteriorParameterSummary`, that behavior must stay outside `core/`.

### F9 — `_native_kwargs` silently drops unsupported engine attributes

`Analysis._sync_engine_from_minimizer_category`
(`analysis.py:1102–1108`) skips `setattr(engine, key, value)` when
`hasattr(engine, key)` is false. This makes the LSQ category's
`max_iterations` / `convergence_tolerance` settings a no-op for
engines that do not expose those attributes (e.g. BUMPS differential
evolution / amoeba may not honour them). The user sees the field in
`help()` and CIF, sets it, and observes no effect.

This is the same shape as the `init` issue in F6: the persisted
category advertises a setting that the engine quietly ignores. The
project's stated audience ("scientists, often non-programmers:
prioritize discoverability, clear errors") makes a silent drop the
worst available behavior.

Suggested follow-up: either narrow the category's declared
descriptors per concrete class (so `BumpsDeMinimizer` does not expose
`max_iterations` if BUMPS-DE ignores it), or make
`_sync_engine_from_minimizer_category` raise / `log.warn(...)` when a
declared category attribute is not consumed by the engine. Both paths
keep the closed-set guarantee the ADR promises.

### F10 — Tests still call removed API, intentionally deferred

`tests/` contains ~28 hits across integration, unit, and functional
suites referencing `analysis.fitting.minimizer_type`,
`analysis.fitting.minimizer`, `show_minimizer_types()`, and
`show_fitting_mode_types()`. This is expected per Plan §"Phase 1
review gate" (the `tests/` migration is P2.1a). Recording it here so
the reviewer does not mistake it for a missing P1.13 step.

The migration list in P2.1a covers every file I could find with a
`git grep` on those patterns; no extra test files appear stranded.

## Documentation

- All five "ADRs amended by this ADR" in the consolidated ADR are
  present in their updated form: `analysis-cif-fit-state.md`,
  `fit-mode-categories.md`, `selector-families.md`,
  `runtime-fit-results.md`, `switchable-category-api.md`.
- `parameter-posterior-summary.md` carries the "Superseded by" header
  and cross-links the new ADR.
- `adrs/index.md` lists the new ADR under "Accepted" and the
  parameter-posterior suggestion under "Superseded".
- `docs/dev/issues/{open,closed}.md` do not appear to need an entry
  (no pre-existing issue tracked this work); skipping the bullet in
  P1.14 is fine.

## Verification commands run for this review

```text
git grep -nE 'analysis\.bayesian_|categories\.bayesian_|_bayesian_(sampler|result|convergence|parameter_posterior|distribution_cache|pair_cache|predictive_dataset)' src/ docs/docs/tutorials/
git grep -nE 'analysis\.deterministic_result|_deterministic_result\.' src/ docs/docs/tutorials/
git grep -nP '\banalysis\.fitting\.(minimizer|show_minimizer_types|minimizer_type)\b|\bproject\.analysis\.fitting\b' src/ docs/docs/tutorials/
git grep -nE 'show_minimizer_types|show_fitting_mode_types' src/ docs/docs/tutorials/
git grep -nP '\bself\.fitting\b|\bself\._fitting\b|\bself\.bayesian_(sampler|result|convergence|parameter_posteriors|distribution_caches|pair_caches|predictive_datasets)\b|\bself\.deterministic_result\b|\bself\._deterministic_result\b' src/easydiffraction/analysis/analysis.py
```

All five return empty against the Phase 1 scopes, matching P1.15.

No tests, lint, or type checks were run; this is a static review.

## Recommended next steps

1. Decide on F1 (collapse vs. enforce) and F2 (class body vs. helper
   factories) before Phase 2 starts, so the Phase 2 emcee work in
   `docs/dev/plans/emcee-minimizer.md` extends one consistent
   pattern.
2. Track F3, F4, F6, F9 in `docs/dev/issues/open.md` if they will not
   be addressed in Plan 2; otherwise reference them from the emcee
   plan.
3. F5, F7 are cosmetic and can be picked up during Phase 2 cleanup
   alongside the `pixi run fix` / `pixi run check` pass in P2.2.
4. F8, F10 are informational only.

## Resolution

- **F1, F2:** addressed by folding identical LSQ descriptor setup into
  `LeastSquaresMinimizerBase` and updating the ADR/plan language to
  describe the accepted helper-construction pattern.
- **F3:** addressed by comparing default-to-default setting values and
  changing the warning text to "uses different defaults".
- **F4:** addressed by adding per-family `_result_descriptor_names` and
  resetting result descriptors from their own `AttributeSpec` defaults.
- **F5:** addressed by removing the unreachable `analysis_to_cif`
  fallback branch.
- **F6:** deferred explicitly to the emcee plan's P1.3 setup step,
  where the DREAM direct-engine initialization enum must be resolved
  before adding a second Bayesian sampler.
- **F7:** addressed by deleting the no-op deterministic/Bayesian
  restore helpers and the live-minimizer sync call.
- **F8:** informational; no code change.
- **F9:** addressed by warning when a native minimizer category setting
  is not supported by the live engine, and by pruning unsupported LSQ
  settings in the descriptor-scope cleanup.
- **F10:** intentionally remains in Phase 2 test migration scope.
