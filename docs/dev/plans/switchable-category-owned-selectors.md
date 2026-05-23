# Plan: Switchable Category Owned Selectors

> This plan follows
> [`.github/copilot-instructions.md`](../../../.github/copilot-instructions.md).
> No deliberate exceptions.

## ADR

Implements
[`docs/dev/adrs/accepted/switchable-category-owned-selectors.md`](../adrs/accepted/switchable-category-owned-selectors.md).
This plan promoted that ADR from Suggestion → Accepted during
implementation (step P1.14).

Affected ADRs that this plan amends or supersedes (from the ADR's
§Consequences → "ADRs that need to be updated"):

- [`accepted/switchable-category-api.md`](../adrs/accepted/switchable-category-api.md)
  — rewrite the §Decision to point at the new ADR; contract becomes
  "category exposes `type` and `show_supported()`; owner exposes only
  the category itself".
- [`accepted/selector-families.md`](../adrs/accepted/selector-families.md)
  — adopt the mechanism-vs-surface framing; all three families share
  the writable `category.type` surface, distinguished by what the
  owner's `_swap_<name>` hook does.
- [`accepted/fit-mode-categories.md`](../adrs/accepted/fit-mode-categories.md)
  — strike the "Deferred Work" entry; document the new `FittingMode`
  category for `analysis.fitting_mode.type`.
- [`suggestions/python-cif-category-correspondence.md`](../adrs/suggestions/python-cif-category-correspondence.md)
  — drop the "Owner-level switchable selectors" exception; every row
  uses the `_<cat>.type` form.
- [`accepted/minimizer-category-consolidation.md`](../adrs/accepted/minimizer-category-consolidation.md)
  — append a "Superseded selector layout" note for the
  `_fitting.minimizer_type` → `_minimizer.type` change and the drop
  of `_minimizer.optimizer_name` / `_minimizer.method_name`.
- [`accepted/analysis-cif-fit-state.md`](../adrs/accepted/analysis-cif-fit-state.md)
  — drop the two persisted minimizer-name fields; document the
  class-level `_engine_metadata` dict as the new restore source.
- [`accepted/display-ux.md`](../adrs/accepted/display-ux.md) —
  replace `project.rendering`/`_rendering.*` references with
  `project.chart`+`project.table` and `_chart.*`+`_table.*`.
- [`accepted/category-owner-sections.md`](../adrs/accepted/category-owner-sections.md)
  — update the `ProjectConfig` children: drop `Rendering`; add
  `Chart` and `Table` as siblings.

## Branch and PR

- Branch: stays on `minimizer-category-consolidation` (per user
  direction at plan creation). Do not push unless asked.
- Each step in §"Implementation steps (Phase 1)" must be staged with
  explicit paths and committed locally **before** moving to the next
  step. See `.github/copilot-instructions.md` → **Commits**.
- After P1.15, stop and wait for the user review gate before starting
  Phase 2.

## Decisions already made (from the ADR)

1. Public surface: `category.type` (writable property) and
   `category.show_supported()` only. No owner-level `<cat>_type`
   setter, no owner-level show-methods, no `show_current()` method
   (the active type is marked `*` in `show_supported()` and is
   readable via `.type`).
2. Uniform CIF: every selector persists exactly one identity tag
   `_<cat>.type`. Owner-level selector tags (`_fitting.minimizer_type`,
   `_fitting.mode_type`, `_calculation.calculator_type`) are deleted.
3. Mechanism is hidden behind the swap hook. Family A swaps the
   category instance; Family B rebinds the live engine; Family C
   activates/deactivates sibling categories. The user-facing API is
   identical across families.
4. `SwitchableCategoryBase` is a behavior-only mixin (no descriptor
   instances, no `__init__` work). Multi-inherited next to
   `CategoryItem` or `CategoryCollection` as the substrate requires.
5. `_supported_types(filters)` is abstract on the mixin; each
   concrete base implements one of three shapes (domain factory,
   renderer factory, or plain enum).
6. Peak aliases stay: `peak.type` accepts the alias
   (`'pseudo-voigt'`) and canonicalizes via `_canonicalize()` hook
   before delegating to the swap; CIF persists the canonical tag.
7. `_minimizer.optimizer_name` / `_minimizer.method_name` are
   dropped from CIF; `FitResults.optimizer_name` / `method_name`
   are restored from a `_engine_metadata: ClassVar[dict[str, str]]`
   on each concrete minimizer category class.
