# Reply 9: Automatic Wyckoff Position Detection

Reply to
[`wyckoff-letter-detection_review-9.md`](wyckoff-letter-detection_review-9.md).
The single finding is accepted and addressed.

## [P2] No-record descriptors still imply an empty letter

**Verdict:** Agree.

**Action taken.** §6 said the empty `multiplicity` / `site_symmetry`
descriptors "follow the letter's empty state in lockstep," which is
wrong for the §8 path where an unsupported group carries a non-empty
explicit letter but still has no `WyckoffPosition` record. Rephrased
both spots so the derived state tracks **record availability**, not
letter emptiness:

- **§6** now states the empty descriptors follow record availability,
  not the letter: a no-record site has empty `multiplicity` /
  `site_symmetry` whether its letter is empty or a non-empty unvalidated
  explicit value (§8). The no-record causes now read "an unsupported
  space group (with or without an explicit letter), or a transient empty
  letter."
- **Testing** (CIF round-trip bullet) now says an unsupported-group row
  keeps empty `multiplicity` / `site_symmetry` whether its letter is
  empty or an explicit value that round-trips verbatim, instead of
  "stays empty."

**Pointer:** §6 (no-record paragraph); Testing (CIF round-trip bullet).
