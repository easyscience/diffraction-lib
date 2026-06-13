# ADR: Switchable Category Owned Selectors

## Status

Accepted.

## Date

2026-05-23

## Group

User-facing API and CIF mapping.

## Context

Today every switchable category — `analysis.minimizer`,
`experiment.background`, `experiment.peak`, `experiment.extinction`, … —
exposes its selector at owner level per
[`switchable-category-api.md`](switchable-category-api.md):

```python
analysis.minimizer_type = 'bumps (lm)'
analysis.minimizer                          # read-only
analysis.show_supported_minimizer_types()   # method on owner
analysis.show_current_minimizer_type()      # method on owner
```

Three problems have accumulated since that ADR landed:

1. **Two-scope UX.** The category instance lives at `analysis.minimizer`
   (read-only). The thing you assign lives at `analysis.minimizer_type`
   (writable). Every supported show-method is on the owner. A scientist
   looking at `analysis.minimizer.help()` sees the configuration
   descriptors but cannot change the active backend from that surface;
   they have to go back up one level. The same split applies to
   background, peak, etc.

2. **CIF duplication and inconsistency.** The owner-level convention
   persists a tag like `_fitting.minimizer_type = 'bumps (lm)'` _and_
   the swapped category records its identity again — e.g.
   `_minimizer.optimizer_name = 'bumps (lm)'`. The two values are by
   construction equal; one of them is dead weight in every saved
   project. The codebase is also internally inconsistent in how it
   persists the active type across switchable categories:
   `_peak.profile_type` is an in-category identity tag (so picking a
   peak profile already lives entirely inside the `_peak.*` block);
   `_background.*` has no identity tag at all today — the active type is
   inferred at load time from which `_pd_background.*` loop columns are
   present; `_fitting.minimizer_type` lives in the owner-level
   `_fitting.*` block separately from the `_minimizer.*` block that the
   swapped category writes; `_calculation.calculator_type` lives inside
   its category block but the descriptor name awkwardly repeats the noun
   ("calculator") instead of using a uniform `.type` selector.
   [`python-cif-category-correspondence.md`](python-cif-category-correspondence.md)
   notes the inconsistency under §"Owner-level switchable selectors" and
   tags it for a future ADR.

