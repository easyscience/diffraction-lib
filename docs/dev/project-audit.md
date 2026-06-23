# Project Audit — Findings and Suggestions

**Date:** 2026-06-23
**Branch:** `develop` (post-merge of peak-profile-cutoff + microstructural size-strain).
**Purpose:** Input for the next step — correcting/extending ADRs and open
issues before applying code changes. This file is a working triage
document, not a permanent artifact; remove it once its findings have been
folded into ADRs/issues.

**Method.** Read-only audit of the codebase (`src/easydiffraction/` — 296
first-party modules, 300 including vendored snapshots), all ADRs (56 accepted,
7 suggestions, plus the index), and the open/closed issue backlog (147 open).
No tests/lint/build were run. Each finding was verified against the code or
document it cites. (Counts as of the audit date; reproduce with
`find src/easydiffraction -name '*.py'`, `ls docs/dev/adrs/accepted/*.md`,
`ls docs/dev/issues/open/*.md`.)

**How to read this.** Items are sorted by priority (highest → lowest) using
the project's own scale. Each finding tags its **Area** and a **Ref**:
- `NEW` — no existing ADR/issue covers it; file one.
- `AMEND <file>` — an existing issue/ADR exists but its text is stale,
  mis-scoped, or mis-prioritized; fix it.
- `TRACKED` — already filed and accurate; listed only for completeness.

An appendix records what was checked and found **clean**, so the next step
knows the coverage.

---

## HIGHEST

None. The original item 1 (TOF cryspy background) was verified during review as
**not** a wrong-science risk — the user's background is added at the model layer,
independent of the cryspy bootstrap CIF — and reclassified to MEDIUM (now item 1
in that section).

---

## HIGH

### 2. Nuclear-only reflection-filter issue reads as unimplemented, but the local fix shipped
- **Area:** Issues · **Ref:** AMEND `highest_nuclear-only-reflection-filter-drops-valid-peaks.md`
- **Location:** issue file; `src/easydiffraction/analysis/calculators/cryspy.py:187,295`
- **Problem:** The issue's "**Fix:** set `flag_only_nuclear = False`" is already
  done at `cryspy.py:295` (powder) and `:187` (structure factor) — landed in the
  same commit as the issue (`d785903d`, the #212 size/strain PR). The text still
  frames the local fix as pending, misleading triage.
- **Action:** Reframe to "local mitigation shipped (cite `cryspy.py:295`);
  remaining scope = report over-filtering upstream to cryspy and re-enable the
  pre-filter only once cryspy filters correctly." Re-decide whether it stays
  `highest` once it is purely upstream-tracking.

### 3. Single-row ASCII data file crashes with opaque IndexError
- **Area:** Code · **Ref:** AMEND `medium_bragg-powder-ascii-loader-returns-zero-points-instead-of-raising.md`
- **Location:** `src/easydiffraction/io/ascii.py:270` + `datablocks/experiment/item/bragg_pd.py:141`
- **Problem:** `load_numeric_block` returns `np.loadtxt(...)`, which yields a 1-D
  array for a single data row; the caller does `data.shape[1]` → bare
  `IndexError: tuple index out of range` at a user-input boundary (hand-made
  one-point file) instead of a clear "needs ≥2 columns" message.
- **Action:** `np.atleast_2d(...)` in the loader (or normalize `ndim` before
  shape checks). Fold into the ASCII-loader issue.

### 4. ASCII loader silently returns 0 points under WARN logger mode
- **Area:** Code · **Ref:** AMEND `medium_bragg-powder-ascii-loader-returns-zero-points-instead-of-raising.md`
- **Location:** `src/easydiffraction/datablocks/experiment/item/bragg_pd.py:141-146`
- **Problem:** On a too-few-columns file the code does `log.error(...)` then
  `return 0`. Default RAISE mode makes `return 0` dead; under WARN mode the
  function silently returns 0, leaving the experiment with no data and no
  exception — a silent-failure boundary path.
- **Action:** Raise `ValueError` directly; drop the conditional `return 0`.
  Same issue as #3. (Cross-link to the logger-reaction-mode issues
  `high_clarify-logger-default-reaction-mode.md` /
  `high_decide-error-handling-strategy-log-error-vs-raise.md`.)

