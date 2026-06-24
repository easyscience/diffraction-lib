# 86. Auto-Resolve `plot_param` X-Axis Descriptor and Add Units

**Priority:** `[priority] low`

**Type:** UX

`plot_param_series` currently requires the user to manually specify the
x-axis parameter (e.g. `x_axis='temperature'` → look up
`diffrn.ambient_temperature`). This should be auto-resolved from the
parameter name. Additionally, axis labels should include units (e.g.
"Temperature (K)").

**Depends on:** nothing.
