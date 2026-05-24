# Reply to Review 1: Switchable Category Owned Selectors ADR

Reply to
[`switchable-category-owned-selectors_review-1.md`](switchable-category-owned-selectors_review-1.md)
for the ADR at
[`switchable-category-owned-selectors.md`](../accepted/switchable-category-owned-selectors.md).

This reply follows
[`.github/copilot-instructions.md`](../../../../.github/copilot-instructions.md).

All seven findings are accepted. The ADR is amended; the changes are
summarised per finding below.

## Findings

### F1 — Proposed base does not cover `background`

**Verdict: agree.**
[`src/easydiffraction/datablocks/experiment/categories/background/base.py:11`](../../../../src/easydiffraction/datablocks/experiment/categories/background/base.py)
declares `BackgroundBase(CategoryCollection)`, so a
`SwitchableCategoryBase(CategoryItem)` cannot apply to it. Singleton
categories (minimizer, peak, extinction) and collection-shaped
categories (background) need the same selector API but different storage
substrates.

**Action.** Recast §4 of the ADR. `SwitchableCategoryBase` is now a
**behavior-only mixin** that contributes the `_parent` back-reference,
the `type` property, `show_supported()`, and the `_swap_method_name` /
`_factory` class-level constants — **no descriptor instances and no
`__init__` work**. Concrete bases multi-inherit it next to the
appropriate storage substrate:

```python
class MinimizerCategoryBase(CategoryItem, SwitchableCategoryBase): ...
class BackgroundBase(CategoryCollection, SwitchableCategoryBase): ...
class PeakBase(CategoryItem, SwitchableCategoryBase): ...
class ExtinctionBase(CategoryItem, SwitchableCategoryBase): ...
```

This matches the existing
[`minimizer-category-consolidation.md`](../accepted/minimizer-category-consolidation.md)
§8 rule (no descriptor mixins) while permitting a behavior mixin.
Persistence on a `CategoryCollection` is handled by F4's recommendation
(the `type` descriptor lives on the collection itself, not on the items
inside the loop).

### F2 — `calculation` is a backend selector, not switchable

**Verdict: agree.**
[`accepted/selector-families.md:27`](../accepted/selector-families.md)
classifies `calculation.calculator_type` as a backend selector, and
[`src/easydiffraction/datablocks/experiment/categories/calculation/default.py:21`](../../../../src/easydiffraction/datablocks/experiment/categories/calculation/default.py)
confirms `Calculation` is a singleton `CategoryItem` with the backend
tag as an internal descriptor; the live calculator is swapped at the
owner-level, not the category instance.

**Action.** Removed `calculation` / `calculator` from §6 of the ADR. The
in-scope list is now `minimizer`, `background`, `peak`, `extinction`,
"and any future instance-swap switchable category". Backend selectors
remain governed by `selector-families.md` unchanged.

### F3 — `show_supported()` cannot be a `@classmethod`

**Verdict: agree on both counts.** A classmethod cannot mark the active
row, and the proposed `cls._factory.show_supported(cls.__mro__[1])`
would raise because
[`src/easydiffraction/core/factory.py:228`](../../../../src/easydiffraction/core/factory.py)
defines the signature as
`(cls, *, calculator=None, sample_form=None, scattering_type=None, beam_mode=None, radiation_probe=None)`
— keyword-only filters, no positional argument.

**Action.** Reshaped the §4 contract:

1. `show_supported()` is an **instance method** on the category.
2. Its body delegates to the owner via a documented private hook
   `self._parent._show_supported_for_<cat>()`. The hook owns the filter
   context (calculator, beam_mode, scattering type, …) and reads the
   current tag from `self.type`.
3. Owners that already implement `show_<cat>_types()` (e.g.
   [`bragg_pd.py:225`](../../../../src/easydiffraction/datablocks/experiment/item/bragg_pd.py)
   for background,
   [`base.py:561`](../../../../src/easydiffraction/datablocks/experiment/item/base.py)
   for peak) rename that method to the `_show_supported_for_<cat>()`
   private form. The user-facing surface is uniformly
   `category.show_supported()`.

So the category exposes a single public API; the owner keeps the
filter-context logic it already has.