### 5. Unknown crystal system returns an unconstrained cell instead of failing cleanly
- **Area:** Code · **Ref:** AMEND `low_improve-error-handling-in-crystallography-utilities.md` (escalate)
- **Location:** `src/easydiffraction/crystallography/crystallography.py:134-138`
- **Problem:** For an unrecognized `crystal_system`, the code `log.error(msg)`
  (no `exc_type`) then falls through to `return cell` with no symmetry
  constraints applied. Default RAISE raises a generic (non-`ValueError`)
  error; under WARN it silently returns an unconstrained cell. `crystal_system`
  is a raw string compared to literals, so an unsupported value is reachable.
- **Action:** Raise `ValueError` explicitly (`exc_type=ValueError`); model
  crystal systems as a `(str, Enum)`. Escalate this issue above `low`.

### 6. Three suggestion ADRs are missing from the ADR index
- **Area:** ADR · **Ref:** NEW (index fix)
- **Location:** `docs/dev/adrs/index.md`
- **Problem:** `suggestions/cif-numeric-precision.md`,
  `suggestions/in-house-calculation-engine.md`, and
  `suggestions/lazy-pattern-recalculation.md` exist on disk but have no index
  row. The index is the stated navigation surface, so these proposals are
  invisible.
- **Action:** Add three "Suggestion" rows under the right groups, each linking
  to the `suggestions/...` path.

### 7. Issue 163 instructs deleting the now-live absorption package
- **Area:** Issues · **Ref:** AMEND `low_fix-gitignore-gaps-and-remove-the-stale-absorption-package.md`
- **Location:** issue file; `src/easydiffraction/datablocks/experiment/categories/absorption/`
- **Problem:** The third bullet says the `absorption/` package "contains no
  tracked source (only a stale `__pycache__/`)" and says to remove it. That is
  no longer true — it now holds implemented source (`base.py`, `cylinder_hewat.py`,
  `none.py`, `factory.py`, `__init__.py`) from the sample-absorption feature.
  Acting on the instruction would delete live code. (The two `.gitignore`
  bullets — `.pyc` → `*.pyc`, add `benchmark.json` — remain valid.)
- **Action:** Drop the "remove absorption package" bullet and the title clause;
  keep the two `.gitignore` fixes; retitle. Priority high because the stale
  instruction is actively dangerous.

---

## MEDIUM

### 1. cryspy bootstrap CIF writes a dummy flat-zero background with mislabeled TOF tags
- **Area:** Code · **Ref:** AMEND `medium_clarify-cryspy-tof-background-cif-tag-names.md`
- **Location:** `src/easydiffraction/analysis/calculators/cryspy.py:1718-1725`
- **Problem:** `_cif_background_section` emits, for both CWL and TOF, two
  background points at `twotheta_min`/`twotheta_max` with hardcoded `0.0`
  intensity (four `# TODO: !!!!????` markers); for TOF the tag is
  `_tof_backgroundpoint_time` but the written values are 2θ, not TOF times.
  **Not a wrong-science risk** (verified in review): the user's real background
  is added at the model layer — background categories (update priority 10) set
  `data.intensity_bkg`, and powder data (priority 100) writes
  `calc + self.intensity_bkg` into `intensity_calc`
  (`datablocks/experiment/categories/data/bragg_pd.py:578`). The dummy cryspy CIF
  section is therefore dead/cosmetic, not a background-dropping path.
- **Action:** Medium cleanup — remove the dead hardcoded background section (or
  populate it correctly, with TOF times for TOF) and fix the mislabeled tags;
  fold into the existing tag-names issue. No escalation. (Originally filed as
  item 1 under HIGHEST; reclassified after review.)

### 8. development-docs-structure ADR documents a stale issues layout
- **Area:** ADR · **Ref:** NEW (ADR fix)
- **Location:** `docs/dev/adrs/accepted/development-docs-structure.md:39-41`
- **Problem:** The diagram shows flat `issues/open.md` + `issues/closed.md`. The
  real (and AGENTS.md-mandated) layout is one file per issue under
  `issues/open/` + `issues/closed/` plus `issues/index.md`.
- **Action:** Update the diagram to `issues/{index.md, open/, closed/}` and note
  the one-file-per-issue convention.

