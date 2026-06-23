# ADR: Development Documentation Structure

## Status

Accepted.

## Date

2026-05-17

## Group

Documentation.

## Context

Development notes, ADRs, roadmap material, package-structure snapshots,
and issue backlogs were all kept directly under `docs/dev` or under
mixed-case directories. That made the development documentation harder
to scan and created several competing naming conventions.

The repository also contains `docs/docs`, which is the MkDocs source for
published user documentation. Development-only material should not be
mixed into that tree unless it is intentionally published.

## Decision

Keep development-only documentation under `docs/dev`.

Use this structure:

```text
docs/dev/
|-- index.md
|-- adrs/
|   |-- index.md
|   |-- accepted/
|   `-- suggestions/
|-- issues/
|   |-- index.md
|   |-- open/
|   `-- closed/
|-- package-structure/
|   |-- full.md
|   `-- short.md
`-- plans/
```

Issues are one Markdown file per issue under `issues/open/` and
`issues/closed/`, with `issues/index.md` as the table of contents (not
flat `open.md` / `closed.md` files).

Use lowercase directory names for new development-doc folders. The
feature/roadmap matrix is published directly in the user documentation
at `docs/docs/features/index.md` (single source of truth for both
current capabilities and planned work); there is no separate
`docs/dev/roadmap/` copy.

Use `docs/dev/adrs/index.md` as the architecture and decision navigation
surface. Do not keep a separate architecture overview that duplicates
ADR content.

## Consequences

- Development documentation remains under the documentation tree without
  being part of the published MkDocs source by default.
- ADRs have one entry point for architecture navigation and separate
  accepted and proposed areas.
- Package-structure snapshots have stable, script-friendly paths.
- The roadmap is published directly as a user-facing page at
  `docs/docs/features/index.md`, kept in sync with the codebase.
