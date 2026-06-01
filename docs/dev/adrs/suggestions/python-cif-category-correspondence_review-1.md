# Review 1: Python and CIF Category Correspondence

## Findings

### P1 - Resolve the `_project.*` versus `_info.*` decision

The decision text says to adopt the strict project-level mapping
`project.<category>.<field> -> _<category>.<field>` at
`python-cif-category-correspondence.md:223`, but the next paragraph
keeps the accepted baseline `project.info.<field> -> _project.<field>`
at `python-cif-category-correspondence.md:233`. The consequences then
still discuss `_info.*` migration risk at
`python-cif-category-correspondence.md:327`. As written, an implementer
cannot tell whether accepting this ADR should keep `_project.*` or
supersede it with `_info.*`. Please choose one explicit decision: either
keep `_project.*` and define strict correspondence as applying only to
the other project-owned singleton categories, or explicitly propose a
superseding `_project.*` -> `_info.*` migration with the compatibility
policy.

### P1 - Update the project persistence inventory

The "Current Persistence Layout" table still lists `project.publication`
and `project.summary` / `summary.cif` at
`python-cif-category-correspondence.md:61` and
`python-cif-category-correspondence.md:66`, and the "Not Yet Mapped"
section repeats `project.summary` at
`python-cif-category-correspondence.md:215`. Those are rejected by the
accepted project-facade/report decisions: report metadata now goes
through `project.report`, `summary.cif` is not part of the save layout,
and `project.publication` is deferred from v1. The same inventory also
omits current persisted project-level structure rendering categories
such as `project.rendering_structure`, `project.structure_view`, and
`project.structure_style`. Please refresh the table before this ADR is
accepted so it does not reintroduce removed surfaces or omit active
project configuration categories.

### P2 - Refresh the constraint correspondence rows

The analysis table says `analysis.constraints[lhs_alias].expression`
maps to `_constraint.expression` and notes that the key is derived from
the expression at `python-cif-category-correspondence.md:105`. That was
superseded by the accepted loop-key ADR: constraints now have an
explicit serialized `_constraint.id` key, while `lhs_alias` and
`rhs_expr` are derived helpers from the expression. Please update this
section to describe `analysis.constraints[id].id -> _constraint.id` and
`analysis.constraints[id].expression -> _constraint.expression`, so
future correspondence work does not preserve the old implicit-key model.

### P2 - Reconcile structure rows with the IUCr alignment decision

The structure table still treats `_atom_site.adp_type` as the direct
current mapping at `python-cif-category-correspondence.md:206` and lists
legacy/capitalization alternatives for Wyckoff and space-group tags at
`python-cif-category-correspondence.md:196` and
`python-cif-category-correspondence.md:203`. The accepted IUCr alignment
ADR made the default-save structure tier dictionary-aligned, including
canonical `_atom_site.ADP_type`, `_atom_site.Wyckoff_symbol`,
`_space_group.name_H-M_alt`, and
`_space_group.IT_coordinate_system_code` on write, with legacy aliases
accepted on read. Please update the current-correspondence rows so this
ADR remains the Python-side companion to the accepted CIF-side policy.

## Checks

Static ADR review only. Per `/review-adr`, I did not edit the ADR under
review, run tests, run formatters, run build commands, or invoke `pixi`.
