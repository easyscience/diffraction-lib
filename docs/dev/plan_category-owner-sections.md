# Category Owner Migration Plan

## Status

Branch: `feature/category-owner-sections`

Two-phase workflow (see `.github/copilot-instructions.md`):

- Phase 1 — Implementation. Code, docs, and architecture updates only.
  Phase 0 baseline characterization tests below are an explicit
  exception (they describe pre-existing behavior so the refactor can be
  verified mechanically). Do not add new feature tests during Phase 1.
- Phase 2 — Verification. Add the per-phase tests listed below, then
  run the verification commands in the "Phase 2 Verification" section.

Stop after Phase 1 and request review before starting Phase 2.

Status checklist (mark `[x]` as completed):

```text
Phase 1 — Implementation
[x] Phase 0: Add baseline characterization tests.
[x] Phase 1: Add CategoryOwner in core/category_owner.py.
[x] Phase 2: Make DatablockItem inherit CategoryOwner.
[x] Phase 3: Split CIF body serialization (category_owner_to_cif).
[x] Phase 4: Move Analysis onto CategoryOwner.
[x] Phase 5: Update dirty-flag lookup to CategoryOwner.
[ ] Phase 6: (Optional) ProjectConfig cleanup.
[ ] Phase 7: Update architecture.md and Issues/issues_open.md.
[ ] Phase 1 review gate: present diff for approval.

Phase 2 — Verification
[ ] Add per-phase unit tests (see "Tests For Phase X" sections).
[ ] pixi run fix
[ ] pixi run check
[ ] pixi run unit-tests
[ ] pixi run integration-tests
[ ] pixi run script-tests
```

## Commit Discipline

When an AI agent follows this plan, every completed Phase 1
implementation step listed in the status checklist must be staged with
explicit paths and committed locally before moving to the next
implementation step or to the Phase 1 review gate. Follow the rules in
the **Commits** section of `.github/copilot-instructions.md`.

- One commit per step. Atomic and single-purpose.
- Stage explicit paths only — do not `git add .`.
- Suggested commit messages (≤72 chars, imperative mood, no type prefix):
  - `Add baseline category-owner characterization tests`
  - `Add CategoryOwner base class`
  - `Make DatablockItem inherit CategoryOwner`
  - `Add category_owner_to_cif and reuse it in datablock serializer`
  - `Make Analysis inherit CategoryOwner`
  - `Generalize dirty-flag lookup to CategoryOwner`
  - `Introduce ProjectConfig category owner` (optional)
  - `Document CategoryOwner in architecture.md`
- Do not stage generated artifacts produced by integration/script/
  notebook tests unless explicitly asked.

## Purpose

This plan explains how to make `Analysis` and project-level configuration
reuse the same category-management behavior as real datablocks without making
them real datablocks.

The current code has two real datablock types:

- `Structure`
- `Experiment`

Those are real datablocks because they represent CIF `data_<id>` blocks and
have a user-defined block ID.

`Analysis` and project-level configuration are different. They own CIF-like
categories, but they are singleton project sections. They should not require a
datablock ID and should not serialize as `data_analysis` or `data_project`.

The target design is:

```text
GuardedBase
|-- CategoryItem
|-- CollectionBase
|   |-- CategoryCollection
|   `-- DatablockCollection
`-- CategoryOwner
    |-- DatablockItem
    |   |-- Structure
    |   `-- ExperimentBase
    |-- Analysis
    `-- ProjectConfig    # optional follow-up
```

`CategoryOwner` contains shared behavior for objects that own flat categories.
`DatablockItem` keeps the additional behavior that only real CIF data blocks
need.

## Important Definitions

Use these terms consistently during the migration.

`DatablockItem`
: A real CIF data block. It serializes with a `data_<id>` header. It has a
  `datablock_entry_name`. Examples: `Structure`, `ExperimentBase`.

`CategoryOwner`
: An object that owns flat sibling categories and can update, enumerate, and
  serialize those categories. It does not necessarily have a `data_` header.
  Examples after migration: `DatablockItem`, `Analysis`, optional
  `ProjectConfig`.

`CategoryItem`
: A single category row. Example: `Cell`, `SpaceGroup`, `Fitting`,
  `Rendering`.

