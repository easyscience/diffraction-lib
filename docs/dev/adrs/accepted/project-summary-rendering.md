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
**`project.report` configuration category** with five scalar
persisted fields (`cif`, `html`, `tex`, `pdf`, `html_offline`)
on `project.cif`, plus ad-hoc per-format methods
(`save_html()`, `save_cif()`, `save_tex()`, `save_pdf()`). The
Python-side `project.report.formats` is a convenience property
view over the four format booleans. The LaTeX writer hardcodes
`iucrjournals` as its document class — there is no style
selector, no `_report.style` field, no `style=` arg on
`save_tex()` / `save_pdf()`. The
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
  `project.report.* ↔ _report.*` (five scalar items, §1.3) and
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
  configuration category (five scalar fields —
  `project.report.{cif, html, tex, pdf, html_offline}` —
  persisted in `project.cif`; `project.report.formats` is a
  property view over the four format booleans), and ad-hoc
  per-format save methods. **All report formats are opt-in via the
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
- Ship exactly one LaTeX style (`iucrjournals`) — no style
  selector, no `ReportStyleEnum`, no `_report.style` field.
  Multi-style support (REVTeX, Elsevier, etc.) is deferred
  to a follow-up ADR; see "Deferred Work".

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
        ├──► HTML renderer              (Jinja + Plotly + MathJax; opt-in via project.report.html)
        ├──► LaTeX renderer             (Jinja + pgfplots; opt-in via project.report.tex/pdf; iucrjournals style only)
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
| `project.report.tex`        | `bool`       | `False`   | When `True`, `project.save()` writes `reports/tex/{<project>.tex, data/, styles/}`.                    |
| `project.report.pdf`        | `bool`       | `False`   | When `True`, `project.save()` writes `reports/<project>.pdf` (and `tex/` as a side-effect).            |
| `project.report.html_offline` | `bool`     | `False`   | When `True`, the HTML report is **fully self-contained** — inline-bundles both Plotly and MathJax (~3 MB + ~1.5 MB on top of the otherwise-empty document). Otherwise both load from CDN. |

Four per-format scalar booleans (`cif`, `html`, `tex`, `pdf`)
plus `html_offline` — **five fields total**, all single-row in
CIF. Matches the existing `project.chart`, `project.table`,
`project.verbosity` scalar-config shape verbatim. All booleans
default to `False`, so an unconfigured project produces no
`reports/` directory at all.

There is no `style` field. The LaTeX output ships exactly one
class (`iucrjournals`); adding another style is deferred
work, not a v1 selector. See §3 for the reasoning behind the
single-style choice.

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
project.report.html_offline = False

# Every subsequent save now emits the configured reports too.
project.save()
# → project.cif (with _report.* config block)
# → structures/<...>.cif, experiments/<...>.cif, analysis/analysis.cif
# → reports/<project>.cif  (because project.report.cif is True)
# → reports/<project>.html (because project.report.html is True)
```

##### Enum backing per the closed-values ADR

The set of report formats is a finite closed set, so per the
accepted
[`enum-backed-closed-values.md`](../accepted/enum-backed-closed-values.md)
contract it is represented internally as `(str, Enum)`:

```python
class ReportFormatEnum(str, Enum):
    CIF = 'cif'
    HTML = 'html'
    TEX = 'tex'
    PDF = 'pdf'
```

The four per-format booleans (`project.report.cif`, `.html`,
`.tex`, `.pdf`) carry one `ReportFormatEnum` member each as a
class-level constant identifying which format they enable. The
`formats` property view returns a list of `ReportFormatEnum`
members (`[ReportFormatEnum.CIF, ReportFormatEnum.HTML]`),
which compare equal to the bare string values for ergonomic
user code (`'cif' in project.report.formats` still works
because `(str, Enum)` inherits string equality).

There is no `ReportStyleEnum`. The LaTeX writer hardcodes
`iucrjournals` as its document class (see §3); when a future
ADR adds a second style, the `ReportStyleEnum` is reintroduced
together with a new `_report.style` config field.

#### 1.2 Ad-hoc per-format methods

Each format has its own explicit write method on the facade,
independent of `project.report.formats`. Use when a user wants
to produce a one-off artifact without changing the persistent
configuration.

```python
project.report.save_cif()                        # writes reports/<project>.cif
project.report.save_html(offline: bool = False)  # writes reports/<project>.html
project.report.save_tex()                        # writes reports/tex/{<project>.tex, ...}
project.report.save_pdf()                        # writes reports/<project>.pdf (compiles TeX too)

# Convenience: write everything currently in project.report.formats.
# Raises ValueError if no formats are configured (see below).
project.report.save()                            # reads config, no flags

