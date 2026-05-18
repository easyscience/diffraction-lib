# Loop Category Key Identity Implementation Plan

## Status

Workflow instructions:

```text
.github/copilot-instructions.md
```

Related ADR suggestion:

```text
docs/dev/adrs/suggestions/loop-category-key-identity.md
```

This plan implements two related changes:

1. Move category identity declarations from per-instance assignments to
   class-level declarations.
2. Add an explicit persisted `id` field to the constraints loop.

Status checklist. Mark `[x]` only while implementing:

```text
Phase 1 - Implementation
[ ] Add class-level identity declarations to CategoryItem.
[ ] Teach Identity to resolve declared category entry names.
[ ] Rebuild collection indexes after CIF loop loading.
[ ] Add _category_code to all current CategoryItem subclasses.
[ ] Add _category_entry_name to all current loop CategoryItem subclasses.
[ ] Remove direct self._identity.category_code assignments.
[ ] Remove direct self._identity.category_entry_name lambda assignments.
[ ] Add Constraint.id descriptor serialized as _constraint.id.
[ ] Change constraints collection keys from lhs_alias to id.
[ ] Preserve default constraints.create(expression=...) behavior by using lhs_alias as the default id.
[ ] Add backward-compatible loading for old CIF loops without _constraint.id.
[ ] Update constraints display.
[ ] Update loop-category-key-identity.md if implementation details differ from the ADR.
[ ] Phase 1 review gate: present diff for approval.

Phase 2 - Verification
[ ] Add tests for the base declarative identity behavior.
[ ] Add parametrized tests for current loop category identity declarations.
[ ] Update constraints tests.
[ ] Update existing round-trip tests that compare constraints CIF.
[ ] Run formatting.
[ ] Run targeted unit tests.
[ ] Run broader checks.
```

## Commit Discipline

When an AI agent follows this plan, every completed Phase 1
implementation step must be staged with explicit paths and committed
locally before moving to the next implementation step or to the Phase 1
review gate.

Follow the **Commits** section of `.github/copilot-instructions.md`.

Rules:

- One commit per implementation step.
- Keep each commit atomic and single-purpose.
- Stage explicit paths only. Do not use `git add .`.
- Do not stage unrelated user changes.
- Do not stage generated artifacts unless the user explicitly asks.
- If a serious uncovered design issue appears, stop and ask before
  continuing.

Suggested branch:

```text
feature/loop-category-key-identity
```

Suggested commit messages:

```text
Add declarative category identity resolution
Declare category identities on current items
Persist explicit constraint identifiers
Update ADR for declarative category identity
Add declarative category identity tests
```

## Goal

Replace repeated constructor code like this:

```python
self._identity.category_code = 'atom_site'
self._identity.category_entry_name = lambda: str(self.label.value)
```

with class-level declarations:

```python
class AtomSite(CategoryItem):
    _category_code = 'atom_site'
    _category_entry_name = 'label'
```

The name `_category_entry_name` is intentionally kept because this is
the preferred project terminology. In this plan it means "the name of
the item attribute used to resolve the entry name". The resolved entry
value is still obtained through:

```python
item._identity.category_entry_name
```

For example, `AtomSite._category_entry_name == 'label'`, while
`atom_site._identity.category_entry_name == 'Ba1'`.

## Non-Goals

Do not change these in this migration:

- Do not rename `Identity.category_entry_name`.
- Do not rename `CategoryCollection`.
- Do not change public collection access syntax.
- Do not change CIF tags except adding `_constraint.id`.
- Do not rename `label` to `id` for atom sites or aliases.
- Do not make `phase_id` the row key for powder reflection loops.

## Design

This plan intentionally uses a narrow metadata lookup based on
`_category_entry_name`. That is an allowed exception to the general "no
string-based dispatch" rule because the attribute name is a class-level
declaration, not user input, and resolution is centralized in
`CategoryItem`.

### CategoryItem Declarations

Add these class attributes to `CategoryItem` in
`src/easydiffraction/core/category.py`:

