# Edi Rename Review 2: Edstar Project Persistence

## Findings

1. [low] The new `project.edifa` rejection branch is untested. The
   follow-up fix added explicit project-level detection before reading
   `project.edi` (`src/easydiffraction/project/project.py:200`), but the
   new coverage only exercises stale section and analysis files
   (`tests/unit/easydiffraction/project/test_project_coverage.py:587`,
   `tests/unit/easydiffraction/project/test_project_coverage.py:605`).
   Persisted-state restore is a boundary input, and the local test rule
   asks for every new code path to be covered. Please add a small test
   that drops `project.edifa` next to, or instead of, `project.edi` and
   asserts `Project.load()` fails with the legacy `.edifa` migration
   error.

## Checks Skipped

Static review only. I did not run tests, lint, formatters, builds, or
any `pixi` commands.
