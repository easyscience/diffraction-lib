# Reply 8: Automatic Wyckoff Position Detection

Reply to
[`wyckoff-letter-detection_review-8.md`](wyckoff-letter-detection_review-8.md).
The single finding is accepted and addressed.

## [P2] Unsupported groups are still described as always empty

**Verdict:** Agree.

**Action taken.** Reply 7 added the "explicit letter on an unsupported
group is stored verbatim" path (§8), which made the older "unsupported →
empty" wording in §3 and §9 only half true. Split that case into its two
sub-cases in both sections:

- **§3 opening** now says the unsupported-group exception splits in two:
  auto-detection is a no-op, so _without_ an explicit letter the value
  stays empty, while an _explicit_ Python/CIF letter is stored verbatim
  (carrying no multiplicity, site symmetry, or constraints — §6).
- **§9 intro** now states the unsupported group splits — no explicit
  letter stays empty, an explicit letter is written verbatim.
- **§9 write bullet** now says **any** non-empty letter is written
  verbatim (whether detected for a supported group or supplied
  explicitly for an unsupported one; only the latter has a `None`
  multiplicity), and a letter serialises as CIF `?` only when it is
  _neither_ detected _nor_ explicitly supplied — an unsupported group
  with no user letter, or a transient pre-update state.

The §9 read bullet already handled both (a present symbol loads as the
letter; an absent/`?` cell stays empty, and fill-if-empty is a no-op for
an unsupported group), so it needed no change.

**Note (context, not a scope change):** the companion
[`space-group-database.md`](space-group-database.md) ADR — whose review
cycle has now closed — makes the bundled table complete for all 230
groups, so in practice "unsupported group" shrinks to genuinely-exotic
settings (and transient pre-update states). The split wording above is
what keeps those residual cases well-defined.

**Pointer:** §3 (opening), §9 (intro and write bullet).