# Ad-hoc string returns:
project.report.as_html(offline: bool = False) -> str
project.report.as_tex() -> str

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
that format — `save_html(offline=True)` is unambiguous; there
is no `save_tex(style=...)` because the LaTeX writer ships
exactly one style (`iucrjournals`), so a style selector would
be dead weight. The cross-format mixing that the earlier
flag-based draft had (`html_offline` ignored when
`html=False`, `style=` ignored without `tex=True`) is gone.

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
`_report.*` — a Set category with five scalar items, no loops:

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
_report.html_offline  no
```

All five items are scalar DDLm dotted entries — the category
is declared `_definition.class Set` so a single value per
item, no loops permitted. Matches the existing `_chart.*`,
`_table.*`, `_verbosity.*` category shape exactly. The
`yes`/`no` boolean encoding follows the project's existing CIF
boolean convention.

The default unconfigured state writes four explicit `no`
values for the format booleans (not an absent or empty
representation), so the "no formats enabled" condition is
always a concrete CIF value, never an empty loop or missing
block:

```text
# Default (project.report.formats = []):
_report.cif           no
_report.html          no
_report.tex           no
_report.pdf           no
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
| **`project.report`** (this ADR)        | **A**   | **`project.cif` (`_report.*`)**             | **`CategoryItem` (five fields) plus action methods**        |
| `project.publication` (this ADR, §5)   | A       | `project.cif` (`_publ_*` / `_journal_*`)    | `CategoryOwner` of six sibling categories                   |
| `project.analysis`                     | B       | `analysis/analysis.cif`                     | `CategoryOwner` (heavy datablock)                           |
| `project.structures[name]`             | B       | `structures/<name>.cif`                     | `CategoryOwner` (heavy datablock)                           |
| `project.experiments[name]`            | B       | `experiments/<name>.cif`                    | `CategoryOwner` (heavy datablock)                           |

Reasons `project.report` is Pattern A, not Pattern B:

- Five scalar config items do not justify a separate file
  (`reports/report.cif` would be a tiny file holding five lines).
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
| `reports/<project>.cif` | gemmi parse always; dictionary checks when local dictionaries load | `EasyDiffractionWriterError` for malformed generated CIF or dictionary diagnostics |
| `reports/<project>.html` | none at write time                                       | n/a — HTML is a render of the data context, not a typed format             |
| `reports/tex/`           | none at write time                                       | n/a — LaTeX errors surface at PDF-compile time, with the engine's message  |
| `reports/<project>.pdf`  | TeX engine's own compilation (returns non-zero on error) | engine-specific message; the `.tex` and `data/` CSVs are still written     |

The dictionaries under `tmp/iucr-dicts/` are optional local
validation aids, not report inputs. If Gemmi cannot load those
local dictionary files, the writer skips dictionary-specific
checks after confirming the generated CIF itself parses; this
avoids blocking report generation on a stale or incompatible
dictionary cache.

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

#### 1.5 Descriptor display metadata — `DisplayHandler`

Parameter names like `u_iso` and unit strings like `Å²` need
prettier representations for the HTML and PDF renderers. The
ADR introduces a new optional handler on the descriptor base
classes (`Parameter`, `NumericDescriptor`, `StringDescriptor`)
that carries the typeset variants in a single place, sibling
to the existing `cif_handler`:

```python
from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class DisplayHandler:
    """Pretty-printing metadata for descriptors.

    All four fields are optional strings. Renderers fall back
    to the descriptor's plain ``name`` / ``units`` when a
    field is unset; missing fields never raise.
    """
    display_name: str | None = None   # HTML / GUI / show() label
    display_units: str | None = None  # HTML / GUI / show() unit string
    latex_name: str | None = None     # LaTeX inline-math label
    latex_units: str | None = None    # LaTeX text/math unit string
```

`DisplayHandler` lives at
`src/easydiffraction/core/display_handler.py` alongside the
existing `CifHandler` in `src/easydiffraction/io/cif/handler.py`
— a frozen dataclass per the project's value-object convention
(matches `TypeInfo`, `Compatibility`, `CalculatorSupport` per
AGENTS.md). `slots=True` keeps memory overhead constant per
attached descriptor.

The plain `name` and `units` fields keep their existing role
on the descriptor, but their **content convention changes**:

- `name` — Python identifier; ASCII snake_case; unchanged.
- `units` — **ASCII only**, following the CIF DDLm
  `_units.code` vocabulary from
  [`cif_core.dic`](../../../../tmp/iucr-dicts/cif_core.dic)
  **verbatim** when the dictionary defines a value for the
  unit. The dictionary's vocabulary is a single source of
  truth, but it is **not** uniformly plural — singular and
  plural forms appear mixed across units (each unit is whatever
  the dictionary actually says). Verified codes from
  `cif_core.dic`:

  | What we need     | `_units.code` value     | Source line in cif_core.dic     |
  | ---------------- | ----------------------- | ------------------------------- |
  | Å (length)       | `angstroms` (plural)    | line 1213                       |
  | Å² (area)        | `angstrom_squared` (singular `angstrom`) | line 1178      |
  | ° (angle)        | `degrees` (plural)      | line 500, 519, 1247, …          |
  | K (temperature)  | `kelvins` (plural)      | line 210, 232, 287, 316         |
  | Pa (pressure)    | `kilopascals` (plural)  | line 115, 136, 161, 184         |
  | µs (time)        | `microseconds` (plural) | (from `cif_pow.dic` TOF text)   |
  | Da (mass)        | `dalton` (singular)     | line 753                        |
  | MGy (dose)       | `megagray` (singular)   | line 592, 607                   |
  | Å⁻¹ (reciprocal) | `reciprocal_angstroms`  | line 795, 825                   |
  | Å⁻² (reciprocal area) | `reciprocal_angstrom_squared` | line 1552, 1587      |
  | dimensionless    | `none`                  | line 459, 480, …                |

- **Units the dictionary does not define.** The crystallographic
  vocabulary includes a handful of compound units that
  `cif_core.dic` does not assign a `_units.code` to — the one
  example currently in scope is `deg²` (squared degrees, used
  for some angular variance metrics). Convention for these:
  extend the same naming pattern (`degrees_squared`) as a
  **project-internal code** with no `_units.code` round-trip.
  The implementation plan keeps a small `units_vocabulary.py`
  module listing every code (dictionary and project-internal)
  so a sweep can validate every `units=` string at
  descriptor-declaration time.

