# Plan: Notebook-Owned Verification Regression Gating (`known_discrepancy`)

Follows [`AGENTS.md`](../../../AGENTS.md). Two explicitly-scoped
exceptions to the usual two-phase rules:

1. A small, unrelated **Windows CI fix** is bundled at the owner's
   request (P1.7).
2. **P1.3 runs each verification page once to classify it**
   (disagree-cleanly / crash / re-gate) — a deliberate, **read-only**
   Phase-1 audit needed to decide each page's migration. It is not test
   authoring and runs no test suite; the exact command is in P1.3. All
   real test work stays in Phase 2.

## ADR

Implements
[`verification-regression-flag`](../adrs/accepted/verification-regression-flag.md)
(Accepted). Per §Change Discipline it is **promoted to `accepted/`** as
part of this PR (P1.6). The sibling
[`verification-software-version-labels`](../adrs/suggestions/verification-software-version-labels.md)
ADR is **not** implemented here — separate work.

Revises two accepted ADRs (P1.5):
[`test-suite-and-validation`](../adrs/accepted/test-suite-and-validation.md)
§6 (the `script-tests` "skip via `ci_skip.txt`" detail) and
[`documentation-ci-build`](../adrs/accepted/documentation-ci-build.md)
(the `ci_skip.txt`/conftest wiring).

## Branch + PR

- Branch: `verification-regression-flag` (flat slug off `develop`,
  **already created and checked out**; carries one prior housekeeping
  commit, `Remove completed dataset-driven-fit-modes plan`).
- PR targets `develop`, not `master`. Do not push unless asked.

## Decisions (from the ADR)

- **Flag.** `assert_patterns_agree` gains
  `known_discrepancy: bool = False` (replacing `raise_on_failure`) and a
  `reason: str | None = None` (**required** when
  `known_discrepancy=True`).
- **Two-sided assertion (Decision 1a).** `known_discrepancy=True`
  asserts the patterns **still disagree**: out of tolerance → render, do
  not raise; **within** tolerance → **raise** a re-gate
  `AssertionError`.
- **Return contract (Decision 1b).** Returns `True` when the page met
  its expectation (agree for default; still-disagree for known-bad) or
  **raises**. No longer the raw agreement boolean; raw metrics stay on
  `verify.pattern_closeness`.
- **One source of truth, two runners (Decision 2).** Delete
  `ci_skip.txt`; `script-tests` statically detects
  `known_discrepancy=True` **or** a `raises-exception` tag in the `.py`
  and **skips** those pages; `conftest.py`'s xfail logic is removed;
  **nbmake runs every page** (render + the re-gate hard-fail).
- **Crash boundary (Decision 3).** Pre-flag-crash pages tag the failing
  cell `raises-exception` (+ a markdown note); `script-tests` skips them
  via the same scan.
- **On-page provenance (Decision 4).** `reason` renders on the page,
  replacing the `ci_skip.txt` comment.
- **Fit hygiene (Decision 5).** A page already agreeing within tolerance
  carries no fit section.
- **Audit (ADR Open Questions).** Every page using the old
  `raise_on_failure=False` is migrated with an explicit per-page
  decision; this is a larger set than `ci_skip.txt` (P1.3).

## Decisions already made for this plan

- The audit covers **11 pages** — the 10 `.py` files using
  `raise_on_failure=False` plus `pd-neut-cwl_tch-fcj-nosldl_lab6` (in
  `ci_skip.txt` but not using the flag, so likely a crash page):
  - **In `ci_skip.txt` + `raise_on_failure=False`** (7): `beba_pbso4`,
    `tch-fcj-noabs-nosldl_lab6`, `tch-fcj-noabs_lab6`, `tch-fcj_lab6`,
    `tof_j_si`, `tof_jvd_si`, `sc-neut-cwl_ext-iso_tbti`.
  - **`ci_skip.txt` only** (1): `tch-fcj-nosldl_lab6` (no flag → audit
    as crash vs gated).
  - **`raise_on_failure=False` only, not skip-listed** (3):
    `pd-neut-tof_jvd_ncaf`, `sc-neut-cwl_noext_tbti`,
    `sc-neut-cwl_pr2nio4` — these currently pass both runners ungated,
    so the audit decides re-gate (`known_discrepancy=False`) vs keep
    `known_discrepancy=True, reason=…`.
