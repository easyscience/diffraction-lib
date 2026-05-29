# ADR: Project Summary Rendering

**Status:** Accepted  
**Date:** 2026-05-26

Defines the **non-CIF** human-readable rendering surface for a project:
what the terminal/Jupyter summary, the auto-generated HTML report, the
on-demand journal-style LaTeX export, and (eventually) the GUI Summary
tab all consume and emit.

Runs alongside, and **extends**, the accepted
[`iucr-cif-tag-alignment.md`](../accepted/iucr-cif-tag-alignment.md) ADR
(landed as PR #184). The alignment ADR established:

- A new `project.report` facade slot (replaces the unimplemented
  `project.summary` placeholder), with `save()` and `check()` methods.
- A single `reports/` directory at project root.
- A `project.save(report=True)` opt-in flag for the IUCr CIF.

That ADR currently scopes `project.report` to **CIF only** — the
multi-datablock IUCr submission CIF written to `reports/<project>.cif`.
This ADR keeps the facade and adds a **`project.report` configuration
category** with five scalar persisted fields (`cif`, `html`, `tex`,
`pdf`, `html_offline`) on `project.cif`, plus ad-hoc per-format methods
(`save_html()`, `save_cif()`, `save_tex()`, `save_pdf()`). The
Python-side API uses those same boolean descriptors directly, matching
the persisted CIF shape. The LaTeX writer hardcodes `iucrjournals` as
its document class — there is no style selector, no `_report.style`
field, no `style=` arg on `save_tex()` / `save_pdf()`. The accepted IUCr
`project.save(report=True)` flag is **removed**; reports come from the
config category, not from boolean flags. All four format booleans
default to `False` so `project.save()` writes nothing under `reports/`
until the user configures otherwise, preserving the "no surprise files"
property.

Coordination points with the alignment ADR (no blocking conflicts; its
Open Questions section is empty):

- **Software-stack identification** — the alignment ADR's §2.3a-i
  defines `_easydiffraction_software.{framework, calculator, minimizer}`
  as the structured CIF emission, plus a concatenated
  `_computing.structure_refinement` free-text string. This ADR's §4
  adopts the same three-role triple as the Python-side attribute layout
  so the same data flows into both write paths.
- **Spec-compliance validation** — the alignment ADR's §2.5 added
  `project.report.check()` (gemmi-based) and a `check=True` flag on
  `project.report.save()`. This ADR **removes the public surface** and
  moves the gemmi pass to an internal pre-write step **inside the CIF
  emission paths only** — `save_cif()` and the `cif` branch under
  `project.save()` (§1.4). HTML, TeX, and PDF outputs are not
  gemmi-validatable and get no pre-write validation; LaTeX errors
  surface at PDF-compile time via the TeX engine. A writer that emits
  non-compliant CIF raises `EasyDiffractionWriterError` instead. This
  ADR's deferred `check_completeness()` (publication-side completeness)
  is a separate concern that stays in Deferred Work.
- **Publication metadata source** — the alignment ADR's Deferred Work
  proposes a user-supplied `reports/publ_info.{toml,json}` to replace
  `?` placeholders. Both write paths read the same Python attribute,
  **`project.publication`** — a new top-level on `Project`, sibling to
  `project.info` and `project.analysis`. The schema is defined in §5 of
  this ADR: six CIF-aligned sibling categories (`journal`,
  `journal_date`, `journal_coeditor`, `contact_author`, `body`,
  `authors`) with full IUCr-tag fidelity. The loader accepts TOML
  (primary) and JSON (fallback); selection is by file extension.

Also touches:

- [`analysis-cif-fit-state.md`](../accepted/analysis-cif-fit-state.md) —
  adds an `analysis.software` provenance category that serialises
  through the analysis tier.
- [`minimizer-input-output-split.md`](../accepted/minimizer-input-output-split.md)
  — the new provenance category lives alongside the existing
  minimizer/fit-result pairing, not inside it.
- [`project-facade-and-persistence.md`](../accepted/project-facade-and-persistence.md)
  — two changes: `project.report` gains a persisted configuration
  category (`_report.*` in `project.cif`, see §1.3), turning the facade
  into a hybrid of helper methods plus persisted config; and a new
  top-level `project.publication` owner is added alongside the existing
  `project.info`, `project.structures`, `project.experiments`,
  `project.analysis`, `project.report` facade slots (see §5).
- [`python-cif-category-correspondence.md`](python-cif-category-correspondence.md)
  — owns the Python↔CIF correspondence rule for **two** new
  project-level singleton surfaces: `project.report.* ↔ _report.*` (five
  scalar items, §1.3) and `project.publication.*` sibling categories ↔
  `_journal.*`, `_publ_author.*`, `_publ_contact_author.*`, etc. (§5).

## Context

The library today has four shapes of summary output:

- `Report.show_report()` and friends — terminal/Jupyter rendering of
  project metadata, crystallographic data per phase, experimental
  configuration, and fit metrics
  ([report.py](../../../../src/easydiffraction/report/report.py)).
  (Pre-PR #184 this was `Summary.show_report()` on `project.summary`;
  the IUCr alignment ADR replaced the unimplemented placeholder.)
- `summary.cif` — was written into the project root on every
  `project.save()` as the literal string `"To be added..."` until PR
  #184 removed both the writer call and the placeholder method. Not a
  valid CIF block in any version that shipped.
- The old GUI's "Summary" tab — a single page listing project info,
  crystal data, data collection, refinement engine + goodness-of-fit,
  with an "Export summary" panel (Name, Format = HTML, Location).
- An eventual journal manuscript — currently produced by hand from the
  scientist's notes and the values shown in the GUI Summary tab.

These four are renderings of the **same** logical view. Every field the
GUI shows is already reachable from the live Python objects; the summary
is not a source of truth and has no field of its own that isn't
computable from `project`, its `structures`, its `experiments`, and
`analysis.fit_results`. The exception is software provenance — which
calculation engine and minimizer (with versions) produced the fit —
which the library does not currently capture anywhere.

Two pressures act on the design:

- **GUI consistency.** The library and the GUI must show the same
  numbers from the same data flow. The GUI Summary tab needs a
  programmatic API, not a CIF or an HTML file to re-parse.
- **Submission-grade output.** Scientists publish in IUCr journals,
  Phys. Rev. B, J. Appl. Cryst., and others. The CIF side of that is
  covered by the alignment ADR's IUCr export. The **manuscript** side
  (refinement tables formatted to journal style) is not.

The default-save `summary.cif` placeholder was the visible artefact of
the unresolved design question. The alignment ADR has since replaced the
unimplemented `project.summary` slot with a `project.report` facade
scoped to IUCr CIF generation (`reports/<project>.cif`). That resolves
the CIF half of the question but leaves the GUI Summary tab, the
terminal `show_report()`, the human-readable HTML, and the
manuscript-bound LaTeX/PDF without a definition. This ADR fills the gap
by extending the same `project.report` facade with non-CIF rendering
surfaces.

## Scope

In scope:

- Extend the alignment ADR's `project.report` facade with
  terminal/Jupyter, HTML, and LaTeX rendering surfaces, a configuration
  category (five scalar fields —
  `project.report.{cif, html, tex, pdf, html_offline}` — persisted in
  `project.cif`), and ad-hoc per-format save methods. **All report
  formats are opt-in via the configuration; every format defaults to
  `False` so `project.save()` writes nothing under `reports/` until a
  format is enabled** — see §1 and §2 for the rationale.
- Define the shared "summary data context" (one dictionary) that
  terminal, HTML, LaTeX, and GUI renderers all consume.
- Add a Python-side software-provenance category on `analysis`
  (`analysis.software`) recording calculation-engine and
  minimization-engine name + version + URL stamped at fit time.
  Persisted in `analysis/analysis.cif` (amends the IUCr ADR's "Analysis
  — unchanged" stance for these fields; see §4 and the ADRs-amended
  list).
- Add a new top-level `project.publication` owner on `Project` (sibling
  to `project.info`, `project.structures`, `project.experiments`,
  `project.analysis`, `project.report`) carrying the `_publ_*` /
  `_journal_*` publication metadata the IUCr writer otherwise emits as
  `?` placeholders. See §5; amends `project-facade-and-persistence.md`
  and complements `python-cif-category-correspondence.md`.
- Ship exactly one LaTeX style (`iucrjournals`) — no style selector, no
  `ReportStyleEnum`, no `_report.style` field. Multi-style support
  (REVTeX, Elsevier, etc.) is deferred to a follow-up ADR; see "Deferred
  Work".

Out of scope:

- CIF tag-name decisions for any serialised field. Those are the
  alignment ADR's job; this ADR notes recommended mappings and
  cross-references.
- The IUCr CIF submission export tag policy and multi-datablock layout.
  Covered by the alignment ADR; the output file lives at
  `reports/<project>.cif` and is opt-in via `project.report.cif = True`.
- Pre-existing project-level singleton categories (`_info.*`,
  `_chart.*`, `_table.*`, `_verbosity.*`). Covered by the in-flight
  [`python-cif-category-correspondence.md`](python-cif-category-correspondence.md).
  This ADR **does** add one new project-level singleton category,
  `_report.*`, alongside them (see §1.3 and the ADRs-amended list); that
  surface is not delegated to the correspondence ADR.
- Static-image PDF generation. HTML prints from any browser; LaTeX
  compiles to PDF locally. No bundled PDF writer.
- Markdown export. Trivial follow-on if the Jinja base templates are in
  place, but no current user requirement.

## Design Philosophy: Summary as a View

Summary is a **derived view**, not a persisted artifact. The same data
dictionary feeds every renderer:

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

Render targets never duplicate the data — they consume the same context.
New summary fields are added in one place (the context builder); every
renderer picks them up.

## Decision

### 1. Extend `project.report` with rendering methods and a config category

The alignment ADR has already created the `project.report` facade
(replacing the unimplemented `project.summary` placeholder). This ADR
extends it along two axes:

- A new **configuration category** on `project.report` — persisted in
  `project.cif`, matching the existing `project.chart`, `project.table`,
  `project.verbosity` config pattern — that records _which_ report
  formats `project.save()` emits and _how_.
- A new set of **ad-hoc per-format methods** for explicit one-off writes
  that bypass the configuration.

The accepted IUCr `project.save(report=True)` flag and the public
`project.report.check()` method are both **removed** (see the
ADRs-amended list). Reports come from configuration, not boolean flags;
dictionary-spec validation runs internally before every CIF write (and
only before CIF writes — HTML, TeX, and PDF have no spec to validate
against; see §1.4) and surfaces as an error on writer bugs, not as a
user opt-in.

#### 1.1 Configuration category — `project.report.*`

Persisted fields on `project.report`, populated by the user once and
read by `project.save()` thereafter:

| Field                         | Type   | Default | Effect                                                                                                                                                                                    |
| ----------------------------- | ------ | ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `project.report.cif`          | `bool` | `False` | When `True`, `project.save()` writes `reports/<project>.cif`.                                                                                                                             |
| `project.report.html`         | `bool` | `False` | When `True`, `project.save()` writes `reports/<project>.html`.                                                                                                                            |
| `project.report.tex`          | `bool` | `False` | When `True`, `project.save()` writes `reports/tex/{<project>.tex, data/, styles/}`.                                                                                                       |
| `project.report.pdf`          | `bool` | `False` | When `True`, `project.save()` writes `reports/<project>.pdf` (and `tex/` as a side-effect).                                                                                               |
| `project.report.html_offline` | `bool` | `False` | When `True`, the HTML report is **fully self-contained** — inline-bundles both Plotly and MathJax (~3 MB + ~1.5 MB on top of the otherwise-empty document). Otherwise both load from CDN. |

Four per-format scalar booleans (`cif`, `html`, `tex`, `pdf`) plus
`html_offline` — **five fields total**, all single-row in CIF. Matches
the existing `project.chart`, `project.table`, `project.verbosity`
scalar-config shape verbatim. All booleans default to `False`, so an
unconfigured project produces no `reports/` directory at all.

There is no `style` field. The LaTeX output ships exactly one class
(`iucrjournals`); adding another style is deferred work, not a v1
selector. See §3 for the reasoning behind the single-style choice.

There is no separate list-style `project.report.formats` property. The
Python API intentionally mirrors CIF and the other project-level
configuration categories: each persisted scalar descriptor is set
directly.

```python
import easydiffraction as ed

project = ed.Project()
# … set up structures, experiments, run fit …

# Configure once — persisted in project.cif (see §1.3 below).
project.report.cif = True
project.report.html = True
project.report.html_offline = False

# Every subsequent save now emits the configured reports too.
project.save()
# → project.cif (with _report.* config block)
# → structures/<...>.cif, experiments/<...>.cif, analysis/analysis.cif
# → reports/<project>.cif  (because project.report.cif is True)
# → reports/<project>.html (because project.report.html is True)
```

##### Enum backing per the closed-values ADR

The set of report formats is a finite closed set, so per the accepted
[`enum-backed-closed-values.md`](../accepted/enum-backed-closed-values.md)
contract it is represented internally as `(str, Enum)`:

```python
class ReportFormatEnum(str, Enum):
    CIF = 'cif'
    HTML = 'html'
    TEX = 'tex'
    PDF = 'pdf'
```

The four per-format booleans (`project.report.cif`, `.html`, `.tex`,
`.pdf`) are the public configuration API. Internal save dispatch may use
`ReportFormatEnum` members to keep the finite format set explicit, but
the enum is not a user-facing selector.

There is no `ReportStyleEnum`. The LaTeX writer hardcodes `iucrjournals`
as its document class (see §3); when a future ADR adds a second style,
the `ReportStyleEnum` is reintroduced together with a new
`_report.style` config field.

#### 1.2 Ad-hoc per-format methods

Each format has its own explicit write method on the facade, independent
of the persisted report booleans. Use when a user wants to produce a
one-off artifact without changing the persistent configuration.

```python
project.report.save_cif()                        # writes reports/<project>.cif
project.report.save_html(offline: bool = False)  # writes reports/<project>.html
project.report.save_tex()                        # writes reports/tex/{<project>.tex, ...}
project.report.save_pdf()                        # writes reports/<project>.pdf (compiles TeX too)

# Convenience: write every report enabled by project.report booleans.
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

Per-format method signatures only carry the args that apply to that
format — `save_html(offline=True)` is unambiguous; there is no
`save_tex(style=...)` because the LaTeX writer ships exactly one style
(`iucrjournals`), so a style selector would be dead weight. The
cross-format mixing that the earlier flag-based draft had
(`html_offline` ignored when `html=False`, `style=` ignored without
`tex=True`) is gone.

`project.save()` itself takes no report-related arguments. The accepted
IUCr `project.save(report=True)` flag is removed (see ADRs amended);
reports are configured on `project.report.*`.

```python
project.save()           # writes project files + enabled report booleans
```

`Summary.as_cif()` and `summary_to_cif()` were already deleted by the
alignment ADR; this ADR's removal of `project.save(report=True)`
finishes the flag-cleanup.

**Empty-configuration behaviour split.**

The two entry points behave differently when no formats are enabled — a
deliberate split: `project.save()` writes the project regardless
(reports are a side-effect of configuration, not the point of the call);
`project.report.save()` is _only_ about reports, so calling it with
nothing configured is a user error.

```python
# project.report.{cif,html,tex,pdf} == False  (default — unconfigured)

project.save()
# → writes project.cif + structures/ + experiments/ + analysis/
# → reports/ is NOT created (no formats enabled — correct default
#   behaviour, no error, no warning).

project.report.save()
# → raises:
#   ValueError(
#       "project.report.save() called with no formats enabled. "
#       "Set project.report.{cif,html,tex,pdf} = True, or call a per-format "
#       "method directly (project.report.save_html(), etc.)."
#   )
```

The Python error matches the CLI's existing behaviour for
`ed save-report` with no flags (§7) — both surfaces refuse to silently
no-op when the user explicitly asked for a report. `project.save()`
keeps the no-report default because the user asked to save the project,
not the reports.

The per-format methods (`save_cif()`, `save_html()`, etc.) never inspect
the persisted report booleans — they always write their format
unconditionally. They are explicit one-offs.

#### 1.3 CIF persistence of the configuration

The configuration category serialises to `project.cif` next to the other
project-level singleton categories (`_info.*`, `_chart.*`, `_table.*`,
`_verbosity.*`). The CIF tag prefix is `_report.*` — a Set category with
five scalar items, no loops:

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

All five items are scalar DDLm dotted entries — the category is declared
`_definition.class Set` so a single value per item, no loops permitted.
Matches the existing `_chart.*`, `_table.*`, `_verbosity.*` category
shape exactly. The `yes`/`no` boolean encoding follows the project's
existing CIF boolean convention.

The default unconfigured state writes four explicit `no` values for the
format booleans (not an absent or empty representation), so the "no
formats enabled" condition is always a concrete CIF value, never an
empty loop or missing block:

```text
# Default (project.report.{cif,html,tex,pdf} = False):
_report.cif           no
_report.html          no
_report.tex           no
_report.pdf           no
_report.html_offline  no
```

Load semantics are symmetric: every `no` reads back as `False` on its
descriptor; the `formats` property view returns `[]`.

The four per-format booleans give the IUCr-aware tooling (`gemmi`,
`publCIF`) a typed, validatable view of the configuration — each format
is a known enum item with type `Boolean`, not a parsed string. There is
no additional Python list view with separate storage; the booleans are
the source of truth.

Adding a new format in the future (e.g. `markdown`) is a one-line schema
extension: add `_report.markdown` to the dictionary and a
`project.report.markdown` boolean to the descriptor, then include it in
the internal save dispatch.

Loading a `project.cif` populates `project.report.*` per the
project-facade-and-persistence contract; on the next `project.save()`,
the configured formats emit automatically with no further user action.

##### Why not its own CIF file?

The project already has two distinct facade patterns for top-level
`project.*` slots, used deliberately for different purposes.
`project.report` is **Pattern A** — lightweight project-level singleton
config — not Pattern B — heavy datablock owner with its own CIF file.
The split is summarised below.

| Slot                                 | Pattern | CIF location                             | Python shape                                         |
| ------------------------------------ | ------- | ---------------------------------------- | ---------------------------------------------------- |
| `project.info`                       | A       | `project.cif` (`_info.*`)                | small `CategoryItem`                                 |
| `project.chart`                      | A       | `project.cif` (`_chart.*`)               | `CategoryItem` (one field)                           |
| `project.table`                      | A       | `project.cif` (`_table.*`)               | `CategoryItem` (one field)                           |
| `project.verbosity`                  | A       | `project.cif` (`_verbosity.*`)           | `CategoryItem` (one field)                           |
| **`project.report`** (this ADR)      | **A**   | **`project.cif` (`_report.*`)**          | **`CategoryItem` (five fields) plus action methods** |
| `project.publication` (this ADR, §5) | A       | `project.cif` (`_publ_*` / `_journal_*`) | `CategoryOwner` of six sibling categories            |
| `project.analysis`                   | B       | `analysis/analysis.cif`                  | `CategoryOwner` (heavy datablock)                    |
| `project.structures[name]`           | B       | `structures/<name>.cif`                  | `CategoryOwner` (heavy datablock)                    |
| `project.experiments[name]`          | B       | `experiments/<name>.cif`                 | `CategoryOwner` (heavy datablock)                    |

Reasons `project.report` is Pattern A, not Pattern B:

- Five scalar config items do not justify a separate file
  (`reports/report.cif` would be a tiny file holding five lines).
- A `reports/report.cif` would force the `reports/` directory to exist
  even when every format boolean is `False` and no reports are written —
  breaks the "no surprise files" property the design is built around.
- Splits report configuration from chart / table / verbosity
  configuration, which already share `project.cif` for the same reason —
  they are all project-level preferences, not domain data.

What makes `project.report` look heavier than `project.chart` /
`project.table` / `project.verbosity` is the action methods on the
facade (`save_cif()`, `save_html()`, `show_report()`, `data_context()`,
etc.). Those live on the Python class alongside the configuration
fields, which is the facade-hybrid amendment to
`project-facade-and-persistence.md` already recorded in the ADRs-amended
list. The action methods do not change where the configuration persists
— that stays in `project.cif`.

#### 1.4 Validation moves internal — CIF only, writer-correctness only

The accepted IUCr ADR §2.5 exposed `project.report.check()` and a
`check=True` flag for gemmi-based dictionary-spec validation. Both are
**removed** in favour of a pre-write self-check inside the CIF emission
paths only:

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

| Output                   | Validation                                                         | Failure mode                                                                       |
| ------------------------ | ------------------------------------------------------------------ | ---------------------------------------------------------------------------------- |
| `reports/<project>.cif`  | gemmi parse always; dictionary checks when local dictionaries load | `EasyDiffractionWriterError` for malformed generated CIF or dictionary diagnostics |
| `reports/<project>.html` | none at write time                                                 | n/a — HTML is a render of the data context, not a typed format                     |
| `reports/tex/`           | none at write time                                                 | n/a — LaTeX errors surface at PDF-compile time, with the engine's message          |
| `reports/<project>.pdf`  | TeX engine's own compilation (returns non-zero on error)           | engine-specific message; the `.tex` and `data/` CSVs are still written             |

The dictionaries under `tmp/iucr-dicts/` are optional local validation
aids, not report inputs. If Gemmi cannot load those local dictionary
files, the writer skips dictionary-specific checks after confirming the
generated CIF itself parses; this avoids blocking report generation on a
stale or incompatible dictionary cache.

User-input validation (e.g., "is the email address syntactically
valid?", "is the ORCID well-formed?") happens **upstream** at the
descriptor's `value_spec` validator — the same boundary where every
other user input is checked. That's a separate concern from the writer
self-check above: descriptor validators raise `typeguard.TypeCheckError`
or the project's `ValidationError` at _assignment time_, before any save
is attempted. By the time the writer runs, the values it receives are
already shape-correct; the gemmi pass on the CIF output catches _writer_
bugs (wrong tag, wrong type, malformed loop), not user bugs.

Rationale: dictionary compliance is a _writer-correctness_ property, not
a user choice. A user can't fix a non-compliant emission without
modifying project state — and even then, the writer should refuse to
emit a malformed file in the first place. Making validation a
user-visible API surface invites users to skip it; making it internal
makes it impossible to skip. Cached dictionary parsing keeps the
overhead to a one-time ~200 ms session cost. The
`EasyDiffractionWriterError` includes the full gemmi diagnostic so bug
reports are actionable.

A separate, _completeness_-oriented check
(`project.report.check_completeness()`) — flagging unfilled `_publ_*` /
`_journal_*` placeholders for journal submission, which is a
publication-readiness question rather than a writer-correctness one — is
a different concern and stays in Deferred Work.

#### 1.5 Descriptor display metadata — `DisplayHandler`

Parameter names like `u_iso` and unit strings like `Å²` need prettier
representations for the HTML and PDF renderers. The ADR introduces a new
optional handler on the descriptor base classes (`Parameter`,
`NumericDescriptor`, `StringDescriptor`) that carries the typeset
variants in a single place, sibling to the existing `cif_handler`:

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

`DisplayHandler` lives at `src/easydiffraction/core/display_handler.py`
alongside the existing `CifHandler` in
`src/easydiffraction/io/cif/handler.py` — a frozen dataclass per the
project's value-object convention (matches `TypeInfo`, `Compatibility`,
`CalculatorSupport` per AGENTS.md). `slots=True` keeps memory overhead
constant per attached descriptor.

The plain `name` and `units` fields keep their existing role on the
descriptor, but their **content convention changes**:

- `name` — Python identifier; ASCII snake_case; unchanged.
- `units` — **ASCII only**, following the CIF DDLm `_units.code`
  vocabulary from
  [`cif_core.dic`](../../../../tmp/iucr-dicts/cif_core.dic) **verbatim**
  when the dictionary defines a value for the unit. The dictionary's
  vocabulary is a single source of truth, but it is **not** uniformly
  plural — singular and plural forms appear mixed across units (each
  unit is whatever the dictionary actually says). Verified codes from
  `cif_core.dic`:

  | What we need          | `_units.code` value                      | Source line in cif_core.dic   |
  | --------------------- | ---------------------------------------- | ----------------------------- |
  | Å (length)            | `angstroms` (plural)                     | line 1213                     |
  | Å² (area)             | `angstrom_squared` (singular `angstrom`) | line 1178                     |
  | ° (angle)             | `degrees` (plural)                       | line 500, 519, 1247, …        |
  | K (temperature)       | `kelvins` (plural)                       | line 210, 232, 287, 316       |
  | Pa (pressure)         | `kilopascals` (plural)                   | line 115, 136, 161, 184       |
  | µs (time)             | `microseconds` (plural)                  | (from `cif_pow.dic` TOF text) |
  | Da (mass)             | `dalton` (singular)                      | line 753                      |
  | MGy (dose)            | `megagray` (singular)                    | line 592, 607                 |
  | Å⁻¹ (reciprocal)      | `reciprocal_angstroms`                   | line 795, 825                 |
  | Å⁻² (reciprocal area) | `reciprocal_angstrom_squared`            | line 1552, 1587               |
  | dimensionless         | `none`                                   | line 459, 480, …              |

- **Units the dictionary does not define.** The crystallographic
  vocabulary includes a handful of compound units that `cif_core.dic`
  does not assign a `_units.code` to — the one example currently in
  scope is `deg²` (squared degrees, used for some angular variance
  metrics). Convention for these: extend the same naming pattern
  (`degrees_squared`) as a **project-internal code** with no
  `_units.code` round-trip. The implementation plan keeps a small
  `units_vocabulary.py` module listing every code (dictionary and
  project-internal) so a sweep can validate every `units=` string at
  descriptor-declaration time.

The Unicode-symbol form (`Å²`) moves into `display_units`; the LaTeX
form (`\AA$^2$`) into `latex_units`.

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

| Renderer / context                       | Name uses                   | Units uses                   |
| ---------------------------------------- | --------------------------- | ---------------------------- |
| LaTeX (`save_tex`)                       | `$U_{\mathrm{iso}}$`        | `\AA$^2$`                    |
| HTML (`save_html`, MathJax-rendered)     | `$U_{\mathrm{iso}}$`        | `\AA$^2$`                    |
| HTML pre-MathJax / GUI / `show_report()` | `Uiso`                      | `Å²`                         |
| `project.report.data_context()` raw dict | both available              | both available               |
| CIF emission                             | `_atom_site.U_iso_or_equiv` | (no `_units.code` row today) |
| Python code / repr                       | `u_iso`                     | `angstrom_squared`           |

##### Resolution rules

The renderers consult the `DisplayHandler` (if attached) using a
per-context fallback chain:

- **LaTeX context** (`save_tex`, `save_pdf`, `as_tex`):
  `handler.latex_name or descriptor.name`,
  `handler.latex_units or descriptor.units`.
- **HTML context** (`save_html`, `as_html`):
  `handler.display_name or descriptor.name`,
  `handler.display_units or descriptor.units`. The HTML template
  additionally surrounds `handler.latex_name` / `handler.latex_units`
  with `\(...\)` math delimiters so MathJax picks them up where the
  descriptor has typeset variants — i.e., HTML can show the same
  `$U_{\mathrm{iso}}$` the PDF shows, while a GUI tooltip or
  `show_report()` printout falls back to `display_*`.
- **GUI / terminal / `show_*()` context**:
  `handler.display_name or descriptor.name`,
  `handler.display_units or descriptor.units`.

Each chain falls through to the descriptor's plain fields, so
**descriptors without a `display_handler` continue to work unchanged** —
they simply render as `u_iso` / `angstrom_squared` in all contexts.
Adding a `display_handler` is opt-in per descriptor.

**Table-rendering paths MUST read through the resolution chain above,
not the plain `descriptor.units` field directly.** This is a strict
requirement because `units=` now holds ASCII CIF DDLm codes
(`'angstrom_squared'`) that would look ridiculous as a column header.
Concretely the following call sites migrate in the implementation sweep:

- Every `show_*()` method on `Report` (terminal / Jupyter table
  builders) — the unit column or row header is built from
  `display_units or units`, not `units` alone.
- Every Jinja macro in `templates/base.j2` that formats a parameter row
  — same resolution rule.
- The HTML template (`templates/html/report.html.j2`) uses
  `display_units` for non-math contexts and the latex_units variant
  inside `\(...\)` math delimiters where the descriptor declares both.
- The LaTeX template (`templates/tex/report.tex.j2`) uses `latex_units`
  (falling through `display_units` then `units` if not declared).
- The shared `data_context()` (§6) builder exposes both rendered strings
  per parameter so neither template has to re-derive the fallback chain
  — the resolution happens once in the builder.

External / third-party readers that hard-coded `parameter.units` to
compare against `'Å²'` (the prior Unicode form) are flagged in the Open
Questions section for a project-wide audit before the sweep lands.

##### Why a handler class instead of four kwargs

Two design pressures:

- The fields cluster — they are all "how to display this parameter" — so
  a single handler keeps the descriptor constructor flat.
  `display_handler=DisplayHandler(latex_name=..., display_name=...)`
  reads cleaner than four sibling kwargs.
- Future display targets (Markdown export, GUI tooltips, an
  ASCII-fallback for terminal narrow-mode) can add fields to
  `DisplayHandler` without growing the descriptor constructor signature.

The mechanism mirrors the existing `cif_handler=CifHandler(...)`
pattern, so anyone reading the descriptor declarations sees the same
shape for CIF metadata and display metadata.

##### Migration sweep

Existing descriptors use `units='Å'` / `'Å²'` / `'°'` etc. (Unicode
short forms). The implementation plan owns the sweep that:

- Converts every existing `units=` Unicode string to the ASCII CIF DDLm
  form (`'Å²'` → `'angstrom_squared'`).
- Adds `display_handler=DisplayHandler(...)` to descriptors the
  renderers benefit from prettifying (atom-site positions / ADPs, cell
  parameters, fit-result R-factors, refinement statistics, peak
  parameters, …). Descriptors the renderers don't show (CIF-only
  internal state) get no handler — the fallback to `name`/`units` is
  fine.
- Verifies the `_chart`, `_table`, `_verbosity` enum values and other
  singleton-config CIF strings don't accidentally collide with the new
  units vocabulary (they shouldn't — those are tag values, not unit
  codes).

The sweep is a Phase 1 step in the implementation plan, not an ADR-level
decision.

### 2. HTML report — config-driven via `project.report.html`

`project.report.html = True` causes `project.save()` to write
`reports/<project>.html`. The all-`False` default keeps `reports/` from
being touched at all on plain `project.save()`. For one-off HTML without
changing the persistent config, call `project.report.save_html()`
directly.

```python
# Persistent — every subsequent save writes the HTML report.
project.report.html = True
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

Asset-bundling modes — `html_offline` controls **both** assets together
(single switch, single contract):

- **CDN mode (default)** — Plotly via `include_plotlyjs='cdn'` (~50-300
  KB on top of the otherwise-empty document, depending on chart count);
  MathJax from `https://cdn.jsdelivr.net/npm/mathjax@3/...` via
  `<script src="...">`. The HTML file itself is small (~50 KB body +
  tags); both assets stream in at page open. **Requires internet to
  view.**
- **Offline mode** (`project.report.html_offline = True` or
  `save_html(offline=True)`) — **fully self-contained**. Plotly inlines
  via `include_plotlyjs=True` (~3 MB); MathJax inlines as a `<script>`
  block holding the `tex-mml-chtml` component bundle (~1.5 MB) read from
  a vendored asset under
  `src/easydiffraction/report/templates/html/vendor/mathjax-tex-mml-chtml.js`.
  Total HTML size ~4.5 MB. Use when readers are air-gapped or when the
  user wants to archive a fully self-contained report.

The `mathjax-tex-mml-chtml.js` bundle is vendored once during the
implementation plan (Apache-2.0 license, ~1.5 MB minified) and refreshed
on the same cadence as `iucrjournals.cls`. No new Python dependency —
it's a static JavaScript asset shipped with the wheel.

**Plotly figures: forced light theme + the notebook modebar.** Two
appearance rules pin the report's charts to a consistent,
document-appropriate look:

- **Light theme only.** Every figure in the HTML report renders with the
  `plotly_white` template, regardless of the author's or reader's system
  / notebook dark-mode setting. The interactive notebook path
  deliberately switches `plotly_white` ↔ `plotly_dark` by theme
  (`PlotlyPlotter._default_template_name` in
  `display/plotters/plotly.py`), but a shared or printed report must not
  inherit a dark background. The HTML renderer therefore sets the
  figure's `template` to `plotly_white` **explicitly per figure** — not
  via the global `pio.templates.default` — so the report's appearance is
  independent of the ambient theme at render time.
- **Notebook modebar, not Plotly's default.** The figure toolbar (zoom /
  pan / etc.) reuses the **same notebook serialization mechanics**,
  which are two distinct pieces: (1) the standard Plotly `config` from
  `PlotlyPlotter._get_config()` — `displayModeBar=True`,
  `displaylogo=False`, the curated `modeBarButtonsToRemove` set
  (`select2d`, `lasso2d`, `zoomIn2d`, `zoomOut2d`, `autoScale2d`) —
  passed to `fig.to_html(config=...)`; and (2) the **custom
  legend-toggle button**, which is _not_ a `config` entry — it is
  installed by the notebook's `post_script` plus the `_wrap_html_figure`
  wrapper. The report must apply **both** (config _and_ post-script +
  wrapper) and must **not** fall back to Plotly's default full modebar.
  These serialization mechanics have one source of truth in
  `display/plotters/plotly.py`, shared by the notebook and the HTML
  report; only the forced `plotly_white` template above is
  report-specific (the notebook stays theme-adaptive).

