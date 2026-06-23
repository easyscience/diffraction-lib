# 188. Track `diffpy.Structure` Deprecation Warning

**Priority:** `[priority] low`

**Type:** Dependency / Deprecation

The test suite surfaces a third-party deprecation:

```
DeprecationWarning: Module 'diffpy.Structure' is deprecated and will be
removed in version 4.0. Use 'diffpy.structure' instead.
```

EasyDiffraction's own code already uses the new lowercase module
(`from diffpy.structure.parsers.p_cif import P_cif` in
`src/easydiffraction/analysis/calculators/pdffit.py:108`), so the
deprecated capital-`S` `diffpy.Structure` is imported by a **transitive
dependency** (diffpy / `diffpy.pdffit2`) and merely surfaced when
Hypothesis scans installed modules
(`hypothesis/internal/conjecture/providers.py`).

The risk is real but external: when diffpy 4.0 removes
`diffpy.Structure`, whatever dependency still imports it breaks.

**Fix:**

1. Identify which installed package imports `diffpy.Structure` (capital).
2. If it is a pinned dependency we control, bump/track it; otherwise
   record the upstream-tracking dependency and watch for the diffpy 4.0
   migration.
3. Optionally add a scoped `filterwarnings` entry so this third-party
   deprecation does not clutter our test output in the meantime.

**Depends on:** nothing (external dependency).
