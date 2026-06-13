# 66. Decide Error-Handling Strategy: `log.error` vs `raise`

**Priority:** `[priority] high`

**Type:** Design

The codebase mixes `log.error(msg)` (which may raise depending on
`Reaction` mode) and direct `raise ValueError(...)`. A consistent
strategy is needed: when to use `log.error` (user-facing, recoverable)
vs native exceptions (programmer errors, unrecoverable). This also
relates to the `Reaction` mode setting (issue 61).

**Depends on:** issue 61.

**Recommended-priority note:** Pin the error-handling strategy (paired with #61): when to use `log.error` vs `raise`. **Tier 2.**
