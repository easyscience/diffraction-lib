# Reply 7: Automatic Wyckoff Position Detection

Reply to
[`wyckoff-letter-detection_review-7.md`](wyckoff-letter-detection_review-7.md).
The single finding is accepted and addressed.

## [P2] Explicit letters for unsupported groups are undefined

**Verdict:** Agree.

**Decision.** Of the two options the review named, the ADR now chooses
**accept the letter verbatim** rather than reject. Rejecting would fail
to load an otherwise-valid CIF that carries a `Wyckoff_symbol` for a
setting we simply do not tabulate, and would block a legitimate Python
assignment — both are boundary inputs the public API and CIF loading
routinely produce, which the project's edge-case rule says to handle
gracefully, not refuse.

**Action taken.** §8 now states that when the space group is absent from
the table its letters cannot be enumerated, so membership validation is
not applied: the validator accepts whatever the user or a CIF supplies.
Auto-detection stays a no-op, but an explicit letter (Python or CIF) is
stored verbatim, carries no `multiplicity` / `site_symmetry` (no record,
§6) and drives no symmetry constraints, and a `log.warning` records that
the group is untabulated and the letter could not be validated. The
rejected "validation error" alternative is documented inline. §3's
letter-edit bullet gained a cross-reference to §8 for this case.

The four surfaces the finding worried about now agree for unsupported
groups: Python assignment and CIF loading both store the letter verbatim
(§3, §8, §9), allowed-value discovery does not restrict it (§8), and
derived-descriptor handling plus the calculator skip already cover the
no-record case (§6, §7, §9).

**Pointer:** §8 (unsupported-group rule), §3 (letter-edit
cross-reference).
