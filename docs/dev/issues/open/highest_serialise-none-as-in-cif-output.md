# 84. Serialise `None` as `.` in CIF Output

**Priority:** `[priority] highest`

**Type:** Correctness

CIF output currently writes `None` as literal text for some fields (e.g.
`_diffrn.ambient_pressure None`). CIF convention uses `.` for
inapplicable values and `?` for unknown. The CIF writer should map
`None` → `.` (or `?` depending on semantics), and the reader should map
`.` → `None`.

**Depends on:** nothing.

**Recommended-priority note:** Spec correctness and round-trip fidelity for CIF `.`/`?` null encoding. **Tier 1 (do first).**
