# 8. Add Explicit `create()` Signatures on Collections

**Priority:** `[priority] high`

**Type:** API safety

`CategoryCollection.create(**kwargs)` accepts arbitrary keyword
arguments and applies them via `setattr`. Typos are silently dropped
(GuardedBase logs a warning but does not raise), so items are created
with incorrect defaults.

**Fix:** concrete collection subclasses (e.g. `AtomSites`, `Background`)
should override `create()` with explicit parameters for IDE autocomplete
and typo detection. The base `create(**kwargs)` remains as an internal
implementation detail.

**Depends on:** nothing.

**Recommended-priority note:** Typos in `create(**kwargs)` are silently
dropped today. **Tier 2 (tooling that prevents whole bug classes).**