**Table contents and heading styling — category-driven, consistent HTML
and PDF.** The reports mirror the project's own datablock categories
rather than maintaining hand-written summary tables:

- **Category-driven sections.** `ReportDataContext` iterates each
  structure and experiment owner's public `categories` in order. Each
  rendered category gets its own sub-subsection. Item categories render
  as two-column key-value tables. Collection categories render scalar
  descriptors first as key-value tables and loop items as loop tables
  with headers. Experiment data categories (`pd_data`, `total_data`,
  `refln`) are skipped because they are plotted or too large for report
  tables. The fit-quality plot remains the first experiment
  sub-subsection, and publication metadata remains source data only — it
  is not added to HTML, TeX, or PDF reports.
- **DisplayHandler names and units.** All table labels and units use the
  per-context `DisplayHandler` resolution chain, so TeX sees LaTeX names
  (`$2\theta$ offset`, `$U_{\mathrm{iso}}$`), HTML sees MathJax-capable
  equivalents, and plain values keep the readable labels (`H-M symbol`,
  `Wavelength`, `Scale`). Units use `deg` rather than a degree symbol in
  report labels.
- **Normal-weight headings and table headers.** Section headings
  (`h1`–`h4`, the document title and section / subsection /
  sub-subsection headers) render at normal weight. Table headers are
  normal weight as well; hierarchy comes from size, spacing, and rule
  lines rather than bold text.
