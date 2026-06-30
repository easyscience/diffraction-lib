# 107. Validate Generated CIF Report Against Official IUCr Dictionaries

**Priority:** `[priority] medium`

**Type:** Test coverage

The runtime gemmi self-check in the IUCr CIF writer was removed (it
validated our own deterministic output at write time and depended on
dictionaries under `tmp/iucr-dicts/`; see the §2.5 amendment in
[`iucr-cif-tag-alignment.md`](../../adrs/accepted/iucr-cif-tag-alignment.md)).
That spec-compliance guarantee now needs to live in a dev-time test
instead.

**Fix:** add a unit or functional test that renders both a powder and a
single-crystal IUCr report CIF and validates every emitted tag against
the latest official COMCIFS `cif_core.dic` and `cif_pow.dic`.
Requirements:

- Cover both powder (`_pd_*`, profile/reflection loops) and
  single-crystal report outputs.
- Do **not** read `tmp/` at runtime — pass the dictionaries explicitly
  as a committed test fixture (or fetch them in test setup and pass the
  path in). The check belongs in the test suite, not in the user's write
  path.
- Parse the DDLm/CIF2 form correctly: the current dictionaries use
  `save_<name>` frames with `_definition.id`, which the removed helper's
  `save__tag` regex and a plain `gemmi.cif.read_file` could not handle.
  Use gemmi's DDL reader or a scan adapted to the DDLm layout.
- Allow the project's private `_easydiffraction_*` extension namespace.

**Depends on:** nothing.
