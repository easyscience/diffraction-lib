# ADR: Project Summary Rendering

**Status:** Accepted  
**Date:** 2026-05-26

Defines the **non-CIF** human-readable rendering surface for a project:
what the terminal/Jupyter summary, the auto-generated HTML report, the
on-demand journal-style LaTeX export, and (eventually) the GUI Summary
tab all consume and emit.

Runs alongside, and **extends**, the accepted
[`iucr-cif-tag-alignment.md`](../accepted/iucr-cif-tag-alignment.md)
ADR (landed as PR #184). The alignment ADR established:

- A new `project.report` facade slot (replaces the unimplemented
  `project.summary` placeholder), with `save()` and `check()`
  methods.
- A single `reports/` directory at project root.
- A `project.save(report=True)` opt-in flag for the IUCr CIF.

That ADR currently scopes `project.report` to **CIF only** — the
multi-datablock IUCr submission CIF written to
`reports/<project>.cif`. This ADR keeps the facade and adds a
**`project.report` configuration category** with six scalar
persisted fields (`cif`, `html`, `tex`, `pdf`, `style`,
`html_offline`) on `project.cif`, plus ad-hoc per-format
methods (`save_html()`, `save_cif()`, `save_tex()`,
`save_pdf()`). The Python-side `project.report.formats` is a
convenience property view over the four format booleans. The
accepted IUCr `project.save(report=True)` flag is **removed**;
reports come from the config category, not from boolean flags.
All four format booleans default to `False` so `project.save()`
writes nothing under `reports/` until the user configures
otherwise, preserving the "no surprise files" property.

Coordination points with the alignment ADR (no blocking conflicts;
its Open Questions section is empty):

- **Software-stack identification** — the alignment ADR's §2.3a-i
  defines `_easydiffraction_software.{framework, calculator, minimizer}`
  as the structured CIF emission, plus a concatenated
  `_computing.structure_refinement` free-text string. This ADR's §4
  adopts the same three-role triple as the Python-side attribute
  layout so the same data flows into both write paths.
- **Spec-compliance validation** — the alignment ADR's §2.5 added
  `project.report.check()` (gemmi-based) and a `check=True`
  flag on `project.report.save()`. This ADR **removes the public
  surface** and moves the gemmi pass to an internal pre-write
  step **inside the CIF emission paths only** — `save_cif()` and
  the `cif` branch under `project.save()` (§1.4). HTML, TeX, and
  PDF outputs are not gemmi-validatable and get no pre-write
  validation; LaTeX errors surface at PDF-compile time via the
  TeX engine. A writer that emits non-compliant CIF raises
  `EasyDiffractionWriterError` instead. This ADR's deferred
  `check_completeness()` (publication-side completeness) is a
  separate concern that stays in Deferred Work.
- **Publication metadata source** — the alignment ADR's Deferred
  Work proposes a user-supplied `reports/publ_info.{toml,json}`
  to replace `?` placeholders. Both write paths read the same
  Python attribute, **`project.publication`** — a new top-level
  on `Project`, sibling to `project.info` and `project.analysis`.
  The schema is defined in §5 of this ADR: six CIF-aligned
  sibling categories (`journal`, `journal_date`, `journal_coeditor`,
  `contact_author`, `body`, `authors`) with full IUCr-tag fidelity.
  The loader accepts TOML (primary) and JSON (fallback); selection
  is by file extension.

Also touches:

- [`analysis-cif-fit-state.md`](../accepted/analysis-cif-fit-state.md)
  — adds an `analysis.software` provenance category that serialises
  through the analysis tier.
- [`minimizer-input-output-split.md`](../accepted/minimizer-input-output-split.md)
  — the new provenance category lives alongside the existing
  minimizer/fit-result pairing, not inside it.
- [`project-facade-and-persistence.md`](../accepted/project-facade-and-persistence.md)
  — two changes: `project.report` gains a persisted
  configuration category (`_report.*` in `project.cif`, see §1.3),
  turning the facade into a hybrid of helper methods plus
  persisted config; and a new top-level `project.publication`
  owner is added alongside the existing `project.info`,
  `project.structures`, `project.experiments`,
  `project.analysis`, `project.report` facade slots (see §5).
- [`python-cif-category-correspondence.md`](python-cif-category-correspondence.md)
  — owns the Python↔CIF correspondence rule for **two** new
  project-level singleton surfaces:
  `project.report.* ↔ _report.*` (six scalar items, §1.3) and
  `project.publication.*` sibling categories ↔ `_journal.*`,
  `_publ_author.*`, `_publ_contact_author.*`, etc. (§5).

## Context

The library today has four shapes of summary output:

- `Report.show_report()` and friends — terminal/Jupyter rendering of
  project metadata, crystallographic data per phase, experimental
  configuration, and fit metrics
  ([report.py](../../../../src/easydiffraction/report/report.py)).
  (Pre-PR #184 this was `Summary.show_report()` on
  `project.summary`; the IUCr alignment ADR replaced the unimplemented
  placeholder.)
- `summary.cif` — was written into the project root on every
  `project.save()` as the literal string `"To be added..."` until
  PR #184 removed both the writer call and the placeholder method.
  Not a valid CIF block in any version that shipped.
- The old GUI's "Summary" tab — a single page listing project info,
  crystal data, data collection, refinement engine + goodness-of-fit,
  with an "Export summary" panel (Name, Format = HTML, Location).
- An eventual journal manuscript — currently produced by hand from the
  scientist's notes and the values shown in the GUI Summary tab.

These four are renderings of the **same** logical view. Every field
the GUI shows is already reachable from the live Python objects; the
summary is not a source of truth and has no field of its own that
isn't computable from `project`, its `structures`, its `experiments`,
and `analysis.fit_results`. The exception is software provenance —
which calculation engine and minimizer (with versions) produced the
fit — which the library does not currently capture anywhere.

Two pressures act on the design:

- **GUI consistency.** The library and the GUI must show the same
  numbers from the same data flow. The GUI Summary tab needs a
  programmatic API, not a CIF or an HTML file to re-parse.
- **Submission-grade output.** Scientists publish in IUCr journals,
  Phys. Rev. B, J. Appl. Cryst., and others. The CIF side of that is
  covered by the alignment ADR's IUCr export. The **manuscript**
  side (refinement tables formatted to journal style) is not.

The default-save `summary.cif` placeholder was the visible artefact
of the unresolved design question. The alignment ADR has since
replaced the unimplemented `project.summary` slot with a
`project.report` facade scoped to IUCr CIF generation
(`reports/<project>.cif`). That resolves the CIF half of the
question but leaves the GUI Summary tab, the terminal
`show_report()`, the human-readable HTML, and the manuscript-bound
LaTeX/PDF without a definition. This ADR fills the gap by extending
the same `project.report` facade with non-CIF rendering surfaces.

## Scope

In scope:

- Extend the alignment ADR's `project.report` facade with
  terminal/Jupyter, HTML, and LaTeX rendering surfaces, a
  configuration category (six scalar fields —
  `project.report.{cif, html, tex, pdf, style, html_offline}` —
  persisted in `project.cif`; `project.report.formats` is a
  property view over the four booleans), and ad-hoc per-format
  save methods. **All report formats are opt-in via the
  configuration; every format defaults to `False` so
  `project.save()` writes nothing under `reports/` until a
  format is enabled** — see §1 and §2 for the rationale.
- Define the shared "summary data context" (one dictionary) that
  terminal, HTML, LaTeX, and GUI renderers all consume.
- Add a Python-side software-provenance category on `analysis`
  (`analysis.software`) recording calculation-engine and
  minimization-engine name + version + URL stamped at fit time.
  Persisted in `analysis/analysis.cif` (amends the IUCr ADR's
  "Analysis — unchanged" stance for these fields; see §4 and the
  ADRs-amended list).
- Add a new top-level `project.publication` owner on `Project`
  (sibling to `project.info`, `project.structures`,
  `project.experiments`, `project.analysis`, `project.report`)
  carrying the `_publ_*` / `_journal_*` publication metadata
  the IUCr writer otherwise emits as `?` placeholders. See §5;
  amends `project-facade-and-persistence.md` and complements
  `python-cif-category-correspondence.md`.
- Sketch the journal-style selector hook for LaTeX (start with one
  style; add more by template, not by code change).

Out of scope:

- CIF tag-name decisions for any serialised field. Those are the
  alignment ADR's job; this ADR notes recommended mappings and
  cross-references.
- The IUCr CIF submission export tag policy and multi-datablock
  layout. Covered by the alignment ADR; the output file lives at
  `reports/<project>.cif` and is opt-in via
  `project.report.formats = ['cif', ...]`.
- Pre-existing project-level singleton categories (`_info.*`,
  `_chart.*`, `_table.*`, `_verbosity.*`). Covered by the
  in-flight
  [`python-cif-category-correspondence.md`](python-cif-category-correspondence.md).
  This ADR **does** add one new project-level singleton
  category, `_report.*`, alongside them (see §1.3 and the
  ADRs-amended list); that surface is not delegated to the
  correspondence ADR.
- Static-image PDF generation. HTML prints from any browser; LaTeX
  compiles to PDF locally. No bundled PDF writer.
- Markdown export. Trivial follow-on if the Jinja base templates are
  in place, but no current user requirement.

## Design Philosophy: Summary as a View

Summary is a **derived view**, not a persisted artifact. The same
data dictionary feeds every renderer:

```
project, structures[], experiments[], analysis.fit_results,
analysis.software           (new — see §4)
        │
        ▼
  ReportDataContext          (in-memory dict, single source of truth)
        │
        ├──► terminal/Jupyter renderer  (existing show_*; on demand)
        ├──► HTML renderer              (Jinja; opt-in via html_report)
        ├──► LaTeX renderer             (Jinja; opt-in via tex_report/pdf_report, style-selectable)
        └──► GUI Summary tab            (programmatic; eventual)
```

Render targets never duplicate the data — they consume the same
context. New summary fields are added in one place (the context
builder); every renderer picks them up.

## Decision

### 1. Extend `project.report` with rendering methods and a config category

The alignment ADR has already created the `project.report` facade
(replacing the unimplemented `project.summary` placeholder). This
ADR extends it along two axes:

- A new **configuration category** on `project.report` —
  persisted in `project.cif`, matching the existing
  `project.chart`, `project.table`, `project.verbosity` config
  pattern — that records *which* report formats `project.save()`
  emits and *how*.
- A new set of **ad-hoc per-format methods** for explicit
  one-off writes that bypass the configuration.

The accepted IUCr `project.save(report=True)` flag and the
public `project.report.check()` method are both **removed** (see
the ADRs-amended list). Reports come from configuration, not
boolean flags; dictionary-spec validation runs internally
before every CIF write (and only before CIF writes — HTML, TeX,
and PDF have no spec to validate against; see §1.4) and
surfaces as an error on writer bugs, not as a user opt-in.

#### 1.1 Configuration category — `project.report.*`

Persisted fields on `project.report`, populated by the user
once and read by `project.save()` thereafter:

| Field                       | Type         | Default   | Effect                                                                                                 |
| --------------------------- | ------------ | --------- | ------------------------------------------------------------------------------------------------------ |
| `project.report.cif`        | `bool`       | `False`   | When `True`, `project.save()` writes `reports/<project>.cif`.                                          |
| `project.report.html`       | `bool`       | `False`   | When `True`, `project.save()` writes `reports/<project>.html`.                                         |
| `project.report.tex`        | `bool`       | `False`   | When `True`, `project.save()` writes `reports/tex/{<project>.tex, figures/, styles/}`.                 |
| `project.report.pdf`        | `bool`       | `False`   | When `True`, `project.save()` writes `reports/<project>.pdf` (and `tex/` as a side-effect).            |
| `project.report.style`      | `str` (Enum) | `'iucr'`  | LaTeX style. Values: `'iucr'`, `'revtex'`. Only meaningful when `tex` or `pdf` is `True`.              |
| `project.report.html_offline` | `bool`     | `False`   | When `True`, the HTML report inline-bundles Plotly (~3 MB extra). Otherwise loads Plotly from CDN.     |

Four per-format scalar booleans (`cif`, `html`, `tex`, `pdf`)
plus two scalars (`style`, `html_offline`) — six fields total,
all single-row in CIF. Matches the existing `project.chart`,
`project.table`, `project.verbosity` scalar-config shape
verbatim. All booleans default to `False`, so an unconfigured
project produces no `reports/` directory at all.

For convenience, `project.report.formats` is exposed as a
**property view** — reading it returns a list of the
currently-`True` formats; assigning a list flips the four
booleans to match:

```python
project.report.formats               # → []
project.report.formats = ['cif', 'html']
project.report.cif                   # → True
project.report.html                  # → True
project.report.tex                   # → False
project.report.formats               # → ['cif', 'html']
```

The list view is the more idiomatic surface for "set of enabled
formats"; the booleans are what CIF persists. Both spellings are
equivalent and round-trip cleanly.

```python
import easydiffraction as ed

project = ed.Project()
# … set up structures, experiments, run fit …

# Configure once — persisted in project.cif (see §1.3 below).
# Either spelling works:
project.report.formats = ['cif', 'html']
# or, equivalently:
#   project.report.cif = True
#   project.report.html = True
project.report.style = 'iucr'
project.report.html_offline = False

# Every subsequent save now emits the configured reports too.
project.save()
# → project.cif (with _report.* config block)
# → structures/<...>.cif, experiments/<...>.cif, analysis/analysis.cif
# → reports/<project>.cif  (because project.report.cif is True)
# → reports/<project>.html (because project.report.html is True)
```

##### Enum backing per the closed-values ADR

Both the format set and the style selector are finite closed
sets, so per the accepted
[`enum-backed-closed-values.md`](../accepted/enum-backed-closed-values.md)
contract they are represented internally as `(str, Enum)`:

```python
class ReportFormatEnum(str, Enum):
    CIF = 'cif'
    HTML = 'html'
    TEX = 'tex'
    PDF = 'pdf'

class ReportStyleEnum(str, Enum):
    IUCR = 'iucr'
    REVTEX = 'revtex'
```

The four per-format booleans (`project.report.cif`, `.html`,
`.tex`, `.pdf`) carry one `ReportFormatEnum` member each as a
class-level constant identifying which format they enable. The
`project.report.style` setter accepts either an Enum member or
the string value (the project's existing convenience pattern);
dispatch and equality checks use enum members, not raw strings.
The `formats` property view returns a list of
`ReportFormatEnum` members (`[ReportFormatEnum.CIF,
ReportFormatEnum.HTML]`), which compare equal to the bare
string values for ergonomic user code (`'cif' in
project.report.formats` still works because `(str, Enum)`
inherits string equality).

CIF serialisation uses the enum string values verbatim
(`_report.style iucr`); the writer rejects any value not in the
declared enum at write-time, matching the gemmi pass's
dictionary-spec check.

#### 1.2 Ad-hoc per-format methods

Each format has its own explicit write method on the facade,
independent of `project.report.formats`. Use when a user wants
to produce a one-off artifact without changing the persistent
configuration.

```python
project.report.save_cif()                        # writes reports/<project>.cif
project.report.save_html(offline: bool = False)  # writes reports/<project>.html
project.report.save_tex(style: str = 'iucr')     # writes reports/tex/{<project>.tex, ...}
project.report.save_pdf(style: str = 'iucr')     # writes reports/<project>.pdf (compiles TeX too)

# Convenience: write everything currently in project.report.formats.
# Raises ValueError if no formats are configured (see below).
project.report.save()                            # reads config, no flags

# Ad-hoc string returns (unchanged from the earlier draft):
project.report.as_html(offline: bool = False) -> str
project.report.as_tex(style: str = 'iucr') -> str

# Shared data context (for GUI Summary tab + Jinja templates):
project.report.data_context() -> dict

# Terminal / Jupyter renderers (existing methods, migrated to
# project.report by PR #184 — names preserved):
project.report.show_report()              # full report — sections below
project.report.show_project_info()
project.report.show_crystallographic_data()
project.report.show_experimental_data()
project.report.show_fitting_details()
```

Per-format method signatures only carry the args that apply to
that format — `save_pdf(style='revtex')` is unambiguous; there
is no `save_html(style=...)` because HTML has no journal style.
The cross-format mixing that the earlier flag-based draft had
(`html_offline` ignored when `html=False`, `style=` ignored
without `tex=True`) is gone.

`project.save()` itself takes no report-related arguments. The
accepted IUCr `project.save(report=True)` flag is removed (see
ADRs amended); reports are configured on `project.report.*`.

```python
project.save()           # writes project files + whatever is in project.report.formats
```

`Summary.as_cif()` and `summary_to_cif()` were already deleted
by the alignment ADR; this ADR's removal of `project.save(report=True)`
finishes the flag-cleanup.

**Empty-configuration behaviour split.**

The two entry points behave differently when no formats are
enabled — a deliberate split: `project.save()` writes the
project regardless (reports are a side-effect of configuration,
not the point of the call); `project.report.save()` is *only*
about reports, so calling it with nothing configured is a user
error.

```python
# project.report.formats == []  (default — unconfigured)

project.save()
# → writes project.cif + structures/ + experiments/ + analysis/
# → reports/ is NOT created (no formats enabled — correct default
#   behaviour, no error, no warning).

project.report.save()
# → raises:
#   ValueError(
#       "project.report.save() called with no formats enabled. "
#       "Set project.report.{cif,html,tex,pdf} = True (or assign a "
#       "list via project.report.formats), or call a per-format "
#       "method directly (project.report.save_html(), etc.)."
#   )
```

The Python error matches the CLI's existing behaviour for
`ed save-report` with no flags (§7) — both surfaces refuse to
silently no-op when the user explicitly asked for a report.
`project.save()` keeps the no-report default because the user
asked to save the project, not the reports.

The per-format methods (`save_cif()`, `save_html()`, etc.)
never inspect `project.report.formats` — they always write
their format unconditionally. They are explicit one-offs.

#### 1.3 CIF persistence of the configuration

The configuration category serialises to `project.cif` next to
the other project-level singleton categories (`_info.*`,
`_chart.*`, `_table.*`, `_verbosity.*`). The CIF tag prefix is
`_report.*` — a Set category with six scalar items, no loops:

```text
data_<project>

# ---- Project info (from project-facade-and-persistence ADR) ----
_info.title          'Quartz at 300 K'
_info.description    'Refinement against XRD pattern xrd_300K.'
_info.created        2026-05-26T12:00:00
_info.last_modified  2026-05-26T15:42:00

# ---- Chart / table / verbosity selectors (existing config) ----
_chart.type          plotly
_table.type          plotly
_verbosity.fit       short

# ---- Report configuration (this ADR §1.3) ----
_report.cif           yes
_report.html          yes
_report.tex           no
_report.pdf           no
_report.style         iucr
_report.html_offline  no
```

All six items are scalar DDLm dotted entries — the category is
declared `_definition.class Set` so a single value per item, no
loops permitted. Matches the existing `_chart.*`, `_table.*`,
`_verbosity.*` category shape exactly. The `yes`/`no` boolean
encoding follows the project's existing CIF boolean convention.

The default unconfigured state writes four explicit `no` values
(not an absent or empty representation), so the "no formats
enabled" condition is always a concrete CIF value, never an
empty loop or missing block:

```text
# Default (project.report.formats = []):
_report.cif           no
_report.html          no
_report.tex           no
_report.pdf           no
_report.style         iucr
_report.html_offline  no
```

Load semantics are symmetric: every `no` reads back as `False`
on its descriptor; the `formats` property view returns `[]`.

The four per-format booleans give the IUCr-aware tooling
(`gemmi`, `publCIF`) a typed, validatable view of the
configuration — each format is a known enum item with type
`Boolean`, not a parsed string. The Python list view
(`project.report.formats`) is a convenience computed from these
four booleans at access time; it has no separate CIF storage.

Adding a new format in the future (e.g. `markdown`) is a
one-line schema extension: add `_report.markdown` to the
dictionary and a `project.report.markdown` boolean to the
descriptor. The list property picks it up automatically.

Loading a `project.cif` populates `project.report.*` per the
project-facade-and-persistence contract; on the next
`project.save()`, the configured formats emit automatically with
no further user action.

##### Why not its own CIF file?

The project already has two distinct facade patterns for
top-level `project.*` slots, used deliberately for different
purposes. `project.report` is **Pattern A** — lightweight
project-level singleton config — not Pattern B — heavy datablock
owner with its own CIF file. The split is summarised below.

| Slot                                   | Pattern | CIF location                                | Python shape                                                |
| -------------------------------------- | ------- | ------------------------------------------- | ----------------------------------------------------------- |
| `project.info`                         | A       | `project.cif` (`_info.*`)                   | small `CategoryItem`                                        |
| `project.chart`                        | A       | `project.cif` (`_chart.*`)                  | `CategoryItem` (one field)                                  |
| `project.table`                        | A       | `project.cif` (`_table.*`)                  | `CategoryItem` (one field)                                  |
| `project.verbosity`                    | A       | `project.cif` (`_verbosity.*`)              | `CategoryItem` (one field)                                  |
| **`project.report`** (this ADR)        | **A**   | **`project.cif` (`_report.*`)**             | **`CategoryItem` (six fields) plus action methods**         |
| `project.publication` (this ADR, §5)   | A       | `project.cif` (`_publ_*` / `_journal_*`)    | `CategoryOwner` of six sibling categories                   |
| `project.analysis`                     | B       | `analysis/analysis.cif`                     | `CategoryOwner` (heavy datablock)                           |
| `project.structures[name]`             | B       | `structures/<name>.cif`                     | `CategoryOwner` (heavy datablock)                           |
| `project.experiments[name]`            | B       | `experiments/<name>.cif`                    | `CategoryOwner` (heavy datablock)                           |

Reasons `project.report` is Pattern A, not Pattern B:

- Six scalar config items do not justify a separate file
  (`reports/report.cif` would be a tiny file holding six lines).
- A `reports/report.cif` would force the `reports/` directory to
  exist even when every format boolean is `False` and no reports
  are written — breaks the "no surprise files" property the
  design is built around.
- Splits report configuration from chart / table / verbosity
  configuration, which already share `project.cif` for the same
  reason — they are all project-level preferences, not domain
  data.

What makes `project.report` look heavier than `project.chart` /
`project.table` / `project.verbosity` is the action methods on
the facade (`save_cif()`, `save_html()`, `show_report()`,
`data_context()`, etc.). Those live on the Python class
alongside the configuration fields, which is the facade-hybrid
amendment to `project-facade-and-persistence.md` already
recorded in the ADRs-amended list. The action methods do not
change where the configuration persists — that stays in
`project.cif`.

#### 1.4 Validation moves internal — CIF only, writer-correctness only

The accepted IUCr ADR §2.5 exposed `project.report.check()` and
a `check=True` flag for gemmi-based dictionary-spec validation.
Both are **removed** in favour of a pre-write self-check inside
the CIF emission paths only:

```text
project.save()
  └─ for each enabled format:
       ├─ build the format content
       ├─ if format ∈ {cif}:  run gemmi against the content
       │    └─ on failure → raise EasyDiffractionWriterError
       │                    pointing at the malformed tag,
       │                    with a "please file a bug" hint.
       ├─ if format ∈ {html, tex, pdf}: no pre-write validation
       │                                 — see scope below.
       └─ atomically write the file
```

**Scope split — what is validated and how:**

| Output                  | Validation                                                | Failure mode                                                              |
| ----------------------- | --------------------------------------------------------- | ------------------------------------------------------------------------- |
| `reports/<project>.cif` | gemmi against `cif_core.dic` / `cif_pow.dic`              | `EasyDiffractionWriterError` (writer bug — file an issue)                  |
| `reports/<project>.html` | none at write time                                       | n/a — HTML is a render of the data context, not a typed format             |
| `reports/tex/`           | none at write time                                       | n/a — LaTeX errors surface at PDF-compile time, with the engine's message  |
| `reports/<project>.pdf`  | TeX engine's own compilation (returns non-zero on error) | engine-specific message; the `.tex` and figures are still written          |

User-input validation (e.g., "is the email address syntactically
valid?", "is the ORCID well-formed?") happens **upstream** at
the descriptor's `value_spec` validator — the same boundary
where every other user input is checked. That's a separate
concern from the writer self-check above: descriptor validators
raise `typeguard.TypeCheckError` or the project's
`ValidationError` at *assignment time*, before any save is
attempted. By the time the writer runs, the values it receives
are already shape-correct; the gemmi pass on the CIF output
catches *writer* bugs (wrong tag, wrong type, malformed loop),
not user bugs.

Rationale: dictionary compliance is a *writer-correctness*
property, not a user choice. A user can't fix a non-compliant
emission without modifying project state — and even then, the
writer should refuse to emit a malformed file in the first
place. Making validation a user-visible API surface invites
users to skip it; making it internal makes it impossible to
skip. Cached dictionary parsing keeps the overhead to a one-time
~200 ms session cost. The `EasyDiffractionWriterError` includes
the full gemmi diagnostic so bug reports are actionable.

A separate, *completeness*-oriented check
(`project.report.check_completeness()`) — flagging unfilled
`_publ_*` / `_journal_*` placeholders for journal submission,
which is a publication-readiness question rather than a
writer-correctness one — is a different concern and stays in
Deferred Work.

### 2. HTML report — config-driven via `project.report.formats`

`'html' in project.report.formats` causes `project.save()` to
write `reports/<project>.html`. The empty default
(`formats = []`) keeps `reports/` from being touched at all on
plain `project.save()`. For one-off HTML without changing the
persistent config, call `project.report.save_html()` directly.

```python
# Persistent — every subsequent save writes the HTML report.
project.report.formats = ['html']
project.report.html_offline = False    # CDN-Plotly (default)
project.save()                         # → reports/<project>.html

# Persistent + air-gapped readers — inline-bundle Plotly.
project.report.html_offline = True
project.save()                         # → reports/<project>.html (~3 MB)

# One-off, ignoring config.
project.report.save_html()                 # CDN-Plotly
project.report.save_html(offline=True)     # inline bundle
```

Plotly bundle modes:

- **CDN mode (default)** — `include_plotlyjs='cdn'`. File size
  ~50-300 KB depending on chart count. Requires internet to view.
- **Offline mode** (`project.report.html_offline = True` or
  `save_html(offline=True)`) — `include_plotlyjs=True`. Adds
  ~3 MB per HTML. Use when readers are air-gapped or when the
  user wants to archive a fully self-contained report.

`reports/` is created lazily — only when at least one format is
configured (or an ad-hoc method is called). A user iterating on
a fit with the default `formats = []` produces no extra files.

Rationale for the config category (replacing the earlier
flag-based and "auto on every save" positions):

- Reports are a *project preference*, not a per-call argument.
  `project.chart.type`, `project.table.type`,
  `project.verbosity.fit` follow the same pattern — set once,
  persisted in `project.cif`, applied on every save.
- `project.save()` has one job: save the project. With
  `formats = []` the report behaviour is unchanged from before
  this ADR; with `formats = ['html']` HTML appears on every
  save without needing a flag on each call.
- The GUI's Summary tab consumes `project.report.data_context()`
  in-memory, not the HTML file — so the GUI-consistency story
  does not depend on the HTML file existing at any particular
  moment.
- No new dependencies for HTML: `plotly`, `jinja2`, `pandas`
  are already declared in
  [pyproject.toml](../../../../pyproject.toml).

Content (one HTML page per project — per-project granularity matches
the IUCr "one CIF per article" convention):

- Project info — title, description, phase count, experiment count.
- Crystal data per phase — phase id, space group, cell parameters,
  atom-sites table.
- Data collection per experiment — experiment id, type fields,
  measured range + number of points. Per-experiment sections are
  anchor-linkable for navigation.
- Refinement — calculation engine + version + URL, minimization
  engine + version + URL, goodness-of-fit, parameter counts
  (total/free/fixed), constraint count.
- Fit charts per experiment — Plotly figures embedded inline via
  `fig.to_html(include_plotlyjs=<cdn|True>)`. Reuses the existing
  `display/plotters/plotly.py` figures.
- Footer — EasyDiffraction version, save timestamp.

### 3. LaTeX + figures + PDF — config-driven via `project.report.formats`

LaTeX is a **publish-time** artifact. `'tex'` and `'pdf'` are
added to `project.report.formats` when the user wants them.
`project.report.style` selects the journal style — only
meaningful when `'tex'` or `'pdf'` is in `formats` (or when an
ad-hoc method is called); HTML and CIF have no style choice.

```python
# Persistent — every save writes TeX + assets.
project.report.formats = ['tex']
project.report.style = 'iucr'
project.save()                              # → reports/tex/{...}

# Persistent — every save writes the compiled PDF too.
project.report.formats = ['tex', 'pdf']
project.save()                              # → reports/tex/{...} + reports/<project>.pdf

# Persistent — switch style.
project.report.style = 'revtex'
project.save()                              # → reports/tex/{...} (REVTeX class)

# One-off, ignoring config.
project.report.save_tex(style='iucr')       # TeX + figures + styles only
project.report.save_pdf(style='revtex')     # TeX + PDF (PDF implies TeX)

# Ad-hoc string return.
project.report.as_tex(style='iucr') -> str
```

**`'pdf' in formats` implies the TeX source is also written** —
a PDF without the editable `.tex` source is useless if the user
wants to tweak before re-compiling. Asking for the PDF always
writes the TeX next to it. Equivalently, `save_pdf()` writes
the TeX assets as a side-effect.

Future `project.report.html_style` (dark mode, journal-mimicking
HTML layout) can land separately without collision because it
lives in the config category, not in a method signature.

#### 3.1 Folder layout

Per-project filenames (`<project>.{cif,html,pdf}`) share a root in
`reports/`; the LaTeX source plus its assets sit in `reports/tex/`.
Single-style today; multi-style ships all class files together so
the user can swap styles by editing one line in `<project>.tex` and
rebuilding the PDF.

**Full reports/ tree when all formats are configured.**
`project.report.formats = ['cif', 'html', 'tex', 'pdf']`:

```
<project_root>/
  reports/                          # populated by project.save() per config
    <project>.cif                   # ← 'cif' in project.report.formats (alignment ADR §2)
    <project>.html                  # ← 'html' in project.report.formats (this ADR §2)
    <project>.pdf                   # ← 'pdf' in project.report.formats (this ADR §3.4)
    tex/                            # ← 'tex' or 'pdf' in project.report.formats (this ADR §3)
      <project>.tex                 #   main document; tables, \includegraphics figures
      figures/
        fit_<expt_id>.pdf           #   one per experiment, vector PDF (kaleido)
      styles/                       #   always-bundled — minimum to compile both styles
        iucrjournals.cls            #     IUCr unified class (CC0 1.0)
        harvard.sty                 #     IUCr companion bibliography style
        revtex4-2.cls               #     REVTeX class (LPPL 1.3c)
        ltxgrid.sty                 #     REVTeX page-grid dep
        ltxutil.sty                 #     REVTeX utilities dep
        ltxfront.sty                #     REVTeX front-matter dep
        ltxdocext.sty               #     REVTeX document-ext dep
        revsymb4-2.sty              #     REVTeX symbols
        aps4-2.rtx                  #     REVTeX: APS journals (PRB, PRA, PRL, PRD)
        aps10pt4-2.rtx              #     REVTeX: 10pt font size
        aps11pt4-2.rtx              #     REVTeX: 11pt font size
        aps12pt4-2.rtx              #     REVTeX: 12pt font size
                                    # 12 files, ~420 KB. AIP/AAPM/SOR/RMP .rtx and
                                    # all .bst BibTeX files excluded; see §3.2.1.
```

**Examples by configuration.**

`project.report.formats = []` (default — nothing written):

```
<project_root>/
  project.cif                       # _report.{cif,html,tex,pdf} = no
  structures/<...>.cif
  experiments/<...>.cif
  analysis/analysis.cif
  # reports/ directory does not exist
```

`project.report.formats = ['cif']` (journal-submission CIF only):

```
<project_root>/
  project.cif
  structures/<...>.cif
  experiments/<...>.cif
  analysis/analysis.cif
  reports/
    <project>.cif                   # IUCr-aligned, multi-datablock (alignment ADR §2.3)
```

`project.report.formats = ['html']` + `html_offline = True`
(self-contained inspection page):

```
<project_root>/
  project.cif
  structures/<...>.cif
  experiments/<...>.cif
  analysis/analysis.cif
  reports/
    <project>.html                  # ~3 MB, Plotly inlined
```

`project.report.formats = ['cif', 'html', 'pdf']`
+ `style = 'iucr'` (typical pre-submission bundle):

```
<project_root>/
  project.cif
  structures/<...>.cif
  experiments/<...>.cif
  analysis/analysis.cif
  reports/
    <project>.cif                   # journal-submission CIF
    <project>.html                  # interactive inspection page
    <project>.pdf                   # IUCr-style typeset refinement table
    tex/                            # source for the PDF (kept editable)
      <project>.tex
      figures/fit_<expt_id>.pdf
      styles/iucrjournals.cls       # only the IUCr files are referenced;
      styles/harvard.sty            # the REVTeX files still ship in the bundle
      ...                           # so the user can swap style with one edit
```

`reports/` is created lazily — only when at least one format
sits in `project.report.formats` (or an ad-hoc method is called).
The `tex/`, `tex/figures/`, and `tex/styles/` subfolders appear
only when `'tex'` or `'pdf'` is in `project.report.formats` (or
`save_tex()` / `save_pdf()` is invoked).

The `<project>` portion of every filename comes from
`project.info.name` verbatim (e.g. a project named
`La0.5Ba0.5CoO3_HRPT` produces `reports/La0.5Ba0.5CoO3_HRPT.html`).
Only filesystem-dangerous characters (path separators, control
chars) are sanitized; case, dots, underscores, and parentheses are
preserved so the user recognises their project name in the file
listing.

#### 3.2 Style selection — two slugs (`iucr`, `revtex`), mixed bundling strategy

Two style slugs ship in v1:

| Slug              | Class file            | Default `\documentclass`             | License        | Distribution                          |
| ----------------- | --------------------- | ------------------------------------ | -------------- | ------------------------------------- |
| `iucr` (default)  | `iucrjournals.cls`    | `\documentclass{iucrjournals}`       | CC0 1.0        | Bundled in wheel (no CTAN package)    |
| `revtex`          | `revtex4-2.cls`       | `\documentclass[prb]{revtex4-2}`     | LPPL 1.3c      | Bundled in wheel (also on CTAN `revtex`) |

The two styles differ in **how the sub-journal is selected**:

- **`iucr` is a unified class.** `iucrjournals.cls` does not use
  document-class options. The same class is used across all IUCr
  journals (Acta Cryst E/B/C/D/F, J. Appl. Cryst.,
  J. Synchrotron Rad., IUCrData) — the sub-journal designation
  is decided at submission via IUCr's web form, not in the `.tex`.
- **`revtex` uses an option letter.** `\documentclass[prb]{revtex4-2}`
  for Phys. Rev. B; the user changes the letter (`pra`, `prl`,
  `prd`, `reprint`, …) to swap sub-journal and rebuilds. The
  library emits a comment block immediately above the
  `\documentclass` line listing the alternatives:

  ```latex
  % Change the option letter to target a different APS journal:
  %   prb     = Phys. Rev. B   [default]
  %   pra     = Phys. Rev. A
  %   prl     = Phys. Rev. Letters
  %   prd     = Phys. Rev. D
  %   reprint = generic reprint format
  \documentclass[prb]{revtex4-2}
  ```

Unknown slugs raise `ValueError(f"Unknown style: {style!r}. "
"Supported: 'iucr', 'revtex'")` — explicit failure beats a silent
fallback.

**Distribution: bundle every style every time.**

`reports/tex/styles/` is populated with the **full set of supported
styles** on every report save — both `iucr` and `revtex` files,
regardless of which slug the user picked. The selected style's
class is `\input` by `<project>.tex`'s `\documentclass{...}` line;
the other style's files sit alongside, ready for a one-line swap.

Rationale:

- Self-contained `reports/tex/` — can be zipped or emailed to a
  co-author who doesn't have EasyDiffraction, rebuilt anywhere
  with a TeX engine.
- Style swap is a `<project>.tex` edit, not a library
  round-trip. Matches the workflow established earlier in
  ADR review.
- No dependency on user's TeX install having `revtex` installed,
  no dependency on tectonic having internet access at compile
  time.
- Single mental model: `tex/styles/` always contains the same set
  of files; not "depends on what you asked for".

Total footprint per save: ~420 KB across 12 files (IUCr ~20 KB +
REVTeX ~400 KB, default APS journal coverage only). Negligible
against the project's data files, the compiled PDF, and the HTML
report. See §3.2.1 for the file list and what's deliberately
excluded.

#### 3.2.1 Source provenance and bundled files

Both upstream sources are vendored under
`src/easydiffraction/report/styles/` in the repository and copied
into `reports/tex/styles/` on report save. Download URLs, dates,
licenses, and file lists below; the implementation plan refreshes
the vendored snapshot when upstream releases a new version.

**IUCr** (`iucrjournals.cls`)

- Source: https://journals.iucr.org/j/services/latexstyle.html
- Snapshot downloaded: 2026-05-26
- License: CC0 1.0 Universal (public domain dedication); declared
  in the `iucrjournals.cls` file header.
- Files included (2):
  - `iucrjournals.cls` — unified IUCr class
    (11 KB, dated 2024-12-02).
  - `harvard.sty` — bibliography style; required by
    `iucrjournals.cls` via `\RequirePackage{harvard}`
    (9 KB, Peter Williams, 2001-10-25).
- Files excluded: `iucr.bib`, `iucr.bst`, `fig1.png`,
  `template.tex` (bibliography / example assets, not needed for
  the refinement-table use case).

**REVTeX 4.2** (`revtex4-2.cls`)

- Sources:
  https://journals.aps.org/revtex (canonical, APS) and
  https://ctan.org/pkg/revtex (CTAN mirror).
- Snapshot downloaded: 2026-05-26 (REVTeX 4.2f, 2022-06-05).
- License: LPPL 1.3c; declared in the `revtex4-2.cls` file
  header (Copyright APS 1999–2022, derived from Arthur Ogawa's
  original v4.0).
- Files included (10 — the minimum to compile the default PRB
  output and let the user swap among PRB/PRA/PRL/PRD via
  documentclass option):
  - Class: `revtex4-2.cls` (203 KB).
  - Companion `.sty` (all loaded by `revtex4-2.cls` via
    `\RequirePackage`): `ltxgrid.sty` (74 KB), `ltxutil.sty`
    (55 KB), `ltxfront.sty` (30 KB), `ltxdocext.sty` (10 KB),
    `revsymb4-2.sty` (6 KB).
  - APS journal config: `aps4-2.rtx` (16 KB) — covers
    PRB / PRA / PRL / PRD via documentclass options.
  - Font-size configs: `aps10pt4-2.rtx`, `aps11pt4-2.rtx`,
    `aps12pt4-2.rtx` (5 KB each).
- Files excluded:
  - `apsrmp4-2.rtx` (Rev. Mod. Phys. — defer until a user
    asks).
  - `aip4-2.rtx`, `aapm4-2.rtx`, `sor4-2.rtx` (AIP, AAPM,
    Society of Rheology — out of the typical condensed-matter /
    diffraction audience; defer).
  - `bibtex/bst/revtex/*.bst` (BibTeX styles — refinement
    appendix has no citations).
  - `doc/latex/revtex/*` (documentation).

Both license texts (CC0 1.0 and LPPL 1.3c) are copied into the
package's licensing documentation alongside the wheel's
BSD-3-Clause `LICENSE`, with attribution to APS and Peter Williams
where the file headers carry it.

Template content for `style='iucr'` (unified IUCr class):

- Refinement-data table in the journal's conventional layout (cell
  parameters with uncertainties, space group, refinement
  statistics, parameter counts, R-factors).
- Atom-site fractional-coordinate table.
- Anisotropic ADP table (when anisotropic ADPs present).
- Per-experiment fit figure via
  `\includegraphics{figures/fit_<expt_id>.pdf}` with the figure
  caption rendered from the experiment metadata.

#### 3.3 Static-image generation — kaleido (same Plotly figures as HTML)

LaTeX figures are produced by the **same Plotly figure objects**
that the HTML report embeds, rendered to vector PDF via Plotly's
official static-image backend `kaleido`:

```python
fig = build_fit_figure(experiment, fit_results)   # existing plotly path
fig.write_html(...)                                # → reports/<project>.html (interactive)
fig.write_image('reports/tex/figures/fit_<id>.pdf')   # → kaleido → vector PDF
```

The HTML's interactive Plotly chart and the LaTeX's static PDF
come from the **same Plotly figure specification rendered by
the same Plotly engine** (kaleido shares Plotly.js with the
browser-side renderer). They are visually consistent — same
trace shapes, same colour mapping, same axis layout — though
exact pixel equality across an interactive HTML target and a
static PDF export cannot be guaranteed (font hinting, anti-
aliasing, and DPI handling differ between the browser and
kaleido's headless Chromium). Sharing the figure spec is
nevertheless the core argument for picking kaleido over a
second rendering toolkit: any visual difference is constrained
to rendering-stack quirks, not data choices.

**`kaleido` v1.0+ is the chosen release line.** Rationale:

- v1 is the actively maintained line upstream. Bug fixes and
  security patches land here; the v0.2 line is in legacy
  maintenance.
- Pinning a project's long-term static-image pipeline to a legacy
  release just to dodge a runtime browser dependency is the wrong
  trade-off — the migration debt accumulates and the runtime gap
  closes naturally as Chrome/Chromium becomes near-universal.
- v1's ~30 MB footprint is genuinely smaller than v0.2's ~80 MB
  bundled-Chromium build.
- The runtime browser requirement is handled by a system-browser
  fast path plus Kaleido's own one-time bootstrap, rather than a
  project-level Pixi dependency: conda-forge does not provide a
  `chromium` package for the workspace's supported platforms.
  Machines with Chrome, Chromium, or Edge installed need no extra
  step. Machines without one can run
  `python -c "import kaleido; kaleido.get_chrome()"` once to
  download Kaleido-managed Chromium into the user cache. The
  report path raises a clear hint for that setup when static-image
  export cannot find a browser. This differs from the
  LaTeX-engine install in §3.4, where `tectonic` is available on
  conda-forge.

Practical install matrix:

| Environment              | kaleido v1 install     | Browser already present? | Extra step                   |
| ------------------------ | ---------------------- | ------------------------ | ---------------------------- |
| Developer laptop         | `pip install kaleido`  | Usually yes (Chrome/Chromium/Edge) | None when present |
| `pixi` dev shell         | added through editable install | System browser preferred | Run `python -c "import kaleido; kaleido.get_chrome()"` once if absent |
| CI runner (GitHub, etc.) | added through editable install | Runner-dependent         | Add the same one-line bootstrap before report-export checks |
| Bare HPC node            | `pip install kaleido`  | Usually no               | Bootstrap once where cache/network policy allows, or install a system browser |

**Dependencies named by this ADR.** The implementation plan must
name two dependencies before any `/draft-impl-1` or
`/draft-impl-2` invocation edits `pyproject.toml`, `pixi.toml`, or
`pixi.lock`:

- `kaleido` (v1.0+) — Python package, runtime dependency for
  rasterising Plotly figures to vector PDF for LaTeX inclusion.
- `tectonic` — pixi/conda package, lightweight TeX engine for §3.4
  PDF compilation in the project dev environment.

`chromium` is deliberately not a dependency: conda-forge has no
package with that name for the supported workspace platforms. The
implementation treats Chrome/Chromium/Edge as the fast path and
reports a clear install hint that points to Kaleido's one-time
`get_chrome()` bootstrap when static-image export cannot find a
browser.

Per AGENTS.md §Architecture, "an accepted plan that **names the
specific dependency** … combined with the user invoking
`/draft-impl-1` or `/draft-impl-2` for that plan … counts as
pre-approval." This ADR does **not** itself pre-approve the
dependency edits; the plan does. The ADR names them here so the
plan author has the canonical list and the implementer can edit
dependency files autonomously once the plan is accepted and the
implementation shortcut is invoked.

#### 3.4 PDF compilation — opportunistic subprocess call

No pure-Python LaTeX compiler exists in practice (TeX is a large C
codebase; reimplementing it pure-Python is not realistic). The
library calls out to an external TeX engine if one is available on
`PATH`, in this preference order:

1. **`tectonic`** — modern Rust-based single-binary TeX engine,
   auto-downloads packages on first use, available on conda-forge.
   First-class fit for `pixi`/`conda` users.
2. **`latexmk`** — TeX Live's standard front-end; handles
   multi-pass compilation. Conda-forge package
   `texlive-core` ships it on Linux/macOS.
3. **`pdflatex`** — bare TeX Live engine, used as a single-pass
   fallback. The Acta Cryst E refinement-table template has no
   bibliography, so one pass suffices.

Behaviour:

- If any of the three is on `PATH`, the PDF is compiled from
  `reports/tex/<project>.tex` and written to
  `reports/<project>.pdf` (one directory up from the .tex source).
  Promoting the compiled artifact to `reports/` keeps the
  filename-root trio (`.cif`, `.html`, `.pdf`) co-located.
- If none is found, the `.tex`, `figures/`, and `styles/` are still
  written; the save log emits a single clear warning, for example:

  ```
  PDF skipped: no TeX engine on PATH.
  Install one with:
    pixi add tectonic         # recommended (conda-forge)
    conda install -c conda-forge tectonic
    # or any TeX Live distribution (latexmk / pdflatex)
  Then re-run project.save() (with 'pdf' in project.report.formats)
  or project.report.save_pdf().
  ```

The library does not bundle a TeX distribution — TeX Live is
multi-GB and pulling it through pip is not feasible. Tectonic is
the lightest realistic install (~50 MB single binary; downloads
packages on demand into a user cache).

**Project-side dev environment.** The project's own `pixi.toml`
gains `tectonic` in a `[feature.docs.dependencies]` (or similar)
group so CI and `pixi run script-tests` can validate PDF
generation end-to-end. End-users picking the library up via plain
`pip install easydiffraction` get the warning path until they
install a TeX engine themselves.

### 4. Software-provenance category on `analysis`

New category `analysis.software`, stamped at fit time, recording the
runtime engine identities. Structure mirrors the alignment ADR's
`_easydiffraction_software.{framework, calculator, minimizer}` triple
so one Python attribute feeds both default save and IUCr export:

```python
analysis.software.framework.name       # str, 'EasyDiffraction'
analysis.software.framework.version    # str, e.g. '0.17.0'
analysis.software.framework.url        # str, project URL

analysis.software.calculator.name      # str, e.g. 'cryspy'
analysis.software.calculator.version   # str, e.g. '1.2.3'
analysis.software.calculator.url       # str

analysis.software.minimizer.name       # str, e.g. 'lmfit'
analysis.software.minimizer.version    # str, e.g. '1.0.0'
analysis.software.minimizer.url        # str

analysis.software.timestamp            # ISO-8601, UTC
```

These are populated automatically by `Analysis.fit()` immediately
before the fit returns success — never by the user.

**Persistence and rendering paths (split):**

- **Default save** (`analysis/analysis.cif`) — written as the
  `analysis.software` category with all nine identity fields plus
  the timestamp. Round-trippable on load. This is the change to
  the accepted IUCr ADR's "Analysis — unchanged" stance on
  software identification; see the ADRs-amended list below for
  the explicit amendment.
- **IUCr export** (`reports/<project>.cif`, alignment ADR §2.3a-i)
  — the `name + version` portion of each role is read **from**
  `analysis.software` (instead of being constructed inline from
  project state, as the alignment ADR's §2.3a-i originally
  specified) and surfaces as
  `_easydiffraction_software.{framework, calculator, minimizer}`
  in `data_global`, plus the concatenated
  `_computing.structure_refinement` free-text string. The
  `timestamp` surfaces as a project-extension
  `_easydiffraction_software.fit_datetime` — **not**
  `_audit.creation_date`, which the accepted IUCr writer already
  uses for the report file's own creation time (see
  `_iso_creation_datetime` in
  [`iucr_writer.py`](../../../../src/easydiffraction/io/cif/iucr_writer.py)).
  Fit time and report-generation time are different events and
  must not collide on the same tag. **URLs are not part of the IUCr export** — they're
  a rendering concern, not a publication-CIF field. Output goes
  to `reports/<project>.cif` (the alignment ADR's canonical
  location; the directory is `reports/`, not `iucr/`).
- **Rendered documents** (`reports/<project>.html`,
  `reports/tex/<project>.tex`) — render the full
  `name — version — url` triple per role, with URLs as hyperlinks in
  HTML and as `\href{}{}` in LaTeX. Matches the old GUI's
  "Calculation engine: CrysPy — https://www.cryspy.fr" row layout.

**Engine `url` is a class-level constant on each backend.** Both
`CalculatorBase` and `MinimizerCategoryBase` subclasses declare a
`url: str` class attribute pointing at the upstream library's
documentation. Explicit, no surprises, no runtime lookup needed.

```python
class CryspyCalculator(CalculatorBase):
    url = 'https://www.cryspy.fr'
    # ...

class CrysfmlCalculator(CalculatorBase):
    url = 'https://code.ill.fr/scientific-software/crysfml'
    # ...

class PdffitCalculator(CalculatorBase):
    url = 'https://www.diffpy.org/products/pdffit2.html'
    # ...

class LmfitMinimizer(MinimizerCategoryBase):
    url = 'https://lmfit.github.io/lmfit-py'
    # ...

class EmceeMinimizer(MinimizerCategoryBase):
    url = 'https://emcee.readthedocs.io'
    # ...
```

`Analysis.fit()` reads `experiment.calculator.url` and
`analysis.minimizer.url` to populate the
`analysis.software.{calculator,minimizer}.url` fields. Version
strings come from `<library>.__version__` at fit time. Both are
recorded once, in the snapshot — the engine library can upgrade
later without rewriting the recorded fit's provenance.

Persistence:

- Default save: written to `analysis/analysis.cif` under category
  names this ADR proposes the alignment ADR adopts in its analysis
  tier (see below). Round-trippable; surfaces as `analysis.software`
  on load.
- HTML/LaTeX rendering: the `Refinement` section reads `analysis.software`
  directly and prints `<engine> <version> — <url>` per the
  old GUI's row format.

**CIF serialisation — reuses the accepted IUCr ADR's tag set,
plus one new fit-time-stamp tag.** Existing IUCr-export tag
names are owned by the alignment ADR §2.3a-i and are reused
here verbatim. One additional project-extension tag —
`_easydiffraction_software.fit_datetime` — is introduced by
this ADR to avoid colliding with the writer's existing
`_audit.creation_date` (which records report-generation time,
not fit time); it is registered as an IUCr amendment in the
ADRs-amended list below.

- Framework, calculator, minimizer roles →
  `_easydiffraction_software.{framework, calculator, minimizer}`
  in `data_global`, plus the concatenated
  `_computing.structure_refinement` free-text string. See
  [`cif_core.dic`](../../../../tmp/iucr-dicts/cif_core.dic) for
  the standard `_computing.structure_refinement` slot.
- Fit-time timestamp → `_easydiffraction_software.fit_datetime`
  (project-extension tag in `data_global`). The IUCr writer's
  own `_audit.creation_date` keeps its existing report-creation
  semantics from
  [`iucr_writer.py`](../../../../src/easydiffraction/io/cif/iucr_writer.py)
  and is not overwritten.
- EasyDiffraction's own version is bundled into the
  framework string and into the
  `_computing.structure_refinement` rendering per the IUCr
  convention; not a separate tag.

No new minimization-engine tag (e.g.
`_easydiffraction_computing.minimization_engine`) is introduced
— the alignment ADR's existing `…software.minimizer` already
covers that role. The only new IUCr-export item is
`_easydiffraction_software.fit_datetime` (see the CIF-serialisation
preamble above and the ADRs-amended list); it extends the
existing `_easydiffraction_software.*` category, not a new
top-level extension namespace. The Python-side `analysis.software`
category feeds both the established triple and the new fit-time
tag; the IUCr-export emission stays under the alignment ADR's
control.

#### 4.1 Missing-provenance behaviour

`analysis.software` is populated by `Analysis.fit()` just before
a successful return — pre-fit calls, failed fits, and projects
loaded from a save predating this ADR all start out **without**
the snapshot. The public API surface treats missing provenance
uniformly:

- **Rendering (`project.report.show_report()`, HTML, TeX).** Each
  role-row prints `"(not available)"` for `name`, omits version
  and URL, and adds a one-line footer "Software-provenance
  snapshot not yet recorded — call `Analysis.fit()` once to
  populate." No warning, no exception; the report still renders
  end-to-end so users iterating on a configuration before fitting
  see the rest of the page.
- **IUCr CIF export (`'cif' in project.report.formats`).** The
  `_easydiffraction_software.{framework, calculator, minimizer}`
  triple emits `?` placeholders consistent with the IUCr ADR's
  unset-field convention. The derived
  `_computing.structure_refinement` string falls back to
  `"EasyDiffraction <version>"` (framework only). The
  `_easydiffraction_software.fit_datetime` tag is omitted
  entirely (no `?` — the absence is the signal).
- **Internal validation (the §1.4 pre-write gemmi pass).** Does
  **not** detect missing provenance. The gemmi pass validates
  that emitted tags and types match the IUCr core / pdCIF
  dictionaries, and it explicitly skips the
  `_easydiffraction_*` extension namespace. So the
  fallback-filled `_computing.structure_refinement`
  (`"EasyDiffraction <version>"`) is not flagged as missing —
  it's a valid string — and the `?` placeholders on
  `_easydiffraction_software.{framework, calculator,
  minimizer}` are not flagged either, because gemmi does not
  validate the extension namespace. Detecting "publication-grade
  provenance is incomplete" is a different concern from
  dictionary-spec compliance and falls to the deferred
  `project.report.check_completeness()` listed in Deferred
  Work. Users who must guarantee complete provenance before
  submission should run that check (once it lands) or inspect
  the rendered report manually.
- **Old projects.** Loading a project saved before this ADR
  produces an `analysis.software` with all fields unset and the
  timestamp `None`. No migration step is run; the user populates
  the snapshot by re-running the fit.

This rule applies wholesale — no flag toggles it, no targeted
exception is raised. Publication-grade users who need the
provenance can re-run the fit; users producing draft / preview
reports keep working without interruption.

### 5. Publication-metadata category on `project`

New top-level category on `Project`, sibling to `project.info` and
`project.analysis`. Populated by the user (directly in Python, or
loaded from a `publ_info.{toml,json}` file). Feeds the `_publ_*` /
`_journal_*` / `_publ_author.*` placeholders that the alignment
ADR's `data_global` block currently emits as `?` (alignment ADR
§2.3a).

#### 5.1 Structure — CIF-aligned sibling categories

`Publication` is a category-owner (like `Experiment`) hosting
sibling sub-categories that map **1:1 to CIF category prefixes**.
No artificial groupings; the CIF dictionaries already provide the
natural shape:

| Python attribute                       | CIF category               | Audience                                                                  |
| -------------------------------------- | -------------------------- | ------------------------------------------------------------------------- |
| `publication.journal`                  | `_journal.*`               | User-set at submission (`name_full`, `paper_category`); editor-set post-acceptance (`year`, `volume`, `issue`, `page_*`, `paper_doi`) |
| `publication.journal_date`             | `_journal_date.*`          | Editor (`accepted`, `from_coeditor`, `printers_final`)                    |
| `publication.journal_coeditor`         | `_journal_coeditor.*`      | Editor (`code`, `name`, `notes`)                                          |
| `publication.contact_author`           | `_publ_contact_author.*`   | User (`name`, `address`, `email`, `phone`, `id_orcid`, `id_iucr`)         |
| `publication.body`                     | `_publ_body.*`             | User (`title`, `synopsis`, `abstract`, `keywords`)                        |
| `publication.authors`                  | `_publ_author.*` (loop)    | User (per author: `name`, `address`, `footnote`, `id_orcid`, `id_iucr`)   |

Access pattern:

```python
project.publication.journal.name_full       = "Acta Crystallographica E"
project.publication.journal.paper_category  = "structure-report"
project.publication.journal.paper_doi       = "10.1107/S2056989026..."   # post-acceptance
project.publication.contact_author.name     = "Jane Doe"
project.publication.contact_author.email    = "jane@example.com"
project.publication.contact_author.id_orcid = "0000-0001-..."
project.publication.body.title              = "Crystal structure of ..."
project.publication.body.synopsis           = "Short summary..."
project.publication.body.abstract           = "..."
project.publication.body.keywords           = ["powder diffraction", "Rietveld", ...]
project.publication.authors.add(name="Jane Doe",   id_orcid="0000-0001-...")
project.publication.authors.add(name="John Smith", id_orcid="0000-0002-...")
```

Python attributes are lowercase snake_case (`id_orcid`); CIF tags
retain dictionary casing (`_publ_contact_author.id_ORCID`). Loops
use the project's existing `CategoryCollection` pattern (`add()`,
indexed access, etc.).

