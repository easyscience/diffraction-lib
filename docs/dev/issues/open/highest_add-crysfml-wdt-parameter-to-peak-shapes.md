# 167. Add CrysFML `WDT` Parameter to Peak Shapes

**Priority:** `[priority] highest`

**Type:** Performance / Engine feature

The CrysFML CFL backend supports a `WDT` peak-profile window parameter
that controls how many FWHM around each Bragg position are evaluated.
EasyDiffraction currently hard-codes this value in the crysfml adapter
to keep FullProf verification profiles consistent, but users cannot
trade accuracy against runtime for large CrysFML powder calculations.

**Fix:** add a user-facing `WDT` parameter on the relevant peak-shape
categories and map it only when the selected calculator is `crysfml`.
The parameter should be documented as CrysFML-only: lowering it can
increase performance by shortening the evaluated peak tails, while
larger values preserve broader pseudo-Voigt tails for verification and
high-accuracy calculations.

**TODOs / locations:**

- Add the peak-shape/category parameter with a clear CrysFML-only
  description and safe default.
- Map the parameter into the crysfml CFL `WDT` condition line.
- Keep other calculators unaffected; do not imply cryspy support.
- Add regression tests for the CFL line and default behaviour.

**Depends on:** the CFL-based crysfml adapter.

**Recommended-priority note:** Marked **highest** because the current
hard-coded value is correctness-preserving but removes a real
performance control from users running CrysFML calculations.
