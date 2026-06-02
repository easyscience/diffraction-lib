# Reply 4: Automatic Wyckoff Position Detection

Reply to
[`wyckoff-letter-detection_review-4.md`](wyckoff-letter-detection_review-4.md).
Both findings accepted. The serializer's empty-string behaviour was
verified before editing.

## [P1] Live descriptor edits can bypass re-detection

**Verdict:** Agree.

**Action taken.** This is the reason the §4 mechanism was previously
left open; the finding settles it. A coordinate is a live `Parameter`,
so `atom.fract_x.value = 0.1` is a normal public edit that never reaches
an `AtomSite.fract_x` property setter — a setter hook would silently
miss it and leave a stale letter. Rewrote §4 to put both triggers in the
**update flow** instead: every public coordinate edit (property _or_
`.value`) marks the owner dirty and runs `_update()`, so that is the one
place that sees them all. Re-detection now compares the current
coordinates against a per-atom baseline (the coordinates the letter was
last detected from) and fires when they differ. The baseline is
refreshed whenever the letter is set or detected — on load, on a user
letter-set, and after auto-detection including the constraint snap — so
a freshly loaded or user-set letter is not re-detected spuriously. The
minimizer (`called_by_minimizer=True`) and the constraint snap are
explicitly excluded. Updated the §3 coordinate bullet to name both
public paths and point to §4.

**Pointer:** §4 (rewritten), §3 (coordinate bullet).

## [P2] Unsupported groups contradict "always concrete" CIF writes

**Verdict:** Agree.

**Action taken.** Qualified the over-broad "concrete at all times"
claim. §3 now reads: concrete for every _supported_ space group; a group
absent from `SPACE_GROUPS` (§8) is the one exception — detection is a
no-op and the letter stays empty, with §9 defining how that serialises.
Verified that the serializer already renders an empty string as the CIF
null `?`
([`serialize.py:62`](../../../../src/easydiffraction/io/cif/serialize.py))
and reads `?` back as the empty default
([`serialize.py:1091`](../../../../src/easydiffraction/io/cif/serialize.py)).
§9's write rule is now explicit: a resolved letter is written as-is; an
empty letter (unsupported group, or a transient not-yet-updated state)
is written as `?`, reads back empty, and round-trips as empty (detection
stays a no-op on reload). The column is always present and well-defined
for the columnar loops, and saving never fails on an unsupported group.
The §9 read bullet now notes the "stays empty when unsupported" case.

**Pointer:** §3 (opening), §9 (intro, write and read bullets).

## Note

The §4-mechanism item in Open Questions is now resolved by this round
(it is decided in §4), so it was removed; the only remaining open
question is tuning the `1e-3` tolerance value.