`CategoryCollection`
: A loop-style category collection. Example: `AtomSites`, `Aliases`,
  `JointFitCollection`.

## Non-Negotiable Rules

Follow these rules throughout the migration:

1. Do not make `Analysis` inherit directly from `DatablockItem`.
2. Do not make `Project` inherit from `DatablockItem`.
3. Do not emit `data_analysis` from `Analysis.as_cif`.
4. Do not emit `data_project` in the saved `project.cif` file.
5. Do not rename CIF tags during this migration.
6. Do not change public access paths unless a phase explicitly says so.
7. Keep `project.parameters` limited to fit-relevant structure and experiment
   parameters unless a separate design decision changes that later.
8. Keep inactive analysis categories accessible unless the fit-mode policy is
   intentionally changed in a separate task.

## Recommended Branching Strategy

Use several small pull requests or commits. Each phase should be independently
reviewable.

Suggested split:

1. Characterization tests.
2. Add `CategoryOwner`.
3. Move `DatablockItem` onto `CategoryOwner`.
4. Split CIF body serialization.
5. Move `Analysis` onto `CategoryOwner`.
6. Update dirty-flag lookup.
7. Optional project-config cleanup.
8. Documentation cleanup.

Do not combine phases 4, 5, and 6 into one large change. If something breaks,
small phases make the source of the break obvious.

## Phase 0: Baseline Safety Tests

Before changing production code, add or confirm tests that describe current
behavior.

### Files To Read First

Read these files before editing:

- `src/easydiffraction/core/datablock.py`
- `src/easydiffraction/core/category.py`
- `src/easydiffraction/core/collection.py`
- `src/easydiffraction/core/identity.py`
- `src/easydiffraction/core/variable.py`
- `src/easydiffraction/analysis/analysis.py`
- `src/easydiffraction/project/project.py`
- `src/easydiffraction/io/cif/serialize.py`
- `docs/dev/architecture.md`
- `docs/dev/Issues/issues_open.md`

### Tests To Add Or Confirm

Add focused tests before refactoring. Good locations are:

- `tests/unit/easydiffraction/core/`
- `tests/unit/easydiffraction/analysis/`
- `tests/unit/easydiffraction/io/cif/`

Test these behaviors:

1. A structure CIF starts with `data_<structure_name>`.
2. An experiment CIF starts with `data_<experiment_name>`.
3. `Analysis.as_cif` does not start with `data_`.
4. `Analysis.as_cif` includes `_fitting.mode_type`.
5. `Analysis.as_cif` includes `fitting`, `aliases`, and `constraints`
   sections when present.
6. In joint mode, `Analysis.as_cif` includes `joint_fit`.
7. In sequential mode, `Analysis.as_cif` includes `sequential_fit` and
   `sequential_fit_extract`.
8. In single mode, inactive mode-specific sections are not serialized.
9. Existing project save/load behavior still reads:
   - `project.cif`
   - `structures/*.cif`
   - `experiments/*.cif`
   - `analysis/analysis.cif`

### Suggested Commands

Run focused tests first:

```shell
pixi run unit-tests tests/unit/easydiffraction/core
pixi run unit-tests tests/unit/easydiffraction/analysis
pixi run unit-tests tests/unit/easydiffraction/io/cif
```

If these pass, run a broader unit subset:

```shell
pixi run unit-tests tests/unit/easydiffraction/datablocks
```

## Phase 1: Add `CategoryOwner`

Create:

```text
src/easydiffraction/core/category_owner.py
```

### Responsibility

`CategoryOwner` should own the behavior currently shared by any object that has
flat categories:

- category discovery
- category sorting by `_update_priority`
- parameter aggregation
- category update orchestration
- dirty flag
- category table in `help()`
- CIF body serialization support, without a `data_` header

### Initial Implementation Shape

Start with this shape. Adjust imports as needed.

