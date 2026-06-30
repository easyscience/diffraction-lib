# 153. `value` Setter Re-Validates on Every NaN Assignment

**Priority:** `[priority] low`

**Type:** Performance

The early-out `if self._value == v: return` never fires when the current
value is `NaN` (`nan == nan` is False), so re-assigning the same `NaN`
to a sentinel field (e.g. NaN data-range bounds) always re-runs
validation and marks the owner dirty. Harmless for correctness, but it
defeats the no-op optimization exactly for the sentinel fields the
codebase relies on.

**Fix:** use a `NaN`-aware equality, or document that NaN fields always
re-validate.

**TODOs / locations:**

- [variable.py](../../../../src/easydiffraction/core/variable.py#L152)

**Depends on:** related to issue 13 (suppress redundant dirty-flag
sets).
