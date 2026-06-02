# Reply 2: Automatic Wyckoff Position Detection

Reply to
[`wyckoff-letter-detection_review-2.md`](wyckoff-letter-detection_review-2.md).
Both findings accepted and addressed in the ADR. The CIF null-token
behaviour was verified against the serializer before editing.

## [P1] The auto-mode invariant contradicts detected letters

**Verdict:** Agree.

**Action taken.** The §3 invariant was stated against the stored value
("empty value ⟺ auto"), which is wrong once detection fills a non-empty
value while the atom is still in auto mode. Rephrased §3 so the
invariant is about the **provided marker**, not the value:
`provided = True` exactly when the user supplied the letter;
`provided = False` is auto mode, in which the stored value may be empty
(unresolved) or a non-empty detected letter that downstream consumers
use — both are valid auto states. The empty `= ''` assignment is
described purely as the public reset command (forces `provided = False`,
drops the value to empty until the next detection). Also softened the
section's lead-in from "one invariant tying it to the value" to "kept
distinct from the stored descriptor value".

**Pointer:** §3 (lead-in sentence and closing invariant paragraph).

## [P2] Project CIF needs a row-level rule for mixed auto/explicit loops

**Verdict:** Agree.

**Action taken.** Confirmed that atom-site loops are emitted through the
ADP-family loop path (`_adp_family_loop_to_cif`, `serialize.py:301`) and
that the project's null token is `?` (`serialize.py:54`), which reads
back as the descriptor default (`serialize.py:1091`) — i.e. the empty
sentinel for the Wyckoff string descriptor. Replaced §9's per-atom
"write no symbol" rule with a concrete per-loop, columnar rule:

- the `_atom_site.Wyckoff_symbol` column is emitted for an emitted loop
  iff at least one row in it has a provided letter;
- when present, provided rows write the letter and auto rows write `?`;
- when no row has a provided letter, the column is omitted.

Updated the read bullet to match: a non-empty cell means explicit, while
`?` / `.` / absent loads as empty and stays auto. This keeps the
"non-empty loaded value ⟺ explicit" rule implementable for mixed loops.

**Pointer:** §9 (write and read bullets).