- **Migration is mechanical except the per-page verdict**, which
  requires running each page once (disagree-cleanly vs crash; re-gate vs
  keep).
- The non-asserting `verify.patterns_agree(...) -> bool` wrapper is
  added **only if** a page or test needs a plain boolean (decide during
  P1.1).

## Open questions

1. Per-page audit verdicts (P1.3) — **resolved**, recorded below. Each
   page was run once with
   `pixi run python docs/docs/verification/<stem>.py` against installed
   cryspy 0.11.0 (the unpinned version CI also resolves), classifying by
   exit code and the rendered agreement table:

   | Page                                    | Result                         | Migration                         |
   | --------------------------------------- | ------------------------------ | --------------------------------- |
   | `pd-neut-cwl_pv-beba_pbso4`             | agrees (fit recovers FullProf) | **re-gate** (drop flag)           |
   | `pd-neut-tof_jvd_ncaf`                  | agrees                         | **re-gate** (was not skip-listed) |
   | `sc-neut-cwl_noext_tbti`                | agrees                         | **re-gate** (was not skip-listed) |
   | `sc-neut-cwl_pr2nio4`                   | agrees                         | **re-gate** (was not skip-listed) |
   | `pd-neut-cwl_tch-fcj-noabs-nosldl_lab6` | disagrees, runs                | `known_discrepancy=True`          |
   | `pd-neut-cwl_tch-fcj-noabs_lab6`        | disagrees, runs                | `known_discrepancy=True`          |
   | `pd-neut-cwl_tch-fcj_lab6`              | disagrees, runs                | `known_discrepancy=True`          |
   | `pd-neut-cwl_tch-fcj-nosldl_lab6`       | disagrees, runs (note updated) | `known_discrepancy=True`          |
   | `pd-neut-tof_j_si`                      | crysfml disagrees              | `known_discrepancy=True`          |
   | `pd-neut-tof_jvd_si`                    | cryspy disagrees               | `known_discrepancy=True`          |
   | `sc-neut-cwl_ext-iso_tbti`              | disagrees                      | `known_discrepancy=True`          |

   No page crashed before its agreement check, so **no
   `raises-exception` cell tags were needed**. The three not-skip-listed
   pages (`jvd_ncaf`, `sc-noext`, `sc-pr2nio4`) all agree, so all are
   re-gated. `pv-beba_pbso4` was previously skip-listed but now agrees
   after its own-asymmetry fit, so it is re-gated too.
   `tch-fcj-nosldl_lab6` previously asserted agreement
   (`raise_on_failure=True`) but disagrees on released cryspy 0.11.0
   (its develop-cryspy demo agrees), so its note was updated and it is
   marked `known_discrepancy=True`.

2. `conftest.py`: **resolved at P1.2** — the file hosted only the
   ci_skip xfail logic, so it was deleted entirely.

## Concrete files likely to change

- `src/easydiffraction/analysis/verification.py` —
  `assert_patterns_agree` (flag, reason, two-sided assertion, return
  contract).
- `tests/unit/easydiffraction/analysis/test_verification.py` — all
  changes happen in **Phase 2**: migrate existing
  `raise_on_failure`/return-contract cases and add the new
  `known_discrepancy` cases. Phase 1 does not touch this file.
- `tools/test_scripts.py` — replace the `ci_skip.txt` skip with the
  in-source static scan.
- `docs/docs/conftest.py` — remove the ci_skip xfail logic.
- `docs/docs/verification/ci_skip.txt` — **deleted**.
- The 11 audited `docs/docs/verification/*.py` pages (+ regenerated
  `.ipynb` via `pixi run notebook-prepare`); also any other page
  carrying a now-removable fit section (Decision 5).
- `docs/docs/verification/index.md` — wording that referenced CI-skip.
- `docs/dev/testing-guide.md` (~line 82) and the `verification-exec`
  task comment in `pixi.toml` (~line 233) — `ci_skip` references that go
  stale once the file is deleted; plus anything else the `git grep`
  surfaces.
- `docs/dev/adrs/suggestions/verification-regression-flag.md` → `git mv`
  to `accepted/`; `docs/dev/adrs/index.md` row flipped to Accepted;
  links fixed.
- `docs/dev/adrs/accepted/test-suite-and-validation.md`,
  `docs/dev/adrs/accepted/documentation-ci-build.md` — revise the
  `ci_skip.txt` wiring text.
