# 144. `_find_loop_for_category` Missing None Guard

**Priority:** `[priority] medium`

**Type:** Robustness

`_find_loop_for_category` does `block.find_loop(name).get_loop()`
directly, while the sibling helper `_has_cif_loop` defensively checks for
`None` and `hasattr(..., 'get_loop')` before calling. If gemmi's
`find_loop` returns a falsy/None-like reference for a tag that exists as a
non-loop scalar (a real hand-edited-CIF possibility — e.g. an
`_atom_site.label` written as a key-value instead of inside a `loop_`),
this path raises `AttributeError` instead of returning `None`.

**Fix:** make the two helpers consistent; guard `find_loop(...)` for
`None` before `.get_loop()`.

**TODOs / locations:**

- [serialize.py](src/easydiffraction/io/cif/serialize.py#L1160)
- [serialize.py](src/easydiffraction/io/cif/serialize.py#L991) —
  `_has_cif_loop` (the correct pattern)

**Depends on:** nothing.
