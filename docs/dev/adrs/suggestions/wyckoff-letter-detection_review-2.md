# Review 2: Automatic Wyckoff Position Detection

## Findings

### [P1] The auto-mode invariant contradicts detected letters

The updated §3 now says `empty value ⟺ auto (provided = False)`, but the
same section also says auto mode re-derives the letter and writes the
detected non-empty value through `_set_wyckoff_letter_detected()`. Those
two rules cannot both be true: after a successful auto-detection, an
auto-mode atom must have `provided = False` and a non-empty
`wyckoff_letter.value`, because calculators, constraints, displays, and
exports consume the resolved value. The invariant should be about the
provided marker, not the stored descriptor value. Please rephrase §3 so
the empty assignment is the public reset command, while auto mode itself
can hold either an empty unresolved value or a non-empty detected value.

### [P2] Project CIF needs a row-level rule for mixed auto/explicit loops

The revised §9 says project CIF writes `_atom_site.Wyckoff_symbol` only
for provided letters and writes "no symbol" for auto-mode atoms. CIF
loops are columnar, so if one atom in an atom-site loop has an explicit
symbol, every row in that loop still needs a cell for that tag. The
current project serializer also routes atom-site loops through the
ADP-family loop path in `serialize.py`, which emits the same parameter
columns for every row. The ADR should define the concrete row-level
encoding: for example, auto rows write the CIF null token (`?` or `.`)
when the column is present, and the column is omitted only when no row
in that emitted loop has a provided letter. That keeps the read-side
"non-empty loaded value means explicit" rule implementable.

## Checks skipped

Per `AGENTS.md` review-shortcut rules, this was a static ADR/source
review only. I did not run tests, `pixi run fix`, `pixi run check`, or
other verification commands.