- `src/easydiffraction/analysis/analysis.py` line ~2819 — **Windows
  fix** (see P1.7).

Find every occurrence first with
`git grep -n "raise_on_failure\|ci_skip"`.

## Implementation steps (Phase 1)

Each `- [ ]` is one atomic commit; stage only the listed paths; commit
each before the next.

- [x] **P1.1 — `known_discrepancy` in `assert_patterns_agree`.** In
      `verification.py`: replace `raise_on_failure` with
      `known_discrepancy: bool = False` and add
      `reason: str | None = None` (required when
      `known_discrepancy=True`); implement the two-sided assertion
      (Decision 1a) and the "expectation met" return (Decision 1b);
      raise a clear re-gate `AssertionError` on unexpected agreement.
      Update the docstring only. **No `test_verification.py` changes in
      Phase 1** — all test work (updating the existing
      `raise_on_failure`/return-contract cases and adding the new
      `known_discrepancy` cases) is the first task of Phase 2; the tests
      may be left temporarily stale until then since they are not run
      during Phase 1. Commit:
      `Add known_discrepancy flag to assert_patterns_agree`

- [x] **P1.2 — Remove `ci_skip.txt`; make both runners in-source.**
      Delete `docs/docs/verification/ci_skip.txt`; remove the xfail
      logic from `docs/docs/conftest.py` (delete the file if nothing
      else lives there, per Open Question 2); replace the skip block in
      `tools/test_scripts.py` with a static scan that skips a
      verification `.py` declaring `known_discrepancy=True` or a
      `raises-exception` tag. Also update the `ci_skip`-mechanism
      references in `docs/dev/testing-guide.md` (~line 82) and the
      `verification-exec` task comment in `pixi.toml` (~line 233), and
      any other reference the grep surfaces, so no obsolete guidance is
      left behind. Commit:
      `Drive verification skips from in-source flag, drop ci_skip.txt`

- [x] **P1.3 — Audit and migrate the 11 pages.** _(Named Phase-1 audit
      exception — read-only classification, see intro.)_ Classify each
      page by running its source once:
      `pixi run python docs/docs/verification/<stem>.py` — a clean exit
      means it runs to completion (then its agreement table says
      disagree-cleanly vs already-agrees); an exception before the final
      agreement call means a crash page. Record the per-page verdict in
      this plan's Open Questions. Then for each: migrate
      `raise_on_failure=False` → `known_discrepancy=True, reason=…`
      (carrying the old `ci_skip.txt` reason onto the page) **or**
      re-gate by dropping the flag where it actually agrees; add
      `raises-exception` cell tags + notes for crash pages; remove fit
      sections from pages that already agree (Decision 5). Run
      `pixi run notebook-prepare`; stage the `.py` + regenerated
      `.ipynb`. Commit:
      `Migrate verification pages to known_discrepancy flag`

- [x] **P1.4 — Update verification docs prose.** Fix
      `docs/docs/verification/index.md` (and any page text) that
      described the `ci_skip.txt` mechanism. Commit:
      `Update verification docs for known_discrepancy gating`

- [x] **P1.5 — Revise the two accepted ADRs.** Update
      `test-suite-and-validation.md` §6 and `documentation-ci-build.md`
      to the in-source mechanism (no `ci_skip.txt`). **Done:** §6 of
      `test-suite-and-validation.md` gained a "Known-discrepancy gating"
      bullet describing the in-source flag/tag and the two runners. A
      `git grep` confirmed `documentation-ci-build.md` never referenced
      `ci_skip.txt`/`conftest`, so it had no stale wiring to revise and
      was left unchanged. Commit:
      `Revise accepted ADRs for in-source verification gating`

- [x] **P1.6 — Promote the ADR.** `git mv`
      `docs/dev/adrs/suggestions/verification-regression-flag.md` →
      `accepted/`; set `**Status:** Accepted`; flip its
      `docs/dev/adrs/index.md` row to Accepted with the `accepted/...`
      link; fix any links that pointed at `suggestions/...`
      (`git grep -n verification-regression-flag`). Commit:
      `Promote verification-regression-flag ADR to accepted`

