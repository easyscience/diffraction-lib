# 19. Add Debug-Mode Logging for Calculator Imports

**Priority:** `[priority] low`

**Type:** Diagnostics

Several calculator modules have commented-out print statements for
import success/failure. These should be wired into the logging system
under a debug level.

**TODOs:**

- [pdffit.py](src/easydiffraction/analysis/calculators/pdffit.py#L34)
- [pdffit.py](src/easydiffraction/analysis/calculators/pdffit.py#L37)
- [crysfml.py](src/easydiffraction/analysis/calculators/crysfml.py#L19)
- [crysfml.py](src/easydiffraction/analysis/calculators/crysfml.py#L23)
- [cryspy.py](src/easydiffraction/analysis/calculators/cryspy.py#L25)
- [cryspy.py](src/easydiffraction/analysis/calculators/cryspy.py#L28)

**Depends on:** nothing.
