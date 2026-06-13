# 157. Add Public API to Clear a Project Path (CLI `fit --dry`)

**Priority:** `[priority] low`

**Type:** API safety

The CLI dry-run path sets `project.info._path = None` directly instead of
using the public `path` setter (which only accepts a `Path`-convertible
value, with no documented way to clear it). This couples the CLI to a
private attribute and means there is no supported public API to "unset" a
project path.

**Fix:** add a public method/setter on `ProjectInfo` to clear the path
(e.g. accept `None`), then call that from the CLI.

**TODOs / locations:**

- [\_\_main\_\_.py](src/easydiffraction/__main__.py#L266)

**Depends on:** nothing.