```python
from __future__ import annotations

from easydiffraction.core.category import CategoryCollection
from easydiffraction.core.category import CategoryItem
from easydiffraction.core.guard import GuardedBase


class CategoryOwner(GuardedBase):
    """Base class for objects that own flat CIF-like categories."""

    def __init__(self) -> None:
        super().__init__()
        self._need_categories_update = True

    @property
    def categories(self) -> list:
        """All category objects owned by this object, sorted by priority."""
        cats = [
            v
            for v in vars(self).values()
            if isinstance(v, (CategoryItem, CategoryCollection))
        ]
        return sorted(cats, key=lambda c: type(c)._update_priority)

    def _serializable_categories(self) -> list:
        """Categories that should be serialized for this owner."""
        return self.categories

    @property
    def parameters(self) -> list:
        """All parameters from all owned categories."""
        params = []
        for category in self.categories:
            params.extend(category.parameters)
        return params

    def _update_categories(
        self,
        *,
        called_by_minimizer: bool = False,
    ) -> None:
        """Run update hooks on all owned categories."""
        if not called_by_minimizer and not self._need_categories_update:
            return

        for category in self.categories:
            category._update(called_by_minimizer=called_by_minimizer)

        self._need_categories_update = False
```

### Help Method

Move the category-summary part of `DatablockItem.help()` into
`CategoryOwner.help()`.

Keep it simple:

1. Call `super().help()`.
2. Render a table of category code, type name, and parameter count.

### Tests For Phase 1

Create fake category owner tests. Do not use `Structure` or `Analysis` yet.

Test:

1. `CategoryOwner.categories` finds direct `CategoryItem` attributes.
2. `CategoryOwner.categories` finds direct `CategoryCollection` attributes.
3. Categories are sorted by `_update_priority`.
4. `CategoryOwner.parameters` aggregates parameters from categories.
5. `_update_categories()` calls category `_update()` methods.
6. `_update_categories()` honors `_need_categories_update`.
7. `_serializable_categories()` returns `categories` by default.

## Phase 2: Make `DatablockItem` Inherit `CategoryOwner`

Edit:

```text
src/easydiffraction/core/datablock.py
```

### What To Change

Change:

```python
class DatablockItem(GuardedBase):
```

to:

```python
class DatablockItem(CategoryOwner):
```

Import `CategoryOwner` from the new module.

Remove from `DatablockItem` any code now provided by `CategoryOwner`:

- `_need_categories_update` initialization
- generic `_update_categories()`
- `categories`
- `parameters`
- category-summary part of `help()`, if moved

Keep these in `DatablockItem`:

- `unique_name`
- `as_cif`
- `_cif_for_display`
- datablock-specific string representations

### Expected Result

This phase should not change public behavior.

These should still work:

```python
structure.as_cif
experiment.as_cif
structure.categories
experiment.categories
structure.parameters
experiment.parameters
```

### Tests For Phase 2

Run:

```shell
pixi run unit-tests tests/unit/easydiffraction/core
pixi run unit-tests tests/unit/easydiffraction/datablocks
pixi run unit-tests tests/unit/easydiffraction/io/cif
```

If failures happen, check parent linkage first. Most failures in this phase are
likely caused by categories not having the expected `_parent`.

## Phase 3: Split CIF Body Serialization From Datablock Serialization

Edit:

```text
src/easydiffraction/io/cif/serialize.py
```

### Problem

`datablock_item_to_cif()` currently does two jobs:

1. Adds the `data_<id>` header.
2. Serializes category content.

Only real datablocks need job 1. `Analysis` and project config need job 2.

### Add `category_owner_to_cif()`

Add a helper like this:

```python
def category_owner_to_cif(
    owner: object,
    max_loop_display: int | None = None,
) -> str:
    """Render a CategoryOwner-like object's categories without a data_ header."""
    from easydiffraction.core.category import CategoryCollection
    from easydiffraction.core.category import CategoryItem

    categories_getter = getattr(owner, "_serializable_categories", None)
    if callable(categories_getter):
        categories = categories_getter()
    else:
        categories = [
            v
            for v in vars(owner).values()
            if isinstance(v, (CategoryItem, CategoryCollection))
        ]

    item_parts = [
        category.as_cif
        for category in categories
        if isinstance(category, CategoryItem) and category.as_cif
    ]

    collection_parts = [
        category_collection_to_cif(category, max_display=max_loop_display)
        for category in categories
        if isinstance(category, CategoryCollection)
    ]

    return "\n\n".join([part for part in item_parts + collection_parts if part])
```

Keep the current item-first, collection-second ordering unless a separate test
and design decision changes it.

### Update `datablock_item_to_cif()`

After adding `category_owner_to_cif()`, reduce `datablock_item_to_cif()` to:

