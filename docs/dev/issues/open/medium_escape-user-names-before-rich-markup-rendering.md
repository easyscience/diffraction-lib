# 145. Escape User Names Before Rich Markup Rendering

**Priority:** `[priority] medium`

**Type:** Robustness

`ConsolePrinter.paragraph()` builds a `Text`, then re-emits
`text.markup` and prints it through Rich, which re-parses markup.
`_validate_name` only rejects `/` and `\`, so a project or experiment
name containing Rich markup characters (e.g. `[red]`, or a bare `[`) is
interpreted as markup or raises `MarkupError` on `save()`. This is a
boundary-input path a user reaches simply by naming a project.

**Fix:** escape user-supplied substrings (`rich.markup.escape`) before
constructing the paragraph, or append the name as a literal `Text`
segment rather than round-tripping through `.markup`.

**TODOs / locations:**

- [logging.py](src/easydiffraction/utils/logging.py#L710)
- [project.py](src/easydiffraction/project/project.py#L501)
- [default.py](src/easydiffraction/project/categories/info/default.py#L80)
  — `_validate_name`

**Depends on:** nothing.
