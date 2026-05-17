# ADR: Category Owners and Real Datablocks

**Status:** Proposed  
**Date:** 2026-05-17

## Context

The current architecture has two real datablock families:

- structures
- experiments

These are real datablocks because each instance maps to a CIF
`data_<id>` block and has a datablock entry name. This is reflected in
`DatablockItem`, `DatablockCollection`, and `datablock_item_to_cif()`.

`Analysis` and project-level configuration are different. They own
CIF-like categories, but they are singleton project sections rather than
collections of independently named data blocks. They should not need a
datablock ID, and they should not serialize as `data_analysis` or
`data_project`.

The problem is that `DatablockItem` currently combines two
responsibilities:

1. It owns and updates flat categories.
2. It represents a real CIF data block with a `data_<id>` header.

This makes it tempting to make `Analysis` inherit from `DatablockItem`
only to reuse category discovery, parameter enumeration, update
orchestration, and CIF category serialization. That would improve code
reuse, but it would weaken the meaning of "datablock" in the model.

The open issue "Make `Analysis` a `DatablockItem`" already identifies
the design fork: either make `Analysis` inherit from `DatablockItem`, or
extract a shared category-update protocol.

A detailed migration plan exists in:

```text
docs/dev/plan_category-owner-sections.md
```

This ADR records the intended architectural decision behind that plan.

## Decision

Introduce a new core abstraction named `CategoryOwner`.

`CategoryOwner` represents an object that owns flat CIF-like categories.
It provides shared behavior for:

- category discovery
- category sorting by `_update_priority`
- parameter aggregation
- category update orchestration
- dirty-flag tracking
- category help display
- category-body CIF serialization without a `data_` header

`DatablockItem` will inherit from `CategoryOwner` and add only the
behavior specific to real CIF data blocks:

- `unique_name` from `datablock_entry_name`
- `data_<id>` header serialization
- participation in `DatablockCollection`

The target hierarchy is:

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

## Detailed Rules

### 1. A real datablock must emit a CIF `data_<id>` header

Only objects that serialize as independent CIF data blocks should
inherit datablock-specific behavior.

Current real datablocks:

- `Structure`
- `ExperimentBase` subclasses

These should continue to emit:

```text
data_<structure_name>
data_<experiment_name>
```

### 2. `Analysis` is a category-owning singleton section

`Analysis` should inherit from `CategoryOwner`, not `DatablockItem`.

It owns categories such as:

- `fitting`
- `aliases`
- `constraints`
- `joint_fit`
- `sequential_fit`
- `sequential_fit_extract`

It should reuse shared category discovery and parameter aggregation, but
its saved CIF should remain a section body. It must not emit
`data_analysis`.

### 3. Project configuration may become a category-owning singleton section

Project-level configuration should eventually follow the same model.

The likely long-term shape is:

```text
Project
`-- ProjectConfig(CategoryOwner)
    |-- ProjectInfo or ProjectMetadata
    `-- Rendering
```

This should be treated as a follow-up after the `Analysis` migration is
stable, because project save/load compatibility is a separate risk.

### 4. CIF serialization should be split by responsibility

Add a serializer for category-owner bodies:

```python
category_owner_to_cif(owner)
```

This function serializes categories but does not add a `data_` header.

Keep `datablock_item_to_cif(datablock)` for real datablocks. It should
compose:

1. `data_<datablock_entry_name>`
2. `category_owner_to_cif(datablock)`

### 5. Active analysis categories remain an owner-level policy

`Analysis` has mode-specific sibling categories. They remain direct
children of `Analysis`, not nested under `fitting`.

`Analysis` should expose a hook such as:

```python
def _serializable_categories(self) -> list:
    ...
```

This hook controls which categories are written for the current fitting
mode:

- shared categories always serialize
- `joint_fit` serializes in joint mode
- `sequential_fit` and `sequential_fit_extract` serialize in sequential
  mode
- inactive mode-specific categories remain accessible but are not
  serialized

