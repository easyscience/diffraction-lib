# Review 2: Switchable Category Owned Selectors Plan

Reviewed plan:
[`switchable-category-owned-selectors.md`](switchable-category-owned-selectors.md)

Reviewed reply:
[`switchable-category-owned-selectors_reply-1.md`](switchable-category-owned-selectors_reply-1.md)

Previous review:
[`switchable-category-owned-selectors_review-1.md`](switchable-category-owned-selectors_review-1.md)

This review follows
[`.github/copilot-instructions.md`](../../../.github/copilot-instructions.md).

No tests, lint, build, formatting, or `pixi` commands were run. This is
a static re-review only.

## Summary

Reply 1 addresses all four Review 1 findings: peak canonicalization no
longer uses beam mode alone, collection scalars no longer merge into
`CategoryCollection.parameters`, the calculator category factory is
renamed to avoid colliding with the backend factory, and the rendering
consumer migration is now part of the P1.9 atomic commit.

The updated plan still has one blocker in P1.8 and two smaller
source/path mismatches that should be corrected before implementation
starts.

## Findings

### F1 - P1.8 assigns the calculator category and backend to the same attribute

P1.8 now correctly distinguishes the category factory from the backend
factory, but it still says the `ExperimentBase` category storage should
be renamed from `_calculation` to `_calculator`, while also stating that
the live backend attribute was already `_calculator`
(`switchable-category-owned-selectors.md:337`). That creates a private
attribute collision: one slot would have to hold both the singleton
`Calculator` category and the live calculator engine.

The current owner layout keeps those responsibilities separate:
`ExperimentBase.__init__` initializes the live backend slot as
`self._calculator = None`, then creates the category at
`self._calculation`
(`src/easydiffraction/datablocks/experiment/item/base.py:71`). The
`calculation` property lazily resolves the live backend if
`self._calculator` is `None`, but returns `self._calculation`
(`src/easydiffraction/datablocks/experiment/item/base.py:172`). Backend
swaps assign `self._calculator = CalculatorFactory.create(tag)`
(`src/easydiffraction/datablocks/experiment/item/base.py:214`).

P1.8 should choose distinct private names after the public rename. For
example, keep the public property as `experiment.calculator`, store the
category in `self._calculator_category` or similar, and either keep the
live backend as `self._calculator` or explicitly rename it to
`self._calculator_backend`. Whichever convention is chosen, the plan
should make the distinction explicit and update the mixin
staleness-check expectations accordingly.

### F2 - P1.5 overstates what `_peak_profile_context()` currently returns

P1.5 says `self._parent._peak_profile_context()` "today returns
`calculator`, `scattering_type`, `beam_mode`, `sample_form`"
(`switchable-category-owned-selectors.md:271`). The current method
returns only `scattering_type` and `beam_mode`
(`src/easydiffraction/datablocks/experiment/item/base.py:618`).

The corrected canonicalization direction from Reply 1 is sound: alias
resolution needs the peak alias context and must include
`scattering_type` plus `beam_mode` where applicable. But the plan should
not describe `_peak_profile_context()` as the full support-filter
context. P1.5 should separate those two concepts: `_canonicalize()` can
pass `_peak_profile_context()` into
`PeakFactory._canonical_tag_for(...)`, while `_supported_types(filters)`
receives the broader filters from `_supported_filters_for(category)`.

### F3 - P2.1a points rendering tests at the wrong package path

P2.1a says to delete
`tests/unit/easydiffraction/datablocks/experiment/categories/rendering/`
if rendering-category tests exist
(`switchable-category-owned-selectors.md:521`). Rendering is a project
category, and the existing test tree is under
`tests/unit/easydiffraction/project/categories/rendering/`.

If the plan is followed literally, the obsolete rendering tests can be
missed or left in the old layout. P2.1a should point at
`tests/unit/easydiffraction/project/categories/rendering/` and replace
it with the new sibling `project/categories/chart/` and
`project/categories/table/` test directories.

## Checks Skipped

Per review instructions, no tests, lint, build, formatting, notebook, or
`pixi` commands were run. The review used static reads and greps only.
