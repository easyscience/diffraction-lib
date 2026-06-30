# 138. `calculate_structure_factors` Contract Disagrees Across Backends and Caller

**Priority:** `[priority] highest`

**Type:** Correctness / Maintainability

`CalculatorBase.calculate_structure_factors` declares
`(structure, experiment, *, called_by_minimizer) -> None`, but the
single real caller (`bragg_sc.py`) unpacks a `(stol, raw_calc)` tuple.
`CryspyCalculator` returns that tuple (and `[], []` on `KeyError`,
silently yielding empty calc downstream), while `CrysfmlCalculator` and
`PdffitCalculator` use a different signature
`(self, structures, experiments)` with no `called_by_minimizer` kwarg.
Selecting crysfml/pdffit for a single-crystal HKL calc raises a
confusing `TypeError`/unpack error instead of a clear "not supported"
message.

**Fix:** unify the abstract signature and return type to
`tuple[np.ndarray, np.ndarray]`, update all three backends, and have
non-supporting backends raise a clear `NotImplementedError`.

**TODOs / locations:**

- [base.py](../../../../src/easydiffraction/analysis/calculators/base.py#L49)
- [cryspy.py](../../../../src/easydiffraction/analysis/calculators/cryspy.py#L127)
- [crysfml.py](../../../../src/easydiffraction/analysis/calculators/crysfml.py#L112)
- [pdffit.py](../../../../src/easydiffraction/analysis/calculators/pdffit.py#L70)
- [bragg_sc.py](../../../../src/easydiffraction/datablocks/experiment/categories/refln/bragg_sc.py#L400)

**Depends on:** related to issue 63 (the sibling `calculate_pattern`
signature question).

**Recommended-priority note:** Promoted to **highest** by the 2026-06-13
audit: a confirmed correctness defect — the backend contract mismatch
causes a wrong/crashing single-crystal HKL calculation.
