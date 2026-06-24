# 27. Handle Zero Uncertainty in Bragg PD Data

**Priority:** `[priority] low`

**Type:** Correctness

A temporary workaround exists for zero uncertainties in measured data.

**Superseded by issue 140**, which broadens this into a single
finite-positive uncertainty-floor policy applied uniformly across Bragg
powder, single-crystal, and PDF data (the Bragg PD guard does not catch
NaN/negative values, and SC/PDF have no guard at all). Keep this entry
as the original narrow note; act on it through issue 140.

**TODOs:**

- [bragg_pd.py](src/easydiffraction/datablocks/experiment/categories/data/bragg_pd.py#L442)

**Depends on:** see issue 140.
