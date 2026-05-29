# Plan: Project Summary Rendering — migration to single-style + pgfplots + DisplayHandler

Implementation plan for the
[`project-summary-rendering`](../adrs/accepted/project-summary-rendering.md)
ADR. Follows [`AGENTS.md`](../../../AGENTS.md) — no deliberate
exceptions to those instructions.

> **Context for this plan.** The branch `project-summary-rendering`
> already carries an end-to-end Phase 1 implementation of an earlier
> version of the same ADR (PR-ready as of commit
> `f354fa435 Reach Phase 1 review gate`). That earlier implementation
> supported two LaTeX styles (`iucr` + `revtex`), used `kaleido` + a
> Chrome bootstrap to render fit-quality figures, and had no
> `DisplayHandler` for descriptor display metadata. The ADR has since
> been substantially rewritten (single `iucrjournals` style only;
> `pgfplots` with external CSV in place of `kaleido`; new
> `DisplayHandler` value object; new ASCII units vocabulary aligned to
> CIF DDLm `_units.code`; MathJax bundled under `html_offline=True`;
> descriptor-driven `fit_data.x` payload in `ReportDataContext`).
>
> This plan is the **migration delta**: the diff between the committed
> implementation and the rewritten ADR. It does **not** re-derive the
> surfaces already shipped (config category, per-format methods,
> `analysis.software`, `project.publication`, and CLI report saving via
> `fit`); those stay as-is except for the later approved removal of the
> standalone `save` / `save-report` commands. Every step below either
> deletes or replaces something the previous implementation introduced,
> or adds a new surface the rewritten ADR requires.

## ADR cross-reference

- **Primary ADR:**
  [`project-summary-rendering.md`](../adrs/accepted/project-summary-rendering.md)
  (Accepted; ADR review cycle closed at review 5 sentinel).
- The ADR's "ADRs amended by this ADR" section is unchanged by this
  migration — the amendments to
  [`iucr-cif-tag-alignment`](../adrs/accepted/iucr-cif-tag-alignment.md),
  [`analysis-cif-fit-state`](../adrs/accepted/analysis-cif-fit-state.md),
  [`project-facade-and-persistence`](../adrs/accepted/project-facade-and-persistence.md),
  and the suggested
  [`python-cif-category-correspondence`](../adrs/suggestions/python-cif-category-correspondence.md)
  were applied in the earlier P1 walk and remain valid.
- No new ADR is required for this migration. The rewritten ADR is the
  authoritative reference.

## Branch and PR

- **Branch:** `project-summary-rendering` (already checked out; carries
  the earlier implementation commits).
- **PR target:** `develop`.
- Do not push the branch until both Phase 1 and Phase 2 review cycles
  close.

## Decisions already made (in the ADR)

These are settled by the accepted, rewritten ADR — this plan does not
re-litigate them:

- **Five-field config, no `style`** (§1.1, §1.3): the `Report`
  `CategoryItem` carries exactly five persisted descriptors — `cif`,
  `html`, `tex`, `pdf`, `html_offline` — written as `_report.*` in
  `project.cif`. No `style` field, no `ReportStyleEnum`, no `--style`
  CLI flag. Multi-style support is deferred to a follow-up ADR (see ADR
  "Deferred Work").
- **Single LaTeX style — `iucrjournals` hardcoded** (§3.2): the LaTeX
  renderer emits one document class (`iucrjournals`). The vendored TeX
  bundle drops from 12 files (previous design) to 2: `iucrjournals.cls`
  and `harvard.sty`, both CC0 1.0 from the IUCr upstream.
- **No `kaleido`, no `chromium`** (§3.3): each fit-quality figure is a
  **standalone `pgfplots` `.tex` document**
  (`reports/tex/data/fit_<expt_id>.tex`, reading its sibling
  `fit_<expt_id>.csv`), compiled independently to `fit_<expt_id>.pdf`
  and pulled into the main report via `\includegraphics` — no inline
  pgfplots in `<project>.tex`, and per-figure compiles isolate the TeX
  memory pool. The fit-quality figure uses the Plotly geometry, colors,
  legend structure, grid colors, and line widths where `pgfplots` can
  support them without exceeding TeX memory. The PDF figure deliberately
  does **not** include the background curve or measured error bars, and
  it keeps every measured point with the small pgfplots marker size from
  the accepted design. The TeX engine (Tectonic / TeX Live / MiKTeX)
  supplies `pgfplots` + `standalone` + TikZ deps from CTAN or its
  default sets.
- **`DisplayHandler` value object** (§1.5): new
  `@dataclass(frozen=True, slots=True)` at
  `src/easydiffraction/core/display_handler.py` carrying four optional
  fields — `display_name`, `display_units`, `latex_name`, `latex_units`.
  Renderers consult it via a per-context fallback chain (LaTeX context →
  `latex_*` fields, HTML context → `display_*` fields, GUI/terminal →
  `display_*` fields), each falling back to the descriptor's plain
  `name` / `units`. **Table-rendering paths MUST read through the
  resolution chain, not the raw `descriptor.units` field**, because
  `units=` now holds ASCII CIF DDLm codes.
- **Units vocabulary aligned to `_units.code`** (§1.5): every `units=`
  string on a descriptor is the ASCII value the CIF DDLm dictionary
  defines verbatim (`angstroms`, `angstrom_squared`, `degrees`,
  `kelvins`, `kilopascals`, `microseconds`, `dalton`, `megagray`,
  `reciprocal_angstroms`, `reciprocal_angstrom_squared`, `none`). The
  single project-internal code in scope is `degrees_squared` (no
  `_units.code` round-trip). A new `units_vocabulary.py` module
  enumerates every valid code for a declaration-time validator. The
  Unicode-symbol form (`Å²`, `°`, `Å`) moves into `display_units`; the
  LaTeX form (`\AA$^2$`, `$\deg$`, `\AA`) into `latex_units`.
- **MathJax bundling under `html_offline`** (§2): `html_offline=True`
  inline-bundles **both** Plotly (~3 MB, `include_plotlyjs=True`) and
  the vendored MathJax `tex-mml-chtml.js` (~1.5 MB, Apache-2.0). When
  `html_offline=False`, both load from CDN. No new Python dependency;
  MathJax is a static JS asset under
  `src/easydiffraction/report/templates/html/vendor/` packaged by
  hatchling.
- **Descriptor-driven `fit_data` shape** (§6): `data_context()`'s
  `experiments[i].fit_data` payload carries an `x` sub-dict (values +
  descriptor `name`, `units`, `display_name`, `latex_name`,
  `display_units`, `latex_units` resolved at builder time) and a
  `series` sub-dict (`meas`, `calc`, `diff`, optional `bkg`, each with
  `values`, optional `su`, `label`). One descriptor path, two renderers
  (Plotly for HTML, pgfplots CSV for TeX), all experiment types — Bragg
  powder `two_theta`, TOF `time_of_flight`, total-scattering `r`, future
  `q`, …
- **CIF persistence unchanged in shape** (§1.3): the existing
  `category_owner_to_cif` walker continues to emit `_report.*`; the
  read-side hook in `project_config_from_cif` continues to restore the
  five fields. Removing `_report.style` from the write surface is the
  only persistence change required.

## Open questions to resolve during implementation

- **`DisplayHandler` attachment point.** The ADR says the handler
  attaches to the descriptor as an optional slot. Confirm during P1
  whether the right surface is the base `Descriptor` class (every
  descriptor type inherits the slot) or the more specific `Parameter` /
  `StringDescriptor` subclasses. Default assumption: base `Descriptor` —
  uniform across all descriptor kinds.
- **MathJax bundle version.** Pick a specific MathJax 3.x release for
  `tex-mml-chtml.js` and pin its source URL in `LICENSES.md` for
  traceability. Assume the latest 3.x release tagged on jsdelivr at
  vendoring time.
- **`reports/tex/data/fit_<expt_id>.csv` schema.** The CSV emitter
  writes one row per data point with columns `x`, `meas`, optional
  `meas_su`, `calc`, `diff`. Background is not emitted to the pgfplots
  CSV because the PDF figure does not plot it. Confirm `figure.tex.j2`'s
  column references match this schema exactly during P1.
- **Style-bundle cleanup vs. wheel size.** The 10 REVTeX files dropped
  from the bundle reduce the wheel by ~350 KB. The Phase 2 verification
  step covers the actual `pixi run dist-build` check
  (`iucrjournals.cls` + `harvard.sty` still ship; MathJax vendored
  bundle included); Phase 1 only edits
  `[tool.hatch.build.targets.wheel]` packaging rules if hatchling's
  defaults don't pick the files up.
- **Tutorial coverage.** The two tutorial files already modified in the
  worktree (`ed-3.py`, `ed-14.py`) reference the old `style=` API; they
  need re-editing or reverting in P1.17 once the new surface is in
  place.

## Concrete files likely to change

**Surface shrink — drop `style` everywhere:**

- `src/easydiffraction/report/enums.py` (existing — delete
  `ReportStyleEnum`; keep only `ReportFormatEnum`).
- `src/easydiffraction/report/__init__.py` (existing — remove
  `ReportStyleEnum` re-export).
- `src/easydiffraction/project/categories/report/default.py` (existing —
  delete the `style` `StringDescriptor`; drop the `style=` parameter
  from `save_tex()`, `save_pdf()`, any `Report.save()` dispatch; update
  docstrings).
