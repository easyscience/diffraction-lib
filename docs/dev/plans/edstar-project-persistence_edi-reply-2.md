# Edi Rename Reply 2: Edstar Project Persistence

Reply to
[`edstar-project-persistence_edi-review-2.md`](edstar-project-persistence_edi-review-2.md).
The single finding is agreed and fixed.

## Finding 1 [low] — `project.edifa` rejection branch untested — Agree, fixed

Verdict: agree. Restore is a boundary input and the project-level
`project.edifa` branch (`src/easydiffraction/project/project.py`,
`_load_project_metadata()`) was the one rejection path without a test;
only the section and analysis branches were covered.

Action (commit `f392f51b`): added
`test_load_rejects_legacy_project_edifa_metadata` in
`tests/unit/easydiffraction/project/test_project_coverage.py`. It saves
a valid project, drops a stale `project.edifa` beside the new
`project.edi`, and asserts `Project.load()` raises the legacy `.edifa`
migration error. Because the `.edifa` check runs before the
`project.edi` read, the mixed-directory case fails loudly as intended.

All three project-restore rejection paths — section files
(`structures/`, `experiments/`), `analysis.edifa`, and `project.edifa` —
now have explicit coverage.

## Verification

`pixi run check` clean (11/11). The new test passes; the full
script-tests (34 passed, 7 skipped) and tutorial-baseline (24 passed, 1
platform skip) gates were green on the pushed branch before this
finding, and this change is test-only.
