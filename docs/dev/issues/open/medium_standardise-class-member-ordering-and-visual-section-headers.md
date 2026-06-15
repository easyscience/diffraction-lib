# 70. Standardise Class Member Ordering and Visual Section Headers

**Priority:** `[priority] medium`

**Type:** Code style

Agree on and enforce a consistent ordering within every class:

1. Class-level attributes / metadata
2. `__init__`
3. Private helper methods
4. Public properties (getters/setters)
5. Public methods

Each group should have a comment header (e.g.
`# --- Public properties ---`) for visual separation. Some classes
already use this pattern; apply it uniformly.

**Depends on:** nothing.
