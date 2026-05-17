# ADR: Workspace Root and Project Information Category

**Status:** Proposed  
**Date:** 2026-05-17

## Context

The current public root object is `Project`. It acts as the top-level
facade for an EasyDiffraction working session:

```python
project = ed.Project(name='lbco_hrpt')
project.structures
project.experiments
project.analysis
project.display
project.summary
project.save()
```

The same word, "project", is also the natural CIF category name for
information about the scientific project:

```cif
_project.id
_project.title
_project.description
_project.created
_project.last_modified
```

This creates a naming conflict. The root object is a broad runtime
facade, while the `_project.*` category is only information about the
scientific project. Using the same name for both makes category naming
awkward:

```python
project.project_info.title
project.config.project_info.title
project.project.title
```

At the same time, replacing `_project.*` with a generic `_meta.*`
category would weaken the CIF model:

```cif
_meta.project_id
_meta.project_title
```

The category name `meta` is too generic. It forces each item name to
repeat what the category should already communicate. The existing
`_project.id` and `_project.title` names are more semantic and better
aligned with the repository rule to follow CIF naming unless there is a
clearly better API.

The design question is therefore:

- should the top-level runtime object remain `Project`, and project
  information move to a different category such as `meta`;
- or should the top-level runtime object be renamed to `Workspace`, so
  `project` can be used cleanly for project information?

## Decision

Rename the top-level runtime facade from `Project` to `Workspace`.

Use `project` as the public project-information category under the
workspace:

```python
workspace = ed.Workspace(project_id='lbco_hrpt')
workspace.project.id
workspace.project.title = 'La0.5Ba0.5CoO3 at HRPT@PSI'
workspace.rendering.table_engine = 'rich'
workspace.verbosity = 'short'
workspace.structures
workspace.experiments
workspace.analysis
```

Persist workspace-level singleton categories in `workspace.cif`:

```cif
_project.id
_project.title
_project.description
_project.created
_project.last_modified

_rendering.chart_engine
_rendering.table_engine

_verbosity.level
```

The saved directory is a workspace directory whose filesystem name is
chosen by the user. The canonical layout is:

```text
<workspace-dir>/
|-- workspace.cif
|-- structures/
|   `-- cosio.cif
|-- experiments/
|   `-- d20.cif
|-- analysis/
|   `-- analysis.cif
`-- summary/
    `-- summary.cif
```

Do not introduce `_meta.*` CIF tags. Do not use `project.cif`,
`config.cif`, or `meta.cif` as the primary singleton configuration file
in the target layout.

The intended naming split is:

```text
Workspace
|-- project      # information about the scientific project
|-- rendering    # rendering preferences
|-- verbosity    # console/output verbosity preference
|-- structures   # real structure datablocks
|-- experiments  # real experiment datablocks
|-- analysis     # analysis section
|-- display      # display facade
`-- summary      # summary/report facade
```

## Rationale

### `Workspace` better describes the top-level facade

The top-level object is more than project metadata. It owns active
collections, analysis state, display helpers, save/load behavior, and
runtime orchestration. `Workspace` describes that broader role without
consuming the domain word `project`.

The name is also familiar in scientific software. It commonly means an
active analysis environment, a data/model container, or a working area.
That is close to the role of the current EasyDiffraction root object.

### `project` is the right category name for project information

Project information is not generic metadata. It is specifically the
identity, title, description, and timestamps of the scientific project.

This reads cleanly:

```python
workspace.project.title
```

and maps directly to clean CIF:

```cif
_project.title
```

### `_meta.project_title` is weaker than `_project.title`

The `_meta` category would make the CIF less domain-oriented. It also
creates longer and more repetitive item names:

```cif
_meta.project_id
_meta.project_title
_meta.project_description
```

The existing `_project.*` tags are clearer:

```cif
_project.id
_project.title
_project.description
```

### This keeps layer-specific consistency

After this decision, each layer has a clear rule:

| Layer           | Rule                           | Example             |
| --------------- | ------------------------------ | ------------------- |
| Runtime root    | working-session facade         | `Workspace`         |
| Public category | semantic category name         | `workspace.project` |
| CIF category    | semantic CIF category          | `_project.*`        |
| Config file     | workspace singleton categories | `workspace.cif`     |

This avoids one-off aliases such as `project.info` while preserving
semantic CIF names.

### `workspace.cif` is clearer than `project.cif`, `config.cif`, or `meta.cif`

The file stores singleton settings owned by the workspace: scientific
project information, rendering preferences, and verbosity. `project.cif`
overloads the project name again, while `config.cif` and `meta.cif` are
generic. `workspace.cif` names the owning layer and lets each category
inside the file keep its domain-specific name.

## Consequences

### Positive

- The root object and project-information category no longer share the
  same conceptual name.
- Public access becomes uniform: `workspace.project`,
  `workspace.rendering`, `workspace.verbosity`, `workspace.analysis`.