- **Decimal-point-aligned number columns.** TeX tables use `siunitx` `S`
  columns. HTML has no browser-native equivalent, so report data carries
  numeric split metadata (`left`, decimal marker, `right`, and
  per-column widths). The HTML template emits `<span class="number">`
  with `number-left`, `number-dot`, and `number-right` children, using
  tabular digits so values such as `0.584(20)` and `3.89086937` align
  visually on the decimal marker without changing the original value
  text.
- **Automatic section numbering via CSS counters.** HTML sections are
  numbered like the PDF (`1.`, `1.1.`, `1.1.1.`) using CSS counters.
  Numbers are presentation-only, so they stay correct if sections are
  added or reordered. The document title and Description section are
  unnumbered, matching the LaTeX report.
- **Framed tables with shared report colors.** HTML and TeX tables have
  an outer frame and, for header tables, one rule below the header. They
  do not draw separators between body rows or between columns. The outer
  frame and the rule below header rows use the same darker color as the
  fit-plot axis rectangle. Fit-plot inner grid lines use the lighter
  Plotly-like grid color. The alternating row background remains a
  separate, lighter report color. These colors are defined once in
  report styling code and passed to HTML CSS, TeX tables, and
  Plotly/pgfplots figures. Body rows alternate with the first body row
  filled, regardless of whether the table has a header.