### F4 — `type` must be a real descriptor, not a computed property

**Verdict: agree.** `CategoryItem.parameters`
([`category.py:70`](../../../../src/easydiffraction/core/category.py))
returns `GenericDescriptorBase` instances only, and
`category_item_to_cif()`
([`io/cif/serialize.py:170`](../../../../src/easydiffraction/io/cif/serialize.py))
serializes only `item.parameters`. A computed property over
`type_info.tag` would never make it into CIF.

**Action.** Rewrote §4 of the ADR. `SwitchableCategoryBase` declares a
real `StringDescriptor` named `type` with
`cif_handler=CifHandler(names=[f'_{category_code}.type'])` and a
class-level validator over the factory's supported tags. The writable
`type` property wraps that descriptor; its setter delegates to the
owner's `_swap_<name>` hook, which constructs the new instance (whose
`type` descriptor naturally defaults to its own factory tag) and
replaces the slot.

CIF read path becomes:

1. Read `_<cat>.type` from the block.
2. Owner calls `_swap_<name>(value)` to install the matching concrete
   class.
3. Generic deserialization populates the remaining descriptors on the
   newly-installed instance.

This matches the read path already established in
[`minimizer-category-consolidation.md`](../accepted/minimizer-category-consolidation.md)
P1.7 (read `_fitting.minimizer_type` first, then populate
`_minimizer.*`). The only change is that the type tag now lives inside
the category's own namespace.

### F5 — Peak CIF tag inconsistency

**Verdict: agree.** §3 promised uniform `_<cat>.type` but the footnote
kept `_peak.profile_type`.
[`categories/peak/base.py:23`](../../../../src/easydiffraction/datablocks/experiment/categories/peak/base.py)
confirms the current spelling.

**Action.** Decision: **rename `_peak.profile_type` → `_peak.type`** for
uniformity. Same beta-posture cutover as the rest of the ADR; no shim.
The ADR footnote is rewritten to spell this out as a deliberate one-time
CIF tag rename, not a documented inconsistency.

(`_background.*` already conforms because background uses no
identity-echo tag today — the rename is peak-only.)

### F6 — `optimizer_name` and `method_name` are real fit metadata

**Verdict: agree.** Confirmed against the source:
[`analysis.py:1387-1390`](../../../../src/easydiffraction/analysis/analysis.py)
populates these from `fitter.minimizer.name` and
`fitter.minimizer.method` — the backend's own internal naming, which is
more specific than the EasyDiffraction tag. For example,
`MinimizerTypeEnum.LMFIT_LEASTSQ` ('lmfit (leastsq)') yields
`optimizer_name='Levenberg-Marquardt'`, `method_name='leastsq'`. The
restore path
([`analysis.py:739`](../../../../src/easydiffraction/analysis/analysis.py))
reads them back into `FitResults`, and
[`accepted/analysis-cif-fit-state.md:93`](../accepted/analysis-cif-fit-state.md)
treats them as persisted deterministic optimizer metadata.

**Action.** Retracted the §3 claim that these are "duplicate by
construction". The ADR now says only `_fitting.minimizer_type` (the
owner-level selector tag) is removed as a duplicate; the
backend-reported `_minimizer.optimizer_name` and
`_minimizer.method_name` stay as fit-result metadata, unchanged.

The §"Example: minimizer in the new shape" CIF block keeps these fields
populated when a fit has run.

### F7 — Stale category references can still mutate the live owner

**Verdict: agree.** Critical edge case I had documented as
"orphaned-object editing" but the orphan is not actually orphaned —
[`core/guard.py:77`](../../../../src/easydiffraction/core/guard.py) sets
`_parent` on guarded assignment, so the old instance retains its
back-reference and a later `m.type = 'X'` from the stale `m` would
re-trigger the owner's swap hook.

**Action.** Added two defences to §4 of the ADR:

1. **Owner detaches the old instance.** `_swap_<name>` clears the old
   instance's `_parent` (and any other back-reference fields) before
   installing the new one:

   ```python
   def _swap_minimizer(self, new_type: str) -> None:
       new_minimizer = MinimizerCategoryFactory.create(new_type)
       self._warn_about_minimizer_swap_defaults(
           self._minimizer, new_minimizer,
       )
       self._minimizer._parent = None       # detach old
       new_minimizer._parent = self
       self._minimizer = new_minimizer
       self._fitter = Fitter(new_type)
   ```

