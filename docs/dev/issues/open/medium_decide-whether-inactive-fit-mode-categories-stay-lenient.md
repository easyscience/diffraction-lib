# 120. Decide Whether Inactive Fit-Mode Categories Stay Lenient

**Priority:** `[priority] medium`

**Type:** API design

`Analysis` currently allows direct access to inactive mode-specific
categories such as `joint_fit` or `sequential_fit`. The values remain
editable, but inactive sections are hidden from help and dropped during
serialization.

**Fix:** confirm whether this lenient access is the long-term contract,
or replace it with a dedicated mode error to prevent silent state loss
on save.

**Depends on:** nothing.