8. Three structural changes beyond pure renames (§8 of the ADR):
   - `Rendering` → `Chart` + `Table` sibling categories.
   - `analysis.fitting_mode_type` (bare descriptor) → `FittingMode`
     category with `.type` selector.
   - `Calculation` → `Calculator` (Python class and CIF block both
     rename).
9. Beta posture: hard cutover, no shims, no deprecation warnings.
   Every test, tutorial, and example CIF is migrated in the same PR.

## Open questions

- **Collection generalisation scope.** §4 of the ADR proposes a
  one-time generalisation of `CategoryCollection` to emit a scalar
  descriptor above its loop. The minimum surface is "one scalar
  named `type`"; the maximum is "any descriptor declared at
  collection level". Plan default: the minimum surface (just
  `type`) — if a second use case appears during implementation,
  generalise then. Record any deviation in the implementer's notes.
- **Owner attribute name for the legacy `analysis.fitting`.** The
  consolidation ADR already removed the `Fitting` Python category.
  After this plan, `analysis.fitting_mode` replaces it as the
  Family-C category. The `_fitting.*` CIF block disappears
  entirely; verify with grep at P1.12.

## Concrete files likely to change

### Created

- `src/easydiffraction/core/switchable.py` — the
  `SwitchableCategoryBase` behavior-only mixin.
- `src/easydiffraction/core/posterior.py` — already created in the
  consolidation work; no change.
- `src/easydiffraction/datablocks/experiment/categories/calculator/`
  — new directory holding the renamed `Calculation` → `Calculator`
  category (`__init__.py`, `default.py`, `factory.py`). The old
  `categories/calculation/` directory is deleted.
- `src/easydiffraction/project/categories/chart/` — new directory
  (`__init__.py`, `default.py`, `factory.py`) holding the
  `Chart(CategoryItem, SwitchableCategoryBase)` class.
- `src/easydiffraction/project/categories/table/` — new directory
  symmetric to `chart/`.
- `src/easydiffraction/analysis/categories/fitting_mode/` — new
  directory holding the minimal `FittingMode(CategoryItem,
  SwitchableCategoryBase)` class.

### Deleted

- `src/easydiffraction/datablocks/experiment/categories/calculation/`
  — replaced by `categories/calculator/` (P1.8).
- `src/easydiffraction/project/categories/rendering/` — replaced by
  `categories/chart/` + `categories/table/` (P1.9).
- All owner-level `show_<cat>_types()` methods and `<cat>_type`
  property+setter pairs across `Analysis`, `ExperimentBase` and its
  subclasses, and `Rendering` (P1.12).
- `Analysis._fitting_mode_type` descriptor + the bare
  `fitting_mode_type` getter/setter on `Analysis` (P1.10).

### Modified

- `src/easydiffraction/core/category.py` — extend
  `CategoryCollection` to support a `_type` descriptor at the
  collection level (P1.2).
- `src/easydiffraction/io/cif/serialize.py` — when serializing a
  `CategoryCollection`, emit the collection-level scalar before
  the loop (P1.2).
- `src/easydiffraction/analysis/analysis.py` — add
  `_swap_minimizer`, `_swap_fitting_mode`, `_supported_filters_for`
  methods (P1.3, P1.4, P1.10); remove the `minimizer_type` and
  `fitting_mode_type` properties + setters (P1.12).
- `src/easydiffraction/datablocks/experiment/item/base.py` — add
  `_swap_peak`, `_swap_background`, `_swap_extinction`,
  `_swap_calculator`, `_supported_filters_for` methods (P1.3,
  P1.5-P1.8); remove the `peak_profile_type`, `extinction_type`,
  `calculator_type` properties + setters (P1.12).
- `src/easydiffraction/datablocks/experiment/item/bragg_pd.py` —
  remove the `background_type` property + setter and
  `show_background_types()` method; remove the
  `_set_calculator_type` override (P1.12).
- `src/easydiffraction/project/project.py` — add
  `_swap_chart`, `_swap_table` methods; expose new `chart`,
  `table` properties; remove the `rendering` property + setters
  (P1.9).
