# 181. Add `from __future__ import annotations` to All Modules

**Priority:** `[priority] low`

**Type:** Hygiene / Consistency

`AGENTS.md` (Code Style) requires `from __future__ import annotations`
in **every** module, but many source files lack it. The linter does not
enforce it universally, so the convention has drifted.

No count is quoted here on purpose: the number is highly sensitive to
scope (whether package `__init__.py` files and vendored snapshots are
counted), and independent passes disagreed — any bare figure is
misleading without its exact command and scope.

**Fix:**

1. Fix the counting scope first — exclude vendored paths
   (`report/templates/.../vendor/`, `report/templates/tex/styles/`,
   `utils/_vendored/...`), and decide whether package `__init__.py`
   files must carry the import.
2. Generate the exact list with a recorded command, e.g.
   `grep -L "from __future__ import annotations" $(find src/easydiffraction -name '*.py' -not -path '*/vendor/*' -not -path '*/_vendored/*' -not -path '*/styles/*')`.
3. Add the import as the first import line of each listed module in one
   mechanical pass.

Priority is consistency, not correctness — no functional impact.

**Depends on:** nothing.
