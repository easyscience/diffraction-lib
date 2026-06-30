# 142. Numeric CIF Parse Failure Silently Stores `None`

**Priority:** `[priority] medium`

**Type:** Robustness

For a NUMERIC field, `_set_param_from_raw_cif_value` calls
`str_to_ufloat(raw).n` and assigns it with no parse-success check. On a
hand-edited/garbled numeric token, `str_to_ufloat` falls back to
`ufloat(default, nan)` where `default` is `None`, so
`param.value = None` runs through the validator with no clear "could not
parse numeric CIF value" diagnostic — unlike the INTEGER branch, which
warns on non-integers.

**Fix:** emit an explicit warning/error naming the field and raw token
when numeric parsing fails, mirroring the INTEGER branch.

**TODOs / locations:**

- [serialize.py](../../../../src/easydiffraction/io/cif/serialize.py#L1121)
- [utils.py](../../../../src/easydiffraction/utils/utils.py#L1094) — `str_to_ufloat`
  fallback

**Depends on:** related to issue 59 (CIF parse validation).
