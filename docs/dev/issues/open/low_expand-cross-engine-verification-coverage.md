# 115. Expand Cross-Engine Verification Coverage

**Priority:** `[priority] low`

**Type:** Test coverage / Documentation

The Verification docs section ships with the framework and the first
cross-engine comparison page (constant-wavelength powder, cryspy ↔
crysfml). Extend it to the remaining supported combinations declared by
the calculator support matrix — time-of-flight powder (cryspy ↔ crysfml)
and single crystal — so every valid experiment/instrument combination is
documented and regression-checked at least once. Each new page is a
calculation-only `.py` under `docs/docs/verification/` wired into
`script-tests` and `notebook-tests`, with explicit metric tolerances.

**Depends on:** nothing.
