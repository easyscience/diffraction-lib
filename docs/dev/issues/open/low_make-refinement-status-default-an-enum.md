# 30. Make `refinement_status` Default an Enum

**Priority:** `[priority] low`

**Type:** Design

`bragg_pd.py` uses `default='incl'` as a raw string with a TODO to make
it an Enum.

**Update:** the rename half is done — the property is now `calc_status`
(in both `bragg_pd.py` and `total_pd.py`), but the value set
(`'incl'`/`'excl'`) is still raw strings enforced by a
`MembershipValidator` and compared against string literals, contrary to
the `(str, Enum)` convention. The enum should be shared by both data
families and the excluded-regions mask logic. See also issue 151 (a dead
`else` branch in the same `_set_calc_status` setter).

**TODOs:**

- [bragg_pd.py](src/easydiffraction/datablocks/experiment/categories/data/bragg_pd.py#L156)
- [total_pd.py](src/easydiffraction/datablocks/experiment/categories/data/total_pd.py#L116)

**Depends on:** nothing.