- `src/easydiffraction/__main__.py` (existing — remove standalone
  report-export CLI options; report saving is driven by persisted
  `_report.*` flags during `fit`).
- `src/easydiffraction/report/tex_renderer.py` (existing — remove style
  dispatch; emit a single template).
- `src/easydiffraction/io/cif/serialize.py` (existing — no code change
  expected; the walker emits whatever descriptors are declared, so
  removing the `style` descriptor drops the `_report.style` row
  automatically).

**Style-bundle shrink (12 → 2):**

- `src/easydiffraction/report/templates/tex/styles/` — delete:
  `revtex4-2.cls`, `ltxgrid.sty`, `ltxutil.sty`, `ltxfront.sty`,
  `ltxdocext.sty`, `revsymb4-2.sty`, `aps4-2.rtx`, `aps10pt4-2.rtx`,
  `aps11pt4-2.rtx`, `aps12pt4-2.rtx`. Keep: `iucrjournals.cls`,
  `harvard.sty`.
- `src/easydiffraction/report/templates/tex/styles/LICENSES.md`
  (existing — rewrite to cover only the two CC0 1.0 files; remove the
  LPPL 1.3c REVTeX section).
- `THIRD_PARTY_LICENSES.md` (existing at repo root — shrink index to one
  entry).
- `src/easydiffraction/report/templates/tex/iucr.tex.j2` (existing —
  rename to a single canonical template name, e.g. `report.tex.j2`).
- `src/easydiffraction/report/templates/tex/revtex.tex.j2` (existing —
  delete).

**Drop `kaleido`:**

- `pyproject.toml` (existing — remove `kaleido` from the runtime
  dependency list).
- `pixi.lock` (regenerated).
- `src/easydiffraction/report/tex_renderer.py` (existing — remove
  kaleido-based PDF figure emission and `figures/` output; replace with
  pgfplots CSV emission).
- `docs/docs/user-guide/analysis-workflow/report.md` (existing — drop
  the kaleido bootstrap section).

**Add `DisplayHandler`:**

- `src/easydiffraction/core/display_handler.py` (new — frozen dataclass
  with four `str | None` fields).
- `src/easydiffraction/core/__init__.py` (existing — export
  `DisplayHandler` alongside `CifHandler` etc., per AGENTS.md
  `__init__.py` rule).
- `src/easydiffraction/core/descriptor.py` (or `parameter.py` /
  `base_descriptor.py` — whichever owns the descriptor base) (existing —
  add an optional `display_handler: DisplayHandler | None = None` slot;
  define resolution helpers `resolve_display_name(context)` /
  `resolve_display_units(context)` per the ADR's per-context fallback
  chain).

**Units vocabulary sweep:**

- `src/easydiffraction/core/units_vocabulary.py` (new — enumerate every
  valid `units=` code; raise `ValueError` with the offending code on
  validation failure; called from the descriptor base class at
  construction time).
- Every descriptor declaration in `src/easydiffraction/` that currently
  passes a Unicode units string (`'Å²'`, `'°'`, `'Å'`, …) — rewrite to
  use the ASCII DDLm code and attach a `DisplayHandler` with the Unicode
  / LaTeX forms. Concrete file list resolved during P1.7's sweep; expect
  ≥20 sites across `datablocks/structure/`, `datablocks/experiment/`,
  `analysis/categories/`.

**Table-rendering migration:**

- `src/easydiffraction/project/categories/report/default.py` (existing —
  every `show_*()` method that builds a unit column reads through
  `resolve_display_units(...)` instead of `descriptor.units` directly).
- `src/easydiffraction/report/html_renderer.py` (existing — same
  migration for Jinja context inputs).
- `src/easydiffraction/report/tex_renderer.py` (existing — same
  migration for the TeX context).
