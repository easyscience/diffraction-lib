# 158. Remove Stale Commented-Out / Dead Code in `core/` and `io/`

**Priority:** `[priority] low`

**Type:** Dead code

The CIF parse module keeps a commented-out `experiment_type_from_block`
helper, and `core/variable.py` carries a dead `_value_spec.validated`
block plus a "Check if it is actually in use?" TODO. These are stale and
removable.

**TODOs / locations:**

- [parse.py](src/easydiffraction/io/cif/parse.py#L65)
- [variable.py](src/easydiffraction/core/variable.py#L99)
- [variable.py](src/easydiffraction/core/variable.py#L167)

**Depends on:** nothing.
