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
|   |-- open.md
|   `-- closed.md
|-- package-structure/
|   |-- full.md
|   `-- short.md
|-- plans/
`-- roadmap/
    `-- ROADMAP.md
```

Use lowercase directory names for new development-doc folders. Keep
`ROADMAP.md` uppercase because it may later be copied into published
user documentation where the conventional filename is useful.

Use `docs/dev/adrs/index.md` as the architecture and decision navigation
surface. Do not keep a separate architecture overview that duplicates
ADR content.

## Consequences

- Development documentation remains under the documentation tree without
  being part of the published MkDocs source by default.
- ADRs have one entry point for architecture navigation and separate
  accepted and proposed areas.
- Package-structure snapshots have stable, script-friendly paths.
- Roadmap publication can later be implemented as a build-time copy from
  `docs/dev/roadmap/ROADMAP.md` into `docs/docs`.
