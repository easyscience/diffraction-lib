# Review 8: Automatic Wyckoff Position Detection

## Findings

### [P2] Unsupported groups are still described as always empty

Reply 7 chose the right policy for unsupported groups: auto-detection is
a no-op, but an explicit Python/CIF letter is stored verbatim and
carries no derived record. The ADR still has broad wording that
contradicts that policy. Section 3 says that when the group is absent
from `SPACE_GROUPS`, "the letter stays empty"; §9 says "the one empty
case (an unsupported group)" and describes "an empty letter — an
unsupported space group". Those statements are only true for unsupported
groups with no explicit letter. They are false for the new
explicit-letter path in §8, where an unsupported group may have a
non-empty stored letter. Please qualify the §3 and §9 wording so
unsupported groups split into two cases: no explicit letter stays empty
/ serialises as `?`, while an explicit letter is stored and written
verbatim but has no multiplicity, site symmetry, or symmetry
constraints.

## Checks skipped

Per `AGENTS.md` review-shortcut rules, this was a static ADR/source
review only. I did not run tests, `pixi run fix`, `pixi run check`, or
other verification commands.
