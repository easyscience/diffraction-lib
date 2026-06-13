# 43. Fix Summary Display Inconsistencies

**Priority:** `[priority] low`

**Type:** UX

The summary rendering had TODOs about fixing description wrapping and
inconsistent header capitalisation.

**Stale references — needs re-anchoring.** The `src/easydiffraction/summary/`
package no longer exists; summary rendering was relocated (see the
[`project-summary-rendering.md`](../adrs/accepted/project-summary-rendering.md)
ADR), so the line anchors below are dead. Before acting on this issue,
re-locate the current summary code (under `project/`) and confirm whether
the wrapping / header-capitalisation problems still exist; if resolved,
close this issue.

**TODOs (dead anchors — update on re-triage):**

- `src/easydiffraction/summary/summary.py#L52` — module removed
- `src/easydiffraction/summary/summary.py#L164` — module removed

**Depends on:** nothing.
