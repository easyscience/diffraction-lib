# 109. Let More Tables Adapt to Terminal Width

**Priority:** `[priority] low`

**Type:** UX / Display

`list_tutorials` now renders its table at the real terminal width via a
new optional `width` parameter threaded through the table render path
(`render_table` → `TableRenderer.render` → backend `render`; Rich
applies it, the HTML backend ignores it). Every other table and all log
output still go through the shared Rich console, whose width is floored
at `ConsoleManager._MIN_CONSOLE_WIDTH = 130` ("to avoid cramped
layouts"). On a standard ~80-column terminal that floor makes wide
tables overflow and soft-wrap badly.

**Fix:** decide on a global policy — either have `_detect_width` trust
the detected terminal width (keeping 130 only as a fallback when
detection fails), or pass the terminal width into more table call sites
the way `list_tutorials` now does. A global change affects every table
(fit results, parameters, ...) and all logs, so weigh it against the
deliberate minimum-width choice.

**Depends on:** related to issue 62.