- `src/easydiffraction/report/data_context.py` (existing — every label /
  unit string baked into the context is resolved per-context here so
  renderers don't re-derive).

**MathJax bundling:**

- `src/easydiffraction/report/templates/html/vendor/mathjax-tex-mml-chtml.js`
  (new — vendored static asset, Apache-2.0).
- `src/easydiffraction/report/templates/html/vendor/LICENSES.md` (new —
  Apache-2.0 text + upstream URL + version).
- `THIRD_PARTY_LICENSES.md` (existing at repo root — extend index with
  MathJax entry alongside the IUCr TeX bundle).
- `src/easydiffraction/report/templates/html/report.html.j2` (existing —
  switch the MathJax `<script>` tag between the relative vendored path
  and the CDN URL per `html_offline`).
- `src/easydiffraction/report/html_renderer.py` (existing — when
  `html_offline=True`, copy the vendored MathJax file next to the
  emitted `<project>.html` so the relative `<script src="vendor/...">`
  resolves; otherwise emit the CDN URL).
- `pyproject.toml` (existing — confirm
  `[tool.hatch.build.targets.wheel.shared-data]` (or the package-data
  equivalent already in place) ships the new `vendor/` subtree).

**`fit_data` shape + pgfplots CSV emitter:**

- `src/easydiffraction/report/data_context.py` (existing — replace the
  previous `figures.fit_per_experiment` payload with the
  descriptor-driven `experiments[i].fit_data` dict per ADR §6).
- `src/easydiffraction/report/tex_renderer.py` (existing — add
  `_write_fit_csv(expt_id, fit_data, out_dir)` writing
  `reports/tex/data/fit_<expt_id>.csv`, and render a standalone
  `data/fit_<expt_id>.tex` per experiment from the new `figure.tex.j2`;
  see §3.3 and P1.16).
- `src/easydiffraction/report/templates/tex/figure.tex.j2` (new —
  `\documentclass{standalone}` pgfplots figure: Plotly-derived geometry,
  colors, line widths, legend structure, Bragg row, residual panel,
  light inner grids, no outside tick marks. Measured points are all
  plotted; background and measured error bars are intentionally omitted
  from the PDF figure. No band. `\pgfplotsset{set layers}` +
  `mark layer=like plot` mandatory; see P1.16 and P1.23).
- `src/easydiffraction/report/templates/tex/report.tex.j2` (renamed from
  `iucr.tex.j2`) — the **main** document: tables +
  `\includegraphics{data/fit_<expt>.pdf}` per experiment. No inline
  pgfplots. Single template, no style branching.
- `src/easydiffraction/report/pdf_compiler.py` (existing — compile each
  `data/fit_<expt>.tex` first, then the main `<project>.tex`, **each
  using the same discovered-engine fallback** `_ENGINE_ORDER` =
  `tectonic` → `latexmk` → `pdflatex` (not tectonic only); per-figure
  separate documents provide the memory isolation; see P1.16).
- `src/easydiffraction/report/html_renderer.py` (existing — the Plotly
  builder now consumes `fit_data` directly rather than expecting
  pre-rendered HTML; serializes through the shared `PlotlyPlotter`
  helper that applies `_get_config()` **and** the legend-toggle
  `post_script` + `_wrap_html_figure` wrapper, with a **report-only**
  `force_template='plotly_white'` override (notebook stays
  theme-adaptive); see ADR §2 and P1.18).
- `src/easydiffraction/report/templates/html/report.html.j2` (existing —
  feed the dict to the Plotly builder at render time).

**Tutorials and docs:**

- `docs/docs/tutorials/ed-3.py`, `docs/docs/tutorials/ed-14.py`
  (existing — already dirty in the worktree from the earlier walk; align
  with the new no-`style` surface, then regenerate notebooks via
  `pixi run notebook-prepare`).
- `docs/docs/tutorials/*.ipynb` (regenerated artefacts matched to the
  edited `.py` sources).
- `docs/docs/user-guide/analysis-workflow/report.md` (existing — remove
  `style=` mentions and the kaleido bootstrap section; add the
  MathJax-offline note).
- `docs/docs/api-reference/report.md` (existing — update the `Report`
  class surface: five fields, no `ReportStyleEnum`, no `--style`).

## Commit discipline

When an AI agent follows this plan, **every completed Phase 1
implementation step must be staged with explicit paths and committed
locally before moving to the next implementation step or the Phase 1
review gate.** Follow the rules in [`AGENTS.md`](../../../AGENTS.md) →
**Commits**. Keep commits atomic, single-purpose, and aligned with the
plan steps. Do not include generated artifacts (data CIFs, project
directories, benchmark CSVs) unless the step explicitly produces them —
see **Workflow** in [`AGENTS.md`](../../../AGENTS.md) for the
generated-artifact exceptions.

## Implementation steps (Phase 1)

- [x] **P1.1 — Remove `ReportStyleEnum` and `style` field**
  - Files: `src/easydiffraction/report/enums.py`,
    `src/easydiffraction/report/__init__.py`,
    `src/easydiffraction/project/categories/report/default.py`.
  - Delete `ReportStyleEnum` and its re-export.
  - Delete the `style` `StringDescriptor` from `Report` (the four-field
    config + `html_offline` remains).
  - Update docstrings to reference the five-field surface; drop any
    "style selector" prose.
  - Commit: `Drop ReportStyleEnum and _report.style field`.

- [x] **P1.2 — Drop `style=` from `save_tex` / `save_pdf` / CLI**
  - Files: `src/easydiffraction/project/categories/report/default.py`,
    `src/easydiffraction/__main__.py`,
    `src/easydiffraction/report/tex_renderer.py`,
    `src/easydiffraction/report/pdf_compiler.py`.
  - Drop the `style='iucr'` kwarg from `save_tex()` and `save_pdf()`
    signatures and from any internal dispatcher / `Report.save()` call
    site.
  - Keep CLI report saving tied to the persisted `_report.*` flags used
    during `fit`; do not add one-off report-export flags.
  - The TeX renderer's template selection collapses to a single template
    (renamed below); remove the `ReportStyleEnum`-driven dispatch.
  - Commit: `Drop style= parameter from save_tex/save_pdf and CLI`.

- [x] **P1.3 — Reduce vendored TeX bundle (12 → 2 files)**
  - Files: delete
    `src/easydiffraction/report/templates/tex/styles/revtex4-2.cls`,
    `ltxgrid.sty`, `ltxutil.sty`, `ltxfront.sty`, `ltxdocext.sty`,
    `revsymb4-2.sty`, `aps4-2.rtx`, `aps10pt4-2.rtx`, `aps11pt4-2.rtx`,
    `aps12pt4-2.rtx` (10 files). Keep `iucrjournals.cls` and
    `harvard.sty`.
  - Rewrite
    `src/easydiffraction/report/templates/tex/styles/LICENSES.md` to
    cover only the two CC0 1.0 files (per-file attribution, upstream
    URL, version). Remove the LPPL 1.3c REVTeX section.
  - Update `THIRD_PARTY_LICENSES.md` at the repo root: shrink the index
    to one entry pointing at the in-package `LICENSES.md`.
  - Commit: `Drop REVTeX style files from vendored TeX bundle`.

- [x] **P1.4 — Rename TeX template to a single canonical name**
  - Files: rename `src/easydiffraction/report/templates/tex/iucr.tex.j2`
    → `report.tex.j2`. Delete
    `src/easydiffraction/report/templates/tex/revtex.tex.j2`.
  - Update `src/easydiffraction/report/tex_renderer.py` to load the
    renamed template by its single path.
  - Commit: `Rename TeX template to single canonical report.tex.j2`.

- [x] **P1.5 — Drop `kaleido` runtime dependency**
  - Files: `pyproject.toml`, `pixi.lock` (regenerated);
    `src/easydiffraction/report/tex_renderer.py`;
    `docs/docs/user-guide/analysis-workflow/report.md`.
  - Remove `kaleido` from the runtime dependency list in
    `pyproject.toml`. Regenerate `pixi.lock`.
  - Strip the kaleido-based PDF figure emission code from the TeX
    renderer (the `figures/` directory creation,
    `fig.write_image(..., engine='kaleido')` calls, and the bootstrap
    warning text).
  - Remove the "Kaleido browser bootstrap" subsection from the
    user-guide report doc.
  - Per AGENTS.md §Architecture, removing a dependency the ADR named is
    pre-approved by the rewritten ADR text (which explicitly says
    kaleido is gone).
  - Commit: `Drop kaleido runtime dependency`.

- [x] **P1.6 — Add `DisplayHandler` dataclass**
  - Files: new `src/easydiffraction/core/display_handler.py`; existing
    `src/easydiffraction/core/__init__.py`.
  - Define `DisplayHandler` exactly per ADR §1.5:
    `@dataclass(frozen=True, slots=True)` with four fields —
    `display_name: str | None = None`,
    `display_units: str | None = None`, `latex_name: str | None = None`,
    `latex_units: str | None = None`. Numpy-style docstring summary ≤72
    chars.
  - Export from `src/easydiffraction/core/__init__.py` so
    `from easydiffraction.core import DisplayHandler` works.
  - Commit: `Add DisplayHandler value object for descriptors`.

- [x] **P1.7 — Wire `display_handler` slot + resolution helpers on
      `Descriptor`**
  - Files: existing `src/easydiffraction/core/descriptor.py` (or
    `parameter.py` / `base_descriptor.py`, whichever owns the base —
    confirm at step start with `git grep -n "class Descriptor"`).
  - Add an optional `display_handler: DisplayHandler | None = None` slot
    on the base class (`__init__` kwarg + storage).
  - Add two resolution helpers on the base class:
    - `resolve_display_name(context: str) -> str` — `context` is one of
      `'latex'`, `'html'`, `'gui'`; returns
      `handler.latex_name or self.name` for `'latex'`,
      `handler.display_name or self.name` otherwise.
    - `resolve_display_units(context: str) -> str` — same shape; falls
      back to `self.units`.
  - Both helpers fall through cleanly when `display_handler is None`, so
    descriptors without an attached handler keep working unchanged.
  - Commit:
    `Wire display_handler slot and resolution helpers on Descriptor`.

- [x] **P1.8 — Inventory every `units=` string and build the vocabulary
      table**
  - Files: new
    `docs/dev/plans/project-summary-rendering_units-inventory.md`
    (working scratch — **not committed**); read-only sweep of
    `src/easydiffraction/`.
  - Run `git grep -nE "units='[^']*'" src/easydiffraction/` and record
    every distinct unit literal. For each, look up the matching
    `_units.code` in
    [`cif_core.dic`](../../../tmp/iucr-dicts/cif_core.dic) and
    [`cif_pow.dic`](../../../tmp/iucr-dicts/cif_pow.dic) via
    `grep -nE "_units.code" tmp/iucr-dicts/*.dic` and pick the
    dictionary's spelling verbatim when one exists. Symbols the
    dictionaries don't define become project-internal codes following
    the dictionary's naming pattern (e.g. `arcminutes`, `teslas`,
    `volts_per_metre`).
  - The **verified inventory** as of this plan (19 distinct literals;
    revise during the step if `src/` has shifted):

    | Symbol   | Code                                        | Source                    |
    | -------- | ------------------------------------------- | ------------------------- |
    | `''`     | `none`                                      | cif_core.dic              |
    | `K`      | `kelvins`                                   | cif_core.dic              |
    | `T`      | `teslas`                                    | project-internal          |
    | `V/m`    | `volts_per_metre`                           | project-internal          |
    | `arcmin` | `arcminutes`                                | project-internal          |
    | `deg`    | `degrees`                                   | cif_core.dic              |
    | `deg²`   | `degrees_squared`                           | project-internal          |
    | `kPa`    | `kilopascals`                               | cif_core.dic              |
    | `Å`      | `angstroms`                                 | cif_core.dic              |
    | `Å²`     | `angstrom_squared`                          | cif_core.dic              |
    | `Å⁻¹`    | `reciprocal_angstroms`                      | cif_core.dic              |
    | `Å⁻²`    | `reciprocal_angstrom_squared`               | cif_core.dic              |
    | `μm`     | `micrometres`                               | project-internal          |
    | `μs`     | `microseconds`                              | cif_core.dic, cif_pow.dic |
    | `μs/Å`   | `microseconds_per_angstrom`                 | cif_pow.dic               |
    | `μs/Å²`  | `microseconds_per_angstrom_squared`         | cif_pow.dic               |
    | `μs²`    | `microseconds_squared`                      | project-internal          |
    | `μs²/Å²` | `microseconds_squared_per_angstrom_squared` | project-internal          |
    | `μs·Å`   | `microsecond_angstroms`                     | project-internal          |

  - The seven project-internal codes follow the dictionary
    plural/singular pattern (each modelled on its closest dictionary
    sibling) and have no `_units.code` round-trip.
  - Commit: none. P1.8 produces no code — it sets up the table that P1.9
    and P1.10 consume. The inventory file is `.gitignore`-style scratch
    under `docs/dev/plans/` named with the `_units-inventory.md` suffix
    so it's clearly disposable; leave it untracked or delete after
    P1.10.

- [x] **P1.9 — Add `units_vocabulary.py` validator covering every
      inventoried code**
  - Files: new `src/easydiffraction/core/units_vocabulary.py`; existing
    `src/easydiffraction/core/__init__.py`.
  - Module exports `VALID_UNITS_CODES: frozenset[str]` containing
    **every** code from the P1.8 inventory — dictionary codes
    (`angstroms`, `angstrom_squared`, `degrees`, `kelvins`,
    `kilopascals`, `microseconds`, `microseconds_per_angstrom`,
    `microseconds_per_angstrom_squared`, `reciprocal_angstroms`,
    `reciprocal_angstrom_squared`, `none`) **plus** every
    project-internal code (`arcminutes`, `teslas`, `volts_per_metre`,
    `micrometres`, `degrees_squared`, `microseconds_squared`,
    `microseconds_squared_per_angstrom_squared`,
    `microsecond_angstroms`).
  - Module exports `validate_units_code(code: str) -> None` raising
    `ValueError(f"Unknown units code: {code!r}. Valid: {sorted(VALID_UNITS_CODES)}")`
    on membership miss.
  - Call `validate_units_code(units)` from the base descriptor's
    `__init__` only when `units` is a non-empty string. Empty strings
    get normalised to `'none'` (the dimensionless ASCII code) at the
    same site so legacy `units=''` declarations keep working until P1.10
    rewrites them.
  - The vocabulary is the single source of truth — adding a new unit
    anywhere in `src/` later requires extending `VALID_UNITS_CODES`
    first, otherwise the descriptor raises at import time. The P1.9 test
    below asserts this round-trip with a parametrised case per code.
  - Commit: `Add units vocabulary validator at descriptor construction`.

