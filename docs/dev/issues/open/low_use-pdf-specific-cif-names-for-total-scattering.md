# 17. Use PDF-Specific CIF Names for Total Scattering

**Priority:** `[priority] low`

**Type:** Naming

The `TotalPdDataPoint` class reuses Bragg powder CIF tag names (e.g.
`_pd_data.point_id`, `_pd_proc.r`, `_pd_meas.intensity_total`) as
placeholders. These should be replaced with proper total-scattering /
PDF-specific CIF names.

**TODOs:**

- [total_pd.py](src/easydiffraction/datablocks/experiment/categories/data/total_pd.py#L48)
  — `_pd_data.point_id`
- [total_pd.py](src/easydiffraction/datablocks/experiment/categories/data/total_pd.py#L62)
  — `_pd_proc.r`
- [total_pd.py](src/easydiffraction/datablocks/experiment/categories/data/total_pd.py#L74)
  — `_pd_meas.intensity_total`
- [total_pd.py](src/easydiffraction/datablocks/experiment/categories/data/total_pd.py#L87)
  — `_pd_meas.intensity_total_su`
- [total_pd.py](src/easydiffraction/datablocks/experiment/categories/data/total_pd.py#L99)
  — `_pd_calc.intensity_total`
- [total_pd.py](src/easydiffraction/datablocks/experiment/categories/data/total_pd.py#L112)
  — `_pd_data.refinement_status`

**Depends on:** nothing.
