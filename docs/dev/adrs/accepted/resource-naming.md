# ADR: Downloadable Resource Naming

**Status:** Accepted **Date:** 2026-06-14

> This ADR follows [`AGENTS.md`](../../../../AGENTS.md). No deliberate
> exception to those instructions is taken.

## Group

Naming.

> Sibling of [`data-source-pinning.md`](data-source-pinning.md): that ADR
> pins *which snapshot* of the data repository to fetch and decides
> replace-in-place under stable identifiers; this ADR decides what those
> identifiers are, for both downloadable datasets and tutorials.

## Context

Downloadable resources — example/tutorial datasets fetched by
`download_data()` and tutorial notebooks fetched by `download_tutorial()`
— are currently identified by integer ids (`download_data(id=44)`), with
files named `ed-<N>.<ext>` and an `index.json` keyed by those integers.

This is fragile:

- **Integers churn.** Replacing a dataset has been done by minting a new
  id with a `replaces` pointer, producing chains like
  `28 -> 30 -> 36 -> 40 -> 44` for one LBCO/HRPT project. Tutorials, in
  turn, are numbered by *creation* order (`ed-1 … ed-29`); inserting a
  beginner tutorial later, or removing/replacing one, would renumber the
  rest. So the number is never a stable handle.
- **Integers are opaque.** `download_data(44)` says nothing; a reader
  cannot tell a structure from a project, or LBCO from Co2SiO4.
- **It fights replace-in-place.** `data-source-pinning.md` decides data
  is updated by overwriting files under stable identifiers; integer ids
  with `replaces` chains contradict that.

The companion `data-source-pinning` ADR establishes "stable identifiers,
replace-in-place" (its Decision 5) but leaves the identifier *form*
undecided. This ADR fixes that form, for datasets and tutorials alike.

## Decision

1. **Descriptive slug ids, not integers.** Every downloadable resource
   is identified by a stable, lowercase-dash slug. Datasets are
   namespaced by kind as `<namespace>/<slug>`:
   - `structures/` — crystal-structure import CIFs,
   - `experiments/` — EasyDiffraction experiment-definition files,
   - `measured/` — raw measured or simulated data files,
   - `projects/` — saved EasyDiffraction project archives.

   Tutorials use a bare descriptive slug (e.g. `refine-lbco-hrpt-from-cif`,
   `pdf-si-nomad`, `bayesian-emcee-resume-lbco-hrpt`). The slug encodes
   the sample, technique, and instrument/qualifier needed to keep it
   unique and self-explanatory, and it carries no volatile facts that
   would force a rename on unrelated changes.

2. **The slug is the stable identity.** Updating a resource overwrites
   the file under the same slug (per `data-source-pinning`); a genuinely
   different resource gets a genuinely different slug. The integer
   `replaces` chains collapse — each chain becomes one slug. A removed
   slug is absent from the catalog and fails with the same clear
   unknown-resource error as any other well-formed but missing id
   (Decision 7).

3. **Drop integer ids as persistent keys.** Integer ids are not used to
   identify resources in `index.json`, tutorials, documentation, tests,
   or any saved code. The project is in beta, so no integer-id
   compatibility shim is kept.

4. **Order is separate metadata, never the id.** Presentation/learning
   order (which mainly matters for tutorials) lives in the MkDocs
   navigation and/or an explicit `order` field in the catalog — never in
   the slug. Inserting, removing, or reordering resources touches that
   metadata only, with no renames.

5. **File paths mirror the id.** The repository path is
   `data/<namespace>/<slug>.<ext>`, and the extension follows the format:
   generic IUCr structures `.cif`; EasyDiffraction experiment-definition
   files `.easydiff`; raw measured data in its native extension
   (`.xye`/`.gr`/`.dat`/`.xys`); multi-file scans and project archives
   `.zip`.

