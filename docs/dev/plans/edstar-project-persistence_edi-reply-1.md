# Edi Rename Reply 1: Edstar Project Persistence

Reply to
[`edstar-project-persistence_edi-review-1.md`](edstar-project-persistence_edi-review-1.md).
All three findings agreed and fixed.

## Finding 1 [high] — Stale `_edi.schema_name` in test and docs — Agree, fixed

Verdict: agree. The marker is version-only now, so both the checked
assertion and the user-facing sample had to follow.

Action:

- The test assertion was already corrected before this review landed:
  `test_save_writes_experiment_edi_files` now asserts
  `_edi.schema_version 1`
  (`tests/unit/easydiffraction/project/test_project_coverage.py:427`,
  commit `56037465`).
- The user-guide project-layout sample no longer shows the
  `_edi.schema_name EasyDiffraction` line; it now shows only
  `_edi.schema_version 1`
  (`docs/docs/user-guide/analysis-workflow/project.md:120`, commit
  `117dbf7c`).

## Finding 2 [medium] — Legacy `.edifa` files silently ignored on restore — Agree, fixed

Verdict: agree. A stale `.edifa` section in a project directory is a
boundary input and must fail loudly, like the existing `.cif` rejection,
not be skipped.

Action (commit `4c26f0a7`): added `_raise_legacy_edifa_error()` and
`.edifa` detection at every restore site in
`src/easydiffraction/project/project.py`:

- `_load_edi_directory()` rejects any `*.edifa` in a section directory
  before loading `*.edi` (covers `structures/` and `experiments/`).
- `_load_project_metadata()` rejects `project.edifa`.
- `_resolved_analysis_path()` rejects `analysis/analysis.edifa` and a
  root `analysis.edifa`.

In each case the `.edifa` check runs _before_ the matching `.edi`
lookup, so a directory mixing a stale `.edifa` with a valid `.edi` still
fails loudly rather than silently preferring one. The error mirrors the
`.cif` migration message and names `.edi` as the replacement. Coverage
added in `tests/unit/easydiffraction/project/test_project_coverage.py`
(`test_load_rejects_legacy_edifa_section_file`,
`test_load_rejects_legacy_edifa_analysis_file`).

## Finding 3 [low] — `pixi.toml` comment drift — Agree, fixed

Verdict: agree. The task reads `analysis.edi`; the comment lagged.

Action (commit `f0217275`): updated the tutorial-output task comment in
`pixi.toml:128` from `analysis.edifa` to `analysis.edi`.

## Verification

`pixi run check` clean (11/11). Unit suite green (3551 passed) including
the two new `.edifa`-rejection tests; integration green (192 passed)
against the regenerated `.edi` external data. Script/functional/
tutorial-baseline gates are running as part of the final pre-push
verification.
