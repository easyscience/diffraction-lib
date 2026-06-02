# Reply 1: Automatic Wyckoff Position Detection

Reply to
[`wyckoff-letter-detection_review-1.md`](wyckoff-letter-detection_review-1.md).
All five findings accepted; the ADR was updated as described below. One
finding (P2 key normalisation) was verified empirically against the
bundled table before editing.

## [P1] Persisting resolved letters loses auto-mode semantics

**Verdict:** Agree.

**Action taken.** Rewrote §9 "CIF behaviour". The project (round-trip)
CIF now writes `_atom_site.Wyckoff_symbol` **only for provided
(explicit) letters**; auto-mode atoms write no symbol and are
deterministically re-derived on load (same coordinates + space group →
same letter). This preserves both the value and the auto/provided
behaviour across save/load, so the contradiction with persisted-state
restore is gone. I also updated §4 (load is a non-minimizer update that
rebuilds the omitted letter), the Positive bullet on round-trips, and
the Compatibility Outcomes bullet to match the new rule. The IUCr report
export still emits every resolved letter, but it is now explicitly
described as a non-round-trip archival path.

**Pointer:** §9, §4, Consequences → Positive and Compatibility Outcomes.

## [P1] Empty string cannot both mean auto and explicit assignment

**Verdict:** Agree.

**Action taken.** Rewrote §3 to give the empty sentinel a single,
documented reset meaning: assigning a non-empty letter sets
`provided = True`; assigning `''` clears the marker and returns the site
to auto mode. The empty sentinel is in the validator's allowed set (§8),
so the reset assignment validates. The section now states the invariant
explicitly: empty value ⟺ auto (`provided = False`); non-empty user
assignment ⟺ `provided = True`.

**Pointer:** §3.

## [P2] No-code space groups need an explicit key normalisation rule

**Verdict:** Agree — and it caught a factual error in the draft.

**Action taken.** Verified against the bundled table: it contains
exactly two `None`-coord-code keys, `(1, None)` (P1, Wyckoff `a`,
multiplicity 1) and `(2, None)` (P-1), and **zero** empty-string keys,
while `SpaceGroup` reports no-code groups as `''`. My draft's "P 1 is
absent from the table" claim was therefore wrong. Added a "Key
normalisation" rule to §2: `''` is normalised to `None` (via a shared
`_normalize_coord_code()` helper) before indexing `SPACE_GROUPS`, so
P1/P-1 resolve to their real positions; corrected the
`detect_wyckoff_letter` bullet to say "genuinely absent"; updated §8 to
key through the same normalisation. Noted that the existing
`_get_wyckoff_exprs()` / `_get_general_position_ops()` lookups should
adopt the helper, since they currently miss the `None`-keyed groups.

**Pointer:** §2 (Key normalisation + `detect_wyckoff_letter` bullet),
§8.

## [P2] CIF presence tracking is underspecified for the marker

**Verdict:** Agree.

**Action taken.** §9 now names the boundary owner: the collection's
`_after_from_cif()` hook, already invoked by
`category_collection_from_cif`
([`serialize.py:1218`](../../../../src/easydiffraction/io/cif/serialize.py)).
Because auto letters are never written (P1 fix above), a present symbol
loads as a non-empty value, so the hook can set `provided = True` for
every atom with a non-empty loaded `wyckoff_letter` — presence ⟺
non-empty value — without threading tag-presence through the generic
loader. CIF-null (`?` / `.`) loads as empty and stays auto.

**Pointer:** §9, read bullets.

## [P3] The auto-fill path names an API that does not exist

**Verdict:** Agree.

**Action taken.** Confirmed there is no `set_value_directly` in
`variable.py`; the real non-validating internal writer is
`_set_value_from_minimizer`
([`variable.py:171`](../../../../src/easydiffraction/core/variable.py)).
§3 now specifies a dedicated private mutator,
`_set_wyckoff_letter_detected()`, modelled on that writer (sets the
value and marks the owner dirty, leaves the provided marker untouched),
and explicitly notes that `set_value_directly` does not exist so the
detected-state write gets its own named path rather than reusing the
minimizer one.

**Pointer:** §3, auto-mode bullet.
