# 151. Replace Dead `else` Branch in `_set_calc_status` With a Real Boolean Check

**Priority:** `[priority] medium`

**Type:** Correctness / Dead code

The pattern
`if v: ... elif not v: ... else: raise ValueError('Expected boolean')`
has an unreachable `else` — every value is truthy or falsy, so the
validation `raise` never fires. A non-boolean (e.g. the string `'0'`,
which is truthy) is silently coerced to `'incl'` rather than rejected.
Duplicated verbatim in both data classes.

**Fix:** replace the truthiness test with an explicit
`isinstance(v, (bool, np.bool_))` check so the guard actually runs.

**TODOs / locations:**

- [bragg_pd.py](src/easydiffraction/datablocks/experiment/categories/data/bragg_pd.py#L407)
- [total_pd.py](src/easydiffraction/datablocks/experiment/categories/data/total_pd.py#L224)

**Depends on:** related to issue 30 (make `calc_status` an enum).
