# 80. Resolve `Any` vs `object` Type Annotation Policy

**Priority:** `[priority] low`

**Type:** Code style

Both `Any` and `object` are used as generic parameter types. Current
pattern: `Any` inside containers (`dict[str, Any]`), `object` for
standalone params (often to avoid circular imports). Decide on a policy:

- Use protocol types / `TYPE_CHECKING` imports instead of `object`.
- Reserve `Any` for genuinely unknown types.
- Document when each is appropriate.

**Depends on:** nothing.
