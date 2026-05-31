# Reply 1: Python and CIF Category Correspondence

## P1 - Resolve the `_project.*` versus `_info.*` decision

Verdict: agree.

Action taken: the ADR now explicitly keeps `_project.*` as the accepted
`project.info` exception and limits the strict
`project.<category>.<field> -> _<category>.<field>` rule to the other
EasyDiffraction-owned project-level singleton configuration categories.
It also states that this ADR does not rename `project.info.name` to
`id`, does not migrate `_project.*` to `_info.*`, and does not add an
`_info.*` compatibility layer.

Pointer: `## Decision`, `### project.info Is A Deliberate Exception`,
and `## Consequences`.

## P1 - Update the project persistence inventory

Verdict: agree.

Action taken: the current persistence layout now removes the obsolete
`project.publication`, `project.summary`, and `summary.cif` entries;
adds `project.report`, `project.rendering_structure`,
`project.structure_view`, and `project.structure_style`; and records
`project.publication` plus journal/publication tags as intentionally not
represented in v1.

Pointer: `## Current Persistence Layout`, `### Project-Level
Configuration`, and `### Not Represented In V1`.

## P2 - Refresh the constraint correspondence rows

Verdict: agree.

Action taken: the analysis table now describes the explicit row-key
model:
`analysis.constraints[id].id -> _constraint.id` and
`analysis.constraints[id].expression -> _constraint.expression`. The row
notes that older CIFs may backfill ids from the expression left-hand
side, and that `lhs_alias` / `rhs_expr` are derived Python helpers.

Pointer: `### Analysis Configuration`.

## P2 - Reconcile structure rows with the IUCr alignment decision

Verdict: agree.

Action taken: the structure table now distinguishes canonical write tags
from read aliases for the affected rows. The default-save rows now use
`_space_group.name_H-M_alt`,
`_space_group.IT_coordinate_system_code`,
`_atom_site.Wyckoff_symbol`, and `_atom_site.ADP_type`, with legacy
alternatives described as read-side aliases.

Pointer: `### Structure Configuration`.
