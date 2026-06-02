# Review 5: Automatic Wyckoff Position Detection

## Findings

### [P2] Empty-letter sites need derived descriptor semantics

Review 4 resolved how an unsupported space group serialises the
`wyckoff_letter`: detection is a no-op, the letter stays empty, and CIF
writes `?`. The ADR still does not define what happens to the derived
`multiplicity` and `site_symmetry` descriptors in that same path.
Section 6 says they are populated from a `WyckoffPosition` record, but
unsupported groups and transient empty letters have no such record; §7
then replaces cryspy's private lookup with
`atom_site.multiplicity.value`, and §9 says project CIF emits
`_atom_site.site_symmetry_multiplicity` derived from the model
multiplicity. An implementation needs a clear contract for the no-record
case: for example, multiplicity/site symmetry become empty/`None`, CIF
writes `?` for multiplicity, and calculators skip over the missing value
instead of writing it into backend arrays. Without that rule, the
unsupported-group escape hatch is only defined for the letter, not for
the model values that now depend on it.

## Checks skipped

Per `AGENTS.md` review-shortcut rules, this was a static ADR/source
review only. I did not run tests, `pixi run fix`, `pixi run check`, or
other verification commands.