The Unicode-symbol form (`Å²`) moves into `display_units`;
the LaTeX form (`\AA$^2$`) into `latex_units`.

##### Worked example — `u_iso`

```python
self._u_iso = Parameter(
    name='u_iso',
    description='Isotropic atomic displacement parameter',
    units='angstrom_squared',
    value_spec=AttributeSpec(default=0.0, validator=RangeValidator(ge=0.0)),
    cif_handler=CifHandler(names=['_atom_site.U_iso_or_equiv']),
    display_handler=DisplayHandler(
        display_name='Uiso',
        display_units='Å²',
        latex_name=r'$U_{\mathrm{iso}}$',
        latex_units=r'\AA$^2$',
    ),
)
```

| Renderer / context        | Name uses                          | Units uses           |
| ------------------------- | ---------------------------------- | -------------------- |
| LaTeX (`save_tex`)        | `$U_{\mathrm{iso}}$`               | `\AA$^2$`            |
| HTML (`save_html`, MathJax-rendered) | `$U_{\mathrm{iso}}$`    | `\AA$^2$`            |
| HTML pre-MathJax / GUI / `show_report()` | `Uiso`              | `Å²`                 |
| `project.report.data_context()` raw dict | both available    | both available       |
| CIF emission              | `_atom_site.U_iso_or_equiv`        | (no `_units.code` row today) |
| Python code / repr        | `u_iso`                            | `angstrom_squared`  |

##### Resolution rules

The renderers consult the `DisplayHandler` (if attached) using
a per-context fallback chain:

- **LaTeX context** (`save_tex`, `save_pdf`, `as_tex`):
  `handler.latex_name or descriptor.name`,
  `handler.latex_units or descriptor.units`.
- **HTML context** (`save_html`, `as_html`):
  `handler.display_name or descriptor.name`,
  `handler.display_units or descriptor.units`.
  The HTML template additionally surrounds `handler.latex_name`
  / `handler.latex_units` with `\(...\)` math delimiters so
  MathJax picks them up where the descriptor has typeset
  variants — i.e., HTML can show the same `$U_{\mathrm{iso}}$`
  the PDF shows, while a GUI tooltip or `show_report()`
  printout falls back to `display_*`.
- **GUI / terminal / `show_*()` context**:
  `handler.display_name or descriptor.name`,
  `handler.display_units or descriptor.units`.

Each chain falls through to the descriptor's plain fields, so
**descriptors without a `display_handler` continue to work
unchanged** — they simply render as `u_iso` / `angstrom_squared`
in all contexts. Adding a `display_handler` is opt-in per
descriptor.

**Table-rendering paths MUST read through the resolution chain
above, not the plain `descriptor.units` field directly.** This
is a strict requirement because `units=` now holds ASCII CIF
DDLm codes (`'angstrom_squared'`) that would look ridiculous
as a column header. Concretely the following call sites
migrate in the implementation sweep:

- Every `show_*()` method on `Report` (terminal / Jupyter
  table builders) — the unit column or row header is built
  from `display_units or units`, not `units` alone.
- Every Jinja macro in `templates/base.j2` that formats a
  parameter row — same resolution rule.
- The HTML template (`templates/html/report.html.j2`) uses
  `display_units` for non-math contexts and the latex_units
  variant inside `\(...\)` math delimiters where the
  descriptor declares both.
- The LaTeX template (`templates/tex/report.tex.j2`) uses
  `latex_units` (falling through `display_units` then `units`
  if not declared).
- The shared `data_context()` (§6) builder exposes both
  rendered strings per parameter so neither template has to
  re-derive the fallback chain — the resolution happens once
  in the builder.

External / third-party readers that hard-coded
`parameter.units` to compare against `'Å²'` (the prior Unicode
form) are flagged in the Open Questions section for a
project-wide audit before the sweep lands.

##### Why a handler class instead of four kwargs

Two design pressures:

- The fields cluster — they are all "how to display this
  parameter" — so a single handler keeps the descriptor
  constructor flat. `display_handler=DisplayHandler(latex_name=...,
  display_name=...)` reads cleaner than four sibling kwargs.
- Future display targets (Markdown export, GUI tooltips, an
  ASCII-fallback for terminal narrow-mode) can add fields to
  `DisplayHandler` without growing the descriptor constructor
  signature.

The mechanism mirrors the existing `cif_handler=CifHandler(...)`
pattern, so anyone reading the descriptor declarations sees the
same shape for CIF metadata and display metadata.

##### Migration sweep

Existing descriptors use `units='Å'` / `'Å²'` / `'°'` etc.
(Unicode short forms). The implementation plan owns the sweep
that:

- Converts every existing `units=` Unicode string to the
  ASCII CIF DDLm form (`'Å²'` → `'angstrom_squared'`).
- Adds `display_handler=DisplayHandler(...)` to descriptors
  the renderers benefit from prettifying (atom-site
  positions / ADPs, cell parameters, fit-result R-factors,
  refinement statistics, peak parameters, …). Descriptors
  the renderers don't show (CIF-only internal state) get no
  handler — the fallback to `name`/`units` is fine.
- Verifies the `_chart`, `_table`, `_verbosity` enum values
  and other singleton-config CIF strings don't accidentally
  collide with the new units vocabulary (they shouldn't —
  those are tag values, not unit codes).