The editor-side categories (`journal_date`, `journal_coeditor`)
exist so the schema can carry editor-supplied fields when a user
manually copies them in (typically by editing
`project.publication.*` in Python after a referee round) — not
because users typically fill them at submission time. Defaults are
`None`; the IUCr writer emits `?` for unset fields. Round-trip is
on the **`project.cif`** axis only (`project.publication` reads
and writes there per the project-facade-and-persistence
contract); **the report CIF at `reports/<project>.cif` stays
export-only** per the accepted IUCr ADR. A reader for
`reports/<project>.cif` is explicitly out of scope.

#### 5.2 Discrete `body` fields, not a markdown blob

`_publ_body.*` in coreCIF supports nested section content via an
`element` / `format` / `contents` trio. For the refinement-table
appendix use case (user pastes content into a full manuscript
later), discrete top-level slots are more discoverable than a
generic markdown blob:

- `publication.body.title`     — manuscript title (single string)
- `publication.body.synopsis`  — short summary (IUCr Acta E requires this)
- `publication.body.abstract`  — abstract text
- `publication.body.keywords`  — list of strings (loop on CIF side)

A future v2 could add free-form section support
(`publication.body.sections[]` with element/format/contents trios)
when users produce full manuscripts from the library. Out of
scope for v1.

