# 132. Decide Future of `show_residual` in `plot_meas_vs_calc`

**Priority:** `[priority] low`

**Type:** API cleanup

Powder Bragg plots now show the residual row by default when
`show_residual=None`, but the public `show_residual` argument still
exists and some call sites still pass `show_residual=True` explicitly.
The API should be clarified: either keep the argument as a compatibility
option, remove it, or standardize a single meaning across powder and
single-crystal plots.

**TODOs:**

- [plotting.py](../../../../src/easydiffraction/display/plotting.py#L459)
- [\_\_main\_\_.py](../../../../src/easydiffraction/__main__.py#L105)

**Depends on:** nothing.