```python
header = f"data_{datablock._identity.datablock_entry_name}"
body = category_owner_to_cif(datablock, max_loop_display=max_loop_display)
if not body:
    return header
return "\n\n".join([header, body])
```

### Tests For Phase 3

Add or update tests for:

1. `category_owner_to_cif()` does not emit `data_`.
2. `datablock_item_to_cif()` still emits `data_<id>`.
3. Empty category owners serialize to an empty string.
4. Empty datablocks serialize to only the header.
5. Loop truncation still works for display.

Run:

```shell
pixi run unit-tests tests/unit/easydiffraction/io/cif
pixi run unit-tests tests/unit/easydiffraction/core
pixi run unit-tests tests/unit/easydiffraction/datablocks
```

## Phase 4: Move `Analysis` Onto `CategoryOwner`

Edit:

```text
src/easydiffraction/analysis/analysis.py
```

### Main Change

Change:

```python
class Analysis:
```

to:

```python
class Analysis(CategoryOwner):
```

Call `super().__init__()` at the start of `Analysis.__init__()`.

### Parent Linkage

Because `Analysis` will now be a `GuardedBase` subclass, private assignment of
`GuardedBase` children should normally set `_parent` automatically.

Still verify these categories have `_parent is analysis`:

- `analysis.aliases`
- `analysis.constraints`
- `analysis.fitting`
- `analysis.joint_fit`
- `analysis.sequential_fit`
- `analysis.sequential_fit_extract`

Some are currently assigned manually and some may not be. Make the result
consistent.

### Keep Existing Public API

Do not remove these access paths:

```python
project.analysis.fitting
project.analysis.aliases
project.analysis.constraints
project.analysis.joint_fit
project.analysis.sequential_fit
project.analysis.sequential_fit_extract
project.analysis.fitting_mode_type
```

If direct public attributes currently exist without properties, convert them
carefully. Less experienced agents should prefer a compatibility-preserving
change:

1. Keep the public access path.
2. Add properties only when needed.
3. Avoid large style cleanup in the same phase.

### Add `_serializable_categories()`

Add this method to `Analysis`:

```python
def _serializable_categories(self) -> list:
    """Analysis categories that should be written for the active fit mode."""
    categories = [
        self.fitting,
        self.aliases,
        self.constraints,
    ]

    if self._fitting_mode_type is FitModeEnum.JOINT:
        categories.append(self.joint_fit)
    elif self._fitting_mode_type is FitModeEnum.SEQUENTIAL:
        categories.extend([
            self.sequential_fit,
            self.sequential_fit_extract,
        ])

    return categories
```

This preserves the current rule:

- shared analysis categories always serialize
- joint-only category serializes only in joint mode
- sequential categories serialize only in sequential mode
- inactive categories remain accessible but are not written

### Update `Analysis.as_cif`

Keep the leading mode line:

```text
_fitting.mode_type <mode>
```

Then append `category_owner_to_cif(self)`.

Example implementation shape:

```python
@property
def as_cif(self) -> str:
    self._update_categories()
    return analysis_to_cif(self)
```

Then update `analysis_to_cif()` in `serialize.py` to use
`category_owner_to_cif(analysis)` internally.

Recommended serializer shape:

```python
def analysis_to_cif(analysis: object) -> str:
    parts = [
        f"_fitting.mode_type {format_value(analysis.fitting_mode_type)}",
    ]
    body = category_owner_to_cif(analysis)
    if body:
        parts.append(body)
    return "\n\n".join(parts)
```

### Keep Or Adjust `_update_categories()`

`Analysis._update_categories()` currently applies constraints. That is
analysis-specific and must not be lost.

Safest first version:

```python
def _update_categories(
    self,
    *,
    called_by_minimizer: bool = False,
) -> None:
    super()._update_categories(called_by_minimizer=called_by_minimizer)

    if self.constraints.enabled and self.constraints._items:
        self.constraints_handler.set_aliases(self.aliases)
        self.constraints_handler.set_constraints(self.constraints)
        self.constraints_handler.apply()
```

If this changes behavior, use the existing constraint logic and leave a short
comment explaining why shared category updates are intentionally skipped or
ordered differently.

### Tests For Phase 4

Add tests for:

