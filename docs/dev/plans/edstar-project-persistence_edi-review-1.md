# Edi Rename Review 1: Edstar Project Persistence

## Findings

1. [high] The schema-marker simplification left stale `_edi.schema_name`
   expectations behind. `section_to_edi()` now writes only
   `_edi.schema_version 1` (`src/easydiffraction/io/edi/serialize.py:9`,
   `src/easydiffraction/io/edi/serialize.py:44`,
   `src/easydiffraction/io/edi/serialize.py:47`), which matches the ADR
   and plan, but `test_save_writes_experiment_edi_files` still asserts
   `_edi.schema_name EasyDiffraction`
   (`tests/unit/easydiffraction/project/test_project_coverage.py:427`).
   The user guide project-layout sample also still shows
   `_edi.schema_name`
   (`docs/docs/user-guide/analysis-workflow/project.md:120`). Please
   update the stale test and documentation sample to the version-only
   marker so the checked behavior and user-facing docs match the new Edi
   schema.

2. [medium] Old `.edifa` section files are silently ignored in mixed
   project directories. `_load_edi_directory()` loads `*.edi` files and
   explicitly rejects legacy `*.cif` files
   (`src/easydiffraction/project/project.py:152`,
   `src/easydiffraction/project/project.py:158`), but it does not
   recognize `*.edifa` as an unsupported previous project-state suffix.
   A directory containing `project.edi` plus stale
   `structures/lbco.edifa` or `experiments/hrpt.edifa` would restore
   without those structures/experiments instead of failing loudly. The
   same gap exists for root or nested `analysis.edifa`, since
   `_resolved_analysis_path()` checks only `.edi` and legacy `.cif`
   paths (`src/easydiffraction/project/project.py:199`,
   `src/easydiffraction/project/project.py:206`). Given persisted-state
   restore is a boundary input, please reject `.edifa` files explicitly
   with the same migration-style error rather than silently skipping
   them.

3. [low] The tutorial-output task comment in `pixi.toml` still says it
   parses `analysis.edifa` (`pixi.toml:128`). The task itself now reads
   `analysis.edi`, so this is documentation drift in the developer task
   list. Please update the comment to avoid sending the next verifier
   looking for the old extension.

## Checks Skipped

Static review only. I did not run tests, lint, formatters, builds, or
any `pixi` commands.
