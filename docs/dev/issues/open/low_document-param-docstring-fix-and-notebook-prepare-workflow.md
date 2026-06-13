# 82. Document `param-docstring-fix` and `notebook-prepare` Workflow

**Priority:** `[priority] low`

**Type:** Documentation

Two manual workflow steps are required between releases/changes:

1. `pixi run param-docstring-fix` — sync Parameter docstrings.
2. `pixi run notebook-prepare` — regenerate tutorial notebooks from
   scripts.

Document these in `CONTRIBUTING.md` or a relevant ADR so they are not
forgotten.

**Depends on:** nothing.
