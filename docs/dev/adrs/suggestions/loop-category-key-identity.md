# ADR: Loop Category Keys and Identity Naming

**Status:** Proposed  
**Date:** 2026-05-18

## Context

CIF dictionaries can declare the key column for a loop category through
`_category_key.name`. For example, crystallographic categories commonly
use domain-specific identity tags such as `_atom_site.label`, while
other loop categories may use an explicit `id` tag.

EasyDiffraction currently models the same runtime concept with
`item._identity.category_entry_name`. `CategoryCollection` uses this
value as the collection key, and category items use it in their
`unique_name` path:

```text
<datablock>.<category_code>.<category_entry_name>
```

The design question is whether the current `category_entry_name`
approach is enough, and how closely Python-facing identity names should
follow CIF key tags.

## Assessment

The current approach is directionally good. It gives every loop item a
stable collection key without hard-coding the key field into
`CategoryCollection`, and most current loop categories derive that key
from the same field that is serialized into CIF.

It is not explicit enough yet. The key field is encoded as a lambda on
each item, not as declarative metadata on the category or descriptor.
Nothing validates that the runtime key corresponds to a serialized CIF
field. The main visible example is `Constraint`: the current collection
key is derived from the left-hand side of `_constraint.expression`, but
no separate `_constraint.id` field is persisted.

## Decision

Keep `category_entry_name` as the runtime analogue of CIF
`_category_key.name`, and formalize the rule:

1. Every concrete `CategoryCollection` should have a documented key
   field.
2. The key should normally be a public descriptor on the item.
3. The key descriptor should normally be serialized to CIF.
4. Standard CIF categories should keep CIF names in Python where those
   names are already meaningful to scientists.
5. Custom categories should prefer `id` only for opaque machine
   identity. Use `label` or `*_id` when the value has clearer domain
   meaning.

The `constraint` category should add an explicit `id` field and use it
as the collection key:

```text
analysis.constraints[id].id -> _constraint.id
```

The existing `lhs_alias` and `rhs_expr` properties should remain derived
helpers from `_constraint.expression`, not the row identity.

This argues against a blanket Python API change to use `id` everywhere.
For scientists moving between notebooks and saved CIF, `atom_site.label`
in Python and `_atom_site.label` in CIF is less surprising than
`atom_site.id` in Python and `_atom_site.label` in CIF.

## Loop Category Keys

Rows are sorted by the chosen Python key style: `id`, then `*_id`, then
`label`. This table lists fields that drive `category_entry_name`;
identifier-like fields that are not collection keys are listed in the
next section.

| Python key      | Area       | Collection class                            | Category code            | CIF key tag                  | Source                      | Decision                                                                                             |
| --------------- | ---------- | ------------------------------------------- | ------------------------ | ---------------------------- | --------------------------- | ---------------------------------------------------------------------------------------------------- |
| `id`            | Analysis   | `Constraints`                               | `constraint`             | `_constraint.id`             | Custom category             | Add this key. Current implementation derives the key from the left side of `_constraint.expression`. |
| `id`            | Analysis   | `SequentialFitExtractCollection`            | `sequential_fit_extract` | `_sequential_fit_extract.id` | Custom category             | Keep. It is an explicit row identifier for extraction rules.                                         |
| `id`            | Experiment | `LineSegmentBackground`                     | `background`             | `_pd_background.id`          | Powder CIF-style category   | Keep. The row identity is opaque and already serialized.                                             |
| `id`            | Experiment | `ChebyshevPolynomialBackground`             | `background`             | `_pd_background.id`          | Powder CIF-style category   | Keep. The row identity is opaque and shared with other background variants.                          |
| `id`            | Experiment | `LinkedPhases`                              | `linked_phases`          | `_pd_phase_block.id`         | Powder CIF-style category   | Keep. Consider `phase_id` only if the public API later standardizes foreign-key names.               |
| `id`            | Experiment | `ExcludedRegions`                           | `excluded_regions`       | `_excluded_region.id`        | Custom category             | Keep. It is a simple custom loop row identifier.                                                     |
| `id`            | Experiment | `ReflnData`                                 | `refln`                  | `_refln.id`                  | CIF-style category          | Keep for the current reflection table shape.                                                         |
| `id`            | Experiment | `PowderCwlReflnData` / `PowderTofReflnData` | `refln`                  | `_refln.id`                  | CIF-style category          | Keep; `phase_id` remains a separate field, not the row key.                                          |
| `experiment_id` | Analysis   | `JointFitCollection`                        | `joint_fit`              | `_joint_fit.experiment_id`   | Custom category             | Keep. The key is a reference to an experiment, so `id` alone would lose context.                     |
| `point_id`      | Experiment | `PdCwlData` / `PdTofData`                   | `pd_data`                | `_pd_data.point_id`          | Powder CIF-style category   | Keep. It is clearer than `id` for dense measured/calculated data points.                             |
| `point_id`      | Experiment | `TotalData`                                 | `total_data`             | `_pd_data.point_id`          | Current powder-data mapping | Keep. Revisit the CIF tag only when total-scattering-specific CIF tags are introduced.               |
| `label`         | Analysis   | `Aliases`                                   | `alias`                  | `_alias.label`               | Custom category             | Keep. It is the user-visible symbol referenced by expressions, not an opaque row id.                 |
| `label`         | Structure  | `AtomSites`                                 | `atom_site`              | `_atom_site.label`           | CIF core category           | Keep. This is a well-known crystallographic identity field.                                          |
| `label`         | Structure  | `AtomSiteAnisoCollection`                   | `atom_site_aniso`        | `_atom_site_aniso.label`     | CIF core category           | Keep. It intentionally matches and references the atom-site label.                                   |