- CIF stays semantic and does not introduce `_meta.*`.
- Workspace-level preferences such as rendering and verbosity are saved
  with the workspace instead of being hidden runtime-only state.
- Project information can use short item names such as `id`, `title`,
  and `description`.
- The top-level facade name better reflects active runtime
  orchestration.

### Negative

- This is a breaking public API change.
- Tutorials, scripts, tests, docs, type hints, and imports must be
  updated from `Project` to `Workspace`.
- Existing saved directories using `project.cif` must be migrated to
  `workspace.cif` if no compatibility loader is kept.
- Existing code that expected verbosity to be runtime-only must account
  for it round-tripping through `workspace.cif`.
- Users familiar with `Project` must learn the new root name.
- `Workspace` can be confused with a filesystem workspace in some
  ecosystems, so documentation must define it clearly as the active
  EasyDiffraction working object.

## Compatibility Policy

EasyDiffraction is in beta, and repository instructions say not to keep
legacy shims by default.

Therefore the target implementation should not add a permanent
`Project = Workspace` alias unless explicitly approved before
implementation.

The migration plan still includes a review gate before removing the old
`Project` public symbol, because this is a user-facing breaking change.

## Alternatives Considered

### Keep `Project` root and rename project information to `meta`

Rejected.

Example:

```python
project.meta.project_title
```

```cif
_meta.project_title
```

This keeps the root class stable, but it weakens the category model.
`meta` is too broad, and the CIF item names become repetitive.

### Keep `Project` root and use `project.config.project`

Rejected for now.

Example:

```python
project.config.project.title
```

This is technically consistent, but it still repeats `project` at
different semantic layers. It also adds depth to common user workflows.
It is a reasonable fallback if the public root rename is rejected.

### Keep `Project` root and use `project.info`

Rejected for the target design.

Example:

```python
project.info.title
```

This is readable, but it preserves a special-case category alias. The
current goal is stronger consistency between public categories and CIF
category concepts.

### Use `project.cif`, `config.cif`, or `meta.cif` for singleton settings

Rejected for the target layout.

`project.cif` repeats the overloaded term that this migration removes.
`config.cif` and `meta.cif` are too generic and do not say which layer
owns the settings. `workspace.cif` is more explicit while still allowing
semantic categories such as `_project`, `_rendering`, and `_verbosity`
inside the file.

### Rename only internal files and keep public API unchanged

Rejected for the target design.

This improves implementation clarity but does not solve the public
naming inconsistency.

### Use `Study` instead of `Workspace`

Rejected.

`Study` is a plausible scientific term, but it is less established for
an active computational container. It also does not map as naturally to
save/load, display, and analysis orchestration.

## Implementation Notes

The implementation should follow:

```text
docs/dev/plans/workspace-root-project-category.md
```

The high-level migration is:

1. Rename the root facade `Project` to `Workspace`.
2. Rename the project package/module surface from `project` to
   `workspace`.
3. Rename `ProjectConfig` to `WorkspaceConfig`.
4. Rename project-level category access from `info` to `project`.
5. Rename project-information `name` access to `id`, matching
   `_project.id`.
6. Move the storage path to `Workspace.path`, because it describes the
   saved workspace directory rather than project information.
7. Keep the information category class named `ProjectInfo` unless a
   later decision chooses `ProjectMetadata`.
8. Keep CIF tags `_project.*` and `_rendering.*`.
9. Rename saved singleton config file from `project.cif` to
   `workspace.cif`.
10. Persist workspace verbosity in `workspace.cif` as
    `_verbosity.level`.
11. Update code, tests, scripts, tutorials, docs, and ADR references.

## Post-Implementation ADR Update

This ADR must be updated after the migration plan is implemented.

When implementation is complete:

1. Change status from `Proposed` to `Accepted and implemented`.
2. Record the final public API and saved file layout.
3. Record whether a temporary or permanent `Project` compatibility alias
   was approved.
4. Record any deviations from the migration plan.
5. Move this file from `docs/dev/adrs/suggestions/` to
   `docs/dev/adrs/accepted/` if the decision is accepted.
6. Update `docs/dev/adrs/index.md` and related accepted ADRs if the ADR
   map changes.
7. Update or close related items in `docs/dev/issues/open.md`.

## Acceptance Criteria

This ADR is satisfied when:

- `ed.Workspace` is the public top-level facade.
- `ed.Project` is removed unless explicitly approved as an alias.
- the public project-information category is `workspace.project`.
- project identity is exposed as `workspace.project.id`.
- the saved directory path is exposed as `workspace.path`.
- the public rendering category is `workspace.rendering`.
- saved singleton configuration lives in `workspace.cif`.
- `workspace.cif` uses `_project.*`, `_rendering.*`, and
  `_verbosity.level` tags.
- no `_meta.*` tags are introduced for project information.
- tutorials and accepted ADRs use `Workspace`.