### 9. Promote `upstream-capability-request-evidence` — already in active use
- **Area:** ADR · **Ref:** AMEND (promote suggestion → accepted)
- **Location:** `docs/dev/adrs/suggestions/upstream-capability-request-evidence.md`
- **Problem:** Status "Proposed", but the convention is already followed:
  `docs/dev/crysfml-python-api-feature-requests.md` +
  `docs/dev/crysfml-python-api-requests/` (10 `request_NN_*.py`, `cfl_common.py`,
  `fullprof/` fixtures).
- **Action:** Promote to `accepted/` (git mv, Status: Accepted, add index row),
  or downgrade the text to "documents an existing convention".

### 10. Promote `verification-example-lifecycle` — already in active use
- **Area:** ADR · **Ref:** AMEND (promote suggestion → accepted)
- **Location:** `docs/dev/adrs/suggestions/verification-example-lifecycle.md`
- **Problem:** Status "Proposed", but `docs/docs/verification/` already follows
  the proposed `<experiment-type>_<sample>_<feature>` naming + reference-dir
  conventions across ~28 `.py` examples and ~18 `fullprof/` dirs. The index row
  already points at the `suggestions/` path.
- **Action:** Promote to `accepted/`, flip Status, repoint the index link.

### 11. `fit-output-files-and-data-exports` suggestion is stale vs shipped code
- **Area:** ADR · **Ref:** AMEND (reword/narrow)
- **Location:** `docs/dev/adrs/suggestions/fit-output-files-and-data-exports.md`
- **Problem:** Frames `results.csv` and `mcmc.h5` as open questions, but both are
  implemented (`analysis/sequential.py` → `analysis/results.csv`;
  `io/results_sidecar.py` → `analysis/mcmc.h5`). Only `data.h5` and an `exports/`
  CSV dir remain.
- **Action:** Mark `results.csv`/`mcmc.h5` delivered (xref
  `analysis-cif-fit-state.md`); rescope to the remaining archive/export items.

### 12. Many modules missing `from __future__ import annotations`
- **Area:** Code · **Ref:** NEW
- **Location:** e.g. `crystallography/crystallography.py:1`, `core/identity.py:1`,
  `core/validation.py:1`, `core/diagnostic.py:1`, all
  `datablocks/experiment/categories/peak/*.py`,
  `analysis/minimizers/{base,dfols,lmfit}.py`
- **Problem:** AGENTS.md (Code Style) requires the import in *every* module, and
  many source files lack it (the linter does not enforce it universally). No
  count is quoted here on purpose: the number is highly sensitive to scope
  (whether package `__init__.py` files and vendored snapshots are counted), and
  independent passes disagreed — so any figure is misleading unless its exact
  command and scope travel with it.
- **Action:** First fix the scope — exclude vendored paths, and decide whether
  package `__init__.py` files must carry the import — then generate the exact
  list with a recorded command (e.g. `grep -L "from __future__ import
  annotations" $(find src/easydiffraction -name '*.py' -not -path '*/vendor/*'
  -not -path '*/_vendored/*')`) and add the import as the first line of each
  listed module in one mechanical pass. (Priority is consistency, not
  correctness.)

### 13. Display `engine` setter swallows ValueError; renderer selector surface is off-contract
- **Area:** Code · **Ref:** NEW
- **Location:** `src/easydiffraction/display/base.py:69-74`
- **Problem:** The `engine` setter catches the factory `ValueError` for an
  unsupported engine, logs a warning, and returns — silently leaving the engine
  unchanged at a user-input boundary. Separately, `RendererBase` exposes
  `engine` (writable) + `show_supported_engines()` + `show_current_engine()`,
  which does not match the category-owned-selector contract (`<category>.type`,
  `show_supported()`, private `_swap_*`).
- **Action:** Raise on an unsupported engine. Decide whether renderer selection
  should follow the switchable-category contract or be explicitly documented as
  exempt (display-only backend, not a domain switchable).

### 14. Per-collection `_update` recalculation logic duplicated across powder data
- **Area:** Code · **Ref:** AMEND `medium_refactor-data-update-methods-split-and-unify.md`
- **Location:** `datablocks/experiment/categories/data/bragg_pd.py:781-793`,
  `.../data/total_pd.py:240-267` (TODO at `total_pd.py:252` flags it)