This preserves the active-sibling selector model accepted in
`docs/dev/ADRs/adr_fit-mode-categories.md`.

## Consequences

### Positive

- The term "datablock" remains precise.
- `Analysis` can reuse standard category discovery and parameter
  enumeration without becoming a fake data block.
- CIF serialization becomes clearer because category-body rendering is
  separated from `data_` header rendering.
- Future project-level category sections can reuse the same base class.
- Dirty-flag behavior can be generalized from `DatablockItem` to
  `CategoryOwner`.

### Trade-offs

- A new core abstraction must be introduced and documented.
- `DatablockItem` must be refactored without changing structure and
  experiment behavior.
- `Analysis` migration touches both runtime behavior and CIF
  serialization, so it needs characterization tests.
- Project configuration cleanup should be delayed to avoid mixing two
  save/load migrations.

### Compatibility Requirements

The migration must preserve:

- `structure.as_cif` starts with `data_<structure_name>`
- `experiment.as_cif` starts with `data_<experiment_name>`
- `analysis.as_cif` does not start with `data_`
- project save/load layout remains compatible
- `project.parameters` remains fit-focused and does not include analysis
  configuration parameters unless a later ADR changes that contract

## Alternatives Considered

### Make `Analysis` inherit from `DatablockItem`

Rejected.

This would be the smallest code change, but it would make "datablock"
mean both real CIF data blocks and singleton project sections. It would
also encourage fake identities such as
`datablock_entry_name = "analysis"`.

### Add `emit_data_header = False` to `DatablockItem`

Rejected.

This keeps inheritance reuse but encodes two different concepts in one
class. It also makes every future datablock-related method check whether
the object is a real datablock.

### Keep `Analysis` fully ad hoc

Rejected.

This preserves current behavior but leaves duplicated logic for category
discovery, category updates, parameter enumeration, and CIF section
serialization.

### Make `Project` itself a `CategoryOwner`

Deferred.

`Project` is a facade that owns collections, display helpers, summary
helpers, analysis, and file I/O. Making the facade itself a category
owner would mix orchestration with category-section behavior. A smaller
`ProjectConfig(CategoryOwner)` is a better follow-up.

## Implementation Plan

Follow:

```text
docs/dev/plan_category-owner-sections.md
```

The plan should be implemented in small phases:

1. Add baseline tests.
2. Add `CategoryOwner`.
3. Make `DatablockItem` inherit `CategoryOwner`.
4. Split category-owner CIF body serialization from datablock
   serialization.
5. Move `Analysis` onto `CategoryOwner`.
6. Generalize dirty-flag lookup from `DatablockItem` to `CategoryOwner`.
7. Optionally introduce `ProjectConfig`.
8. Update architecture and issue tracking.

## Post-Implementation ADR Update

This ADR must be updated after the migration plan is implemented.

When implementation is complete:

1. Change status from `Proposed` to `Accepted and implemented`.
2. Update the date if the project convention requires the implementation
   date.
3. Replace tentative wording such as "should" and "target hierarchy"
   with the actual final design.
4. Record any deviations from the migration plan.
5. Link to the implementation PR or commit if available.
6. Move this file from `docs/dev/ADR-suggestions/` to `docs/dev/ADRs/`
   if that is the repository convention for accepted decisions.
7. Update `docs/dev/architecture.md`.
8. Update or close the related issue in `docs/dev/Issues/issues_open.md`
   (move to `docs/dev/Issues/issues_closed.md` on full resolution).

## Acceptance Criteria

This ADR is satisfied when:

- `CategoryOwner` exists and is documented.
- `DatablockItem` inherits from `CategoryOwner`.
- `Analysis` inherits from `CategoryOwner`, not `DatablockItem`.
- `Analysis` uses shared category discovery and parameter enumeration.
- real datablocks still emit `data_<id>` headers.
- singleton sections do not emit fake `data_` headers.
- dirty-flag propagation works for all category owners.
- architecture documentation distinguishes real datablocks from
  category-owning sections.
