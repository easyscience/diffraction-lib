# 143. Verify String-Field CIF Round-Trip Strips `;` Text Delimiters

**Priority:** `[priority] medium`

**Type:** Correctness

`_set_param_from_raw_cif_value` strips text-field delimiters once at the
top, but loop cells passed from `category_collection_from_cif` carry
already-split raw tokens, and the STRING branch only calls
`_strip_optional_quotes`. A multi-line semicolon-delimited string value
(e.g. a long `description` written as a CIF `;`-text-field) loaded via the
descriptor `from_cif` path — not the dedicated `ProjectInfo` reader — can
retain its `;\n … \n;` framing.

**Fix:** confirm round-trip of long descriptions/strings through the
descriptor `from_cif` path and route both paths through one shared
text-field-aware reader (see issue 57).

**TODOs / locations:**

- [serialize.py](src/easydiffraction/io/cif/serialize.py#L1104)
- [serialize.py](src/easydiffraction/io/cif/serialize.py#L1131)

**Depends on:** related to issue 57 (CIF deserialisation helper cleanup).
