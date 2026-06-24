# 20. Redirect or Suppress CrysPy stderr Warnings

**Priority:** `[priority] low`

**Type:** UX

CrysPy emits warnings to stderr during pattern calculation.

**Mostly implemented.** Both computation entry points already wrap the
cryspy call in `contextlib.redirect_stderr(io.StringIO())`
(`cryspy.py:195` and `:343`). The original TODO line references
(`#L112`, `#L184`) are stale — line 112 is now unrelated code.

**Remaining work:**

- Remove the two now-satisfied
  `# TODO: Redirect stderr to suppress Cryspy warnings.` comments that
  still sit directly above the working redirects (`cryspy.py:190`,
  `:338`).
- Confirm no other cryspy call path emits unredirected stderr (audit the
  remaining cryspy entry points and extend the redirect if any are
  missed).

**Depends on:** nothing.