- [x] **P1.10 — Sweep `units=` strings across `src/` + attach
      `DisplayHandler`**
  - Files: every descriptor declaration in `src/easydiffraction/` from
    the P1.8 inventory. The sites are concentrated under
    `src/easydiffraction/datablocks/experiment/categories/` (data,
    diffrn, extinction, instrument, peak, refln) and
    `src/easydiffraction/datablocks/structure/categories/`
    (atom_site_aniso, atom_sites, cell).
  - For each call site, apply the inventory mapping from P1.8:
    - Rewrite the unit literal to the ASCII code.
    - Attach a
      `DisplayHandler(display_units=<symbol>, latex_units=<latex>)` with
      the matching Unicode and LaTeX forms (e.g.
      `display_units='Å²', latex_units=r'\AA$^2$'`;
      `display_units='μs/Å', latex_units=r'$\mu\mathrm{s}/\mathrm{\AA}$'`).
      For descriptors whose `name` would benefit from a typeset form
      (Greek letters, subscripts, `Uiso`), also set `display_name` /
      `latex_name`.
    - The empty-string case (`units=''`) becomes `units='none'` plus no
      `display_units` on the handler so terminal output stays bare.
  - The construction-time validator from P1.9 catches any miss
    automatically — if a code is missed, descriptor instantiation raises
    at import time and `pytest --collect-only` fails fast.
  - Commit:
    `Migrate descriptor units to ASCII codes with DisplayHandler`.

- [x] **P1.11 — Migrate table-rendering paths to read via
      `DisplayHandler`**
  - Files: existing
    `src/easydiffraction/project/categories/report/default.py`,
    `src/easydiffraction/report/data_context.py`,
    `src/easydiffraction/report/html_renderer.py`,
    `src/easydiffraction/report/tex_renderer.py`.
  - Every `show_*()` method on `Report` building a unit column reads
    `descriptor.resolve_display_units('gui')` (or `'html'` for Jupyter
    contexts) instead of `descriptor.units` directly.
  - `data_context()` bakes resolved labels and units into the dict
    per-renderer-context once at builder time so Jinja templates consume
    strings, not raw descriptors.
  - HTML and TeX renderers read the pre-resolved strings from the
    context.
  - Commit:
    `Read display labels through DisplayHandler resolution chain`.

- [x] **P1.12 — Vendor MathJax `tex-mml-chtml.js`**
  - Files: new
    `src/easydiffraction/report/templates/html/vendor/mathjax-tex-mml-chtml.js`
    (Apache-2.0, ~1.5 MB minified, MathJax 3.x); new
    `src/easydiffraction/report/templates/html/vendor/LICENSES.md` (full
    Apache-2.0 text + upstream URL + version); update
    `THIRD_PARTY_LICENSES.md` at the repo root.
  - The vendor URL is jsdelivr's
    `https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js` at
    vendoring time; record the exact pinned version string in
    `vendor/LICENSES.md` for traceability.
  - If hatchling's default behaviour does not pick the new `vendor/`
    subtree up under `[tool.hatch.build.targets.wheel]`, extend the
    packaging config with a
    `force-include = { "src/easydiffraction/report/templates/html/vendor" = "easydiffraction/report/templates/html/vendor" }`
    rule in the same commit. The actual `pixi run dist-build` +
    `unzip -l dist/*.whl` verification is a Phase 2 step (see the test
    plan below) per AGENTS.md §Workflow's two-phase split.
  - Commit: `Vendor MathJax tex-mml-chtml bundle`.

- [x] **P1.13 — Wire MathJax loader through `html_offline`**
  - Files: existing
    `src/easydiffraction/report/templates/html/report.html.j2`; existing
    `src/easydiffraction/report/html_renderer.py`.
  - Template emits one of two `<script>` tags driven by a boolean
    context variable `html_offline`:
    - `True`: `<script src="vendor/mathjax-tex-mml-chtml.js"></script>`.
    - `False`:
      `<script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>`.
  - When `html_offline=True`, the renderer copies the vendored file next
    to the emitted `<project>.html` so the relative
    `<script src="vendor/...">` resolves on-disk (use `shutil.copy2`).
    The CDN branch needs no file copy.
  - This is the **same switch** that already governs the
    `fig.to_html(include_plotlyjs=<cdn|True>)` call; the two assets are
    tied to one config field per ADR §2.
  - Commit: `Inline MathJax when html_offline=True`.

- [x] **P1.14 — Add `x_descriptor` + `fit_data_arrays()` on
      `ExperimentBase` and data categories**
  - Files: existing
    `src/easydiffraction/datablocks/experiment/item/base.py` (the
    experiment base — see
    `src/easydiffraction/datablocks/experiment/item/base.py:618` for the
    existing `data` property the new API forwards through);
    `src/easydiffraction/datablocks/experiment/categories/data/bragg_pd.py`,
    `src/easydiffraction/datablocks/experiment/categories/data/total_pd.py`.
  - The current report builder reaches the x array via
    `_line_fit_x_values()` plus an ad-hoc string label (see
    `src/easydiffraction/report/data_context.py:433` and
    `src/easydiffraction/report/data_context.py:470`). Replace that
    ad-hoc path with a **two-layer API**: descriptor metadata lives on
    the data category; `ExperimentBase` exposes flat forwarding
    properties so the renderer reads `e.x_descriptor` and
    `e.fit_data_arrays()` directly.
  - **Layer A — data-category bindings** (`x_descriptor` returns the
    existing descriptor object that owns the x axis; `fit_data_arrays()`
    returns a dict of numpy arrays):
    - `BraggPdData` (Bragg powder, both beam modes):
      - `x_descriptor` returns the `two_theta` descriptor for CWL
        (`bragg_pd.py:210`) or the `time_of_flight` descriptor for TOF
        (`bragg_pd.py:220`). The CWL-vs-TOF branch keys on the
        experiment's `beam_mode`. The descriptor objects live on the
        data-point class, but the collection-level `x_descriptor`
        returns the same descriptor object — the values come from the
        existing collection-level x-array properties already in place at
        `bragg_pd.py:607` and `bragg_pd.py:688`.
    - `TotalPdData` (total-scattering powder):
      - `x_descriptor` returns the `r` descriptor (`total_pd.py:55`).
      - x-array lives at `total_pd.py:366`.
    - `BraggScData` (Bragg single-crystal):
      - `x_descriptor` returns **`None`** — no 1-D x axis, no fit chart
        in scope. (A 2-D figure path is deferred per ADR §8.)
      - `fit_data_arrays()` returns an empty dict `{}` for the same
        reason.
    - All three categories' `fit_data_arrays()` return the dict
      `{'x': np.ndarray, 'meas': np.ndarray, 'meas_su': np.ndarray | None, 'calc': np.ndarray, 'diff': np.ndarray, 'bkg': np.ndarray | None}`
      — x values folded into the same dict so the renderer has one
      source of truth for "all arrays this experiment's fit chart
      needs". Consolidates the existing scattered accessors
      (`measured.intensity`, `calculated.intensity`, inline-difference
      computation in the data-context builder) into one boundary.
  - **Layer B — experiment-class flat surface, split per family** (so
    single-crystal experiments — which do not initialise `self._data`
    per
    `src/easydiffraction/datablocks/experiment/item/base.py:426,446,504`
    — never reach a `self.data.*` dereference):
    - `PdExperimentBase.x_descriptor` — property forwarding to
      `self.data.x_descriptor`. `self._data` is set by
      `PdExperimentBase` (see
      `src/easydiffraction/datablocks/experiment/item/base.py:519,534`),
      so the forward succeeds for every concrete powder experiment.
    - `PdExperimentBase.fit_data_arrays()` — method forwarding to
      `self.data.fit_data_arrays()`.
    - `ScExperimentBase.x_descriptor` — property returning `None`
      directly. No `self.data` reach- through; single-crystal
      experiments have no 1-D x axis and so no fit chart, full stop.
    - `ScExperimentBase.fit_data_arrays()` — method returning `{}`
      directly.
    - Renderers call `e.x_descriptor` and `e.fit_data_arrays()` on the
      experiment regardless of family and branch on
      `if e.x_descriptor is None: skip` — the value carries the "no x
      axis" signal, and no `AttributeError` is ever raised.
    - `ExperimentBase` itself stays abstract for these two surfaces — it
      does **not** declare a default implementation that would mask the
      per-family split. Concrete families inherit from
      `PdExperimentBase` / `ScExperimentBase` and pick up the matching
      version.
  - The `is None` / `{}` semantics replace the previous `hasattr` +
    `NotImplementedError` combination, which would have propagated the
    exception out of `hasattr` rather than registering as absence.
  - Commit: `Add x_descriptor and fit_data_arrays on ExperimentBase`.

