# ADR: Project Facade and Persistence Layout

## Status

Accepted current design.

## Date

2026-05-17

## Group

Persistence.

## Context

`Project` is the current top-level user facade. It owns project
metadata, structures, experiments, rendering preferences, display
helpers, analysis, summaries, verbosity, and save/load behavior.

The persisted project directory needs to separate real CIF datablocks
from singleton project sections.

## Decision

Use `Project` as the current top-level facade and persist projects as a
directory of CIF files:

```text
project_dir/
|-- project.cif
|-- summary.cif
|-- structures/
|-- experiments/
`-- analysis/
    `-- analysis.cif
```

Real structures and experiments serialize as `data_<id>` datablocks.
Singleton sections such as project configuration, analysis, and summary
serialize without fake `data_` headers.

## Consequences

The saved layout mirrors the current object graph while preserving the
semantic difference between real datablocks and singleton sections. A
proposed `Workspace` rename is tracked separately as an ADR suggestion.
