# Review 15: Automatic Wyckoff Position Detection

## Findings

### [P2] Compatibility still says explicit-letter projects are unaffected

The ADR now intentionally changes the explicit-letter snapping path for
non-first orbit representatives: explicit-letter snapping must choose the
nearest representative rather than `coords_xyz[0]`
(`wyckoff-letter-detection.md` 136-144, 557-561). That is the right
decision, but the Compatibility Outcomes still say projects that already
specify every Wyckoff letter are "unaffected" and "produce identical
constraints" (`wyckoff-letter-detection.md` 501-504). That is no longer
strictly true for an existing project whose explicit letter is paired
with coordinates on a non-first representative, such as Pm-3m `6e`
`(0,x,0)`: the new behavior deliberately fixes the current
`coords_xyz[0]` snap.

Please soften that compatibility claim. A more accurate outcome is that
explicit letters remain respected and reload verbatim, while constraints
are unchanged except where the current first-representative shortcut was
wrong for coordinates on a different representative. That makes the
intended compatibility surface clear without hiding the bug fix.

## Checks skipped

Per `AGENTS.md` review-shortcut rules, this was a static ADR/source
review only. I did not run tests, `pixi run fix`, `pixi run check`, or
other verification commands.