- Every concrete switchable-category class:
  - `src/easydiffraction/analysis/categories/minimizer/{base,lsq_base,bayesian_base,...}.py`
    — multi-inherit `SwitchableCategoryBase` on `MinimizerCategoryBase`;
    add `_type` descriptor, `_supported_types()`, `_engine_metadata`
    on each concrete class (P1.4, P1.11).
  - `src/easydiffraction/datablocks/experiment/categories/peak/base.py`
    — multi-inherit; add `_type` descriptor and `_canonicalize()`
    override that delegates to `PeakFactory._canonical_tag_for(...)`
    using the full owner-provided peak profile context
    (`calculator`, `scattering_type`, `beam_mode`, `sample_form`);
    rename CIF tag `_peak.profile_type` → `_peak.type` (P1.5).
  - `src/easydiffraction/datablocks/experiment/categories/background/base.py`
    — multi-inherit; add collection-level `_type` descriptor on the
    `BackgroundBase(CategoryCollection, ...)` (P1.6).
  - `src/easydiffraction/datablocks/experiment/categories/extinction/base.py`
    — multi-inherit; add `_type` descriptor (P1.7).
- `src/easydiffraction/io/cif/serialize.py` — drop owner-level
  `_fitting.minimizer_type`, `_calculation.calculator_type`,
  `_rendering.chart_engine`, `_rendering.table_engine`,
  `_fitting.mode_type` emit/read paths; route every selector
  through its category's `_type` descriptor (P1.4-P1.10).
- All tutorials referencing the renamed selectors:
  `docs/docs/tutorials/ed-*.py` files — list enumerated at
  P1.13 start via grep.
- All ADR amendment files listed in §"ADR" above.

### Add (Phase 2)

- `tests/unit/easydiffraction/core/test_switchable.py` — covers
  the mixin's setter staleness checks, `_canonicalize()` default
  identity, and `show_supported()` rendering with the three
  shapes.
- `tests/unit/easydiffraction/project/categories/chart/`,
  `categories/table/` — mirror the new source tree.
- `tests/unit/easydiffraction/datablocks/experiment/categories/calculator/`
  — mirror.
- `tests/unit/easydiffraction/analysis/categories/fitting_mode/`
  — mirror.

## Implementation steps (Phase 1)

Mark `[x]` as each step lands. Each step is a single atomic commit
with explicit `git add` paths.

- [x] **P1.1 — Add `SwitchableCategoryBase` mixin.** New file
      `src/easydiffraction/core/switchable.py` containing the
      behavior-only mixin sketched in ADR §4: `_parent`
      back-reference, `type` property with setter staleness checks,
      `_canonicalize()` default identity, abstract
      `_supported_types(filters)`, and `show_supported()` renderer.
      No subclassing wired yet. No descriptor instances, no
      `__init__` work; behavior-only.
      Commit: `Add SwitchableCategoryBase behavior-only mixin`

- [x] **P1.2 — Generalise `CategoryCollection` for collection-level
      scalars.** In `src/easydiffraction/core/category.py`, add a
      **separate** collection-scalar access surface — a new
      `CategoryCollection.scalar_descriptors` property (or
      equivalent `_collection_scalars` mapping) that the CIF
      serializer/deserializer consults. **`CategoryCollection.parameters`
      stays unchanged** ("all parameters from all items"), so no
      owner-level parameter scan or loop-column logic sees the
      scalar selector. In
      `src/easydiffraction/io/cif/serialize.py`, extend
      `category_collection_to_cif()` ([line 244](../../../src/easydiffraction/io/cif/serialize.py))
      to emit the scalar from `scalar_descriptors` above the loop,
      and extend the reader ([line 964](../../../src/easydiffraction/io/cif/serialize.py))
      to peek the scalar before iterating items.
      Implementation note: keep the surface to just `type` (one
      scalar per collection) per the Open question.
      Commit: `Support collection-level scalar descriptors`

- [x] **P1.3 — Add owner-side swap-hook scaffolding.** On each of
      `Analysis` (`src/easydiffraction/analysis/analysis.py`),
      `ExperimentBase`
      (`src/easydiffraction/datablocks/experiment/item/base.py`),
      and `Project` (`src/easydiffraction/project/project.py`):
      - Add a `_supported_filters_for(category)` dispatch that
        returns the filter dict per category (empty for owners
        without context filters).
      - Pre-stage stub `_swap_<name>` methods for the categories
        each owner hosts — bodies fill in subsequent steps.
      Owner sets `_parent` on every assigned category at
      construction. No public selector surface changes yet.
      Commit: `Add owner-side switchable hook scaffolding`