```python
class CategoryItem(GuardedBase):
    _category_code: str | None = None
    _category_entry_name: str | None = None
```

Update `CategoryItem.__init__()` so it assigns `_category_code` once:

```python
def __init__(self) -> None:
    super().__init__()
    if self._category_code is not None:
        self._identity.category_code = self._category_code
```

Do not try to resolve `_category_entry_name` in `CategoryItem.__init__`.
Many item classes create descriptors after `super().__init__()` returns,
and some mixin-based classes run `CategoryItem.__init__()` before their
descriptors are created.

Add a resolver method to `CategoryItem`:

```python
def _resolve_category_entry_name(self) -> str | None:
    attr_name = self._category_entry_name
    if attr_name is None:
        return None

    value = getattr(self, attr_name)
    if isinstance(value, GenericDescriptorBase):
        value = value.value
    return str(value)
```

Import `GenericDescriptorBase` from `easydiffraction.core.variable` in
`category.py` if it is not already in scope.

### Identity Resolution

Update `Identity._resolve_up()` in
`src/easydiffraction/core/identity.py` so that category entries can be
resolved from the owning object before walking to the parent.

Add this logic after checking direct callable/string values and before
climbing to the parent:

```python
if attr == 'category_entry':
    resolver = getattr(self._owner, '_resolve_category_entry_name', None)
    if callable(resolver):
        resolved = resolver()
        if resolved is not None:
            return resolved
```

Keep the existing `category_entry_name` setter. It remains useful as an
escape hatch and keeps old code compatible during migration.

### Collection Index Rebuild After CIF Loading

Update `category_collection_from_cif()` in
`src/easydiffraction/io/cif/serialize.py`.

Currently `_adopt_items()` rebuilds the index before loop values are
loaded into each item. After declarative keys are resolved from
descriptor values, the index must be rebuilt after parameters are
loaded.

After the row population loop, run any collection hook and rebuild:

```python
after_from_cif = getattr(self, '_after_from_cif', None)
if callable(after_from_cif):
    after_from_cif()

self._rebuild_index()
```

The hook is needed for constraints to backfill missing ids from old CIF
files.

## Category Migration Table

Add `_category_code` to each listed class. Add `_category_entry_name`
only when the class is a loop item and currently has a collection key.
Then remove matching constructor assignments.

