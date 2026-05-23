# Review 1: Switchable Category Owned Selectors Plan

Reviewed plan:
[`switchable-category-owned-selectors.md`](switchable-category-owned-selectors.md)

This review follows
[`.github/copilot-instructions.md`](../../../.github/copilot-instructions.md).

No tests, lint, build, formatting, or `pixi` commands were run. This is a
static plan review only.

## Summary

The plan is close enough to implement once the items below are corrected.
The main issues are in the step boundaries and a few implementation details
that would either break existing behavior or make the required atomic commits
non-buildable.

## Findings

### F1 - Peak canonicalization omits required alias context

P1.5 says `PeakBase._canonicalize(value)` should call an existing
`_canonicalize_peak_profile_type` helper using only
`self._parent.type.beam_mode.value`
(`switchable-category-owned-selectors.md:258`). A static grep found no such
helper in `src/easydiffraction`; the current implementation lives in
`PeakFactory._canonical_tag_for(...)`.

More importantly, peak aliases require the full local context. The factory
alias rules match `scattering_type` plus `beam_mode` for Bragg profiles and
`scattering_type` alone for Total profiles
(`src/easydiffraction/datablocks/experiment/categories/peak/factory.py:34`).
The current owner-level setter passes `**self._peak_profile_context()` into
`PeakFactory._canonical_tag_for(...)`
(`src/easydiffraction/datablocks/experiment/item/base.py:532`).

If the plan is implemented as written, aliases such as `pseudo-voigt` will not
canonicalize reliably for CW/TOF Bragg contexts, and Total aliases cannot be
resolved from beam mode alone. P1.5 should explicitly use the full peak
profile context, including at least `scattering_type` and `beam_mode`, and
should either create the helper in that step or name the existing factory API
directly.

### F2 - Collection-level `_type` should not be merged into `parameters`

P1.2 says to allow a collection-level `_type` descriptor by extending
`CategoryCollection.parameters` and the serializer path
(`switchable-category-owned-selectors.md:217`). Today,
`CategoryCollection.parameters` means only "all parameters from all items in
this collection" and flattens child item parameters
(`src/easydiffraction/core/category.py:230`). The collection CIF serializer
also builds loop columns from the first item's parameters
(`src/easydiffraction/io/cif/serialize.py:254`), and the reader mirrors that
shape from a temporary item instance
(`src/easydiffraction/io/cif/serialize.py:964`).

Changing `parameters` to include a collection scalar would alter a broad core
contract for every collection, and it risks leaking a scalar selector into
owner-level parameter scans or loop column logic. The plan should instead add
a separate collection-scalar access path that is used by CIF owner/collection
serialization and deserialization, while leaving `CategoryCollection.parameters`
as item-parameter-only.

### F3 - Calculator factory naming is ambiguous after the rename

P1.8 renames `Calculation` to `Calculator` and says
`ExperimentBase._swap_calculator(new_type)` rebinds the live backend using the
existing `CalculatorFactory.create(...)`
(`switchable-category-owned-selectors.md:293`). There are already two factory
roles in this area: the backend calculator factory is
`easydiffraction.analysis.calculators.factory.CalculatorFactory`
(`src/easydiffraction/analysis/calculators/factory.py:19`), while the
experiment category factory is currently
`easydiffraction.datablocks.experiment.categories.calculation.factory.CalculationFactory`
(`src/easydiffraction/datablocks/experiment/categories/calculation/factory.py:12`).

After moving `categories/calculation/` to `categories/calculator/`, renaming
the category factory to `CalculatorFactory` would create two same-named
factories with different responsibilities. Leaving it as `CalculationFactory`
would conflict with the new category noun. P1.8 should choose and document a
non-conflicting name, such as `CalculatorCategoryFactory`, and should state
which factory creates the singleton category versus which factory creates the
live backend engine.

### F4 - P1.9 deletes `project.rendering` before updating its consumers

P1.9 removes `project.rendering` and exposes `project.chart` /
`project.table` (`switchable-category-owned-selectors.md:315`), but P1.12
defers removing remaining `project.rendering` references until several commits
later (`switchable-category-owned-selectors.md:376`). The repository still has
many direct consumers, including `src/easydiffraction/__main__.py:87`,
`src/easydiffraction/analysis/analysis.py:1636`, and multiple calls in
`src/easydiffraction/project/display.py`.

Because the plan requires each Phase 1 step to land as a single atomic commit,
P1.9 would leave the branch broken until P1.12. The rendering split step should
update all direct runtime consumers from `project.rendering.plotter` and
related paths to the new `project.chart` / `project.table` API in the same
commit, or it should introduce an explicit temporary compatibility path and
remove it in P1.12.

## Checks Skipped

Per review instructions, no tests, lint, build, formatting, notebook, or `pixi`
commands were run. The review used static reads and greps only.
