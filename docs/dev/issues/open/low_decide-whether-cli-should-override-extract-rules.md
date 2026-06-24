# 127. Decide Whether CLI Should Override Extract Rules

**Priority:** `[priority] low`

**Type:** CLI design

The CLI can override mode and worker settings, but persisted
`sequential_fit_extract` rules are not yet overridable from the command
line.

**Fix:** decide whether extraction rules stay project-file-only or gain
an explicit CLI override syntax.

**Depends on:** nothing.