- [x] **P1.7 — Windows CI fix (bundled, unrelated).** In
      `src/easydiffraction/analysis/analysis.py` (~line 2819) the
      rewritten `data_dir` is built with
      `str(Path('data') / 'sequential')`, which is `data\sequential` on
      Windows and fails `test_copy_data_archives_and_rewrites_data_dir`
      (expects `data/sequential`). Store a POSIX path:
      `Path('data', 'sequential').as_posix()` (or the literal
      `'data/sequential'`). The existing test is the spec — no test
      change. Commit:
      `Store sequential data_dir as POSIX path for Windows`

- [x] **P1.8 — Phase 1 review gate.** No-code; mark `[x]` and commit the
      checklist update alone. Commit: `Reach Phase 1 review gate`

## Status checklist

- [x] P1.1 known_discrepancy flag
- [x] P1.2 remove ci_skip.txt + runners
- [x] P1.3 audit + migrate pages
- [x] P1.4 verification docs prose
- [x] P1.5 revise accepted ADRs
- [x] P1.6 promote ADR
- [x] P1.7 Windows CI fix
- [x] P1.8 Phase 1 review gate
- [x] Phase 2 verification green

## Phase 2 — Verification

Per the `AGENTS.md` two-phase workflow, Phase 2 **starts with the test
work**, then runs the verification commands. No `test_verification.py`
edits happen in Phase 1 — Phase 1 may leave the existing tests
temporarily stale (they are not run until here).

**Step 1 — update and extend `test_verification.py` first.** Before any
`pixi run` command:

- **Update existing cases** to the changed contract: every test that
  passed `raise_on_failure=` migrates to `known_discrepancy=`, and every
  test asserting the old "returns the raw agreement boolean" return
  value migrates to the Decision 1b "expectation met" contract (`True`
  when the page met its expectation, `AssertionError` otherwise).
- **Add new cases** for the new behavior:
  - the two-sided assertion — a `known_discrepancy=True` page that is
    out of tolerance passes, and one that is within tolerance raises the
    re-gate `AssertionError`;
  - the required-`reason` validation — `known_discrepancy=True` without
    a non-empty `reason` raises;
  - the "expectation met" return value for both a default page and a
    passing `known_discrepancy=True` page.

**Step 2 — run the verification commands.** From the repo root; use the
zsh-safe log-capture when output is needed.

- `pixi run fix` (commit auto-fixes incl. regenerated
  `docs/dev/package-structure/{full,short}.md`).
- `pixi run check > /tmp/edi-check.log 2>&1; check_exit_code=$?; tail -n 200 /tmp/edi-check.log; exit $check_exit_code`
- `pixi run unit-tests > /tmp/edi-unit.log 2>&1; unit_tests_exit_code=$?; tail -n 120 /tmp/edi-unit.log; exit $unit_tests_exit_code`
  (Linux cannot reproduce the Windows path failure — the
  `test_copy_data_archives_and_rewrites_data_dir` test already passes
  here; the P1.7 fix makes it pass on Windows too.)
- `pixi run integration-tests > /tmp/edi-int.log 2>&1; integration_tests_exit_code=$?; tail -n 120 /tmp/edi-int.log; exit $integration_tests_exit_code`
- `pixi run script-tests > /tmp/edi-script.log 2>&1; script_tests_exit_code=$?; tail -n 120 /tmp/edi-script.log; exit $script_tests_exit_code`
  (must skip the `known_discrepancy=True` / `raises-exception` pages via
  the new in-source scan — confirm none of them run here).
- `pixi run notebook-tests > /tmp/edi-nb.log 2>&1; notebook_tests_exit_code=$?; tail -n 120 /tmp/edi-nb.log; exit $notebook_tests_exit_code`
  (every page executes; a still-discrepant `known_discrepancy=True` page
  passes, and a `raises-exception` page xfails cell-precisely).

## Suggested Pull Request

**Title:** Simpler, self-documenting handling of known-bad verification
pages

**Description:** A verification page that can't yet match its reference
(because an engine feature isn't implemented) is now marked **in the
notebook itself** with `known_discrepancy=True` and a short reason that
shows on the published page — replacing the separate hidden skip list.
Good pages stay regression tests as before; a known-bad page that later
starts matching now fails CI on purpose, so its "known-bad" mark gets
removed deliberately rather than lingering forever. Also fixes a
Windows-only path issue in sequential fitting so the saved data folder
is recorded consistently across operating systems.
