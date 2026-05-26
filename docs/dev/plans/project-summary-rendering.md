# Plan: Project Summary Rendering

Implementation plan for the
[`project-summary-rendering`](../adrs/suggestions/project-summary-rendering.md)
ADR. Follows [`AGENTS.md`](../../../AGENTS.md) — no deliberate
exceptions to those instructions.

## ADR cross-reference

- **Primary ADR:** `project-summary-rendering.md` (currently in
  `suggestions/`; this plan promotes it to `accepted/` as the
  final P1 step before the review gate).
- **Amends** (per the ADR's "ADRs amended by this ADR" section):
  - [`iucr-cif-tag-alignment.md`](../adrs/accepted/iucr-cif-tag-alignment.md)
    — five amendments: removes `project.save(report=True)`
    flag, redesigns `project.report.save()` (no-arg config
    reader + per-format `save_*()` methods), removes public
    `check()` + `check=True` (moves gemmi pass internal,
    CIF-only), reads `_easydiffraction_software.*` from
    persisted `analysis.software`, adds
    `_easydiffraction_software.fit_datetime` extension tag.
  - [`analysis-cif-fit-state.md`](../adrs/accepted/analysis-cif-fit-state.md)
    — adds `analysis.software` to the persisted analysis state.
  - [`project-facade-and-persistence.md`](../adrs/accepted/project-facade-and-persistence.md)
    — `project.report` gains a persisted configuration category
    (`_report.*` in `project.cif`); new top-level
    `project.publication` owner; singleton-category enumeration
    extended.
  - [`python-cif-category-correspondence.md`](../adrs/suggestions/python-cif-category-correspondence.md)
    — **proposed** (in `suggestions/`); this plan amends its
    correspondence table to add the two new surfaces
    (`project.report.* ↔ _report.*` and
    `project.publication.* ↔ _publ_*` / `_journal_*`) but
    does **not** promote it to `accepted/`. Promotion (with
    its own review cycle) is a separate concern; downstream
    code does not rely on it being accepted.

## Branch and PR

- **Branch:** `project-summary-rendering` (already checked out;
  rebased onto latest `develop`, which includes the merged IUCr
  CIF tag alignment work as PR #184).
- **PR target:** `develop`.
- Do not push the branch until both Phase 1 and Phase 2 review
  cycles close.

## Decisions already made (in the ADR)

These are settled by the accepted ADR — the plan does not
re-litigate them, only implements them:

- **Three-tier extension of `project.report`:**
  - **Config category** (§1.1, §1.3): six scalar fields on
    `project.report` (`cif`, `html`, `tex`, `pdf`, `style`,
    `html_offline`) persisted to `project.cif` as
    `_report.*`. `project.report.formats` is a property view
    over the four format booleans. Pattern A (project-level
    singleton config), not Pattern B (datablock owner) — see
    §1.3 "Why not its own CIF file?".
  - **Ad-hoc per-format methods** (§1.2): `save_cif()`,
    `save_html(offline=False)`, `save_tex(style='iucr')`,
    `save_pdf(style='iucr')` on the facade. Each ignores
    `formats` and writes its format unconditionally.
  - **Convenience save** (`project.report.save()`): reads
    config, raises `ValueError` when no formats are enabled.
- **Validation moves internal — CIF only** (§1.4): the gemmi
  dictionary-spec pass runs before every CIF write
  (`save_cif()` and the `cif` branch under `project.save()`);
  HTML/TeX/PDF get no pre-write validation. Public
  `project.report.check()` and `check=True` are **removed**;
  writer-correctness failures raise
  `EasyDiffractionWriterError`.
- **Empty-config behaviour split**: `project.save()` with
  `formats = []` writes the project as usual, no reports, no
  error. `project.report.save()` with `formats = []` raises
  `ValueError` pointing at the configuration category.
- **Enums per the accepted closed-values ADR**:
  `ReportFormatEnum('cif', 'html', 'tex', 'pdf')` and
  `ReportStyleEnum('iucr', 'revtex')`, both `(str, Enum)`. CIF
  serialisation uses the enum string values verbatim.
- **`analysis.software` provenance category** (§4): persisted
  to `analysis/analysis.cif` with framework, calculator,
  minimizer sub-categories (each `name + version + url`) plus
  a `fit_datetime` timestamp. Populated by `Analysis.fit()`
  immediately before successful return. URLs declared as
  class-level `url` constants on backend classes.
- **Missing-provenance behaviour** (§4.1): pre-fit, failed-fit,
  and pre-ADR loaded projects render `"(not available)"` on
  every surface; IUCr CIF emits `?` placeholders; no exception
  raised; `_easydiffraction_software.fit_datetime` is omitted
  when unset.
- **`project.publication` top-level owner** (§5): six sibling
  CIF-aligned sub-categories (`journal`, `journal_date`,
  `journal_coeditor`, `contact_author`, `body`, `authors`).
  Persisted to `project.cif`. TOML primary / JSON fallback
  loader (`project.publication.load(...)`). No reader for
  `reports/<project>.cif` — that file stays export-only per
  the accepted IUCr ADR.
- **Shared `ReportDataContext`** (§6): one dict feeding all
  renderers (terminal, HTML, TeX, GUI). New summary fields
  are added in one place (`data_context()`); all renderers
  pick them up.
- **CLI surface** (§7): `ed save` reads the persisted config;
  `ed save-report --html` / `--cif` / `--tex` / `--pdf
  --style iucr` is the one-off subcommand. `ed save-report`
  with no flags raises a clear error.
- **Dependencies named by the ADR** (§3.2, §3.4): `kaleido`
  (Python, runtime, `pyproject.toml`), `chromium` (pixi/conda,
  dev/docs feature), `tectonic` (pixi/conda, dev/docs feature).
  Per AGENTS.md §Architecture, naming them in this accepted
  plan plus a `/draft-impl-1` invocation counts as
  pre-approval for the implementation steps to edit
  `pyproject.toml` / `pixi.toml` / `pixi.lock`.

## Open questions to resolve during implementation

- **`formats` property class.** The Python `formats` property
  view derives a `list[ReportFormatEnum]` from the four
  booleans. Implementer decides between a thin
  `property` on `Report` versus a richer descriptor type — the
  former is simpler and fits the existing pattern.
- **Pixi env gemmi version.** Confirm the pinned `gemmi`
  supports the validation calls inherited from the
  alignment ADR. If too old, bump the constraint in
  `pyproject.toml` / `pixi.toml` / `pixi.lock` (pre-approved
  because `gemmi` is already named in the alignment ADR and
  this ADR's text).
- **LaTeX style file vendoring location.** Probable home:
  `src/easydiffraction/report/templates/tex/styles/`. Confirm
  during P1 by checking how other vendored assets are laid
  out (the project already vendors plugin templates under
  `src/easydiffraction/display/`).
- **TeX engine discovery order.** ADR §3.4 lists
  `tectonic` → `latexmk` → `pdflatex`. Confirm the discovery
  function and the "engine missing → write `.tex` + warning"
  fallback during P1.20.
- **Tutorial coverage scope.** Identify which tutorials gain
  `project.report` configuration examples (most likely
  `ed-3.py`, `ed-5.py`, `ed-8.py`, `ed-14.py` — the same
  tutorials touched by PR #184) and which gain a new
  end-to-end "save HTML + PDF" demo.

## Concrete files likely to change

**Foundation (P1.1–P1.7):**
- `src/easydiffraction/report/enums.py` (new — `ReportFormatEnum`,
  `ReportStyleEnum`).
- `src/easydiffraction/project/categories/report/` (new package:
  `__init__.py`, `default.py` — the refactored `Report` class as
  a `CategoryItem`; `factory.py` — `ReportFactory`). Mirrors the
  existing `chart/`, `table/`, `verbosity/` layout under
  `src/easydiffraction/project/categories/`.
- `src/easydiffraction/report/report.py` (existing —
  **deleted**; the current plain-facade `Report` body is
  migrated into the new package above. No shim file.
  Existing public import path `from easydiffraction.report
  import Report` continues to work via the next bullet.)
- `src/easydiffraction/report/__init__.py` (existing —
  one-line update: `from easydiffraction.report.report import
  Report` becomes `from
  easydiffraction.project.categories.report.default import
  Report`. The public `easydiffraction.report.Report` import
  path is preserved.)
- `src/easydiffraction/project/project_config.py` (existing —
  add `report` slot/property alongside `info`, `chart`,
  `table`, `verbosity`; persistence is automatic via the
  existing `category_owner_to_cif` walker).
- `src/easydiffraction/project/project.py` (existing — bind
  `self._report = self._config.report`; drop `report=True` /
  `check=True` flags from `Project.save()`).
- `src/easydiffraction/io/cif/iucr_writer.py` (existing —
  internalise the gemmi validation step).
- `src/easydiffraction/report/check.py` (existing — remove or
  re-purpose into the internal validator).

**Analysis software provenance (P1.8–P1.10):**
- `src/easydiffraction/analysis/categories/software/` (new
  package: `__init__.py`, `base.py`, `default.py`,
  `factory.py`).
- `src/easydiffraction/analysis/analysis.py` (existing — wire
  the new category into `Analysis`; populate at fit time).
- `src/easydiffraction/datablocks/experiment/categories/calculator/*.py`
  and
  `src/easydiffraction/analysis/categories/minimizer/*.py`
  (existing — add `url` class constants).
- `src/easydiffraction/io/cif/iucr_writer.py` (existing —
  read the triple from `analysis.software`; add
  `_easydiffraction_software.fit_datetime` emission).
- `docs/dev/adrs/accepted/analysis-cif-fit-state.md` (amend).

**IUCr ADR amendments (P1.11):**
- `docs/dev/adrs/accepted/iucr-cif-tag-alignment.md` (amend
  with all five amendments).

**`project.publication` category (P1.12–P1.15):**
- `src/easydiffraction/project/categories/publication/` (new
  package: `__init__.py`, `journal.py`, `journal_date.py`,
  `journal_coeditor.py`, `contact_author.py`, `body.py`,
  `authors.py`, `default.py`, `factory.py`).
- `src/easydiffraction/project/project.py` (existing — add
  `publication` facade slot).
- `src/easydiffraction/io/cif/iucr_writer.py` (existing —
  read `data_global` `_publ_*` / `_journal_*` items from
  `project.publication.*` instead of static `?` placeholders).
- `src/easydiffraction/project/publication_loader.py` (new —
  TOML/JSON loader).
- `docs/dev/adrs/accepted/project-facade-and-persistence.md`
  (amend).
- `docs/dev/adrs/suggestions/python-cif-category-correspondence.md`
  (amend).

**Shared data context + Jinja base (P1.16):**
- `src/easydiffraction/report/data_context.py` (new).
- `src/easydiffraction/report/templates/base.j2` (new).

**HTML renderer (P1.17):**
- `src/easydiffraction/report/html_renderer.py` (new).
- `src/easydiffraction/report/templates/html/report.html.j2`
  (new).
- `src/easydiffraction/report/templates/html/style.css` (new).

**LaTeX + PDF (P1.18–P1.20):**
- `pyproject.toml` (add `kaleido`).
- `pixi.toml` (add `chromium`, `tectonic` to dev/docs feature).
- `pixi.lock` (regenerated).
- `src/easydiffraction/report/templates/tex/iucr.tex.j2` (new).
- `src/easydiffraction/report/templates/tex/revtex.tex.j2` (new).
- `src/easydiffraction/report/templates/tex/styles/` (new —
  12 vendored class/style files per ADR §3.2.1).
- `src/easydiffraction/report/tex_renderer.py` (new).
- `src/easydiffraction/report/pdf_compiler.py` (new — subprocess
  wrapper over the TeX engine).

**Library-side new properties (P1.21):**
- `src/easydiffraction/datablocks/structure/categories/space_group/default.py`
  (add `crystal_system` property derived from
  `_space_group.name_H-M_alt`).
- `src/easydiffraction/datablocks/experiment/item/base.py` (or
  equivalent — add `measured_range` property).

**CLI (P1.22):**
- `src/easydiffraction/cli/save.py` (existing — match
  `project.save()` no-arg behaviour reading config).
- `src/easydiffraction/cli/save_report.py` (new — `ed save-report
  --cif --html --tex --pdf --style iucr` subcommand).

**Tutorials / docs (P1.23):**
- `docs/docs/tutorials/*.py` (audit for `project.report` usage;
  add `project.report.formats` examples to ed-3, ed-5, ed-8,
  ed-14 — confirm list during P1.23; regenerate notebooks).
- `docs/docs/user-guide/analysis-workflow/report.md` (existing
  — extend with the configuration-category section).
- `docs/docs/api-reference/report.md` (existing — extend with
  the new save methods, enums, configuration fields).

**ADR promotion (P1.24):**
- `docs/dev/adrs/suggestions/project-summary-rendering.md` →
  moved to `docs/dev/adrs/accepted/`.
- `docs/dev/adrs/index.md` (row updated to `accepted/`).

## Commit discipline

When an AI agent follows this plan, **every completed Phase 1
implementation step must be staged with explicit paths and
committed locally before moving to the next implementation step
or the Phase 1 review gate.** Follow the rules in
[`AGENTS.md`](../../../AGENTS.md) → **Commits**. Keep commits
atomic, single-purpose, and aligned with the plan steps. Do not
include generated artifacts (data CIFs, project directories,
benchmark CSVs) unless the step explicitly produces them — see
**Workflow** in [`AGENTS.md`](../../../AGENTS.md) for the
generated-artifact exceptions.

## Implementation steps (Phase 1)

- [x] **P1.1 — Add `ReportFormatEnum` and `ReportStyleEnum`**
  - Files: new `src/easydiffraction/report/enums.py`.
  - Define `ReportFormatEnum(str, Enum)` with members `CIF`,
    `HTML`, `TEX`, `PDF` (string values `'cif'`, `'html'`,
    `'tex'`, `'pdf'`).
  - Define `ReportStyleEnum(str, Enum)` with members `IUCR`,
    `REVTEX` (string values `'iucr'`, `'revtex'`).
  - Re-export from `src/easydiffraction/report/__init__.py`.
  - Commit: `Add ReportFormatEnum and ReportStyleEnum`.

- [x] **P1.2 — Refactor `Report` into a `CategoryItem` and register it on `ProjectConfig`**
  - Files: existing `src/easydiffraction/report/report.py`;
    new `src/easydiffraction/project/categories/report/`
    package (`__init__.py`, `default.py`, `factory.py`); modify
    `src/easydiffraction/project/project_config.py`.
  - Refactor the current plain-facade `Report` class into a
    `CategoryItem` subclass living at
    `src/easydiffraction/project/categories/report/default.py`
    (matching the layout of `chart/`, `table/`,
    `verbosity/`). The class keeps **every existing rendering
    method** (`show_report`, `show_project_info`,
    `show_crystallographic_data`, `show_experimental_data`,
    `show_fitting_details`, `help`) — this is the explicit
    "facade-hybrid" amendment to
    `project-facade-and-persistence.md` already documented in
    the ADR. Static helper methods (`_fmt_row` etc.) move
    with it.
  - Add six descriptor fields to the new `Report`
    (`CategoryItem`): `cif` (`BoolDescriptor`), `html`
    (`BoolDescriptor`), `tex` (`BoolDescriptor`), `pdf`
    (`BoolDescriptor`), `style` (`StringDescriptor` typed
    against `ReportStyleEnum`), `html_offline`
    (`BoolDescriptor`). Each gets
    `CifHandler(names=['_report.<field>'])`.
  - Add a `formats` Python `@property` (getter returns
    `list[ReportFormatEnum]` derived from the four booleans;
    setter accepts a list/iterable of `ReportFormatEnum`
    members or strings and updates the four booleans). This is
    a pure-Python property — it has no CIF handler, no
    descriptor — so the existing `as_cif` walker on
    `CategoryItem` ignores it automatically.
  - Add a `ReportFactory` per the `@Factory.register` contract.
  - Register `Report` on `ProjectConfig` alongside `info`,
    `chart`, `table`, `verbosity`: add `self._report =
    ReportFactory.create(ReportFactory.default_tag())` in
    `ProjectConfig.__init__` and a `report` property.
  - Update `Project.__init__` to read `self._report =
    self._config.report` (replacing the current
    `self._report = Report(self)`); the `Project.report`
    property is unchanged.
  - **Wire the parent back-reference explicitly.** The current
    `CategoryOwner` does not auto-assign `_parent`; the
    project's `_attach_category_parents()` is the central
    wiring point and currently handles `structures`,
    `experiments`, `analysis`, `chart`, `table`. Add
    `self._report._parent = self` to that method so the moved
    rendering methods can still reach the project via
    `self._parent`.
  - **Add a `project` property on `Report`** that returns
    `self._parent`. Every method that currently dereferences
    `self.project` (across the show_*, as_*, save_* surface)
    keeps working unchanged because `self.project` now resolves
    to the same project object, just via the parent
    back-reference instead of a constructor argument. No
    method body needs to change; only the `self.project`
    attribute initialisation in `Report.__init__` goes away
    (it becomes the property).
  - **Write side is automatic** — `category_owner_to_cif`
    (`src/easydiffraction/io/cif/serialize.py:566-575`) walks
    `ProjectConfig` and emits every registered `CategoryItem`,
    so the six `_report.*` items appear under `data_<project>`
    next to `_info.*`, `_chart.*`, `_table.*`, `_verbosity.*`
    automatically once `Report` is a `CategoryItem`.
  - **Read side is NOT automatic** — `project_config_from_cif`
    (`src/easydiffraction/io/cif/serialize.py:675-689`)
    manually calls `chart.from_cif(block)`,
    `table.from_cif(block)`, `verbosity.from_cif(block)` and
    must be extended to call `report.from_cif(block)` too. P1.3
    owns that extension (see next step).
  - Commit: `Refactor Report into a ProjectConfig CategoryItem`.

- [x] **P1.3 — Wire `_report.*` into the `project.cif` loader (with legacy defaults)**
  - File:
    `src/easydiffraction/io/cif/serialize.py` (the existing
    `project_config_from_cif()` function at
    lines 675-689).
  - Add a `report = getattr(project, 'report', None); if
    report is not None: report.from_cif(block)` block, matching
    the existing pattern used for `chart`, `table`, and
    `verbosity`.
  - The `Report.from_cif(block)` implementation inherits from
    the `CategoryItem` base class — no new override needed —
    and it must treat **missing `_report.*` items as
    not-present rather than as an error**. The base class
    behaviour is already to leave descriptors at their
    declared defaults when the matching CIF item is absent,
    which gives us the documented defaults
    (`cif=html=tex=pdf=False`, `style='iucr'`,
    `html_offline=False`) on legacy `project.cif` files
    automatically. Add a one-line docstring comment to the
    new loader block summarising the missing-items → defaults
    rule so a future reader doesn't tighten it into a strict
    check.
  - This step also formally verifies the round-trip claim
    in P1.2: write side from `category_owner_to_cif` emits
    `_report.*`; read side from `project_config_from_cif`
    (after this step) restores it.
  - Commit:
    `Load _report.* from project.cif with legacy defaults`.

- [x] **P1.4 — Move gemmi validation internal (CIF only)**
  - Files: `src/easydiffraction/io/cif/iucr_writer.py`,
    `src/easydiffraction/report/check.py` (or move/rename).
  - Refactor the existing `Report.check()` body into a private
    pre-write helper (e.g. `_validate_iucr_cif(content)`)
    invoked from inside the CIF emission path.
  - On gemmi failure, raise
    `EasyDiffractionWriterError(<gemmi diagnostic>)` —
    a new exception in `src/easydiffraction/core/errors.py`
    (or wherever project exceptions live) — instead of writing
    a broken file.
  - The validation function is **only** wired into the CIF
    write paths (`save_cif()`, the `cif` branch under
    `project.save()`). HTML/TeX/PDF paths do not call it.
  - Cache the parsed dictionaries at module import so the cost
    is paid once per session.
  - Commit: `Move IUCr CIF validation inside the writer`.

- [x] **P1.5 — Remove public `check()` and `check=True`**
  - Files: `src/easydiffraction/project/categories/report/default.py`
    (the moved `Report` class — same target for P1.6, P1.7,
    P1.20),
    `src/easydiffraction/project/project.py`,
    `src/easydiffraction/cli/` (any commands exposing
    `--check`).
  - Delete `Report.check()` method.
  - Drop the `check=False` keyword from `Project.save()`.
  - Update any docstrings / tutorials that reference the
    removed surface (P1.23 will sweep tutorials).
  - Commit: `Remove public Report.check() and check=True flag`.

- [x] **P1.6 — Per-format `save_*()` methods + `Report.save()`**
  - Files: `src/easydiffraction/project/categories/report/default.py`,
    `src/easydiffraction/project/project.py`.
  - Add `save_cif()`, `save_html(offline=False)`,
    `save_tex(style='iucr')`, `save_pdf(style='iucr')` to
    `Report`. `save_cif()` invokes the existing alignment-ADR
    IUCr writer; the other three are stubs that raise
    `NotImplementedError('lands in P1.17 / P1.19 / P1.20')`
    so the wiring is testable now without all renderers in
    place.
  - Add `Report.save()`: reads `self.formats`, dispatches to
    the matching `save_*()` per enabled format; raises
    `ValueError(...)` when `formats` is empty (matching CLI's
    no-flag behaviour).
  - Rewire `Project.save()`: drop the `report=True` kwarg;
    after the regular project files are written, call
    `Report._save_configured()` (a private "no-arg, no-error
    on empty" sibling of `save()`) that emits each enabled
    format, returning quietly when none are configured.
  - Commit: `Add per-format save methods and Report.save dispatch`.

- [x] **P1.7 — Empty-config behaviour tests-of-intent**
  - Files: `src/easydiffraction/project/categories/report/default.py`
    (assertion docstrings / runtime checks).
  - Add the explicit `ValueError` message from §1.2 of the
    ADR to `Report.save()` so future readers see the same
    text the CLI prints.
  - Verify (no test commits in P1 — actual tests land in P2)
    that:
    - `project.save()` with no formats writes only project
      files.
    - `project.report.save()` with no formats raises.
    - `project.report.save_cif()` always writes regardless of
      config.
  - This step is largely contract-locking — the behaviour was
    introduced in P1.6, this step makes the contract visible
    in code via the docstrings and the error message.
  - Commit: `Lock empty-config behaviour in Report API`.

- [x] **P1.8 — Add `analysis.software` category + URL constants**
  - Files: new
    `src/easydiffraction/analysis/categories/software/`
    package (`__init__.py`, `base.py`, `default.py`,
    `factory.py`); modify backend classes for `url`.
  - Define the `Software` category with three sibling
    sub-categories: `framework`, `calculator`, `minimizer`.
    Each carries `name` (string), `version` (string), `url`
    (string). The top-level category also carries
    `timestamp` (ISO-8601 datetime string, nullable).
  - Add `url: str` class-level constants to existing
    calculator backend classes (`CryspyCalculator`,
    `CrysfmlCalculator`, `PdffitCalculator`) and minimizer
    classes (`LmfitMinimizer`, `EmceeMinimizer`, …) per the
    ADR §4 list.
  - No fit-time population yet (that's P1.9).
  - Commit:
    `Add analysis.software category and engine URL constants`.

- [x] **P1.9 — Populate `analysis.software` at fit time + `fit_datetime` emission**
  - Files:
    `src/easydiffraction/analysis/analysis.py`,
    `src/easydiffraction/io/cif/iucr_writer.py`.
  - In `Analysis.fit()`, immediately before successful return,
    populate `analysis.software.*` from the active calculator
    / minimizer instances (read `name` from `type_info`,
    `version` from the upstream library's `__version__`, `url`
    from the class constant). Set `timestamp` to the current
    UTC ISO-8601 string.
  - Update the IUCr writer's `data_global` block builder to
    read the `_easydiffraction_software.{framework, calculator,
    minimizer}` triple **from** `analysis.software` (currently
    constructed inline per the alignment ADR's §2.3a-i —
    replace that inline construction).
  - Add `_easydiffraction_software.fit_datetime` emission in
    `data_global` when `analysis.software.timestamp` is set;
    omit entirely when unset (per the missing-provenance
    behaviour in §4.1).
  - Update `_computing.structure_refinement` derivation to
    fall back to `"EasyDiffraction <version>"` (framework
    only) when calculator / minimizer details are unset.
  - Commit: `Populate analysis.software at fit time and emit fit_datetime`.

- [x] **P1.10 — Amend `analysis-cif-fit-state.md` ADR**
  - File: `docs/dev/adrs/accepted/analysis-cif-fit-state.md`.
  - Document the new `analysis.software` persisted category
    (framework / calculator / minimizer triples + timestamp).
  - Commit: `Amend analysis-cif-fit-state for analysis.software`.

- [x] **P1.11 — Amend `iucr-cif-tag-alignment.md` ADR**
  - File: `docs/dev/adrs/accepted/iucr-cif-tag-alignment.md`.
  - Five amendments per the ADR's amended-list entry:
    (1) `project.save(report=True)` flag removal;
    (2) `Report.save()` surface redesign (per-format methods +
    no-arg convenience + `ValueError` on empty);
    (3) `_easydiffraction_software.*` triple read from
    `analysis.software`;
    (4) `_easydiffraction_software.fit_datetime` extension tag
    added to `data_global`;
    (5) public `check()` + `check=True` removed; gemmi pass
    moves internal (CIF emission paths only).
  - Update the Current State table row for software
    identification accordingly.
  - Commit: `Amend iucr-cif-tag-alignment for project.report`.

- [x] **P1.12 — Add `project.publication` top-level owner**
  - Files: new
    `src/easydiffraction/project/categories/publication/`
    package; modify `src/easydiffraction/project/project.py`.
  - Define `Publication` as a `CategoryOwner` exposing six
    sibling sub-categories per the ADR §5.1 table:
    `journal`, `journal_date`, `journal_coeditor`,
    `contact_author`, `body`, `authors` (loop).
  - Each sub-category carries the items enumerated in §5.1
    (e.g. `journal.name_full`, `journal.paper_doi`,
    `contact_author.name`, `contact_author.id_orcid`,
    `contact_author.id_iucr`, …) with
    `CifHandler(names=['_<cat>.<field>'])` carrying the
    **dictionary casing** for the CIF tag side
    (`_journal.paper_DOI`, `_publ_contact_author.id_ORCID`,
    `_publ_contact_author.id_IUCr`, etc.) while **Python
    attributes stay lowercase snake_case** per the ADR §5.1
    contract. The Python ↔ CIF casing split is the same shape
    PR #184 already locked in for the structure tier
    (`atom_site.adp_type` Python attr ↔ `_atom_site.ADP_type`
    CIF tag).
  - `Project` gains a `publication` read-only facade property
    returning the `Publication` instance.
  - No CIF write wiring yet (that's P1.13).
  - Commit: `Add project.publication facade and sub-categories`.

- [ ] **P1.13 — Persist `project.publication.*` to `project.cif`**
  - Files: `src/easydiffraction/project/project.py` (and the
    project-CIF serializer).
  - Extend the project-CIF write path to include the
    `_publ_*` / `_journal_*` items after `_report.*`. Unset
    fields write as `?` (the existing CIF unset-value
    convention).
  - Extend the read path to populate `project.publication.*`
    from any `_publ_*` / `_journal_*` items found in
    `project.cif`. Missing items leave the descriptors at
    `None`.
  - Commit: `Persist project.publication to project.cif`.

- [ ] **P1.14 — TOML/JSON loader for publication metadata**
  - File: new
    `src/easydiffraction/project/publication_loader.py`.
  - Implement `Publication.load(path: str | Path)`:
    - Extension dispatch: `.toml` → `tomllib` (stdlib 3.11+),
      `.json` → `json` (stdlib).
    - Unknown extension → `ValueError("Unsupported publication-info
      format: <ext>. Use .toml or .json.")`.
    - Map flat keys (`journal_name_full`,
      `contact_author_name`, …) to the matching
      sub-category fields; unknown keys raise
      `ValueError(<key>)`.
  - Commit: `Add Publication.load TOML/JSON entry point`.

- [ ] **P1.15 — Wire IUCr writer to read from `project.publication.*` + amend ADRs**
  - Files: `src/easydiffraction/io/cif/iucr_writer.py`,
    `docs/dev/adrs/accepted/project-facade-and-persistence.md`,
    `docs/dev/adrs/suggestions/python-cif-category-correspondence.md`.
  - Update the IUCr writer's `data_global` content (§2.3a of
    the alignment ADR) to read `_publ_*` / `_journal_*` values
    from `project.publication.*` instead of emitting static
    `?` placeholders. Unset fields still emit `?`; set fields
    emit the user's value.
  - Amend `project-facade-and-persistence.md`: add
    `project.publication` to the facade enumeration; add
    `project.report` as a hybrid (config + actions); extend
    the project-level singleton-category list with
    `_report.*` and the `_publ_*` / `_journal_*` family.
  - Amend `python-cif-category-correspondence.md`: add two
    rows to the correspondence table for
    `project.report.* ↔ _report.*` and
    `project.publication.* ↔ _publ_* / _journal_*`.
  - Commit:
    `Read publication metadata from project.publication in IUCr writer`.

- [ ] **P1.16 — `ReportDataContext` builder + Jinja base templates**
  - Files: new `src/easydiffraction/report/data_context.py`;
    new `src/easydiffraction/report/templates/base.j2`.
  - `data_context()` builds the dict per §6 of the ADR
    (project metadata, structures iterable, experiments
    iterable, fit results, software triple, publication
    metadata, save timestamp, EasyDiffraction version).
  - `base.j2` defines shared macros (parameter row, uncertainty
    formatting) for the HTML and TeX renderers.
  - No HTML/TeX renderer yet; this step is the shared
    foundation.
  - Commit: `Add ReportDataContext builder and Jinja base macros`.

- [ ] **P1.17 — HTML renderer + `save_html(offline=False)`**
  - Files: new
    `src/easydiffraction/report/html_renderer.py`;
    new `src/easydiffraction/report/templates/html/report.html.j2`;
    new `src/easydiffraction/report/templates/html/style.css`.
  - Implement `Report.as_html(offline=False)`: reads
    `data_context()`, renders the Jinja HTML template, embeds
    Plotly figures via `fig.to_html(include_plotlyjs=<cdn|True>)`
    per the `offline` argument.
  - Replace the `NotImplementedError` stub in `Report.save_html()`
    with the real call (writes
    `reports/<project>.html`).
  - No new dependencies — `plotly`, `jinja2`, `pandas` are
    already declared.
  - Commit: `Add HTML renderer with CDN and offline Plotly modes`.

- [ ] **P1.18 — Vendor LaTeX styles + add `kaleido` / `chromium` / `tectonic` deps**
  - Files: `pyproject.toml`, `pixi.toml`, `pixi.lock`; new
    `src/easydiffraction/report/templates/tex/styles/` (12
    files: `iucrjournals.cls`, `harvard.sty`, `revtex4-2.cls`,
    `ltxgrid.sty`, `ltxutil.sty`, `ltxfront.sty`,
    `ltxdocext.sty`, `revsymb4-2.sty`, `aps4-2.rtx`,
    `aps10pt4-2.rtx`, `aps11pt4-2.rtx`, `aps12pt4-2.rtx`);
    new `src/easydiffraction/report/templates/tex/styles/LICENSES.md`
    (vendored-license attributions); new
    `THIRD_PARTY_LICENSES.md` at repository root.
  - Add `kaleido` (v1.0+) to the runtime dependency list in
    `pyproject.toml`.
  - Add `chromium` and `tectonic` to the dev/docs feature
    group in `pixi.toml`.
  - Regenerate `pixi.lock`.
  - Copy the 12 upstream style files into the vendored
    directory.
  - **Concrete licence destinations** (root `LICENSE` is
    deliberately **not** edited — keep that file scoped to the
    wheel's BSD-3-Clause text only):
    - `src/easydiffraction/report/templates/tex/styles/LICENSES.md` —
      ships with the wheel. Contains the full CC0 1.0 text for
      the IUCr files (`iucrjournals.cls`, `harvard.sty`), the
      full LPPL 1.3c text for the REVTeX files (`revtex4-2.cls`,
      `ltx{grid,util,front,docext}.sty`, `revsymb4-2.sty`,
      `aps{4-2,10pt4-2,11pt4-2,12pt4-2}.rtx`), per-file
      attribution (upstream URL, version, original author /
      project), and a header pointing readers back at
      `THIRD_PARTY_LICENSES.md` at the repo root.
    - `THIRD_PARTY_LICENSES.md` at repo root — short index
      listing every vendored third-party asset and pointing
      at the in-package `LICENSES.md` for the full texts. The
      file is created in this PR; future vendored content
      extends the same index.
  - **Verify wheel packaging under hatchling.** The project
    uses hatchling (`[build-system] build-backend =
    'hatchling.build'`); `[tool.hatch.build.targets.wheel]`
    currently lists `packages = ['src/easydiffraction']` with
    no explicit include/exclude rules. By hatchling's default
    behaviour, every non-pyc file inside the listed package
    ships with the wheel — so `.cls`, `.sty`, `.rtx`, and
    `.md` files at
    `src/easydiffraction/report/templates/tex/styles/` should
    be picked up automatically. **Verify with the existing
    project task**: after vendoring the files, run
    `pixi run dist-build` (defined at
    [`pixi.toml:284-285`](../../../pixi.toml) as
    `python -m build --wheel --outdir dist`) and inspect the
    resulting wheel with
    `unzip -l dist/*.whl | grep styles/` to confirm the 12
    style files and `LICENSES.md` are inside. `dist/*.whl`
    is a local verification artefact — **do not stage it**;
    it is not part of the PR's source diff. If the style
    files are missing from the wheel, extend
    `[tool.hatch.build.targets.wheel]` with a
    `force-include = { "src/easydiffraction/report/templates"
    = "easydiffraction/report/templates" }` (or equivalent
    `include` rule) and re-run `pixi run dist-build` to
    re-verify. Do **not** add
    `[tool.setuptools.package-data]` — this project does not
    use setuptools.
  - Commit: `Vendor LaTeX styles with licenses and add kaleido/chromium/tectonic deps`.

- [ ] **P1.19 — LaTeX renderer + `save_tex(style='iucr')`**
  - Files: new
    `src/easydiffraction/report/tex_renderer.py`;
    new `src/easydiffraction/report/templates/tex/iucr.tex.j2`;
    new `src/easydiffraction/report/templates/tex/revtex.tex.j2`.
  - `Report.as_tex(style='iucr')` reads `data_context()`,
    renders the matching Jinja TeX template (driven by the
    `ReportStyleEnum` value), emits a `<project>.tex` that
    `\input{}`'s table partials and `\includegraphics{}`'s
    figures.
  - `Report.save_tex(style='iucr')` writes the rendered TeX
    plus its assets to `reports/tex/`: the main document, a
    `figures/` directory with vector-PDF fits via `kaleido`,
    and a `styles/` directory copied from the vendored
    bundle (P1.18).
  - Replace the `NotImplementedError` stub in
    `Report.save_tex()` with the real call.
  - Commit: `Add LaTeX renderer and save_tex with vendored styles`.

- [ ] **P1.20 — PDF compilation + `save_pdf(style='iucr')`**
  - Files: new
    `src/easydiffraction/report/pdf_compiler.py`;
    modify
    `src/easydiffraction/project/categories/report/default.py`.
  - Implement engine discovery: try `tectonic` first, then
    `latexmk`, then `pdflatex` (per the ADR's order).
  - `Report.save_pdf(style='iucr')` writes the TeX bundle
    (calls `save_tex()` as a side-effect, per the ADR's
    "PDF implies TeX" rule), compiles to PDF via subprocess
    against the first available engine, writes
    `reports/<project>.pdf`.
  - If no engine is found: still write the TeX bundle,
    print the §3.4 install hint (`pixi add tectonic` etc.),
    return without raising — matches the ADR's
    "opportunistic" semantics.
  - Replace the `NotImplementedError` stub in
    `Report.save_pdf()` with the real call.
  - Commit: `Add opportunistic PDF compilation via TeX subprocess`.

- [ ] **P1.21 — Add `crystal_system` and `measured_range` properties**
  - Files:
    `src/easydiffraction/datablocks/structure/categories/space_group/default.py`,
    `src/easydiffraction/datablocks/experiment/item/base.py`.
  - Add a `crystal_system` property to `SpaceGroup` derived
    from `name_H-M_alt` (mapping table maintained in the
    descriptor).
  - Add a `measured_range` property to the experiment base
    class returning `(min, max, inc)` derived from the
    underlying x-axis array (a single axis: `2theta_scan` for
    CWL, `time_of_flight` for TOF — never both at once).
    Boundary cases — **explicit contract** so renderers don't
    need defensive checks:
    - **Empty data** (no points loaded yet) → returns `None`
      (not a tuple). Renderers display `"(no data)"`.
    - **Single point** → `(value, value, None)`. `inc` is
      `None` to signal "no spacing".
    - **Nonuniform spacing** (max−min step deviates from the
      median step by more than 1% of the median) →
      `(min, max, None)`. `inc` is `None`; the renderers may
      still show `min` / `max`.
    - **Uniform spacing** → `(min, max, inc)` where `inc` is
      the median step (a single representative value).
    - **Units** match the experiment's x-axis units (`'deg'`
      for `2theta_scan`, `'us'` for `time_of_flight`).
      Returned as bare floats; the renderer prepends units via
      `data_context()`.
  - Both properties are read-only computed properties — no
    CIF representation, no validation hooks. They exist
    purely to feed the renderers via `data_context()`.
  - Commit: `Add crystal_system and measured_range properties for reports`.

- [ ] **P1.22 — CLI `ed save-report` subcommand**
  - Files: new `src/easydiffraction/cli/save_report.py`;
    modify `src/easydiffraction/cli/save.py`.
  - Add an `ed save-report` subcommand accepting `--cif`,
    `--html`, `--tex`, `--pdf`, `--style iucr`,
    `--offline` flags. Dispatches to
    `project.report.save_*()` methods per flag.
  - `ed save-report` with no flags → clear error pointing at
    the configuration category (matches the Python
    `ValueError` from P1.6).
  - `ed save` continues to read the persisted config; no flag
    surface added on `ed save`.
  - Commit: `Add ed save-report CLI subcommand`.

- [ ] **P1.23 — Update tutorials and user-guide docs**
  - Files: `docs/docs/tutorials/*.py`,
    `docs/docs/tutorials/*.ipynb` (regenerated artefacts —
    explicitly staged because `pixi run notebook-prepare`
    emits them and they must travel with the `.py` edits),
    `docs/docs/user-guide/analysis-workflow/report.md`,
    `docs/docs/api-reference/report.md`.
  - Audit tutorial sources for `project.report.save()` /
    `project.report.check()` / `project.save(report=True)`
    references; rewrite to use the configuration category
    or per-format methods per the new contract.
  - Add at least one tutorial demonstrating
    `project.report.formats = ['html']` + `project.save()`
    end-to-end with the resulting `reports/<project>.html`.
  - Extend the user-guide report page with the configuration
    table (§1.1) and the worked examples (§3.1).
  - Extend the API-reference report page with the new
    `Report` class surface (six fields, per-format
    `save_*()` methods, enums).
  - Regenerate notebooks via `pixi run notebook-prepare`.
  - Commit:
    `Update tutorials and user-guide docs for project.report`.

- [ ] **P1.24 — Promote ADR to `accepted/`**
  - Files: move
    `docs/dev/adrs/suggestions/project-summary-rendering.md`
    to `docs/dev/adrs/accepted/`; update
    `docs/dev/adrs/index.md`.
  - Flip the ADR's `**Status:**` line from `Proposed` to
    `Accepted`; update the date to today (Phase 1 acceptance
    date).
  - Index row: status `Suggestion` → `Accepted`; link target
    changes from `suggestions/` to `accepted/`.
  - Commit:
    `Promote project-summary-rendering ADR to accepted`.

- [ ] **P1.25 — Reach Phase 1 review gate**
  - No-code step. Mark every `[ ]` above as `[x]`; commit the
    plan-file update alone.
  - Commit: `Reach Phase 1 review gate`.

## Test plan (Phase 2)

Per AGENTS.md §Testing, every new module, class, and bug fix
ships with tests; unit tests mirror the source tree. Before
running the verification commands below, add or update:

- [ ] **`tests/unit/easydiffraction/report/test_enums.py`** —
  `ReportFormatEnum` and `ReportStyleEnum` are `(str, Enum)`
  per the closed-values ADR; membership tests; round-trip via
  string values. P1.1 surface.
- [ ] **`tests/unit/easydiffraction/project/categories/report/test_default.py`**
  (extend) — six descriptor fields read/write; `formats`
  property view round-trip (list/iterable → booleans →
  list); per-format `save_*()` methods called with no
  config; `Report.save()` `ValueError` on empty config;
  `Report.save()` dispatches to the right `save_*()` per
  enabled format. P1.2–P1.7 surface.
- [ ] **`tests/unit/easydiffraction/project/test_project.py`**
  (extend) — `project.report.*` round-trip through
  `project.cif`; `Project.save()` honours the config when set;
  `Project.save()` writes no reports when config is empty;
  `report=True` and `check=True` removed (calling with them
  raises `TypeError`). P1.3, P1.5, P1.6 surface.
- [ ] **`tests/unit/easydiffraction/io/cif/test_iucr_writer.py`**
  (extend) — internal gemmi validation runs on CIF emission;
  malformed-tag injection triggers `EasyDiffractionWriterError`;
  HTML/TeX/PDF paths do not invoke gemmi. P1.4 surface.
- [ ] **`tests/unit/easydiffraction/analysis/categories/software/test_software.py`**
  (new) — `Software` category shape; `framework`/
  `calculator`/`minimizer` sub-categories carry name + version +
  url; `timestamp` ISO-8601 round-trip via `analysis.cif`. P1.8
  surface.
- [ ] **`tests/unit/easydiffraction/analysis/test_analysis.py`**
  (extend) — `Analysis.fit()` populates `analysis.software` on
  success; missing provenance renders `"(not available)"` /
  `?` placeholders; `_easydiffraction_software.fit_datetime`
  appears in the IUCr export only when timestamp is set. P1.9
  surface.
- [ ] **`tests/unit/easydiffraction/project/categories/publication/test_publication.py`**
  (new) — `Publication` exposes six sibling sub-categories;
  each item carries the right `_publ_*` / `_journal_*` CIF
  tag with dictionary casing; loop semantics for
  `publication.authors`. P1.12 surface.
- [ ] **`tests/unit/easydiffraction/project/categories/publication/test_publication_loader.py`**
  (new) — `Publication.load()` accepts TOML and JSON;
  unknown extension raises; unknown key raises with the key
  name; flat-key → sub-category mapping is exhaustive. P1.14
  surface.
- [ ] **`tests/unit/easydiffraction/io/cif/test_iucr_writer.py`**
  (further extend) — `_publ_*` / `_journal_*` items in
  `data_global` read from `project.publication.*` instead of
  static placeholders; unset fields still emit `?`. P1.15
  surface.
- [ ] **`tests/unit/easydiffraction/report/test_data_context.py`**
  (new) — `data_context()` returns the expected dict shape
  per ADR §6; missing software / missing publication /
  pre-fit project state degrade gracefully. P1.16 surface.
- [ ] **`tests/unit/easydiffraction/report/test_html_renderer.py`**
  (new) — golden-string snapshots for the rendered HTML
  against a small fixture project; Plotly CDN vs offline
  mode markers in the output. P1.17 surface.
- [ ] **`tests/unit/easydiffraction/report/test_tex_renderer.py`**
  (new) — golden-string snapshots for the rendered TeX with
  `style='iucr'` and `style='revtex'`; ensures both Jinja
  templates compile to syntactically valid LaTeX (lexer-only
  check, no engine compile).
- [ ] **`tests/unit/easydiffraction/report/test_pdf_compiler.py`**
  (new) — engine discovery order respected; missing-engine
  branch writes TeX and returns silently with the install
  hint; engine non-zero exit raises a clear error.
- [ ] **`tests/unit/easydiffraction/datablocks/structure/categories/space_group/test_default.py`**
  (extend) — `crystal_system` derived correctly from a set of
  representative H-M symbols. P1.21 surface.
- [ ] **`tests/unit/easydiffraction/datablocks/experiment/item/test_base.py`**
  (extend) — `measured_range` boundary cases per P1.21's
  contract: empty data → `None`; single point → `(v, v,
  None)`; nonuniform spacing (>1% deviation from median) →
  `(min, max, None)`; uniform spacing → `(min, max, inc)`
  with `inc` as the median step. Covers both CWL
  (`2theta_scan`, `'deg'`) and TOF (`time_of_flight`,
  `'us'`) x-axes. P1.21 surface.
- [ ] **`tests/unit/easydiffraction/cli/test_save_report.py`**
  (new) — `ed save-report` dispatches to the matching
  `save_*()` methods; `ed save-report` with no flags exits
  with the expected error. P1.22 surface.
- [ ] **Integration / script-test coverage** — verify
  `pixi run script-tests` exercises at least one tutorial
  that sets `project.report.formats` and the resulting
  `reports/<project>.html` is non-empty and gemmi-validates.
  Extend a tutorial if not.

Use `pixi run test-structure-check` to confirm the unit-test
layout mirrors the source tree per AGENTS.md §Testing.

## Verification commands (Phase 2)

Per AGENTS.md §Workflow, save any required check output with the
zsh-safe pattern. Variable names per-task:

```sh
pixi run fix > /tmp/easydiffraction-fix.log 2>&1; fix_exit_code=$?; tail -n 200 /tmp/easydiffraction-fix.log; exit $fix_exit_code
pixi run check > /tmp/easydiffraction-check.log 2>&1; check_exit_code=$?; tail -n 200 /tmp/easydiffraction-check.log; exit $check_exit_code
pixi run test-structure-check > /tmp/easydiffraction-test-structure-check.log 2>&1; test_structure_check_exit_code=$?; tail -n 200 /tmp/easydiffraction-test-structure-check.log; exit $test_structure_check_exit_code
pixi run unit-tests > /tmp/easydiffraction-unit-tests.log 2>&1; unit_tests_exit_code=$?; tail -n 200 /tmp/easydiffraction-unit-tests.log; exit $unit_tests_exit_code
pixi run integration-tests > /tmp/easydiffraction-integration-tests.log 2>&1; integration_tests_exit_code=$?; tail -n 200 /tmp/easydiffraction-integration-tests.log; exit $integration_tests_exit_code
pixi run script-tests > /tmp/easydiffraction-script-tests.log 2>&1; script_tests_exit_code=$?; tail -n 200 /tmp/easydiffraction-script-tests.log; exit $script_tests_exit_code
```

Run in order; each must complete clean before the next. Per
AGENTS.md §Workflow: `pixi run fix` regenerates
`docs/dev/package-structure/full.md` and `short.md`
automatically. The new vendored LaTeX style files under
`src/easydiffraction/report/templates/tex/styles/` are
intentional sources — included in commits. Benchmark CSVs
under `docs/dev/benchmarking/` produced by
`pixi run script-tests` are untracked verification artifacts;
do not stage them.

## Suggested Pull Request

**Title:** `[report] Add HTML, TeX, PDF outputs and publication metadata to project.report`

**Description:**

Builds on the IUCr CIF alignment work (PR #184) by filling in
the non-CIF half of the publication bundle. The `project.report`
facade now covers four output formats — CIF, HTML, TeX, PDF —
opt-in via a persisted configuration category on
`project.report` that's written to `project.cif` alongside
the existing project-level preferences (`project.info`,
`project.chart`, `project.table`, `project.verbosity`).

A user configures their report preferences once:

```python
project.report.formats = ['html', 'cif']
project.report.style = 'iucr'
project.report.html_offline = False
```

and every subsequent `project.save()` writes the configured
reports under `reports/`. Per-format ad-hoc methods
(`project.report.save_html()`, `save_cif()`, `save_tex()`,
`save_pdf()`) cover one-offs without changing the persisted
config. The CLI mirrors the split: `ed save` reads the
configuration; `ed save-report --html --tex --pdf --style iucr`
is the one-off subcommand.

LaTeX support ships with vendored IUCr and REVTeX style files
(12 files, ~420 KB) so users can swap journal styles with one
line in `<project>.tex` and recompile. PDF compilation is
opportunistic — works when `tectonic`, `latexmk`, or `pdflatex`
is on `PATH`; otherwise the editable `.tex` and figures are
still written and the user gets an install hint.

The PR also adds two new persisted categories:
**`analysis.software`** (calculator and minimizer name +
version + URL stamped at fit time, ending the long-standing
provenance gap), and **`project.publication`**
(journal/author/contact-author metadata that feeds the
`_publ_*` / `_journal_*` placeholders in journal-submission
CIFs, replaceable by a TOML or JSON file).

The PR amends three accepted ADRs
(`iucr-cif-tag-alignment`, `analysis-cif-fit-state`,
`project-facade-and-persistence`) plus the in-flight proposed
ADR `python-cif-category-correspondence` (which stays in
`suggestions/`; this PR only updates its correspondence table
to include the new `project.report.*` / `project.publication.*`
surfaces, it does not promote it to accepted), and promotes the
`project-summary-rendering` ADR itself from `suggestions/` to
`accepted/`.

**Scope label:** `[report]`. The headline feature is the
`project.report` rendering surface; the `project.publication`
addition and IUCr writer wiring are supporting changes for
the same user-visible deliverable.
