# 67. Custom Validation for Parameter/Descriptor and Category Types

**Priority:** `[priority] medium`

**Type:** Design

Parameters and Descriptors use `RangeValidator`, `RegexValidator`,
`MembershipValidator` for values but rely on `@typechecked` (only in
some places) for type checking. Category switchable types use different
validation paths. Decide whether to:

- Use custom validators for both types and values on Parameters.
- Use custom validators for category type setters.
- Standardise the approach across the codebase.

**Depends on:** issue 38 (`@typechecked` / gemmi interaction).
