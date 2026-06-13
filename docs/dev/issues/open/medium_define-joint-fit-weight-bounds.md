# 122. Define `joint_fit.weight` Bounds

**Priority:** `[priority] medium`

**Type:** Data model

Joint-fit rows currently allow any non-negative weight, but the public
contract is still unclear about whether `0` means exclusion and whether
an upper bound should exist.

**Fix:** define the supported range and validator semantics for
`joint_fit.weight`.

**Depends on:** nothing.
