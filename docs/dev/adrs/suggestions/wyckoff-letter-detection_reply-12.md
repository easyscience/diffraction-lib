# Reply 12: Automatic Wyckoff Position Detection

Reply to
[`wyckoff-letter-detection_review-12.md`](wyckoff-letter-detection_review-12.md).

## [P1] Detected letters can still snap through the wrong orbit representative

**Verdict:** Agree.

**Action taken.** The ADR now requires representative selection. The
`WyckoffPosition` record carries a selected `coord_template`;
`detect_wyckoff_position()` returns the nearest matched representative
inside the winning orbit, and explicit-letter snapping calls
`wyckoff_position_info(..., fract_xyz=current_coords)` to choose the
nearest representative for that letter. The ADR explicitly rejects using
`coords_xyz[0]` for snapping and calls out the Pm-3m `6e` non-first
representative case. Tests now include auto-detection and explicit-letter
snapping through a non-first representative.

**Pointer:** Decision §2 ("Representative selection") and Testing.

## [P1] Space-group and setting edits do not trigger redetection

**Verdict:** Agree.

**Action taken.** The ADR now treats space-group key changes as a
first-class trigger. The update flow records the `(name_hm, coord_code)`
key used for the last Wyckoff derivation. If the key changes, every atom
site re-runs the supported/unsupported policy even when coordinates are
unchanged. Supported new keys re-detect all letters and multiplicities;
unsupported new keys preserve stored letters verbatim as unvalidated
values, set multiplicity to `None`, skip constraints, and warn that the
group is untabulated. The user-set-letter persistence language was
updated to include space-group-key edits as a re-detection trigger.

**Pointer:** Decision §§3-5, Trade-offs, Alternatives Considered, and
Testing.

## [P2] Same-letter coordinate snaps are still silent

**Verdict:** Agree.

**Action taken.** The ADR now adds an explicit warning for user
coordinate edits whose constraint snap changes stored coordinates even
when the detected letter stays the same:
_"coordinates of <site> were adjusted to satisfy Wyckoff letter L"_.
Testing now covers same-letter coordinate edits whose snap moves stored
coordinates.

**Pointer:** Decision §5 and Testing.
