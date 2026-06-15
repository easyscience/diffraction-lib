# 156. Size `chapter()` Divider From the Live Console Width

**Priority:** `[priority] low`

**Type:** Robustness / Display

`ConsoleManager.get()` constructs the shared `Console` once with the
width detected at first use and caches it; `chapter()` calls
`_detect_width()` fresh on each invocation to size its divider line. If
the terminal is resized between first console creation and a `chapter()`
call, the computed padding no longer matches the console's fixed render
width, producing a mis-aligned or wrapped header rule.

**Fix:** size `chapter()` from the live console's `width`
(`cls._console.width`) instead of re-detecting.

**TODOs / locations:**

- [logging.py](src/easydiffraction/utils/logging.py#L784)

**Depends on:** related to issue 109 (table/terminal width policy).
