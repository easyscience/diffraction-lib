# 77. Add Help Methods to Public Discovery Facades

Added consistent `help()` methods for plain user-facing facade classes
that do not inherit the guarded object hierarchy: `project.display`,
`project.display.parameters`, `project.display.fit`,
`project.display.posterior`, `analysis.display`, and `project.summary`.
Introduced `render_object_help()` so these helpers share the same
property and method table style as `GuardedBase.help()`. Documented the
convention in
[`help-discoverability.md`](../../adrs/accepted/help-discoverability.md).