- **Predictable table widths.** HTML and TeX key-value tables use at
  least half of the available text width. Loop tables are classified
  from their rendered content: compact loops use half width, while wider
  loops use the full text width. This keeps small tables aligned with
  each other while giving wide category loops enough room for scientific
  values.
- **Left-aligned report title, subtitle, and description.** Reports
  render the project title as a left-aligned title, followed by a
  smaller subtitle (`EasyDiffraction report`). The project description
  is rendered as an unnumbered `Description` section, not as publication
  metadata and not as a centered abstract block.
- **Configurable free report font.** Report styling defines a single
  font configuration. HTML uses a non-embedded local-font stack headed
  by Nunito. TeX uses `fontspec` when the engine supports it, tries
  Nunito for text and Fira Math for math, and otherwise falls back to
  the TeX engine's bundled Latin Modern defaults. The PDF engine embeds
  the fonts it uses.

`reports/` is created lazily — only when at least one format is
configured (or an ad-hoc method is called). A user iterating on a fit
with the default all-`False` report booleans produces no extra files.

Rationale for the config category (replacing the earlier flag-based and
"auto on every save" positions):

- Reports are a _project preference_, not a per-call argument.
  `project.chart.type`, `project.table.type`, `project.verbosity.fit`
  follow the same pattern — set once, persisted in `project.cif`,
  applied on every save.
- `project.save()` has one job: save the project. With all report
  booleans `False`, the report behaviour is unchanged from before this
  ADR; with `project.report.html = True`, HTML appears on every save
  without needing a flag on each call.
- The GUI's Summary tab consumes `project.report.data_context()`
  in-memory, not the HTML file — so the GUI-consistency story does not
  depend on the HTML file existing at any particular moment.
- No new Python dependencies for HTML: `plotly`, `jinja2`, `pandas` are
  already declared in [pyproject.toml](../../../../pyproject.toml).
  MathJax loads from CDN by default, or from a vendored `tex-mml-chtml`
  bundle (~1.5 MB) inside the HTML when `html_offline=True` — same
  single switch that controls Plotly's CDN/inline mode (see the
  asset-bundling block above). MathJax renders inline math
  (`$U_{\mathrm{iso}}$`, `$\AA$`, etc.) identically to the LaTeX output.
  This is what makes the "HTML and PDF look the same" story work: column
  headers, units, and parameter labels are the same LaTeX-math strings
  on both sides, just rendered by MathJax in the browser and by the TeX
  engine in the PDF.