- [x] **P1.4 — Wire `analysis.minimizer` to the new mixin.**
      - `MinimizerCategoryBase` multi-inherits
        `SwitchableCategoryBase`; declare `_category_code`,
        `_owner_attr_name = 'minimizer'`,
        `_swap_method_name = '_swap_minimizer'`.
      - Add `_type` `StringDescriptor` with
        `cif_handler=CifHandler(names=['_minimizer.type'])`.
      - Implement `_supported_types(filters)` (Shape 1 — domain
        factory).
      - `Analysis._swap_minimizer(new_type)` performs the existing
        swap logic from the consolidation work, plus
        `old._parent = None`.
      - Add the new `_minimizer.type` CIF emit/read path; remove
        the `_fitting.minimizer_type` path. CIF read peeks
        `_minimizer.type` first, then populates the rest.
      Commit: `Wire analysis.minimizer to category-owned selector`

- [x] **P1.5 — Wire `experiment.peak` to the new mixin.**
      - `PeakBase` multi-inherits the mixin; rename CIF tag
        `_peak.profile_type` → `_peak.type` (renames the descriptor
        from `profile_type` to `type`).
      - Override `_canonicalize(value)` to delegate to
        `PeakFactory._canonical_tag_for(...)` (the existing
        canonicalization API at
        [`peak/factory.py:34`](../../../src/easydiffraction/datablocks/experiment/categories/peak/factory.py)),
        passing the **peak alias context** via
        `self._parent._peak_profile_context()` (which today
        returns `scattering_type` and `beam_mode` per
        [`item/base.py:618`](../../../src/easydiffraction/datablocks/experiment/item/base.py)
        — enough to disambiguate Bragg vs Total and CWL vs TOF for
        alias resolution). Beam-mode alone is insufficient: Bragg
        profiles need `scattering_type` + `beam_mode`; Total
        profiles need `scattering_type` alone. The current
        owner-level setter passes the same two-key context into
        `PeakFactory._canonical_tag_for(...)` at
        [`item/base.py:532`](../../../src/easydiffraction/datablocks/experiment/item/base.py).
      - `_supported_types(filters)` (Shape 1) — receives the
        broader filter dict from `_supported_filters_for(category)`
        on the owner: `calculator`, `scattering_type`,
        `sample_form`, `beam_mode`. **This is a different (wider)
        context than the canonicalization context above** —
        canonicalization picks one tag; supported-types filters the
        listing.
      - Override `show_supported()` to add an alias column when
        aliases exist (the per-row alias is derived from the
        canonical tag).
      - `ExperimentBase._swap_peak(new_type)` calls
        `PeakFactory.create(...)` and rebinds.
      Commit: `Wire experiment.peak to category-owned selector`

- [x] **P1.6 — Wire `experiment.background` to the new mixin.**
      - `BackgroundBase(CategoryCollection, SwitchableCategoryBase)`;
        declare the collection-level `_type` descriptor via P1.2's
        generalisation with `cif_handler=CifHandler(names=['_background.type'])`.
      - `_supported_types(filters)` (Shape 1).
      - `ExperimentBase._swap_background(new_type)` calls
        `BackgroundFactory.create(...)` and rebinds.
      - Existing `_pd_background.*` loop columns are **unchanged**
        per ADR §3 (B2 choice).
      Commit: `Wire experiment.background to category-owned selector`

- [x] **P1.7 — Wire `experiment.extinction` to the new mixin.**
      - `ExtinctionBase` multi-inherits the mixin; add `_type`
        descriptor with `cif_handler=CifHandler(names=['_extinction.type'])`.
      - `_supported_types(filters)` (Shape 1, `calculator` filter).
      - `ExperimentBase._swap_extinction(new_type)` calls
        `ExtinctionFactory.create(...)` and rebinds.
      Commit: `Wire experiment.extinction to category-owned selector`