#### 5.3 Input mechanism — TOML primary, JSON fallback

Two import paths, both writing into the same in-memory
`project.publication` object:

```python
# Direct Python edit (preferred for notebook / interactive use):
project.publication.contact_author.email = "jane@example.com"

# File-based load (preferred for collaborative / batch workflows):
project.publication.load("reports/publ_info.toml")    # TOML, by extension
project.publication.load("reports/publ_info.json")    # JSON, by extension
```

TOML is the primary format:

- **Comment support** — users can document why a field is set / unset.
- **Multi-line strings** — abstracts, addresses, and synopses without escaping.
- **Familiar** — the project already uses `pyproject.toml` and `pixi.toml`.
- **Standard library** `tomllib` (Python 3.11+); no new dependency.

JSON is supported as a fallback for programmatic generation (e.g.
a user script that dumps publication data from a database; an
external tool that produces JSON output). Standard library `json`.

Format selection is by file extension. Unknown extensions raise
`ValueError("Unsupported publication-info format: <ext>. "
"Use .toml or .json.")`. No YAML support — adds a dependency for
no gain.

Reading from the report CIF (`reports/<project>.cif`) back into
`project.publication` is **explicitly out of scope** here and
remains the accepted IUCr ADR's "Export only — no round-trip"
contract. Users who edit the report file by hand should also
update `project.publication` (or its TOML/JSON source) so the
next save reflects the edits; the library does not auto-import.

