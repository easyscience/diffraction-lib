# Reply 5: Automatic Wyckoff Position Detection

Reply to
[`wyckoff-letter-detection_review-5.md`](wyckoff-letter-detection_review-5.md).
The single finding is accepted and addressed.

## [P2] Empty-letter sites need derived descriptor semantics

**Verdict:** Agree.

**Action taken.** Review 4 defined the empty/unsupported escape hatch
for the letter only; this extends it to the values that depend on it.
Three edits:

- **§6** now states the no-record case explicitly: when there is no
  `WyckoffPosition` record (unsupported group, or a transient empty
  letter before the first update), `multiplicity` is `None` and
  `site_symmetry` is the empty string. They track the letter's empty
  state in lockstep, and both serialise to CIF `?`.
- **§7** now specifies that the calculator skips a `None` multiplicity —
  it leaves the backend's own inferred value in place rather than
  writing `None` into the array. This is behaviour-preserving: today's
  `_update_atom_multiplicity()` already returns early when the group is
  absent from `SPACE_GROUPS`, so the no-override-on-unsupported
  behaviour is unchanged.
- **§9** write rule now notes that
  `_atom_site.site_symmetry_multiplicity` is written as `?` when the
  multiplicity is `None` — the same unsupported-group case as the
  letter. (Both are derived and ignored on read, per the existing §9
  rule, so they are recomputed rather than trusted.)

The unsupported-group escape hatch is now defined for the letter and for
both derived model values that build on it.

**Pointer:** §6 (new no-record paragraph), §7 (None-skip clause), §9
(write bullet).
