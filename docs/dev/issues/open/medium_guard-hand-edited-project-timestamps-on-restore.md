# 146. Guard Hand-Edited Project Timestamps on Restore

**Priority:** `[priority] medium`

**Type:** Robustness

`created` and `last_modified` parse the stored CIF string with `strptime`
using a fixed `'%d %b %Y %H:%M:%S'` format every time the property is
read. If a user hand-edits the project file and changes the timestamp to
any other format, reading these properties (or any report/display path
that touches them) raises a bare `ValueError` with no actionable message.

**Fix:** validate on load and emit a descriptive error, or store the raw
string and parse lazily with a guarded message.

**TODOs / locations:**

- [default.py](src/easydiffraction/project/categories/info/default.py#L89)
  — `_parse_timestamp`
- [default.py](src/easydiffraction/project/categories/info/default.py#L152)
  — `created` / `last_modified` getters

**Depends on:** nothing.
