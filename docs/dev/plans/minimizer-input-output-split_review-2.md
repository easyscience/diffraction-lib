# Review 2: Minimizer Input/Output Split Plan

## Findings

1. **High — Removed output names are still described as one-to-one
   `fit_result` replacements.** P1.15 and P2.1 say to replace every
   `analysis.minimizer.<output_field>` with
   `analysis.fit_result.<output_field>`, and even give
   `analysis.minimizer._set_runtime_seconds(...)` →
   `analysis.fit_result._set_runtime_seconds(...)` as the fixture
   migration example (`minimizer-input-output-split.md:426-474`). That
   replacement is wrong for the fields the ADR intentionally collapses
   into existing common fit-result names: `runtime_seconds` becomes
   `fit_result.fitting_time`, and `iterations_performed` becomes
   `fit_result.iterations`. The current common category already exposes
   `_set_fitting_time` and `_set_iterations`, not `_set_runtime_seconds`
   / `_set_iterations_performed`
   (`src/easydiffraction/analysis/categories/fit_result/default.py:113-126`).
   If the plan is followed literally, tutorials/tests will be migrated
   to attributes and setters that do not exist after P1.2/P1.3. Please
   add an explicit migration map for renamed outputs, at minimum
   `runtime_seconds` → `fitting_time` and `iterations_performed` →
   `iterations`, and say the existing common projection writer owns
   those values rather than moving the old minimizer
   `_set_runtime_seconds` call verbatim.

2. **High — P1.6 retargets reset calls to a method that no fit-result
   class is told to implement.** P1.6 says
   `_clear_minimizer_result_projection()` should become
   `_clear_fit_result_projection()` and call
   `self.fit_result._reset_result_descriptors()`
   (`minimizer-input-output-split.md:280-294`). Today
   `_reset_result_descriptors()` exists only on `MinimizerCategoryBase`
   (`src/easydiffraction/analysis/categories/minimizer/base.py:69-74`),
   while the current `FitResult` class has no equivalent helper
   (`src/easydiffraction/analysis/categories/fit_result/default.py:20-135`).
   P1.2/P1.3 ask the new family classes to declare
   `_result_descriptor_names`, and P2.2 later mentions testing
   `FitResultBase._reset_result_descriptors`, but no Phase 1
   implementation step actually adds that method before P1.6 starts
   calling it. Add an explicit P1.1/P1.2 instruction to put
   `_result_descriptor_names` and `_reset_result_descriptors()` on
   `FitResultBase` (or a shared helper) before retargeting the clear
   path.

3. **Medium — The CIF ordering steps contradict each other and may
   change pre-fit emission.** P1.11 says `_fit_result.*` order is
   enforced by `Analysis._serializable_categories()` putting
   `self.fit_result` directly after `self.minimizer`
   (`minimizer-input-output-split.md:369-376`), but P1.12 immediately
   says `_serializable_categories` already includes `self.fit_result`
   via `_fit_state_categories`
   (`minimizer-input-output-split.md:386-392`). In current code,
   `fit_result` is appended only when persisted fit state exists
   (`src/easydiffraction/analysis/analysis.py:852-873`, `:1182-1186`),
   and CIF read order is already handled separately by
   `analysis_from_cif`: minimizer type is restored before
   `analysis.fit_result.from_cif(block)` runs
   (`src/easydiffraction/io/cif/serialize.py:552-590`). If an
   implementer follows P1.11 literally by moving `fit_result` directly
   into the main category list after `minimizer`, pre-fit CIFs may start
   emitting default `_fit_result.*` fields. Please make the plan choose
   one contract: keep `fit_result` conditional inside
   `_fit_state_categories` and describe the ordering as "after minimizer
   when persisted", or explicitly require a guarded direct insertion
   that preserves the current no-persisted-fit-state behavior.

## Checks

Skipped by instruction: this is a static plan review only. I did not run
tests, `pixi run fix`, `pixi run check`, or any other build or
verification command.
