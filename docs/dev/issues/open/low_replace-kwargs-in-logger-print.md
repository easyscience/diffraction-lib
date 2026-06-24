# 185. Replace `**kwargs` in `Logger.print`

**Priority:** `[priority] low`

**Type:** Code style / Convention

`Logger.print(cls, *objects, **kwargs)`
(`src/easydiffraction/utils/logging.py:683`) forwards `**kwargs` to the
Rich console, which `AGENTS.md` (Code Style) forbids ("No `**kwargs` —
use explicit keyword arguments"). `Logger.print` is a project-owned
public façade, so it should enumerate the Rich console options it
actually supports rather than passing an open `**kwargs`.

(Other `**kwargs` occurrences are arguable framework plumbing —
`super().__init__` chains in `core/variable.py` / factory code, or
`object`-typed minimizer-solver passthroughs to third-party libraries —
and are out of scope here.)

**Fix:** replace `**kwargs` on `Logger.print` with the explicit keyword
arguments it forwards, or document the framework-passthrough exception
if intentional.

**Depends on:** nothing.