The sweep is a Phase 1 step in the implementation plan, not
an ADR-level decision.

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

# Persistent + air-gapped readers — fully self-contained:
# inline Plotly AND inline MathJax.
project.report.html_offline = True
project.save()                         # → reports/<project>.html (~4.5 MB)

# One-off, ignoring config.
project.report.save_html()                 # CDN: Plotly + MathJax both from CDN
project.report.save_html(offline=True)     # inline: Plotly + MathJax both inlined
```

Asset-bundling modes — `html_offline` controls **both** assets
together (single switch, single contract):

- **CDN mode (default)** — Plotly via
  `include_plotlyjs='cdn'` (~50-300 KB on top of the
  otherwise-empty document, depending on chart count);
  MathJax from `https://cdn.jsdelivr.net/npm/mathjax@3/...`
  via `<script src="...">`. The HTML file itself is small
  (~50 KB body + tags); both assets stream in at page open.
  **Requires internet to view.**
- **Offline mode** (`project.report.html_offline = True` or
  `save_html(offline=True)`) — **fully self-contained**.
  Plotly inlines via `include_plotlyjs=True` (~3 MB); MathJax
  inlines as a `<script>` block holding the
  `tex-mml-chtml` component bundle (~1.5 MB) read from a
  vendored asset under
  `src/easydiffraction/report/templates/html/vendor/mathjax-tex-mml-chtml.js`.
  Total HTML size ~4.5 MB. Use when readers are air-gapped
  or when the user wants to archive a fully self-contained
  report.

The `mathjax-tex-mml-chtml.js` bundle is vendored once
during the implementation plan (Apache-2.0 license, ~1.5 MB
minified) and refreshed on the same cadence as
`iucrjournals.cls`. No new Python dependency — it's a
static JavaScript asset shipped with the wheel.

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
- No new Python dependencies for HTML: `plotly`, `jinja2`,
  `pandas` are already declared in
  [pyproject.toml](../../../../pyproject.toml). MathJax
  loads from CDN by default, or from a vendored
  `tex-mml-chtml` bundle (~1.5 MB) inside the HTML when
  `html_offline=True` — same single switch that controls
  Plotly's CDN/inline mode (see the asset-bundling block
  above). MathJax renders inline math (`$U_{\mathrm{iso}}$`,
  `$\AA$`, etc.) identically to the LaTeX output. This is
  what makes the "HTML and PDF look the same" story work:
  column headers, units, and parameter labels are the same
  LaTeX-math strings on both sides, just rendered by
  MathJax in the browser and by the TeX engine in the PDF.

