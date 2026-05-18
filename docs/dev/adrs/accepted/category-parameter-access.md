# ADR: Two-Level Category Parameter Access

## Status

Accepted.

## Date

2026-05-17

## Group

Core model.

## Context

EasyDiffraction models CIF concepts as datablocks, categories, category
collections, and parameters. Users need predictable navigation paths
from a structure or experiment to any parameter.

## Decision

Use at most two navigation levels from a datablock to a parameter:

```python
structure.cell.length_a = 3.88
experiment.instrument.setup_wavelength = 1.494
structure.atom_sites['Si'].adp_iso = 0.47
experiment.background['10'].y = 170
```

The general forms are:

- `DATABLOCK.CATEGORY_ITEM.PARAMETER`
- `DATABLOCK.CATEGORY_COLLECTION[ITEM_ID].PARAMETER`

Categories are flat siblings under their owner. A category must not own
another category of a different type.

## Consequences

API paths remain short, regular, and close to CIF category structure.
Nested category designs are rejected because they make parameter access
depth depend on the domain area and obscure the CIF-like model.