### 6. Shared `ReportDataContext` + Jinja templates

One context-builder method on the `project.report` facade:

```python
def data_context(self) -> dict:
    return {
        'project': {
            'title': self.project.info.title,
            'description': self.project.info.description,
            'n_phases': len(self.project.structures),
            'n_experiments': len(self.project.experiments),
        },
        'structures': [
            {
                'id': s.name,
                'space_group': s.space_group.name_h_m.value,
                'cell': {
                    'a': s.cell.length_a.value,
                    'b': s.cell.length_b.value,
                    ...
                },
                'atom_sites': [...],
            }
            for s in self.project.structures.values()
        ],
        'experiments': [...],
        'refinement': {
            'calculation_engine': {...},
            'minimization_engine': {...},
            'goodness_of_fit': ...,
            'parameters': {'total': ..., 'free': ..., 'fixed': ...},
            'constraints': ...,
        },
        'software': {...},  # from §4
        'publication': {     # from project.publication (§5); unset fields → None
            'journal':          {...},   # _journal.*
            'journal_date':     {...},   # _journal_date.* (editor-side)
            'journal_coeditor': {...},   # _journal_coeditor.* (editor-side)
            'contact_author':   {...},   # _publ_contact_author.*
            'body':             {...},   # _publ_body.{title, synopsis, abstract, keywords}
            'authors':          [...],   # _publ_author.* loop
        },
        'figures': {
            'fit_per_experiment': {expt_id: plotly_html_div, ...},
        },
        'metadata': {
            'easydiffraction_version': ...,
            'generated_at': ...,
        },
    }
```

