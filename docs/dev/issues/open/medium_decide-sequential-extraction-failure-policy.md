# 124. Decide Sequential Extraction Failure Policy

**Priority:** `[priority] medium`

**Type:** Runtime behaviour

Today a failed required extract rule marks that file as failed and the
run continues. The overall aggregation policy is still undefined.

**Fix:** decide whether one failed file should abort the whole run,
remain an isolated row-level failure, or count toward a configurable
failure threshold.

**Depends on:** nothing.