| File                                                                                | Class                      | `_category_code`         | `_category_entry_name` | Notes                                        |
| ----------------------------------------------------------------------------------- | -------------------------- | ------------------------ | ---------------------- | -------------------------------------------- |
| `src/easydiffraction/project/categories/info/default.py`                            | `ProjectInfo`              | `project`                | none                   | Singleton category.                          |
| `src/easydiffraction/project/categories/rendering/default.py`                       | `Rendering`                | `rendering`              | none                   | Singleton category.                          |
| `src/easydiffraction/analysis/categories/fitting/default.py`                        | `Fitting`                  | `fitting`                | none                   | Singleton category.                          |
| `src/easydiffraction/analysis/categories/sequential_fit/default.py`                 | `SequentialFit`            | `sequential_fit`         | none                   | Singleton category.                          |
| `src/easydiffraction/analysis/categories/aliases/default.py`                        | `Alias`                    | `alias`                  | `label`                | Loop key stays `_alias.label`.               |
| `src/easydiffraction/analysis/categories/constraints/default.py`                    | `Constraint`               | `constraint`             | `id`                   | Add the id descriptor first.                 |
| `src/easydiffraction/analysis/categories/joint_fit/default.py`                      | `JointFitItem`             | `joint_fit`              | `experiment_id`        | Loop key stays `_joint_fit.experiment_id`.   |
| `src/easydiffraction/analysis/categories/sequential_fit_extract/default.py`         | `SequentialFitExtractItem` | `sequential_fit_extract` | `id`                   | Loop key stays `_sequential_fit_extract.id`. |
| `src/easydiffraction/datablocks/structure/categories/cell/default.py`               | `Cell`                     | `cell`                   | none                   | Singleton category.                          |
| `src/easydiffraction/datablocks/structure/categories/space_group/default.py`        | `SpaceGroup`               | `space_group`            | none                   | Singleton category.                          |
| `src/easydiffraction/datablocks/structure/categories/atom_sites/default.py`         | `AtomSite`                 | `atom_site`              | `label`                | Loop key stays `_atom_site.label`.           |
| `src/easydiffraction/datablocks/structure/categories/atom_site_aniso/default.py`    | `AtomSiteAniso`            | `atom_site_aniso`        | `label`                | Loop key stays `_atom_site_aniso.label`.     |
| `src/easydiffraction/datablocks/experiment/categories/experiment_type/default.py`   | `ExperimentType`           | `expt_type`              | none                   | Singleton category.                          |
| `src/easydiffraction/datablocks/experiment/categories/calculation/default.py`       | `Calculation`              | `calculation`            | none                   | Singleton category.                          |
| `src/easydiffraction/datablocks/experiment/categories/diffrn/default.py`            | `DefaultDiffrn`            | `diffrn`                 | none                   | Singleton category.                          |
| `src/easydiffraction/datablocks/experiment/categories/instrument/base.py`           | `InstrumentBase`           | `instrument`             | none                   | Subclasses inherit this code.                |
| `src/easydiffraction/datablocks/experiment/categories/peak/base.py`                 | `PeakBase`                 | `peak`                   | none                   | Subclasses inherit this code.                |
| `src/easydiffraction/datablocks/experiment/categories/extinction/becker_coppens.py` | `BeckerCoppensExtinction`  | `extinction`             | none                   | Singleton category.                          |
| `src/easydiffraction/datablocks/experiment/categories/linked_crystal/default.py`    | `LinkedCrystal`            | `linked_crystal`         | none                   | Singleton category.                          |
| `src/easydiffraction/datablocks/experiment/categories/linked_phases/default.py`     | `LinkedPhase`              | `linked_phases`          | `id`                   | Loop key stays `_pd_phase_block.id`.         |
| `src/easydiffraction/datablocks/experiment/categories/background/line_segment.py`   | `LineSegment`              | `background`             | `id`                   | Loop key stays `_pd_background.id`.          |
| `src/easydiffraction/datablocks/experiment/categories/background/chebyshev.py`      | `PolynomialTerm`           | `background`             | `id`                   | Loop key stays `_pd_background.id`.          |
| `src/easydiffraction/datablocks/experiment/categories/excluded_regions/default.py`  | `ExcludedRegion`           | `excluded_regions`       | `id`                   | Loop key stays `_excluded_region.id`.        |
| `src/easydiffraction/datablocks/experiment/categories/refln/bragg_sc.py`            | `Refln`                    | `refln`                  | `id`                   | Powder reflection rows inherit this key.     |
| `src/easydiffraction/datablocks/experiment/categories/data/bragg_pd.py`             | `PdCwlDataPoint`           | `pd_data`                | `point_id`             | CWL powder data row.                         |
| `src/easydiffraction/datablocks/experiment/categories/data/bragg_pd.py`             | `PdTofDataPoint`           | `pd_data`                | `point_id`             | TOF powder data row.                         |
| `src/easydiffraction/datablocks/experiment/categories/data/total_pd.py`             | `TotalDataPoint`           | `total_data`             | `point_id`             | Total-scattering data row.                   |

Do not add `_category_code` or `_category_entry_name` to
`PowderReflnBase`, `PowderCwlRefln`, or `PowderTofRefln`; they inherit
the `refln` identity declarations from `Refln`.

## Constraints Migration

### Target Shape

`Constraint` should become:

```python
class Constraint(CategoryItem):
    _category_code = 'constraint'
    _category_entry_name = 'id'

    def __init__(self) -> None:
        super().__init__()

        self._id = StringDescriptor(
            name='id',
            description='Identifier for this constraint.',
            value_spec=AttributeSpec(
                default='_',
                validator=RegexValidator(pattern=r'^[A-Za-z_][A-Za-z0-9_]*$'),
            ),
            cif_handler=CifHandler(names=['_constraint.id']),
        )
        self._expression = StringDescriptor(...)
```

