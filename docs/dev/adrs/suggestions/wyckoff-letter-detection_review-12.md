# Review 12: Automatic Wyckoff Position Detection

## Findings

### [P1] Detected letters can still snap through the wrong orbit representative

The ADR correctly says the database stores the **full orbit** for each
Wyckoff position and that detection tests membership in every orbit
template (`wyckoff-letter-detection.md` 49-58, 87-92). But the snapping
decision still delegates to the "existing constraint step" after only the
letter is stored (`wyckoff-letter-detection.md` 239-240), while the
current constraint helper reads only `coords_xyz[0]` for that letter
(`crystallography.py` 177-218). That leaves a silent corruption path:
for Pm-3m `6e`, a coordinate near `(0,x,0)` can be correctly detected as
letter `e`, then `_get_wyckoff_exprs()` applies the first template
`(x,0,0)`, treats `y` and `z` as fixed, and snaps the atom toward
`(0,0,0)` instead of the matched orbit representative.

Please make the ADR settle how coordinate snapping and constrained-axis
flags choose the orbit representative. The implementation needs either
the matched/nearest template returned with the detection result or a
separate helper that selects the nearest template for an already-known
letter before snapping. The tests should include a non-first
representative, plus the explicit-letter path, so an implementer cannot
follow the ADR and leave the current `coords_xyz[0]` behavior in place.

### [P1] Space-group and setting edits do not trigger redetection

The ADR makes the Wyckoff letter, multiplicity, and
`space_group_Wyckoff` table depend on the current space-group key, but
the trigger/baseline design only tracks coordinate changes
(`wyckoff-letter-detection.md` 151-227). A public edit to
`structure.space_group.name_h_m` or
`structure.space_group.it_coordinate_system_code` marks the structure
dirty, yet the atom coordinates can be unchanged, so fill-if-empty is a
no-op and the coordinate baseline does not force re-detection. The result
can be a stale letter from the old group: it may be invalid in the new
group, or worse, still be a valid letter with different multiplicity,
site symmetry, or constrained coordinates.

Please define the space-group-change path explicitly. For example, record
the `(name_hm, coord_code)` key alongside the coordinates used for the
last detection, and re-detect/re-derive all atom-site Wyckoff values when
that key changes. The ADR also needs to settle the warning and
unsupported-group behavior for transitions into an untabulated group,
because without an auto/provided marker the old stored letter may be a
previously detected value rather than an explicit user value.

### [P2] Same-letter coordinate snaps are still silent

The ADR says neither the letter nor the coordinates change silently after
a user edit and that lenient matching movement is surfaced by a warning
(`wyckoff-letter-detection.md` 241-248, 437-439). The listed warnings do
not cover a common case: the user edits a coordinate, detection keeps the
same letter because the point is still within tolerance, and the
constraint pass snaps the coordinate back to the exact special value. In
that path the coordinate changes but the letter does not, so the
"letter changed" warning never fires.

Please either add a warning for any user coordinate edit whose constraint
snap changes stored coordinates, or narrow the ADR text so it no longer
claims this movement is surfaced. Given the project audience and the
critical-software guidance in `AGENTS.md`, warning on user-edited
coordinate movement seems like the safer policy.

## Checks skipped

Per `AGENTS.md` review-shortcut rules, this was a static ADR/source
review only. I did not run tests, `pixi run fix`, `pixi run check`, or
other verification commands.
