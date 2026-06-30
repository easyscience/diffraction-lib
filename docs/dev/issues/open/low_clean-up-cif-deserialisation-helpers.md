# 57. Clean Up CIF Deserialisation Helpers

**Priority:** `[priority] low`

**Type:** Maintainability

`serialize.py` has several TODOs: verify methods after the
`format_param_value` section, extract a helper for quoted-string
stripping, find a better way to set `_item_type` on
`CategoryCollection`, rename it to `_item_cls`, and remove duplicated
`param_from_cif` logic.

**TODOs:**

- [serialize.py](../../../../src/easydiffraction/io/cif/serialize.py#L454)
- [serialize.py](../../../../src/easydiffraction/io/cif/serialize.py#L562)
- [serialize.py](../../../../src/easydiffraction/io/cif/serialize.py#L617)
- [serialize.py](../../../../src/easydiffraction/io/cif/serialize.py#L619)
- [serialize.py](../../../../src/easydiffraction/io/cif/serialize.py#L656)

**Depends on:** nothing.