1. `isinstance(analysis, CategoryOwner)`.
2. `analysis.categories` includes analysis categories.
3. `analysis.parameters` includes fitting and analysis config descriptors.
4. Parent links are set on all analysis categories.
5. `analysis.as_cif` still does not start with `data_`.
6. `analysis.as_cif` still includes `_fitting.mode_type`.
7. Mode-specific serialization behavior is unchanged.
8. `analysis.help()` still works and respects `_help_filter()`.

Run:

```shell
pixi run unit-tests tests/unit/easydiffraction/analysis
pixi run unit-tests tests/unit/easydiffraction/io/cif
pixi run unit-tests tests/unit/easydiffraction/project
```

## Phase 5: Update Dirty-Flag Lookup

Edit:

```text
src/easydiffraction/core/variable.py
```

### Current Behavior

Descriptors currently find a `DatablockItem` ancestor when marking an owner
dirty after value changes.

That is too narrow after this migration. `Analysis` will also be a category
owner.

### Target Behavior

Descriptors should mark the nearest `CategoryOwner` ancestor dirty.

Change helper naming carefully. For example:

```python
def _category_owner(self) -> object | None:
    from easydiffraction.core.category_owner import CategoryOwner

    return self._parent_of_type(CategoryOwner)
```

Then update value setters to use this owner:

```python
parent_owner = self._category_owner()
if parent_owner is not None:
    parent_owner._need_categories_update = True
```

### Compatibility Check

This must still mark structures and experiments dirty because
`DatablockItem` now inherits `CategoryOwner`.

### Tests For Phase 5

Add tests for:

1. Changing a structure parameter marks the structure dirty.
2. Changing an experiment parameter marks the experiment dirty.
3. Changing an analysis category descriptor marks analysis dirty.
4. `_set_value_from_minimizer()` still marks the owner dirty.

Run:

```shell
pixi run unit-tests tests/unit/easydiffraction/core
pixi run unit-tests tests/unit/easydiffraction/analysis
pixi run unit-tests tests/unit/easydiffraction/datablocks
```

## Phase 6: Optional Project Config Cleanup

This phase is optional and should be a separate PR. Do not do it until
`Analysis` is stable.

### Goal

Project-level configuration also has category-like behavior. Today:

- `ProjectInfo` is a special metadata object.
- `Rendering` is already a `CategoryItem`.
- `project_config_to_cif()` manually combines them.

The cleaner long-term shape is:

```text
Project
`-- ProjectConfig(CategoryOwner)
    |-- ProjectInfo or ProjectMetadata
    `-- Rendering
```

### Low-Risk Version

If converting `ProjectInfo` into a `CategoryItem` is too disruptive, do not do
it immediately.

Instead:

1. Add `ProjectConfig(CategoryOwner)`.
2. Put only `rendering` inside it at first.
3. Keep `ProjectInfo` special.
4. Keep `project.info` and `project.rendering` public access unchanged.
5. Use shared category-owner serialization only for `rendering`.

### Full Version

Convert project metadata into a real category item:

```text
ProjectMetadata(CategoryItem)
```

It should own descriptors for:

- project id
- title
- description
- created timestamp
- last modified timestamp

This is more work because timestamps and path handling need care. Do not mix
this with the `Analysis` migration.

### Save/Load Rule

Even after this cleanup, saved `project.cif` should remain a section file
without an explicit `data_` header. The loader currently wraps project config
with `data_project` before parsing, and that can remain an implementation
detail.

## Phase 7: Documentation Updates

Update:

```text
docs/dev/architecture.md
docs/dev/Issues/issues_open.md
```

### Architecture Updates

In `architecture.md`, update the object hierarchy to include
`CategoryOwner`.

Replace the current hierarchy with something like:

```text
GuardedBase
|-- CategoryItem
|-- CollectionBase
|   |-- CategoryCollection
|   `-- DatablockCollection
`-- CategoryOwner
    `-- DatablockItem