- **Problem:** The "loop linked structures → fetch calculator → accumulate
  `scale * calculate_pattern` → set result" loop is copy-pasted across
  `bragg_pd`, `total_pd`, `bragg_sc` with small variations and a self-admitted
  divergence-risk TODO.
- **Action:** Extract a shared base-class helper. Fold into the existing refactor
  issue.

### 15. Near-zero uncertainty clamp duplicated between CIF and ASCII paths
- **Area:** Code · **Ref:** AMEND `highest_unify-uncertainty-floor-handling-across-bragg-pd-single-crystal-and-pdf-data.md`
- **Location:** `bragg_pd.py:701-706` (CIF read) and `bragg_pd.py:163` (ASCII loader)
- **Problem:** The `np.where(su < _MIN_UNCERTAINTY, 1.0, ...)` workaround lives in
  two places with a TODO (`bragg_pd.py:694-700`) asking for a consistent
  approach; the two data sources can diverge.
- **Action:** Centralize the clamp in `NumericDescriptor`'s validator so CIF and
  ASCII cannot diverge. Cross-link to the existing highest uncertainty-floor issue.

### 16. TOF size/strain microstructural parameters lack mixin-level unit tests
- **Area:** Tests · **Ref:** NEW
- **Location:** `tests/unit/.../peak/test_tof_mixins.py`; source
  `tof_mixins.py` (`broad_gauss_size_g`, `broad_gauss_strain_g`,
  `broad_lorentz_size_l`, `broad_lorentz_strain_l`)
- **Problem:** The four new size/strain `Parameter`s and their properties are
  never asserted to exist/default/set in the mixin tests (only covered
  indirectly via `test_cryspy.py:707-726`), unlike every sibling param in the
  same file.
- **Action:** Add assertions that each appears in `p.parameters`, defaults to
  0.0, and updates via its setter. (Phase 2 work per the two-phase workflow.)

### 17. Issue 79 (silent save/load drift) is filed `low` despite silent-data-loss framing
- **Area:** Issues · **Ref:** AMEND `low_verify-completeness-of-analysis-cif-serialisation.md`
- **Location:** issue file
- **Problem:** It describes the same silent-loss class as issues 139 (highest) /
  142 (medium) but sits at `low`. Defensible as an *audit* task (no concrete
  missing field named), but inconsistent with the persistence-correctness cluster.
- **Action:** Either elevate to `medium`, or add a one-line note that it is an
  audit task (no confirmed loss yet) to justify `low`.

### 18. Issue 20 (cryspy stderr) is largely implemented — stale line numbers + orphan TODOs
- **Area:** Issues · **Ref:** AMEND `low_redirect-or-suppress-cryspy-stderr-warnings.md`
- **Location:** issue file; `analysis/calculators/cryspy.py:195,343` (redirects),
  `:190,338` (orphan `# TODO: Redirect stderr`)
- **Problem:** The redirect is already implemented (`contextlib.redirect_stderr`
  at 195/343); the cited `#L112`/`#L184` are stale (112 is now pref-orient code).
- **Action:** Close as substantially fixed, or rescope to "remove satisfied TODO
  comments + confirm all cryspy entry points are covered"; fix line refs.

---

## LOW

### 19. String-dispatch `getattr(self, f'_{attr}')` in the identity resolver
- **Area:** Code · **Ref:** NEW
- **Location:** `src/easydiffraction/core/identity.py:38` (and `:45`)
- **Problem:** `_resolve_up` builds attribute names by interpolation where `attr`
  ∈ {`datablock_entry`, `category_code`, `category_entry`}. AGENTS.md forbids
  string dispatch; `attr` is internal so it plausibly fits the "narrow framework
  metadata lookup" exception, but it is not centrally validated nor enum-modeled.
- **Action:** Replace with explicit branches, or model the three values as a
  `(str, Enum)` validated centrally to land cleanly inside the exception.

### 20. `Logger.print` uses `**kwargs`
- **Area:** Code · **Ref:** NEW
- **Location:** `src/easydiffraction/utils/logging.py:683-707`
- **Problem:** AGENTS.md forbids `**kwargs`. `Logger.print` is a project-owned
  public façade forwarding to Rich; it could enumerate the console options it
  supports. (Other `**kwargs` hits are `super().__init__` plumbing or
  third-party solver passthroughs — arguably exempt.)
