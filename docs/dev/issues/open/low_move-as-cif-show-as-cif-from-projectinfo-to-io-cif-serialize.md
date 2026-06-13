# 58. Move `as_cif` / `show_as_cif` from `ProjectInfo` to `io.cif.serialize`

**Priority:** `[priority] low`

**Type:** Maintainability

`ProjectInfo` methods `as_cif` and `show_as_cif` have TODOs suggesting
they belong in the serialisation module.

**TODOs:**

- [project_info.py](src/easydiffraction/project/project_info.py#L123)
- [project_info.py](src/easydiffraction/project/project_info.py#L128)

**Depends on:** nothing.
