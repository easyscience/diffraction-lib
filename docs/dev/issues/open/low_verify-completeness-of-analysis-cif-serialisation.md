# 79. Verify Completeness of Analysis CIF Serialisation

**Priority:** `[priority] low`

**Type:** Correctness

`analysis_to_cif()` and `analysis_from_cif()` exist, but audit whether
**all** analysis state is persisted: aliases, constraints, fit mode,
joint-fit weights, minimiser type, calculator assignments. Any missing
fields means a loaded project silently differs from the saved one.

**Priority note:** kept `low` deliberately. This is a *verification*
task — no concrete dropped field has been identified yet. It describes
the same silent save/load-drift class as the confirmed persistence
defects (issues 139 `highest`, 142 `medium`), but unlike those it names
no reproduced loss; if the audit turns up a real missing field, split
that out as its own issue and prioritise it on its merits.

**Depends on:** related to issue 121.
