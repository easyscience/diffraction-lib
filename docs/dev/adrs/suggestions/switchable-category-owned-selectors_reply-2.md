# Reply to Review 2: Switchable Category Owned Selectors ADR

Reply to
[`switchable-category-owned-selectors_review-2.md`](switchable-category-owned-selectors_review-2.md)
for the ADR at
[`switchable-category-owned-selectors.md`](../accepted/switchable-category-owned-selectors.md).

This reply follows
[`.github/copilot-instructions.md`](../../../../.github/copilot-instructions.md).

All five findings are accepted. Each was discussed interactively with
the user before applying the amendment; the selected option and its
rationale appear below.

## Findings

### F1 — `_background.type` won't round-trip through the generic collection serializer

**Verdict: agree.**
[`src/easydiffraction/core/category.py:230`](../../../src/easydiffraction/core/category.py)
returns parameters from items only, and
[`src/easydiffraction/io/cif/serialize.py:244`](../../../src/easydiffraction/io/cif/serialize.py)
writes a loop built from the first item's parameters. A collection-
level `_type` descriptor on `BackgroundBase(CategoryCollection, ...)`
would silently not serialize.

**Gemmi check.** Before deciding, the assistant verified empirically
that the CIF format and gemmi parser both support a scalar tag and a
loop sharing the same category prefix in the same block:

```text
data_test
_background.type chebyshev
loop_
_background.Chebyshev_order
_background.Chebyshev_coef
0  0.42
1 -0.18
2  0.05
```

`gemmi.cif.read_string(...).sole_block().find_value('_background.type')`
returns `'chebyshev'`, and the loop reads back correctly. No conflict.

**Convention check.** Today every `_<cat>.*` block in the project's
saved CIFs is uniformly scalar OR loop, never mixed in one prefix.
The powder-background loop currently lives at `_pd_background.*`
(IUCr pd_CIF convention, with the `_pd_` powder-diffraction prefix).
Three sub-options were on the table for option B:

- **B1.** Rename loop to `_background.*`; one prefix everywhere.
  Drops the `_pd_` powder-diffraction provenance from the loop tags.
- **B2.** Scalar `_background.type` (new prefix) + keep
  `_pd_background.*` loop. Two CIF prefixes for one Python
  collection.
- **B3.** Keep `_pd_background.*` for both scalar and loop. Breaks
  the ADR's uniform `_<cat>.type` rule for this row.

**User decision: B2.** Respects the IUCr pd_CIF powder-diffraction
convention for the loop columns; satisfies the ADR's uniform
`_<cat>.type` rule for the selector; the Python `BackgroundBase`
collection owns two CIF prefixes (one for its scalar selector, one
for its loop rows).

**Action.** ADR §3 CIF table row for `_background.type` reads "two
prefixes". ADR §4 documents a small generalization of
`CategoryCollection` (and its serializer) to support collection-
level scalar descriptors that emit their CIF tag above the loop
the items contribute. The `BackgroundBase` collection-level
`_type` descriptor uses `cif_handler=CifHandler(names=['_background.type'])`;
the existing `_pd_background.*` loop columns are unchanged.

### F2 — Mixin assumed `FactoryBase` API; breaks Families B and C

**Verdict: agree.** The proposed mixin called
`_factory._supported_map()` and
`_factory.supported_for(**filters)`, which works for domain factories
([`src/easydiffraction/core/factory.py:228`](../../../src/easydiffraction/core/factory.py))
but not for `RendererFactoryBase`
([`src/easydiffraction/display/base.py:104`](../../../src/easydiffraction/display/base.py),
exposes `_registry()` / `supported_engines()` / `descriptions()`) and
not for `FitModeEnum`
([`src/easydiffraction/analysis/enums.py:10`](../../../src/easydiffraction/analysis/enums.py),
no factory at all).

**Options:**

- **A.** Per-category `_supported_types(filters) -> list[tuple[str, str]]`
  method. Each concrete base implements the right call (domain
  factory / renderer factory / enum). Mixin's `show_supported()`
  renders the returned (tag, description) pairs. Three "shapes" of
  enumerator coexist; no upstream changes to factories or enums.