**Visual consistency with the PDF.** The HTML template mirrors the
TeX/PDF report structure rather than presenting a separate
dashboard-style design. Section order, headings, project-title
treatment, abstract handling, table labels, and `booktabs`-like
top/middle/bottom rules match the PDF as closely as browser CSS allows.
Publication metadata is intentionally not rendered in HTML or TeX/PDF
reports; it remains source data for the IUCr CIF path. Plots stay
format-specific (Plotly interactive in HTML, pgfplots static in PDF),
but the HTML renderer reuses the same Plotly figure builder as normal
EasyDiffraction plotting for the corresponding plot kind. For powder
Bragg measured-vs-calculated plots that means the report HTML is the
same composite layout as the direct Plotly view: main intensity row,
Bragg tick row, and residual row. The TeX renderer mirrors that
structure with native pgfplots group panels and maps the same names,
colors, line widths, axis labels, and axis ranges where pgfplots has an
equivalent. Measured uncertainty is **not** drawn as per-point error
bars in the PDF (they exhaust TeX's fixed memory pool — see §3.3); the
PDF intensity panel is measured line+markers and calculated line only.

Content (one HTML page per project — per-project granularity matches the
IUCr "one CIF per article" convention):

- Project info — title, phase count, experiment count. The project
  description is rendered as the report abstract when non-empty.
- Crystal data per phase — phase id, space group, cell parameters,
  atom-sites table.
- Data collection per experiment — experiment id, type fields, measured
  range + number of points. Per-experiment sections are anchor-linkable
  for navigation.
- Refinement — calculation engine + version + URL, minimization engine +
  version + URL, goodness-of-fit, parameter counts (total/free/fixed),
  constraint count.
- Fit charts per experiment — Plotly figures built at template- render
  time from the shared fit-data series in `data_context()` (see §6 —
  `experiments[i].fit_data` carries an `x` sub-dict (values + descriptor
  name / display label / LaTeX label / units, all four label forms
  pre-resolved at builder time per §1.5) and a `series` sub-dict
  (`meas`, `calc`, `diff`, optional `bkg`, each carrying values + label
  - optional `su` uncertainty array). Powder Bragg fit data also carries
    Bragg tick sets extracted from the same reflection data used by the
    interactive plotter. The descriptor-driven `x` payload covers Bragg
    powder CWL `two_theta`, TOF `time_of_flight`, and total-scattering
    `r` uniformly — any experiment whose x-axis descriptor exposes a
    `DisplayHandler` drops in without further ADR changes. The HTML
    renderer converts this dict into the same `PowderMeasVsCalcSpec`
    consumed by `PlotlyPlotter` for direct plotting, then embeds the
    resulting figure via `fig.to_html(include_plotlyjs=<cdn|True>)`. The
    same `fit_data` series feeds the pgfplots CSV emitter for the LaTeX
    renderer, while shared report-plot helpers reuse the Plotly display
    constants for style — one source of truth for both data and visual
    conventions.

### 3. LaTeX + PDF — config-driven via booleans

LaTeX is a **publish-time** artifact. `project.report.tex` and
`project.report.pdf` are enabled when the user wants them. There is no
style selector: the LaTeX writer ships exactly one document class
(`iucrjournals`); the **content layout deliberately does not replicate
IUCr's published journal format** — it mirrors the project's own
category-based structure (project info, software, refinement,
structures, experiments) section by section. Think "typeset Python
state" rather than "ready-to-submit manuscript".

```python
# Persistent — every save writes TeX + assets.
project.report.tex = True
project.save()                              # → reports/tex/{...}

# Persistent — every save writes the compiled PDF too.
project.report.tex = True
project.report.pdf = True
project.save()                              # → reports/tex/{...} + reports/<project>.pdf

# One-off, ignoring config.
project.report.save_tex()                   # TeX + data + style only
project.report.save_pdf()                   # TeX + PDF (PDF implies TeX)

# Ad-hoc string return.
project.report.as_tex() -> str
```

**`project.report.pdf = True` implies the TeX source is also written** —
a PDF without the editable `.tex` source is useless if the user wants to
tweak before re-compiling. Asking for the PDF always writes the TeX next
to it. Equivalently, `save_pdf()` writes the TeX assets as a
side-effect.

Future `project.report.html_style` (dark mode, journal-mimicking HTML
layout) can land separately without collision because it lives in the
config category, not in a method signature.

**Plots use `pgfplots`, emitted as one standalone `.tex` figure per
experiment, compiled independently to PDF, and included in the main
report via `\includegraphics`.** The figure pipeline writes, per
experiment, a CSV (`data/fit_<expt>.csv`), a standalone pgfplots
document (`data/fit_<expt>.tex`), and the compiled figure
(`data/fit_<expt>.pdf`); `<project>.tex` then does
`\includegraphics{data/fit_<expt>.pdf}`. This removes the Plotly +
kaleido + headless-Chromium dependency chain entirely — figures compile
to PDF using only `tectonic` (or another local TeX engine) plus the
`pgfplots` package, which `tectonic` resolves on demand. Building each
figure in its own compile also isolates its memory cost (see §3.3 —
TeX's fixed main- memory pool caps the coordinate count a _single_
document can hold, so per-figure isolation prevents accumulation across
experiments). See §3.3 for the figure composition and build detail.

#### 3.1 Folder layout

Per-project filenames (`<project>.{cif,html,pdf}`) share a root in
`reports/`; the LaTeX source plus its assets sit in `reports/tex/`.
Single style (`iucrjournals`) — no multi-style infrastructure.

**Full reports/ tree when all formats are configured.**
`project.report.cif/html/tex/pdf = True`:

```
<project_root>/
  reports/                          # populated by project.save() per config
    <project>.cif                   # ← project.report.cif
    <project>.html                  # ← project.report.html
    <project>.pdf                   # ← project.report.pdf
    tex/                            # ← project.report.tex or project.report.pdf
      <project>.tex                 #   main document; tables + \includegraphics of figure PDFs
      data/
        fit_<expt_id>.csv           #   profile data: x, meas, calc, diff (+ meas_su)
        fit_<expt_id>.tex           #   standalone pgfplots figure document (one per experiment)
        fit_<expt_id>.pdf           #   built independently from the .tex; included by <project>.tex
      styles/                       #   vendored — required to compile the TeX
        iucrjournals.cls            #     IUCr unified class (CC0 1.0)
        harvard.sty                 #     IUCr companion bibliography style
                                    # 2 files, ~70 KB. See §3.2.1.
```

**Examples by configuration.**

`project.report.{cif,html,tex,pdf} = False` (default — nothing written):

```
<project_root>/
  project.cif                       # _report.{cif,html,tex,pdf} = no
  structures/<...>.cif
  experiments/<...>.cif
  analysis/analysis.cif
  # reports/ directory does not exist
```

`project.report.cif = True` (journal-submission CIF only):

```
<project_root>/
  project.cif
  structures/<...>.cif
  experiments/<...>.cif
  analysis/analysis.cif
  reports/
    <project>.cif                   # IUCr-aligned, multi-datablock (alignment ADR §2.3)
```

`project.report.html = True` + `html_offline = True` (self-contained
inspection page):

```
<project_root>/
  project.cif
  structures/<...>.cif
  experiments/<...>.cif
  analysis/analysis.cif
  reports/
    <project>.html                  # ~3 MB, Plotly inlined
```

`project.report.cif/html/pdf = True` (typical pre-submission bundle):

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

`reports/` is created lazily — only when at least one report boolean is
enabled (or an ad-hoc method is called). The `tex/`, `tex/data/`, and
`tex/styles/` subfolders appear only when `project.report.tex` or
`project.report.pdf` is `True` (or `save_tex()` / `save_pdf()` is
invoked).

The `<project>` portion of every filename comes from `project.info.name`
verbatim (e.g. a project named `La0.5Ba0.5CoO3_HRPT` produces
`reports/La0.5Ba0.5CoO3_HRPT.html`). Only filesystem-dangerous
characters (path separators, control chars) are sanitized; case, dots,
underscores, and parentheses are preserved so the user recognises their
project name in the file listing.

#### 3.2 Single style — `iucrjournals`

The LaTeX writer ships exactly one document class:
`\documentclass[11pt,a4paper]{iucrjournals}`. No style selector, no slug
enum, no `_report.style` config field. Picking `iucrjournals` is a
convenience — it gives the typeset PDF a clean academic look without
committing to journal-submission fidelity.

**The LaTeX content is NOT a journal-submission manuscript.** It mirrors
the project's own category-based structure section-by-section: Project
Summary, Software, Refinement, Structures (one subsection per phase),
Experiments (one subsection per experiment). Tables use `booktabs`
(`\toprule`/`\midrule`/`\bottomrule`) and `float`'s `[H]` placement;
math uses inline LaTeX (`$Fd\bar{3}m$`, `\AA`, `$\deg$`). Reference
example at [`tmp/latex/example.tex`](../../../../tmp/latex/example.tex).

The `iucrjournals.cls` choice has two practical advantages over a bare
`article`:

- IUCr's class handles crystallographic typography (`\AA`, space-group
  symbols, structure-factor formatting) cleanly out of the box.
- Vendored document-class files (`iucrjournals.cls` + `harvard.sty`)
  ship with the wheel, so an IUCr TeX- distribution install is not
  required — the document class is local. The TeX engine itself must
  still supply `pgfplots` and its `pgf` / `tikz` dependencies, which
  `tectonic` resolves from CTAN on first compile and which TeX Live /
  MiKTeX ship in their default sets; see §3.3 for the compile-time
  dependency story.

Multi-style support (REVTeX, Elsevier `elsarticle`, …) is **deferred
work** — see "Deferred Work" below. A future ADR adds a style selector
when there is a concrete second style to ship.

The generated document uses the project title directly in `\title{...}`
and emits an empty `\author{}`. If `project.info.description` is
non-empty, that text becomes the document abstract; if it is empty, the
abstract environment is omitted. Publication metadata
(`project.publication.*`) is not included in the human-readable HTML or
TeX/PDF reports.

#### 3.2.1 Source provenance and bundled files

The IUCr source is vendored under
`src/easydiffraction/report/templates/tex/styles/` in the repository and
copied into `reports/tex/styles/` on report save. Download URL, date,
license, and file list below; the implementation plan refreshes the
vendored snapshot when upstream releases a new version.

**IUCr** (`iucrjournals.cls`)

- Source: https://journals.iucr.org/j/services/latexstyle.html
- Snapshot downloaded: 2026-05-26
- License: CC0 1.0 Universal (public domain dedication); declared in the
  `iucrjournals.cls` file header.
- Files included (2):
  - `iucrjournals.cls` — unified IUCr class (11 KB, dated 2024-12-02).
  - `harvard.sty` — bibliography style; required by `iucrjournals.cls`
    via `\RequirePackage{harvard}` (9 KB, Peter Williams, 2001-10-25).
- Files excluded: `iucr.bib`, `iucr.bst`, `fig1.png`, `template.tex`
  (bibliography / example assets, not needed for the category-mirror
  layout).

Total footprint per save: ~20 KB across 2 files. The CC0 1.0 licence
text is copied into the package's licensing documentation per the
implementation plan, with attribution to Peter Williams where the file
headers carry it.

REVTeX and other styles are **not** vendored — only `iucrjournals.cls`
ships. See "Deferred Work" for multi-style addition.

#### 3.3 Plot generation — standalone `pgfplots` figures, built independently, included as PDF

Plots inside the LaTeX output are drawn by the
[`pgfplots`](https://www.overleaf.com/learn/latex/Pgfplots_package)
package — vector, not pre-rendered raster — but **each fit figure is its
own standalone `.tex` document, compiled independently to a PDF, and
pulled into the report with `\includegraphics`.** The main
`<project>.tex` carries no inline pgfplots; it only includes the
pre-built figure PDFs.

**Per-experiment files** (`reports/tex/data/`):

- `fit_<expt>.csv` — profile data, one column per series: `x`, `meas`,
  `calc`, `diff` (and `meas_su` when measured standard uncertainties
  exist).
- `fit_<expt>.tex` — a `\documentclass{standalone}` pgfplots document
  that reads `fit_<expt>.csv`.
- `fit_<expt>.pdf` — produced by compiling `fit_<expt>.tex` on its own;
  this is what `<project>.tex` includes.

```latex
% ---- data/fit_<expt>.tex (standalone, built on its own) ----
\documentclass[border=2pt]{standalone}
\usepackage{pgfplots}
\usepgfplotslibrary{groupplots}
\pgfplotsset{compat=1.18}
\pgfplotsset{set layers}              % REQUIRED — see "Marker z-order" below
\definecolor{ed_meas}{RGB}{31,119,180}
\definecolor{ed_calc}{RGB}{214,39,40}
\definecolor{ed_bragg_0}{RGB}{255,127,14}
\definecolor{ed_diff}{RGB}{44,160,44}
\begin{document}
\begin{tikzpicture}
\begin{groupplot}[group style={group size=1 by 3, vertical sep=4pt,
                  x descriptions at=edge bottom},
                  width=12cm, xmin=<min>, xmax=<max>,
                  mark layer=like plot]
  % Intensity panel — exactly TWO plots
  \nextgroupplot[ylabel={Intensity (arb. units)}, xticklabels=\empty,
                 legend pos=north east]
  % (1) measured: connecting line + markers
  \addplot+[mark=*, mark size=0.75pt, color=ed_meas, line width=0.5pt,
            line join=bevel, mark options={line width=0pt}]
    table[x=x, y=meas, col sep=comma] {fit_<expt>.csv};
  \addlegendentry{Measured}
  % (2) calculated: line, declared LAST so it draws on top
  \addplot+[color=ed_calc, line width=0.75pt, line join=bevel, no markers]
    table[x=x, y=calc, col sep=comma] {fit_<expt>.csv};
  \addlegendentry{Calculated}
  % Bragg tick row
  \nextgroupplot[ymin=0.5, ymax=1.5, ytick=1, yticklabels={<phase>},
                 xticklabels=\empty, ylabel={Bragg}]
  \addplot+[color=ed_bragg_0, only marks, mark=|, mark size=5pt]
    coordinates {(<peak-x>,1) ...};
  % Residual panel
  \nextgroupplot[xlabel={$2\theta$ (degree)}, ylabel={Residual}]
  \addplot+[color=ed_diff, line width=0.5pt, line join=bevel, no markers]
    table[x=x, y=diff, col sep=comma] {fit_<expt>.csv};
\end{groupplot}
\end{tikzpicture}
\end{document}
```

```latex
% ---- <project>.tex includes the pre-built PDF ----
\begin{figure}[H]\centering
\includegraphics[width=\linewidth]{data/fit_<expt>.pdf}
\caption{Fit quality for experiment <expt>.}
\end{figure}
```

**Intensity panel — exactly two plots: measured and calculated.**
Measured is a connecting line with markers; calculated is a line drawn
last (on top). The figure carries **no measured–calculated difference
band, no per-point error bars, and no background curve** on the
intensity axis. The difference is shown in its own residual panel; the
background is omitted from report charts. Bragg tick coordinates are
written directly into the figure `.tex` (sparse, categorical
annotations, not a dense profile series).

**Why no per-point error bars (the core constraint).** TeX engines
(pdfTeX/XeTeX — and therefore `tectonic`, which is XeTeX-based) allocate
a _fixed_ main-memory pool (`main memory size=5000000`); `tectonic` does
not expose a knob to raise it, and the only engine that grows memory
dynamically (LuaTeX) is not available cross-platform on conda-forge (no
`texlive-core` for `win-64`). pgfplots holds an in-memory structure per
plotted primitive, and per-point error bars
(`error bars/.cd, y dir=both, y explicit`) cost a path _per data point_
— empirically the dominant consumer. A measured series with markers +
error bars overflowed the pool at ~1600 points; the same series as a
line + markers, without error bars, compiles at full resolution (3098
points) in the same pool. **Measured uncertainty is therefore not shown
as per-point error bars in the PDF report.** (An exploration of a single
±Nσ fill polygon as a cheaper uncertainty cue was prototyped and then
dropped in favour of the simpler two-plot figure; it is not part of this
decision.)

**Marker z-order — `set layers` is mandatory.** pgfplots' default is a
two-pass render: all lines first, then all markers on a foreground pass,
so markers always paint over lines regardless of `\addplot` order.
`mark layer=like plot` restores plot-order layering **but only takes
effect when `\pgfplotsset{set layers}` is active**. Both are required so
the calculated line (declared last) draws over the measured markers.
With `mark layer=like plot` alone (no `set layers`) the calculated line
renders _under_ the measured markers.

**Simplified measured-marker options.** A filled `mark=*` inherits both
its fill and its border colour from the plot's `color=`, so
`mark options={fill=…, draw=…}` is redundant when they match `color`.
The one non-redundant piece is `mark options={line width=0pt}`: without
it the marker border inherits the plot's `line width` and visibly
fattens the dot. The canonical measured plot is therefore
`mark=*, mark size=0.75pt, color=ed_meas, line width=0.5pt, line join=bevel, mark options={line width=0pt}`.

**Data resolution — full up to a cap, peak-preserving downsample above
it.** Each figure compiles in its own process with a fresh pool, so a
single experiment's chart is the unit that must fit. HRPT/typical CWL
(~3k points) renders every point; a dense CWL (~15k) or TOF bank (~30k)
would overflow even a plain line, so above a safe cap the renderer
downsamples with a **peak-preserving** method (min/max-per-bin or LTTB —
never naive every-Nth striding, which can step over a sharp Bragg apex
and flatten it). The full-fidelity data always remains in the CIF/CSV;
the figure is a view.

**Why standalone figures included as PDF, not inline pgfplots.**

- **Memory isolation.** Each figure's pgfplots load lives in its own
  compile; the main report never accumulates every experiment's
  coordinates in one pool. A five-experiment report that would overflow
  if inlined compiles fine as five independent figures + a light main
  document.
- **No Python image renderer needed.** Removes `kaleido` and the
  headless-Chromium chain plus the cross-platform `chromium` packaging
  problem on conda-forge. Vector throughout — no rasterization.
- **Independently rebuildable.** A figure can be regenerated or
  hand-tweaked without recompiling the whole report; the CSV and figure
  `.tex` stay editable.
- **Native LaTeX typography.** Axis labels, legends, captions render in
  the document font; no font-hinting mismatch.
- **Shared visual conventions.** The figure `.tex` consumes the same
  display colours and range helpers as the HTML/Plotly path, mapped to
  TeX-native `\definecolor`, `line width`, legend, and `groupplot`
  options.
- **`pgfplots` and `standalone` are on every modern TeX distribution.**
  TeX Live and MiKTeX ship them. `tectonic` can resolve them into its
  user cache when needed. No extra vendoring.

**Caveats.**

- The build now compiles N+1 documents (one per experiment figure, plus
  the main report). The PDF compiler (§3.4) drives the per-figure builds
  before the main document.
- The HTML output stays Plotly-based (interactive in the browser); the
  LaTeX output is pgfplots-based (static PDF). They share the two-plot
  measured/calculated composition, series colours, and source data, but
  are not pixel- identical. Font-family parity is deferred.

**Dependencies named by this ADR.** The implementation plan must name
one dependency before any `/draft-impl-1` or `/draft-impl-2` invocation
edits `pyproject.toml`, `pixi.toml`, or `pixi.lock`:

- `tectonic` — pixi/conda package, lightweight TeX engine for §3.4 PDF
  compilation in the project dev environment. `tectonic` can resolve
  `pgfplots` and any other TeX-package dependency from CTAN into its
  user cache.

Neither `kaleido` nor a browser is a dependency. The earlier draft's
`kaleido` + `chromium` chain is dropped wholesale.

Per AGENTS.md §Architecture, "an accepted plan that **names the specific
dependency** … combined with the user invoking `/draft-impl-1` or
`/draft-impl-2` for that plan … counts as pre-approval." This ADR does
**not** itself pre-approve the dependency edits; the plan does. The ADR
names `tectonic` here so the plan author has the canonical list and the
implementer can edit dependency files autonomously once the plan is
accepted and the implementation shortcut is invoked.

#### 3.4 PDF compilation — opportunistic subprocess call

No pure-Python LaTeX compiler exists in practice (TeX is a large C
codebase; reimplementing it pure-Python is not realistic). The library
calls out to an external TeX engine if one is available on `PATH`, in
this preference order:

1. **`tectonic`** — modern Rust-based single-binary TeX engine,
   auto-downloads packages on first use, available on conda-forge.
   First-class fit for `pixi`/`conda` users.
2. **`latexmk`** — TeX Live's standard front-end; handles multi-pass
   compilation. Conda-forge package `texlive-core` ships it on
   Linux/macOS.
3. **`pdflatex`** — bare TeX Live engine, used as a single-pass
   fallback. The Acta Cryst E refinement-table template has no
   bibliography, so one pass suffices.

Behaviour:

- If any of the three is on `PATH`, the PDF is compiled from
  `reports/tex/<project>.tex` and written to `reports/<project>.pdf`
  (one directory up from the .tex source). Promoting the compiled
  artifact to `reports/` keeps the filename-root trio (`.cif`, `.html`,
  `.pdf`) co-located.
- If none is found, the `.tex`, `data/`, and `styles/` are still
  written; the save log emits a single clear warning, for example:

  ```
  PDF skipped: no TeX engine on PATH.
  Install one with:
    pixi add tectonic         # recommended (conda-forge)
    conda install -c conda-forge tectonic
    # or any TeX Live distribution (latexmk / pdflatex)
  Then set project.report.pdf = True and re-run project.save(),
  or call project.report.save_pdf().
  ```

The library does not bundle a TeX distribution — TeX Live is multi-GB
and pulling it through pip is not feasible. Tectonic is the lightest
realistic install (~50 MB single binary; downloads packages on demand
into a user cache).

**Project-side dev environment.** The project's own `pixi.toml` gains
`tectonic` in a `[feature.docs.dependencies]` (or similar) group so CI
and `pixi run script-tests` can validate PDF generation end-to-end.
End-users picking the library up via plain `pip install easydiffraction`
get the warning path until they install a TeX engine themselves.

### 4. Software-provenance category on `analysis`

New category `analysis.software`, stamped at fit time, recording the
runtime engine identities. Structure mirrors the alignment ADR's
`_easydiffraction_software.{framework, calculator, minimizer}` triple so
one Python attribute feeds both default save and IUCr export:

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

These are populated automatically by `Analysis.fit()` immediately before
the fit returns success — never by the user.

**Persistence and rendering paths (split):**

- **Default save** (`analysis/analysis.cif`) — written as the
  `analysis.software` category with all nine identity fields plus the
  timestamp. Round-trippable on load. This is the change to the accepted
  IUCr ADR's "Analysis — unchanged" stance on software identification;
  see the ADRs-amended list below for the explicit amendment.
- **IUCr export** (`reports/<project>.cif`, alignment ADR §2.3a-i) — the
  `name + version` portion of each role is read **from**
  `analysis.software` (instead of being constructed inline from project
  state, as the alignment ADR's §2.3a-i originally specified) and
  surfaces as
  `_easydiffraction_software.{framework, calculator, minimizer}` in
  `data_global`, plus the concatenated `_computing.structure_refinement`
  free-text string. The `timestamp` surfaces as a project-extension
  `_easydiffraction_software.fit_datetime` — **not**
  `_audit.creation_date`, which the accepted IUCr writer already uses
  for the report file's own creation time (see `_iso_creation_datetime`
  in
  [`iucr_writer.py`](../../../../src/easydiffraction/io/cif/iucr_writer.py)).
  Fit time and report-generation time are different events and must not
  collide on the same tag. **URLs are not part of the IUCr export** —
  they're a rendering concern, not a publication-CIF field. Output goes
  to `reports/<project>.cif` (the alignment ADR's canonical location;
  the directory is `reports/`, not `iucr/`).
- **Rendered documents** (`reports/<project>.html`,
  `reports/tex/<project>.tex`) — render the full `name — version — url`
  triple per role, with URLs as hyperlinks in HTML and as `\href{}{}` in
  LaTeX. Matches the old GUI's "Calculation engine: CrysPy —
  https://www.cryspy.fr" row layout.

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
`analysis.software.{calculator,minimizer}.url` fields. Version strings
come from `<library>.__version__` at fit time. Both are recorded once,
in the snapshot — the engine library can upgrade later without rewriting
the recorded fit's provenance.

Persistence:

- Default save: written to `analysis/analysis.cif` under category names
  this ADR proposes the alignment ADR adopts in its analysis tier (see
  below). Round-trippable; surfaces as `analysis.software` on load.
- HTML/LaTeX rendering: the `Refinement` section reads
  `analysis.software` directly and prints `<engine> <version> — <url>`
  per the old GUI's row format.

**CIF serialisation — reuses the accepted IUCr ADR's tag set, plus one
new fit-time-stamp tag.** Existing IUCr-export tag names are owned by
the alignment ADR §2.3a-i and are reused here verbatim. One additional
project-extension tag — `_easydiffraction_software.fit_datetime` — is
introduced by this ADR to avoid colliding with the writer's existing
`_audit.creation_date` (which records report-generation time, not fit
time); it is registered as an IUCr amendment in the ADRs-amended list
below.

- Framework, calculator, minimizer roles →
  `_easydiffraction_software.{framework, calculator, minimizer}` in
  `data_global`, plus the concatenated `_computing.structure_refinement`
  free-text string. See
  [`cif_core.dic`](../../../../tmp/iucr-dicts/cif_core.dic) for the
  standard `_computing.structure_refinement` slot.
- Fit-time timestamp → `_easydiffraction_software.fit_datetime`
  (project-extension tag in `data_global`). The IUCr writer's own
  `_audit.creation_date` keeps its existing report-creation semantics
  from
  [`iucr_writer.py`](../../../../src/easydiffraction/io/cif/iucr_writer.py)
  and is not overwritten.
- EasyDiffraction's own version is bundled into the framework string and
  into the `_computing.structure_refinement` rendering per the IUCr
  convention; not a separate tag.

No new minimization-engine tag (e.g.
`_easydiffraction_computing.minimization_engine`) is introduced — the
alignment ADR's existing `…software.minimizer` already covers that role.
The only new IUCr-export item is
`_easydiffraction_software.fit_datetime` (see the CIF-serialisation
preamble above and the ADRs-amended list); it extends the existing
`_easydiffraction_software.*` category, not a new top-level extension
namespace. The Python-side `analysis.software` category feeds both the
established triple and the new fit-time tag; the IUCr-export emission
stays under the alignment ADR's control.

#### 4.1 Missing-provenance behaviour

`analysis.software` is populated by `Analysis.fit()` just before a
successful return — pre-fit calls, failed fits, and projects loaded from
a save predating this ADR all start out **without** the snapshot. The
public API surface treats missing provenance uniformly:

- **Rendering (`project.report.show_report()`, HTML, TeX).** Each
  role-row prints `"(not available)"` for `name`, omits version and URL,
  and adds a one-line footer "Software-provenance snapshot not yet
  recorded — call `Analysis.fit()` once to populate." No warning, no
  exception; the report still renders end-to-end so users iterating on a
  configuration before fitting see the rest of the page.
- **IUCr CIF export (`project.report.cif = True`).** The
  `_easydiffraction_software.{framework, calculator, minimizer}` triple
  emits `?` placeholders consistent with the IUCr ADR's unset-field
  convention. The derived `_computing.structure_refinement` string falls
  back to `"EasyDiffraction <version>"` (framework only). The
  `_easydiffraction_software.fit_datetime` tag is omitted entirely (no
  `?` — the absence is the signal).
- **Internal validation (the §1.4 pre-write gemmi pass).** Does **not**
  detect missing provenance. The gemmi pass validates that emitted tags
  and types match the IUCr core / pdCIF dictionaries, and it explicitly
  skips the `_easydiffraction_*` extension namespace. So the
  fallback-filled `_computing.structure_refinement`
  (`"EasyDiffraction <version>"`) is not flagged as missing — it's a
  valid string — and the `?` placeholders on
  `_easydiffraction_software.{framework, calculator, minimizer}` are not
  flagged either, because gemmi does not validate the extension
  namespace. Detecting "publication-grade provenance is incomplete" is a
  different concern from dictionary-spec compliance and falls to the
  deferred `project.report.check_completeness()` listed in Deferred
  Work. Users who must guarantee complete provenance before submission
  should run that check (once it lands) or inspect the rendered report
  manually.
- **Old projects.** Loading a project saved before this ADR produces an
  `analysis.software` with all fields unset and the timestamp `None`. No
  migration step is run; the user populates the snapshot by re-running
  the fit.

This rule applies wholesale — no flag toggles it, no targeted exception
is raised. Publication-grade users who need the provenance can re-run
the fit; users producing draft / preview reports keep working without
interruption.

### 5. Publication-metadata category on `project`

New top-level category on `Project`, sibling to `project.info` and
`project.analysis`. Populated by the user (directly in Python, or loaded
from a `publ_info.{toml,json}` file). Feeds the `_publ_*` / `_journal_*`
/ `_publ_author.*` placeholders that the alignment ADR's `data_global`
block currently emits as `?` (alignment ADR §2.3a).

#### 5.1 Structure — CIF-aligned sibling categories

`Publication` is a category-owner (like `Experiment`) hosting sibling
sub-categories that map **1:1 to CIF category prefixes**. No artificial
groupings; the CIF dictionaries already provide the natural shape:

| Python attribute               | CIF category             | Audience                                                                                                                              |
| ------------------------------ | ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------- |
| `publication.journal`          | `_journal.*`             | User-set at submission (`name_full`, `paper_category`); editor-set post-acceptance (`year`, `volume`, `issue`, `page_*`, `paper_doi`) |
| `publication.journal_date`     | `_journal_date.*`        | Editor (`accepted`, `from_coeditor`, `printers_final`)                                                                                |
| `publication.journal_coeditor` | `_journal_coeditor.*`    | Editor (`code`, `name`, `notes`)                                                                                                      |
| `publication.contact_author`   | `_publ_contact_author.*` | User (`name`, `address`, `email`, `phone`, `id_orcid`, `id_iucr`)                                                                     |
| `publication.body`             | `_publ_body.*`           | User (`title`, `synopsis`, `abstract`, `keywords`)                                                                                    |
| `publication.authors`          | `_publ_author.*` (loop)  | User (per author: `name`, `address`, `footnote`, `id_orcid`, `id_iucr`)                                                               |

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

Python attributes are lowercase snake_case (`id_orcid`); CIF tags retain
dictionary casing (`_publ_contact_author.id_ORCID`). Loops use the
project's existing `CategoryCollection` pattern (`add()`, indexed
access, etc.).

The editor-side categories (`journal_date`, `journal_coeditor`) exist so
the schema can carry editor-supplied fields when a user manually copies
them in (typically by editing `project.publication.*` in Python after a
referee round) — not because users typically fill them at submission
time. Defaults are `None`; the IUCr writer emits `?` for unset fields.
Round-trip is on the **`project.cif`** axis only (`project.publication`
reads and writes there per the project-facade-and-persistence contract);
**the report CIF at `reports/<project>.cif` stays export-only** per the
accepted IUCr ADR. A reader for `reports/<project>.cif` is explicitly
out of scope.

#### 5.2 Discrete `body` fields, not a markdown blob

`_publ_body.*` in coreCIF supports nested section content via an
`element` / `format` / `contents` trio. For the refinement-table
appendix use case (user pastes content into a full manuscript later),
discrete top-level slots are more discoverable than a generic markdown
blob:

- `publication.body.title` — manuscript title (single string)
- `publication.body.synopsis` — short summary (IUCr Acta E requires
  this)
- `publication.body.abstract` — abstract text
- `publication.body.keywords` — list of strings (loop on CIF side)

A future v2 could add free-form section support
(`publication.body.sections[]` with element/format/contents trios) when
users produce full manuscripts from the library. Out of scope for v1.

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
- **Multi-line strings** — abstracts, addresses, and synopses without
  escaping.
- **Familiar** — the project already uses `pyproject.toml` and
  `pixi.toml`.
- **Standard library** `tomllib` (Python 3.11+); no new dependency.

JSON is supported as a fallback for programmatic generation (e.g. a user
script that dumps publication data from a database; an external tool
that produces JSON output). Standard library `json`.

Format selection is by file extension. Unknown extensions raise
`ValueError("Unsupported publication-info format: <ext>. " "Use .toml or .json.")`.
No YAML support — adds a dependency for no gain.

Reading from the report CIF (`reports/<project>.cif`) back into
`project.publication` is **explicitly out of scope** here and remains
the accepted IUCr ADR's "Export only — no round-trip" contract. Users
who edit the report file by hand should also update
`project.publication` (or its TOML/JSON source) so the next save
reflects the edits; the library does not auto-import.

### 6. Shared `ReportDataContext` + Jinja templates

One context-builder method on the `project.report` facade. Descriptors
expose their `DisplayHandler` (§1.5) through the context so the
templates can consume `display_name` / `display_units` for HTML / GUI
rendering and `latex_name` / `latex_units` for LaTeX, with graceful
fallback to plain `name` / `units` when no handler is attached:

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

GUI consumes `project.report.data_context()` directly — no CIF parsing,
no HTML scraping. This is the consistency guarantee.

### 7. CLI surface mirrors the Python split

Two subcommands match the Python `project.save()` vs
`project.report.save_*()` split:

```bash
ed save                                            # project files + enabled report booleans
ed save-report --html                              # one-off — write reports/<project>.html only
ed save-report --cif --tex --pdf                   # one-off — full LaTeX bundle + CIF
```

`ed save-report` with no `--cif`/`--html`/`--tex`/`--pdf` exits with a
clear error pointing the user at the report booleans. `--pdf` implies
`--tex` so the user always gets the editable source next to the PDF.

For users who want to **persist** the choice across runs, the
configuration category is set the usual way — by setting
`project.report.<format> = True`, by editing `project.cif` directly, or
programmatically — and `ed save` picks it up on every subsequent save.

CLI flags are short (no `_report` suffix; the subcommand name
`save-report` already scopes them). The Python and CLI surfaces stay
symmetric:

| Python (config — persisted)          | Python (ad-hoc — one-off)    | CLI (one-off subcommand) |
| ------------------------------------ | ---------------------------- | ------------------------ |
| `project.report.html = True`         | `project.report.save_html()` | `ed save-report --html`  |
| `project.report.cif = True`          | `project.report.save_cif()`  | `ed save-report --cif`   |
| `project.report.tex = True`          | `project.report.save_tex()`  | `ed save-report --tex`   |
| `project.report.pdf = True`          | `project.report.save_pdf()`  | `ed save-report --pdf`   |
| `project.report.html_offline = True` | `save_html(offline=True)`    | `--html --offline`       |

### 8. Fields the library currently lacks

The HTML/LaTeX renderers need three derived fields plus the
display-metadata mechanism from §1.5; this ADR scopes them all as
in-scope work:

- `structures[i].crystal_system` — derivable from
  `space_group.name_h_m`, but not currently exposed as a property.
- `experiments[i].measured_range` — `min`, `max`, `inc` triple from the
  underlying data arrays. Not currently exposed as a property on
  `Experiment`.
- `analysis.parameter_counts` — total / free / fixed / constrained. Free
  and fixed are derivable from `project.free_parameters`; total and
  constrained need a single aggregating helper.
- **Descriptor display metadata (§1.5).** The
  `display_handler=DisplayHandler(...)` kwarg is added to every
  descriptor base class. The implementation plan sweeps existing
  `units=` Unicode strings to ASCII (CIF DDLm `_units.code` vocabulary)
  and attaches `DisplayHandler` instances to atom-site, cell,
  fit-result, peak, and other parameters the renderers surface.
  Descriptors without a handler keep working — they fall back to plain
  `name`/`units` in every renderer.

The first three are pure derived properties — no new state, no
persistence beyond what already exists. The fourth is the
descriptor-level mechanism from §1.5; it is library-wide and benefits
every renderer (HTML, PDF, terminal, GUI) simultaneously.

## Consequences

### Positive

- `summary.cif` placeholder goes away (alignment ADR + this ADR jointly
  retire it); no more "To be added..." on disk.
- HTML can be auto-regenerated on every save by setting
  `project.report.html = True` once (or via the GUI's "Export" panel).
  Zero-friction inspection for users who want it, no surprise file
  writes for users who don't.
- LaTeX export covers the "send the refinement table to my co-author"
  workflow that today requires manual transcription.
- Engine name + version + URL are captured at fit time, ending the
  current provenance gap. Maps cleanly to coreCIF
  `_computing.structure_refinement` for journal-bound CIFs.
- The GUI Summary tab consumes the same Python data context as the HTML
  renderer. Library and GUI cannot drift on "what numbers are shown".
- New summary fields are added in one place
  (`project.report.data_context()`); all renderers pick them up.
- Single LaTeX style (`iucrjournals`) keeps the v1 surface small: no
  style enum, no `_report.style` config field, no multi-class vendored
  bundle. Future styles add via a new ADR alongside the new class files.

### Trade-offs

- All report outputs are opt-in. The default all-`False` report booleans
  mean daily `project.save()` calls write only project files —
  `reports/` isn't created until a format is configured (or an ad-hoc
  method is called).
- HTML is small (~50–300 KB CDN-mode, ~few MB offline); users who want
  it on every save set `project.report.html = True` once.
- LaTeX bundle (`reports/tex/` + `reports/<project>.pdf`) is a handful
  of files (`.tex`, CSV data per experiment, two vendored class/style
  files, compiled PDF) — only written when `project.report.tex` or
  `project.report.pdf` is `True` (or an ad-hoc `save_tex()` /
  `save_pdf()` call is made). Total per-save footprint is dominated by
  the CSVs; the `tex/styles/` directory holds ~20 KB across 2 files.
- One upstream snapshot vendored in the repository (`iucrjournals.cls` +
  `harvard.sty`, CC0 1.0). The plan refreshes the snapshot when upstream
  releases a new version; the licence text is copied into the package's
  licensing documentation alongside the wheel's BSD-3-Clause `LICENSE`
  with attribution.
- **No Python image renderer in the LaTeX path.** The earlier draft's
  `kaleido` runtime dependency and the matching Chrome/Chromium browser
  requirement are both dropped in favour of `pgfplots` reading the
  project's CSV data directly. The HTML output remains Plotly-based
  (interactive in the browser); the LaTeX output is pgfplots-based
  (static in the PDF). The two renderings share the underlying data and
  reuse Plotly's report-relevant styling constants wherever pgfplots has
  an equivalent — see §3 and §3.3 for the rationale.
- PDF compilation is opportunistic — works when `tectonic`, `latexmk`,
  or `pdflatex` is on `PATH`; otherwise the `.tex` and the `data/` CSV
  files are still written and the user gets a clear one-line install
  hint (`pixi add tectonic` is the recommended path).
- The `data_context` dict is a public API surface. Renaming a key
  affects every renderer. Treated like a public method signature.
- `analysis.software` adds a new category to persist on every save.
  Small (8 string fields) but visible in `analysis.cif` diffs.
- Two ADRs (this one + alignment) must move in lockstep on the
  `_computing.*` mapping and on publication-metadata sourcing.
  Cross-references in both should make the coupling explicit.

### ADRs amended by this ADR

- [`iucr-cif-tag-alignment.md`](../accepted/iucr-cif-tag-alignment.md) —
  five amendments:
  1. **`project.save()` flag removal.** The accepted
     `project.save(report=True)` flag is **removed**. Reports come from
     the new `project.report` configuration category (§1.1, §1.3) — five
     scalar items persisted to `project.cif` (`_report.cif`,
     `_report.html`, `_report.tex`, `_report.pdf`,
     `_report.html_offline`). Set the configuration once through those
     booleans; `project.save()` applies it on every save thereafter.
     Replaces the flag with persisted configuration, matching the
     existing `project.chart`, `project.table`, `project.verbosity`
     pattern.
  2. **`project.report.save()` surface redesigned.** The accepted
     `project.report.save()` is now a no-argument convenience that reads
     the configuration category (raises `ValueError` when no formats are
     enabled — §1.2). Per-format ad-hoc writes use new explicit methods:
     `project.report.save_cif()`, `save_html(offline=False)`,
     `save_tex()`, `save_pdf()`. The earlier draft's
     `save(cif=True, html=True, tex=True, pdf=True, style=, check=)`
     flag bundle is dropped. `project.report.check()` and the
     `check=True` flag are **removed**: dictionary-spec validation runs
     internally **before every CIF write only** (`save_cif()` and the
     `cif` branch under `project.save()`; HTML, TeX, and PDF get no
     pre-write validation — see §1.4). A writer- correctness failure on
     the CIF path raises `EasyDiffractionWriterError` instead of
     producing a broken file.
  3. **Software-identification source.** The alignment ADR's §2.3a-i
     described the `_easydiffraction_software.*` triple as a
     "report-only projection … built inline by the IUCr writer from
     existing state", with no default-save persistence. This ADR
     introduces a persisted `analysis.software` category (§4) and amends
     that stance: the triple is read **from** `analysis.software` at
     IUCr-export time, not reconstructed inline. The Current State table
     row that previously read "`_calculator.type`, `_minimizer.type` …
     Analysis — unchanged" gains an "Analysis — `analysis.software`
     persisted" note.
  4. **New project-extension tag for fit time.** Adds
     `_easydiffraction_software.fit_datetime` to the `data_global` block
     in the IUCr export. The accepted ADR's §2.3a-i listed
     `_easydiffraction_software.{framework, calculator, minimizer}`
     only; `fit_datetime` extends that same category prefix without
     introducing a new top-level extension namespace. The writer's
     existing `_audit.creation_date` keeps its
     `_iso_creation_datetime()` source (report-generation time) and is
     **not** overwritten — fit time and report time are distinct events.
  5. **Publication metadata in the default save.** The alignment ADR's
     Scope explicitly excluded "Adding new CIF categories the project
     does not currently track (`_chemical.*`, `_publ.*`, `_journal.*`)
     **for the default save**" (alignment ADR §Scope, lines 101-110).
     This ADR adds `project.publication.*` (§5) and persists it to
     `project.cif` — a different file from `reports/<project>.cif`, but
     still a default-save change that the alignment ADR did not
     anticipate. Specifically:
     - `_publ_contact_author.*`, `_publ_author.*`, `_publ_body.*`,
       `_journal.*`, `_journal_date.*`, `_journal_coeditor.*` are now in
       scope for `project.cif`.
     - The accepted IUCr export still reads these from
       `project.publication.*` and emits them in `data_global` per
       §2.3a; the `?` placeholder semantics for unset fields are
       unchanged.
     - The accepted "Export only — no round-trip" rule for
       `reports/<project>.cif` is **unaffected** — `project.publication`
       round-trips through `project.cif`, not through the report CIF
       (see §5.1 / §5.3).

  All other IUCr-export decisions in the alignment ADR (multi-datablock
  layout, tag-name policy, gemmi as the validation engine) are
  unaffected — only the public surface for validation changes:
  `project.report.check()` and `check=True` are removed; the gemmi pass
  moves inside the writer **on the CIF emission paths only** (§1.4),
  running before every CIF write (no pre-write validation for HTML, TeX,
  or PDF — those formats have no spec to check against).

- [`analysis-cif-fit-state.md`](../accepted/analysis-cif-fit-state.md) —
  adds `analysis.software` to the persisted analysis state.
- [`project-facade-and-persistence.md`](../accepted/project-facade-and-persistence.md)
  — three changes:
  1. **`project.report` gains a persisted configuration category.** The
     accepted ADR scoped `project.report` as a CIF-write helper (single
     output: `reports/<project>.cif`). This ADR extends it with a
     configuration category (`_report.*` in `project.cif`, five scalar
     items per §1.1 / §1.3) that the existing `Project.save()` reads on
     every save. The facade becomes a hybrid — helper methods
     (`save_*()`) **and** persisted configuration on the same Python
     object.
  2. **New top-level `project.publication` facade slot (§5).** Sibling
     to `project.info`, `project.structures`, `project.experiments`,
     `project.analysis`, `project.report`. Persisted to `project.cif`
     next to the other project-level singleton categories.
  3. **Project-level singleton category enumeration extended.** The
     accepted ADR enumerates `_info.*`, `_chart.*`, `_table.*`,
     `_verbosity.*` as the project-level singleton categories owned by
     `project.cif`. This ADR adds two more to that enumeration:
     `_report.*` (this ADR §1.3) and `_publication.*` family (this ADR
     §5; concrete sub-prefixes are `_publ_*` and `_journal_*` per IUCr
     coreCIF).
- [`python-cif-category-correspondence.md`](python-cif-category-correspondence.md)
  — owns the Python-to-CIF correspondence rule for two new project-level
  singleton surfaces:
  - `project.report.*` ↔ `_report.*` — five scalar items (four format
    booleans plus `html_offline`) per §1.3.
  - `project.publication.*` ↔ `_publ_*` / `_journal_*` sibling
    categories per §5. Python attributes are lowercase snake_case
    (`id_orcid`); CIF tags retain dictionary casing
    (`_publ_contact_author.id_ORCID`).

  Both follow the correspondence ADR's existing 1:1 mapping pattern. The
  correspondence ADR's enumeration of "currently persisted Python
  category surfaces" gains two rows for these additions.

  No conflict with the correspondence ADR's project-level category list
  because `_publ_*` / `_journal_*` are publication-domain, not
  project-level singleton categories.

## Open Questions

- **GUI Export panel.** Two reasonable shapes: (a) checkboxes edit
  `project.report.{cif,html,tex,pdf}` directly + a "Save now" button
  that calls `project.save()` (config-driven, matches the Python
  surface) or (b) checkboxes drive ad-hoc per-format calls
  (`save_html()`, `save_pdf()`) without changing the persisted config
  (one-off ergonomics). Either fits the configuration / ad-hoc split in
  §1; the exact GUI layout (single dialog vs. inline checkboxes, button
  labels, post-save action) decides at GUI-integration time, not here.
- **`units=` sweep — backward compatibility.** Existing descriptors use
  Unicode short-form units (`'Å'`, `'Å²'`, `'°'`). The §1.5 convention
  is ASCII (CIF DDLm `_units.code`: `'angstroms'`, `'angstrom_squared'`,
  `'degrees'`). Audit the project for external readers of
  `descriptor.units` before the plan runs the sweep — tutorial sources,
  the display layer, third-party scripts that may depend on the Unicode
  value via `parameter.units`. Confirm whether any consumer hard-codes
  the Unicode strings (literal `'Å²'` comparison) and would need
  updating alongside the sweep. Recommendation: project-internal callers
  move to `parameter.display_handler.display_units` when present, with
  fallback to `parameter.units`; the sweep is a same-PR change.

## Alternatives Considered

### A. Leave `project.report` scoped to CIF only

Status of the alignment ADR before this ADR's amendment: facade exists
but only writes the IUCr CIF. The GUI Summary tab would then need its
own renderer, the everyday project folder would have no human-readable
artefact, and there'd be no LaTeX/PDF path. Auto HTML and the
GUI-consistency story both disappear. Rejected on UX and consistency
grounds.

### B. HTML auto-saved on every `project.save()`

An earlier revision of this ADR had HTML always-on, no opt-in flag, the
philosophy being "every artefact stays fresh". Rejected in favour of the
configuration approach: `project.save()` does one job (save the project)
and reads the report booleans to decide which reports come along. Empty
config = no reports. Users who want auto-fresh HTML set
`project.report.html = True` once; the GUI consumes
`project.report.data_context()` in-memory, not the HTML file, so
freshness of the file does not affect GUI consistency.

### C. Markdown as the primary rendered format

Markdown is git-friendly and renders nicely in many viewers. But it
cannot embed interactive Plotly figures and has no journal-style
analogue for LaTeX. Could be added as a third renderer (the Jinja base
template makes it a few hundred lines) but not as the primary. Deferred.

### D. Build the HTML renderer inside the GUI, not the library

Push HTML/LaTeX rendering into the GUI codebase; the library only
exposes the data context. Saves library complexity. But: CLI users get
nothing, notebook users get nothing, and the GUI's renderer is not
exercised by CI. Rejected for the consistency benefit of a single
renderer.

### E. PDF as the primary rendered format

Could be done via `weasyprint` (HTML→PDF) or directly via `reportlab`.
Adds a dependency, slows save, and most users print HTML to PDF from a
browser anyway. Deferred.

## Deferred Work

- Markdown rendering as a third Jinja target.
- **Multi-style LaTeX support.** v1 ships only `iucrjournals` with no
  style selector and no `_report.style` config field. Adding a second
  style (REVTeX 4.2, Elsevier `elsarticle`, Springer `svjour3`, etc.) is
  a follow-up ADR that reintroduces:
  - a `ReportStyleEnum` (per the closed-values ADR),
  - a `_report.style` config field on `project.report`,
  - a `style=` arg on `save_tex()` / `save_pdf()`,
  - a `--style` CLI flag on `ed save-report`,
  - vendored class files for the new style.

  The renderer in v1 hardcodes `iucrjournals`; reintroducing the
  selector is a contained change, not a rewrite, but it is its own ADR
  so the design conversation does not relitigate on each new template
  request.

- **Bibliography support** (`iucr.bib` / `iucr.bst`). IUCr ships
  bibliography styles for citing IUCr publications. Not bundled in v1
  because the v1 report mirrors internal category structure rather than
  producing a manuscript with references. Add when users produce full
  manuscripts from the library.
- **Snapshot-refresh automation.** A small `pixi` task to re-fetch the
  upstream IUCr source and diff against the vendored snapshot would help
  track when IUCr releases a new version. v1 refreshes by hand during
  plan work.
- **Larger-pattern pgfplots tuning.** Powder patterns with ~50K points
  compile in pgfplots in seconds. If users produce significantly larger
  patterns and compile time becomes uncomfortable, the renderer can
  downsample via `pgfplots`'s `each nth point=N` option, or switch to
  matplotlib-rendered PDF figures for the LaTeX path while keeping
  pgfplots as the default. Tune when needed.
- Tab/accordion navigation in HTML for projects with many experiments.
- `project.report.check_completeness()` — complements the internal gemmi
  pass from §1.4 (dictionary spec compliance, enforced before every CIF
  write). The completeness check would flag whether the user has filled
  in `_publ_*` / `_journal_*` placeholders for their target journal,
  which dictionary validation cannot determine. Different concern,
  different layer.
- A pinned-snapshot variant of `<project>.html` (timestamped, kept next
  to fit-run-specific artifacts) for users who want to track refinement
  history visually across saves.
- Additional figure types beyond fit + difference (e.g. cumulative-χ²
  plot, residual histogram, posterior corner plot for Bayesian fits).
  Same data-context-driven pattern, new matplotlib + Plotly renderers
  per type.

## Suggested Pull Request

**Title:** Extend `project.report` with HTML, TeX, and PDF outputs
(opt-in)

**Description:**

Builds on the IUCr CIF alignment work by filling in the non-CIF half of
the publication bundle. The `project.report` facade covers four output
formats — CIF, HTML, TeX, PDF — chosen via a configuration category on
the project (persisted in `project.cif`) and applied automatically on
every save:

```python
project.report.cif = True                   # emit IUCr CIF on save
project.report.html = True                  # emit HTML on save
project.report.html_offline = False         # Plotly via CDN (default) or inlined

project.save()
# → project.cif (with the _report.* config)
# → structures/, experiments/, analysis/ as before
# → reports/<project>.cif and reports/<project>.html per config
```

Per-format ad-hoc methods cover one-offs without changing the persisted
config: `project.report.save_html(offline=False)`, `save_cif()`,
`save_tex()`, `save_pdf()`. The CLI mirrors with a new subcommand,
`ed save-report --cif --html --tex --pdf` (also a one-off; `ed save`
reads the persisted config).

The LaTeX bundle ships `<project>.tex`, CSV data per experiment, and the
`iucrjournals` vendored style under `reports/tex/`. The compiled
`<project>.pdf` is written one level up (next to the CIF and HTML) when
a TeX engine — `tectonic` (recommended, conda-forge), `latexmk`, or
`pdflatex` — is on `PATH`. The `.tex` document mirrors the project's own
category-based structure (Project Summary, Software, Refinement,
Structures, Experiments) rather than imitating an IUCr
journal-submission manuscript — "typeset Python state", not a
ready-to-submit manuscript.

Plots inside the LaTeX output are rendered by `pgfplots` as one
standalone figure document per experiment, compiled independently to PDF
and included in the report via `\includegraphics` (§3.3). The HTML
output stays Plotly-based (interactive in the browser) and reuses the
direct EasyDiffraction Plotly figure builder for powder Bragg
measured-vs-calculated plots. The LaTeX output is pgfplots-based (static
in the PDF) and mirrors the same main-intensity / Bragg tick / residual
row structure with native groupplots. The two share the underlying data
and the Plotly-derived visual conventions that map cleanly to both
backends (series names, colors, line widths, axis labels, ranges, and
legend placement). Measured uncertainty is **not** drawn as per-point
error bars in the PDF intensity panel — they exhaust TeX's fixed memory
pool (§3.3); the PDF shows measured line+markers and calculated line
only. There is no pixel-equality claim and no Python image-rendering
dependency in the LaTeX path (`kaleido` and the browser dependency from
earlier drafts are both gone).

Adds an `analysis.software` Python category — three-role triple
(framework / calculator / minimizer) matching the alignment ADR's
`_easydiffraction_software.*` CIF emission — recording engines,
versions, and URLs at fit time so every report carries authoritative
provenance. The library, the CLI, and the GUI all consume the same
in-memory report data (`project.report.data_context()`) — no code path
renders independently. This keeps the forthcoming GUI Summary tab in
lockstep with the library.