**Visual consistency with the PDF.** The HTML template
applies academic-paper CSS — top/middle/bottom table rules
that mimic `booktabs`, a serif body font, narrow margins,
table cells in a tabular sans-serif numeric face — so a
reader scrolling the HTML page sees roughly the same
layout the compiled PDF gives them. Plots stay
format-specific (Plotly interactive in HTML, pgfplots
static in PDF), but every label, header, and unit string
matches because both renderers consume the same
`DisplayHandler` data per §1.5.

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
- Fit charts per experiment — Plotly figures built at template-
  render time from the shared fit-data series in
  `data_context()` (see §6 — `experiments[i].fit_data` carries
  an `x` sub-dict (values + descriptor name / display label /
  LaTeX label / units, all four label forms pre-resolved at
  builder time per §1.5) and a `series` sub-dict (`meas`,
  `calc`, `diff`, optional `bkg`, each carrying values + label
  + optional `su` uncertainty array). The descriptor-driven
  `x` payload covers Bragg powder CWL `two_theta`, TOF
  `time_of_flight`, and total-scattering `r` uniformly — any
  experiment whose x-axis descriptor exposes a
  `DisplayHandler` drops in without further ADR changes. The
  Jinja template feeds the dict to
  `display/plotters/plotly.py` and embeds the resulting figure
  via `fig.to_html(include_plotlyjs=<cdn|True>)`. The same
  `fit_data` series feeds the pgfplots CSV emitter for the
  LaTeX renderer — one source of truth.
- Footer — EasyDiffraction version, save timestamp.

### 3. LaTeX + PDF — config-driven via `project.report.formats`

LaTeX is a **publish-time** artifact. `'tex'` and `'pdf'` are
added to `project.report.formats` when the user wants them.
There is no style selector: the LaTeX writer ships exactly one
document class (`iucrjournals`); the **content layout
deliberately does not replicate IUCr's published journal
format** — it mirrors the project's own category-based
structure (project info, software, refinement, structures,
experiments) section by section. Think "typeset Python state"
rather than "ready-to-submit manuscript".

```python
# Persistent — every save writes TeX + assets.
project.report.formats = ['tex']
project.save()                              # → reports/tex/{...}

# Persistent — every save writes the compiled PDF too.
project.report.formats = ['tex', 'pdf']
project.save()                              # → reports/tex/{...} + reports/<project>.pdf

# One-off, ignoring config.
project.report.save_tex()                   # TeX + data + style only
project.report.save_pdf()                   # TeX + PDF (PDF implies TeX)

# Ad-hoc string return.
project.report.as_tex() -> str
```

**`'pdf' in formats` implies the TeX source is also written** —
a PDF without the editable `.tex` source is useless if the user
wants to tweak before re-compiling. Asking for the PDF always
writes the TeX next to it. Equivalently, `save_pdf()` writes
the TeX assets as a side-effect.

Future `project.report.html_style` (dark mode, journal-mimicking
HTML layout) can land separately without collision because it
lives in the config category, not in a method signature.

**Plots use `pgfplots` with external CSV data, not pre-rendered
images.** The figure-rendering pipeline produces CSV files
under `reports/tex/data/`; the `.tex` document references them
with `\addplot table {data/fit_<expt>.csv};`. This removes the
Plotly + kaleido + headless-Chromium dependency chain entirely
— the LaTeX bundle compiles to PDF using only `tectonic` (or
another local TeX engine) plus the `pgfplots` package, which
`tectonic` resolves on demand. See §3.3 for the figure
emission detail.

#### 3.1 Folder layout

Per-project filenames (`<project>.{cif,html,pdf}`) share a root in
`reports/`; the LaTeX source plus its assets sit in `reports/tex/`.
Single style (`iucrjournals`) — no multi-style infrastructure.

**Full reports/ tree when all formats are configured.**
`project.report.formats = ['cif', 'html', 'tex', 'pdf']`:

```
<project_root>/
  reports/                          # populated by project.save() per config
    <project>.cif                   # ← 'cif' in project.report.formats (alignment ADR §2)
    <project>.html                  # ← 'html' in project.report.formats (this ADR §2)
    <project>.pdf                   # ← 'pdf' in project.report.formats (this ADR §3.4)
    tex/                            # ← 'tex' or 'pdf' in project.report.formats (this ADR §3)
      <project>.tex                 #   main document; tables + pgfplots figures
      data/
        fit_<expt_id>.csv           #   one per experiment, plotted via pgfplots
      styles/                       #   vendored — required to compile the TeX
        iucrjournals.cls            #     IUCr unified class (CC0 1.0)
        harvard.sty                 #     IUCr companion bibliography style
                                    # 2 files, ~70 KB. See §3.2.1.
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

`project.report.formats = ['cif', 'html', 'pdf']` (typical
pre-submission bundle):

```
<project_root>/
  project.cif
  structures/<...>.cif
  experiments/<...>.cif
  analysis/analysis.cif
  reports/
    <project>.cif                   # journal-submission CIF
    <project>.html                  # interactive inspection page
    <project>.pdf                   # typeset PDF, iucrjournals class
    tex/                            # source for the PDF (kept editable)
      <project>.tex
      data/fit_<expt_id>.csv        # pgfplots data per experiment
      styles/iucrjournals.cls
      styles/harvard.sty
```

`reports/` is created lazily — only when at least one format
sits in `project.report.formats` (or an ad-hoc method is called).
The `tex/`, `tex/data/`, and `tex/styles/` subfolders appear
only when `'tex'` or `'pdf'` is in `project.report.formats` (or
`save_tex()` / `save_pdf()` is invoked).

The `<project>` portion of every filename comes from
`project.info.name` verbatim (e.g. a project named
`La0.5Ba0.5CoO3_HRPT` produces `reports/La0.5Ba0.5CoO3_HRPT.html`).
Only filesystem-dangerous characters (path separators, control
chars) are sanitized; case, dots, underscores, and parentheses are
preserved so the user recognises their project name in the file
listing.

#### 3.2 Single style — `iucrjournals`

The LaTeX writer ships exactly one document class:
`\documentclass[11pt,a4paper]{iucrjournals}`. No style selector,
no slug enum, no `_report.style` config field. Picking
`iucrjournals` is a convenience — it gives the typeset PDF a
clean academic look without committing to journal-submission
fidelity.

**The LaTeX content is NOT a journal-submission manuscript.**
It mirrors the project's own category-based structure
section-by-section: Project Summary, Software, Refinement,
Structures (one subsection per phase), Experiments (one
subsection per experiment). Tables use `booktabs`
(`\toprule`/`\midrule`/`\bottomrule`) and `float`'s `[H]`
placement; math uses inline LaTeX (`$Fd\bar{3}m$`, `\AA`,
`$\deg$`). Reference example at
[`tmp/latex/example.tex`](../../../../tmp/latex/example.tex).

The `iucrjournals.cls` choice has two practical advantages
over a bare `article`:

- IUCr's class handles crystallographic typography
  (`\AA`, space-group symbols, structure-factor formatting)
  cleanly out of the box.
- Vendored document-class files (`iucrjournals.cls` +
  `harvard.sty`) ship with the wheel, so an IUCr TeX-
  distribution install is not required — the document class
  is local. The TeX engine itself must still supply
  `pgfplots` and its `pgf` / `tikz` dependencies, which
  `tectonic` resolves from CTAN on first compile and which
  TeX Live / MiKTeX ship in their default sets; see §3.3 for
  the compile-time dependency story.

Multi-style support (REVTeX, Elsevier `elsarticle`, …) is
**deferred work** — see "Deferred Work" below. A future ADR
adds a style selector when there is a concrete second style
to ship.

#### 3.2.1 Source provenance and bundled files

The IUCr source is vendored under
`src/easydiffraction/report/templates/tex/styles/` in the
repository and copied into `reports/tex/styles/` on report
save. Download URL, date, license, and file list below; the
implementation plan refreshes the vendored snapshot when
upstream releases a new version.

**IUCr** (`iucrjournals.cls`)

- Source: https://journals.iucr.org/j/services/latexstyle.html
- Snapshot downloaded: 2026-05-26
- License: CC0 1.0 Universal (public domain dedication);
  declared in the `iucrjournals.cls` file header.
- Files included (2):
  - `iucrjournals.cls` — unified IUCr class
    (11 KB, dated 2024-12-02).
  - `harvard.sty` — bibliography style; required by
    `iucrjournals.cls` via `\RequirePackage{harvard}`
    (9 KB, Peter Williams, 2001-10-25).
- Files excluded: `iucr.bib`, `iucr.bst`, `fig1.png`,
  `template.tex` (bibliography / example assets, not needed
  for the category-mirror layout).

Total footprint per save: ~20 KB across 2 files. The CC0 1.0
licence text is copied into the package's licensing
documentation per the implementation plan, with attribution to
Peter Williams where the file headers carry it.

REVTeX and other styles are **not** vendored — only
`iucrjournals.cls` ships. See "Deferred Work" for
multi-style addition.

#### 3.3 Plot generation — `pgfplots` with external CSV data

Plots inside the LaTeX output are rendered by the
[`pgfplots`](https://www.overleaf.com/learn/latex/Pgfplots_package)
package directly, not by a pre-rendered raster or vector
image. Each fit plot becomes a `\begin{tikzpicture}` block in
`<project>.tex` that loads its data from a sibling CSV file:

```latex
\begin{figure}[H]
\centering
\begin{tikzpicture}
\begin{axis}[width=\linewidth, xlabel={$2\theta$ (deg)},
             ylabel={Intensity (arb. units)},
             legend pos=north east]
  \addplot[only marks, mark size=0.5pt]
    table[x=two_theta, y=meas, col sep=comma]
    {data/fit_<expt>.csv};
  \addlegendentry{Measured};
  \addplot[no markers]
    table[x=two_theta, y=calc, col sep=comma]
    {data/fit_<expt>.csv};
  \addlegendentry{Calculated};
  \addplot[no markers, dashed]
    table[x=two_theta, y=diff, col sep=comma]
    {data/fit_<expt>.csv};
  \addlegendentry{Difference};
\end{axis}
\end{tikzpicture}
\caption{Fit quality for experiment <expt>.}
\end{figure}
```

Data files at `reports/tex/data/fit_<expt_id>.csv` carry one
column per series (`x`, `meas`, `calc`, `diff`, optionally
`background`). Powder profiles with thousands of points stay
in CSV; pgfplots reads them at compile time.

**Why pgfplots and not pre-rendered images.**

- **No Python image renderer needed.** Removes `kaleido` and
  the headless-Chromium dependency chain that earlier drafts
  carried, plus the cross-platform `chromium` packaging
  problem on conda-forge.
- **Editable.** A user opening the PDF source can tweak
  axis labels, colours, legend, or marker size by editing
  the `\begin{axis}[...]` options directly in
  `<project>.tex`. The CSV stays untouched.
- **Native LaTeX typography.** Axis labels, legends, and
  captions render in the same font family as the surrounding
  document. No font-hinting mismatch the way there would be
  with a Plotly-rendered PNG/PDF.
- **`pgfplots` is on every modern TeX distribution.**
  `tectonic` resolves it on demand from CTAN; TeX Live and
  MiKTeX ship it in their default sets. No extra
  vendoring.

**Caveats.**

- Compile-time scales with the data-point count. Powder
  patterns with ~50K points compile in seconds, not
  milliseconds; the implementer can downsample for very
  large patterns via a `pgfplots` `each nth point=N` option
  if compile time becomes noticeable. This is a tuning knob
  for the renderer, not an ADR-level decision.
- The HTML output remains Plotly-based (interactive in the
  browser); the LaTeX output is pgfplots-based (static in
  the PDF). The two have **different visual styling** by
  design — there is no shared figure-rendering library and
  no "pixel-identical" claim. Sharing the same source data
  (the project state via the data context) is the only
  consistency guarantee.

**Dependencies named by this ADR.** The implementation plan
must name one dependency before any `/draft-impl-1` or
`/draft-impl-2` invocation edits `pyproject.toml`, `pixi.toml`,
or `pixi.lock`:

- `tectonic` — pixi/conda package, lightweight TeX engine for
  §3.4 PDF compilation in the project dev environment.
  `tectonic` auto-resolves `pgfplots` and any other
  TeX-package dependency from CTAN on first use.

Neither `kaleido` nor a browser is a dependency. The earlier
draft's `kaleido` + `chromium` chain is dropped wholesale.

Per AGENTS.md §Architecture, "an accepted plan that **names
the specific dependency** … combined with the user invoking
`/draft-impl-1` or `/draft-impl-2` for that plan … counts as
pre-approval." This ADR does **not** itself pre-approve the
dependency edits; the plan does. The ADR names `tectonic`
here so the plan author has the canonical list and the
implementer can edit dependency files autonomously once the
plan is accepted and the implementation shortcut is invoked.

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
- If none is found, the `.tex`, `data/`, and `styles/` are still
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

One context-builder method on the `project.report` facade.
Descriptors expose their `DisplayHandler` (§1.5) through the
context so the templates can consume `display_name` /
`display_units` for HTML / GUI rendering and `latex_name` /
`latex_units` for LaTeX, with graceful fallback to plain
`name` / `units` when no handler is attached:

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
        # Raw, serialisable fit data per experiment — the
        # single source of truth for both the HTML Plotly
        # builder and the LaTeX pgfplots CSV emitter. No
        # pre-rendered Plotly HTML in the context; that would
        # bind the data to one renderer.
        'experiments': [
            {
                ...,
                'fit_data': {
                    # X-axis carries values + labels pre-resolved
                    # through the DisplayHandler chain from §1.5.
                    # `name`/`units` are the **descriptor**'s
                    # underlying strings — both ASCII Python
                    # identifiers (`name` snake_case, `units` from
                    # the DDLm `_units.code` vocabulary). They are
                    # not CIF tags or tag fragments. `display_*` /
                    # `latex_*` are resolved once at builder time
                    # so neither template has to re-derive them.
                    # No enumerated `x_label` — any descriptor
                    # (Bragg powder `two_theta`, TOF
                    # `time_of_flight`, total-scattering `r`,
                    # future `q`, …) drops in by exposing a
                    # `DisplayHandler` and falls back gracefully if
                    # none is attached.
                    'x': {
                        'values':        [...],
                        'name':          'two_theta', # or 'time_of_flight', 'r', …
                        'units':         'degrees',   # ASCII CIF DDLm unit code
                        'display_name':  '2θ',
                        'latex_name':    r'$2\theta$',
                        'display_units': '°',
                        'latex_units':   r'$\deg$',
                    },
                    # Each y-series carries values + an optional
                    # uncertainty array + a label string. The label
                    # is the resolved display/latex form for the
                    # current renderer, picked at builder time.
                    'series': {
                        'meas': {'values': [...], 'su': [...], 'label': 'Measured'},
                        'calc': {'values': [...], 'label': 'Calculated'},
                        'diff': {'values': [...], 'label': 'Difference'},
                        'bkg':  {'values': [...], 'label': 'Background'},  # optional
                    },
                },
            }
            for e in self.project.experiments.values()
        ],
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
        'metadata': {
            'easydiffraction_version': ...,
            'generated_at': ...,
        },
    }
```

Templates live under `src/easydiffraction/report/templates/`:

```
templates/
  base.j2                       # shared macros (parameter row, uncertainty fmt)
  html/
    report.html.j2
    style.css
  tex/
    report.tex.j2               # single LaTeX template — emits
                                # \documentclass[11pt,a4paper]{iucrjournals}
                                # and the project-category-based body
                                # (Project Summary, Software, Refinement,
                                # Structures, Experiments).
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
| `project.report.formats = ['tex']`        | `project.report.save_tex()`          | `ed save-report --tex`                 |
| `project.report.formats = ['pdf']`        | `project.report.save_pdf()`          | `ed save-report --pdf`                 |
| `project.report.html_offline = True`      | `save_html(offline=True)`            | `--html --offline`                    |

### 8. Fields the library currently lacks

The HTML/LaTeX renderers need three derived fields plus the
display-metadata mechanism from §1.5; this ADR scopes them all as
in-scope work:

- `structures[i].crystal_system` — derivable from
  `space_group.name_h_m`, but not currently exposed as a property.
- `experiments[i].measured_range` — `min`, `max`, `inc` triple from
  the underlying data arrays. Not currently exposed as a property on
  `Experiment`.
- `analysis.parameter_counts` — total / free / fixed / constrained.
  Free and fixed are derivable from
  `project.free_parameters`; total and constrained need a single
  aggregating helper.
- **Descriptor display metadata (§1.5).** The
  `display_handler=DisplayHandler(...)` kwarg is added to every
  descriptor base class. The implementation plan sweeps existing
  `units=` Unicode strings to ASCII (CIF DDLm `_units.code`
  vocabulary) and attaches `DisplayHandler` instances to atom-site,
  cell, fit-result, peak, and other parameters the renderers
  surface. Descriptors without a handler keep working — they
  fall back to plain `name`/`units` in every renderer.

The first three are pure derived properties — no new state, no
persistence beyond what already exists. The fourth is the
descriptor-level mechanism from §1.5; it is library-wide and
benefits every renderer (HTML, PDF, terminal, GUI) simultaneously.

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
- Single LaTeX style (`iucrjournals`) keeps the v1 surface
  small: no style enum, no `_report.style` config field, no
  multi-class vendored bundle. Future styles add via a new
  ADR alongside the new class files.

### Trade-offs

- All report outputs are opt-in. Default
  `project.report.formats = []` means daily `project.save()`
  calls write only project files — `reports/` isn't created
  until a format is configured (or an ad-hoc method is called).
- HTML is small (~50–300 KB CDN-mode, ~few MB offline); users
  who want it on every save add `'html'` to
  `project.report.formats` once.
- LaTeX bundle (`reports/tex/` + `reports/<project>.pdf`) is a
  handful of files (`.tex`, CSV data per experiment, two
  vendored class/style files, compiled PDF) — only written
  when `'tex'` or `'pdf'` is in `project.report.formats` (or
  an ad-hoc `save_tex()` / `save_pdf()` call is made). Total
  per-save footprint is dominated by the CSVs; the
  `tex/styles/` directory holds ~20 KB across 2 files.
- One upstream snapshot vendored in the repository
  (`iucrjournals.cls` + `harvard.sty`, CC0 1.0). The plan
  refreshes the snapshot when upstream releases a new
  version; the licence text is copied into the package's
  licensing documentation alongside the wheel's BSD-3-Clause
  `LICENSE` with attribution.
- **No Python image renderer in the LaTeX path.** The earlier
  draft's `kaleido` runtime dependency and the matching
  Chrome/Chromium browser requirement are both dropped in
  favour of `pgfplots` reading the project's CSV data
  directly. The HTML output remains Plotly-based (interactive
  in the browser); the LaTeX output is pgfplots-based (static
  in the PDF). The two renderings share the underlying data
  but not the visual styling — see §3 and §3.3 for the
  rationale.
- PDF compilation is opportunistic — works when `tectonic`,
  `latexmk`, or `pdflatex` is on `PATH`; otherwise the `.tex`
  and the `data/` CSV files are still written and the user
  gets a clear one-line install hint (`pixi add tectonic` is
  the recommended path).
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
     (§1.1, §1.3) — five scalar items persisted to `project.cif`
     (`_report.cif`, `_report.html`, `_report.tex`, `_report.pdf`,
     `_report.html_offline`). The Python-side
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
     `save_tex()`, `save_pdf()`. The earlier draft's
     `save(cif=True, html=True, tex=True, pdf=True, style=,
     check=)` flag bundle is dropped.
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
     `project.cif`, five scalar items per §1.1 / §1.3) that the
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
  - `project.report.*` ↔ `_report.*` — five scalar items (four
    format booleans plus `html_offline`) per §1.3.
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
- **`units=` sweep — backward compatibility.** Existing
  descriptors use Unicode short-form units (`'Å'`, `'Å²'`,
  `'°'`). The §1.5 convention is ASCII (CIF DDLm `_units.code`:
  `'angstroms'`, `'angstrom_squared'`, `'degrees'`).
  Audit the project for external readers of `descriptor.units`
  before the plan runs the sweep — tutorial sources, the
  display layer, third-party scripts that may depend on the
  Unicode value via `parameter.units`. Confirm whether any
  consumer hard-codes the Unicode strings (literal `'Å²'`
  comparison) and would need updating alongside the sweep.
  Recommendation: project-internal callers move to
  `parameter.display_handler.display_units` when present, with
  fallback to `parameter.units`; the sweep is a same-PR change.

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
- **Multi-style LaTeX support.** v1 ships only `iucrjournals`
  with no style selector and no `_report.style` config field.
  Adding a second style (REVTeX 4.2, Elsevier `elsarticle`,
  Springer `svjour3`, etc.) is a follow-up ADR that
  reintroduces:
  - a `ReportStyleEnum` (per the closed-values ADR),
  - a `_report.style` config field on `project.report`,
  - a `style=` arg on `save_tex()` / `save_pdf()`,
  - a `--style` CLI flag on `ed save-report`,
  - vendored class files for the new style.
  
  The renderer in v1 hardcodes `iucrjournals`; reintroducing
  the selector is a contained change, not a rewrite, but it
  is its own ADR so the design conversation does not relitigate
  on each new template request.
- **Bibliography support** (`iucr.bib` / `iucr.bst`). IUCr
  ships bibliography styles for citing IUCr publications.
  Not bundled in v1 because the v1 report mirrors internal
  category structure rather than producing a manuscript with
  references. Add when users produce full manuscripts from
  the library.
- **Snapshot-refresh automation.** A small `pixi` task to
  re-fetch the upstream IUCr source and diff against the
  vendored snapshot would help track when IUCr releases a
  new version. v1 refreshes by hand during plan work.
- **Larger-pattern pgfplots tuning.** Powder patterns with
  ~50K points compile in pgfplots in seconds. If users
  produce significantly larger patterns and compile time
  becomes uncomfortable, the renderer can downsample via
  `pgfplots`'s `each nth point=N` option, or switch to
  matplotlib-rendered PDF figures for the LaTeX path while
  keeping pgfplots as the default. Tune when needed.
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
project.report.html_offline = False         # Plotly via CDN (default) or inlined

project.save()
# → project.cif (with the _report.* config)
# → structures/, experiments/, analysis/ as before
# → reports/<project>.cif and reports/<project>.html per config
```

Per-format ad-hoc methods cover one-offs without changing the
persisted config:
`project.report.save_html(offline=False)`,
`save_cif()`, `save_tex()`, `save_pdf()`.
The CLI mirrors with a new subcommand,
`ed save-report --cif --html --tex --pdf` (also a one-off;
`ed save` reads the persisted config).

The LaTeX bundle ships `<project>.tex`, CSV data per
experiment, and the `iucrjournals` vendored style under
`reports/tex/`. The compiled `<project>.pdf` is written one
level up (next to the CIF and HTML) when a TeX engine —
`tectonic` (recommended, conda-forge), `latexmk`, or `pdflatex`
— is on `PATH`. The `.tex` document mirrors the project's own
category-based structure (Project Summary, Software,
Refinement, Structures, Experiments) rather than imitating an
IUCr journal-submission manuscript — "typeset Python state",
not a ready-to-submit manuscript.

Plots inside the LaTeX output are rendered by `pgfplots`
reading the CSV data at compile time. The HTML output stays
Plotly-based (interactive in the browser); the LaTeX output
is pgfplots-based (static in the PDF). The two share the
underlying data but not the visual styling — there is no
shared figure-rendering library, no pixel-equality claim, and
no Python image-rendering dependency in the LaTeX path
(`kaleido` and the browser dependency from earlier drafts are
both gone).

Adds an `analysis.software` Python category — three-role triple
(framework / calculator / minimizer) matching the alignment ADR's
`_easydiffraction_software.*` CIF emission — recording engines,
versions, and URLs at fit time so every report carries
authoritative provenance. The library, the CLI, and the GUI all
consume the same in-memory report data (`project.report.data_context()`)
— no code path renders independently. This keeps the forthcoming
GUI Summary tab in lockstep with the library.
