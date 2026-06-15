# 55. Fix Jupyter Scroll Disabling for MkDocs

**Priority:** `[priority] low`

**Type:** Docs / UX

`display/__init__.py` has disabled `JupyterScrollManager` because it
breaks MkDocs builds.

**TODOs:**

- [**init**.py](src/easydiffraction/display/__init__.py#L15)

**Depends on:** nothing.
