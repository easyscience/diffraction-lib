# 58. Move `as_cif` / `show_as_cif` from `ProjectInfo` to `io.cif.serialize`

Closed: serialization moved to `io/cif/serialize.py` `project_info_to_cif` (`:548`); `ProjectInfo.as_cif` / `show_as_cif` now delegate to it (`project/categories/info/default.py:173`). The original "consider moving" TODOs are gone.
