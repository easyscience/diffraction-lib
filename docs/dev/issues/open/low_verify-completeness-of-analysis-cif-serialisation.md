# 79. Verify Completeness of Analysis CIF Serialisation

**Priority:** `[priority] low`

**Type:** Correctness

`analysis_to_cif()` and `analysis_from_cif()` exist, but audit whether
**all** analysis state is persisted: aliases, constraints, fit mode,
joint-fit weights, minimiser type, calculator assignments. Any missing
fields means a loaded project silently differs from the saved one.

**Depends on:** related to issue 121.