- **B.** Define a `SupportedTypeProvider` protocol with adapters.
- **C.** Mixin scoped to Family A; separate mixins for B and C.

**User decision: A.** Smallest change, no abstraction, no upstream
factory churn. The three shapes are isolated by category and each
is two or three lines.

**Action.** ADR §4 mixin sketch drops `_factory: ClassVar[...]`, adds
an abstract `_supported_types(filters)` method, and rewrites
`show_supported()` to call it. ADR adds a sub-section showing the
three concrete shapes (factory / renderer factory / enum) so the
implementing plan has a template.

### F3 — Peak alias system would be silently dropped

**Verdict: agree.** Today peak accepts context-local aliases like
`'pseudo-voigt'` and canonicalizes to `'cwl-pseudo-voigt'` /
`'tof-pseudo-voigt'`
([`src/easydiffraction/datablocks/experiment/categories/peak/factory.py:34`](../../../src/easydiffraction/datablocks/experiment/categories/peak/factory.py),
[`src/easydiffraction/datablocks/experiment/item/base.py:532`](../../../src/easydiffraction/datablocks/experiment/item/base.py)).
The amended mixin validated against raw factory tags, which would
have broken the alias UX. The Example CIF section was also still
showing alias values.

**User decision: B (keep aliases via per-category hook).** The mixin
gains a default-identity `_canonicalize(value, filters) -> str` hook;
`PeakBase` overrides it to call the existing `_canonicalize_peak_profile_type`
helper. CIF persists the canonical tag (so round-trips are stable
regardless of context shifts), but the Python `type` setter accepts
either alias or canonical. `show_supported()` displays both alias
and canonical for categories that have aliases (peak overrides
`show_supported()` to add a third column; other categories use the
default two-column rendering).

**Action.** ADR §4 mixin sketch gains `_canonicalize()`. ADR §6 scope
notes that categories with alias systems keep them; the mixin
provides the default-identity behaviour. Example CIF and Python
sections updated to show that `_peak.type` persists the canonical
tag while the writable `type` setter still accepts the alias.

### F4 — Two accepted ADRs missing from the amendments list

**Verdict: agree.**
[`accepted/display-ux.md`](../accepted/display-ux.md) and
[`accepted/category-owner-sections.md`](../accepted/category-owner-sections.md)
both describe `project.rendering` / `_rendering.*` as the canonical
shape, which this ADR supersedes.

**User decision: B (grep every accepted ADR for renamed identifiers).**
The grep was run for each of the renamed Python names and CIF tags
in the ADR's catalog. Beyond the two ADRs the reviewer flagged, the
grep produced four additional hits that turned out to be generic
phrasing rather than category-specific references (and therefore
need no amendment):

- [`factory-contracts.md`](../accepted/factory-contracts.md): "calculator_support for calculation-engine support" (generic phrase).
- [`test-strategy.md`](../accepted/test-strategy.md): "real calculation engines" (generic phrase).
- [`enum-backed-closed-values.md`](../accepted/enum-backed-closed-values.md): "calculators, minimizers, and rendering engines" (generic example list).
- [`project-facade-and-persistence.md`](../accepted/project-facade-and-persistence.md): "rendering preferences" (generic descriptive phrase).

**Action.** ADR's "ADRs to amend" list grows by two:
[`display-ux.md`](../accepted/display-ux.md) (the writable selector
surface for chart/table renderers and their CIF block move from
`_rendering.*` to `_chart.*`/`_table.*`) and
[`category-owner-sections.md`](../accepted/category-owner-sections.md)
(the `ProjectConfig` children list and the `_rendering` CIF block
reference). The four generic-phrase hits are mentioned in this
reply but explicitly excluded from the amendments list.

### F5 — `DEFAULT_METHOD` is module-level, not a class constant

**Verdict: agree.** Amended §3 said the engine's `DEFAULT_METHOD`
"class constant" was the restore source. The source
([`src/easydiffraction/analysis/minimizers/lmfit_leastsq.py:12`](../../../src/easydiffraction/analysis/minimizers/lmfit_leastsq.py),
[`src/easydiffraction/analysis/minimizers/bumps_lm.py:12`](../../../src/easydiffraction/analysis/minimizers/bumps_lm.py))
has `DEFAULT_METHOD = 'leastsq'` at module level, not on the class.
The contract pointed at a thing that didn't exist.