Define the public property:

```python
@property
def id(self) -> StringDescriptor:
    """Identifier for this constraint."""
    return self._id

@id.setter
def id(self, value: str) -> None:
    self._id.value = value
```

Keep `lhs_alias` and `rhs_expr` as derived read-only properties.

### Create API

Change `Constraints.create()` from:

```python
def create(self, *, expression: str) -> None:
```

to:

```python
def create(self, *, expression: str, id: str | None = None) -> None:
```

Implementation order:

```python
item = Constraint()
item.expression = expression
item.id = id if id is not None else item.lhs_alias
self.add(item)
self._enabled = True
```

This preserves the current default user experience:

```python
analysis.constraints.create(expression='biso_Ba = biso_La')
analysis.constraints['biso_Ba']
```

It also allows explicit ids:

```python
analysis.constraints.create(
    id='constraint_1',
    expression='biso_Ba = biso_La',
)
analysis.constraints['constraint_1']
```

### Backward-Compatible CIF Loading

Old CIF files only contain:

```cif
loop_
_constraint.expression
biso_Ba = biso_La
```

New CIF files should contain:

```cif
loop_
_constraint.id
_constraint.expression
biso_Ba "biso_Ba = biso_La"
```

Add a hook on `Constraints`:

```python
def _after_from_cif(self) -> None:
    for index, item in enumerate(self._items, start=1):
        if item.id.value in {'', '_'}:
            fallback = item.lhs_alias or f'constraint_{index}'
            item.id = fallback
```

The generic `category_collection_from_cif()` hook described above must
call this before rebuilding the index.

### Constraints Display

Update `Constraints.show()` to include the id:

```text
id | expression
```

Keep the existing empty warning behavior.

## Required Code Searches

After migration, these searches should return no category-item
constructor assignments:

```shell
git grep -n -E "self\\._identity\\.category_code =" -- src/easydiffraction
git grep -n -E "self\\._identity\\.category_entry_name =" -- src/easydiffraction
git grep -n -E "category_entry_name = lambda" -- src/easydiffraction
```

The following reads are expected to remain:

```shell
git grep -n "_identity\\.category_entry_name" -- src/easydiffraction
```

Those reads are used by collections, display, reporting, and parameter
unique names.

Do not use `rg` in this plan; it is not available in every contributor
environment. Use `git grep` for repository searches.

## Tests To Add Or Update

### Base Identity Tests

Add or update tests under `tests/unit/easydiffraction/core/`.

Test a fake category item:

```python
class FakeItem(CategoryItem):
    _category_code = 'fake'
    _category_entry_name = 'id'

    def __init__(self):
        super().__init__()
        self._id = StringDescriptor(...)

    @property
    def id(self):
        return self._id
```

Assert:

```python
item._identity.category_code == 'fake'
item._identity.category_entry_name == item.id.value
item.id.unique_name.endswith('.fake.<id>.id')
```

Also test that a singleton-like item with `_category_code` and no
`_category_entry_name` resolves category code but returns no entry name.

### Current Category Parametrized Tests

Add a parametrized test that instantiates representative loop item
classes and verifies category code plus entry:

```text
Alias -> alias, label
JointFitItem -> joint_fit, experiment_id
SequentialFitExtractItem -> sequential_fit_extract, id
AtomSite -> atom_site, label
AtomSiteAniso -> atom_site_aniso, label
LinkedPhase -> linked_phases, id
LineSegment -> background, id
PolynomialTerm -> background, id
ExcludedRegion -> excluded_regions, id
Refln -> refln, id
PdCwlDataPoint -> pd_data, point_id
PdTofDataPoint -> pd_data, point_id
TotalDataPoint -> total_data, point_id
```

Do not instantiate heavy calculator-backed owner objects for this test;
instantiate item classes directly.

### Constraints Tests

Update
`tests/unit/easydiffraction/analysis/categories/test_constraints.py`.

Required assertions:

