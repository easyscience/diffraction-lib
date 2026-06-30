# 26. Clarify `dtype` Usage in Data Point Arrays

**Priority:** `[priority] low`

**Type:** Cleanup

Many array constructions pass `dtype=float` or `dtype=object` with a
`TODO: needed? DataTypes.NUMERIC?` comment. Decide whether explicit
dtype is needed and align with `DataTypes`.

**TODOs:**

- [bragg_pd.py](../../../../src/easydiffraction/datablocks/experiment/categories/data/bragg_pd.py#L415)
- [bragg_pd.py](../../../../src/easydiffraction/datablocks/experiment/categories/data/bragg_pd.py#L423)
- [bragg_pd.py](../../../../src/easydiffraction/datablocks/experiment/categories/data/bragg_pd.py#L431)
- [bragg_pd.py](../../../../src/easydiffraction/datablocks/experiment/categories/data/bragg_pd.py#L456)
- [bragg_pd.py](../../../../src/easydiffraction/datablocks/experiment/categories/data/bragg_pd.py#L466)
- [bragg_pd.py](../../../../src/easydiffraction/datablocks/experiment/categories/data/bragg_pd.py#L474)
- [bragg_pd.py](../../../../src/easydiffraction/datablocks/experiment/categories/data/bragg_pd.py#L543)
- [bragg_pd.py](../../../../src/easydiffraction/datablocks/experiment/categories/data/bragg_pd.py#L556)
- [bragg_pd.py](../../../../src/easydiffraction/datablocks/experiment/categories/data/bragg_pd.py#L624)
- [bragg_pd.py](../../../../src/easydiffraction/datablocks/experiment/categories/data/bragg_pd.py#L637)
- [total_pd.py](../../../../src/easydiffraction/datablocks/experiment/categories/data/total_pd.py#L370)
- [total_pd.py](../../../../src/easydiffraction/datablocks/experiment/categories/data/total_pd.py#L378)

**Depends on:** nothing.