3. **Cross-cutting inconsistency.** Issue [#76](../../issues/closed/consistent-type-suffix-in-switchable-category-api-names.md)
   ("Consistent `_type` suffix in switchable-category API names")
   tracked the inconsistency in the _method names_ on the owner, but
   assumed the owner-level model stayed.
   [`fit-mode-categories.md`](fit-mode-categories.md) §"Deferred Work"
   explicitly records:

   > "A separate ADR for changing switchable category selectors globally
   > from owner-level names such as `peak_profile_type` toward
   > category-owned selectors such as `peak.profile_type`."

   This ADR is that follow-up.

The
[`minimizer-category-consolidation.md`](minimizer-category-consolidation.md)
work just landed; it intentionally preserved `_fitting.minimizer_type`
because the broader convention had not yet been amended. With that PR
merged, the path is clear to amend the convention now.

## Decision

### 1. The category owns its selector

Every in-scope selector category — across all three mechanism families
recognised by [`selector-families.md`](selector-families.md) (A
switchable categories, B backend selectors, C active-sibling selectors)
— exposes the same writable surface:

```python
category.type             # writable property (str)
category.show_supported() # one method, current marked with '*'
```

That is the entire public selector surface. Nothing else. Setting
`category.type = 'X'` delegates to the owner's `_swap_<name>` hook; what
happens behind that hook depends on the family — the owner replaces the
category instance (Family A), rebinds the live engine behind a singleton
category (Family B), or activates / deactivates sibling categories
(Family C). The user-facing API does not change with the mechanism. See
§6 for the full scope and the mechanism-vs- surface framing.

Owner-level shims are removed (no `<owner>.<cat>_type`, no
`show_supported_<cat>_types()`, no `show_current_<cat>_type()`). The
owner exposes only the category itself, e.g. `analysis.minimizer`.

Exception: an internally paired category whose concrete class is fully
determined by another category's `type` may omit its own public
selector. Today this applies only to `analysis.fit_result`, whose class
is derived from `analysis.minimizer.type` by the
[`minimizer-input-output-split.md`](minimizer-input-output-split.md)
ADR. It has no `fit_result.type`, no `fit_result.show_supported()`, and
no `_fit_result.type` CIF tag.

The owner still owns the swap mechanism (it holds the slot) but the swap
is _initiated_ from the category through a back-reference.

### 2. `show_current()` is intentionally omitted

`category.show_supported()` marks the active type with `'*'` in its
table, so a dedicated "show current" method would print a strict subset
of the same information. The machine-readable accessor is
`category.type`. Three paths cover every reasonable user need:

| User wants                         | API                         |
| ---------------------------------- | --------------------------- |
| The active type as a string        | `category.type`             |
| The active type printed            | `print(category.type)`      |
| The full table, active row starred | `category.show_supported()` |

A separate `show_current()` method is therefore not added, and the
existing owner-level `show_current_<cat>_type()` methods are removed in
step with the rest of this ADR.

### 3. CIF mapping is collapsed to one `_<cat>.type` tag per category

Every selector — across all three families that present a writable type
surface — persists exactly one identity tag, `_<cat>.type`. Owner-level
selector tags are dropped. Per-category identity-echo tags are renamed
to the uniform spelling. Three CIF block names are new (`_chart`,
`_table`, `_calculator`) because the `Rendering` category is split and
the `Calculation` category is renamed (see §8); one is new
(`_fitting_mode`) because the active-sibling selector is promoted to its
own category (also §8).

| Today                                 | Replacement             | Mechanism family ¹ |
| ------------------------------------- | ----------------------- | ------------------ |
| `_fitting.minimizer_type`             | `_minimizer.type`       | A                  |
| `_peak.profile_type`                  | `_peak.type`            | A                  |
| (none — only `_pd_background.*` loop) | `_background.type`      | A                  |
| (none — only active-class fields)     | `_extinction.type`      | A                  |
| `_calculation.calculator_type`        | `_calculator.type`      | B (and §8 rename)  |
| `_rendering.chart_engine`             | `_rendering_plot.type`  | B (and §8 split)   |
| `_rendering.table_engine`             | `_rendering_table.type` | B (and §8 split)   |
| `_fitting.mode_type`                  | `_fitting_mode.type`    | C (and §8 promote) |

¹ Mechanism family per [`selector-families.md`](selector-families.md): A
swaps the category instance, B swaps the live engine behind a singleton
category, C activates or deactivates sibling categories. The user-
facing CIF and Python surface is **identical** across all three.

After the consolidation: the `_fitting.*` and `_rendering.*` CIF blocks
**disappear entirely**. `_fitting` was a heterogeneous bag holding two
unrelated selectors; `_rendering` did the same. Both are split into
single-purpose blocks aligned with the new `_<cat>.type` rule.

`_minimizer.optimizer_name` and `_minimizer.method_name` are also
**dropped**. Inspecting
[`src/easydiffraction/analysis/minimizers/lmfit_leastsq.py`](../../../src/easydiffraction/analysis/minimizers/lmfit_leastsq.py)
(and the matching `bumps_lm.py`, `dfols.py`, …) shows that `name`
defaults to the enum tag itself and `method` to a per-engine
module-level constant. The public API never overrides them at
construction. So the persisted values are deterministic functions of the
tag, not independent observations — exactly the duplication that
motivated the ADR.

The runtime `FitResults.optimizer_name` and `FitResults.method_name` are
derived on restore from a class-level metadata dict declared on each
concrete minimizer category:

```python
class LmfitLeastsqMinimizer(LeastSquaresMinimizerBase):
    type_info = TypeInfo(
        tag='lmfit (leastsq)',
        description='LMFIT library with Levenberg-Marquardt least squares method',
    )
    _engine_metadata: ClassVar[dict[str, str]] = {
        'optimizer_name': 'lmfit (leastsq)',
        'method_name': 'leastsq',
    }
```

Restore reads `type(self.minimizer)._engine_metadata` — no engine
instance construction is needed, and the engine modules themselves do
not need to grow class-level mirrors of their module-level
`DEFAULT_METHOD` constants. The dict lives on the category class where
`type_info.description` already lives, keeping all per-tag metadata in
one place. [`analysis-cif-fit-state.md`](analysis-cif-fit-state.md) is
amended to drop these two fields from the persisted projection and to
point at the class-level dict as the new restore source.

### 4. Mechanism: behavior-only mixin + parent-side swap hook

`SwitchableCategoryBase` is a **behavior-only mixin**, not an
intermediate in the storage hierarchy. It carries no descriptor
instances and does no `__init__` work, which keeps it compatible with
both singleton categories (extending `CategoryItem`) and
collection-shaped categories (extending `CategoryCollection`):

```python
class MinimizerCategoryBase(CategoryItem, SwitchableCategoryBase): ...
class PeakBase(CategoryItem, SwitchableCategoryBase): ...
class ExtinctionBase(CategoryItem, SwitchableCategoryBase): ...
class BackgroundBase(CategoryCollection, SwitchableCategoryBase): ...
```

This is consistent with
[`minimizer-category-consolidation.md`](minimizer-category-consolidation.md)
§8 "no mixins" — that rule rejects mixins **for descriptor
declarations**; behavior mixins are allowed (the
`LeastSquaresMinimizerBase` / `BayesianMinimizerBase` intermediates
introduced in P1.4 are the precedent).

The mixin itself:

```python
class SwitchableCategoryBase:
    """Behavior-only mixin for instance-swap switchable categories."""

    _parent: object | None = None
    _category_code: ClassVar[str]            # e.g. 'minimizer'
    _owner_attr_name: ClassVar[str]          # e.g. 'minimizer'
    _swap_method_name: ClassVar[str]         # e.g. '_swap_minimizer'

    @property
    def type(self) -> str:
        """Active factory tag for this category."""
        return self._type.value

    @type.setter
    def type(self, value: str) -> None:
        if self._parent is None:
            msg = (
                f'{type(self).__name__} is detached; '
                'cannot change type on a stale instance.'
            )
            raise RuntimeError(msg)
        live = getattr(self._parent, self._owner_attr_name)
        if live is not self:
            msg = (
                f'{type(self).__name__} is no longer the live '
                f'category on its owner; obtain a fresh reference '
                f'via owner.{self._owner_attr_name}.'
            )
            raise RuntimeError(msg)
        canonical = self._canonicalize(value)
        getattr(self._parent, self._swap_method_name)(canonical)

    def _canonicalize(self, value: str) -> str:
        """Resolve a user-supplied tag to its canonical factory tag.

        Default: identity. Categories with a context-local alias
        system (currently `peak` only) override this to map aliases
        such as ``'pseudo-voigt'`` to canonical tags such as
        ``'cwl-pseudo-voigt'`` using the owner's context (beam mode).
        CIF persists the canonical tag, so round-trips are stable
        regardless of context shifts. See §"Aliases" below.
        """
        return value

    def _supported_types(
        self, filters: dict[str, object]
    ) -> list[tuple[str, str]]:
        """Return ``[(tag, description), ...]`` for supported types.

        Subclasses MUST implement. The mixin's ``show_supported()``
        renders the returned pairs into a table. Three concrete
        shapes coexist depending on what backs the category — a
        domain factory, a renderer factory, or a plain enum (see
        §"Three supported-type shapes" below).
        """
        raise NotImplementedError

    def show_supported(self) -> None:
        """Show supported types for this category.

        Renders one ``['*', tag, description]`` row per supported
        type, with the currently active type marked ``'*'``. The
        owner contributes only a filter dict (calculator, beam mode,
        …); rendering itself lives here so the table shape is
        uniform across every switchable in the project.
        """
        filters = (
            self._parent._supported_filters_for(self)
            if self._parent is not None
            else {}
        )
        current = self.type
        columns_data = [
            ['*' if tag == current else '', tag, description]
            for tag, description in self._supported_types(filters)
        ]
        console.paragraph(f'{type(self).__bases__[0].__name__} types')
        render_table(
            columns_headers=['', 'Type', 'Description'],
            columns_alignment=['left', 'left', 'left'],
            columns_data=columns_data,
        )
```

#### Three supported-type shapes

The mixin's `_supported_types()` is abstract because the project hosts
three different backings for switchable categories. Each concrete base
picks the shape that matches its backing — two or three lines, no
abstraction in the mixin itself.

```python
# Shape 1 — domain factories (FactoryBase API):
# minimizer, peak, background, extinction, calculator
class MinimizerCategoryBase(CategoryItem, SwitchableCategoryBase):
    def _supported_types(self, filters):
        return [
            (cls.type_info.tag, cls.type_info.description)
            for cls in MinimizerCategoryFactory.supported_for(**filters)
        ]

# Shape 2 — renderer factories (RendererFactoryBase API):
# chart, table. The 'auto' sentinel is part of the supported set
# alongside the concrete engines, so it appears as a row in the
# table and gets the '*' mark when chart.type / table.type is
# currently 'auto' (which is the default value per
# CHART_ENGINE_OPTIONS / TABLE_ENGINE_OPTIONS).
class ChartBase(CategoryItem, SwitchableCategoryBase):
    _auto_description: ClassVar[str] = (
        'Pick a backend automatically based on environment'
    )

    def _supported_types(self, filters):
        # PlotterFactory.descriptions() returns list[tuple[str, str]]
        # already in (engine, description) shape.
        return [('auto', self._auto_description), *PlotterFactory.descriptions()]

# Shape 3 — plain enum (no factory): fitting_mode
class FittingModeBase(CategoryItem, SwitchableCategoryBase):
    def _supported_types(self, filters):
        return [(mode.value, mode.description()) for mode in FitModeEnum]
```

The five Shape-1 categories share an identical body; if duplication
becomes a problem in implementation, factor it into a small base helper.
The two Shape-2 categories also share an identical body. Shape 3 has
exactly one user. No upstream changes to factories or enums are
required.

#### Aliases

Categories with a context-local alias system (currently `peak` only)
override `_canonicalize()` to resolve user-supplied aliases to canonical
factory tags. The setter applies canonicalization before delegating to
the owner's swap hook, so the underlying descriptor and the persisted
CIF tag are always canonical:

```python
class PeakBase(CategoryItem, SwitchableCategoryBase):
    def _canonicalize(self, value: str) -> str:
        beam_mode = self._parent.type.beam_mode.value
        return _canonicalize_peak_profile_type(value, beam_mode)
```

`show_supported()` defaults to two-column rendering (tag, description).
Categories that want to show aliases alongside canonical tags (peak)
override `show_supported()` to add a third column; the per-category
override pattern is the same as the existing
[`base.show_peak_profile_types()`](../../../src/easydiffraction/datablocks/experiment/item/base.py)
implementation, just moved onto the category.

`type` is backed by a **real `StringDescriptor`** named `_type` that
each concrete-base `__init__` constructs with
`cif_handler=CifHandler(names=[f'_{category_code}.type'])` and a
membership validator over the factory's supported tags. The descriptor
is what serializes; the property is the user-facing writable hook with
the staleness checks.

For `CategoryItem` substrates (minimizer, peak, extinction, calculator,
chart, table, fitting_mode) the generic CIF emit/read path
[`io/cif/serialize.py:170`](../../../src/easydiffraction/io/cif/serialize.py)
picks the descriptor up by name automatically — no custom hook is
needed. For the `CategoryCollection` substrate (background only),
[`category.py:230`](../../../src/easydiffraction/core/category.py)'s
`parameters` returns only loop-item parameters and
[`io/cif/serialize.py:244`](../../../src/easydiffraction/io/cif/serialize.py)
writes only the loop, so a collection-level `_type` descriptor needs a
small additional path: the writer emits the scalar tag above the loop,
and the reader peeks the scalar before iterating items. This is a
**one-time generalization of the collection serializer** to support
collection-level scalar descriptors that sit alongside the loop; the
change is reusable by any future collection-shaped switchable.

CIF format note. The CIF specification allows scalar tags and loop tags
to share a category prefix in the same block as long as no individual
tag is duplicated; gemmi handles this correctly (verified empirically by
reading a `_background.type chebyshev` scalar alongside a
`_background.Chebyshev_order` / `_background.Chebyshev_coef` loop in the
same block — see Reply 2 F1 for the test script). The collection-shaped
`background` row of the catalog therefore persists the scalar selector
on `_background.type` while the existing loop columns stay on their
current `_pd_background.*` prefix (IUCr pd_CIF convention); the Python
`BackgroundBase` collection owns both CIF prefixes — one for its scalar
selector, one for its row data.

The owner provides two private hooks per switchable category. First, a
`_swap_<name>` method that performs the swap and **detaches the old
instance** before installing the new one, so a stale reference cannot
accidentally re-trigger another swap. Second, a single
`_supported_filters_for(category)` dispatch that returns the filter dict
for any of the owner's categories:

```python
class Analysis:
    def _swap_minimizer(self, new_type: str) -> None:
        new_minimizer = MinimizerCategoryFactory.create(new_type)
        self._warn_about_minimizer_swap_defaults(
            self._minimizer, new_minimizer,
        )
        self._minimizer._parent = None       # detach old
        new_minimizer._parent = self
        self._minimizer = new_minimizer
        self._fitter = Fitter(new_type)

    def _supported_filters_for(
        self, category: SwitchableCategoryBase
    ) -> dict[str, object]:
        # analysis switchables have no context filters today
        return {}


class ExperimentBase:
    def _supported_filters_for(self, category):
        calculator = self.calculator.type
        if category is self.background:
            return {'calculator': calculator}
        if category is self.extinction:
            return {'calculator': calculator}
        if category is self.peak:
            return {
                'calculator': calculator,
                'scattering_type': self.type.scattering_type.value,
                'sample_form': self.type.sample_form.value,
                'beam_mode': self.type.beam_mode.value,
            }
        return {}
```

The existing owner-level `show_<cat>_types()` methods
([`bragg_pd.show_background_types()`](../../../src/easydiffraction/datablocks/experiment/item/bragg_pd.py),
[`base.show_peak_profile_types()`](../../../src/easydiffraction/datablocks/experiment/item/base.py),
`Calculation.show_calculator_types()`,
`Analysis.show_supported_minimizer_types()`, …) are **deleted**. The
mixin's `show_supported()` reproduces the same `['*', tag, description]`
table shape that all of them produce today, so the user-facing output is
unchanged; only the entry point moves from the owner onto the category.
Owners contribute only the filter dict via
`_supported_filters_for(category)`.

The Family-B swap hooks (e.g. `Experiment._swap_calculator`,
`Project._swap_rendering_plot`, `Project._swap_rendering_table`) follow
the same shape but rebind the live engine rather than the category
instance. The Family-C swap hook (`Analysis._swap_fitting_mode`)
performs the existing sibling-activation logic. The mixin does not care
which mechanism the owner uses; it only routes the writable surface.

CIF read path becomes:

1. Owner peeks `_<cat>.type` from the CIF block.
2. Owner calls `_swap_<name>(value)` to install the matching concrete
   class — its `_type` descriptor is now initialised to the persisted
   value.
3. Generic CIF deserialization populates the remaining descriptors on
   the newly-installed instance.

This is the same shape as
[`minimizer-category-consolidation.md`](minimizer-category-consolidation.md)
P1.7's peek-then-populate flow; the only change is that the type tag
lives inside the category's own namespace.

### 5. Stale-reference safety

After a swap the old instance is **detached** (`_parent = None`), and
the `type` setter checks both attachment and slot liveness (see §4). Two
stale-reference scenarios collapse to a clear error rather than silent
mutation:

```python
m = project.analysis.minimizer        # binds to instance A
project.analysis.minimizer.type = 'bumps (dream)'   # A is detached, B installed
m.type = 'lmfit'                       # ⇒ RuntimeError: detached / stale
```

Descriptor writes on the detached instance (`m.sampling_steps = 3000`)
still mutate the orphan — that is the unavoidable Python semantics for
any held reference — but the **type-swap path** is now safe from
re-triggering the parent. The intended scientist workflow goes through
the live property each time:

```python
project.analysis.minimizer.type = 'bumps (dream)'
project.analysis.minimizer.sampling_steps = 3000
```

A future refactor could additionally emit a `log.warn(...)` from
descriptor setters on detached instances (so even
`m.sampling_steps = 3000` flags the stale-orphan write); the design is
recorded as a follow-up but is not part of this ADR.

### 6. Scope: every selector that presents a writable type surface

This ADR applies to every selector whose public Python surface is "set a
type / pick from a supported list", regardless of what happens behind
the setter. Three mechanism families per
[`selector-families.md`](selector-families.md) all present the **same**
writable `category.type` surface and the same
`category.show_supported()` API; the mechanism differs only in what the
owner's `_swap_<name>` hook does behind that surface.

**In scope:**

- **Family A — switchable-category selectors:** `minimizer`,
  `background`, `peak` (currently exposed as `peak_profile`),
  `extinction`. Owner's `_swap_<name>` replaces the category instance
  via the matching factory.
- **Family B — backend selectors:** `calculator` (today the
  awkwardly-named `experiment.calculation.calculator_type`; the Python
  class `Calculation` is renamed to `Calculator` and the category
  attribute moves from `experiment.calculation` to
  `experiment.calculator` — see §8c), `chart` and `table` (split out of
  the current `rendering` category — see §8a). Owner's `_swap_<name>`
  keeps the category singleton and rebinds the live engine instead. The
  user-facing API surface is identical to Family A.
- **Family C — active-sibling selector:** `fitting_mode` (today the bare
  `analysis.fitting_mode_type` descriptor; promoted to its own small
  `FittingMode` category — see §8). Owner's `_swap_<name>` activates /
  deactivates sibling categories (`joint_fit` / `sequential_fit` /
  `sequential_fit_extract`) based on the new value. The user-facing API
  surface is identical to Family A.

The categories with a single factory tag and no second concrete type
registered today (e.g. `aliases`, `constraints`, `cell`, `space_group`,
…) are not in scope. They inherit the convention automatically when a
second type is added.

**Out of scope:**

- **Plain enum descriptors:** `experiment.type.sample_form`,
  `experiment.type.beam_mode`, `experiment.type.radiation_probe`,
  `experiment.type.scattering_type` (creation-time axes per
  [`immutable-experiment-type.md`](immutable-experiment-type.md));
  `atom_site.adp_type` (governed by
  [`type-neutral-adp-parameters.md`](type-neutral-adp-parameters.md));
  `extinction.becker-coppens.model` (a closed-set enum nested inside the
  Family-A `extinction` category — local to the selected extinction
  class). These select a value, not a type or backend, and do not
  present a `.type` writable surface.

The plan that implements this ADR enumerates the exact set of affected
categories and their swap hooks at the start of Phase 1.

### 7. Beta posture: hard cutover, no shims

[`AGENTS.md`](../../../../AGENTS.md) → **Change Discipline**: "Project
is in beta: no legacy shims, no deprecation warnings — update tests and
tutorials to the current API." This ADR keeps that posture:

- `<owner>.<cat>_type` is **deleted**, not deprecated.
- `show_supported_<cat>_types()` / `show_current_<cat>_type()` are
  deleted.
- Owner-level CIF selector tags are deleted.
- Identity-echo CIF fields are deleted.
- Every tutorial, test, and example CIF is migrated.

Existing saved projects under `tmp/tutorials/projects/*` regenerate from
script tests, matching the precedent set by
[`minimizer-category-consolidation.md`](minimizer-category-consolidation.md).

### 8. Three structural changes beyond pure renames

Three selectors need structural changes to fit the `category.type` rule
under [`category-parameter-access.md`](category-parameter-access.md)'s
two-level parameter access (`datablock.category.parameter`) and the
"category name matches the noun of the thing being selected" convention
shared by every other in-scope category (`minimizer`, `peak`,
`background`, …).

#### 8a. `Rendering` → `Chart` + `Table`

Today `project.rendering` is a single category holding two engine
selectors (`chart_engine`, `table_engine`) plus two live facades
(`plotter`, `tabler`). The two-level rule blocks
`project.rendering.chart.type` and `project.rendering.table.type` (three
levels).

The `Rendering` category is **removed**. Two new sibling categories
appear on `Project`:

- `project.rendering_plot` — `CategoryItem` with one writable selector
  `type` (`PlotterEngineEnum` plus the `'auto'` sentinel) and the live
  `Plotter` facade as a private internal. CIF block:
  `_rendering_plot.*`.
- `project.rendering_table` — `CategoryItem` with one writable selector
  `type` (`TableEngineEnum` plus `'auto'`) and the live `TableRenderer`
  facade as a private internal. CIF block: `_rendering_table.*`.

Both follow the §4 mechanism — Family B (engine swap), `category.type`
surface — and become natural homes for future chart-only and table-only
descriptors (e.g. `chart.height`, `chart.theme`, `table.max_rows`,
`table.precision`).

The owner-level `project.rendering.show_chart_engines()`,
`project.rendering.show_table_engines()`, and
`project.rendering.show_config()` methods are deleted. Their
replacements are `project.rendering_plot.show_supported()`,
`project.rendering_table.show_supported()`, and (if needed) a thin
`project.show_config()` that prints both categories' current state.

#### 8b. `analysis.fitting_mode_type` → `analysis.fitting_mode.type`

Today `analysis.fitting_mode_type` is a bare `FitModeEnum` descriptor
sitting directly on `Analysis`. Not a category. The two-level rule
permits `analysis.fitting_mode.type` if we promote it.

A new minimal `FittingMode` category is added under `Analysis`:

- One descriptor: `type` (`FitModeEnum`-valued, defaults to
  `FitModeEnum.SINGLE`).
- One swap hook on the owner: `Analysis._swap_fitting_mode(new_value)`
  which performs the existing sibling-activation work (controls which of
  `joint_fit` / `sequential_fit` / `sequential_fit_extract` is visible
  to `help()`, written by the serialiser, and used at fit time).
- CIF block: `_fitting_mode.*` (currently `_fitting.mode_type`).

Today the category has only one descriptor. Future mode-wide settings
(e.g. parallel-independent-fit knobs from open issue #89) have a natural
home there. The "don't introduce abstractions before a second concrete
use" rule from CLAUDE.md is satisfied here because the abstraction we
are introducing is the **uniform `category.type` surface across the
project**, not a one-off `FittingMode` class.

#### 8c. `Calculation` → `Calculator`

Today `experiment.calculation` is a singleton category holding one
descriptor named `calculator_type` (CIF tag
`_calculation.calculator_type`). The category name does not match the
thing being selected — every other in-scope category is named after the
noun whose type is chosen (`minimizer`, `peak`, `background`,
`extinction`, `chart`, `table`, `fitting_mode`). The mismatched name is
the only reason the descriptor is called `calculator_type` rather than
`type`.

The Python class `Calculation` is renamed to `Calculator`. The
owner-side attribute moves from `experiment.calculation` to
`experiment.calculator`. The single writable selector becomes
`experiment.calculator.type`. The CIF block becomes `_calculator.*`. The
live calculator engine (which today is held on `experiment._calculator`
and rebound by `ExperimentBase._set_calculator_type`) keeps its current
binding — this is a Family-B engine-swap mechanism; only the user-facing
surface and the CIF block name change.

Affected ADRs: this rename adds a small amendment to
[`python-cif-category-correspondence.md`](python-cif-category-correspondence.md)
(category and CIF tag both move from `calculation` to `calculator`) and
to [`selector-families.md`](selector-families.md) (the example row for
Family B).

After all three structural changes the `_fitting.*`, `_rendering.*`, and
`_calculation.*` CIF blocks disappear from saved projects. All three
were either heterogeneous bags (`_fitting`, `_rendering`) or mis-named
singletons (`_calculation`); the new layout has one selector per block,
aligned with the descriptor it persists and the noun it names.

## Catalog of selectors across the codebase

After this ADR every selector that presents a writable type surface
follows the **same** `category.type` shape, regardless of mechanism
family. The single in-scope table below covers all eight; the mechanism
column distinguishes what happens behind the setter (A = category
instance swap, B = engine swap, C = sibling activation). Plain enum
descriptors (Family D) keep their existing form and are listed in a
separate, smaller table.

### In scope — every selector with a writable type surface

| #   | Owner      | Today                                          | Proposed Python                      | CIF today                               | CIF proposed            | Mech           | Source                                            |
| --- | ---------- | ---------------------------------------------- | ------------------------------------ | --------------------------------------- | ----------------------- | -------------- | ------------------------------------------------- |
| 1   | analysis   | `analysis.minimizer_type = 'X'`                | `analysis.minimizer.type = 'X'`      | `_fitting.minimizer_type`               | `_minimizer.type`       | A              | `analysis/analysis.py:1022`                       |
| 2   | experiment | `experiment.peak_profile_type = 'X'`           | `experiment.peak.type = 'X'`         | `_peak.profile_type`                    | `_peak.type`            | A              | `experiment/item/base.py:514`                     |
| 3   | experiment | `experiment.background_type = 'X'`             | `experiment.background.type = 'X'`   | (none — only `_pd_background.*` loop)   | `_background.type`      | A              | `experiment/item/bragg_pd.py:184`                 |
| 4   | experiment | `experiment.extinction_type = 'X'`             | `experiment.extinction.type = 'X'`   | (none — only active class's own fields) | `_extinction.type`      | A              | `experiment/item/base.py:312`                     |
| 5   | experiment | `experiment.calculation.calculator_type = 'X'` | `experiment.calculator.type = 'X'`   | `_calculation.calculator_type`          | `_calculator.type`      | B + §8 rename  | `experiment/categories/calculation/default.py:50` |
| 6   | project    | `project.rendering.chart_engine = 'X'`         | `project.rendering_plot.type = 'X'`  | `_rendering.chart_engine`               | `_rendering_plot.type`  | B + §8 split   | `project/categories/rendering/default.py:100`     |
| 7   | project    | `project.rendering.table_engine = 'X'`         | `project.rendering_table.type = 'X'` | `_rendering.table_engine`               | `_rendering_table.type` | B + §8 split   | `project/categories/rendering/default.py:109`     |
| 8   | analysis   | `analysis.fitting_mode_type = 'X'`             | `analysis.fitting_mode.type = 'X'`   | `_fitting.mode_type`                    | `_fitting_mode.type`    | C + §8 promote | `analysis/analysis.py:960`                        |

Mechanism legend (recap):

- **A (instance swap):** owner's `_swap_<name>` calls
  `Factory.create(value)` and rebinds the slot.
- **B (engine swap):** owner's `_swap_<name>` keeps the singleton
  category, rebinds the live engine behind it (Plotter, TableRenderer,
  calculator backend).
- **C (sibling activation):** owner's `_swap_<name>` records the new
  `FitModeEnum` value and updates which sibling categories are visible,
  authoritative, and serialised.

The user-facing Python and CIF columns are uniform across all eight.
Implementers and reviewers can read every row from a single template.

Notes on the in-scope rows:

- Rows 1–4 are pure renames + the structural moves in §3 (Python
  selector onto the category; CIF tag onto `_<cat>.type`).
- Row 5 involves §8c's `Calculation` → `Calculator` rename: the Python
  class is renamed, the owner-side attribute moves from
  `experiment.calculation` to `experiment.calculator`, the descriptor is
  renamed `calculator_type` → `type`, and the CIF block changes from
  `_calculation.*` to `_calculator.*`. The setter delegation pattern is
  already in place today
  ([`calculation/default.py:61`](../../../src/easydiffraction/datablocks/experiment/categories/calculation/default.py)),
  so no mechanism change is required.
- Rows 6 and 7 involve §8a's `Rendering` → `Chart` + `Table` split
  (Python category restructure, CIF block split).
- Row 8 involves §8b's `FittingMode` promotion (new minimal category on
  `Analysis`, CIF block rename).

### Out of scope — plain enum descriptors (Family D)

Closed-set string descriptors with a `MembershipValidator`. Selecting a
value records a choice and may trigger bookkeeping, but does not present
the `category.type` writable surface and does not swap a category,
engine, or sibling.

| #   | Python                                                                       | CIF                          | Effect                                                                                                           | Source                                                  |
| --- | ---------------------------------------------------------------------------- | ---------------------------- | ---------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------- |
| 1   | `experiment.type.sample_form`                                                | `_expt_type.sample_form`     | Powder vs single-crystal; creation-time axis.                                                                    | `experiment/categories/experiment_type/default.py:104`  |
| 2   | `experiment.type.beam_mode`                                                  | `_expt_type.beam_mode`       | CWL vs TOF; creation-time axis.                                                                                  | `…/experiment_type/default.py:114`                      |
| 3   | `experiment.type.radiation_probe`                                            | `_expt_type.radiation_probe` | Neutron vs X-ray; creation-time axis.                                                                            | `…/experiment_type/default.py:124`                      |
| 4   | `experiment.type.scattering_type`                                            | `_expt_type.scattering_type` | Bragg vs total scattering; creation-time axis.                                                                   | `…/experiment_type/default.py:134`                      |
| 5   | `atom_site.adp_type` (per row of `structure.atom_sites`)                     | `_atom_site.adp_type`        | Pick ADP convention (`Biso`/`Uiso`/`Bani`/`Uani`); triggers value conversion and `atom_site_aniso` sibling sync. | `structure/categories/atom_sites/default.py:377`        |
| 6   | `extinction.becker-coppens.model` (nested inside in-scope row 4 when active) | `_extinction.model`          | Mosaicity distribution (`gauss`/`lorentz`) inside the Becker-Coppens extinction category.                        | `experiment/categories/extinction/becker_coppens.py:92` |
| 7   | `project.verbosity.fit`                                                      | `_verbosity.fit`             | Pick fit-output verbosity (`full`/`short`/`silent`).                                                             | `project/categories/verbosity/default.py:43`            |

Notes on Family D:

- Rows 1–4 are creation-time axes governed by
  [`immutable-experiment-type.md`](immutable-experiment-type.md); no
  user-facing writable setter, listed only for completeness.
- Row 5 (`adp_type`) has Family-C-like side effects per
  [`type-neutral-adp-parameters.md`](type-neutral-adp-parameters.md).
  Stays.
- Row 6 (`extinction.becker-coppens.model`) is a Family-D enum
  **inside** an in-scope Family-A category (extinction). Selecting the
  model is local to the Becker-Coppens class; selecting the extinction
  class itself goes through the new `experiment.extinction.type`
  surface. Both work independently.

### Categories with a `_type` slot but no observable selector (informational)

Many categories store a private
`self._<x>_type: str = Factory.default_tag()` but only one concrete type
is registered (`default`), so no public `_type` property, no
`show_supported_*` method, and no observable selector exist. Examples:
`aliases`, `constraints`, `cell`, `space_group`, `atom_sites`,
`atom_site_aniso`, `diffrn`, `linked_crystal`, `linked_phases`,
`excluded_regions`, `data`, `instrument`, `refln`, `sequential_fit`,
`sequential_fit_extract`.

If a second concrete type is ever registered for one of these, this
ADR's rule applies automatically: the category becomes an in-scope
member and exposes `category.type` plus `category.show_supported()`.

## Consequences

### Architecture wins

- One uniform API surface per category: `type`, `show_supported()`, and
  the category's own descriptors. No two-scope split.
- `category.help()` becomes self-contained: it lists every property the
  user can read or write _for that category_, including the type
  selector. Discoverability is single-step.
- CIF projects shrink by one tag per switchable category plus any
  redundant identity-echo fields. The remaining `_<cat>.*` block is a
  self-describing record of the active backend's state.
- The convention extends naturally to future switchable categories.
  Adding emcee, a new background flavor, a new peak profile, etc. costs
  one class plus factory registration; no owner-side selector plumbing.

### Trade-offs

- Reference-staleness is a real but documented quirk (see §5). The
  scientist workflow does not hit it; expert users who store a reference
  and then swap have a documented gotcha.
- The migration is cross-cutting. Every test, tutorial, and saved
  fixture that touches a switchable selector needs an edit. Order of
  magnitude: dozens of test files, every tutorial, every saved
  `analysis.cif` / `experiment.cif`.
- Two beta-period CIF formats coexist briefly (consolidation just
  shipped). Anyone with projects saved in the post-consolidation format
  needs to regenerate; the project's beta posture covers this.

### ADRs that need to be updated when this ADR is accepted

- [`switchable-category-api.md`](switchable-category-api.md) — rewrite
  the §"Decision" to point at this ADR. The new contract is "the
  category exposes `type` (getter+setter) and `show_supported()`; the
  owner exposes only the category itself".
- [`selector-families.md`](selector-families.md) — rewrite the
  §"Decision" to use the mechanism-vs-surface framing from §6: all three
  families (A switchable categories, B backend selectors, C
  active-sibling selectors) present the same writable `category.type`
  surface; the family classification documents only what the owner's
  `_swap_<name>` does behind that surface. Update every "Examples" row
  to the proposed `<owner>.<cat>.type` form.
- [`fit-mode-categories.md`](fit-mode-categories.md) — strike the
  matching "Deferred Work" entry (this ADR closes the follow-up).
  Replace the `analysis.fitting_mode_type` description with
  `analysis.fitting_mode.type` and document the new `FittingMode`
  category (§8b).
- [`python-cif-category-correspondence.md`](python-cif-category-correspondence.md)
  — the §"Owner-level switchable selectors" table becomes obsolete;
  remove the "deliberate abstraction" exception. Update every entry to
  the `_<cat>.type` form.
- [`minimizer-category-consolidation.md`](minimizer-category-consolidation.md)
  — append a "Superseded selector layout" note pointing here for the
  `_fitting.minimizer_type` → `_minimizer.type` change and the drop of
  `_minimizer.optimizer_name` / `_minimizer.method_name`.
- [`analysis-cif-fit-state.md`](analysis-cif-fit-state.md) — drop
  `_minimizer.optimizer_name` and `_minimizer.method_name` from the
  persisted projection (§3 of this ADR). The runtime
  `FitResults.optimizer_name` / `method_name` fields are populated on
  restore from the active minimizer class's metadata rather than from
  CIF.
- [`display-ux.md`](display-ux.md) — replace every reference to
  `project.rendering`, `_rendering.chart_engine`, and
  `_rendering.table_engine` with the post-§8a shape:
  `project.rendering_plot.type`, `project.rendering_table.type`, CIF
  blocks `_rendering_plot.*` and `_rendering_table.*`. Drop the
  writable-selector contract that puts chart/table engines on the
  `rendering` category; document instead that each renderer lives on its
  own category with the canonical `category.type` surface.
- [`category-owner-sections.md`](category-owner-sections.md) — update
  the `ProjectConfig` children list: drop `Rendering`; add `Chart` and
  `Table` as siblings. Update the `_rendering.*` CIF block reference to
  `_rendering_plot.*` and `_rendering_table.*`.

(A grep against `docs/dev/adrs/accepted/` for the renamed Python names
and CIF tags surfaced four additional hits that turned out to be generic
phrasing — "rendering engines", "real calculation engines",
"calculator_support for calculation-engine support", "rendering
preferences" — rather than category-specific references. Those four ADRs
(`factory-contracts.md`, `test-strategy.md`,
`enum-backed-closed-values.md`, `project-facade-and-persistence.md`) are
unaffected and intentionally not listed here. See Reply 2 F4 for the
full grep results.)

### Issues that this ADR closes

- [#72 "Warn on All Switchable-Category Type Changes"](../../issues/closed/warn-on-all-switchable-category-type-changes.md)
  — the warning logic moves into each owner's `_swap_<name>` method;
  uniform by construction.
- [#76 "Consistent `_type` suffix in switchable-category API names"](../../issues/closed/consistent-type-suffix-in-switchable-category-api-names.md)
  — superseded; the new convention drops the suffix entirely.

## Alternatives Considered

### A. `__class__` mutation on the existing instance

Replace `self.__class__` with the new concrete class so the user's
reference keeps pointing at "the same object". Rejected:
[`AGENTS.md`](../../../../AGENTS.md) → **Architecture** forbids it ("no
monkey-patching or runtime class mutation"). It would also confuse
`isinstance` checks and break descriptor introspection.

### B. Single category class with internal mode switching

One `MinimizerCategory` class with a `type` attribute that reconfigures
internal state. Rejected: conflicts with
[`minimizer-category-consolidation.md`](minimizer-category-consolidation.md)
§8 ("concrete classes carry their own defaults; no mixins"). Loses
per-backend type signatures and `help()` output.

### C. Proxy / handle layer

`analysis.minimizer` returns a `SwitchableHandle[MinimizerCategoryBase]`
that wraps the concrete instance and delegates via `__getattr__`.
Rejected: the user wants the _category_ to be the interface, not a
wrapper that looks like one. `isinstance` checks, descriptor
introspection, factory metadata, and `help()` all need bespoke
delegation. The cost is much higher than the back-reference approach for
no extra capability.

### D. Keep owner-level setters; just deduplicate CIF

Strip `_fitting.minimizer_type` from CIF while leaving the Python API at
owner level. Rejected: fixes the CIF duplication but leaves the UX split
(the original complaint). Half a solution at the cost of a separate
amendment ADR.

### E. Hybrid: writable `type` on category + alias on owner

Keep `<owner>.<cat>_type` as a thin alias that forwards to
`<owner>.<cat>.type` setter, "for backwards compatibility". Rejected:
beta posture explicitly says "no legacy shims, no deprecation warnings".
Dual surfaces double the API and the documentation burden.

## Example: end state across the project

The end state of every switchable surface, in one place. All eight
in-scope rows from the catalog appear; the uniform `_<cat>.type` rule is
visible at a glance.

### `project.cif`

```
data_project

_rendering_plot.type   plotly
_rendering_table.type   rich
```

The `_rendering.*` block is gone; two single-purpose blocks replace it
(§8a).

### `experiment.cif` (per-experiment block)

```
data_hrpt

_calculator.type          cryspy

_peak.type                cwl-pseudo-voigt
_peak.broad_gauss_u       0.0123
_peak.broad_gauss_v      -0.0045
_peak.broad_gauss_w       0.0212
_peak.broad_lorentz_x     0.0085
_peak.broad_lorentz_y     0.0021

_background.type          chebyshev
loop_
  _pd_background.id
  _pd_background.Chebyshev_order
  _pd_background.Chebyshev_coef
  1   0   0.42
  2   1  -0.18
  3   2   0.05
```

Three things change in this block:

- `_calculation.calculator_type` becomes `_calculator.type` (the
  category is also renamed `Calculation` → `Calculator`; §8c).
- `_peak.profile_type` becomes `_peak.type`; the existing
  `_peak.broad_gauss_*` and `_peak.broad_lorentz_*` parameter tags are
  unchanged (the names come from
  [`src/easydiffraction/datablocks/experiment/categories/peak/cwl_mixins.py`](../../../src/easydiffraction/datablocks/experiment/categories/peak/cwl_mixins.py)).
  The CIF value is the **canonical tag** (`cwl-pseudo-voigt` here, since
  the example experiment is constant-wavelength); the writable Python
  setter `experiment.peak.type` accepts the alias `'pseudo-voigt'` too
  and canonicalizes it before persisting (see §4 → "Aliases").
- `_background.type` is **new** (today the type is implicit in whichever
  `_pd_background.*` columns are present); the existing
  `_pd_background.Chebyshev_order` / `_pd_background.Chebyshev_coef`
  loop tags are unchanged.

### `analysis.cif` (Bayesian fit)

```
data_analysis

_fitting_mode.type        joint

_minimizer.type                       'bumps (dream)'
_minimizer.sampling_steps             3000
_minimizer.burn_in_steps              600
_minimizer.thinning_interval          1
_minimizer.population_size            4
_minimizer.parallel_workers           0
_minimizer.initialization_method      latin_hypercube
_minimizer.random_seed                ?

_fit_result.result_kind                bayesian
_fit_result.fitting_time               124.7
_fit_result.reduced_chi_square         1.18
_fit_result.acceptance_rate_mean       0.27
_fit_result.gelman_rubin_max           1.03
_fit_result.effective_sample_size_min  482
_fit_result.best_log_posterior        -1234.56
```

The `_fitting.*` block is gone (`_fitting.minimizer_type` →
`_minimizer.type`; `_fitting.mode_type` → `_fitting_mode.type`).
Fit-result outputs live under `_fit_result.*` per
[`minimizer-input-output-split.md`](minimizer-input-output-split.md);
`_minimizer.*` carries only user-writable settings.

### `analysis.cif` (deterministic fit)

```
data_analysis

_fitting_mode.type        single

_minimizer.type                       'lmfit (leastsq)'
_minimizer.max_iterations             1000

_fit_result.result_kind                deterministic
_fit_result.fitting_time               12.34
_fit_result.iterations                 87
_fit_result.exit_reason                converged
_fit_result.reduced_chi_square         1.42
_fit_result.objective_value            1532.4
```

`_minimizer.optimizer_name` and `_minimizer.method_name` are gone — they
were per-engine constants and are derived from `_minimizer.type` at
restore time (§3).

### Python surface

```python
# Family A — instance-swap categories
project.analysis.minimizer.show_supported()
project.analysis.minimizer.type = 'bumps (dream)'
project.analysis.minimizer.sampling_steps = 3000

project.experiments['hrpt'].peak.show_supported()
project.experiments['hrpt'].peak.type = 'pseudo-voigt'
project.experiments['hrpt'].peak.broad_gauss_u = 0.0123
project.experiments['hrpt'].peak.broad_lorentz_x = 0.0085

project.experiments['hrpt'].background.show_supported()
project.experiments['hrpt'].background.type = 'chebyshev'
project.experiments['hrpt'].background.create(id='1', order=0, coef=0.42)

# Family B — engine-swap categories (same surface)
project.experiments['hrpt'].calculator.show_supported()
project.experiments['hrpt'].calculator.type = 'cryspy'

project.rendering_plot.show_supported()
project.rendering_plot.type = 'plotly'

project.rendering_table.show_supported()
project.rendering_table.type = 'rich'

# Family C — active-sibling selector (same surface)
project.analysis.fitting_mode.show_supported()
project.analysis.fitting_mode.type = 'joint'
```

One template, eight selectors, three mechanisms behind the scenes.
