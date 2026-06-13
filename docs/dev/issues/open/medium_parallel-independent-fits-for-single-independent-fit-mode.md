# 89. Parallel Independent Fits for Single/Independent Fit Mode

**Priority:** `[priority] medium`

**Type:** Performance

In `single` (independent) fit mode, each experiment has its own
structure parameters and is completely independent. These fits could run
in parallel threads. Sequential mode, by contrast, must remain single-
threaded because each step's output is the next step's input.

**Depends on:** nothing (issue 78 resolved).