6. **Listings show a positional `#`; the slug is the only persisted
   handle.** `list_data()` and `list_tutorials()` print a leading `#`
   row counter (consistent with the project's other tables) over a
   deterministic listing order, alongside the slug. The slug is the
   canonical argument everywhere:
   - **The slug is the canonical argument.** `download_data(name)` and
     `download_tutorial(name)` take the slug string as their first
     positional argument, named `name`; the old integer `id=` argument
     is removed, not retyped, and there is no `id=` keyword.
   - **The integer shorthand is an interactive convenience on both
     surfaces.** Both the Python functions and the CLI download command
     **may** additionally accept a positional integer that selects a row
     by position. The shorthand is stateless: the integer is resolved
     against the same deterministic catalog order that `list_*` prints,
     recomputed fresh at call time — there is no persisted "last display"
     state to consult. This number is a transient row index tied to that
     order, never an identity, and there is no `--id` flag.
   - **Saved artifacts are slug-only.** Tutorials, documentation, tests,
     and any other saved code use slugs exclusively; the positional
     integer is for live exploration only and must never be written into
     a persisted artifact, or it reintroduces the order-dependent churn
     this ADR removes.

7. **Slug grammar and boundary validation.** Because `download_data()`,
   `download_tutorial()`, and the CLI accept these ids from public users,
   the id is validated at that boundary *before* any catalog lookup,
   path, or URL is built:
   - A **slug segment** matches `[a-z0-9]+(-[a-z0-9]+)*` — lowercase
     ASCII letters and digits in dash-separated groups, with no leading,
     trailing, or doubled dashes and no other characters.
   - A **tutorial id** is exactly one slug segment.
   - A **dataset id** is `<namespace>/<slug>` with exactly one slash,
     where `<namespace>` is one of the four fixed values (`structures`,
     `experiments`, `measured`, `projects`) — a closed set, so it is an
     enum per `AGENTS.md` — and `<slug>` is one slug segment.
   - An id never contains a file extension, an empty segment, a `.` or
     `..` segment, extra slashes, or any other path/URL separator beyond
     the single namespace slash.
   - A value that violates this grammar raises a clear validation error
     naming the offending input. A well-formed id that is simply absent
     from the index is a distinct "unknown resource" error, not a
     validation error.

## Consequences

- Resource references become self-documenting and stable across
  insertion, removal, and replacement; the `replaces` churn disappears.
- One consistent identifier scheme spans datasets and tutorials and the
  `download_*`/`list_*` API.
- The kind namespace doubles as the on-disk folder, so id and path stay
  in sync and the kind is visible without a separate column.
- A one-time migration is required: rename every dataset id and file,
  rewrite `index.json`, rename the tutorial sources and their generated
  notebooks, update the MkDocs nav and the `download_*`/`list_*` calls in
  all tutorials and docs, and move order into metadata. The full
  old → new name tables are recorded in the §Name map below; only the
  step-by-step migration mechanics belong in the implementation plan.
- The optional positional-integer shorthand is a convenience only;
  because it is order-dependent, it must never appear in saved code, or
  it reintroduces exactly the churn this ADR removes.

## Alternatives Considered

- **Keep integer ids.** Rejected: opaque, and they churn on
  replace/insert/remove as shown above.
- **Stable, never-reused integer ids.** Rejected: a permanent number is
  just the current `ed-N` scheme, which still renumbers nothing but also
  conveys nothing and already accumulated `replaces` chains.
- **Version/`data-vN` tags or versioned directories.** Out of scope here
  and rejected in `data-source-pinning` (multi-purpose repo; prefer
  replace-in-place).
- **Numeric ordering for tutorials.** Rejected: tutorials are authored in
  feature-implementation order, not learning order, so a numeric id is
  not a meaningful or stable sequence; order belongs in nav metadata.
- **Slug-only with no positional shortcut.** Viable and strictest; the
  positional `#` is offered as an interactive convenience under the
  guardrail in Decision 6.

## Name map

This is the authoritative old → new **name** map for every resource that
exists today. The step-by-step migration *mechanics* (rewriting
`index.json`, moving files, regenerating notebooks, wiring nav order, and
updating the `download_*`/`list_*` calls) remain a plan concern; the
names themselves are fixed here.

### Datasets

The superseded integer ids from the `replaces` chains
(`28, 30, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43`) disappear — each chain
collapses to one stable slug overwritten in place.

**`structures/` — crystal-structure import CIFs**

| Old id / file               | New id              |
| --------------------------- | ------------------- |
| 1 `ed-1.cif` (La0.5Ba0.5CoO3) | `structures/lbco`   |
| 20 `ed-20.cif` (Tb2Ti2O7)     | `structures/tbti`   |
| 21 `ed-21.cif` (Taurine)      | `structures/taurine`|

**`experiments/` — EasyDiffraction experiment-definition files**

| Old id / file                                  | New id                |
| ---------------------------------------------- | --------------------- |
| 2 `ed-2.cif` (LBCO HRPT, experiment definition) | `experiments/lbco-hrpt`|

> Id 2 is a full experiment-definition file: its id is the
> extension-free `experiments/lbco-hrpt` (per Decisions 1 and 5), and the
> stored file migrates from `.cif` to the new `.easydiff` format, so its
> path is `data/experiments/lbco-hrpt.easydiff`. Id 3, which previously
> shared the "LBCO HRPT" description, is the *raw measured pattern* and
> moves to `measured/` below.

**`measured/` — raw measured or simulated data**

| Old id / file                                   | New id                            |
| ----------------------------------------------- | --------------------------------- |
| 3 `ed-3.xye` (LBCO HRPT, 300 K pattern)         | `measured/lbco-hrpt`              |
| 4 `ed-4.gr` (NaCl)                              | `measured/nacl-pdf`               |
| 5 `ed-5.gr` (Si, NOMAD)                         | `measured/si-pdf-nomad`           |
| 6 `ed-6.gr` (Ni)                               | `measured/ni-pdf`                 |
| 7 `ed-7.xye` (Si, SEPD)                         | `measured/si-sepd`                |
| 8 `ed-8.xye` (LBCO+Si, McStas)                  | `measured/lbco-si-mcstas`         |
| 9 `ed-9.xys` (NCAF, WISH banks 5&6)             | `measured/ncaf-wish-b56`          |
| 10 `ed-10.xys` (NCAF, WISH banks 4&7)           | `measured/ncaf-wish-b47`          |
| 11 `ed-11.xye` (HS, HRPT)                       | `measured/hs-hrpt`                |
| 12 `ed-12.xye` (Co2SiO4, D20)                   | `measured/cosio-d20`              |
| 13 `ed-13.dat` (PbSO4, D1A)                     | `measured/pbso4-d1a`              |
| 14 `ed-14.dat` (PbSO4, D1A 1st half)            | `measured/pbso4-d1a-part1`        |
| 15 `ed-15.dat` (PbSO4, D1A 2nd half)            | `measured/pbso4-d1a-part2`        |
| 16 `ed-16.dat` (PbSO4, lab X-ray)               | `measured/pbso4-xray`             |
| 17 `ed-17.xye` (Si, McStas DMSC2025)            | `measured/si-mcstas-dmsc2025`     |
| 18 `ed-18.xye` (LBCO+Si, McStas DMSC2025)       | `measured/lbco-si-mcstas-dmsc2025`|
| 19 `ed-19.xye` (Tb2Ti2O7, HEiDi)               | `measured/tbti-heidi`             |
| 22 `ed-22.xye` (Taurine, SENJU)                 | `measured/taurine-senju`          |
| 23 `ed-23.zip` (Co2SiO4 D20 T-scan, 20 files)   | `measured/cosio-d20-scan-20f`     |
| 24 `ed-24.zip` (... 156 files)                  | `measured/cosio-d20-scan-156f`    |
| 25 `ed-25.zip` (... 3 files)                    | `measured/cosio-d20-scan-3f`      |
| 26 `ed-26.zip` (... 46 files)                   | `measured/cosio-d20-scan-46f`     |
| 27 `ed-27.zip` (... 23 files)                   | `measured/cosio-d20-scan-23f`     |
| 29 `ed-29.zip` (... 213 files)                  | `measured/cosio-d20-scan-213f`    |
| 31 `ed-31.dat` (La 7-cation perovskite, synchrotron X-ray) | `measured/hep7c-xray-synchrotron` |
| 32 `ed-32.dat` (La 7-cation perovskite, lab Cu Ka)         | `measured/hep7c-xray-cuka`        |
| 33 `ed-33.zip` (ferrite+austenite, BEER)        | `measured/ferrite-austenite-beer` |

> Ids 31 and 32 previously shared the description "LaM7O3, X-ray". Their
> `.pcr` sources show both are the same La/7-cation high-entropy
> perovskite (GdFeO3-type, Pnma) measured on different instruments:
> 31 is synchrotron (lambda = 0.2071 A), 32 is lab Cu Ka1 (Bruker D8).
> The sample's own `hep7c` code disambiguates them, and their index
> descriptions are made distinct to match.

**`projects/` — saved EasyDiffraction project archives (chains collapse)**

| Old ids / files                          | New id                  |
| ---------------------------------------- | ----------------------- |
| 28, 30, 36, 40, 44 (LBCO HRPT, 300 K)    | `projects/lbco-hrpt`    |
| 34, 37, 41, 45 (Co2SiO4 D20 T-scan)      | `projects/cosio-d20-scan`|
| 35, 38, 42, 46 (emcee, LBCO HRPT)        | `projects/lbco-hrpt-emcee`|
| 39, 43, 47 (bumps-dream, LBCO HRPT)      | `projects/lbco-hrpt-dream`|

### Tutorials

Presentation order moves to the MkDocs nav (Decision 4), so these slugs
carry no sequence and can be inserted, removed, or reordered freely.
There is no `ed-19` tutorial — id 19 is a dataset only.

| Old id | Title                                          | New id                            |
| ------ | ---------------------------------------------- | --------------------------------- |
| ed-1   | Structure Refinement: LBCO, HRPT (from CIF)    | `refine-lbco-hrpt-from-cif`       |
| ed-2   | Structure Refinement: LBCO, HRPT (from data)   | `refine-lbco-hrpt-from-data`      |
| ed-3   | Structure Refinement: LBCO, HRPT (report)      | `refine-lbco-hrpt-report`         |
| ed-4   | Refinement: PbSO4, NPD+XRD                     | `refine-pbso4-joint`              |
| ed-5   | Refinement: Co2SiO4, D20                       | `refine-cosio-d20`                |
| ed-6   | Refinement: HS, HRPT                           | `refine-hs-hrpt`                  |
| ed-7   | Refinement: Si, SEPD                           | `refine-si-sepd`                  |
| ed-8   | Refinement: NCAF, WISH                         | `refine-ncaf-wish`                |
| ed-9   | Refinement: LBCO+Si, McStas                    | `refine-lbco-si-mcstas`           |
| ed-10  | PDF: Ni, NPD                                   | `pdf-ni-npd`                      |
| ed-11  | PDF: Si, NOMAD (SNS)                           | `pdf-si-nomad`                    |
| ed-12  | PDF: NaCl, XRD                                 | `pdf-nacl-xrd`                    |
| ed-13  | Fitting exercise: Si, LBCO                     | `fitting-exercise-si-lbco`        |
| ed-14  | Refinement: Tb2Ti2O7, HEiDi                    | `refine-tbti-heidi`               |
| ed-15  | Refinement: Taurine, SENJU                     | `refine-taurine-senju`            |
| ed-16  | Joint: Si, Bragg+PDF                           | `joint-si-bragg-pdf`              |
| ed-17  | Refinement: Co2SiO4, D20 (T-scan)              | `refine-cosio-d20-tscan`          |
| ed-18  | Load Project and Fit: LBCO, HRPT               | `load-and-fit-lbco-hrpt`          |
| ed-20  | Instrument calibration: BEER, ESS              | `calibrate-beer-ess`              |
| ed-21  | Bayesian (bumps-dream): LBCO, HRPT             | `bayesian-dream-lbco-hrpt`        |
| ed-22  | Bayesian (emcee): Tb2Ti2O7, HEiDi              | `bayesian-emcee-tbti-heidi`       |
| ed-23  | Refinement: Co2SiO4 D20 (T-scan, resumed)      | `refine-cosio-d20-tscan-resumed`  |
| ed-24  | Bayesian Display (bumps-dream): LBCO, HRPT     | `bayesian-dream-display-lbco-hrpt`|
| ed-25  | Bayesian (emcee): LBCO, HRPT                   | `bayesian-emcee-lbco-hrpt`        |
| ed-26  | Bayesian Resume (emcee): LBCO, HRPT            | `bayesian-emcee-resume-lbco-hrpt` |
| ed-27  | Calculation Without Data: LBCO, CWL            | `simulate-lbco-cwl`               |
| ed-28  | Calculation Without Data: Si, TOF              | `simulate-si-tof`                 |
| ed-29  | Calculation Without Data: NaCl, X-ray          | `simulate-nacl-xray`              |

## Deferred Work

- The step-by-step migration *mechanics* — rewriting `index.json`,
  moving/renaming files, regenerating notebooks, wiring nav order, and
  updating the `download_*`/`list_*` calls in tutorials and docs — are an
  implementation concern for the plan, not this ADR. The old → new
  **name** map itself is fixed above in §Name map.
- Whether to implement the positional-integer shorthand at all, or ship
  slug-only first, is left to the plan.