2. **Setter rejects stale-instance writes.** The `type` setter on
   `SwitchableCategoryBase` checks both attachment **and** liveness:

   ```python
   @type.setter
   def type(self, value: str) -> None:
       if self._parent is None:
           raise RuntimeError(
               f'{type(self).__name__} is detached; '
               'cannot change type on a stale instance.'
           )
       live = getattr(self._parent, self._owner_attr_name)
       if live is not self:
           raise RuntimeError(
               f'{type(self).__name__} is no longer the live '
               f'category on its owner; obtain a fresh reference '
               f'via owner.{self._owner_attr_name}.'
           )
       getattr(self._parent, self._swap_method_name)(value)
   ```

The new `_owner_attr_name` class constant names the slot (`'minimizer'`,
`'background'`, …). With these two checks the "stale `m`" scenario fails
loudly instead of silently mutating the owner.

The §5 "Reference-staleness" subsection of the ADR is rewritten to
document this as a _raised error_, not a silent gotcha. Descriptor
writes on the stale instance (e.g. `m.sampling_steps = 3000`) still
operate on the orphan — that is the unavoidable Python semantics — but
the `type` swap path is now safe.

## Addendum — design clarifications raised after the initial reply

Three of the review-1 findings were revisited in a follow-up discussion.
The ADR is amended again to reflect the revised positions:

### F6 walked back — `_minimizer.optimizer_name` / `_minimizer.method_name` are dropped after all

My original reply accepted the reviewer's claim that these fields "carry
information beyond the tag". Re-reading the engine sources
([`src/easydiffraction/analysis/minimizers/lmfit_leastsq.py`](../../../src/easydiffraction/analysis/minimizers/lmfit_leastsq.py)
and the matching `bumps_lm.py`, `dfols.py`, …) shows that:

- `name` defaults to the `MinimizerTypeEnum` tag itself.
- `method` defaults to a per-engine module-level constant
  (`DEFAULT_METHOD = 'leastsq'` etc.).
- The public API never overrides them at construction.

So in practice the persisted values are **deterministic functions of the
tag**, exactly the duplication this ADR is built to remove. Dropping
them and deriving `FitResults.optimizer_name` / `FitResults.method_name`
from the active minimizer class on restore is the consistent move.

ADR amendment: §3 now drops both fields; the Consequences list adds
[`analysis-cif-fit-state.md`](../accepted/analysis-cif-fit-state.md) to
the ADRs that need to be amended.

### F3 refined — `show_supported()` renders in the mixin

My original reply pushed the rendering through a per-owner
`_show_supported_for_<cat>()` method, which would have duplicated the
table-building code across every owner. Concrete factoring is cleaner:
the mixin's `show_supported()` builds the `['*', tag, description]`
table itself; the owner only contributes a context-filter dict through
`_supported_filters_for(category)`. Every existing `show_<cat>_types()`
method on an owner is **deleted** (not renamed) because the rendering
moves to the mixin.

ADR amendment: §4 contains the refined mixin body and the matching
owner-side `_supported_filters_for()` dispatch sketch.

### F2 expanded — `calculation` is brought in scope via the mechanism-vs-surface framing

My original reply removed `calculation` from scope on the grounds that
the reviewer was correct: it is a backend selector (engine swap), not a
category instance swap. That is true at the mechanism level. But from
the user's perspective, setting `calculation.calculator_type = 'cryspy'`
is exactly the same gesture as setting
`analysis.minimizer_type = 'bumps (lm)'`. The distinction matters
internally; the public surface should be uniform.

The ADR is re-shaped around a **mechanism-vs-surface** framing. Three
families per [`selector-families.md`](../accepted/selector-families.md)
all present the same writable `category.type` surface; the family
distinction documents what happens behind the setter (instance swap,
engine swap, sibling activation). `calculation` is brought back in scope
as a Family-B row, alongside two new structural changes (rendering split
into `chart` + `table`, and `fitting_mode` promotion from bare
descriptor to category) that bring the rest of the codebase under the
same rule.

