# 182. Display `engine` Setter Swallows `ValueError` and Is Off-Contract

**Priority:** `[priority] medium`

**Type:** Robustness / Architecture

Two related problems in the display renderer base
(`src/easydiffraction/display/base.py`):

- **Swallowed boundary error.** The `engine` setter (`base.py:56-76`)
  wraps the factory `create(new_engine)` in `try/except ValueError`,
  logs a warning, and `return`s — silently leaving the engine unchanged
  when a user passes an unsupported engine name. This is a user-input
  boundary that should fail loudly (raise), not warn-and-continue.
- **Off-contract selector surface.** `RendererBase` exposes a writable
  `engine` property (`:44`, `:56`) plus `show_supported_engines()`
  (`:85`) and `show_current_engine()` (`:99`). This does not match the
  category-owned-selector contract
  ([`switchable-category-owned-selectors.md`](../../adrs/accepted/switchable-category-owned-selectors.md):
  `<category>.type`, `show_supported()`, private `_swap_*`).

**Fix:** raise on an unsupported engine instead of
warning-and-returning; and decide whether renderer engine selection
should follow the switchable-category contract or be explicitly
documented as exempt (a display-only backend, not a domain switchable).

**Depends on:** related to issues 61 / 66 (`log.error` vs `raise`
strategy).