Templates live under `src/easydiffraction/report/templates/`, keyed by
style slug:

```
templates/
  base.j2                       # shared macros (parameter row, uncertainty fmt)
  html/
    report.html.j2
    style.css
  tex/
    iucr.tex.j2                 # ships in v1; emits \documentclass{iucrjournals}
    revtex.tex.j2               # ships in v1; emits \documentclass[prb]{revtex4-2}
```

GUI consumes `project.report.data_context()` directly — no CIF
parsing, no HTML scraping. This is the consistency guarantee.

### 7. CLI surface mirrors the Python split

Two subcommands match the Python `project.save()` vs
`project.report.save_*()` split:

```bash
ed save                                            # project files + whatever is in project.report.formats
ed save-report --html                              # one-off — write reports/<project>.html only
ed save-report --cif --tex --pdf                   # one-off — full LaTeX bundle + CIF
ed save-report --cif --tex --pdf --style iucr
```

`ed save-report` with no `--cif`/`--html`/`--tex`/`--pdf` exits
with a clear error pointing the user at the configuration
category (`ed config project.report.formats html cif`).
`--pdf` implies `--tex` so the user always gets the editable
source next to the PDF.

For users who want to **persist** the choice across runs, the
configuration category is set the usual way — interactively
through `ed config project.report.formats html cif`, by editing
`project.cif` directly, or programmatically — and `ed save`
picks it up on every subsequent save.

