# 161. Add Boundary Tests for `verification.py` FullProf/IGOR Parsers

**Priority:** `[priority] low`

**Type:** Test coverage

A `test_verification.py` mirror exists, but the FullProf/IGOR parsers
(`_parse_fullprof_header` fixed-width fallback, `_parse_igor_profile`,
`_parse_array_background`, `_parse_columned_background`,
`load_fullprof_sc_f2calc`) are dense external-file-format parsers — the
"file formats / external-library boundary" cases `AGENTS.md` says must
be tested for every code path.

**Fix:** add targeted cases for malformed headers, missing tables, and
non-numeric rows in the existing mirror.

**TODOs / locations:**

- [verification.py](../../../../src/easydiffraction/analysis/verification.py) (tests
  in `tests/unit/easydiffraction/analysis/test_verification.py`)

**Depends on:** nothing.
