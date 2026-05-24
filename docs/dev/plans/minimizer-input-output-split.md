# Plan: Minimizer Input/Output Split

> This plan follows
> [`.github/copilot-instructions.md`](../../../.github/copilot-instructions.md).
> No deliberate exceptions.

## ADR

Implements
[`docs/dev/adrs/suggestions/minimizer-input-output-split.md`](../adrs/suggestions/minimizer-input-output-split.md).
This plan promotes that ADR from Suggestion → Accepted during
implementation (step P1.16).

Affected ADRs that this plan amends (per the ADR's §"ADRs amended"):

- [`accepted/minimizer-category-consolidation.md`](../adrs/accepted/minimizer-category-consolidation.md)
  — §1 becomes a partial rule; §"Alternatives Considered → D" records
  the reversal.
- [`accepted/analysis-cif-fit-state.md`](../adrs/accepted/analysis-cif-fit-state.md)
  — §"Minimizer fit projection" rewritten for the settings-only
  `_minimizer.*` / outputs-on-`_fit_result.*` shape.
- [`accepted/runtime-fit-results.md`](../adrs/accepted/runtime-fit-results.md)
  — closing paragraph references this ADR alongside the existing two.
- [`accepted/switchable-category-owned-selectors.md`](../adrs/accepted/switchable-category-owned-selectors.md)
  — §1 gains the documented "fully-determined paired category"
  exception.
- [`accepted/display-ux.md`](../adrs/accepted/display-ux.md) —
  `project.display.fit.results()` prints a "Settings used" block.

## Branch and PR

- Branch: `minimizer-input-output-split` (continued from the branch
  the ADR was drafted on). Do not push unless asked.
- Each step in §"Implementation steps (Phase 1)" must be staged with
  explicit paths and committed locally **before** moving to the next
  step. See `.github/copilot-instructions.md` → **Commits**.
- After P1.17, stop and wait for the user review gate before starting
  Phase 2.

## Decisions already made (from the ADR)

1. `analysis.minimizer` holds **writable user settings only**.
2. `analysis.fit_result` becomes a class hierarchy paired with
   `analysis.minimizer`. `FitResultBase` carries common fields;
   `LeastSquaresFitResult` and `BayesianFitResult` add family-specific
   ones.
3. `fit_result` is **not a user-facing switchable category**. No
   `fit_result.type`, no `fit_result.show_supported()`. The owner's
   `_swap_minimizer` hook installs both the minimizer and the paired
   `fit_result` atomically.
4. Pairing rule is encoded on the minimizer base classes:
   `LeastSquaresMinimizerBase._fit_result_class = LeastSquaresFitResult`,
   `BayesianMinimizerBase._fit_result_class = BayesianFitResult`.
5. `objective_value` (raw χ²) and `reduced_chi_square` are distinct
   fields, both kept on `LeastSquaresFitResult`.
6. `credible_interval_inner` / `credible_interval_outer` stay on the
   output side (`BayesianFitResult`) at the fixed `0.68` / `0.95`
   values. User-configurable levels deferred to a follow-on ADR.
7. The display extension lives under
   `project.display.fit.results()`; no new `Analysis`-level display
   method is added.
8. Beta posture: hard cutover, no shims, no deprecation warnings.
   Tutorials and saved fixtures regenerate.

## Open questions

- **Existing `analysis.fit_result.from_cif` parameter ordering.**
  After this split, the CIF restore for `_fit_result.*` must run
  **after** `_minimizer.*` is read so the paired class is known
  before the result descriptors load. The current `_restore_*` order
  in [`serialize.py`](../../../src/easydiffraction/io/cif/serialize.py)
  reads `_minimizer.*` first via `_swap_minimizer`, then iterates the
  rest. P1.6 must ensure `_fit_result` is included in the iteration
  only after the swap has installed the paired class. Confirm during
  P1.6 implementation.
- **Posterior-summary code path that currently writes
  `_set_credible_interval_*` on `minimizer`.** After P1.11, the
  setters move to `BayesianFitResult`. The
  `_store_posterior_fit_projection` method in
  [`analysis.py`](../../../src/easydiffraction/analysis/analysis.py)
  must be updated to call
  `self._fit_result._set_credible_interval_inner(...)` instead of
  `self.minimizer._set_*`. Verify the order of operations against the
  test in
  [`test_results_sidecar.py`](../../../tests/unit/easydiffraction/io/test_results_sidecar.py).

## Concrete files likely to change

### Created

- `src/easydiffraction/analysis/categories/fit_result/base.py` —
  rename existing `FitResult` class to `FitResultBase` (or extract a
  base). Common output descriptors live here.
- `src/easydiffraction/analysis/categories/fit_result/lsq.py` —
  `LeastSquaresFitResult` with LSQ-specific output descriptors.
- `src/easydiffraction/analysis/categories/fit_result/bayesian.py` —
  `BayesianFitResult` with Bayesian-specific output descriptors,
  including `credible_interval_inner` / `credible_interval_outer`.
- *(`src/easydiffraction/analysis/categories/fit_result/factory.py`
  already exists; this plan extends it rather than creating it. See
  P1.4 — the factory becomes a registration helper for the two new
  family classes; the authoritative swap mechanism is the
  `_fit_result_class` attribute on the paired minimizer base, not a
  factory lookup. The factory is still useful for introspection /
  testing.)*
- `tests/unit/easydiffraction/analysis/categories/fit_result/test_base.py`
- `tests/unit/easydiffraction/analysis/categories/fit_result/test_lsq.py`
- `tests/unit/easydiffraction/analysis/categories/fit_result/test_bayesian.py`
- `tests/unit/easydiffraction/analysis/categories/fit_result/test_factory.py`

### Modified

- `src/easydiffraction/analysis/categories/fit_result/__init__.py`
  — add explicit imports for every new concrete class to trigger
  factory registration.
- `src/easydiffraction/analysis/categories/fit_result/default.py`
  — rewritten to import from the new family modules; the existing
  `FitResult` is renamed to `FitResultBase` and absorbed.
- `src/easydiffraction/analysis/categories/minimizer/base.py` — add
  `_fit_result_class: ClassVar[type]` declaration.
- `src/easydiffraction/analysis/categories/minimizer/lsq_base.py`
  — set `_fit_result_class = LeastSquaresFitResult`; **remove**
  `objective_name`, `objective_value`, `n_data_points`, `n_parameters`,
  `n_free_parameters`, `degrees_of_freedom`, `covariance_available`,
  `correlation_available`, `runtime_seconds`, `iterations_performed`,
  `exit_reason` from descriptor declarations and from
  `_result_descriptor_names`. `_setting_descriptor_names` stays
  `('max_iterations',)`.
- `src/easydiffraction/analysis/categories/minimizer/bayesian_base.py`
  — set `_fit_result_class = BayesianFitResult`; remove
  `runtime_seconds`, `point_estimate_name`, `sampler_completed`,
  `credible_interval_inner`, `credible_interval_outer`,
  `acceptance_rate_mean`, `gelman_rubin_max`,
  `effective_sample_size_min`, `best_log_posterior` from descriptor
  declarations and from `_result_descriptor_names`.
  `_setting_descriptor_names` keeps the seven Bayesian inputs.
- `src/easydiffraction/analysis/analysis.py` — extend
  `_swap_minimizer` to also instantiate the paired `fit_result` via
  the minimizer's `_fit_result_class`; add `analysis.fit_result`
  property; route every `self._minimizer._set_*` result-writer call
  in `_store_least_squares_result_projection` /
  `_store_posterior_fit_projection` /
  `_restore_fit_results_from_projection` to
  `self._fit_result._set_*` instead.
- `src/easydiffraction/io/cif/serialize.py` — emit/read
  `_fit_result.*` from the paired class; remove the removed
  `_minimizer.*` output tags from the serialise/deserialise paths.
  Update the legacy-tag rejection message.
- `src/easydiffraction/project/display.py` — extend
  `project.display.fit.results()` to print a "Settings used" block
  populated from `analysis.minimizer.*` above the existing result
  tables.
- All tutorials referencing `analysis.minimizer.<output_field>`
  (e.g. `runtime_seconds`, `gelman_rubin_max`, `objective_value`) →
  `analysis.fit_result.<output_field>`. List enumerated at P1.15
  start via `git grep`.
- Tests reading `analysis.minimizer.<output_field>` → migrate to
  `analysis.fit_result.<output_field>`. P2.1 enumerates.

### Deleted

- None. The existing `fit_result/default.py` is rewritten in place;
  the existing `FitResult` class becomes `FitResultBase`.

## Implementation steps (Phase 1)

Mark `[x]` as each step lands.

- [x] **P1.1 — Rename `FitResult` to `FitResultBase`; add reset
      hooks; update every import site.** In
      `src/easydiffraction/analysis/categories/fit_result/default.py`,
      rename the class. The factory `@register` decorator stays on
      the renamed class so the default-tag lookup keeps working until
      P1.4 extends the factory.

      Add two class-level hooks to `FitResultBase` matching the
      `MinimizerCategoryBase` shape introduced by the consolidation
      work
      ([`minimizer/base.py:69-74`](../../../src/easydiffraction/analysis/categories/minimizer/base.py)):

      ```python
      _result_descriptor_names: ClassVar[tuple[str, ...]] = (
          'success', 'message', 'iterations',
          'fitting_time', 'reduced_chi_square', 'result_kind',
      )

      def _reset_result_descriptors(self) -> None:
          """Reset fit-result descriptors to declared defaults."""
          for name in self._result_descriptor_names:
              descriptor = getattr(self, name)
              if isinstance(descriptor, GenericDescriptorBase):
                  descriptor.value = descriptor._value_spec.default_value()
      ```

      `LeastSquaresFitResult` (P1.2) and `BayesianFitResult` (P1.3)
      then add their own field names to `_result_descriptor_names`
      so the inherited helper resets every relevant descriptor.

      This must land in P1.1 because P1.6 retargets
      `_clear_minimizer_result_projection` (renamed
      `_clear_fit_result_projection`) to call
      `self.fit_result._reset_result_descriptors()`, and that method
      must exist on `FitResultBase` before the swap is wired.

      Update every package-level import that referenced the old
      name. `git grep -nP '\bFitResult\b' src/ tests/` lists the
      sites at plan time:

      - `src/easydiffraction/analysis/__init__.py` (line 14 today)
      - `src/easydiffraction/analysis/categories/__init__.py`
        (line 14 today)
      - `src/easydiffraction/analysis/categories/fit_result/__init__.py`
      - `src/easydiffraction/analysis/analysis.py` (import line 18;
        type annotation on the `fit_result` property at line 432;
        `self._fit_result = FitResult()` at line 483; same
        construction at line 1208)

      All four `FitResult` import/annotation/construction sites in
      `analysis.py` become `FitResultBase` after this step. The two
      `self._fit_result = FitResult()` construction sites (init and
      `_clear_persisted_fit_state`) become
      `FitResultBase()` temporarily; P1.6 retargets them to the
      paired class.

      Re-run `git grep -nP '\bFitResult\b' src/` at the end of this
      step — every remaining hit must be the renamed class name or a
      module path, not the old bare class. Tests are migrated by
      P2.1.

      Commit: `Rename FitResult to FitResultBase, add reset hooks`

- [x] **P1.2 — Add `LeastSquaresFitResult` class.** New file
      `src/easydiffraction/analysis/categories/fit_result/lsq.py`.
      `LeastSquaresFitResult(FitResultBase)` declares: `objective_name`,
      `objective_value`, `n_data_points`, `n_parameters`,
      `n_free_parameters`, `degrees_of_freedom`,
      `covariance_available`, `correlation_available`, `exit_reason`.
      **All defaults are `None` with `allow_none=True`**, matching the
      consolidation cleanup that previously moved LSQ outputs off `0` /
      `false` / `''` so a pre-fit CIF emits `?` rather than a value
      that looks like a degenerate result. This applies to numeric,
      integer-like, string, and bool fields alike; the descriptor
      helpers in `LeastSquaresMinimizerBase`
      ([`lsq_base.py`](../../../src/easydiffraction/analysis/categories/minimizer/lsq_base.py))
      that currently produce these descriptors are the model — they
      can be lifted into `LeastSquaresFitResult` verbatim before being
      removed from `lsq_base.py` at P1.9. Declare
      `_expected_descriptor_names`, `_result_descriptor_names` for
      parity with the minimizer hierarchy. Tests deferred to Phase 2.
      Commit: `Add LeastSquaresFitResult class`

- [ ] **P1.3 — Add `BayesianFitResult` class.** New file
      `src/easydiffraction/analysis/categories/fit_result/bayesian.py`.
      `BayesianFitResult(FitResultBase)` declares:
      `point_estimate_name`, `sampler_completed`,
      `credible_interval_inner` (default `0.68`),
      `credible_interval_outer` (default `0.95`),
      `acceptance_rate_mean`, `gelman_rubin_max`,
      `effective_sample_size_min`, `best_log_posterior`. Declare
      `_expected_descriptor_names`, `_result_descriptor_names`.
      Tests deferred to Phase 2. Commit:
      `Add BayesianFitResult class`

- [ ] **P1.4 — Register fit-result classes with the existing
      `FitResultFactory`.** The factory already exists at
      [`src/easydiffraction/analysis/categories/fit_result/factory.py`](../../../src/easydiffraction/analysis/categories/fit_result/factory.py)
      and currently registers only the default common class. Update
      it to also register `LeastSquaresFitResult` and
      `BayesianFitResult` with their family tags. Update
      `src/easydiffraction/analysis/categories/fit_result/__init__.py`
      to explicitly import every concrete class (so registration
      fires on package import, per the repo's standard pattern).

      **Authoritative mechanism:** `Analysis._swap_minimizer`
      constructs the paired fit-result via the minimizer's
      `_fit_result_class` attribute (P1.5), not via a factory
      lookup. The factory is kept as a registration helper for
      introspection and testing; do not add a public selector surface
      (`type`, `show_supported`) since `fit_result` is internally
      paired, per ADR §1. Commit:
      `Register fit-result family classes with factory`

- [ ] **P1.5 — Declare `_fit_result_class` on minimizer bases.** In
      `src/easydiffraction/analysis/categories/minimizer/lsq_base.py`,
      add `_fit_result_class: ClassVar[type] = LeastSquaresFitResult`.
      In
      `src/easydiffraction/analysis/categories/minimizer/bayesian_base.py`,
      add `_fit_result_class: ClassVar[type] = BayesianFitResult`. Add
      the matching declaration to
      `src/easydiffraction/analysis/categories/minimizer/base.py` with
      `_fit_result_class: ClassVar[type] = FitResultBase` as a safety
      fallback (no concrete minimizer instantiates the bare base, but
      `_swap_minimizer` reads through this attribute). Commit:
      `Declare paired _fit_result_class on minimizer bases`

- [ ] **P1.6 — Wire `Analysis._swap_minimizer` to install both
      instances, and update every `_fit_result` reset path.** In
      `src/easydiffraction/analysis/analysis.py`:

  - `__init__` constructs the initial `_fit_result` from the default
    minimizer's `_fit_result_class`:
    `self._fit_result = self._minimizer._fit_result_class()`. The
    line 483 `self._fit_result = FitResultBase()` (after P1.1) is
    replaced.
  - `_replace_minimizer` constructs `self._fit_result =
    new_minimizer._fit_result_class()` after the new minimizer is
    created. The old `fit_result` is detached (`_parent = None`)
    before being replaced.
  - `_clear_persisted_fit_state` (line 1204 today) currently calls
    `self._clear_minimizer_result_projection()` and then
    `self._fit_result = FitResult()`. After P1.1 + the split, both
    lines must change:
    - `self._fit_result = self.minimizer._fit_result_class()`
      replaces the bare `FitResultBase()` construction. This keeps
      the paired class invariant whenever the persisted state is
      reset.
    - `self._clear_minimizer_result_projection()` currently calls
      `self.minimizer._reset_result_descriptors()`. After P1.9/P1.10
      remove the result descriptors from the minimizer, this method
      becomes a no-op. **Retarget it to
      `self.fit_result._reset_result_descriptors()`** and rename it
      to `_clear_fit_result_projection`. Update the call sites
      (line 1204; potentially others — `git grep` confirms).
  - Add `analysis.fit_result` read-only property
    (`return self._fit_result`). Type annotation:
    `FitResultBase` (the family classes inherit from it).
  - Wire `self._fit_result._parent = self` in
    `_attach_category_parents`. Every `_fit_result` reassignment in
    the methods above must also set `_parent` on the new instance.

  Verification at the end of this step:

  ```
  git grep -nE 'self\._fit_result\s*=' src/easydiffraction/analysis/analysis.py
  ```

  Every match must construct via `self.minimizer._fit_result_class()`
  (or `new_minimizer._fit_result_class()` in `_replace_minimizer`),
  not a bare class name. There must be no remaining
  `self._fit_result = FitResultBase()` after this step.

  Commit: `Wire fit_result swap and reset paths to paired class`

- [ ] **P1.7 — Route LSQ result writers to `fit_result`.** In
      `src/easydiffraction/analysis/analysis.py`,
      `_store_least_squares_result_projection` currently writes to
      `self.minimizer._set_objective_name(...)` etc. Reroute every
      such call to `self.fit_result._set_*`. Same for
      `_restore_fit_results_from_projection`'s LSQ branch
      (it reads `self.minimizer.objective_name.value` etc. — change
      to `self.fit_result.<name>.value`). Commit:
      `Route LSQ result writers to fit_result`

- [ ] **P1.8 — Route Bayesian result writers to `fit_result`.** Same
      treatment for `_store_posterior_fit_projection` and the
      Bayesian branch of `_restore_fit_results_from_projection`.
      Includes the `_set_credible_interval_*` calls — they now target
      `self.fit_result._set_credible_interval_*`. Commit:
      `Route Bayesian result writers to fit_result`

- [ ] **P1.9 — Remove output fields from LSQ minimizer base.** In
      `src/easydiffraction/analysis/categories/minimizer/lsq_base.py`,
      delete the descriptor declarations and properties for
      `objective_name`, `objective_value`, `n_data_points`,
      `n_parameters`, `n_free_parameters`, `degrees_of_freedom`,
      `covariance_available`, `correlation_available`,
      `runtime_seconds`, `iterations_performed`, `exit_reason`. Remove
      these names from `_expected_descriptor_names` and
      `_result_descriptor_names`. `_setting_descriptor_names` stays
      `('max_iterations',)`. After this step,
      `_result_descriptor_names` on `LeastSquaresMinimizerBase` is
      `()` and `_reset_result_descriptors()` is a no-op on every LSQ
      minimizer — confirming the P1.6 retarget of
      `_clear_minimizer_result_projection` to operate on
      `self.fit_result` is the correct call site.

      Note: `optimizer_name` and `method_name` were already removed
      by the consolidation work (`_engine_metadata` dict replaces
      them); this step is the bulk removal of the remaining LSQ
      outputs.

      Commit: `Remove LSQ output descriptors from minimizer base`

- [ ] **P1.10 — Remove duplicate fields from Bayesian minimizer
      base.** In
      `src/easydiffraction/analysis/categories/minimizer/bayesian_base.py`,
      delete the descriptor declarations and properties for
      `runtime_seconds`, `point_estimate_name`, `sampler_completed`,
      `credible_interval_inner`, `credible_interval_outer`,
      `acceptance_rate_mean`, `gelman_rubin_max`,
      `effective_sample_size_min`, `best_log_posterior`. Remove these
      names from `_expected_descriptor_names` and
      `_result_descriptor_names`. The `_setting_descriptor_names`
      tuple keeps the seven Bayesian inputs.

      Commit: `Remove Bayesian output descriptors from minimizer base`

- [ ] **P1.11 — Update CIF emit/read for the split.** In
      `src/easydiffraction/io/cif/serialize.py`:

  **No category-list reordering is performed in this step.** Neither
  `Analysis._serializable_categories()` nor
  `Analysis._fit_state_categories()` is restructured. `fit_result`
  stays conditionally included by `_fit_state_categories()` only
  when `self._has_persisted_fit_state()` is true — exactly as today.
  Pre-fit projects continue to emit no `_fit_result.*` block.

  The only changes in this step are content updates inside the
  existing emit/read flow:

  - `_minimizer.*` emit/read continues to handle settings only (the
    minimizer category's `from_cif` walks its remaining descriptors
    after P1.9 / P1.10 removed the output descriptors).
  - `_fit_result.*` emit/read picks up the new family-specific
    descriptors automatically because P1.6 wires the paired class
    (`LeastSquaresFitResult` or `BayesianFitResult`) onto
    `self._fit_result`. The existing
    `analysis.fit_result.from_cif(block)` call inside
    `_restore_common_fit_state`
    ([`serialize.py:590`](../../../src/easydiffraction/io/cif/serialize.py))
    reads `_fit_result.*` tags into the already-paired class — no
    reordering, no new call.
  - The read-side already restores `minimizer.type` first
    ([`serialize.py:553-555`](../../../src/easydiffraction/io/cif/serialize.py)),
    so the paired-class swap fires before `fit_result.from_cif` runs.
    No code change is required here.
  - Update the legacy-tag rejection message in
    `_raise_for_legacy_analysis_tags` to include the now-removed
    `_minimizer.<output_name>` tags (e.g.
    `_minimizer.runtime_seconds`, `_minimizer.gelman_rubin_max`) as
    legacy markers that should raise a clear error rather than load
    silently.

  Commit: `Serialize fit outputs to _fit_result.* tags`

- [ ] **P1.12 — Confirm `_fit_state_categories` returns the paired
      `fit_result`.** In
      `src/easydiffraction/analysis/analysis.py`,
      `_fit_state_categories()` already returns `[self.fit_parameters,
      self.fit_result, self.fit_parameter_correlations]` when
      persisted fit state exists. After P1.6 wires the paired-class
      construction, `self.fit_result` is automatically the paired
      `LeastSquaresFitResult` / `BayesianFitResult` instance — no
      method body change is needed. The dead branch in
      `_fit_state_categories` (review-9 finding F4, open issue #101)
      can be cleaned up here since this step is already reading the
      function. The plan does not require the cleanup; if taken,
      mention "closes #101" in the commit message.

  Commit: `Confirm fit_result paired instance flows through serializer`

- [ ] **P1.13 — Update `project.display.fit.results()` to add a
      "Settings used" block.** In
      `src/easydiffraction/project/display.py`, extend the existing
      results-display method to print, above the current tables, a
      one-section table titled "Settings used" populated from
      `analysis.minimizer.*`. Use the same `render_table` machinery
      the rest of the display facade uses. Commit:
      `Add settings-used block to fit.results display`

- [ ] **P1.14 — Amend the five accepted ADRs listed in §"ADR".** For
      each, apply the matching paragraph from the ADR's §"ADRs
      amended" section:
  - `minimizer-category-consolidation.md` — §1 partial-rule
    qualification; §"Alternatives Considered → D" reversal record.
  - `analysis-cif-fit-state.md` — §"Minimizer fit projection"
    rewrite.
  - `runtime-fit-results.md` — closing-paragraph reference.
  - `switchable-category-owned-selectors.md` — §1 paired-category
    exception paragraph.
  - `display-ux.md` — `project.display.fit.results()` settings-block
    note.
  - Update `docs/dev/adrs/index.md` to add the new ADR row under
    "Accepted" (per P1.16 promotion).

  Commit: `Amend affected ADRs for minimizer input/output split`

- [ ] **P1.15 — Update tutorials.** `git grep` `docs/docs/tutorials/`
      for `analysis.minimizer.<output_field>` references and rewrite
      each per the migration table below. The two **collapsed** rows
      target existing common fields on `FitResultBase` (already
      written by the existing common projection writer); they are not
      1:1 renames of the old setter/getter name. The other rows are
      moved-but-keep-the-name relocations.

      | Old (removed at P1.9 / P1.10) | New | Notes |
      | --- | --- | --- |
      | `analysis.minimizer.runtime_seconds` | `analysis.fit_result.fitting_time` | Collapsed onto existing common field; setter remains `fit_result._set_fitting_time(...)` (already in `FitResultBase`). |
      | `analysis.minimizer.iterations_performed` | `analysis.fit_result.iterations` | Collapsed onto existing common field; setter remains `fit_result._set_iterations(...)`. |
      | `analysis.minimizer.objective_name` | `analysis.fit_result.objective_name` | Moved to `LeastSquaresFitResult`. |
      | `analysis.minimizer.objective_value` | `analysis.fit_result.objective_value` | Moved to `LeastSquaresFitResult`. |
      | `analysis.minimizer.n_data_points` | `analysis.fit_result.n_data_points` | Moved to `LeastSquaresFitResult`. |
      | `analysis.minimizer.n_parameters` | `analysis.fit_result.n_parameters` | Moved to `LeastSquaresFitResult`. |
      | `analysis.minimizer.n_free_parameters` | `analysis.fit_result.n_free_parameters` | Moved to `LeastSquaresFitResult`. |
      | `analysis.minimizer.degrees_of_freedom` | `analysis.fit_result.degrees_of_freedom` | Moved to `LeastSquaresFitResult`. |
      | `analysis.minimizer.covariance_available` | `analysis.fit_result.covariance_available` | Moved to `LeastSquaresFitResult`. |
      | `analysis.minimizer.correlation_available` | `analysis.fit_result.correlation_available` | Moved to `LeastSquaresFitResult`. |
      | `analysis.minimizer.exit_reason` | `analysis.fit_result.exit_reason` | Moved to `LeastSquaresFitResult`. |
      | `analysis.minimizer.point_estimate_name` | `analysis.fit_result.point_estimate_name` | Moved to `BayesianFitResult`. |
      | `analysis.minimizer.sampler_completed` | `analysis.fit_result.sampler_completed` | Moved to `BayesianFitResult`. |
      | `analysis.minimizer.credible_interval_inner` | `analysis.fit_result.credible_interval_inner` | Moved to `BayesianFitResult`. |
      | `analysis.minimizer.credible_interval_outer` | `analysis.fit_result.credible_interval_outer` | Moved to `BayesianFitResult`. |
      | `analysis.minimizer.acceptance_rate_mean` | `analysis.fit_result.acceptance_rate_mean` | Moved to `BayesianFitResult`. |
      | `analysis.minimizer.gelman_rubin_max` | `analysis.fit_result.gelman_rubin_max` | Moved to `BayesianFitResult`. |
      | `analysis.minimizer.effective_sample_size_min` | `analysis.fit_result.effective_sample_size_min` | Moved to `BayesianFitResult`. |
      | `analysis.minimizer.best_log_posterior` | `analysis.fit_result.best_log_posterior` | Moved to `BayesianFitResult`. |

      Run `pixi run notebook-prepare` to regenerate the `.ipynb`
      files.

      Verification grep (must return empty against
      `docs/docs/tutorials/`):

      ```
      git grep -nE 'analysis\.minimizer\.(runtime_seconds|iterations_performed|objective_value|objective_name|n_data_points|n_parameters|n_free_parameters|degrees_of_freedom|covariance_available|correlation_available|exit_reason|point_estimate_name|sampler_completed|credible_interval_inner|credible_interval_outer|acceptance_rate_mean|gelman_rubin_max|effective_sample_size_min|best_log_posterior)' docs/docs/tutorials/
      ```

      Commit: `Update tutorials to read outputs from fit_result`

- [ ] **P1.16 — Promote ADR + update index.**
  - `git mv docs/dev/adrs/suggestions/minimizer-input-output-split.md
    docs/dev/adrs/accepted/minimizer-input-output-split.md`. Flip the
    Status header to `Accepted`.
  - Move the seven `_reply-N.md` and seven `_review-N.md` siblings:
    keep them next to the ADR if the project convention preserves
    history under `accepted/`; delete them if the convention is to
    drop the deliberation artefacts on promotion (the
    `switchable-category-owned-selectors` precedent deleted them).
    Per the precedent, delete on promotion.
  - Update `docs/dev/adrs/index.md` — move the row for this ADR from
    Suggestion → Accepted.

  Commit: `Promote minimizer-input-output-split ADR`

- [ ] **P1.17 — Phase 1 review gate.** No code change. Re-run the
      P1.15 tutorial grep against `src/`, `docs/docs/tutorials/`, and
      `tests/`. The `src/` and `docs/docs/tutorials/` scopes must
      return empty. The `tests/` sweep is deferred to P2.1, which
      migrates the tests. Then stop and request user review. After
      approval, proceed to Phase 2.

## Verification (Phase 2)

Each command captures its log with a zsh-safe exit-code variable as
required by `.github/copilot-instructions.md` → **Workflow**.

- [ ] **P2.1 — Migrate existing tests off the removed minimizer
      output fields.** `git grep` `tests/` for the same patterns as
      P1.15. Apply the same migration table from P1.15 — including
      the two collapsed rows (`runtime_seconds` → `fitting_time`,
      `iterations_performed` → `iterations`) where the setter name
      also changes. Examples:

      - Reader rewrite:
        `analysis.minimizer.gelman_rubin_max` →
        `analysis.fit_result.gelman_rubin_max`.
      - Reader rewrite with collapse:
        `analysis.minimizer.runtime_seconds` →
        `analysis.fit_result.fitting_time`.
      - Setter rewrite (moved-but-kept name):
        `analysis.minimizer._set_gelman_rubin_max(...)` →
        `analysis.fit_result._set_gelman_rubin_max(...)`.
      - Setter rewrite (collapsed name):
        `analysis.minimizer._set_runtime_seconds(...)` →
        `analysis.fit_result._set_fitting_time(...)`.

      Layout check:

      ```
      pixi run test-structure-check > /tmp/easydiffraction-test-structure-check.log 2>&1; \
        test_structure_check_exit_code=$?; \
        tail -n 200 /tmp/easydiffraction-test-structure-check.log; \
        exit $test_structure_check_exit_code
      ```

      Final stale-reference grep (all four must return empty):

      ```
      git grep -nE 'analysis\.minimizer\.(runtime_seconds|iterations_performed|objective_value|objective_name|n_data_points|n_parameters|n_free_parameters|degrees_of_freedom|covariance_available|correlation_available|exit_reason|point_estimate_name|sampler_completed|credible_interval_inner|credible_interval_outer|acceptance_rate_mean|gelman_rubin_max|effective_sample_size_min|best_log_posterior)' src/ docs/docs/tutorials/ tests/
      git grep -nE '_minimizer\.(runtime_seconds|iterations_performed|objective_value|point_estimate_name|sampler_completed|credible_interval_inner|credible_interval_outer|acceptance_rate_mean|gelman_rubin_max|effective_sample_size_min|best_log_posterior)' src/ docs/docs/tutorials/ tests/
      ```

- [ ] **P2.2 — Add unit tests for new modules.** New tests under
      `tests/unit/easydiffraction/analysis/categories/fit_result/`:
  - `test_base.py` — `FitResultBase` defaults, `_reset_result_descriptors`.
  - `test_lsq.py` — `LeastSquaresFitResult` defaults; CIF round-trip
    of LSQ outputs.
  - `test_bayesian.py` — `BayesianFitResult` defaults including the
    fixed credible interval levels; CIF round-trip.
  - `test_factory.py` — pairing rule via
    `LeastSquaresMinimizerBase._fit_result_class` and
    `BayesianMinimizerBase._fit_result_class`.

      Layout check:

      ```
      pixi run test-structure-check > /tmp/easydiffraction-test-structure-check.log 2>&1; \
        test_structure_check_exit_code=$?; \
        tail -n 200 /tmp/easydiffraction-test-structure-check.log; \
        exit $test_structure_check_exit_code
      ```

- [ ] **P2.3 — Auto-fixes and static checks.**

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

      Iterate `pixi run check` until clean. Do not raise lint
      thresholds — refactor instead.

- [ ] **P2.4 — Unit tests.**

      ```
      pixi run unit-tests > /tmp/easydiffraction-unit-tests.log 2>&1; \
        unit_tests_exit_code=$?; \
        tail -n 200 /tmp/easydiffraction-unit-tests.log; \
        exit $unit_tests_exit_code
      ```

- [ ] **P2.5 — Integration tests.**

      ```
      pixi run integration-tests > /tmp/easydiffraction-integration-tests.log 2>&1; \
        integration_tests_exit_code=$?; \
        tail -n 200 /tmp/easydiffraction-integration-tests.log; \
        exit $integration_tests_exit_code
      ```

- [ ] **P2.6 — Script tests.**

      ```
      pixi run script-tests > /tmp/easydiffraction-script-tests.log 2>&1; \
        script_tests_exit_code=$?; \
        tail -n 200 /tmp/easydiffraction-script-tests.log; \
        exit $script_tests_exit_code
      ```

      This regenerates `tmp/tutorials/projects/*` fixtures with the
      new CIF layout (`_minimizer.*` settings-only,
      `_fit_result.*` outputs).

## Suggested Pull Request

**Title:** Split minimizer settings from fit-result outputs

**Description (user-facing):**

`analysis.minimizer` now holds only the settings you can change —
`sampling_steps`, `max_iterations`, and the other input knobs. Once a
fit completes, every output the project records (wall time, χ², the
Bayesian diagnostics, the LSQ counters) lives on a paired
`analysis.fit_result`. The pairing happens automatically when you
change minimizer type, so users never see a separate result selector.

`project.display.fit.results()` now prints a "Settings used" block
above the existing result tables, so the settings that produced the
fit and the outputs the fit produced are visible side-by-side without
having to open two namespaces.

The CIF layout follows the same split: `_minimizer.*` holds settings
only, `_fit_result.*` holds outputs. Saved projects from the previous
layout do not load unchanged (the project is in beta; no legacy
shims). Tutorials and saved-fixture regeneration land in this PR.
