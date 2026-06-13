# 32. Move Common Methods to `DatablockCollection` Base Class

**Priority:** `[priority] medium`

**Type:** Maintainability

Both `Experiments` and `Structures` collections duplicate methods
(`from_cif_str`, `from_cif_file`, `show`, `show_as_cif`, etc.) that
could live in the base `DatablockCollection`.

**TODOs:**

- [collection.py](src/easydiffraction/datablocks/experiment/collection.py#L29)
  — `Make abstract in DatablockCollection?`
- [collection.py](src/easydiffraction/datablocks/experiment/collection.py#L65)
  — `Move to DatablockCollection?`
- [collection.py](src/easydiffraction/datablocks/experiment/collection.py#L82)
- [collection.py](src/easydiffraction/datablocks/experiment/collection.py#L145)
- [collection.py](src/easydiffraction/datablocks/experiment/collection.py#L151)
- [collection.py](src/easydiffraction/datablocks/structure/collection.py#L30)
- [collection.py](src/easydiffraction/datablocks/structure/collection.py#L48)
- [collection.py](src/easydiffraction/datablocks/structure/collection.py#L65)
- [collection.py](src/easydiffraction/datablocks/structure/collection.py#L82)
- [collection.py](src/easydiffraction/datablocks/structure/collection.py#L88)

**Depends on:** nothing.

**Recommended-priority note:** Part of the data `_update` refactor
cluster (with #25 / #33): lift duplicated collection methods to the
base. **Tier 4 (maintainability).**
