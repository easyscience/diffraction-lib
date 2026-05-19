# ADR: Notebook Generation Source of Truth

## Status

Accepted.

## Date

2026-05-17

## Group

Documentation.

## Context

Tutorial notebooks are published as `.ipynb` files, but editing notebook
JSON by hand creates noisy diffs and inconsistent formatting.

## Decision

Treat tutorial `.py` files under `docs/docs/tutorials/` as the editable
source of truth. Regenerate notebooks with:

```shell
pixi run notebook-prepare
```

Do not edit generated `.ipynb` tutorial files by hand.

## Consequences

Tutorial diffs stay reviewable, and notebooks are regenerated through
the same script path used by the documentation workflow.
