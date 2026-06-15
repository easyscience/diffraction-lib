# Plan: Documentation snippet smoke tests

This plan follows [`AGENTS.md`](../../../AGENTS.md). No deliberate
exceptions to those instructions are required.

## ADR

Implements decision 3 ("Add snippet smoke tests for user-facing
examples") of the accepted ADR
[`documentation-ci-build.md`](../adrs/accepted/documentation-ci-build.md).
No new ADR is required. The ADR's "Implementation Status" table marks
this decision as the highest-value remaining gap, and its "Deferred
Work" section points at this plan.

## Motivation

User-facing code snippets drift from the public API. A recent pass found
`from easydiffraction import Structure / Experiment` (neither exported)
and `download_from_repository(...)` (does not exist) live in
`user-guide/first-steps.md`. The strict MkDocs build and link checker do
not execute Python, so this class of breakage reaches readers. A small,
fast, backend-free smoke test that exercises the documented public API
shape would catch it before merge.

## Branch and PR

- Branch: `documentation-snippet-tests` (flat slug, off `develop`).
  Created and checked out by `/draft-impl-1`.
- PR targets `develop`, not `master`. Do not push unless asked.

## Decisions

- **Explicit markers, not blanket extraction.** Only fenced
  ` ```python ` blocks explicitly opted in are executed. Many documented
  snippets are intentionally non-self-contained (they reference a
  `project` built in an earlier block, download data, or run `fit()`
  against a real backend); auto-running every block would force heavy
  fixtures and network/backends, which the ADR rules out. The opt-in
  marker is an HTML comment on the line immediately before the fence:
  `<!-- api-shape-test -->`. This keeps the test set curated and the
  intent visible in the source Markdown.
- **API shape only, no computation.** Marked snippets construct small
  in-memory objects and assert public names exist (`Project()`,
  `project.structures.create(...)`, `experiment.peak.type = ...`,
  `project.analysis.minimizer.show_supported()`,
  `project.display.parameters.all()`). They must not download data, run
  `fit()`, or select a real calculator/sampler backend.
- **No network, no real backends, no notebooks.** The runner sets a
  guard (monkeypatched `download_data`/`download_tutorial` that raise,
  and a check that no marked snippet imports a calculator backend).
  Snippets run in a unique temp working directory.
- **Test tier: `tests/functional/`.** These are fast, in-process,
  backend-free checks of the public API as documented — the same tier as
  the existing functional suite (`pixi run functional-tests`, no
  `-n auto`, no backends). They are not unit tests (they do not mirror a
  single `src/` module) and not integration tests (no network/backends),
  so `tests/unit/` structure mirroring (`test-structure-check`) is
  unaffected.
- **One always-on shape check, independent of markers.** In addition to
  marked-snippet execution, a parametrised test scans the doc set for
  `from easydiffraction import <name>` and `edi.<name>` references and
  asserts each resolves against the installed package. This alone would
  have caught the `first-steps.md` regression and needs no per-snippet
  curation.
- **Scope of pages (initial).** Per the ADR:
  `docs/docs/quick-reference/index.md`,
  `docs/docs/user-guide/first-steps.md`,
  `docs/docs/user-guide/analysis-workflow/*.md`. Expandable later.

## Open questions

- Marker syntax: `<!-- api-shape-test -->` HTML comment (recommended,
  invisible in rendered docs) vs. a fenced info string like
  ` ```python title="api-shape-test" `. Recommendation: HTML comment.
  Confirm during `/draft-impl-1`.
- Whether to wire the new pixi task into the `lint-format.yml` gate now
  or fold it into `functional-tests` (already in `pixi run all` and the
  test workflow). Recommendation: fold into `functional-tests` so no CI
  wiring change is needed; add a thin `docs-snippet-tests` alias for
  local runs.

## Concrete files likely to change

- New: `tests/functional/test_docs_snippets.py` — the runner: snippet
  extraction (reuse the Markdown-walking style of
  `tools/test_scripts.py` and the skip-list pattern of
  `docs/docs/conftest.py`), the marked-snippet execution test, and the
  always-on import-shape test.
- New (optional): a tiny helper module if extraction logic is shared,
  e.g. `tests/functional/_docs_snippets.py`.
- `pixi.toml` — add a `docs-snippet-tests` convenience task (and, per
  the open question, optionally have `functional-tests` already cover
  it).
- `docs/docs/quick-reference/index.md`,
  `docs/docs/user-guide/first-steps.md`,
  `docs/docs/user-guide/analysis-workflow/*.md` — add
  `<!-- api-shape-test -->` markers above the curated safe snippets;
  make minimal edits only where a snippet must be self-contained to run.
- `docs/dev/adrs/accepted/documentation-ci-build.md` — flip decision 3
  in the Implementation Status table from "Not done" to "Done" and drop
  the matching Deferred Work bullet (final Phase 1 step before the
  gate).

## Implementation steps (Phase 1)

Each `- [ ]` step is one atomic commit. An AI agent following this plan
must edit the checkbox to `- [x]`, stage the listed files with explicit
paths, and commit locally with the step's `Commit:` line **before**
moving to the next step (per AGENTS.md → Commits). Do not create or run
the test suite as a debugging tool during Phase 1; Phase 2 owns
verification.

- [ ] **P1.1 — Add the import-shape test (always-on).** Create
      `tests/functional/test_docs_snippets.py` with the doc-page list
      and a parametrised test that extracts every
      `from easydiffraction import <name>` and `edi.<name>` reference
      from the listed pages and asserts each name resolves on the
      installed `easydiffraction` package. Files:
      `tests/functional/test_docs_snippets.py`. Commit:
      `Add import-shape smoke test for doc snippets`

- [ ] **P1.2 — Add the marked-snippet extractor and runner.** Extend the
      test module to collect ` ```python ` blocks preceded by
      `<!-- api-shape-test -->`, and exec each page's marked blocks in a
      shared namespace inside a unique temp cwd, with `download_data` /
      `download_tutorial` monkeypatched to raise and a guard rejecting
      any real-backend selection. No snippets are marked yet, so the
      test is a no-op collection at this point. Files:
      `tests/functional/test_docs_snippets.py` (+ optional
      `tests/functional/_docs_snippets.py`). Commit:
      `Add marked-snippet runner for doc smoke tests`

- [ ] **P1.3 — Mark and (minimally) adapt Quick Reference snippets.**
      Add `<!-- api-shape-test -->` to the backend-free, self-contained
      snippets in `quick-reference/index.md` (session start,
      build-a-project in code, show/select-type blocks). Make the
      smallest edits needed for them to run standalone; do not change
      documented behaviour. Files: `docs/docs/quick-reference/index.md`,
      `tests/functional/test_docs_snippets.py` (if fixtures needed).
      Commit: `Mark Quick Reference snippets for smoke testing`

- [ ] **P1.4 — Mark and adapt First Steps and Analysis Workflow
      snippets.** Same treatment for `user-guide/first-steps.md` and
      `user-guide/analysis-workflow/*.md`. Files:
      `docs/docs/user-guide/first-steps.md`,
      `docs/docs/user-guide/analysis-workflow/*.md`. Commit:
      `Mark user-guide snippets for smoke testing`

- [ ] **P1.5 — Add the `docs-snippet-tests` pixi task.** Add a
      convenience task running the new file (e.g.
      `docs-snippet-tests = 'python -m pytest tests/functional/test_docs_snippets.py --color=yes -v'`).
      Confirm the open question on `functional-tests` coverage; if
      folding in, no workflow change is required. Files: `pixi.toml`.
      Commit: `Add docs-snippet-tests pixi task`

- [ ] **P1.6 — Update the ADR Implementation Status.** In
      `documentation-ci-build.md`, flip decision 3 to "Done" with a
      pointer to the new task, and remove the snippet-tests bullet from
      Deferred Work. Files:
      `docs/dev/adrs/accepted/documentation-ci-build.md`. Commit:
      `Mark snippet smoke tests done in documentation-ci-build ADR`

- [ ] **P1.7 — Phase 1 review gate (no code).** Mark this item `[x]` and
      commit the checklist update alone. Commit:
      `Reach Phase 1 review gate`

## Verification (Phase 2)

Run after Phase 1 review. Capture logs with the zsh-safe pattern where
output is needed for analysis.

```bash
pixi run fix
pixi run check > /tmp/easydiffraction-check.log 2>&1; check_exit_code=$?; tail -n 200 /tmp/easydiffraction-check.log; exit $check_exit_code
pixi run unit-tests
pixi run functional-tests > /tmp/easydiffraction-functional.log 2>&1; functional_tests_exit_code=$?; tail -n 200 /tmp/easydiffraction-functional.log; exit $functional_tests_exit_code
pixi run integration-tests
pixi run script-tests
```

Expectations:

- `pixi run functional-tests` (covering the new
  `tests/functional/test_docs_snippets.py`) passes, and the import-shape
  test fails loudly if a documented symbol is later removed or renamed.
- `pixi run check` stays clean, including `spell-check`, `link-check`,
  and the strict docs build.

## Status checklist

- [ ] P1.1 Import-shape test
- [ ] P1.2 Marked-snippet runner
- [ ] P1.3 Quick Reference snippets marked
- [ ] P1.4 User-guide snippets marked
- [ ] P1.5 `docs-snippet-tests` pixi task
- [ ] P1.6 ADR Implementation Status updated
- [ ] P1.7 Phase 1 review gate
- [ ] Phase 2 verification complete

## Suggested Pull Request

**Title:** Catch broken code examples in the documentation automatically

**Description:** EasyDiffraction now checks its own documentation: a
fast test confirms that the Python commands shown in the Quick
Reference, First Steps, and Analysis Workflow pages still match the
current software. If a future change renames or removes something used
in an example, the check fails before the documentation goes out, so the
commands you copy from the guides keep working. The check runs entirely
offline and does not perform any real calculations, so it stays quick.