- [x] **P1.15 — Replace `fit_data` shape in `data_context()`**
  - Files: existing `src/easydiffraction/report/data_context.py`.
  - Replace the previous `figures.fit_per_experiment`
    `expt_id -> plotly_html_div` payload with the descriptor-driven
    shape per ADR §6, consuming the flat API from P1.14:

    ```python
    'experiments': [
        _build_experiment_payload(e)
        for e in self.project.experiments.values()
    ]

    # In a module-level helper:
    def _build_experiment_payload(e):
        base = {'id': e.id, ...}  # other experiment fields
        if e.x_descriptor is None:
            base['fit_data'] = None
            return base
        arrays = e.fit_data_arrays()
        base['fit_data'] = {
            'x': {
                'values':        arrays['x'],
                'name':          e.x_descriptor.name,
                'units':         e.x_descriptor.units,
                'display_name':  e.x_descriptor.resolve_display_name('html'),
                'latex_name':    e.x_descriptor.resolve_display_name('latex'),
                'display_units': e.x_descriptor.resolve_display_units('html'),
                'latex_units':   e.x_descriptor.resolve_display_units('latex'),
            },
            'series': {
                'meas': {'values': arrays['meas'],    'su': arrays['meas_su'], 'label': 'Measured'},
                'calc': {'values': arrays['calc'],                              'label': 'Calculated'},
                'diff': {'values': arrays['diff'],                              'label': 'Difference'},
                'bkg':  {'values': arrays['bkg'],                               'label': 'Background'},
            },
        }
        return base
    ```

    Single-crystal experiments contribute `fit_data: None`; renderers
    skip the fit-quality block when the value is `None`. The
    `fit_data_arrays()` call happens once per experiment, so the four
    `arrays[...]` reads share a single dict.

  - The previous pre-rendered HTML payload is **removed entirely** —
    neither renderer reads it. The Plotly figure is built at HTML render
    time from `fit_data`; the LaTeX renderer reads the same `fit_data`
    for the CSV emitter in P1.16.
  - Commit: `Replace fit_data payload with descriptor-driven shape`.

- [x] **P1.16 — Standalone per-figure pgfplots `.tex` → PDF, included by
      the report** (See ADR §3.3 — "standalone pgfplots figures, built
      independently, included as PDF" — for the full decision this step
      implements.)
  - Files: existing `src/easydiffraction/report/tex_renderer.py`,
    `src/easydiffraction/report/pdf_compiler.py`; renamed
    `src/easydiffraction/report/templates/tex/report.tex.j2` (from
    P1.4); new `src/easydiffraction/report/templates/tex/figure.tex.j2`
    (standalone figure document).
  - Add `_write_fit_csv(expt_id, fit_data, out_dir)` writing
    `<out_dir>/data/fit_<expt_id>.csv` with columns
    `x, meas, calc, diff` (+ `meas_su` when present). Write all rows; do
    not downsample the pgfplots data. Background is omitted from this
    CSV because the PDF figure does not plot it. Python stdlib `csv`, no
    new dependency.
  - Add `figure.tex.j2`: a `\documentclass{standalone}` pgfplots
    document, one per experiment, rendered to `data/fit_<expt_id>.tex`.
    Mandatory preamble: `\pgfplotsset{set layers}` **and** axis option
    `mark layer=like plot` (both required — `mark layer` is inert
    without `set layers`; together they let the calculated line draw
    over the measured markers).
  - **Intensity panel: two plotted data series.**
    - Measured — connecting line + markers for **all** points: `mark=*`,
      small `mark size=0.75pt`, Plotly- derived line width,
      `line join=bevel`, and marker outline width `0pt`.
    - Calculated — red line, declared after measured so it draws above
      the measured data.
    - **No measured–calculated band, no background curve, and no
      measured error bars in the PDF.** Residual and Bragg peaks stay in
      their own panels, but appear in the main legend like Plotly.
  - Bragg tick row + residual panel as before (residual in its own
    panel; difference is not overlaid on intensity).
  - `report.tex.j2` (main document) includes each figure as a pre-built
    PDF: `\includegraphics[width=\linewidth]{data/fit_<expt_id>.pdf}` —
    **no inline pgfplots in the main report**.
  - `Report.save_tex()` writes, per experiment, the CSV + the standalone
    `fit_<expt_id>.tex`, and writes the main `<project>.tex`.
    `pdf_compiler.py` is extended so `save_pdf()` compiles **each figure
    `.tex` first, then the main `<project>.tex`** (which
    `\includegraphics` the figure PDFs) — an N+1-document build. Each
    compile (figure and main) uses the **same discovered-engine fallback
    the compiler already implements** (`tectonic` → `latexmk` →
    `pdflatex`, `_ENGINE_ORDER` in `pdf_compiler.py`) — not `tectonic`
    only — so TeX Live / MiKTeX users keep PDF output. Compiling each
    figure as its own document is what isolates the memory pool; the
    engine choice is unchanged. When only `tex` is configured (no
    `pdf`), the figure `.tex` + CSV are written but not compiled.
  - **Data resolution — concrete contract.** Plot every row from
    `fit_data` in the pgfplots CSV. Do not downsample PDF plots or use a
    sampled marker/error-bar overlay.
  - Commit: `Emit standalone pgfplots figures included as PDF`.

- [x] **P1.17 — HTML Plotly builder consumes `fit_data` directly**
  - Files: existing `src/easydiffraction/report/html_renderer.py`;
    existing `src/easydiffraction/report/templates/html/report.html.j2`;
    existing `src/easydiffraction/display/plotters/plotly.py` (if
    separate — confirm with `git grep -n "class.*Plotly" src/`).
  - The HTML renderer feeds each experiment's `fit_data` dict to the
    Plotly builder at render time, then embeds the resulting figure via
    `fig.to_html(include_plotlyjs=<cdn|True>)`. The template no longer
    expects pre-rendered HTML in the context.
  - Axis labels and series labels come from the same `fit_data` payload
    the TeX renderer uses — one source of truth.
  - Commit: `Build Plotly fit figures from fit_data context`.

- [x] **P1.18 — HTML serialization parity: forced light theme + notebook
      modebar (ADR §2)**
  - Files: `src/easydiffraction/report/html_renderer.py`;
    `src/easydiffraction/display/plotters/plotly.py` (extract a shared
    serialization helper — see below).
  - **Problem this fixes.** The current report HTML path serializes with
    only `full_html=False` + `include_plotlyjs=...`
    (`html_renderer.py:283`); it does **not** pass the notebook
    `config`, does **not** pass the notebook `post_script`, and does
    **not** force the figure template after `PlotlyPlotter()` has set
    the global default from the ambient theme (`html_renderer.py:221`).
    So the report can inherit a dark theme and shows Plotly's default
    modebar. ADR §2 requires the report to match the notebook.
  - **Forced light theme — report only.** For the report, set each
    figure's `template` to `plotly_white` **on the figure object** (e.g.
    `fig.update_layout(template='plotly_white')`) right before
    serialization — not via the global `pio.templates.default`, which
    `PlotlyPlotter.__init__` already set from the ambient theme. This
    makes the report independent of notebook/system dark mode. **The
    notebook path must NOT be forced** — it stays theme-adaptive per
    `_default_template_name` (ADR §1 / §2). So forcing `plotly_white` is
    a report-only override, not part of the shared mechanics.
  - **Notebook modebar — reuse the notebook serialization mechanics (two
    pieces).** The curated buttons come from
    `PlotlyPlotter._get_config()` (`plotly.py:567` —
    `displaylogo=False`, `modeBarButtonsToRemove`), **but the custom
    legend-toggle button is NOT in `_get_config()`** — it is installed
    via `post_script` plus the `_wrap_html_figure` wrapper in
    `_show_figure` (`plotly.py:954`). To match the notebook, the report
    must pass **both** `config=_get_config()` and the same
    `post_script`, and apply the same wrapper.
  - **Implementation: one shared low-level helper + a report-only
    template override.** Extract the notebook's
    `pio.to_html(..., config=_get_config(), post_script=...)`
    - `_wrap_html_figure` sequence into a single classmethod on
      `PlotlyPlotter` that takes the template as a parameter — e.g.
      `serialize_html(fig, *, offline, force_template: str | None = None)`:
      it applies `_get_config()`, the legend-toggle `post_script`, and
      the wrapper, and when `force_template` is given does
      `fig.update_layout(template=force_template)` first. The
      **notebook** path (`_show_figure`) calls it with
      `force_template=None` (keeps its theme-adaptive template); the
      **report** renderer calls it with `force_template='plotly_white'`.
      One source of truth for the modebar/post-script/wrapper; the
      light-theme override lives only at the report call site.
  - Commit: `Serialize report Plotly figures via shared notebook path`.

