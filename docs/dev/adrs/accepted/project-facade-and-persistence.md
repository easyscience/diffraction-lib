# ADR: Project Facade and Persistence Layout

## Status

Accepted current design.

## Date

2026-05-17

## Group

Persistence.

## Context

`Project` is the top-level user facade. It owns project metadata,
structures, experiments, rendering preferences, display helpers,
analysis, report helpers, publication metadata, verbosity, and save/load
behavior.

A later proposal considered renaming this facade to `Workspace` so that
`project` could be reserved for the scientific project information
category. The final naming decision is to keep `Project` as the public
root because it matches scientific user language and the saved project
container.

The persisted project directory needs to separate real CIF datablocks
from singleton project sections.

## Decision

Use `Project` as the top-level facade and persist projects as a
directory of CIF files:

```text
project_dir/
|-- project.cif
|-- structures/
|-- experiments/
|-- analysis/
|   `-- analysis.cif
`-- reports/
    `-- <project>.cif
```

Real structures and experiments serialize as `data_<id>` datablocks.
Singleton sections such as project configuration and analysis serialize
without fake `data_` headers. Journal-submission reports are generated
through `project.report` and written only when requested, using
`reports/<project>.cif`; default project saves do not write
`summary.cif`.

Expose submission-report helpers as `project.report`. This facade is a
hybrid surface: its scalar output configuration persists to
`project.cif` as `_report.*`, while its methods render report artifacts
under `reports/`. The previous `project.summary` placeholder and its
`summary.cif` output are not part of the persistence layout.

Expose journal-submission metadata as `project.publication`. It is a
top-level owner with CIF-aligned sibling categories for `_journal.*`,
`_journal_date.*`, `_journal_coeditor.*`, `_publ_contact_author.*`,
`_publ_body.*`, and the `_publ_author.*` loop. These singleton
publication categories persist in `project.cif` and feed report exports;
`reports/<project>.cif` remains export-only.

Keep project information available as `project.info`. The Python name
avoids a confusing `project.project` access path, while the persisted
CIF category remains the semantic `_project.*` category:

```cif
_project.id
_project.title
_project.description
_project.created
_project.last_modified
```

Do not introduce `_meta.*` tags for project information. The category is
scientific project information, not generic metadata. Any future change
from `_project.*` to another category name must be a separate explicit
persistence decision.

Keep `project.cif` as the primary singleton project configuration file
while `Project` remains the root facade. Do not rename it to
`workspace.cif` as a side effect of category cleanup.

The saved project directory path is runtime file-I/O state, not a
serialized project-information field. If the path is exposed in Python,
it must not emit a `_project.path` CIF item.

The project-level singleton categories currently persisted in
`project.cif` are `_project.*`, `_rendering_plot.*`, `_report.*`,
`_rendering_table.*`, `_verbosity.*`, `_journal.*`, `_journal_date.*`,
`_journal_coeditor.*`, `_publ_contact_author.*`, `_publ_body.*`, and the
`_publ_author.*` loop.

## Consequences

The saved layout mirrors the current object graph while preserving the
semantic difference between real datablocks and singleton sections. The
`Workspace` rename proposal is rejected; ADR examples should continue to
use `Project`, `project.info`, and `project.cif` unless a later accepted
ADR changes a narrower part of this design.
