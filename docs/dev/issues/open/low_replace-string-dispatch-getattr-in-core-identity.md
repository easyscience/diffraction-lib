# 184. Replace String-Dispatch `getattr` in `core/identity.py`

**Priority:** `[priority] low`

**Type:** Code style / Convention

`Identity._resolve_up` builds attribute names by string interpolation —
`getattr(self, f'_{attr}', None)` (`src/easydiffraction/core/identity.py:38`),
where `attr` is one of `datablock_entry` / `category_code` /
`category_entry`. `AGENTS.md` (Code Style) forbids string-based dispatch
(`getattr(self, f'_{name}')`). The value is internal (not user input), so
it plausibly fits the "narrow framework metadata lookup" exception, but it
is not validated in one central place and the three values are not modeled
as an enum — so it sits in a gray zone of the rule.

**Fix:** replace with explicit resolver branches/methods, or model the
three allowed values as a `(str, Enum)` validated centrally, so the lookup
lands cleanly inside the documented metadata-lookup exception.

**Depends on:** nothing.