- **Action:** Replace with explicit keyword args, or document the
  framework-passthrough exception.

### 21. Commented-out dead code blocks in boundary modules
- **Area:** Code · **Ref:** AMEND `low_remove-stale-commented-out-dead-code-in-core-and-io.md`
- **Location:** `io/cif/parse.py:65-71` (dead `experiment_type_from_block`),
  `display/__init__.py:15-18` (disabled scroll-manager call),
  `data/bragg_pd.py:742-744`, `io/cif/serialize.py:860`
- **Problem:** Dead/uncertain commented blocks clutter boundary modules.
- **Action:** Delete the dead `parse.py` function and `bragg_pd` comment; resolve
  or file the MkDocs scroll-disable; resolve the serialize.py "check methods" TODO.

### 22. `called_by_minimizer` flag is threaded through but unused in cell update
- **Area:** Code · **Ref:** AMEND `low_clarify-cell-update-usage-of-called-by-minimizer.md`
- **Location:** `datablocks/structure/categories/cell/default.py:176-192`
- **Problem:** `_update(called_by_minimizer=...)` immediately `del`s the flag
  (`# TODO: ???`, docstring "Currently unused"), yet it is threaded through the
  whole update chain (`total_pd.py:261`, `bragg_pd.py:786`).
- **Action:** Implement the intended fast-path (skip symmetry recompute during
  fitting) or remove the dead parameter. Fold into the existing issue.

### 23. 552 KB `handler-inventory.json` under the edstar ADR dir has a generator but no ADR link
- **Area:** ADR · **Ref:** NEW
- **Location:** `docs/dev/adrs/accepted/edstar-project-persistence/handler-inventory.json`;
  generator `tools/edi_handler_inventory.py:25,359`
- **Problem:** It is **not** an orphan (correcting the original finding): the file
  is the generated output target of a repository tool —
  `tools/edi_handler_inventory.py` assembles the path as `DEFAULT_OUTPUT`
  (`:18-25`) and writes it (`:359`). But unlike the other two ADR sibling dirs, it
  is not linked from `edstar-project-persistence.md`, so a reader of the ADR has
  no pointer to what it is or how it is regenerated.
- **Action:** Add a one-line reference/regeneration note in the ADR citing
  `tools/edi_handler_inventory.py` (do **not** delete it).

### 24. Superseded `parameter-posterior-summary` ADR still lives under `suggestions/`
- **Area:** ADR · **Ref:** NEW (organizational)
- **Location:** `docs/dev/adrs/suggestions/parameter-posterior-summary.md` (index line 26)
- **Problem:** Status "Superseded" and the design is implemented
  (`core/posterior.py`, `Parameter.posterior`), but a superseded/implemented ADR
  under `suggestions/` is an odd state.
- **Action:** Relocate to `accepted/` (historical record) keeping Status
  "Superseded", or move to an archive. No correctness impact.

### 25. `cutoff_fwhm` mixin getter/setter not covered at the mixin-test level
- **Area:** Tests · **Ref:** NEW
- **Location:** `tests/unit/.../peak/test_{cwl,tof}_mixins.py`; source
  `cwl_mixins.py:145-162`, `tof_mixins.py:143-160`
- **Problem:** `cutoff_fwhm` is covered at the concrete-class level
  (`test_cwl.py`/`test_tof.py` default + negative-reject) but not in the mixin
  tests targeting these exact files. Thoroughness gap, not an untested path.
- **Action:** Optionally add a mixin-level getter/setter assertion; otherwise no
  action (already covered).

### 26. `AdpTypeEnum.description()` is never exercised
- **Area:** Tests · **Ref:** NEW
- **Location:** `structure/categories/atom_sites/enums.py`; rollup
  `tests/unit/.../structure/categories/test_atom_sites.py`
- **Problem:** Members and `.default()` are tested, but `description()` is not —
  inconsistent with `SampleFormEnum`/`PeakProfileTypeEnum`, which test it.
- **Action:** Add a parametrized test asserting `description()` is non-empty for
  every member.