- [x] **P1.19 — Clean up stale `figures/` references in code and docs**
  - Files: `src/easydiffraction/project/categories/report/default.py`,
    `src/easydiffraction/report/tex_renderer.py`,
    `src/easydiffraction/report/pdf_compiler.py`,
    `docs/docs/user-guide/analysis-workflow/report.md`,
    `docs/docs/api-reference/report.md`.
  - Update install-hint warning text (engine-missing branch) from
    "`.tex`, `figures/`, and `styles/` are still written" to "`.tex`,
    `data/`, and `styles/` are still written" — matches the new on-disk
    layout.
  - Update docstrings and user-guide prose anywhere the old `figures/`
    directory was named.
  - A final `git grep -n figures/` across `src/` and `docs/` should
    return only legitimate hits (e.g. inline comments describing the
    rendered output's typesetting, not filesystem paths).
  - Commit: `Replace stale figures/ references with data/`.

- [x] **P1.20 — Update tutorials and user-guide for the new surface**
  - Files: `docs/docs/tutorials/ed-3.py`,
    `docs/docs/tutorials/ed-14.py`, any other tutorial `.py` referencing
    `style=` or `--style` (grep at step start); regenerated
    `docs/docs/tutorials/*.ipynb` artefacts;
    `docs/docs/user-guide/analysis-workflow/report.md`;
    `docs/docs/api-reference/report.md`.
  - Drop every `style='iucr'` / `style='revtex'` / `--style iucr`
    reference from tutorial sources. The new examples show
    `project.report.formats = ['html', 'tex']` + `project.save()` and
    the matching one-off `project.report.save_pdf()`.
  - Add a short user-guide note covering the `html_offline=True`
    two-asset bundle (Plotly + MathJax, ~4.5 MB total).
  - Regenerate notebooks via `pixi run notebook-prepare` and stage the
    regenerated `.ipynb` files alongside the `.py` edits.
  - Commit: `Update tutorials and docs for single-style report surface`.

- [x] **P1.21 — Visual parity check — PDF figure vs Plotly figure**
  - Files: `src/easydiffraction/report/templates/tex/figure.tex.j2`
    (geometry fixes); read-only reference to the Plotly builder in
    `src/easydiffraction/display/plotters/plotly.py`.
  - The pgfplots PDF figure and the Plotly HTML figure must share the
    **same geometry** even though fonts and exact line rendering differ.
    This is a build-and-eyeball check on a real project (the `lbco_hrpt`
    tutorial), **not** an automated pixel test — fonts differ, so pixel
    diffing would false-fail. It is a Phase 1 step because it drives
    geometry corrections to `figure.tex.j2`; it produces template
    commits, not test files.
  - Procedure (per representative experiment):
    1. **Build the PDF figure.** Compile the standalone
       `reports/tex/data/fit_<expt>.tex` to `fit_<expt>.pdf` (and/or the
       full `reports/<project>.pdf`).
    2. **Rasterize to PNG.** Any available rasteriser —
       `pdftoppm -png -r 150 fit_<expt>.pdf out`,
       `magick -density 150 fit_<expt>.pdf out.png`, or macOS
       `sips -s format png fit_<expt>.pdf --out out.png`.
    3. **Capture the Plotly reference.** Generate
       `reports/<project>.html` (or the notebook figure) for the same
       experiment and capture its chart as an image — open the HTML in a
       browser and screenshot, or use a browser-automation tool.
       Plotly→static image has **no** headless path here (`kaleido` was
       dropped), so the reference comes from the rendered HTML /
       notebook, not a Python export.
    4. **Compare geometry side by side.** The two images must match on:
       - overall figure aspect ratio / box dimensions;
       - number of stacked panels and their **relative heights**
         (intensity : Bragg : residual);
       - **vertical spacing between panels** (no oversized or uneven
         gaps);
       - which panels carry x-axis ticks/labels (**only the bottom
         panel**) and which carry a y-axis title (**each panel its own,
         once** — no missing titles, no stray/overlapping titles across
         panels);
       - x-range (`xmin`/`xmax`) and per-panel y-range;
       - legend position. Fonts, line antialiasing, and marker rendering
         may differ — out of scope.
  - **Known defects to fix in `figure.tex.j2`:** uneven/wrong
    inter-panel spacing (`vertical sep` / per-panel `height`), and
    spurious or overlapping y-axis titles on the short Bragg / residual
    panels (tune each panel's `ylabel`, `ylabel style`, `yticklabel`
    placement so labels don't collide — the demo symptom where "Bragg",
    "lbco", and "Residual" overprinted). Re-run steps 1–4 until the
    geometry matches the Plotly figure.
  - Follow-up adjustment: derive pgfplots panel heights and vertical
    spacing from the Plotly row-height constants. Use `scale only axis`
    so the axes rectangles preserve Plotly's main/Bragg/residual ratios,
    with total axis height matching the current Plotly chart aspect
    ratio (about 70% of the axis width for the representative 856x600
    HTML chart).
  - Commit one geometry fix per logical change, e.g.
    `Match pgfplots figure geometry to Plotly layout`.

- [x] **P1.22 — Reach Phase 1 review gate**
  - No-code step. Mark every `[ ]` above as `[x]`; commit the plan-file
    update alone.
  - Commit: `Reach Phase 1 review gate`.

- [x] **P1.23 — Align report plot styling with Plotly output**
  - Files: `src/easydiffraction/display/plotters/plotly.py`,
    `src/easydiffraction/report/fit_plot.py`,
    `src/easydiffraction/report/tex_renderer.py`,
    `src/easydiffraction/report/templates/tex/figure.tex.j2`.
  - HTML reports force report-only light styling after applying
    `plotly_white`: legend background `rgba(255, 255, 255, 0.5)` and
    light axis-frame colors are applied even when the figure object was
    built under a dark notebook/system theme. Notebook rendering stays
    theme-adaptive.
  - The measured powder trace exposes reusable style constants: marker
    size 6 px, marker outline 0 px, line width 2 px, error-bar thickness
    2 px, and error-bar cap width 4 px for Plotly/HTML. The PDF
    deliberately keeps the smaller accepted pgfplots measured marker
    size (`0.75pt`) and does not draw measured error bars.
  - PDF figures use Plotly-like inner grids: vertical grid lines on
    major x ticks in all panels, horizontal grid lines in the intensity
    and residual panels, no outside tick marks, and light Plotly-derived
    axis/grid colors.
  - PDF legends include measured, calculated, residual, and Bragg-peak
    entries. Residual and Bragg peaks remain in their own panels even
    though their legend entries live with the main legend, matching
    Plotly where practical.
  - Compile and visually inspect the standalone `fit_<expt_id>.pdf` plus
    the full report PDF on the representative `lbco_hrpt` project. The
    standalone figure should match the Plotly chart's 70%
    height-to-width ratio and keep the same main/Bragg/residual panel
    ratios and vertical spacing.
  - Commit: `Align report plot styling with Plotly output`.

- [x] **P1.24 — Disable draft line numbers and align numeric tables**
  - Files: `src/easydiffraction/report/templates/tex/report.tex.j2`.
  - Disable the `iucrjournals.cls` draft line numbering in generated
    reports by emitting `\nolinenumbers` at the start of the document.
    The vendored class still loads `lineno`, but reports should not show
    line numbers by default.
  - Add `siunitx` to the report template and use `S` columns for numeric
    report tables: refinement, unit-cell numeric rows, atom-site
    fractional coordinates / occupancies / isotropic ADPs, anisotropic
    ADPs, and experiment temperature / pressure. Non-numeric rows in
    mixed key-value tables are wrapped in `\multicolumn` cells so
    `siunitx` does not parse text as a number.
  - Parenthesized uncertainty notation such as `0.584(20)` is left
    unwrapped in `S` cells; `siunitx` parses it as numeric uncertainty
    notation and aligns on the decimal marker.
  - Commit: `Align numeric report table columns`.

- [x] **P1.25 — Restore accepted pgfplots line widths**
  - Files: `src/easydiffraction/report/fit_plot.py`.
  - Keep Plotly/HTML line-width settings unchanged, but use the earlier
    accepted pgfplots widths for PDF figures: measured line `0.5pt`,
    calculated line `0.75pt`, and residual line `0.5pt`.
  - Commit: `Restore pgfplots report line widths`.

- [x] **P1.26 — Render category-driven reports with aligned tables (ADR
      §2)**
  - Files: `docs/dev/adrs/accepted/project-summary-rendering.md`,
    `src/easydiffraction/datablocks/experiment/categories/background/base.py`,
    `src/easydiffraction/datablocks/experiment/categories/background/line_segment.py`,
    `src/easydiffraction/datablocks/experiment/categories/calculator/default.py`,
    `src/easydiffraction/datablocks/experiment/categories/data/bragg_pd.py`,
    `src/easydiffraction/datablocks/experiment/categories/diffrn/default.py`,
    `src/easydiffraction/datablocks/experiment/categories/experiment_type/default.py`,
    `src/easydiffraction/datablocks/experiment/categories/instrument/cwl.py`,
    `src/easydiffraction/datablocks/experiment/categories/instrument/tof.py`,
    `src/easydiffraction/datablocks/experiment/categories/linked_crystal/default.py`,
    `src/easydiffraction/datablocks/experiment/categories/linked_phases/default.py`,
    `src/easydiffraction/datablocks/experiment/categories/peak/base.py`,
    `src/easydiffraction/datablocks/experiment/categories/peak/cwl_mixins.py`,
    `src/easydiffraction/datablocks/experiment/categories/refln/bragg_pd.py`,
    `src/easydiffraction/datablocks/structure/categories/atom_sites/default.py`,
    `src/easydiffraction/datablocks/structure/categories/cell/default.py`,
    `src/easydiffraction/datablocks/structure/categories/space_group/default.py`,
    `src/easydiffraction/display/plotters/base.py`,
    `src/easydiffraction/report/data_context.py`,
    `src/easydiffraction/report/templates/html/report.html.j2`,
    `src/easydiffraction/report/templates/html/style.css`,
    `src/easydiffraction/report/templates/tex/figure.tex.j2`,
    `src/easydiffraction/report/templates/tex/report.tex.j2`,
    `src/easydiffraction/report/tex_renderer.py`.
  - **Category-driven report content.** Replace the last hand-written
    structure and experiment summary tables with `ReportDataContext`
    category traversal: every public structure category and every public
    experiment category gets its own sub-subsection, item categories
    render as two-column key-value tables, and collection loops render
    as one-to-one loop tables. Experiment data categories (`pd_data`,
    `total_data`, `refln`) stay out of the tabular report because they
    are already represented by plots or are too large for summary
    tables. The fit-quality chart remains the first experiment
    sub-subsection.
  - **Shared readable labels and units.** Add the missing
    `DisplayHandler` names and units used by report tables so HTML and
    TeX resolve the same domain labels (`H-M symbol`,
    `$2\theta$ offset`, `Wavelength`, `Scale`, `$U_{\mathrm{iso}}$`,
    etc.) rather than raw CIF field names where a better report label
    exists. Normalise report angle units to `deg` and avoid
    degree-symbol / `degree_squared` labels.
  - **Normal-weight headings and headers.** Make HTML and TeX document
    titles, section headings, subheadings, and table headers normal
    weight. Table hierarchy comes from spacing, sizing, and rules
    instead of bold headers.
  - **Decimal-point-aligned numeric columns.** Keep TeX numeric columns
    on `siunitx` `S` columns and add HTML-side numeric metadata (`left`,
    decimal marker, `right`, and per-column widths) so `report.html.j2`
    emits `number-left`, `number-dot`, and `number-right` spans with
    tabular digits. This aligns values such as `0.584(20)` and
    `3.89086937` on the decimal marker without changing the displayed
    text.
  - **Matching table layout.** HTML tables shrink to their content width
    instead of filling the report page. HTML and TeX both use only top,
    middle, and bottom rules with very light alternating body-row
    backgrounds starting at the first body row.
  - **Automatic HTML section numbering.** Add CSS counters so HTML
    sections mirror the PDF numbering (`1`, `1.1`, `1.1.1`) while
    keeping the document title and Abstract unnumbered.
  - **PDF plot legend polish.** Explicitly set the measured marker fill
    and draw color in the pgfplots legend so the legend marker matches
    the plotted measured points.
  - Commit: `Render category-driven reports with aligned tables`.

- [x] **P1.27 — Harmonize report tables, colors, title, and fonts (ADR
      §2)**
  - Files: `docs/dev/adrs/accepted/project-summary-rendering.md`,
    `docs/dev/plans/project-summary-rendering.md`,
    `src/easydiffraction/display/plotters/plotly.py`,
    `src/easydiffraction/report/data_context.py`,
    `src/easydiffraction/report/fit_plot.py`,
    `src/easydiffraction/report/html_renderer.py`,
    `src/easydiffraction/report/style.py`,
    `src/easydiffraction/report/templates/html/report.html.j2`,
    `src/easydiffraction/report/templates/html/style.css`,
    `src/easydiffraction/report/templates/tex/figure.tex.j2`,
    `src/easydiffraction/report/templates/tex/report.tex.j2`,
    `src/easydiffraction/report/tex_renderer.py`.
  - Add report styling constants for the axis-frame color, table-inner
    color, chart-grid color, row-fill color, subtitle, HTML font stack,
    and TeX font choices. Feed those constants into HTML CSS, Plotly
    report figure serialization, pgfplots figures, and TeX table styles.
  - Render HTML and TeX tables with an outer frame and, for header
    tables, one header rule. The outer frame and header rule use the
    darker shared axis-frame color; filled rows use the shared row-fill
    color. Tables do not draw separators between columns or between body
    rows.
  - Keep the HTML and TeX row striping consistent: the first body row is
    filled for both header and key-value tables. Remove the extra TeX
    spacing around the line below header rows by using framed tables
    plus a single colored header rule instead of booktabs rules.
  - Force key-value tables to occupy half of the text line. Classify
    loop tables from their rendered content: compact loops occupy half
    of the text line, and wider loops occupy the full text line. Add
    `report_style` to the saved TeX report context so project saves can
    render the configured font and color settings.
  - Tighten HTML table line height to match the denser PDF table rhythm.
  - Add terminal dots to generated section numbers in both HTML and TeX
    (`1.`, `1.1.`, `1.1.1.`).
  - Render the report title and project description left-aligned. Show
    the project description as an unnumbered `Description` section, and
    show `EasyDiffraction report` as a smaller subtitle under the main
    title.
  - Configure free report fonts centrally: HTML uses a non-embedded
    local font stack headed by Nunito; TeX uses `fontspec` with Nunito
    and Fira Math when available, otherwise leaving the engine's bundled
    Latin Modern defaults in place so the generated PDF embeds the fonts
    it actually uses.
  - Commit: `Harmonize report table and title styling`.

## Test plan (Phase 2)

Per AGENTS.md §Testing, every new module, class, and bug fix ships with
tests; unit tests mirror the source tree. Before running the
verification commands below, add or update:

- [ ] **`tests/unit/easydiffraction/report/test_enums.py`** (extend) —
      `ReportStyleEnum` removed (calling `ReportStyleEnum('iucr')`
      raises `AttributeError`); `ReportFormatEnum` membership unchanged.
      P1.1 surface.
- [ ] **`tests/unit/easydiffraction/project/categories/report/test_default.py`**
      (extend) — no `style` descriptor field; `report.save_tex()` and
      `report.save_pdf()` accept no `style=` kwarg (calling raises
      `TypeError`); the five remaining descriptors round-trip through
      `project.cif`. P1.1, P1.2 surface.
- [ ] **`tests/unit/easydiffraction/test___main__.py`** (extend) —
      standalone `save` and `save-report` commands are unknown; project-
      first argument normalization does not treat them as saved-project
      actions. P1.2 surface.
- [ ] **`tests/unit/easydiffraction/core/test_display_handler.py`**
      (new) — `DisplayHandler` is frozen, slotted; all four fields
      default to `None`; constructor accepts kwargs; unspecified fields
      stay `None`. P1.6 surface.
- [ ] **`tests/unit/easydiffraction/core/test_descriptor_display.py`**
      (new) — `Descriptor` with no `display_handler` returns `name` /
      `units` from every `resolve_*` call; with a handler attached,
      returns the right field per context (`'latex'` / `'html'` /
      `'gui'`); missing handler fields fall back to plain `name` /
      `units`. P1.7 surface.
- [ ] **`tests/unit/easydiffraction/core/test_units_vocabulary.py`**
      (new) — `VALID_UNITS_CODES` contains **every** code from the P1.8
      inventory (11 dictionary codes + 8 project-internal codes —
      exhaustive enumeration in the test body so the next contributor
      adding a unit has a matching test row);
      `validate_units_code('angstroms')` is a no-op;
      `validate_units_code('Å')` raises `ValueError` citing the
      offending code; the empty-string → `'none'` normalisation is
      exercised. P1.9 surface.
- [ ] **Descriptor-instantiation smoke** — every descriptor declared
      under `src/easydiffraction/` constructs without raising at import
      time. Run via `pytest --collect-only` (a collection failure on a
      missing code is the desired signal) or a dedicated test importing
      every category package. P1.10 surface — catches any missed
      inventory entry from P1.8.
- [ ] **`tests/unit/easydiffraction/project/categories/report/test_default.py`**
      (further extend) — every `show_*()` method renders unit columns
      using `display_units` rather than the raw `units=` ASCII code (a
      snapshot containing `Å²` rather than `angstrom_squared`). P1.11
      surface.
- [ ] **`tests/unit/easydiffraction/report/test_html_renderer.py`**
      (extend) — `html_offline=False` emits the CDN MathJax script tag;
      `html_offline=True` emits the relative vendored path and copies
      `mathjax-tex-mml-chtml.js` next to the output `.html`. P1.12,
      P1.13 surface.
- [ ] **`tests/unit/easydiffraction/datablocks/experiment/categories/data/test_bragg_pd.py`**
      and **`test_total_pd.py`** (extend) — data-category `x_descriptor`
      resolves to the right descriptor per beam mode (CWL → `two_theta`,
      TOF → `time_of_flight`, total → `r`). `fit_data_arrays()` returns
      the documented dict shape including the `'x'` numpy array.
      Single-crystal experiments have no data category in the current
      tree (`src/easydiffraction/datablocks/experiment/categories/data/`
      contains only `bragg_pd.py`, `total_pd.py`, `factory.py`,
      `__init__.py`) — their `None` / `{}` semantics are covered in the
      `ExperimentBase` bullet below, not here. P1.14 layer A.
- [ ] **`tests/unit/easydiffraction/datablocks/experiment/item/test_base.py`**
      (extend) — Layer B split is asserted against **real concrete
      experiments**, not a mocked base:
  - Construct concrete `CwlPdExperiment` / `TofPdExperiment` (or
    whichever non-abstract powder classes the tree exposes) —
    `x_descriptor` forwards to the data category and returns the
    matching descriptor; `fit_data_arrays()` returns the populated dict.
  - Construct concrete `CwlScExperiment` / `TofScExperiment` —
    `x_descriptor is None` and `fit_data_arrays() == {}`. Asserting on
    the concrete class catches the `self._data`-not-set pitfall flagged
    in the review: a regression that naively moved the forwarding to
    `ExperimentBase` would raise `AttributeError` on these instances,
    not return `None`.
  - No `AttributeError`, `NotImplementedError`, or any other exception
    escapes either property under any of the four experiments above.
    P1.14 layer B.
- [ ] **`tests/unit/easydiffraction/report/test_data_context.py`**
      (extend) — each experiment's `fit_data` carries the new `x`
      sub-dict (six string keys + `values`) and `series` sub-dict
      (`meas`, `calc`, `diff`, optional `bkg`); pre-rendered HTML keys
      are absent; single-crystal experiments emit `fit_data: None`.
      P1.15 surface.
- [ ] **`tests/unit/easydiffraction/report/test_tex_renderer.py`**
      (extend) — `_write_fit_csv` writes the right schema
      (`x, meas, calc, diff` + optional `meas_su`) with every row from
      `fit_data`; each standalone `data/fit_<expt>.tex` contains
      measured line+markers for all points, calculated line, residual
      and Bragg legend entries, light inner grid settings, and no
      band/fill-between, no background plot, no error-bar overlay, and
      no sampled marker path; the preamble contains both
      `\pgfplotsset{set layers}` and `mark layer=like plot`; the main
      `report.tex` uses `\includegraphics{data/fit_<expt>.pdf}` and
      contains **no** inline `\begin{axis}`. P1.16 + P1.23 surface.
- [ ] **`tests/unit/easydiffraction/report/test_html_renderer.py`**
      (further extend) — Plotly figures appear in the rendered HTML and
      are built from the `fit_data` payload rather than read from a
      context key; the resulting HTML body contains a
      `<div class="plotly-graph-div">` per experiment. P1.17 surface.
- [ ] **`tests/unit/easydiffraction/report/test_html_renderer.py`**
      (further extend) — **HTML serialization parity, with the
      report-only light override.** With `pio.templates.default` set to
      `plotly_dark` (simulating notebook/system dark mode):
  - **Report** serialization (`force_template='plotly_white'`) carries
    `plotly_white`, not `plotly_dark`.
  - **Notebook** serialization (`force_template=None`) keeps the
    theme-adaptive template (here `plotly_dark`) — i.e. the shared
    helper does **not** force light for the notebook path. This guards
    the regression where forcing light leaks into the interactive path.
  - Both paths emit a `config` matching `PlotlyPlotter._get_config()`
    (`displaylogo:false`, the curated `modeBarButtonsToRemove` set)
    **and** the legend- toggle behaviour from the shared `post_script` /
    `_wrap_html_figure`, since both call the single serialization
    helper. P1.18 surface.
  - The report path also forces light legend background and light
    axis-frame colors after applying `plotly_white`, preventing
    dark-theme colors from leaking into report HTML. P1.23 surface.
- [ ] **`tests/unit/easydiffraction/report/test_pdf_compiler.py`**
      (extend) — **N+1 build + engine fallback.** Each figure
      `data/fit_<expt>.tex` is compiled **before** the main
      `<project>.tex` (assert call ordering); figure and main compiles
      use the **same discovered engine** (`_ENGINE_ORDER` fallback
      `tectonic` → `latexmk` → `pdflatex`), not tectonic only; the
      no-engine branch writes the `.tex` + CSV bundle and returns with
      the install hint **without raising**; an engine non-zero exit
      raises a clear error. P1.16 surface.
- [ ] **`tests/unit/easydiffraction/report/test_html_renderer.py`**
      (further extend) — **HTML category tables and CSS polish
      (P1.26).** Rendered fixtures include category-driven structure and
      experiment tables, with experiment data categories skipped and the
      fit-quality chart first in the experiment block. Numeric cells
      render split into `<span class="number">` with `number-left`,
      `number-dot`, and `number-right` children while preserving the
      original `aria-label`; non-numeric cells stay plain. The emitted
      CSS sets `h1`–`h4` and `th` to `font-weight: 400`, fits tables to
      content width, stripes the first body row, and defines
      section-numbering counters on `h2`/`h3`/`h4`; the title (`h1`) and
      Abstract carry no counter. P1.26 surface.
- [ ] **`tests/unit/easydiffraction/report/test_tex_renderer.py`**
      (further extend) — **TeX category tables and styling (P1.26).**
      The main report renders structure and experiment categories as
      separate sub-subsections, skips experiment data categories, uses
      normal-weight titles/headings/table headers, applies the first-row
      table striping commands, keeps numeric columns on `S` alignment,
      emits readable labels/units, and sets the measured pgfplots legend
      marker color explicitly. P1.26 surface.
- [ ] **`tests/unit/easydiffraction/report/test_html_renderer.py`**
      (further extend) — **shared report styling (P1.27).** Assert that
      the HTML report injects shared axis/grid/row color CSS variables,
      uses dotted section-number counters, renders a left-aligned
      subtitle and unnumbered `Description` section, emits framed tables
      without column or body-row separators, sets compact table
      line-height, and applies content-driven half/full table width
      classes.
- [ ] **`tests/unit/easydiffraction/report/test_tex_renderer.py`**
      (further extend) — **shared report styling (P1.27).** Assert that
      the TeX report defines the shared axis/grid/row colors, uses
      framed half-width and full-width tables without inner column
      separators, emits a colored header rule instead of booktabs or
      body-row rules, adds terminal dots to section numbers, renders the
      custom left-aligned title/subtitle and `Description` section,
      includes the configured font setup, and passes `report_style`
      through saved TeX report rendering.
- [ ] **Wheel-packaging verification** — run `pixi run dist-build` and
      then
      `unzip -l dist/*.whl | grep -E 'mathjax|iucrjournals.cls|harvard.sty'`
      to confirm the wheel ships the two remaining TeX style files plus
      the MathJax bundle. The 10 deleted REVTeX files must be absent
      from the wheel. `dist/*.whl` is a verification artefact — do not
      stage it. P1.3 + P1.11
  - P1.12 surface.
- [ ] **No-kaleido smoke** — after the dependency removal, importing
      `easydiffraction.report` does not require `kaleido`;
      `pixi run unit-tests` passes without the package present. P1.5
      surface — covered automatically by the broader test sweep but call
      it out.
- [ ] **Integration / script-test coverage** — verify
      `pixi run script-tests` exercises at least one tutorial that emits
      `reports/<project>.html` with MathJax loaded and one tutorial that
      emits the pgfplots `.tex` + `data/*.csv` bundle. Extend a tutorial
      if not.

Use `pixi run test-structure-check` to confirm the unit-test layout
mirrors the source tree per AGENTS.md §Testing.

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

Run in order; each must complete clean before the next. Per AGENTS.md
§Workflow: `pixi run fix` regenerates
`docs/dev/package-structure/full.md` and `short.md` automatically. The
new vendored MathJax bundle and the two remaining TeX style files are
intentional sources — included in commits. The 10 deleted REVTeX files
are removed from the worktree via `git rm` so the deletion appears in
the diff. Benchmark CSVs under `docs/dev/benchmarking/` produced by
`pixi run script-tests` are untracked verification artifacts; do not
stage them.

Docstring convention for propagated exceptions: document exceptions in a
`Raises` section where the function body raises them directly. For
public wrappers that call lower-level helpers which may raise, keep the
wrapper lint-clean under pydoclint's direct-raise rule and mention the
propagation in prose only when it materially helps users.

## Suggested Pull Request

**Title:**
`[report] Single iucrjournals style + pgfplots + DisplayHandler`

**Description:**

Aligns the `project.report` rendering surface with the rewritten
`project-summary-rendering` ADR. The visible changes for users:

- **One LaTeX style — `iucrjournals`.** The `style=` argument is gone,
  and CLI report generation now follows the report flags persisted in
  `project.cif` during `fit`. Multi-style support (REVTeX, Elsevier, …)
  is deferred to a follow-up ADR. The vendored TeX bundle shrinks from
  12 files to 2 (`iucrjournals.cls` + `harvard.sty`, both CC0 1.0).
- **No `kaleido`, no Chrome bootstrap.** Each fit-quality figure in the
  PDF / TeX bundle is a standalone `pgfplots` document under
  `reports/tex/data/`, compiled to PDF and included in the report —
  vector throughout, no inline pgfplots in the main document. The TeX
  engine (Tectonic / TeX Live / MiKTeX) handles the plotting; users no
  longer need a system browser to generate a PDF report.
- **Fit plots look consistent across HTML and PDF.** Report HTML always
  uses the light Plotly report theme, while the PDF figure uses
  Plotly-derived colors, line widths, marker sizes, grids, panel
  proportions, and legend entries.
- **Offline HTML is now actually offline.** When
  `project.report.html_offline = True`, both Plotly and MathJax are
  inline-bundled — the resulting `.html` opens with no network. The
  vendored MathJax `tex-mml-chtml.js` (~1.5 MB, Apache-2.0) ships with
  the wheel.
- **Pretty units in tables, ASCII codes on the wire.** Descriptor
  `units=` strings now follow the CIF DDLm `_units.code` vocabulary
  verbatim (`angstrom_squared`, `degrees`, `kelvins`, `kilopascals`, …).
  A new `DisplayHandler` value object carries the Unicode and LaTeX
  label / unit forms (`Å²`, `°`, `$U_{\mathrm{iso}}$`) so every renderer
  — terminal `show_*`, Jupyter HTML, PDF — shows the right form for its
  context.

Internally, the change pivots fit-data flow through a single
descriptor-driven `fit_data` payload in `ReportDataContext`: one source
of truth, two renderers (Plotly for HTML, pgfplots CSV for TeX), every
experiment type (Bragg powder, TOF, total-scattering, future Q-space)
without further ADR changes.

**Scope label:** `[report]`. Builds on PR #184 (IUCr CIF alignment) and
the earlier commits on this branch (`project.report` config category,
`analysis.software`, `project.publication`, and CLI report saving via
`fit`).
