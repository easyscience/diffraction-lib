# 81. Enforce Docstrings on All Public Methods

**Priority:** `[priority] medium`

**Type:** Code quality

Some public methods (e.g. `plot_meas_vs_calc`, others) lack docstrings.
Decide:

- All public methods **must** have numpy-style docstrings.
- Private helpers: minimal one-liner docstring or none? Choose a policy.
- Enable a ruff rule (e.g. `D103`, `D102`) or add a custom check to
  enforce.

**Depends on:** nothing.
