# 137. CLI `fit` Command Never Saves Results to Disk

**Priority:** `[priority] highest`

**Type:** Correctness

The `fit` subcommand loads the project, calls `project.analysis.fit()`,
and displays outputs, but in the **non-`--dry`** path it never calls
`project.save()`. The `--dry` flag's help text ("Run fitting without
saving results back to the project directory") implies the default run
*does* save, and the sibling `undo` command does save. A scientist
running `easydiffraction PROJECT_DIR fit` sees results on screen but
finds the project directory unchanged.

**TODOs / locations:**

- [\_\_main\_\_.py](src/easydiffraction/__main__.py#L256) — `fit` command,
  add `project.save()` after `_display_fit_outputs` when not `dry`.

**Note:** the integration test
`tests/integration/fitting/test_cli_entrypoints.py` currently encodes
the no-save call sequence, so fixing the bug also requires updating that
test.

**Depends on:** nothing.

**Recommended-priority note:** Promoted to **highest** by the 2026-06-13 full-codebase audit: a confirmed correctness defect — the default `fit` path silently discards results (a "do-first" wrong-results problem the 2026-06-10 tiering predates).
