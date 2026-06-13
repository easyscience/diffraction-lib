# 126. Decide How Mid-Run Sequential Failures Persist

**Priority:** `[priority] low`

**Type:** Recovery design

If a sequential fit fails partway through, the recovery and persistence
contract for `analysis/results.csv` is not fully specified.

**Fix:** define whether partial CSV output is authoritative for resume,
left untouched for manual recovery, or replaced on the next run.

**Depends on:** nothing.
