# 152. `help()` Mislabels Boolean Descriptors as "numeric"

**Priority:** `[priority] low`

**Type:** API safety / UX

In `CategoryItem.help()` the type column is computed as
`'string' if isinstance(val, GenericStringDescriptor) else 'numeric'`, so
any non-string descriptor (including a `BoolDescriptor`) is shown to the
user as type "numeric". For a scientist reading `help()` to learn what to
type, this is a misleading hint.

**Fix:** map the descriptor families (string / numeric / bool) explicitly.

**TODOs / locations:**

- [category.py](src/easydiffraction/core/category.py#L108)

**Depends on:** nothing.