### 27. Size/strain feature row links to the plain JVD verification page
- **Area:** Docs · **Ref:** NEW
- **Location:** `docs/docs/features/index.md:319`
- **Problem:** The Jorgensen–Von Dreele row advertises `size_g/strain_g/size_l/
  strain_l` but its verification decagram points at
  `pd-neut-tof_Si_jorgensen-von-dreele.ipynb` (no size/strain), while a dedicated
  `pd-neut-tof_Si_jorgensen-von-dreele-size-strain.ipynb` exists.
- **Action:** Add a second decagram link (or sub-note) to the size/strain
  verification page so the claim is backed.

### 28. Stray local artifacts in the verification tree (already gitignored — cleanup only)
- **Area:** Tutorials · **Ref:** NEW (local cleanup)
- **Location:** `docs/docs/verification/fort.77` (FullProf scratch),
  `docs/docs/verification/__pycache__/`, `.ipynb_checkpoints/` holding
  old lowercase verification stems
- **Problem:** Leftover generated artifacts sitting in the verification dir. These
  are **already ignored** (correcting the original finding): `.gitignore` has
  `fort.*` (`:67`), `__pycache__/` (`:2`), and `.ipynb_checkpoints` (`:26`), so
  they cannot be accidentally staged. The only open question is whether to delete
  the local copies so they stop confusing readers grepping the dir.
- **Action:** Local cleanup only — `rm` the stray files; **no `.gitignore` change
  needed** (coverage already exists).

### 29. No-op `assert True` in `test_logging.py`
- **Area:** Tests · **Ref:** TRACKED `low_replace-no-op-assert-true-in-test-logging-py.md`
- **Location:** `tests/unit/easydiffraction/utils/test_logging.py:26`
- **Problem:** `test_logger_configure_and_warn_reaction` ends in `assert True`
  ("nothing to assert"), verifying no observable effect. Already filed.
- **Action:** None new — confirm the existing issue captures replacing it with
  real assertions (capsys output, `_reaction`/`_mode`/`_level`, no-raise in WARN).

---

## Appendix A — Verified clean (no defect; coverage record)

These were actively checked and found correct; recorded so the next step does
not re-investigate them.

- **High-traffic ADRs match the code:** `switchable-category-owned-selectors`,
  `selector-families`, `factory-contracts`, `minimizer-input-output-split`,
  `peak-profile-cutoff`, `enum-backed-closed-values`. Verified
  `experiment.{calculator,background,peak}`, `analysis.{minimizer,fitting_mode}`,
  `project.rendering_{plot,table}` expose category-owned `.type` +
  `show_supported()` with only private `_set_*`/`_swap_*`; `analysis.fit_result`
  + `_fit_result_class` present; `cutoff_fwhm` default 0.0 injected as
  `profile_cutoff_fwhm`; the enums are all StrEnum.
- **Issue index is mechanically clean:** 147 open files == 147 rows; all links
  resolve both ways; priority columns match filenames and `**Priority:**` lines;
  ordering is priority-then-number; no duplicate `# <n>.` ids; number gaps are
  consistent with the no-reuse rule.
- **Sequential-fit issue cluster (121/123/124/125/126/127) is genuinely distinct**
  — no duplicates to merge; issue 27 is intentionally retained as the narrow
  predecessor of 140.
- **Staleness false-positives:** cutoff auto-detection (#179) and the dead-else
  in `_set_calc_status` (#151, `bragg_pd.py:425-434`) are both still accurate —
  not fixed by recent work.
- **Test mirroring satisfied** for all recently added code (peak mixins,
  excluded_regions, atom_sites, data_range) per `tools/test_structure_check.py`.
- **Unit suite is hermetic** against Logger WARN/RAISE leakage —
  `tests/unit/conftest.py:25-41` resets reaction/mode around every test; no
  network/sleep/real-engine usage in unit tests.

## Appendix B — In-flight, out of audit scope

- **microstructural-size-strain** has 7 `_review-N`/`_reply-N` artifacts but no
  committed base plan and no ADR, while the size/strain code already exists. This
  is an in-progress design cycle, not a missing record for shipped behavior.
  Ensure the design lands as a plan (+ an ADR if it changes architecture) before
  the PR, per Change Discipline.