```

Add this design rule:

```text
A real datablock is a CategoryOwner that serializes as a CIF data_<id> block.
Not every CategoryOwner is a real datablock.
```

Update the flat category structure section from:

```text
Owner (DatablockItem / Analysis)
```

to:

```text
Owner (CategoryOwner)
```

Explain that:

- `Structure` and `ExperimentBase` are real datablocks.
- `Analysis` is a singleton category-owning section.
- Project configuration may become a singleton category-owning section.

### Issues File Updates

When the migration is complete, update issue 5 in
`docs/dev/Issues/issues_open.md`.

If fully complete, remove the issue and add a note to closed issues if that is
the project convention.

If only `CategoryOwner` is introduced but `Analysis` is not migrated yet,
change the issue text to reflect the remaining work.

## Final Acceptance Criteria

The migration is done when all of these are true:

1. `CategoryOwner` exists and is tested.
2. `DatablockItem` inherits from `CategoryOwner`.
3. `Structure.as_cif` still emits `data_<structure_name>`.
4. `Experiment.as_cif` still emits `data_<experiment_name>`.
5. `Analysis` inherits from `CategoryOwner`.
6. `Analysis.as_cif` does not emit a `data_` header.
7. `Analysis` uses shared category discovery for `categories`.
8. `Analysis` uses shared parameter enumeration for `parameters`.
9. Inactive analysis categories remain accessible.
10. Inactive analysis categories are not serialized.
11. Dirty-flag marking works for structures, experiments, and analysis.
12. Project save/load format remains compatible.
13. Documentation distinguishes real datablocks from category-owning sections.

## Common Mistakes To Avoid

### Mistake: Making `Analysis` A Fake Datablock

Do not solve this by setting:

```python
self._identity.datablock_entry_name = lambda: "analysis"
```

That makes parameter identities and CIF output imply that analysis is a real
datablock. It is not.

### Mistake: Adding A Boolean Flag To `DatablockItem`

Avoid:

```python
class Analysis(DatablockItem):
    emit_data_header = False
```

This works mechanically but weakens the model. The class name
`DatablockItem` should mean real datablock.

### Mistake: Changing Fit Parameter Semantics

Do not change `project.parameters` to include analysis parameters during this
migration. Analysis parameters are configuration parameters, not model
parameters for fitting.

### Mistake: Refactoring Public API While Moving Base Classes

Do not rename `fitting_mode_type`, `joint_fit`, `sequential_fit`,
`rendering`, or `info` during this migration. Naming cleanup can happen later.

### Mistake: Assuming `vars(owner)` Order Is A Design Contract

If serialization order matters, write tests for it. Prefer explicit
`_serializable_categories()` hooks for owners that need a specific active
subset.

## Minimal Agent Checklist

The authoritative checklist lives in the **Status** section at the top of
this document. Keep it updated as work progresses.

## Phase 2 Verification

Run these in order after Phase 1 is reviewed and approved.

Per-area focused unit tests first:

```shell
pixi run unit-tests tests/unit/easydiffraction/core
pixi run unit-tests tests/unit/easydiffraction/analysis
pixi run unit-tests tests/unit/easydiffraction/io/cif
pixi run unit-tests tests/unit/easydiffraction/datablocks
pixi run unit-tests tests/unit/easydiffraction/project
```

Then the full project verification commands required by
`.github/copilot-instructions.md`:

```shell
pixi run fix
pixi run check
pixi run unit-tests
pixi run integration-tests
pixi run script-tests
```

`pixi run fix` regenerates `docs/dev/package-structure-*.md`
automatically — do not edit those by hand. Accept the auto-fix output
and re-run `pixi run check` until clean.

## Suggested Pull Request

**Title:** Separate category-owning sections from real CIF datablocks

**Description (end-user oriented):**

This change reorganizes how the library models the different pieces of
a project that own CIF-like categories. Crystal structures and
experiments stay "real" CIF data blocks — each one is saved with its
own `data_<id>` header, exactly as before. The `Analysis` section
(fitting mode, aliases, constraints, joint/sequential fit settings) and
project-level configuration are now treated as singleton sections that
share the same convenient features (category discovery, parameter
listing, dirty tracking, `help()` tables) without pretending to be data
blocks. As a result:

- Saved CIF files keep their current layout: structures and experiments
  start with `data_<name>`; analysis and project configuration stay as
  section files without a fake `data_` header.
- `project.parameters`, `analysis.parameters`, and `structure.parameters`
  behave consistently and discoverably.
- Future project metadata cleanup can reuse the same base class.

No user-facing API names change in this PR; existing tutorials,
scripts, and saved projects continue to work.
