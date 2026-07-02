# 47. Improve Error Handling in Crystallography Utilities

**Priority:** `[priority] low`

**Type:** Diagnostics

`crystallography.py` logs errors with a TODO asking whether these should
raise `ValueError` or provide better diagnostics.

**TODOs:**

- [crystallography.py](../../../../src/easydiffraction/crystallography/crystallography.py#L39)
- [crystallography.py](../../../../src/easydiffraction/crystallography/crystallography.py#L45)
- [crystallography.py](../../../../src/easydiffraction/crystallography/crystallography.py#L84)

**Depends on:** nothing.

**Audit note (2026-06-23):** concrete instance — for an unrecognised
`crystal_system`, `crystallography.py:134-138` calls `log.error(...)`
without `exc_type` and then falls through to `return cell` with no
symmetry constraints applied; under WARN logger mode this silently
returns an unconstrained cell. Fix = raise `ValueError` explicitly (and
consider modelling crystal systems as a `(str, Enum)`). Gated on the
logger-reaction decision (issues 61 / 66).