- [x] **P1.8 — Rename `Calculation` → `Calculator` (§8c).**
      - Move
        `src/easydiffraction/datablocks/experiment/categories/calculation/`
        to `categories/calculator/` via `git mv` (preserves history).
      - Rename the Python class `Calculation` → `Calculator`, the
        CIF block prefix `_calculation` → `_calculator`, and the
        descriptor `calculator_type` → `type`.
      - **Factory naming.** The category factory (currently
        [`CalculationFactory`](../../../src/easydiffraction/datablocks/experiment/categories/calculation/factory.py))
        is renamed to **`CalculatorCategoryFactory`** to avoid
        colliding with the existing **backend** factory
        [`easydiffraction.analysis.calculators.factory.CalculatorFactory`](../../../src/easydiffraction/analysis/calculators/factory.py).
        Two factories live in this area after the rename:
        - `CalculatorCategoryFactory.create(...)` — creates the
          singleton `Calculator` category instance (the
          Python-object holder).
        - `CalculatorFactory.create(...)` — creates the live
          backend engine (cryspy / crysfml / pdffit) that
          `experiment._calculator` is bound to. **Unchanged.**
      - Multi-inherit the mixin; declare `_category_code='calculator'`,
        `_owner_attr_name='calculator'`,
        `_swap_method_name='_swap_calculator'`.
      - `ExperimentBase._swap_calculator(new_type)` is a Family-B
        engine-swap: keeps the singleton category instance and
        rebinds the live backend `experiment._calculator` via the
        existing **backend** `CalculatorFactory.create(...)`.
      - **Private-attribute layout (resolves naming collision).**
        Today `ExperimentBase.__init__` already uses
        `self._calculator = None` for the live-backend slot
        ([`item/base.py:71`](../../../src/easydiffraction/datablocks/experiment/item/base.py))
        and stores the category at `self._calculation`
        ([`item/base.py:172`](../../../src/easydiffraction/datablocks/experiment/item/base.py)).
        After the rename the public property `experiment.calculator`
        returns the **category** instance, and the live backend
        stays at `self._calculator`. To avoid collision, the
        category slot is renamed `self._calculation` →
        `self._calculator_category` (not `self._calculator`). The
        property body becomes `return self._calculator_category`.
        The mixin's staleness check (`parent.calculator is self`)
        works because the public `calculator` property returns the
        category. Update every internal reference accordingly.
      - Update `_supported_filters_for(category)` on `ExperimentBase`
        and the few downstream consumers (`background`, `extinction`,
        `peak` filters use `self.calculator.type` after the rename).
      Commit: `Rename Calculation to Calculator and wire to mixin`

- [x] **P1.9 — Split `Rendering` into `Chart` + `Table` (§8a).**
      This step lands as a **single atomic commit** that covers
      both the new categories AND every consumer of the removed
      `project.rendering` surface, so the branch stays buildable
      between steps. Don't split this into "new categories" and
      "migrate consumers" sub-commits.

      Sub-tasks (in one commit):
      - Delete `src/easydiffraction/project/categories/rendering/`.
      - Create `categories/chart/` and `categories/table/` with one
        concrete class each (`Chart`, `Table`) inheriting
        `(CategoryItem, SwitchableCategoryBase)`. Each holds its
        respective live facade (`Plotter`, `TableRenderer`) as a
        private internal.
      - Declare `_type` descriptors:
        `cif_handler=CifHandler(names=['_chart.type'])` and
        `cif_handler=CifHandler(names=['_table.type'])`. Include
        the `'auto'` sentinel in the membership validator.
      - `_supported_types(filters)` (Shape 2) — prepend
        `('auto', _auto_description)` to
        `PlotterFactory.descriptions()` / `TableRendererFactory.descriptions()`.
      - `Project._swap_chart(new_type)` / `Project._swap_table(new_type)`
        rebind the live engine on the singleton category (engine
        swap, not category swap).
      - Expose `project.chart` and `project.table` properties on
        `Project`. Remove `project.rendering`.
      - **Migrate every runtime consumer of `project.rendering.*`
        in the same commit.** Known sites (from a grep at plan
        time):
        - [`src/easydiffraction/__main__.py:87`](../../../src/easydiffraction/__main__.py)
        - [`src/easydiffraction/analysis/analysis.py:1636`](../../../src/easydiffraction/analysis/analysis.py)
        - Multiple sites in
          [`src/easydiffraction/project/display.py`](../../../src/easydiffraction/project/display.py)
        - Any other site surfaced by
          `git grep -nE '\bproject\.rendering\b|\brendering\.(plotter|tabler|chart_engine|table_engine)\b' src/`
          — re-run the grep at implementation time; if anything
          is missing from this list, add it before staging the
          commit.
      - The translation rule is: `project.rendering.plotter` →
        `project.chart.plotter`, `project.rendering.tabler` →
        `project.table.tabler`, `project.rendering.chart_engine` →
        `project.chart.type`, `project.rendering.table_engine` →
        `project.table.type`.
      - Verification before staging the commit:
        `git grep -nE '\bproject\.rendering\b|\brendering\.(plotter|tabler|chart_engine|table_engine)\b' src/`
        must return empty. (Tests and tutorials are handled by
        P2.1a and P1.13 respectively.)
      Commit: `Split Rendering into Chart and Table sibling categories`

