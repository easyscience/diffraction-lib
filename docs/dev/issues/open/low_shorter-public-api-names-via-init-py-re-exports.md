# 69. Shorter Public API Names via `__init__.py` Re-Exports

**Priority:** `[priority] low`

**Type:** API ergonomics

Classes are imported in `__init__.py` files but users still need deep
paths to reach them. Consider whether top-level re-exports (e.g.
`from easydiffraction import Project, Structure, Experiment`) should
provide shorter access, and document the policy.

**Depends on:** nothing.
