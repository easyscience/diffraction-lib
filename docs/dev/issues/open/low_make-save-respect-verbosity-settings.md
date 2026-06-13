# 92. Make `save()` Respect Verbosity Settings

**Priority:** `[priority] low`

**Type:** UX

`Project.save()` unconditionally prints progress via `console.print()`.
It should respect the logger's verbosity mode so that silent/quiet
operation is possible (e.g. in automated pipelines or tests).

**Depends on:** nothing.
