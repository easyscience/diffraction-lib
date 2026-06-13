# 148. Atom-Site / Phase-ID Label Regex Rejects Valid CIF Labels

**Priority:** `[priority] medium`

**Type:** Robustness

`_atom_site.label` and `_pd_phase_block.id` use
`RegexValidator(r'^[A-Za-z_][A-Za-z0-9_]*$')`, which rejects valid CIF
identifiers that begin with a digit or contain `+`/`-`/`'` (e.g. ion
labels like `O1-`, `Tb3+`, or block names starting with a digit). Loading
a real-world third-party CIF with such labels fails at the parse
boundary. The excluded-regions id regex differs again
(`^[A-Za-z0-9_]*$`) — an inconsistency among the three.

**Fix:** relax the CIF-facing validator to match CIF label rules (or
decouple the internal dict key from the CIF label), and standardise the
pattern across categories.

**TODOs / locations:**

- [default.py](src/easydiffraction/datablocks/structure/categories/atom_sites/default.py#L71)
- [default.py](src/easydiffraction/datablocks/experiment/categories/linked_phases/default.py#L38)
- [default.py](src/easydiffraction/datablocks/experiment/categories/excluded_regions/default.py#L45)

**Depends on:** subsumes part of issue 29 (standardise CIF ID validator
pattern) with the concrete invalid-label consequence.