ADR amendments:

- §3 CIF mapping table grows from 5 rows to 8.
- §6 scope rewritten as "every selector with a writable type surface",
  grouped by mechanism behind the surface rather than by whether it is
  in scope.
- New §8 records the two structural changes (rendering split,
  fitting_mode promotion).
- Catalog of selectors collapses Families A/B/C into one in-scope 8-row
  table; Family D stays as a separate out-of-scope table.
- Consequences widens the list of ADRs to amend (selector-families,
  fit-mode-categories, analysis-cif-fit-state).
- Example CIF section now shows all three files post-migration.

### Naming consistency — `Calculation` → `Calculator`

A follow-up question pointed out that every other in-scope category is
named after the **thing being selected** (`minimizer` = minimizer,
`peak` = peak, `background` = background, `extinction` = extinction,
`chart` = chart, `table` = table, `fitting_mode` = fitting mode).
`calculation` was the odd one out — the thing whose type is selected is
a calculator, not a calculation. The mismatched category name is the
only reason the descriptor today is called `calculator_type` rather than
`type`.

Renaming the Python class `Calculation` → `Calculator`, the owner
attribute `experiment.calculation` → `experiment.calculator`, the
descriptor `calculator_type` → `type`, and the CIF block
`_calculation.*` → `_calculator.*` is the consistent move. The mechanism
stays Family B (engine swap) — only the user-facing surface and the CIF
block name change.

ADR amendments:

- §8 grows a third structural change, §8c.
- Catalog row 5 updates Python/CIF columns and marks the mechanism as
  "B + §8 rename".
- §3 table, §6 in-scope list, §4 mechanism example, and Example CIF /
  Python sections all updated.
- ADRs to amend now also includes
  [`python-cif-category-correspondence.md`](../accepted/python-cif-category-correspondence.md)
  to reflect the category rename.

### Example accuracy — peak and background descriptor names

The first version of the Example section used invented descriptor names
(`_peak.broadening_u/v/w`, `_pd_background.order/coeff`). Grepping the
source shows the real spellings:

- Peak (CWL profile parameters per
  [`peak/cwl_mixins.py`](../../../src/easydiffraction/datablocks/experiment/categories/peak/cwl_mixins.py)):
  `_peak.broad_gauss_u`, `_peak.broad_gauss_v`, `_peak.broad_gauss_w`,
  `_peak.broad_lorentz_x`, `_peak.broad_lorentz_y`.
- Background Chebyshev (per
  [`background/chebyshev.py`](../../../src/easydiffraction/datablocks/experiment/categories/background/chebyshev.py)):
  `_pd_background.id`, `_pd_background.Chebyshev_order`,
  `_pd_background.Chebyshev_coef`.

The Example CIF and Python surface sections in the ADR are updated to
use the real names so the document is usable as a concrete reference for
the implementing plan. Going forward every CIF tag and descriptor name
in ADR examples is grepped from the source before being written.

### Net effect

Eight selectors, one rule. The user types
`<owner>.<category>.type = 'X'` and runs
`<owner>.<category>.show_supported()` for every selector in the project;
the CIF reads `_<cat>.type` everywhere. The mechanism families (A/B/C)
remain a useful internal classification but no longer leak into the
public API.

## Verification

This reply is a static one. No tests, lint, build, or `pixi` commands
were run, matching the reviewer's own constraint. Markdown files in this
review cycle were also not run through `prettier` per the new
review/reply formatting rule in
[`.github/copilot-instructions.md`](../../../../.github/copilot-instructions.md)
→ **Change Discipline**.

The implementing plan (separate file, to be drafted only after ADR
acceptance) will include the standard Phase-2 verification suite.

## Summary of files touched by this reply

- [`docs/dev/adrs/accepted/switchable-category-owned-selectors.md`](../accepted/switchable-category-owned-selectors.md)
  — amended per F1–F7 in the initial pass; re-amended per the addendum
  above.
- [`docs/dev/adrs/suggestions/switchable-category-owned-selectors_reply-1.md`](switchable-category-owned-selectors_reply-1.md)
  — this file.
