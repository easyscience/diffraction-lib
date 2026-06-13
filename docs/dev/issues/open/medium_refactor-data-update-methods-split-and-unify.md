# 25. Refactor Data `_update` Methods (Split and Unify)

**Priority:** `[priority] medium`

**Type:** Maintainability

Multiple `_update` helpers in Bragg PD, Bragg SC, and Total PD data
classes have `TODO: split into multiple methods` or
`TODO: refactor _get_valid_linked_phases` markers. The update logic
should be decomposed and the `_get_valid_linked_phases` responsibility
should be narrowed. The Total PD and Bragg PD classes should also adapt
the pattern from `bragg_sc.py`.

**TODOs:**

- [bragg_pd.py](src/easydiffraction/datablocks/experiment/categories/data/bragg_pd.py#L386)
- [bragg_pd.py](src/easydiffraction/datablocks/experiment/categories/data/bragg_pd.py#L389)
- [bragg_pd.py](src/easydiffraction/datablocks/experiment/categories/data/bragg_pd.py#L506)
- [bragg_pd.py](src/easydiffraction/datablocks/experiment/categories/data/bragg_pd.py#L585)
- [bragg_sc.py](src/easydiffraction/datablocks/experiment/categories/data/bragg_sc.py#L271)
- [total_pd.py](src/easydiffraction/datablocks/experiment/categories/data/total_pd.py#L254)
- [total_pd.py](src/easydiffraction/datablocks/experiment/categories/data/total_pd.py#L257)
- [total_pd.py](src/easydiffraction/datablocks/experiment/categories/data/total_pd.py#L349)

**Depends on:** nothing.

**Recommended-priority note:** Part of the data `_update` refactor cluster (with #32 / #33): decompose `_update`. **Tier 4 (maintainability).**