CLI flags are short (no `_report` suffix; the subcommand name
`save-report` already scopes them). The Python and CLI surfaces
stay symmetric:

| Python (config — persisted)               | Python (ad-hoc — one-off)            | CLI (one-off subcommand)              |
| ----------------------------------------- | ------------------------------------ | ------------------------------------- |
| `project.report.formats = ['html']`       | `project.report.save_html()`         | `ed save-report --html`               |
| `project.report.formats = ['cif']`        | `project.report.save_cif()`          | `ed save-report --cif`                |
| `project.report.formats = ['tex']`        | `project.report.save_tex(style=…)`   | `ed save-report --tex --style iucr`   |
| `project.report.formats = ['pdf']`        | `project.report.save_pdf(style=…)`   | `ed save-report --pdf --style iucr`   |
| `project.report.style = 'iucr'`           | (passed as `style=…` per-call)       | `--style iucr`                        |
| `project.report.html_offline = True`      | `save_html(offline=True)`            | `--html --offline`                    |

### 8. Fields the library currently lacks

The HTML/LaTeX renderers need three fields the library does not
expose today; this ADR scopes them as in-scope work:

- `structures[i].crystal_system` — derivable from
  `space_group.name_h_m`, but not currently exposed as a property.
- `experiments[i].measured_range` — `min`, `max`, `inc` triple from
  the underlying data arrays. Not currently exposed as a property on
  `Experiment`.