- [x] **P1.10 — Promote `fitting_mode_type` to `FittingMode` (§8b).**
      - Create
        `src/easydiffraction/analysis/categories/fitting_mode/`
        with a `FittingMode(CategoryItem, SwitchableCategoryBase)`
        class.
      - One `_type` descriptor backed by `FitModeEnum`;
        `cif_handler=CifHandler(names=['_fitting_mode.type'])`.
      - `_supported_types(filters)` (Shape 3 — plain enum):
        `[(mode.value, mode.description()) for mode in FitModeEnum]`.
      - `Analysis._swap_fitting_mode(new_value)` performs the
        existing sibling-activation logic (controls which of
        `joint_fit` / `sequential_fit` / `sequential_fit_extract`
        is visible/serialized/used at fit time).
      - Expose `analysis.fitting_mode` property; remove the bare
        `fitting_mode_type` getter/setter.
      - Remove the `_fitting.mode_type` CIF tag; add
        `_fitting_mode.type`. CIF read path peeks `_fitting_mode.type`
        first.
      Commit: `Promote fitting_mode to FittingMode category`

- [x] **P1.11 — Drop persisted minimizer-name fields; add
      `_engine_metadata`.**
      - Drop `_minimizer.optimizer_name` and `_minimizer.method_name`
        from the LSQ base descriptor declarations and CIF emit/read
        paths.
      - On each concrete minimizer category class
        (`LmfitLeastsqMinimizer`, `LmfitLeastSquaresMinimizer`,
        `BumpsLmMinimizer`, etc.), declare:
        ```python
        _engine_metadata: ClassVar[dict[str, str]] = {
            'optimizer_name': '<engine name>',
            'method_name': '<method name>',
        }
        ```
      - In `Analysis._restore_fit_results_from_projection`, replace
        the reads from the dropped descriptors with
        `type(self.minimizer)._engine_metadata['optimizer_name']`
        and `['method_name']`.
      Commit: `Drop persisted optimizer_name/method_name; add metadata dict`