## Non-Key Identity And Reference Fields

These fields are serialized in loop rows and look identity-like, but
they do not define the collection key.

| Python field        | Area       | Collection class                            | Category code | CIF tag                    | Role                                                                                  |
| ------------------- | ---------- | ------------------------------------------- | ------------- | -------------------------- | ------------------------------------------------------------------------------------- |
| `phase_id`          | Experiment | `PowderCwlReflnData` / `PowderTofReflnData` | `refln`       | `_refln.phase_id`          | References the linked phase for a calculated reflection. Row key remains `_refln.id`. |
| `param_unique_name` | Analysis   | `Aliases`                                   | `alias`       | `_alias.param_unique_name` | References the target parameter. Row key remains `_alias.label`.                      |

## Naming Guidance

Use `label` when the identity is a user-visible, domain-specific symbol.
This applies to atom sites and aliases. A label is not weaker than an
`id` if the category defines it as the key.

Use `id` when the identity is an opaque row identifier without a richer
domain word. This applies to excluded regions, background terms,
sequential-fit extraction rules, and current reflection rows.

Use `*_id` when the identity is primarily a reference to another object.
This applies to `experiment_id` and `point_id`. It keeps the public API
clearer than a generic `id` while still expressing uniqueness within the
collection.

Avoid renaming standard CIF identity fields in Python unless the CIF
name is actively hostile to the user-facing model. Each intentional
Python/CIF mismatch adds translation cost for users who move between
Jupyter, CLI output, and saved CIF files.

## Implementation Notes

The current `category_entry_name` mechanism can stay, but it should be
made easier to audit. A future implementation should add metadata that
identifies the key descriptor for each `CategoryCollection`, or at least
tests that the resolved key comes from a serialized descriptor.

For constraints, add a descriptor-backed `id` property serialized as
`_constraint.id`, and change `category_entry_name` to resolve from that
descriptor. Keep `_constraint.expression` for the full equation. Keep
`lhs_alias` and `rhs_expr` as derived convenience properties.

When reading older CIF files that only contain `_constraint.expression`,
derive a deterministic fallback `id` from the old `lhs_alias` key, then
write `_constraint.id` on the next save.

## Consequences

Keeping CIF names where possible improves notebook-to-CIF continuity and
makes saved files easier to inspect. It also reduces the amount of
documentation needed to explain common crystallographic terms such as
`atom_site.label`.

Allowing custom categories to use `id`, `label`, or `*_id` means the API
will not be mechanically uniform, but it will be semantically clearer.
Uniformity should come from documented key metadata and predictable
collection behavior, not from forcing every row key to be named `id`.

## References

- [COMCIFS `cif_core.dic`](https://github.com/COMCIFS/cif_core/blob/main/cif_core.dic)
- [IUCr Core CIF dictionary browser](https://www.iucr.org/resources/cif/dictionaries/browse/cif_core)
