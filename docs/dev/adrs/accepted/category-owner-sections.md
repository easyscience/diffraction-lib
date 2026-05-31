# ADR: Category Owners and Real Datablocks

## Status

Accepted and implemented.

## Date

2026-05-17

## Context

The library has two different kinds of objects that expose CIF-like
categories:

- real datablocks such as structures and experiments
- singleton project sections such as analysis and project configuration

Real datablocks map to CIF `data_<id>` blocks and therefore need a
datablock identity plus a `data_` header. Singleton sections do not.

Before this change, `DatablockItem` mixed two responsibilities:

1. owning and updating flat categories
2. representing a real CIF data block with a `data_<id>` header

That made it tempting to move `Analysis` onto `DatablockItem` just to
reuse category discovery, parameter enumeration, dirty tracking, and CIF
serialization. Doing so would have weakened the meaning of "datablock"
in the architecture and encouraged fake identities such as
`datablock_entry_name = "analysis"`.

## Decision

Introduce `CategoryOwner` as the shared abstraction for objects that own
flat CIF-like categories.

### 1. Real datablocks remain `DatablockItem`-based

`DatablockItem` now inherits from `CategoryOwner` and keeps only the
behavior specific to real CIF data blocks:

- `data_<id>` header serialization
- datablock identity via `datablock_entry_name`
- participation in `DatablockCollection`

The real datablock families remain:

- `Structure`
- `ExperimentBase` subclasses

They continue to serialize as independent CIF data blocks with
`data_<name>` headers.

### 2. `Analysis` is a category-owning singleton section

`Analysis` inherits from `CategoryOwner`, not `DatablockItem`.

It reuses shared behavior for:

- category discovery
- parameter aggregation
- category update orchestration
- dirty-flag tracking
- help display
- headerless CIF body serialization

`Analysis` remains a singleton section without a fake `data_` header. It
uses an owner-level `_serializable_categories()` policy so that only the
active sibling categories are written for the current fitting mode.
Inactive mode-specific categories remain accessible but are not
serialized.

### 3. Project configuration is a category-owning singleton section

Project-level configuration follows the same pattern via a private
`ProjectConfig(CategoryOwner)` object.

Its current children are:

- `ProjectInfo`
- `Chart`
- `Table`

The public API stays flat and user-facing:

- `project.info`
- `project.rendering_plot`
- `project.rendering_table`

Saved `project.cif` remains a section file without a `data_` header. It
serializes the `_project.*` metadata category plus the
`_rendering_plot.*` and `_rendering_table.*` configuration categories
without pretending that the project config is a real datablock.

### 4. CIF serialization is split by responsibility

Serialization is separated into two layers:

- `category_owner_to_cif(owner)` renders category bodies without a
  `data_` header
- `datablock_item_to_cif(datablock)` renders the `data_<id>` header and
  then the category-owner body

This keeps the meaning of `DatablockItem` precise while letting
singleton sections reuse the same category serialization logic.

### 5. Dirty-flag propagation is generalized to `CategoryOwner`

Descriptor changes now mark the nearest `CategoryOwner` ancestor dirty
instead of depending on `DatablockItem` specifically. Structures,
experiments, analysis, and project configuration now share the same
owner-level dirty/update contract.

## Resulting Hierarchy

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
    `-- ProjectConfig
```

## Consequences

### Positive

- The term "datablock" remains semantically precise.
- `Analysis` and project configuration reuse the standard category-owner
  behavior without becoming fake data blocks.
- CIF serialization is clearer because category-body rendering is
  separated from `data_` header rendering.
- Dirty-flag handling is consistent across all category owners.
- Project-level singleton sections now follow the same architectural
  pattern as analysis.

### Trade-offs

- The core model gains a new abstraction that must be understood and
  documented.
- Owner-level serialization policy now lives in explicit hooks such as
  `_serializable_categories()` instead of falling out of the raw object
  layout.

### Compatibility Outcomes

The implemented design preserves these contracts:

- `structure.as_cif` starts with `data_<structure_name>`
- `experiment.as_cif` starts with `data_<experiment_name>`
- `analysis.as_cif` does not start with `data_`
- `project.cif` does not emit `data_project`
- `project.parameters` remains fit-focused and does not include analysis
  configuration parameters
- saved project layout remains compatible

## Alternatives Considered

### Make `Analysis` inherit from `DatablockItem`

Rejected.

This would have been the smallest code change, but it would make
"datablock" mean both real CIF data blocks and singleton project
sections.

### Add `emit_data_header = False` to `DatablockItem`

Rejected.

This would keep reuse through inheritance but encode two different
concepts in one class and force datablock behavior to branch on whether
the object is "real enough" to emit a header.

### Keep `Analysis` fully ad hoc

Rejected.

That would preserve current behavior but keep duplicated logic for
category discovery, category updates, parameter enumeration, and CIF
section serialization.

### Make `Project` itself a `CategoryOwner`

Rejected.

`Project` is a top-level facade that coordinates structures,
experiments, analysis, display, summary, and file I/O. A smaller private
`ProjectConfig(CategoryOwner)` keeps the category-owning concern local
to the singleton project-section surface instead of mixing it into the
facade itself.

## Verification

This decision is fully implemented and was verified with:

- `pixi run fix`
- `pixi run check`
- `pixi run unit-tests`
- `pixi run integration-tests`
- `pixi run script-tests`