- [x] **P1.12 — Delete owner-level selector shims and CIF tags.**
      - Remove the following from `Analysis`: `minimizer_type`
        getter/setter, `show_supported_minimizer_types()`,
        `show_current_minimizer_type()`,
        `show_supported_fitting_mode_types()`,
        `show_current_fitting_mode_type()`,
        `_changed_minimizer_defaults` (already inlined elsewhere).
      - Remove from `ExperimentBase` and `BraggPDExperiment`:
        `peak_profile_type` getter/setter, `extinction_type`,
        `background_type`, `calculator_type`, and the matching
        `show_<cat>_types()` methods.
      - `project.rendering` is already fully migrated by P1.9 (the
        consumer migration is part of P1.9's atomic commit); this
        step's verification confirms no straggler remains.
      - Drop CIF emit/read paths for the deleted owner-level tags.
      - Verification grep:
        ```
        git grep -nE '\b(minimizer_type|peak_profile_type|background_type|extinction_type|calculator_type|fitting_mode_type)\b' src/
        git grep -nE 'show_(supported|current)_(minimizer|background|peak|extinction|calculator|fitting_mode)_(type|types)' src/
        git grep -nE '_fitting\.(minimizer_type|mode_type)|_rendering\.(chart_engine|table_engine)|_calculation\.calculator_type' src/
        ```
        All three must return empty.
      Commit: `Remove owner-level selector shims and obsolete CIF tags`

- [x] **P1.13 — Update tutorials.** Grep
      `docs/docs/tutorials/*.py` for the renamed Python paths and
      replace each with the new shape:
      - `project.analysis.minimizer_type = X` →
        `project.analysis.minimizer.type = X`
      - `project.experiments['…'].peak_profile_type = X` →
        `project.experiments['…'].peak.type = X`
      - Same shape for `background_type`, `extinction_type`,
        `calculator_type`, `fitting_mode_type`.
      - `project.rendering.chart_engine = X` →
        `project.chart.type = X`; `table_engine` → `table.type`.
      - Replace `show_supported_<cat>_types()` and
        `show_current_<cat>_type()` calls with
        `<cat>.show_supported()`.
      Run `pixi run notebook-prepare`. Verification grep against
      `docs/docs/tutorials/` matches P1.12's patterns; all must
      return empty.
      Commit: `Update tutorials for category-owned selectors`

- [x] **P1.14 — Promote ADR + amend affected ADRs.**
      - `git mv docs/dev/adrs/suggestions/switchable-category-owned-selectors.md docs/dev/adrs/accepted/`.
        Flip Status header to `Accepted`. Update any relative
        links that move.
      - Edit each of the eight ADRs listed in §"ADR" above per
        the matching bullet in the ADR's §"ADRs to amend":
        `switchable-category-api.md`, `selector-families.md`,
        `fit-mode-categories.md`,
        `python-cif-category-correspondence.md`,
        `minimizer-category-consolidation.md`,
        `analysis-cif-fit-state.md`, `display-ux.md`,
        `category-owner-sections.md`.
      - Update [`docs/dev/adrs/index.md`](../adrs/index.md): move
        the row for this ADR from Suggestion → Accepted.
      - Close open issues
        [#72](../issues/open.md) ("Warn on All Switchable-Category
        Type Changes") and
        [#76](../issues/open.md) ("Consistent `_type` suffix in
        switchable-category API names") by moving them to
        [`closed.md`](../issues/closed.md) with a pointer to the
        new ADR. Replace #72 with a note that the warning logic is
        now uniform via `_swap_<name>` hooks; replace #76 with a
        pointer to the new uniform surface that drops the suffix.
      Commit: `Promote switchable-category-owned-selectors ADR`

- [x] **P1.15 — Phase 1 review gate.** No code change in this
      step. Re-run the three targeted greps from P1.12 against the
      Phase 1 scopes (`src/` and `docs/docs/tutorials/`); they must
      all return empty. The `tests/` sweep is intentionally
      deferred to P2.1a, which is the step that migrates the tests.
      Then stop and request user review. After approval, proceed
      to Phase 2.

## Verification (Phase 2)

Each command captures its log with a zsh-safe exit-code variable as
required by `.github/copilot-instructions.md` → **Workflow**.

- [ ] **P2.1a — Migrate existing tests off removed API.** Each
      bullet is a separate commit. Grep
      `tests/` for the same patterns as P1.12 and replace, mirroring
      the surface change.

      Delete (obsolete after Phase 1):
      - `tests/unit/easydiffraction/project/categories/rendering/`
        (rendering is a project category, not an experiment
        category; the existing test tree lives under
        `tests/unit/easydiffraction/project/categories/`). Replace
        with new `tests/unit/easydiffraction/project/categories/chart/`,
        `tests/unit/easydiffraction/project/categories/table/`
        directories mirroring the new source layout.
      - Any test referencing `Calculation` (now `Calculator`) by
        the old name. The existing tree
        `tests/unit/easydiffraction/datablocks/experiment/categories/calculation/`
        moves to `categories/calculator/` via `git mv`; references
        to `CalculationFactory` become `CalculatorCategoryFactory`
        per P1.8's factory rename.

      Rewrite call sites (one commit per file or per small
      cluster):
      - `tests/unit/easydiffraction/analysis/test_analysis.py`
        and `test_analysis_coverage.py` — every
        `a.minimizer_type = X` → `a.minimizer.type = X`; every
        `a.show_supported_minimizer_types()` →
        `a.minimizer.show_supported()`; same for fitting_mode.
      - `tests/unit/easydiffraction/datablocks/experiment/*.py` —
        every `e.peak_profile_type`, `e.background_type`,
        `e.extinction_type`, `e.calculator_type` →
        `e.peak.type`, `e.background.type`, `e.extinction.type`,
        `e.calculator.type`.
      - `tests/integration/fitting/*.py` and
        `tests/functional/test_switchable_categories.py` — extend
        the parametrized matrix to include the new uniform
        surface; assert `category.show_supported()` and
        `category.type` exist on every in-scope category.
      - `tests/unit/easydiffraction/project/test_project.py` and
        `test_display.py` — `project.rendering.chart_engine`
        / `table_engine` → `project.chart.type` / `project.table.type`.
      - `tests/unit/easydiffraction/io/test_results_sidecar.py` and
        `test_cif_serialize.py` (or wherever applicable) — update
        round-trip assertions to the new tag names.

      Layout check:
      ```
      pixi run test-structure-check > /tmp/easydiffraction-test-structure-check.log 2>&1; \
        test_structure_check_exit_code=$?; \
        tail -n 200 /tmp/easydiffraction-test-structure-check.log; \
        exit $test_structure_check_exit_code
      ```

      Stale-reference greps:
      ```
      git grep -nE '\b(minimizer_type|peak_profile_type|background_type|extinction_type|calculator_type|fitting_mode_type)\b' tests/
      git grep -nE 'show_(supported|current)_(minimizer|background|peak|extinction|calculator|fitting_mode)_(type|types)' tests/
      git grep -nE '_fitting\.(minimizer_type|mode_type)|_rendering\.(chart_engine|table_engine)|_calculation\.calculator_type' tests/
      ```
      All three must return empty.

- [ ] **P2.1 — Add unit tests for new modules.**
      - `tests/unit/easydiffraction/core/test_switchable.py`
        covering: setter staleness check raises when `_parent` is
        `None`; setter staleness check raises when the live slot
        no longer points at `self`; default `_canonicalize()` is
        identity; `show_supported()` renders all three Shape
        templates (factory / renderer-factory / enum).
      - Per-category unit tests mirroring the new source layout
        (`chart/`, `table/`, `calculator/`, `fitting_mode/`).
      Verify layout with
      `pixi run test-structure-check`.

- [ ] **P2.2 — Auto-fixes and static checks.**
      ```
      pixi run fix > /tmp/easydiffraction-fix.log 2>&1; \
        fix_exit_code=$?; tail -n 200 /tmp/easydiffraction-fix.log; \
        exit $fix_exit_code
      pixi run check > /tmp/easydiffraction-check.log 2>&1; \
        check_exit_code=$?; tail -n 200 /tmp/easydiffraction-check.log; \
        exit $check_exit_code
      ```

- [ ] **P2.3 — Unit tests.**
      ```
      pixi run unit-tests > /tmp/easydiffraction-unit-tests.log 2>&1; \
        unit_tests_exit_code=$?; tail -n 200 /tmp/easydiffraction-unit-tests.log; \
        exit $unit_tests_exit_code
      ```

- [ ] **P2.4 — Integration tests.**
      ```
      pixi run integration-tests > /tmp/easydiffraction-integration-tests.log 2>&1; \
        integration_tests_exit_code=$?; tail -n 200 /tmp/easydiffraction-integration-tests.log; \
        exit $integration_tests_exit_code
      ```

- [ ] **P2.5 — Script tests.**
      ```
      pixi run script-tests > /tmp/easydiffraction-script-tests.log 2>&1; \
        script_tests_exit_code=$?; tail -n 200 /tmp/easydiffraction-script-tests.log; \
        exit $script_tests_exit_code
      ```
      This regenerates `tmp/tutorials/projects/*` fixtures with
      the new CIF layout.

## Suggested Pull Request

**Title:** Make switchable-category selectors live on the category

**Description (user-facing):**

Every place EasyDiffraction lets you pick an implementation — the
minimizer, the peak profile, the background, the extinction
correction, the calculator backend, the chart and table renderers,
the fitting mode — now uses the same compact shape:

```python
project.analysis.minimizer.type = 'bumps (dream)'
project.experiments['hrpt'].peak.type = 'pseudo-voigt'
project.experiments['hrpt'].background.type = 'chebyshev'
project.chart.type = 'plotly'
project.analysis.fitting_mode.type = 'joint'
```

and the matching `category.show_supported()` to see the table of
choices with the active one starred.

CIF files become more compact too — every selector persists as a
single `_<cat>.type` tag inside the same block as the category's
other parameters. Owner-level mirror tags such as
`_fitting.minimizer_type` go away.

The implementation also tidies up three small structural irritants
behind the scenes (the rendering category split into chart and
table, the fitting-mode descriptor promoted to its own category,
and the `Calculation` category renamed to `Calculator` to match
what it actually selects). No fitting or rendering capability is
removed; everything you can do today is still possible — just with
one unified, predictable shape.
