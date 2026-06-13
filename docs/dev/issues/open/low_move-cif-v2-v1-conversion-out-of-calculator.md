# 18. Move CIF v2→v1 Conversion Out of Calculator

**Priority:** `[priority] low`

**Type:** Maintainability

`PdffitCalculator.calculate_pattern` contains inline CIF v2→v1
conversion (dot-to-underscore rewriting). This should live in a shared
`io` module.

**TODOs:**

- [pdffit.py](src/easydiffraction/analysis/calculators/pdffit.py#L118)

**Depends on:** nothing.
