# 74. Sync Property Type Hints with Private Attributes + Custom Lint

**Priority:** `[priority] medium`

**Type:** Tooling / Correctness

Public property getters return `Parameter` / `StringDescriptor` etc.,
and setters accept `float` / `str` etc. These annotations must stay in
sync with the private `_attr` type. Currently there is no automated
check. Options:

- A custom script (like `param_consistency.py`) to verify sync.
- A ruff plugin or post-ruff check step.
- Also covers: enforcing `Base` suffix (not prefix), checking missing
  docstrings (issue 81), and other project-specific conventions.

**Depends on:** nothing.
