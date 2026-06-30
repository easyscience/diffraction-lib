# 29. Standardise CIF ID Validator Pattern Across Categories

**Priority:** `[priority] medium`

**Type:** Consistency

Multiple category item classes use the same regex `r'^[A-Za-z0-9_]*$'`
for their id/label validators with an identical TODO about CIF label vs.
internal label conversion.

**TODOs:**

- [bragg_pd.py](../../../../src/easydiffraction/datablocks/experiment/categories/data/bragg_pd.py#L43)
- [bragg_sc.py](../../../../src/easydiffraction/datablocks/experiment/categories/refln/bragg_sc.py#L39)
- [chebyshev.py](../../../../src/easydiffraction/datablocks/experiment/categories/background/chebyshev.py#L52)
- [line_segment.py](../../../../src/easydiffraction/datablocks/experiment/categories/background/line_segment.py#L45)
- [default.py](../../../../src/easydiffraction/datablocks/experiment/categories/excluded_regions/default.py#L39)
- [default.py](../../../../src/easydiffraction/datablocks/structure/categories/atom_sites/default.py#L45)

**Depends on:** nothing.