**Options:**

- **A.** Promote `DEFAULT_METHOD` to `ClassVar` on each engine
  (touches ~9 engine files).
- **B.** Construct the engine on restore via
  `MinimizerFactory.create(tag)` and read `engine.name` /
  `engine.method`.
- **C.** Class-level `_engine_metadata: ClassVar[dict[str, str]]`
  on each concrete *minimizer category* (not the engine). Restore
  reads `type(self.minimizer)._engine_metadata` directly. No engine
  construction. No engine refactor.
- **D.** Walk back F6 — keep `_minimizer.optimizer_name` /
  `_minimizer.method_name` in CIF.

**User decision: C.** The minimizer category is the right home for
"metadata about this minimizer choice" — `type_info.description`
already lives there. The class-level dict is two lines per
concrete minimizer.

**Action.** ADR §3 rewrites the optimizer_name/method_name restore
contract to say "read `type(self.minimizer)._engine_metadata` —
each concrete minimizer category class declares it as a
`ClassVar[dict[str, str]]` containing the backend's
`optimizer_name` and `method_name`". Adds an example
declaration for `LmfitLeastsqMinimizer`.

## Verification

This reply is a static one. No tests, lint, build, or `pixi` commands
were run, matching the reviewer's own constraint. Markdown files in
this review cycle were also not run through `prettier`, per the
[`.github/copilot-instructions.md`](../../../../.github/copilot-instructions.md)
→ **Change Discipline** rule on review/reply files.

Only one empirical check was run, scoped to F1: a tiny gemmi script
to confirm that a scalar tag and a loop sharing the same CIF category
prefix round-trip correctly. The script result is quoted above; no
project tests or build commands were touched.

The implementing plan (separate file, drafted only after ADR
acceptance) will include the standard Phase-2 verification suite.

## Addendum — third example-correctness fix

After the F1-F5 amendments were applied, a follow-up question
flagged that the Python `background.create(...)` line in the
Example section used the CIF tag names (`Chebyshev_order`,
`Chebyshev_coef`) as keyword arguments rather than the actual
Python attribute names (`order`, `coef`).
[`src/easydiffraction/datablocks/experiment/categories/background/chebyshev.py:101,116`](../../../src/easydiffraction/datablocks/experiment/categories/background/chebyshev.py)
defines the public properties as `order` and `coef`; the
`Chebyshev_order` / `Chebyshev_coef` spellings appear only in the
`cif_handler=CifHandler(names=[...])` arguments. The class
docstring (`chebyshev.py:39`) is explicit: "New public attribute
names: ``order`` and ``coef`` replacing the longer
``chebyshev_order`` / ``chebyshev_coef``."

This is the same class of mistake as the
`_peak.broadening_u/v/w` invention caught in Reply 1's addendum —
sloppy at the CIF↔Python boundary in example code.

**Action.** Fixed the line to
`project.experiments['hrpt'].background.create(id='1', order=0, coef=0.42)`.
A re-scan of the rest of the Example Python surface against the
source confirmed the other lines (`peak.broad_gauss_u`,
`peak.broad_lorentz_x`, `minimizer.sampling_steps`, all the
`.type` assignments) use the actual Python attribute names.

Going forward, every Python keyword argument and every CIF tag in
ADR examples is grepped from the source before it's written. The
two same-class slip-ups in two consecutive reviews suggest this
discipline needs to be a habit, not an exception.

## Summary of files touched by this reply

- [`docs/dev/adrs/accepted/switchable-category-owned-selectors.md`](../accepted/switchable-category-owned-selectors.md)
  — amended per F1-F5, plus the addendum above for the
  `background.create()` keyword-name fix.
- [`docs/dev/adrs/suggestions/switchable-category-owned-selectors_reply-2.md`](switchable-category-owned-selectors_reply-2.md)
  — this file.