```python
c = Constraint()
c.expression = 'a = b + c'
c.id = 'constraint_a'
assert c.id.value == 'constraint_a'
assert c.lhs_alias == 'a'
assert c.rhs_expr == 'b + c'
assert c._identity.category_entry_name == 'constraint_a'
```

Default id behavior:

```python
coll = Constraints()
coll.create(expression='a = b + c')
assert 'a' in coll.names
assert coll['a'].id.value == 'a'
assert coll['a'].rhs_expr == 'b + c'
```

Explicit id behavior:

```python
coll = Constraints()
coll.create(id='c1', expression='a = b + c')
assert 'c1' in coll.names
assert coll['c1'].lhs_alias == 'a'
```

CIF serialization:

```python
cif = coll.as_cif
assert '_constraint.id' in cif
assert '_constraint.expression' in cif
```

Backward-compatible CIF loading:

```python
cif = '''
data_analysis

loop_
_constraint.expression
"a = b + c"
'''
```

Load through the existing analysis/constraints loader and assert the
loaded collection has key `a`.

### Existing Round-Trip Tests

Update tests that compare constraint CIF or constraint collection keys:

- `tests/unit/easydiffraction/project/test_project_load.py`
- `tests/unit/easydiffraction/io/cif/test_serialize_category_owner_baseline.py`
- `tests/integration/fitting/test_project_load.py`

Expected changes:

- New saved analysis CIF includes `_constraint.id`.
- Old expression-only fixtures, if any, still load.
- Existing constraint workflows still work when no explicit id is
  supplied.

## Verification Commands

Run the smallest useful checks first:

```shell
pixi run python -m pytest tests/unit/easydiffraction/analysis/categories/test_constraints.py
pixi run python -m pytest tests/unit/easydiffraction/core/
pixi run python -m pytest tests/unit/easydiffraction/io/cif/test_serialize_category_owner_baseline.py
```

Then run broader checks:

```shell
pixi run unit-tests
pixi run integration-tests
pixi run check
```

If the modified-file Prettier helper is still missing, format changed
Markdown directly:

```shell
npx prettier --write --config=prettierrc.toml docs/dev/plans/loop-category-key-identity.md docs/dev/adrs/suggestions/loop-category-key-identity.md
```

## Local Availability Check

The plan was checked against the current repository state:

- `.github/copilot-instructions.md` exists.
- `src/easydiffraction/core/category.py`,
  `src/easydiffraction/core/identity.py`, and
  `src/easydiffraction/io/cif/serialize.py` exist.
- `tests/unit/easydiffraction/analysis/categories/test_constraints.py`
  exists.
- `tests/unit/easydiffraction/core/` exists.
- `tests/unit/easydiffraction/io/cif/test_serialize_category_owner_baseline.py`
  exists.
- `pixi.toml` defines `fix`, `check`, `unit-tests`, `integration-tests`,
  and `test-structure-check`.
- `prettierrc.toml` and local Prettier are available.
- `tools/nonpy_prettier_modified.py` is not present, so use the direct
  `npx prettier --write --config=prettierrc.toml ...` fallback for
  touched Markdown files.

## Acceptance Criteria

The implementation is done when all of these are true:

- All current category codes are declared as `_category_code` on item
  classes.
- All current loop collection keys are declared as
  `_category_entry_name` on item classes.
- No current category item sets `self._identity.category_code` in its
  constructor.
- No current category item sets `self._identity.category_entry_name` in
  its constructor.
- `item._identity.category_entry_name` still works for all loop rows.
- Descriptor `unique_name` values still include datablock, category,
  entry, and descriptor name.
- Constraints persist `_constraint.id`.
- Constraints created without an explicit id still default to the left
  hand alias.
- Old constraints CIF without `_constraint.id` still loads and receives
  deterministic ids.
- Collection indexes are correct after CIF loading.

## Suggested Pull Request

Title:

```text
Use declarative category identity metadata
```

Description:

```text
This change makes category and loop-row identities easier to audit and
keeps saved CIF identifiers explicit. Constraint rows gain a stable
identifier while existing constraint expressions continue to work.
```
