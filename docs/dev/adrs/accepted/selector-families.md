# ADR: Selector Families

## Status

Accepted.

## Date

2026-05-17

## Group

User-facing API.

## Context

Several public names use a selector-like shape, but they do not all mean
the same thing. Treating every `<name>_type` as a switchable category
would blur distinct concepts.

## Decision

This ADR is amended by
[`switchable-category-owned-selectors.md`](switchable-category-owned-selectors.md).
The family names now describe the owner-side mechanism, not distinct
public selector surfaces. All three families share the same public
shape:

```python
category.type = 'new-type'
category.show_supported()
```

The owner exposes the category itself and implements a private
`_swap_<name>` hook. That hook determines whether the assignment swaps a
category instance, rebinds a live backend behind a singleton category,
or activates sibling categories.

Recognize three selector families:

| Family                       | User intent                     | Examples                                                                                    |
| ---------------------------- | ------------------------------- | ------------------------------------------------------------------------------------------- |
| Backend selector             | Pick an execution backend       | `experiment.calculator.type`, `project.rendering_plot.type`, `project.rendering_table.type` |
| Switchable-category selector | Swap a category implementation  | `analysis.minimizer.type`, `experiment.background.type`, `experiment.peak.type`             |
| Active-sibling selector      | Pick the active sibling surface | `analysis.fitting_mode.type`                                                                |

Backend selectors live on dedicated configuration categories.
Switchable-category selectors live on the category they replace, and the
owner swaps the instance behind the same public property. Active-sibling
selectors also live on a category and the owner decides which sibling
categories are visible, authoritative, and serialized.

## Consequences

Selector names stay familiar without forcing one implementation pattern
onto different concepts. Future selectors should declare which family
they belong to before adding API.
