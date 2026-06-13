# 65. Replace All Bare `print()` Calls with Logging

**Priority:** `[priority] medium`

**Type:** Code quality

A few bare `print()` calls remain in `src/` (not `console.print()`, not
commented out, excluding vendored code). All output should go through
`log` or `console` so that verbosity is controllable. Current offenders:

- [ascii.py](src/easydiffraction/display/plotters/ascii.py#L211)
- [ascii.py](src/easydiffraction/display/plotters/ascii.py#L354)
- [display.py](src/easydiffraction/project/display.py#L687)

Most earlier offenders are already resolved; the remaining calculator
import prints are commented out and tracked separately under issue 19.

**Depends on:** nothing.

**Recommended-priority note:** Bare `print()` → logging; now only 3 real call sites. **Tier 4 (maintainability).**