- `analysis.parameter_counts` — total / free / fixed / constrained.
  Free and fixed are derivable from
  `project.free_parameters`; total and constrained need a single
  aggregating helper.

All three are pure derived properties — no new state, no persistence
beyond what already exists.

## Consequences

### Positive

- `summary.cif` placeholder goes away (alignment ADR + this ADR
  jointly retire it); no more "To be added..." on disk.
- HTML can be auto-regenerated on every save by adding `'html'`
  to `project.report.formats` once (or via the GUI's "Export"
  panel). Zero-friction inspection for users who want it, no
  surprise file writes for users who don't.
- LaTeX export covers the "send the refinement table to my
  co-author" workflow that today requires manual transcription.
- Engine name + version + URL are captured at fit time, ending the
  current provenance gap. Maps cleanly to coreCIF
  `_computing.structure_refinement` for journal-bound CIFs.
- The GUI Summary tab consumes the same Python data context as the
  HTML renderer. Library and GUI cannot drift on "what numbers are
  shown".
- New summary fields are added in one place
  (`project.report.data_context()`); all renderers pick them up.
- Style selector is a template registration, not a code path.
  Adding `'prb'`, `'jac'`, etc. is a Jinja file + one-line
  registration.

### Trade-offs

- All report outputs are opt-in. Default
  `project.report.formats = []` means daily `project.save()`
  calls write only project files — `reports/` isn't created
  until a format is configured (or an ad-hoc method is called).
- HTML is small (~50–300 KB CDN-mode, ~few MB offline); users
  who want it on every save add `'html'` to
  `project.report.formats` once.
- LaTeX bundle (`reports/tex/` + `reports/<project>.pdf`) is
  several files (`.tex`, figures, compiled PDF, full styles
  directory) — only written when `'tex'` or `'pdf'` is in
  `project.report.formats` (or an ad-hoc `save_tex()` /
  `save_pdf()` call is made). The `tex/styles/` directory
  always contains
  every supported style's files (12 files, ~420 KB) so the user
  can swap styles by editing one line in `<project>.tex` and
  rebuilding, without re-running the library. Negligible against
  project data files, the PDF, and the HTML report.
- Two upstream snapshots vendored in the repository
  (`iucrjournals.cls` family CC0 1.0; REVTeX 4.2 family LPPL
  1.3c). The plan refreshes the snapshot when upstream releases
  a new version; license texts are copied into the package's
  licensing documentation alongside the wheel's BSD-3-Clause
  `LICENSE` with attribution.
- Adds **kaleido v1.0+** as a direct dependency (~30 MB).
  Justified by the visual-consistency win: the HTML and LaTeX
  figures come from the same Plotly figure objects rendered by
  the same Plotly engine (interactive in HTML, static PDF via
  kaleido), so any visual difference is bounded by
  browser/runtime/export quirks rather than two unrelated
  rendering toolkits drifting on data choices. v1 relies on
  Chrome/Chromium for rendering; the project's `pixi.toml` adds
  `tectonic`, while Chromium is not modeled as a conda dependency
  because conda-forge has no `chromium` package for the workspace
  platforms. Developers and CI can use an installed
  Chrome/Chromium/Edge browser or run
  `python -c "import kaleido; kaleido.get_chrome()"` once to
  download Kaleido-managed Chromium. End users on machines without
  a browser get a clear install hint at first use.
- PDF compilation is opportunistic — works when `tectonic`,
  `latexmk`, or `pdflatex` is on `PATH`; otherwise the `.tex` and
  figures are still written and the user gets a clear one-line
  install hint (`pixi add tectonic` is the recommended path).
- The `data_context` dict is a public API surface. Renaming a key
  affects every renderer. Treated like a public method signature.
- `analysis.software` adds a new category to persist on every save.
  Small (8 string fields) but visible in `analysis.cif` diffs.
- Two ADRs (this one + alignment) must move in lockstep on the
  `_computing.*` mapping and on publication-metadata sourcing.
  Cross-references in both should make the coupling explicit.

### ADRs amended by this ADR

