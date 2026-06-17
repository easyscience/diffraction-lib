# Reply 2: Dataset-Driven Fit Modes and Sequential Redefinition

## P1 — Give loaded-dataset `reverse` a public home or defer it

**Verdict:** Agree.

The Reply 1 edits introduced an "opt-in reverse" for loaded-dataset
`sequential` while Decision 5a simultaneously parked `sequential_fit`
(where `reverse` lives) — hidden and omitted from CIF. That left the
reverse option with no public or persisted home, and the ADR adds no
owner-level setter, so the plan would have had to invent unapproved API
surface. Inventing a loaded-series config category just to host one
ordering flag is not worth it in the first step.

**Action taken:**

- Edited **Decision 3** to drop configurable reverse/custom ordering
  from the first step. The series order is now simply the deterministic
  project collection order; the ADR explicitly states that the existing
  `reverse` flag lives on the parked `sequential_fit` category, that no
  new owner-level setter or category is added for it, and that ordering
  control is **deferred to the input-source follow-up**. Until then,
  users order the series by the order in which they add experiments.

Affected section: `## Decision` (3).