- [`iucr-cif-tag-alignment.md`](../accepted/iucr-cif-tag-alignment.md)
  — five amendments:
  1. **`project.save()` flag removal.** The accepted
     `project.save(report=True)` flag is **removed**. Reports
     come from the new `project.report` configuration category
     (§1.1, §1.3) — six scalar items persisted to `project.cif`
     (`_report.cif`, `_report.html`, `_report.tex`, `_report.pdf`,
     `_report.style`, `_report.html_offline`). The Python-side
     `project.report.formats` is a property view over the four
     format booleans. Set the configuration once; `project.save()`
     applies it on every save thereafter. Replaces the flag with
     persisted configuration, matching the existing
     `project.chart`, `project.table`, `project.verbosity`
     pattern.
  2. **`project.report.save()` surface redesigned.** The
     accepted `project.report.save()` is now a no-argument
     convenience that reads the configuration category (raises
     `ValueError` when no formats are enabled — §1.2). Per-format
     ad-hoc writes use new explicit methods:
     `project.report.save_cif()`, `save_html(offline=False)`,
     `save_tex(style='iucr')`, `save_pdf(style='iucr')`. The
     earlier draft's `save(cif=True, html=True, tex=True,
     pdf=True, style=, check=)` flag bundle is dropped.
     `project.report.check()` and the `check=True` flag are
     **removed**: dictionary-spec validation runs internally
     **before every CIF write only** (`save_cif()` and the
     `cif` branch under `project.save()`; HTML, TeX, and PDF
     get no pre-write validation — see §1.4). A writer-
     correctness failure on the CIF path raises
     `EasyDiffractionWriterError` instead of producing a
     broken file.
  3. **Software-identification source.** The alignment ADR's
     §2.3a-i described the `_easydiffraction_software.*` triple as
     a "report-only projection … built inline by the IUCr writer
     from existing state", with no default-save persistence. This
     ADR introduces a persisted `analysis.software` category (§4)
     and amends that stance: the triple is read **from**
     `analysis.software` at IUCr-export time, not reconstructed
     inline. The Current State table row that previously read
     "`_calculator.type`, `_minimizer.type` … Analysis —
     unchanged" gains an "Analysis — `analysis.software`
     persisted" note.
  4. **New project-extension tag for fit time.** Adds
     `_easydiffraction_software.fit_datetime` to the
     `data_global` block in the IUCr export. The accepted ADR's
     §2.3a-i listed `_easydiffraction_software.{framework,
     calculator, minimizer}` only; `fit_datetime` extends that
     same category prefix without introducing a new top-level
     extension namespace. The writer's existing
     `_audit.creation_date` keeps its
     `_iso_creation_datetime()` source (report-generation time)
     and is **not** overwritten — fit time and report time are
     distinct events.
  5. **Publication metadata in the default save.** The alignment
     ADR's Scope explicitly excluded "Adding new CIF categories
     the project does not currently track (`_chemical.*`,
     `_publ.*`, `_journal.*`) **for the default save**"
     (alignment ADR §Scope, lines 101-110). This ADR adds
     `project.publication.*` (§5) and persists it to
     `project.cif` — a different file from
     `reports/<project>.cif`, but still a default-save change
     that the alignment ADR did not anticipate. Specifically:
     - `_publ_contact_author.*`, `_publ_author.*`, `_publ_body.*`,
       `_journal.*`, `_journal_date.*`, `_journal_coeditor.*` are
       now in scope for `project.cif`.
     - The accepted IUCr export still reads these from
       `project.publication.*` and emits them in `data_global`
       per §2.3a; the `?` placeholder semantics for unset fields
       are unchanged.
     - The accepted "Export only — no round-trip" rule for
       `reports/<project>.cif` is **unaffected** —
       `project.publication` round-trips through `project.cif`,
       not through the report CIF (see §5.1 / §5.3).
  
  All other IUCr-export decisions in the alignment ADR
  (multi-datablock layout, tag-name policy, gemmi as the
  validation engine) are unaffected — only the public surface
  for validation changes: `project.report.check()` and
  `check=True` are removed; the gemmi pass moves inside the
  writer **on the CIF emission paths only** (§1.4), running
  before every CIF write (no pre-write validation for HTML, TeX,
  or PDF — those formats have no spec to check against).
- [`analysis-cif-fit-state.md`](../accepted/analysis-cif-fit-state.md)
  — adds `analysis.software` to the persisted analysis state.
- [`project-facade-and-persistence.md`](../accepted/project-facade-and-persistence.md)
  — three changes:
  1. **`project.report` gains a persisted configuration category.**
     The accepted ADR scoped `project.report` as a CIF-write helper
     (single output: `reports/<project>.cif`). This ADR extends
     it with a configuration category (`_report.*` in
     `project.cif`, six scalar items per §1.1 / §1.3) that the
     existing `Project.save()` reads on every save. The facade
     becomes a hybrid — helper methods (`save_*()`) **and**
     persisted configuration on the same Python object.
  2. **New top-level `project.publication` facade slot (§5).**
     Sibling to `project.info`, `project.structures`,
     `project.experiments`, `project.analysis`, `project.report`.
     Persisted to `project.cif` next to the other project-level
     singleton categories.
  3. **Project-level singleton category enumeration extended.**
     The accepted ADR enumerates `_info.*`, `_chart.*`,
     `_table.*`, `_verbosity.*` as the project-level singleton
     categories owned by `project.cif`. This ADR adds two more
     to that enumeration: `_report.*` (this ADR §1.3) and
     `_publication.*` family (this ADR §5; concrete sub-prefixes
     are `_publ_*` and `_journal_*` per IUCr coreCIF).
- [`python-cif-category-correspondence.md`](python-cif-category-correspondence.md)
  — owns the Python-to-CIF correspondence rule for two new
  project-level singleton surfaces:
  - `project.report.*` ↔ `_report.*` — six scalar items (four
    format booleans, `style`, `html_offline`) per §1.3.
  - `project.publication.*` ↔ `_publ_*` / `_journal_*` sibling
    categories per §5. Python attributes are lowercase
    snake_case (`id_orcid`); CIF tags retain dictionary casing
    (`_publ_contact_author.id_ORCID`).
  
  Both follow the correspondence ADR's existing 1:1 mapping
  pattern. The correspondence ADR's enumeration of "currently
  persisted Python category surfaces" gains two rows for these
  additions.
  
  No conflict with the correspondence ADR's project-level
  category list because `_publ_*` / `_journal_*` are
  publication-domain, not project-level singleton categories.

## Open Questions

- **GUI Export panel.** Two reasonable shapes: (a) checkboxes
  edit `project.report.formats` directly + a "Save now" button
  that calls `project.save()` (config-driven, matches the
  Python surface) or (b) checkboxes drive ad-hoc per-format
  calls (`save_html()`, `save_pdf()`) without changing the
  persisted config (one-off ergonomics). Either fits the
  configuration / ad-hoc split in §1; the exact GUI layout
  (single dialog vs. inline checkboxes, button labels,
  post-save action) decides at GUI-integration time, not here.

## Alternatives Considered

### A. Leave `project.report` scoped to CIF only

Status of the alignment ADR before this ADR's amendment: facade
exists but only writes the IUCr CIF. The GUI Summary tab would
then need its own renderer, the everyday project folder would have
no human-readable artefact, and there'd be no LaTeX/PDF path. Auto
HTML and the GUI-consistency story both disappear. Rejected on UX
and consistency grounds.

### B. HTML auto-saved on every `project.save()`

An earlier revision of this ADR had HTML always-on, no opt-in
flag, the philosophy being "every artefact stays fresh".
Rejected in favour of the configuration approach:
`project.save()` does one job (save the project) and reads
`project.report.formats` to decide which reports come along.
Empty config = no reports. Users who want auto-fresh HTML add
`'html'` to `project.report.formats` once; the GUI consumes
`project.report.data_context()` in-memory, not the HTML file, so
freshness of the file does not affect GUI consistency.

### C. Markdown as the primary rendered format

Markdown is git-friendly and renders nicely in many viewers. But it
cannot embed interactive Plotly figures and has no journal-style
analogue for LaTeX. Could be added as a third renderer (the Jinja
base template makes it a few hundred lines) but not as the primary.
Deferred.

### D. Build the HTML renderer inside the GUI, not the library

Push HTML/LaTeX rendering into the GUI codebase; the library only
exposes the data context. Saves library complexity. But: CLI users
get nothing, notebook users get nothing, and the GUI's renderer is
not exercised by CI. Rejected for the consistency benefit of a
single renderer.

### E. PDF as the primary rendered format

Could be done via `weasyprint` (HTML→PDF) or directly via
`reportlab`. Adds a dependency, slows save, and most users print
HTML to PDF from a browser anyway. Deferred.

## Deferred Work

- Markdown rendering as a third Jinja target.
- Additional style slugs beyond v1's `iucr` and `revtex`
  (e.g. ICDD, Elsevier `elsarticle`, Springer `svjour3`). Each new
  slug ships as one new Jinja template + a registration row; no
  code restructuring needed.
- **Bibliography support** (`iucr.bib` / `iucr.bst`,
  REVTeX `*.bst` files). Both upstream distributions ship
  bibliography styles for citing IUCr / APS publications. Not
  bundled in v1 because the refinement-table appendix use case
  has no citations. Add when users start producing full
  manuscripts from the library.
- **Extended REVTeX journal coverage.** v1 bundles `aps4-2.rtx`
  (covers PRB/PRA/PRL/PRD). The four upstream `.rtx` files for
  Rev. Mod. Phys. (`apsrmp4-2.rtx`), AIP (`aip4-2.rtx`), AAPM
  (`aapm4-2.rtx`), and Society of Rheology (`sor4-2.rtx`) total
  ~76 KB and are skipped to stay minimal. Add them when users
  in those communities ask. Users on the deferred journals can
  install REVTeX from TeX Live (full coverage is in the default
  install) and the swap-with-one-line-edit workflow then works.
- **Snapshot-refresh automation.** A small `pixi` task to
  re-fetch upstream sources and diff against the vendored
  snapshot would help track when IUCr or APS releases a new
  version. v1 refreshes by hand during plan work.
- **Per-style subfolder layout.** v1 flattens all 12 style files
  into one `reports/tex/styles/` directory. As more styles ship
  (Elsevier `elsarticle`, Springer `svjour3`, …), a per-style
  subfolder layout (`styles/iucr/*`, `styles/revtex/*`,
  `styles/elsarticle/*`) becomes cleaner — needs `TEXINPUTS=./styles//:`
  configured for the TeX engine. Defer until the file count
  becomes uncomfortable.
- Tab/accordion navigation in HTML for projects with many
  experiments.
- `project.report.check_completeness()` — complements the
  internal gemmi pass from §1.4 (dictionary spec compliance,
  enforced before every CIF write). The completeness check would
  flag whether the user has filled in `_publ_*` / `_journal_*`
  placeholders for their target journal, which dictionary
  validation cannot determine. Different concern, different layer.
- A pinned-snapshot variant of `<project>.html` (timestamped, kept
  next to fit-run-specific artifacts) for users who want to track
  refinement history visually across saves.
- Additional figure types beyond fit + difference (e.g.
  cumulative-χ² plot, residual histogram, posterior corner plot
  for Bayesian fits). Same data-context-driven pattern, new
  matplotlib + Plotly renderers per type.

## Suggested Pull Request

**Title:** Extend `project.report` with HTML, TeX, and PDF outputs (opt-in)

**Description:**

Builds on the IUCr CIF alignment work by filling in the non-CIF
half of the publication bundle. The `project.report` facade
covers four output formats — CIF, HTML, TeX, PDF — chosen via a
configuration category on the project (persisted in
`project.cif`) and applied automatically on every save:

```python
project.report.formats = ['cif', 'html']    # which formats project.save() emits
project.report.style = 'iucr'               # LaTeX style (when 'tex' or 'pdf' is in formats)
project.report.html_offline = False         # Plotly via CDN (default) or inlined

project.save()
# → project.cif (with the _report.* config)
# → structures/, experiments/, analysis/ as before
# → reports/<project>.cif and reports/<project>.html per config
```

Per-format ad-hoc methods cover one-offs without changing the
persisted config:
`project.report.save_html(offline=False)`,
`save_cif()`, `save_tex(style='revtex')`, `save_pdf()`.
The CLI mirrors with a new subcommand,
`ed save-report --cif --html --tex --pdf --style iucr` (also a
one-off; `ed save` reads the persisted config).

The LaTeX bundle ships `<project>.tex`, vector-PDF figures, and
the full set of supported style files under `reports/tex/`. The
compiled `<project>.pdf` is written one level up (next to the
CIF and HTML) when a TeX engine — `tectonic` (recommended,
conda-forge), `latexmk`, or `pdflatex` — is on `PATH`. v1 ships
two styles, both **fully bundled** in `reports/tex/styles/` on
every report save (~420 KB across 12 files):

- `iucr` (default) — IUCr's `iucrjournals.cls` (CC0 1.0,
  https://journals.iucr.org/j/services/latexstyle.html), unified
  across Acta Cryst E/B/C/D/F, J. Appl. Cryst., J. Synchrotron
  Rad., IUCrData. Sub-journal is decided at submission, not in
  the `.tex`.
- `revtex` — APS's `revtex4-2.cls` family (LPPL 1.3c,
  https://journals.aps.org/revtex / https://ctan.org/pkg/revtex).
  PRB by default; user changes the documentclass option letter
  to switch to PRA / PRL / PRD / Rev. Mod. Phys. / AIP / AAPM /
  SOR / generic reprint.

Bundling both styles regardless of the active selection makes
`reports/tex/` self-contained — the user (or a collaborator
without EasyDiffraction) can rebuild in any style by editing
one line in `<project>.tex` and rerunning the TeX engine.

Adds an `analysis.software` Python category — three-role triple
(framework / calculator / minimizer) matching the alignment ADR's
`_easydiffraction_software.*` CIF emission — recording engines,
versions, and URLs at fit time so every report carries
authoritative provenance. The library, the CLI, and the GUI all
consume the same in-memory report data (`project.report.data_context()`)
— no code path renders independently. This keeps the forthcoming
GUI Summary tab in lockstep with the library.
