# ADR: EasyDiff Project Persistence

**Status:** Accepted  
**Date:** 2026-06-12

## Group

Persistence.

## Context

`AGENTS.md` says CIF maps to `DatablockItem` / `DatablockCollection` and
`CategoryItem` / `CategoryCollection`, and that CIF naming should be
followed unless a better API is clear. The better API case now exists in
several places.

EasyDiffraction already exposes user-facing names that intentionally do
not mirror official CIF names:

- `atom_site.adp_iso` instead of `B_iso_or_equiv` or `U_iso_or_equiv`
- `atom_site_aniso.adp_11` instead of `B_11`, `U_11`, or `beta_11`
- `experiment.instrument.setup_wavelength` instead of a radiation
  wavelength loop
- `experiment.instrument.calib_d_to_tof_*` instead of a
  `_pd_calib_d_to_tof` coefficient loop
- `experiment.preferred_orientation.march_r` instead of the long
  `_pd_pref_orient_March_Dollase.r` project tag

The current accepted ADRs split the save/export surface only partly.
Default project files are still named `*.cif`, while
[`iucr-cif-tag-alignment.md`](iucr-cif-tag-alignment.md) also says the
default save should use IUCr-aligned structure tags in some areas. That
makes the project files look stricter than they really are, and it
pushes unfriendly official names back into the round-trip format used by
scientists and by EasyDiffraction itself.

Report CIF is different. `project.report.save_cif()` is the intended
external submission/export boundary, and it already has a separate
writer with IUCr-oriented reshaping and extension namespacing.

## Relationship To Existing ADRs

If accepted, this ADR amends or supersedes parts of several accepted
ADRs. Acceptance must update those ADRs and
[`docs/dev/adrs/index.md`](../index.md) so the accepted documentation
does not describe conflicting persistence layouts.

- Supersedes the **default-save naming and file-extension** parts of
  [`iucr-cif-tag-alignment.md`](iucr-cif-tag-alignment.md). Report-CIF
  export remains governed by that ADR's IUCr-aligned writer policy.
- Amends
  [`python-cif-category-correspondence.md`](python-cif-category-correspondence.md)
  by replacing the scoped Python-to-`project.cif` correspondence with
  Python-to-EasyDiff correspondence across project files.
- Amends
  [`project-facade-and-persistence.md`](project-facade-and-persistence.md)
  by replacing `project.cif`, `structures/*.cif`, `experiments/*.cif`,
  and `analysis/analysis.cif` with the `.easydiff` project layout.
- Amends [`category-owner-sections.md`](category-owner-sections.md) only
  for file-format terminology. The distinction between real data blocks
  and singleton category-owner sections remains.
- Carries forward
  [`free-flag-cif-encoding.md`](free-flag-cif-encoding.md) for
  free/fixed parameter encoding inside STAR values.

Other accepted ADRs that mention `project.cif`, `analysis/analysis.cif`,
or `structures/*.cif` need follow-up wording updates when this ADR is
accepted, but their domain decisions remain unchanged unless explicitly
listed above.

## Decision

Adopt **EasyDiff** as the internal EasyDiffraction project persistence
format:

- EasyDiff uses STAR syntax and leading-underscore data names.
- EasyDiff is an EasyDiffraction-owned schema, not an IUCr dictionary
  claim.
- EasyDiff project names optimize for Python/API discoverability,
  readable diffs, and safe hand editing.
- IUCr CIF remains a strict import/export boundary format.

Use **EasyDiff** as the human-facing schema/format name in prose,
headings, UI labels, and documentation tables. Use lowercase only for
literal syntax: `.easydiff` for the file extension and `_easydiff.*` for
the schema-marker category/items. Do not use `EASYDIFF` unless quoting
an external source that has already standardized that spelling.

Persist project state using `.easydiff` files:

```text
project_dir/
|-- project.easydiff
|-- structures/
|   `-- <structure>.easydiff
|-- experiments/
|   `-- <experiment>.easydiff
|-- analysis/
|   |-- analysis.easydiff
|   |-- results.csv
|   `-- results.h5
`-- reports/
    `-- <project>.cif
```

The report file remains `reports/<project>.cif` and remains strict
IUCr/pdCIF as far as the project can make it. Nonstandard report values
continue to use `_easydiffraction_*` extension categories inside report
CIF.

EasyDiff governs the `*.easydiff` files only. Existing non-STAR analysis
artifacts keep their current formats: `analysis/results.h5` remains the
binary fit-result sidecar, and `analysis/results.csv` remains the
tabular sequential-fit output used by plotting and user inspection.

The existing gemmi-based parser reads STAR/CIF content rather than
relying on the file extension, so no new low-level parser is required.
The implementation work is in save/load path discovery, filename
conventions, tag aliases, validation, CLI help, documentation, and
tutorials.

### File Extension Alternatives

The extension decision is separate from the tag-naming decision.

**Keep `.cif`, but document it as an EasyDiffraction STAR dialect.**
This minimizes migration churn: existing ZIP project detection, docs,
tutorials, tests, and external workflows that look for `project.cif`
keep working. The downside is that the file name continues to imply
strict CIF dictionary compatibility for files that intentionally use
EasyDiffraction-owned names such as `_atom_site.adp_iso` and
`_instrument.setup_wavelength`.

**Use `.easydiff` for project persistence.** This is the selected
option. It makes the file type honest: STAR syntax, EasyDiffraction
schema. The cost is a beta layout migration and documentation churn, but
it prevents scientists and external tools from mistaking project state
files for submission/interchange CIFs.

**Use `.edstar`.** This is rejected. STAR is the syntax layer, while the
saved files are EasyDiffraction application artifacts with an
EasyDiffraction-owned schema. The name over-emphasizes the syntax and
can sound like a new generic STAR dialect. It also keeps the `ed`
prefix, which crystallographers may read as electron diffraction.

**Use `.easydiffraction`.** This is rejected. It identifies the product
but not the syntax, is long for files scientists may inspect and share,
and would be awkward if EasyDiffraction later owns non-STAR project
artifacts with the same brand name. `EasyDiff` already expands the
product association into the format name: EasyDiffraction-owned STAR.

**Use `.edcif`.** This advertises EasyDiffraction ownership but still
suggests CIF dictionary semantics. It is therefore less clear than
`.easydiff`. It is also too easy to read as electron-diffraction CIF,
matching the existing `cif_ed` naming convention in the COMCIFS
electron-diffraction dictionary work.

**Use `.txt`.** This is rejected. Its one real advantage is that a
desktop double-click opens it in any text editor with no file
association — but that is a GUI-only benefit. In a terminal, notebook,
or CLI workflow (`cat`, `less`, `vim`, `nano`, `code …`) an `.easydiff`
file opens identically regardless of suffix, so CLI users gain nothing
from `.txt`. Against that, `.txt` loses everything the chosen extension
provides: the project files get **no identity** (a directory of
`project.txt`, `<structure>.txt`, `<experiment>.txt` is
indistinguishable from loose notes or data dumps); they **cannot be
globbed** to locate EasyDiffraction projects (`*.txt` collides with
everything); load-path discovery **weakens** (the loader can no longer
key on a unique suffix and would have to rely on fixed filenames or
content sniffing); and the suffix signals "scratch file, edit freely"
for a format that has selector/body consistency rules and a load-time
validation boundary — the casual hand-editing most likely to corrupt it.
`.txt` is the opposite extreme from `.cif`: where `.cif` over-claims
dictionary semantics, `.txt` claims none at all, so the same honesty
argument that rejects `.cif` also rejects `.txt`. The "I can't open an
unknown extension" concern that motivates `.txt` is instead addressed by
the plain-text guarantee in §Naming Policy, which keeps the files
openable in any editor without sacrificing identity.

## Naming Policy

EasyDiff data names should follow the public EasyDiffraction model:

```text
_<category>.<field>
```

Use leading underscores because they are part of STAR/CIF data-name
syntax, not Python privacy markers.

Use API-oriented field names for project persistence:

```text
_atom_site.adp_iso
_atom_site.adp_type
_atom_site_aniso.adp_11
_instrument.setup_wavelength
_instrument.calib_d_to_tof_linear
_preferred_orientation.march_r
```

Three rules make these names deterministic across the inventory:

- **Field names follow the public property, not the descriptor
  `Parameter.name`.** Where the two differ — notably the TOF peak
  profile, whose descriptors are stored as bare stems (`gauss_sigma_0`,
  `lorentz_gamma_0`, `rise_alpha_0`, `decay_beta_0`) while the public
  properties carry grouping prefixes (`broad_gauss_sigma_0`,
  `broad_lorentz_gamma_0`, `exp_rise_alpha_0`, `exp_decay_beta_0`) —
  EasyDiff writes the public-property name. This is the point of the
  format: a saved field matches the Python path a scientist types. The
  current bare CIF stem is preserved as a read alias.
- **Loop (collection) categories use the singular row-category form of
  the public owner attribute**, following the CIF convention that a loop
  of many rows is named in the singular (`_atom_site` for many atom
  sites). So `structure.atom_sites` → `_atom_site`, `analysis.aliases` →
  `_alias`, `experiment.excluded_regions` → `_excluded_region`,
  `experiment.linked_phases` → `_linked_structure`,
  `experiment.linked_crystal` → `_linked_structure`. This is
  intentionally the singular noun, not the internal
  `CategoryItem._category_code`, which is plural for some collections
  (for example `excluded_regions`, `linked_phases`) and singular for
  others (`alias`, `constraint`). The plural collection name stays in
  the Python API (`structure.atom_sites`); the file describes the
  per-row item, so it is singular — the universal STAR/CIF convention.
- **Row keys use `id` for a row's own local identity and `<target>_id`
  for a reference to another datablock.** Every loop category's own
  primary key is `id` — including `_atom_site.id` and `_alias.id`,
  replacing the CIF-specific `label` so users do not memorize which
  categories key on `label`. A column that references a separate
  datablock keeps the explicit `<target>_id` form: `_linked_structure`,
  `_preferred_orientation`, and `_refln` (powder) reference a structure
  datablock via `structure_id`; `_joint_fit` references an experiment
  via `experiment_id`. The `_id` suffix always means "points at another
  datablock's `id`." Report CIF still emits the official keys
  (`_atom_site.label`, `_pd_phase_block.id`), and `label` / `phase_id`
  remain read aliases. Tightly-coupled satellite loops reuse the parent
  key name (`_atom_site_aniso.id` joins `_atom_site.id`), mirroring how
  CIF reuses `_atom_site_aniso.label`.

### Abbreviation Policy

Spell every word in full. Abbreviate a word only if its short form is on
the approved allowlist below — a short form qualifies only when **both**
(1) the IUCr CIF dictionaries use it in data names and (2) it is the
form a crystallographer or instrument scientist recognizes on sight. The
same concept uses the same form in every name. Use an initialism (`h_m`,
`it`) only when the initialism is itself the standard term; otherwise
use the recognizable word (`march`, not `m_d`).

CIF-named concepts inherit CIF's spelling automatically (CIF's
abbreviations are this allowlist's source, and report export must emit
them anyway). EasyDiffraction-owned concepts use full words, drawing
only from the allowlist.

**Approved abbreviations:** `calc` (calculated), `meas` (measured),
`coef` (coefficient), `su` (standard uncertainty), `iso`/`aniso`
(isotropic/anisotropic), `fract` (fractional), `coord` (coordinate, only
for coordinate-code/template names), `inc` (increment), `min`/`max`,
`prof` (profile), `r`/`wr`/`gt` (R-factor / weighted-R / greater-than),
`h_m` (Hermann–Mauguin), `it` (International Tables), `id`,
`index_h`/`index_k`/`index_l` (Miller indices), `adp` (atomic
displacement parameter), `tof` (time-of-flight), `cwl` (constant
wavelength), `fcj` (Finger–Cox–Jephcoat), `q` (momentum transfer).

**Always spelled in full** (not on the allowlist): `parameter` (not
`param`), `distance` (not `dist`), `reciprocal` and `quadratic` (not
`recip`/`quad`), `preferred_orientation` (CIF's `pref_orient`
contraction is not sight-recognized), and MCMC terms such as
`effective_sample_size` and `gelman_rubin`.

Persist selectors for user-visible model choices, and keep value names
generic when they represent the same user concept across selector
values:

```text
_background.type line_segment

loop_
_background.id
_background.position
_background.intensity
1 10.0 120.0
2 20.0 118.0
```

```text
loop_
_atom_site.id
_atom_site.adp_type
_atom_site.adp_iso
Si Biso 0.5
O  Uiso 0.0063
```

Do not prefix internal EasyDiff categories with `_easydiffraction_` or
`_easydiff_`. The `.easydiff` suffix and schema marker already identify
the dialect.

Use `_easydiffraction_*` for custom keys serialized into strict report
CIF when a nonstandard extension must coexist with official IUCr tags.
Do not use `_easydiff_*` in report CIFs. `_easydiff.*` is reserved for
the EasyDiff schema marker in project files, while report CIF is an
IUCr-facing export with EasyDiffraction extension categories. Keeping
the prefixes separate means report-CIF extensions can remain stable even
if the internal EasyDiff project schema changes.

Each EasyDiff file should include a schema marker near the top:

```text
_easydiff.schema_name EasyDiffraction
_easydiff.schema_version 1
```

Loaders must require `schema_name == 'EasyDiffraction'` when the marker
is present. For `schema_version`, the v1 loader accepts `1`, rejects
newer major versions with a clear error, and rejects missing markers in
`.easydiff` project files. The marker is therefore a validation
boundary, not decorative metadata.

**Plain-text guarantee (openability).** EasyDiff files are plain UTF-8
STAR text with no binary content, so they open and hand-edit in any text
editor. The `.easydiff` suffix is an honest _label_, not a barrier: even
where the operating system has no default application registered for it,
a user can always open the file with "Open With → any text editor" (or
`cat`/`less`/`vim`/`nano`/`code` in a terminal). This is the deliberate
answer to the "unknown extension" concern that would otherwise argue for
a generic `.txt` (see §File Extension Alternatives): EasyDiff keeps the
universal openability of plain text while retaining a distinct,
greppable identity. Editors may additionally be mapped to treat
`*.easydiff` as CIF/STAR for syntax highlighting — something a generic
`.txt` cannot provide per-file-type.

### Selector Validation Contract

Selectors are authoritative boundary input. During restore, loaders read
selector fields such as `_background.type`, `_minimizer.type`, and
`_atom_site.adp_type` before loading the value fields controlled by
those selectors.

When selector and body fields disagree, load rejects the file with a
clear error. It must not silently drop rows, silently switch the
selector, or let one side win. Examples:

- `_background.type chebyshev` with `_background.position` /
  `_background.intensity` line-segment rows is invalid.
- `_background.type line_segment` with Chebyshev-only fields is invalid.
- unknown selector values are invalid.

EasyDiff v1 does not rename selector values, so it has no selector-value
legacy aliases. The `import_names`/read-alias mechanism covers data-name
aliases only. If a future ADR renames a selector value, that ADR must
also define where the value alias map lives, for example on the
`(str, Enum)` that owns the closed value set or on the category setter
that validates the selector.

If a selector is absent in a legacy file, the loader may use the current
category default only when no implementation-specific fields are
present. If implementation-specific fields are present and the type
cannot be resolved unambiguously, load rejects with a clear error.

### Free/Fixed Fit Flags

EasyDiff keeps the accepted free/fixed parameter encoding from
[`free-flag-cif-encoding.md`](free-flag-cif-encoding.md):

- fixed or constrained numeric parameters write as plain values;
- independently free parameters write with uncertainty brackets, for
  example `3.8909()` or `3.89(20)`;
- user-constrained dependent parameters write without brackets.

This remains valid because EasyDiff uses STAR value syntax. The schema
marker and renamed data names do not change the value-level round-trip
contract.

## Compatibility

Project restore should accept:

- the new `.easydiff` project layout;
- official CIF import tags where supported today;
- known EasyDiffraction data-name read aliases in `CifHandler` import
  aliases.

Project restore should not load the previous beta `.cif` project layout.
The project is still in beta, so no project-persistence deprecation shim
is required.

### Restore Contract

The loader follows a fixed contract:

- **`.easydiff` takes precedence.** When a project directory contains
  both `project.easydiff` and a legacy `project.cif`, the loader reads
  `project.easydiff` and ignores `project.cif`, treating the `.cif` as a
  stale pre-migration copy. It does not merge the two.
- **Clear error for legacy-only projects.** A directory that contains
  only `project.cif` fails to load with an explicit migration error that
  names the file and tells the user to open it in a supporting version
  and re-save as `.easydiff`. The loader never silently produces an
  empty or partial project.
- **Clear error for missing EasyDiff metadata.** A project directory
  with neither `project.easydiff` nor legacy `project.cif` fails with an
  explicit message naming the required `project.easydiff` marker.

## Handler Model

The current `CifHandler.names` list is overloaded: the first entry is
the default write tag, and the full list is also an import alias list.
EasyDiff should make this explicit.

Proposed concept:

```python
StarHandler(
    project_name='_atom_site.adp_iso',
    import_names=[
        '_atom_site.adp_iso',
        '_atom_site.B_iso_or_equiv',
        '_atom_site.U_iso_or_equiv',
    ],
    iucr_name=None,
)
```

The exact class name can remain `CifHandler` during migration, but the
responsibilities should be explicit:

- `project_name`: EasyDiff write name.
- `import_names`: accepted EasyDiff/CIF/legacy read aliases.
- `iucr_name`: single-field report-CIF name when a simple mapping
  exists.
- category transformers: report-CIF reshaping when a field cannot map
  one-to-one.

## Consequences

### Positive

- Project files stop claiming to be strict CIF while still using a
  mature STAR parser and syntax.
- Python and saved-project names become easier for scientists to match.
- Official CIF remains available where it matters: import/export and
  report submission.
- Type-neutral ADP persistence becomes straightforward:
  `_atom_site.adp_iso` and `_atom_site_aniso.adp_ij`.
- Future project-owned categories no longer need to search for awkward
  pseudo-CIF tags before they have an external dictionary counterpart.

### Trade-Offs

- The saved project layout changes from `*.cif` to `*.easydiff`.
- Existing docs, tutorials, tests, ZIP project detection, and loaders
  need an explicit migration.
- External tools that previously tried to read project `*.cif` files
  must instead use `reports/<project>.cif` or official CIF import/export
  paths.
- The code needs a clearer handler API so import aliases and write names
  are not conflated.

## Considered Naming Options

### Option A: Type In The Data Names

This mirrors how CIF often encodes the selected convention or model in
the item names themselves.

```text
loop_
_background_line_segment.id
_background_line_segment.x
_background_line_segment.y
1 10.0 120.0
2 20.0 118.0
```

```text
loop_
_atom_site.label
_atom_site.B_iso_or_equiv
Si 0.5
```

Advantages:

- The tag itself tells a hand editor which convention or model is being
  edited.
- There is no separate selector field that can disagree with the value
  fields.
- It matches external interchange formats where independent programs
  cannot rely on EasyDiffraction project state.

Disadvantages:

- It breaks stable parameter identity for fields like ADPs. The same
  conceptual value would move between `B_iso_or_equiv`,
  `U_iso_or_equiv`, and `beta_*`, which complicates aliases,
  constraints, free flags, tables, and UI state.
- Empty selected models are hard to represent. A line-segment background
  with no points has no loop rows from which to infer the selected type.
- It reintroduces long dictionary names into the internal project
  format.

### Option B: Selector Plus Generic Names

This is the selected EasyDiff policy.

```text
_background.type line_segment

loop_
_background.id
_background.position
_background.intensity
1 10.0 120.0
2 20.0 118.0
```

```text
loop_
_atom_site.id
_atom_site.adp_type
_atom_site.adp_iso
Si Biso 0.5
O  Uiso 0.0063
```

Advantages:

- It matches the Python API and the switchable-category selector
  contract.
- Parameter names remain stable across type switches, which protects
  aliases, constraints, fit flags, parameter tables, and display state.
- Empty selected models are representable because the selector exists
  even when no value rows exist.
- The report CIF writer can still emit official type-specific tags at
  the external boundary.

Disadvantages:

- A hand editor must read selector and values together.
- Raw text can contain inconsistent combinations, such as
  `_background.type chebyshev` with `_background.position` rows. Load
  validation must report these boundary-input errors clearly.

### Option C: Selector Plus Type-Specific Body

This keeps an explicit selector and also embeds the selected type in the
body tags.

```text
_background.type line_segment

loop_
_background_line_segment.id
_background_line_segment.x
_background_line_segment.y
1 10.0 120.0
2 20.0 118.0
```

Advantages:

- The selected type remains explicit even for empty models.
- Body tags are highly self-describing.
- It may be useful for rare categories whose implementations have
  genuinely different shapes.

Disadvantages:

- It duplicates type information in two places.
- It creates consistency rules between selector and body category.
- It adds loader complexity and still harms API-to-file predictability.

EasyDiff therefore uses Option B by default. Option C is allowed only
when selected implementations have genuinely different data shapes and
the type-specific body names improve hand editing more than they harm
consistency. ADPs are not such a case: `adp_iso` and `adp_ij` remain
generic values interpreted through `adp_type`.

## Parameter Inventory

This table inventories persisted descriptors currently declared through
`CifHandler` in `src/easydiffraction` as of 2026-06-12. Compact
`{a,b,c}` notation means each listed field is a separate parameter. The
official/report column lists IUCr or pdCIF names where a current
one-to-one or report-transform mapping is known. Blank means no official
CIF name is currently available or the current report path uses an
EasyDiffraction extension tag.

The table is intended to be exhaustive for every `CifHandler`-declared
descriptor in `src/easydiffraction`. Implementation must verify that
claim with a generated inventory before changing write tags; any
descriptor absent from this table is a migration blocker.

| Area                                                              | Current EasyDiffraction names                                                                                                                                                                                                                                                                                                                                                          | Current project tags                                                                                                                                                                                                                                                                                    | Suggested EasyDiff tags                                                                                                                                                                                                                                                                                                                                       | Official/report CIF names                                                                                                    |
| ----------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| `analysis.aliases`                                                | `label`, `param_unique_name`                                                                                                                                                                                                                                                                                                                                                           | `_alias.{label,param_unique_name}`                                                                                                                                                                                                                                                                      | `_alias.{id,parameter_unique_name}`                                                                                                                                                                                                                                                                                                                           |                                                                                                                              |
| `analysis.constraints`                                            | `id`, `expression`                                                                                                                                                                                                                                                                                                                                                                     | `_constraint.{id,expression}`                                                                                                                                                                                                                                                                           | `_constraint.{id,expression}`                                                                                                                                                                                                                                                                                                                                 |                                                                                                                              |
| `analysis.fit_parameter_correlations`                             | `id`, `source_kind`, `param_unique_name_i`, `param_unique_name_j`, `correlation`                                                                                                                                                                                                                                                                                                       | `_fit_parameter_correlation.{id,source_kind,param_unique_name_i,param_unique_name_j,correlation}`                                                                                                                                                                                                       | `_fit_parameter_correlation.{id,source_kind,parameter_unique_name_i,parameter_unique_name_j,correlation}`                                                                                                                                                                                                                                                     |                                                                                                                              |
| `analysis.fit_parameters`                                         | `param_unique_name`, `fit_min`, `fit_max`, `fit_bounds_uncertainty_multiplier`, `start_value`, `start_uncertainty`, `posterior_best_sample_value`, `posterior_median`, `posterior_uncertainty`, `posterior_interval_68_low`, `posterior_interval_68_high`, `posterior_interval_95_low`, `posterior_interval_95_high`, `posterior_gelman_rubin`, `posterior_effective_sample_size_bulk` | `_fit_parameter.*` with same item names                                                                                                                                                                                                                                                                 | `_fit_parameter.{parameter_unique_name,fit_min,fit_max,bounds_uncertainty_multiplier,start_value,start_uncertainty,posterior_best_sample_value,posterior_median,posterior_uncertainty,posterior_interval_68_low,posterior_interval_68_high,posterior_interval_95_low,posterior_interval_95_high,posterior_gelman_rubin,posterior_effective_sample_size_bulk}` |                                                                                                                              |
| `analysis.fit_result` common                                      | `result_kind`, `success`, `message`, `iterations`, `fitting_time`, `reduced_chi_square`                                                                                                                                                                                                                                                                                                | `_fit_result.{result_kind,success,message,iterations,fitting_time,reduced_chi_square}`                                                                                                                                                                                                                  | same                                                                                                                                                                                                                                                                                                                                                          | `reduced_chi_square` maps by report topology to `_refine_ls.*` or `_pd_proc_ls.*`                                            |
| `analysis.fit_result` least-squares core                          | `objective_name`, `objective_value`, `n_data_points`, `n_parameters`, `n_free_parameters`, `degrees_of_freedom`, `covariance_available`, `correlation_available`, `exit_reason`                                                                                                                                                                                                        | `_fit_result.*` with same item names                                                                                                                                                                                                                                                                    | same                                                                                                                                                                                                                                                                                                                                                          | topology-specific `_refine_ls.*` / `_pd_proc_ls.*` for counts where reportable                                               |
| `analysis.fit_result` least-squares R factors                     | `r_factor_all`, `wr_factor_all`, `r_factor_gt`, `wr_factor_gt`                                                                                                                                                                                                                                                                                                                         | `_fit_result.R_factor_all`, `_fit_result.wR_factor_all`, `_fit_result.R_factor_gt`, `_fit_result.wR_factor_gt`                                                                                                                                                                                          | `_fit_result.{r_factor_all,wr_factor_all,r_factor_gt,wr_factor_gt}`                                                                                                                                                                                                                                                                                           | `_refine_ls.{R_factor_all,wR_factor_all,R_factor_gt,wR_factor_gt}`                                                           |
| `analysis.fit_result` powder profile                              | `prof_r_factor`, `prof_wr_factor`, `prof_wr_expected`, `profile_function`, `background_function`                                                                                                                                                                                                                                                                                       | `_fit_result.prof_R_factor`, `_fit_result.prof_wR_factor`, `_fit_result.prof_wR_expected`, `_fit_result.profile_function`, `_fit_result.background_function`                                                                                                                                            | `_fit_result.{prof_r_factor,prof_wr_factor,prof_wr_expected,profile_function,background_function}`                                                                                                                                                                                                                                                            | `_pd_proc_ls.{prof_R_factor,prof_wR_factor,prof_wR_expected,profile_function,background_function}`                           |
| `analysis.fit_result` fit counts                                  | `number_restraints`, `number_constraints`, `shift_over_su_max`, `shift_over_su_mean`                                                                                                                                                                                                                                                                                                   | `_fit_result.*` with same item names                                                                                                                                                                                                                                                                    | same                                                                                                                                                                                                                                                                                                                                                          | `_refine_ls.{number_restraints,number_constraints}` for counts                                                               |
| `analysis.fit_result` reflection summaries                        | `threshold_expression`, `number_reflns_total`, `number_reflns_gt`                                                                                                                                                                                                                                                                                                                      | `_fit_result.*` with same item names                                                                                                                                                                                                                                                                    | same                                                                                                                                                                                                                                                                                                                                                          | `_reflns.{threshold_expression,number_total,number_gt}`                                                                      |
| `analysis.fit_result` Bayesian                                    | `point_estimate_name`, `sampler_completed`, `credible_interval_inner`, `credible_interval_outer`, `acceptance_rate_mean`, `resolved_random_seed`, `gelman_rubin_max`, `effective_sample_size_min`, `best_log_posterior`                                                                                                                                                                | `_fit_result.*` with same item names                                                                                                                                                                                                                                                                    | same                                                                                                                                                                                                                                                                                                                                                          |                                                                                                                              |
| `analysis.fitting_mode`                                           | `type`                                                                                                                                                                                                                                                                                                                                                                                 | `_fitting_mode.type`                                                                                                                                                                                                                                                                                    | same                                                                                                                                                                                                                                                                                                                                                          |                                                                                                                              |
| `analysis.joint_fit`                                              | `experiment_id`, `weight`                                                                                                                                                                                                                                                                                                                                                              | `_joint_fit.{experiment_id,weight}`                                                                                                                                                                                                                                                                     | same                                                                                                                                                                                                                                                                                                                                                          |                                                                                                                              |
| `analysis.minimizer` common                                       | `type`, `max_iterations`                                                                                                                                                                                                                                                                                                                                                               | `_minimizer.{type,max_iterations}`                                                                                                                                                                                                                                                                      | same                                                                                                                                                                                                                                                                                                                                                          |                                                                                                                              |
| `analysis.minimizer` Bayesian                                     | `sampling_steps`, `burn_in_steps`, `thinning_interval`, `population_size`, `parallel_workers`, `initialization_method`, `random_seed`, `proposal_moves`                                                                                                                                                                                                                                | `_minimizer.*` with same item names                                                                                                                                                                                                                                                                     | same                                                                                                                                                                                                                                                                                                                                                          |                                                                                                                              |
| `analysis.sequential_fit`                                         | `data_dir`, `file_pattern`, `max_workers`, `chunk_size`, `reverse`                                                                                                                                                                                                                                                                                                                     | `_sequential_fit.*` with same item names                                                                                                                                                                                                                                                                | same                                                                                                                                                                                                                                                                                                                                                          |                                                                                                                              |
| `analysis.sequential_fit_extract`                                 | `id`, `target`, `pattern`, `required`                                                                                                                                                                                                                                                                                                                                                  | `_sequential_fit_extract.*` with same item names                                                                                                                                                                                                                                                        | same                                                                                                                                                                                                                                                                                                                                                          |                                                                                                                              |
| `analysis.software` (role loop)                                   | `framework.{name,version,url}`, `calculator.{name,version,url}`, `minimizer.{name,version,url}`, `timestamp`                                                                                                                                                                                                                                                                           | `_software.{framework,calculator,minimizer}_{name,version,url}`, `_software.timestamp`                                                                                                                                                                                                                  | `_software.{id,name,version,url}` loop (`id` ∈ framework/calculator/minimizer); `timestamp` → `_metadata.timestamp`                                                                                                                                                                                                                                           | `_computing.structure_refinement` and `_easydiffraction_software.*` derived in report CIF                                    |
| `experiment.background` selector                                  | `type`                                                                                                                                                                                                                                                                                                                                                                                 | `_background.type`                                                                                                                                                                                                                                                                                      | same                                                                                                                                                                                                                                                                                                                                                          |                                                                                                                              |
| `experiment.background` line segment                              | `id`, `x`, `y`                                                                                                                                                                                                                                                                                                                                                                         | `_pd_background.id`, `_pd_background.line_segment_X`, `_pd_background.line_segment_intensity`                                                                                                                                                                                                           | `_background.{id,position,intensity}`                                                                                                                                                                                                                                                                                                                         | `_pd_background.*` where representable                                                                                       |
| `experiment.background` Chebyshev                                 | `id`, `order`, `coef`                                                                                                                                                                                                                                                                                                                                                                  | `_pd_background.id`, `_pd_background.Chebyshev_order`, `_pd_background.Chebyshev_coef`                                                                                                                                                                                                                  | `_background.{id,order,coef}`                                                                                                                                                                                                                                                                                                                                 | `_pd_background.*` where representable                                                                                       |
| `experiment.calculator`                                           | `type`                                                                                                                                                                                                                                                                                                                                                                                 | `_calculator.type`                                                                                                                                                                                                                                                                                      | same                                                                                                                                                                                                                                                                                                                                                          |                                                                                                                              |
| `experiment.data` Bragg powder                                    | `point_id`, `d_spacing`, `intensity_meas`, `intensity_meas_su`, `intensity_calc`, `intensity_bkg`, `calc_status`, `two_theta`, `time_of_flight`                                                                                                                                                                                                                                        | `_pd_data.point_id`, `_pd_proc.d_spacing`, `_pd_meas.intensity_total`, `_pd_meas.intensity_total_su`, `_pd_calc.intensity_total`, `_pd_calc.intensity_bkg`, `_pd_data.refinement_status`, `_pd_proc.2theta_scan`, `_pd_meas.time_of_flight`                                                             | `_data.{id,d_spacing,intensity_meas,intensity_meas_su,intensity_calc,intensity_bkg,calc_status,two_theta,time_of_flight}`                                                                                                                                                                                                                                     | current `_pd_*` tags, with report profile loop using `_pd_meas.*`, `_pd_calc.*`, `_pd_proc.*`, and `_pd_proc_ls.weight`      |
| `experiment.data` total powder                                    | `point_id`, `r`, `g_r_meas`, `g_r_meas_su`, `g_r_calc`, `calc_status`                                                                                                                                                                                                                                                                                                                  | `_pd_data.point_id`, `_pd_proc.r`, `_pd_meas.intensity_total`, `_pd_meas.intensity_total_su`, `_pd_calc.intensity_total`, `_pd_data.refinement_status`                                                                                                                                                  | `_data.{id,r,g_r_meas,g_r_meas_su,g_r_calc,calc_status}`                                                                                                                                                                                                                                                                                                      | PDF-specific report names are not finalized                                                                                  |
| `experiment.data_range` CWL powder                                | `two_theta_min`, `two_theta_max`, `two_theta_inc`                                                                                                                                                                                                                                                                                                                                      | `_pd_meas.{2theta_range_min,2theta_range_max,2theta_range_inc}`                                                                                                                                                                                                                                         | `_data_range.{two_theta_min,two_theta_max,two_theta_inc}`                                                                                                                                                                                                                                                                                                     | current `_pd_meas.*` tags                                                                                                    |
| `experiment.data_range` single crystal                            | `sin_theta_over_lambda_min`, `sin_theta_over_lambda_max`                                                                                                                                                                                                                                                                                                                               | `_refln.{sin_theta_over_lambda_range_min,sin_theta_over_lambda_range_max}`                                                                                                                                                                                                                              | `_data_range.{sin_theta_over_lambda_min,sin_theta_over_lambda_max}`                                                                                                                                                                                                                                                                                           | current `_refln.*` tags                                                                                                      |
| `experiment.data_range` TOF                                       | `time_of_flight_min`, `time_of_flight_max`, `time_of_flight_inc`                                                                                                                                                                                                                                                                                                                       | `_pd_meas.{time_of_flight_range_min,time_of_flight_range_max,time_of_flight_range_inc}`                                                                                                                                                                                                                 | `_data_range.{time_of_flight_min,time_of_flight_max,time_of_flight_inc}`                                                                                                                                                                                                                                                                                      | current `_pd_meas.*` tags                                                                                                    |
| `experiment.diffrn`                                               | `ambient_temperature`, `ambient_pressure`, `ambient_magnetic_field`, `ambient_electric_field`                                                                                                                                                                                                                                                                                          | `_diffrn.*` with same item names                                                                                                                                                                                                                                                                        | same                                                                                                                                                                                                                                                                                                                                                          | `_diffrn.{ambient_temperature,ambient_pressure}`; fields and electric/magnetic fields are report extensions                  |
| `experiment.excluded_regions`                                     | `id`, `start`, `end`                                                                                                                                                                                                                                                                                                                                                                   | `_excluded_region.{id,start,end}`                                                                                                                                                                                                                                                                       | same                                                                                                                                                                                                                                                                                                                                                          | report free text `_pd_proc.info_excluded_regions` plus extension rows                                                        |
| `experiment.type` → `experiment_type`                             | `sample_form`, `beam_mode`, `radiation_probe`, `scattering_type`                                                                                                                                                                                                                                                                                                                       | `_expt_type.{sample_form,beam_mode,radiation_probe,scattering_type}`                                                                                                                                                                                                                                    | `_experiment_type.{sample_form,beam_mode,radiation_probe,scattering_type}`                                                                                                                                                                                                                                                                                    |                                                                                                                              |
| `experiment.extinction`                                           | `type`, `model`, `mosaicity`, `radius`                                                                                                                                                                                                                                                                                                                                                 | `_extinction.{type,model,mosaicity,radius}`                                                                                                                                                                                                                                                             | same                                                                                                                                                                                                                                                                                                                                                          | `_refine_ls.extinction_method`, `_refine_ls.extinction_coef`, `_refine.special_details` by report transform                  |
| `experiment.instrument` CWL                                       | `setup_wavelength`, `calib_twotheta_offset`, `calib_sample_displacement`, `calib_sample_transparency`                                                                                                                                                                                                                                                                                  | `_instr.wavelength`, `_instr.2theta_offset`, `_instr.sample_displacement`, `_instr.sample_transparency`                                                                                                                                                                                                 | `_instrument.{setup_wavelength,calib_twotheta_offset,calib_sample_displacement,calib_sample_transparency}`                                                                                                                                                                                                                                                    | `_diffrn_radiation_wavelength.value`; `_pd_calib.2theta_offset`                                                              |
| `experiment.instrument` TOF                                       | `setup_twotheta_bank`, `calib_d_to_tof_offset`, `calib_d_to_tof_linear`, `calib_d_to_tof_quad`, `calib_d_to_tof_recip`                                                                                                                                                                                                                                                                 | `_instr.2theta_bank`, `_instr.{d_to_tof_offset,d_to_tof_linear,d_to_tof_quad,d_to_tof_recip}`                                                                                                                                                                                                           | `_instrument.{setup_twotheta_bank,calib_d_to_tof_offset,calib_d_to_tof_linear,calib_d_to_tof_quadratic,calib_d_to_tof_reciprocal}`                                                                                                                                                                                                                            | `_pd_calib_d_to_tof.{id,power,coeff,coeff_su,diffractogram_id}` loop for nonzero coefficients                                |
| `experiment.linked_crystal` → `linked_structure` (single crystal) | `id`, `scale`                                                                                                                                                                                                                                                                                                                                                                          | `_sc_crystal_block.{id,scale}`                                                                                                                                                                                                                                                                          | `_linked_structure.{structure_id,scale}`                                                                                                                                                                                                                                                                                                                      |                                                                                                                              |
| `experiment.linked_phases` → `linked_structures` (powder)         | `id`, `scale`                                                                                                                                                                                                                                                                                                                                                                          | `_pd_phase_block.{id,scale}`                                                                                                                                                                                                                                                                            | `_linked_structure.{structure_id,scale}`                                                                                                                                                                                                                                                                                                                      | `_pd_phase_block.{id,scale}`                                                                                                 |
| `experiment.peak` CWL profile                                     | `type`, `broad_gauss_u`, `broad_gauss_v`, `broad_gauss_w`, `broad_lorentz_x`, `broad_lorentz_y`, `asym_empir_1`, `asym_empir_2`, `asym_empir_3`, `asym_empir_4`, `asym_fcj_1`, `asym_fcj_2`                                                                                                                                                                                            | `_peak.*` with same item names                                                                                                                                                                                                                                                                          | same                                                                                                                                                                                                                                                                                                                                                          | no pdCIF one-to-one parametric profile tags                                                                                  |
| `experiment.peak` TOF profile                                     | `broad_gauss_sigma_{0,1,2}`, `broad_lorentz_gamma_{0,1,2}`, `exp_rise_alpha_{0,1}`, `exp_decay_beta_{0,1}`, `dexp_rise_alpha_{1,2}`, `dexp_decay_beta_{00,01,10}`, `dexp_switch_r_{01,02,03}`                                                                                                                                                                                          | `_peak.{gauss_sigma_0,gauss_sigma_1,gauss_sigma_2,lorentz_gamma_0,lorentz_gamma_1,lorentz_gamma_2,rise_alpha_0,rise_alpha_1,decay_beta_0,decay_beta_1,dexp_rise_alpha_1,dexp_rise_alpha_2,dexp_decay_beta_00,dexp_decay_beta_01,dexp_decay_beta_10,dexp_switch_r_01,dexp_switch_r_02,dexp_switch_r_03}` | `_peak.{broad_gauss_sigma_0,broad_gauss_sigma_1,broad_gauss_sigma_2,broad_lorentz_gamma_0,broad_lorentz_gamma_1,broad_lorentz_gamma_2,exp_rise_alpha_0,exp_rise_alpha_1,exp_decay_beta_0,exp_decay_beta_1,dexp_rise_alpha_1,dexp_rise_alpha_2,dexp_decay_beta_00,dexp_decay_beta_01,dexp_decay_beta_10,dexp_switch_r_01,dexp_switch_r_02,dexp_switch_r_03}`   | no pdCIF one-to-one parametric profile tags                                                                                  |
| `experiment.peak` total scattering                                | `damp_q`, `broad_q`, `cutoff_q`, `sharp_delta_1`, `sharp_delta_2`, `damp_particle_diameter`                                                                                                                                                                                                                                                                                            | `_peak.*` with same item names                                                                                                                                                                                                                                                                          | same                                                                                                                                                                                                                                                                                                                                                          | no finalized PDF-specific CIF tags                                                                                           |
| `experiment.preferred_orientation`                                | `phase_id`, `march_r`, `index_h`, `index_k`, `index_l`, `march_random_fract`                                                                                                                                                                                                                                                                                                           | `_pref_orient.*` with same item names                                                                                                                                                                                                                                                                   | `_preferred_orientation.{structure_id,march_r,index_h,index_k,index_l,march_random_fract}`                                                                                                                                                                                                                                                                    | `_pd_pref_orient_March_Dollase.{phase_id,r,index_h,index_k,index_l}`; random fraction is an EasyDiffraction report extension |
| `experiment.refln` powder calculated                              | `id`, `d_spacing`, `sin_theta_over_lambda`, `index_h`, `index_k`, `index_l`, `phase_id`, `f_calc`, `f_squared_calc`, `two_theta`, `time_of_flight`                                                                                                                                                                                                                                     | `_refln.*` with same item names                                                                                                                                                                                                                                                                         | `_refln.{id,d_spacing,sin_theta_over_lambda,index_h,index_k,index_l,structure_id,f_calc,f_squared_calc,two_theta,time_of_flight}`                                                                                                                                                                                                                             | report powder reflection loop uses `_refln.index_*`, `_refln.F_squared_*`, `_pd_refln.phase_id`, `_refln.d_spacing`          |
| `experiment.refln` single crystal                                 | `id`, `d_spacing`, `sin_theta_over_lambda`, `index_h`, `index_k`, `index_l`, `intensity_meas`, `intensity_meas_su`, `intensity_calc`, `wavelength`                                                                                                                                                                                                                                     | `_refln.*` with same item names                                                                                                                                                                                                                                                                         | same                                                                                                                                                                                                                                                                                                                                                          | `_refln.*`; report maps intensities to `_refln.F_squared_*` where applicable                                                 |
| `structure.atom_sites` identity and coordinates                   | `label`, `type_symbol`, `fract_x`, `fract_y`, `fract_z`, `occupancy`                                                                                                                                                                                                                                                                                                                   | `_atom_site.*` with same item names                                                                                                                                                                                                                                                                     | `_atom_site.{id,type_symbol,fract_x,fract_y,fract_z,occupancy}`                                                                                                                                                                                                                                                                                               | `_atom_site.{label,type_symbol,fract_x,fract_y,fract_z,occupancy}`                                                           |
| `structure.atom_sites` Wyckoff                                    | `wyckoff_letter`, `multiplicity`                                                                                                                                                                                                                                                                                                                                                       | `_atom_site.Wyckoff_symbol`, `_atom_site.site_symmetry_multiplicity`                                                                                                                                                                                                                                    | `_atom_site.{wyckoff_letter,multiplicity}`                                                                                                                                                                                                                                                                                                                    | `_atom_site.Wyckoff_symbol`, `_atom_site.site_symmetry_multiplicity`                                                         |
| `structure.atom_sites` ADP                                        | `adp_iso`, `adp_type`                                                                                                                                                                                                                                                                                                                                                                  | `_atom_site.B_iso_or_equiv`, `_atom_site.ADP_type`                                                                                                                                                                                                                                                      | `_atom_site.{adp_iso,adp_type}`                                                                                                                                                                                                                                                                                                                               | `_atom_site.{B_iso_or_equiv,U_iso_or_equiv}`, `_atom_site.ADP_type`                                                          |
| `structure.atom_site_aniso`                                       | `label`, `adp_11`, `adp_22`, `adp_33`, `adp_12`, `adp_13`, `adp_23`                                                                                                                                                                                                                                                                                                                    | `_atom_site_aniso.label`, `_atom_site_aniso.B_11`, `_atom_site_aniso.B_22`, `_atom_site_aniso.B_33`, `_atom_site_aniso.B_12`, `_atom_site_aniso.B_13`, `_atom_site_aniso.B_23`                                                                                                                          | `_atom_site_aniso.{id,adp_11,adp_22,adp_33,adp_12,adp_13,adp_23}`                                                                                                                                                                                                                                                                                             | `_atom_site_aniso.{label,B_*,U_*,beta_*}` by `adp_type`                                                                      |
| `structure.cell`                                                  | `length_a`, `length_b`, `length_c`, `angle_alpha`, `angle_beta`, `angle_gamma`                                                                                                                                                                                                                                                                                                         | `_cell.*` with same item names                                                                                                                                                                                                                                                                          | same                                                                                                                                                                                                                                                                                                                                                          | same                                                                                                                         |
| `structure.geom`                                                  | `min_bond_distance_cutoff`, `bond_distance_incr`                                                                                                                                                                                                                                                                                                                                       | `_geom.*` with same item names                                                                                                                                                                                                                                                                          | `_geom.{min_bond_distance_cutoff,bond_distance_inc}`                                                                                                                                                                                                                                                                                                          | same                                                                                                                         |
| `structure.space_group`                                           | `name_h_m`, `it_coordinate_system_code`                                                                                                                                                                                                                                                                                                                                                | `_space_group.name_H-M_alt`, `_space_group.IT_coordinate_system_code`                                                                                                                                                                                                                                   | `_space_group.{name_h_m,coord_system_code}`                                                                                                                                                                                                                                                                                                                   | `_space_group.name_H-M_alt`, `_space_group.IT_coordinate_system_code`                                                        |
| `structure.space_group_wyckoff` (derived; **not persisted**)      | `id`, `letter`, `multiplicity`, `site_symmetry`, `coords_xyz`                                                                                                                                                                                                                                                                                                                          | `_space_group_Wyckoff.{id,letter,multiplicity,site_symmetry,coords_xyz}`                                                                                                                                                                                                                                | — (regenerated from `space_group` on load; never written)                                                                                                                                                                                                                                                                                                     | `_space_group_Wyckoff.*`                                                                                                     |
| `project.info` → `metadata`                                       | `name`, `title`, `description`, `created`, `last_modified`; relocated `analysis.software.timestamp` as `timestamp`                                                                                                                                                                                                                                                                     | `_project.id`, `_project.title`, `_project.description`, `_project.created`, `_project.last_modified`; `_software.timestamp`                                                                                                                                                                            | `_metadata.{name,title,description,created,last_modified,timestamp}`                                                                                                                                                                                                                                                                                          |                                                                                                                              |
| `project.rendering_plot`                                          | `type`                                                                                                                                                                                                                                                                                                                                                                                 | `_rendering_plot.type`                                                                                                                                                                                                                                                                                  | same                                                                                                                                                                                                                                                                                                                                                          |                                                                                                                              |
| `project.rendering_structure`                                     | `type`                                                                                                                                                                                                                                                                                                                                                                                 | `_rendering_structure.type`                                                                                                                                                                                                                                                                             | same                                                                                                                                                                                                                                                                                                                                                          |                                                                                                                              |
| `project.rendering_table`                                         | `type`                                                                                                                                                                                                                                                                                                                                                                                 | `_rendering_table.type`                                                                                                                                                                                                                                                                                 | same                                                                                                                                                                                                                                                                                                                                                          |                                                                                                                              |
| `project.report`                                                  | `cif`, `html`, `tex`, `pdf`, `html_offline`                                                                                                                                                                                                                                                                                                                                            | `_report.*` with same item names                                                                                                                                                                                                                                                                        | same                                                                                                                                                                                                                                                                                                                                                          | report-output configuration only                                                                                             |
| `project.structure_style`                                         | `atom_view`, `color_scheme`, `adp_probability`, `atom_scale`                                                                                                                                                                                                                                                                                                                           | `_structure_style.*` with same item names                                                                                                                                                                                                                                                               | same                                                                                                                                                                                                                                                                                                                                                          |                                                                                                                              |
| `project.structure_view`                                          | `show_labels`, `show_moments`, `range_a_min`, `range_a_max`, `range_b_min`, `range_b_max`, `range_c_min`, `range_c_max`                                                                                                                                                                                                                                                                | `_structure_view.*` with same item names                                                                                                                                                                                                                                                                | same                                                                                                                                                                                                                                                                                                                                                          |                                                                                                                              |
| `project.verbosity`                                               | `fit`                                                                                                                                                                                                                                                                                                                                                                                  | `_verbosity.fit`                                                                                                                                                                                                                                                                                        | same                                                                                                                                                                                                                                                                                                                                                          |                                                                                                                              |

## Naming Precedent and Guard Notes

These notes record why several names are intentional, so a future
reviewer does not "correct" them toward a different precedent.

- **Structure links use "structure", not "phase"/"crystal".** The model
  datablock is `Structure` and the API is `project.structures`, so an
  experiment links structures. `experiment.linked_phases` →
  `experiment.linked_structures` (powder, collection) and
  `experiment.linked_crystal` → `experiment.linked_structure` (single
  crystal); both serialize to the `_linked_structure` category. Every
  structure reference uses `structure_id` (mirroring the existing
  `_joint_fit.experiment_id`). `phase`/`crystal`/`phase_id` and the IUCr
  `_pd_phase_block` / `_sc_crystal_block` tags remain read aliases.
  These are public-API renames, not only file-tag changes (blast radius
  ~100+ files); they belong in Phase 1. Accessing the wrong cardinality
  for the experiment family, such as `linked_structure` on a powder
  experiment or `linked_structures` on a single-crystal experiment, must
  fail with a clear sample-form-aware error rather than silently
  ignoring user input.
- **`id` is the universal own-key.** `_atom_site.id` and `_alias.id`
  replace CIF's `label` so the rule "every row has an `id`; `_id`
  columns point elsewhere" has no exceptions. EasyDiff already departs
  from strict CIF (e.g. `adp_iso` for `B_iso_or_equiv`), and report CIF
  still writes the official `_atom_site.label`, so compatibility is
  unaffected.
- **`damp_` groups by effect, not mechanism.** In the total-scattering
  peak, `damp_q` (resolution) and `damp_particle_diameter` (finite size)
  both attenuate the G(r) amplitude envelope, so they share the `damp_`
  family; `broad_` grows peak width, `sharp_` shrinks it, `cutoff_` is
  the Fourier truncation. `damp_particle_diameter` is intentional — do
  not rename it to `particle_diameter`.
- **`two_theta_inc` keeps `inc`.** `inc` is the IUCr pdCIF term
  (`_pd_meas_2theta_range_inc`); `step` is FullProf-internal only.
- **`march_random_fract` is not IUCr `fract`.** IUCr
  `_pd_pref_orient_March_Dollase.fract` is the multi-direction
  fractional contribution; EasyDiff's field is the random/untextured
  fraction (cryspy `_texture_g_2`). Do not collapse them.
- **Type-neutral ADPs are deliberate.** `adp_iso` / `adp_type` /
  `adp_11` stay generic because `adp_type` is co-persisted and
  load-validated, making the B↔U distinction lossless while keeping
  parameter identity stable across a type switch.
- **Report-CIF casing.** EasyDiff lowercases for Python/STAR
  friendliness, but the report writer emits IUCr canonical casing:
  `_refln.F_calc`, `_refln.F_squared_calc`, `_space_group.name_H-M_alt`.
  The uppercase forms are also accepted as read aliases.
- **`coord_system_code` uses existing coordinate wording.** The value is
  still the International Tables coordinate-system qualifier, and report
  CIF still writes `_space_group.IT_coordinate_system_code`, but the
  project-facing API and EasyDiff field use `coord_system_code`. `coord`
  is already used in EasyDiffraction's Wyckoff-coordinate vocabulary
  (`coord_code`, `coords_xyz`), while `it` is not otherwise used in
  project-facing parameter names.
- **`_data` is intentional.** `experiment.data` is already a mass-noun
  owner attribute, so EasyDiff keeps `_data` instead of inventing
  `_data_point`. The row identity is still `_data.id`; the category name
  follows the public owner attribute when the owner is not plural.

## Code/EasyDiff 1-to-1 Correspondence

EasyDiff targets a strict 1-to-1 correspondence between the public
Python API path and the persisted data name: a saved `_category.field`
equals `object.category.field` in code. The **only** systematic
divergence is that a collection category is plural in the API
(`structure.atom_sites`) and singular in the file (`_atom_site`),
because the file names the per-row item — the universal STAR/CIF
convention.

Achieving 1-to-1 at v1.0.0 requires these **public-API renames** (they
are API changes, not only file-tag changes; official import aliases stay
available, report CIF keeps the official names, and pre-release EasyDiff
names are not preserved as legacy aliases):

| Code today                                        | Code at v1.0.0                            | EasyDiff                              |
| ------------------------------------------------- | ----------------------------------------- | ------------------------------------- |
| `atom_sites[*].label`                             | `atom_sites[*].id`                        | `_atom_site.id`                       |
| `atom_site_aniso[*].label`                        | `atom_site_aniso[*].id`                   | `_atom_site_aniso.id`                 |
| `aliases[*].label`                                | `aliases[*].id`                           | `_alias.id`                           |
| `experiment.linked_phases`                        | `experiment.linked_structures`            | `_linked_structure`                   |
| `experiment.linked_crystal`                       | `experiment.linked_structure`             | `_linked_structure`                   |
| linked item `id`                                  | linked item `structure_id`                | `_linked_structure.structure_id`      |
| `refln` (powder) `phase_id`                       | `refln` `structure_id`                    | `_refln.structure_id`                 |
| `preferred_orientation.phase_id`                  | `preferred_orientation.structure_id`      | `_preferred_orientation.structure_id` |
| `experiment.type`                                 | `experiment.experiment_type`              | `_experiment_type`                    |
| `project.info`                                    | `project.metadata`                        | `_metadata`                           |
| `structure.space_group.it_coordinate_system_code` | `structure.space_group.coord_system_code` | `_space_group.coord_system_code`      |

Plus the Abbreviation Policy renames (§Naming Policy), listed
per-parameter in the Per-Parameter Map: `bond_distance_incr`→`inc`,
`calib_d_to_tof_quad`/`recip`→`quadratic`/`reciprocal`,
`param_unique_name`→`parameter_unique_name`, `data.point_id`→`id`,
`fit_bounds_uncertainty_multiplier`→`bounds_uncertainty_multiplier`, and
background line-segment `x`/`y`→`position`/`intensity`.

### Python-Side Migration

The public-API renames above remove the old Python attribute names when
the migration lands. The project is still in beta, so there are no
transitional Python properties, no deprecation warnings, and no
dual-write public API. "Read alias" in this ADR means only that the
loader accepts old **file data names** through `import_names`; it does
not mean `atom_site.label`, `experiment.type`, `linked_phases`,
`param_unique_name`, or other renamed Python attributes remain usable.

The same rule applies to every public creation surface. `add()` and
`create()` keyword arguments use the v1.0.0 names in the table: for
example `atom_sites.add(id='Si', ...)`,
`background.add(position=..., intensity=...)`, and
`fit_parameters.add(parameter_unique_name=...)`. Implementation must
migrate tutorials and tests at those call sites and must make stale
keywords fail clearly at the public boundary rather than being silently
ignored by guarded assignment.

Documented exceptions where strict 1-to-1 is intentionally not pursued:

- **`_linked_structure` maps to two owner attributes** — the powder
  collection `linked_structures` and the single-crystal item
  `linked_structure`. They have different cardinality (collection vs
  single item) but identical fields, and an experiment is either powder
  or single crystal, so only one appears per file. This is one file
  category ↔ two Python attributes by design.
- **`analysis.software` is modelled as a role loop** (not an exception —
  it becomes 1-to-1 like the rest). The three roles (framework,
  calculator, minimizer) are persisted as a `_software` loop keyed by
  `id`, accessed in code as `software[role].{name,version,url}`,
  following the same singular-loop + `id` rules as every other
  collection. The role id is a closed value set and must be backed by a
  `(str, Enum)` such as `SoftwareRoleEnum`, not ad hoc strings. The
  save-time `timestamp` moves to `project.metadata`.

## Per-Parameter Map

A human-readable, one-row-per-parameter companion to the compact
inventory above. Shorthands: `structure` =
`project.structures['<name>']`, `experiment` =
`project.experiments['<name>']`, `analysis` = `project.analysis`,
`project` = the project facade. `['<id>']` marks a loop (collection)
row. In the **v1.0.0 API** column, `same` means the public name is
unchanged from today; an explicit path marks a rename. The **EasyDiff**
column is the persisted data name.

### Structure

| Current API                                       | v1.0.0 API                                | EasyDiff                         |
| ------------------------------------------------- | ----------------------------------------- | -------------------------------- |
| `structure.cell.length_a`                         | same                                      | `_cell.length_a`                 |
| `structure.cell.length_b`                         | same                                      | `_cell.length_b`                 |
| `structure.cell.length_c`                         | same                                      | `_cell.length_c`                 |
| `structure.cell.angle_alpha`                      | same                                      | `_cell.angle_alpha`              |
| `structure.cell.angle_beta`                       | same                                      | `_cell.angle_beta`               |
| `structure.cell.angle_gamma`                      | same                                      | `_cell.angle_gamma`              |
| `structure.space_group.name_h_m`                  | same                                      | `_space_group.name_h_m`          |
| `structure.space_group.it_coordinate_system_code` | `structure.space_group.coord_system_code` | `_space_group.coord_system_code` |
| `structure.atom_sites['<id>'].label`              | `structure.atom_sites['<id>'].id`         | `_atom_site.id`                  |
| `structure.atom_sites['<id>'].type_symbol`        | same                                      | `_atom_site.type_symbol`         |
| `structure.atom_sites['<id>'].fract_x`            | same                                      | `_atom_site.fract_x`             |
| `structure.atom_sites['<id>'].fract_y`            | same                                      | `_atom_site.fract_y`             |
| `structure.atom_sites['<id>'].fract_z`            | same                                      | `_atom_site.fract_z`             |
| `structure.atom_sites['<id>'].occupancy`          | same                                      | `_atom_site.occupancy`           |
| `structure.atom_sites['<id>'].wyckoff_letter`     | same                                      | `_atom_site.wyckoff_letter`      |
| `structure.atom_sites['<id>'].multiplicity`       | same                                      | `_atom_site.multiplicity`        |
| `structure.atom_sites['<id>'].adp_iso`            | same                                      | `_atom_site.adp_iso`             |
| `structure.atom_sites['<id>'].adp_type`           | same                                      | `_atom_site.adp_type`            |
| `structure.atom_site_aniso['<id>'].label`         | `structure.atom_site_aniso['<id>'].id`    | `_atom_site_aniso.id`            |
| `structure.atom_site_aniso['<id>'].adp_11`        | same                                      | `_atom_site_aniso.adp_11`        |
| `structure.atom_site_aniso['<id>'].adp_22`        | same                                      | `_atom_site_aniso.adp_22`        |
| `structure.atom_site_aniso['<id>'].adp_33`        | same                                      | `_atom_site_aniso.adp_33`        |
| `structure.atom_site_aniso['<id>'].adp_12`        | same                                      | `_atom_site_aniso.adp_12`        |
| `structure.atom_site_aniso['<id>'].adp_13`        | same                                      | `_atom_site_aniso.adp_13`        |
| `structure.atom_site_aniso['<id>'].adp_23`        | same                                      | `_atom_site_aniso.adp_23`        |
| `structure.geom.min_bond_distance_cutoff`         | same                                      | `_geom.min_bond_distance_cutoff` |
| `structure.geom.bond_distance_incr`               | `structure.geom.bond_distance_inc`        | `_geom.bond_distance_inc`        |
| `structure.space_group_wyckoff['<id>'].*`         | same                                      | — (derived; not persisted)       |

### Experiment

| Current API                                           | v1.0.0 API                                          | EasyDiff                                    |
| ----------------------------------------------------- | --------------------------------------------------- | ------------------------------------------- |
| `experiment.type.sample_form`                         | `experiment.experiment_type.sample_form`            | `_experiment_type.sample_form`              |
| `experiment.type.beam_mode`                           | `experiment.experiment_type.beam_mode`              | `_experiment_type.beam_mode`                |
| `experiment.type.radiation_probe`                     | `experiment.experiment_type.radiation_probe`        | `_experiment_type.radiation_probe`          |
| `experiment.type.scattering_type`                     | `experiment.experiment_type.scattering_type`        | `_experiment_type.scattering_type`          |
| `experiment.calculator.type`                          | same                                                | `_calculator.type`                          |
| `experiment.background.type`                          | same                                                | `_background.type`                          |
| `experiment.background['<id>'].x`                     | `experiment.background['<id>'].position`            | `_background.position`                      |
| `experiment.background['<id>'].y`                     | `experiment.background['<id>'].intensity`           | `_background.intensity`                     |
| `experiment.background['<id>'].order`                 | same                                                | `_background.order`                         |
| `experiment.background['<id>'].coef`                  | same                                                | `_background.coef`                          |
| `experiment.instrument.setup_wavelength`              | same                                                | `_instrument.setup_wavelength`              |
| `experiment.instrument.calib_twotheta_offset`         | same                                                | `_instrument.calib_twotheta_offset`         |
| `experiment.instrument.calib_sample_displacement`     | same                                                | `_instrument.calib_sample_displacement`     |
| `experiment.instrument.calib_sample_transparency`     | same                                                | `_instrument.calib_sample_transparency`     |
| `experiment.instrument.setup_twotheta_bank`           | same                                                | `_instrument.setup_twotheta_bank`           |
| `experiment.instrument.calib_d_to_tof_offset`         | same                                                | `_instrument.calib_d_to_tof_offset`         |
| `experiment.instrument.calib_d_to_tof_linear`         | same                                                | `_instrument.calib_d_to_tof_linear`         |
| `experiment.instrument.calib_d_to_tof_quad`           | `experiment.instrument.calib_d_to_tof_quadratic`    | `_instrument.calib_d_to_tof_quadratic`      |
| `experiment.instrument.calib_d_to_tof_recip`          | `experiment.instrument.calib_d_to_tof_reciprocal`   | `_instrument.calib_d_to_tof_reciprocal`     |
| `experiment.peak.type`                                | same                                                | `_peak.type`                                |
| `experiment.peak.broad_gauss_u`                       | same                                                | `_peak.broad_gauss_u`                       |
| `experiment.peak.broad_gauss_v`                       | same                                                | `_peak.broad_gauss_v`                       |
| `experiment.peak.broad_gauss_w`                       | same                                                | `_peak.broad_gauss_w`                       |
| `experiment.peak.broad_lorentz_x`                     | same                                                | `_peak.broad_lorentz_x`                     |
| `experiment.peak.broad_lorentz_y`                     | same                                                | `_peak.broad_lorentz_y`                     |
| `experiment.peak.asym_empir_1`                        | same                                                | `_peak.asym_empir_1`                        |
| `experiment.peak.asym_empir_2`                        | same                                                | `_peak.asym_empir_2`                        |
| `experiment.peak.asym_empir_3`                        | same                                                | `_peak.asym_empir_3`                        |
| `experiment.peak.asym_empir_4`                        | same                                                | `_peak.asym_empir_4`                        |
| `experiment.peak.asym_fcj_1`                          | same                                                | `_peak.asym_fcj_1`                          |
| `experiment.peak.asym_fcj_2`                          | same                                                | `_peak.asym_fcj_2`                          |
| `experiment.peak.broad_gauss_sigma_0`                 | same                                                | `_peak.broad_gauss_sigma_0`                 |
| `experiment.peak.broad_gauss_sigma_1`                 | same                                                | `_peak.broad_gauss_sigma_1`                 |
| `experiment.peak.broad_gauss_sigma_2`                 | same                                                | `_peak.broad_gauss_sigma_2`                 |
| `experiment.peak.broad_lorentz_gamma_0`               | same                                                | `_peak.broad_lorentz_gamma_0`               |
| `experiment.peak.broad_lorentz_gamma_1`               | same                                                | `_peak.broad_lorentz_gamma_1`               |
| `experiment.peak.broad_lorentz_gamma_2`               | same                                                | `_peak.broad_lorentz_gamma_2`               |
| `experiment.peak.exp_rise_alpha_0`                    | same                                                | `_peak.exp_rise_alpha_0`                    |
| `experiment.peak.exp_rise_alpha_1`                    | same                                                | `_peak.exp_rise_alpha_1`                    |
| `experiment.peak.exp_decay_beta_0`                    | same                                                | `_peak.exp_decay_beta_0`                    |
| `experiment.peak.exp_decay_beta_1`                    | same                                                | `_peak.exp_decay_beta_1`                    |
| `experiment.peak.dexp_rise_alpha_1`                   | same                                                | `_peak.dexp_rise_alpha_1`                   |
| `experiment.peak.dexp_rise_alpha_2`                   | same                                                | `_peak.dexp_rise_alpha_2`                   |
| `experiment.peak.dexp_decay_beta_00`                  | same                                                | `_peak.dexp_decay_beta_00`                  |
| `experiment.peak.dexp_decay_beta_01`                  | same                                                | `_peak.dexp_decay_beta_01`                  |
| `experiment.peak.dexp_decay_beta_10`                  | same                                                | `_peak.dexp_decay_beta_10`                  |
| `experiment.peak.dexp_switch_r_01`                    | same                                                | `_peak.dexp_switch_r_01`                    |
| `experiment.peak.dexp_switch_r_02`                    | same                                                | `_peak.dexp_switch_r_02`                    |
| `experiment.peak.dexp_switch_r_03`                    | same                                                | `_peak.dexp_switch_r_03`                    |
| `experiment.peak.damp_q`                              | same                                                | `_peak.damp_q`                              |
| `experiment.peak.broad_q`                             | same                                                | `_peak.broad_q`                             |
| `experiment.peak.cutoff_q`                            | same                                                | `_peak.cutoff_q`                            |
| `experiment.peak.sharp_delta_1`                       | same                                                | `_peak.sharp_delta_1`                       |
| `experiment.peak.sharp_delta_2`                       | same                                                | `_peak.sharp_delta_2`                       |
| `experiment.peak.damp_particle_diameter`              | same                                                | `_peak.damp_particle_diameter`              |
| `experiment.extinction.type`                          | same                                                | `_extinction.type`                          |
| `experiment.extinction.model`                         | same                                                | `_extinction.model`                         |
| `experiment.extinction.mosaicity`                     | same                                                | `_extinction.mosaicity`                     |
| `experiment.extinction.radius`                        | same                                                | `_extinction.radius`                        |
| `experiment.diffrn.ambient_temperature`               | same                                                | `_diffrn.ambient_temperature`               |
| `experiment.diffrn.ambient_pressure`                  | same                                                | `_diffrn.ambient_pressure`                  |
| `experiment.diffrn.ambient_magnetic_field`            | same                                                | `_diffrn.ambient_magnetic_field`            |
| `experiment.diffrn.ambient_electric_field`            | same                                                | `_diffrn.ambient_electric_field`            |
| `experiment.data_range.two_theta_min`                 | same                                                | `_data_range.two_theta_min`                 |
| `experiment.data_range.two_theta_max`                 | same                                                | `_data_range.two_theta_max`                 |
| `experiment.data_range.two_theta_inc`                 | same                                                | `_data_range.two_theta_inc`                 |
| `experiment.data_range.sin_theta_over_lambda_min`     | same                                                | `_data_range.sin_theta_over_lambda_min`     |
| `experiment.data_range.sin_theta_over_lambda_max`     | same                                                | `_data_range.sin_theta_over_lambda_max`     |
| `experiment.data_range.time_of_flight_min`            | same                                                | `_data_range.time_of_flight_min`            |
| `experiment.data_range.time_of_flight_max`            | same                                                | `_data_range.time_of_flight_max`            |
| `experiment.data_range.time_of_flight_inc`            | same                                                | `_data_range.time_of_flight_inc`            |
| `experiment.data['<id>'].point_id`                    | `experiment.data['<id>'].id`                        | `_data.id`                                  |
| `experiment.data['<id>'].d_spacing`                   | same                                                | `_data.d_spacing`                           |
| `experiment.data['<id>'].intensity_meas`              | same                                                | `_data.intensity_meas`                      |
| `experiment.data['<id>'].intensity_meas_su`           | same                                                | `_data.intensity_meas_su`                   |
| `experiment.data['<id>'].intensity_calc`              | same                                                | `_data.intensity_calc`                      |
| `experiment.data['<id>'].intensity_bkg`               | same                                                | `_data.intensity_bkg`                       |
| `experiment.data['<id>'].calc_status`                 | same                                                | `_data.calc_status`                         |
| `experiment.data['<id>'].two_theta`                   | same                                                | `_data.two_theta`                           |
| `experiment.data['<id>'].time_of_flight`              | same                                                | `_data.time_of_flight`                      |
| `experiment.data['<id>'].r` (PDF)                     | same                                                | `_data.r`                                   |
| `experiment.data['<id>'].g_r_meas` (PDF)              | same                                                | `_data.g_r_meas`                            |
| `experiment.data['<id>'].g_r_meas_su` (PDF)           | same                                                | `_data.g_r_meas_su`                         |
| `experiment.data['<id>'].g_r_calc` (PDF)              | same                                                | `_data.g_r_calc`                            |
| `experiment.refln['<id>'].id`                         | same                                                | `_refln.id`                                 |
| `experiment.refln['<id>'].d_spacing`                  | same                                                | `_refln.d_spacing`                          |
| `experiment.refln['<id>'].sin_theta_over_lambda`      | same                                                | `_refln.sin_theta_over_lambda`              |
| `experiment.refln['<id>'].index_h`                    | same                                                | `_refln.index_h`                            |
| `experiment.refln['<id>'].index_k`                    | same                                                | `_refln.index_k`                            |
| `experiment.refln['<id>'].index_l`                    | same                                                | `_refln.index_l`                            |
| `experiment.refln['<id>'].phase_id` (powder)          | `experiment.refln['<id>'].structure_id`             | `_refln.structure_id`                       |
| `experiment.refln['<id>'].f_calc`                     | same                                                | `_refln.f_calc`                             |
| `experiment.refln['<id>'].f_squared_calc`             | same                                                | `_refln.f_squared_calc`                     |
| `experiment.refln['<id>'].two_theta`                  | same                                                | `_refln.two_theta`                          |
| `experiment.refln['<id>'].time_of_flight`             | same                                                | `_refln.time_of_flight`                     |
| `experiment.refln['<id>'].intensity_meas` (SC)        | same                                                | `_refln.intensity_meas`                     |
| `experiment.refln['<id>'].intensity_meas_su` (SC)     | same                                                | `_refln.intensity_meas_su`                  |
| `experiment.refln['<id>'].intensity_calc` (SC)        | same                                                | `_refln.intensity_calc`                     |
| `experiment.refln['<id>'].wavelength` (SC)            | same                                                | `_refln.wavelength`                         |
| `experiment.excluded_regions['<id>'].id`              | same                                                | `_excluded_region.id`                       |
| `experiment.excluded_regions['<id>'].start`           | same                                                | `_excluded_region.start`                    |
| `experiment.excluded_regions['<id>'].end`             | same                                                | `_excluded_region.end`                      |
| `experiment.linked_phases['<id>'].id`                 | `experiment.linked_structures['<id>'].structure_id` | `_linked_structure.structure_id`            |
| `experiment.linked_phases['<id>'].scale`              | `experiment.linked_structures['<id>'].scale`        | `_linked_structure.scale`                   |
| `experiment.linked_crystal.id`                        | `experiment.linked_structure.structure_id`          | `_linked_structure.structure_id`            |
| `experiment.linked_crystal.scale`                     | `experiment.linked_structure.scale`                 | `_linked_structure.scale`                   |
| `experiment.preferred_orientation.phase_id`           | `experiment.preferred_orientation.structure_id`     | `_preferred_orientation.structure_id`       |
| `experiment.preferred_orientation.march_r`            | same                                                | `_preferred_orientation.march_r`            |
| `experiment.preferred_orientation.index_h`            | same                                                | `_preferred_orientation.index_h`            |
| `experiment.preferred_orientation.index_k`            | same                                                | `_preferred_orientation.index_k`            |
| `experiment.preferred_orientation.index_l`            | same                                                | `_preferred_orientation.index_l`            |
| `experiment.preferred_orientation.march_random_fract` | same                                                | `_preferred_orientation.march_random_fract` |

### Analysis

| Current API                                                            | v1.0.0 API                                                      | EasyDiff                                              |
| ---------------------------------------------------------------------- | --------------------------------------------------------------- | ----------------------------------------------------- |
| `analysis.aliases['<id>'].label`                                       | `analysis.aliases['<id>'].id`                                   | `_alias.id`                                           |
| `analysis.aliases['<id>'].param_unique_name`                           | `analysis.aliases['<id>'].parameter_unique_name`                | `_alias.parameter_unique_name`                        |
| `analysis.constraints['<id>'].id`                                      | same                                                            | `_constraint.id`                                      |
| `analysis.constraints['<id>'].expression`                              | same                                                            | `_constraint.expression`                              |
| `analysis.fit_parameters['<id>'].param_unique_name`                    | `analysis.fit_parameters['<id>'].parameter_unique_name`         | `_fit_parameter.parameter_unique_name`                |
| `analysis.fit_parameters['<id>'].fit_min`                              | same                                                            | `_fit_parameter.fit_min`                              |
| `analysis.fit_parameters['<id>'].fit_max`                              | same                                                            | `_fit_parameter.fit_max`                              |
| `analysis.fit_parameters['<id>'].fit_bounds_uncertainty_multiplier`    | `analysis.fit_parameters['<id>'].bounds_uncertainty_multiplier` | `_fit_parameter.bounds_uncertainty_multiplier`        |
| `analysis.fit_parameters['<id>'].start_value`                          | same                                                            | `_fit_parameter.start_value`                          |
| `analysis.fit_parameters['<id>'].start_uncertainty`                    | same                                                            | `_fit_parameter.start_uncertainty`                    |
| `analysis.fit_parameters['<id>'].posterior_best_sample_value`          | same                                                            | `_fit_parameter.posterior_best_sample_value`          |
| `analysis.fit_parameters['<id>'].posterior_median`                     | same                                                            | `_fit_parameter.posterior_median`                     |
| `analysis.fit_parameters['<id>'].posterior_uncertainty`                | same                                                            | `_fit_parameter.posterior_uncertainty`                |
| `analysis.fit_parameters['<id>'].posterior_interval_68_low`            | same                                                            | `_fit_parameter.posterior_interval_68_low`            |
| `analysis.fit_parameters['<id>'].posterior_interval_68_high`           | same                                                            | `_fit_parameter.posterior_interval_68_high`           |
| `analysis.fit_parameters['<id>'].posterior_interval_95_low`            | same                                                            | `_fit_parameter.posterior_interval_95_low`            |
| `analysis.fit_parameters['<id>'].posterior_interval_95_high`           | same                                                            | `_fit_parameter.posterior_interval_95_high`           |
| `analysis.fit_parameters['<id>'].posterior_gelman_rubin`               | same                                                            | `_fit_parameter.posterior_gelman_rubin`               |
| `analysis.fit_parameters['<id>'].posterior_effective_sample_size_bulk` | same                                                            | `_fit_parameter.posterior_effective_sample_size_bulk` |
| `analysis.fit_parameter_correlations['<id>'].id`                       | same                                                            | `_fit_parameter_correlation.id`                       |
| `analysis.fit_parameter_correlations['<id>'].source_kind`              | same                                                            | `_fit_parameter_correlation.source_kind`              |
| `analysis.fit_parameter_correlations['<id>'].param_unique_name_i`      | `…parameter_unique_name_i`                                      | `_fit_parameter_correlation.parameter_unique_name_i`  |
| `analysis.fit_parameter_correlations['<id>'].param_unique_name_j`      | `…parameter_unique_name_j`                                      | `_fit_parameter_correlation.parameter_unique_name_j`  |
| `analysis.fit_parameter_correlations['<id>'].correlation`              | same                                                            | `_fit_parameter_correlation.correlation`              |
| `analysis.fit_result.result_kind`                                      | same                                                            | `_fit_result.result_kind`                             |
| `analysis.fit_result.success`                                          | same                                                            | `_fit_result.success`                                 |
| `analysis.fit_result.message`                                          | same                                                            | `_fit_result.message`                                 |
| `analysis.fit_result.iterations`                                       | same                                                            | `_fit_result.iterations`                              |
| `analysis.fit_result.fitting_time`                                     | same                                                            | `_fit_result.fitting_time`                            |
| `analysis.fit_result.reduced_chi_square`                               | same                                                            | `_fit_result.reduced_chi_square`                      |
| `analysis.fit_result.objective_name`                                   | same                                                            | `_fit_result.objective_name`                          |
| `analysis.fit_result.objective_value`                                  | same                                                            | `_fit_result.objective_value`                         |
| `analysis.fit_result.n_data_points`                                    | same                                                            | `_fit_result.n_data_points`                           |
| `analysis.fit_result.n_parameters`                                     | same                                                            | `_fit_result.n_parameters`                            |
| `analysis.fit_result.n_free_parameters`                                | same                                                            | `_fit_result.n_free_parameters`                       |
| `analysis.fit_result.degrees_of_freedom`                               | same                                                            | `_fit_result.degrees_of_freedom`                      |
| `analysis.fit_result.covariance_available`                             | same                                                            | `_fit_result.covariance_available`                    |
| `analysis.fit_result.correlation_available`                            | same                                                            | `_fit_result.correlation_available`                   |
| `analysis.fit_result.exit_reason`                                      | same                                                            | `_fit_result.exit_reason`                             |
| `analysis.fit_result.r_factor_all`                                     | same                                                            | `_fit_result.r_factor_all`                            |
| `analysis.fit_result.wr_factor_all`                                    | same                                                            | `_fit_result.wr_factor_all`                           |
| `analysis.fit_result.r_factor_gt`                                      | same                                                            | `_fit_result.r_factor_gt`                             |
| `analysis.fit_result.wr_factor_gt`                                     | same                                                            | `_fit_result.wr_factor_gt`                            |
| `analysis.fit_result.prof_r_factor`                                    | same                                                            | `_fit_result.prof_r_factor`                           |
| `analysis.fit_result.prof_wr_factor`                                   | same                                                            | `_fit_result.prof_wr_factor`                          |
| `analysis.fit_result.prof_wr_expected`                                 | same                                                            | `_fit_result.prof_wr_expected`                        |
| `analysis.fit_result.profile_function`                                 | same                                                            | `_fit_result.profile_function`                        |
| `analysis.fit_result.background_function`                              | same                                                            | `_fit_result.background_function`                     |
| `analysis.fit_result.number_restraints`                                | same                                                            | `_fit_result.number_restraints`                       |
| `analysis.fit_result.number_constraints`                               | same                                                            | `_fit_result.number_constraints`                      |
| `analysis.fit_result.shift_over_su_max`                                | same                                                            | `_fit_result.shift_over_su_max`                       |
| `analysis.fit_result.shift_over_su_mean`                               | same                                                            | `_fit_result.shift_over_su_mean`                      |
| `analysis.fit_result.threshold_expression`                             | same                                                            | `_fit_result.threshold_expression`                    |
| `analysis.fit_result.number_reflns_total`                              | same                                                            | `_fit_result.number_reflns_total`                     |
| `analysis.fit_result.number_reflns_gt`                                 | same                                                            | `_fit_result.number_reflns_gt`                        |
| `analysis.fit_result.point_estimate_name`                              | same                                                            | `_fit_result.point_estimate_name`                     |
| `analysis.fit_result.sampler_completed`                                | same                                                            | `_fit_result.sampler_completed`                       |
| `analysis.fit_result.credible_interval_inner`                          | same                                                            | `_fit_result.credible_interval_inner`                 |
| `analysis.fit_result.credible_interval_outer`                          | same                                                            | `_fit_result.credible_interval_outer`                 |
| `analysis.fit_result.acceptance_rate_mean`                             | same                                                            | `_fit_result.acceptance_rate_mean`                    |
| `analysis.fit_result.resolved_random_seed`                             | same                                                            | `_fit_result.resolved_random_seed`                    |
| `analysis.fit_result.gelman_rubin_max`                                 | same                                                            | `_fit_result.gelman_rubin_max`                        |
| `analysis.fit_result.effective_sample_size_min`                        | same                                                            | `_fit_result.effective_sample_size_min`               |
| `analysis.fit_result.best_log_posterior`                               | same                                                            | `_fit_result.best_log_posterior`                      |
| `analysis.fitting_mode.type`                                           | same                                                            | `_fitting_mode.type`                                  |
| `analysis.minimizer.type`                                              | same                                                            | `_minimizer.type`                                     |
| `analysis.minimizer.max_iterations`                                    | same                                                            | `_minimizer.max_iterations`                           |
| `analysis.minimizer.sampling_steps`                                    | same                                                            | `_minimizer.sampling_steps`                           |
| `analysis.minimizer.burn_in_steps`                                     | same                                                            | `_minimizer.burn_in_steps`                            |
| `analysis.minimizer.thinning_interval`                                 | same                                                            | `_minimizer.thinning_interval`                        |
| `analysis.minimizer.population_size`                                   | same                                                            | `_minimizer.population_size`                          |
| `analysis.minimizer.parallel_workers`                                  | same                                                            | `_minimizer.parallel_workers`                         |
| `analysis.minimizer.initialization_method`                             | same                                                            | `_minimizer.initialization_method`                    |
| `analysis.minimizer.random_seed`                                       | same                                                            | `_minimizer.random_seed`                              |
| `analysis.minimizer.proposal_moves`                                    | same                                                            | `_minimizer.proposal_moves`                           |
| `analysis.joint_fit['<id>'].experiment_id`                             | same                                                            | `_joint_fit.experiment_id`                            |
| `analysis.joint_fit['<id>'].weight`                                    | same                                                            | `_joint_fit.weight`                                   |
| `analysis.sequential_fit.data_dir`                                     | same                                                            | `_sequential_fit.data_dir`                            |
| `analysis.sequential_fit.file_pattern`                                 | same                                                            | `_sequential_fit.file_pattern`                        |
| `analysis.sequential_fit.max_workers`                                  | same                                                            | `_sequential_fit.max_workers`                         |
| `analysis.sequential_fit.chunk_size`                                   | same                                                            | `_sequential_fit.chunk_size`                          |
| `analysis.sequential_fit.reverse`                                      | same                                                            | `_sequential_fit.reverse`                             |
| `analysis.sequential_fit_extract['<id>'].id`                           | same                                                            | `_sequential_fit_extract.id`                          |
| `analysis.sequential_fit_extract['<id>'].target`                       | same                                                            | `_sequential_fit_extract.target`                      |
| `analysis.sequential_fit_extract['<id>'].pattern`                      | same                                                            | `_sequential_fit_extract.pattern`                     |
| `analysis.sequential_fit_extract['<id>'].required`                     | same                                                            | `_sequential_fit_extract.required`                    |
| `analysis.software.framework.name`                                     | `analysis.software['framework'].name`                           | `_software.name` (`id`=framework)                     |
| `analysis.software.framework.version`                                  | `analysis.software['framework'].version`                        | `_software.version`                                   |
| `analysis.software.framework.url`                                      | `analysis.software['framework'].url`                            | `_software.url`                                       |
| `analysis.software.calculator.{name,version,url}`                      | `analysis.software['calculator'].{name,version,url}`            | `_software.{name,version,url}` (`id`=calculator)      |
| `analysis.software.minimizer.{name,version,url}`                       | `analysis.software['minimizer'].{name,version,url}`             | `_software.{name,version,url}` (`id`=minimizer)       |
| `analysis.software.timestamp`                                          | `project.metadata.timestamp`                                    | `_metadata.timestamp`                                 |

### Project

| Current API                               | v1.0.0 API                       | EasyDiff                           |
| ----------------------------------------- | -------------------------------- | ---------------------------------- |
| `project.info.name`                       | `project.metadata.name`          | `_metadata.name`                   |
| `project.info.title`                      | `project.metadata.title`         | `_metadata.title`                  |
| `project.info.description`                | `project.metadata.description`   | `_metadata.description`            |
| `project.info.created`                    | `project.metadata.created`       | `_metadata.created`                |
| `project.info.last_modified`              | `project.metadata.last_modified` | `_metadata.last_modified`          |
| `analysis.software.timestamp`             | `project.metadata.timestamp`     | `_metadata.timestamp`              |
| `project.rendering_plot.type`             | same                             | `_rendering_plot.type`             |
| `project.rendering_structure.type`        | same                             | `_rendering_structure.type`        |
| `project.rendering_table.type`            | same                             | `_rendering_table.type`            |
| `project.report.cif`                      | same                             | `_report.cif`                      |
| `project.report.html`                     | same                             | `_report.html`                     |
| `project.report.tex`                      | same                             | `_report.tex`                      |
| `project.report.pdf`                      | same                             | `_report.pdf`                      |
| `project.report.html_offline`             | same                             | `_report.html_offline`             |
| `project.structure_style.atom_view`       | same                             | `_structure_style.atom_view`       |
| `project.structure_style.color_scheme`    | same                             | `_structure_style.color_scheme`    |
| `project.structure_style.adp_probability` | same                             | `_structure_style.adp_probability` |
| `project.structure_style.atom_scale`      | same                             | `_structure_style.atom_scale`      |
| `project.structure_view.show_labels`      | same                             | `_structure_view.show_labels`      |
| `project.structure_view.show_moments`     | same                             | `_structure_view.show_moments`     |
| `project.structure_view.range_a_min`      | same                             | `_structure_view.range_a_min`      |
| `project.structure_view.range_a_max`      | same                             | `_structure_view.range_a_max`      |
| `project.structure_view.range_b_min`      | same                             | `_structure_view.range_b_min`      |
| `project.structure_view.range_b_max`      | same                             | `_structure_view.range_b_max`      |
| `project.structure_view.range_c_min`      | same                             | `_structure_view.range_c_min`      |
| `project.structure_view.range_c_max`      | same                             | `_structure_view.range_c_max`      |
| `project.verbosity.fit`                   | same                             | `_verbosity.fit`                   |

## Documentation: Parameter-Reference Pages

The user-guide parameter reference must be reworked to reflect the
EasyDiff split between the friendly project format and the strict report
CIF. Two documentation surfaces are in scope:

- The index page
  [`docs/docs/user-guide/parameters.md`](../../../docs/user-guide/parameters.md),
  which today renders two-tab content-tab tables
  (`=== "How to access in the code"` and
  `=== "CIF name for serialization"`).
- The per-category detail pages under `docs/docs/user-guide/parameters/`
  (for example `atom_site.md`, `cell.md`, `peak.md`, `background.md`,
  `instrument.md`, `space_group.md`, `expt_type.md`, `linked_phases.md`,
  `pref_orient.md`), whose section titles are currently the CIF data
  names linked directly to the IUCr definition.

The rework keeps the existing MkDocs Material machinery so the pages
still build to static HTML: `pymdownx.tabbed` content tabs, `attr_list`
for the `:material-*:` icons and the `{:.label-cif}` /
`{:.label-experiment}` chips, reference-style links, and the
`<!-- prettier-ignore-start/-end -->` fences around the link
definitions. Only the table content and the per-parameter titles change,
not the rendering mechanism.

### Three-Tab Mapping Tables

Each mapping table in `parameters.md` gains a third tab. The first two
columns (Category, Parameter) stay identical across all three tabs; only
the right-hand column(s) differ:

1. **"How to access in the code"** (kept) — the public Python access
   path in its **v1.0.0** form, with this ADR's renames applied:
   `atom_sites['ID'].id` (not `.label`), `linked_structures['ID'].scale`
   (not `linked_phases`), `experiment_type.beam_mode` (not `expt_type`),
   `instrument.calib_d_to_tof_quadratic` (not `_quad`), and so on.
2. **"Keys in EasyDiff"** (new) — the persisted `.easydiff` data name
   taken from this ADR's Parameter Inventory and Per-Parameter Map, for
   example `_atom_site.id`, `_atom_site.adp_iso`, `_cell.length_a`,
   `_instrument.setup_wavelength`, `_peak.broad_gauss_sigma_0`,
   `_background.position`. This tab has **no** "CIF dictionary" column:
   EasyDiff is an EasyDiffraction-owned schema, and the `.easydiff`
   suffix plus the `_easydiff.schema_*` marker already identify the
   dialect.
3. **"Keys in CIF"** (new; replaces the old "CIF name for
   serialization") — the strict name emitted by
   `project.report.save_cif()` into `reports/<project>.cif`, with a "CIF
   dictionary" column:
   - where an official IUCr/pdCIF name exists, list that name and tag it
     `[coreCIF]` or `[pdCIF]` (for example `_atom_site.B_iso_or_equiv` →
     coreCIF, `_pd_phase_block.scale` → pdCIF);
   - where no official name exists, list the EasyDiffraction extension
     name and tag it `[easydiffCIF]` (for example the parametric
     `_peak.*` profile coefficients and
     `_pref_orient.march_random_fract`). Only parameters the report
     writer actually emits appear in this tab; derived/never-persisted
     entries (for example `space_group_wyckoff`) are omitted.

The crucial change from today is the separation of concerns: the
**project-save** names now live in tab 2 (EasyDiff), and the
**official-CIF** names live in tab 3, explicitly labelled as the
_report_ boundary. This matches the ADR's thesis that project files are
EasyDiff and only `reports/<project>.cif` is strict IUCr. The current
page conflates the two by labelling the old project write tags
(`_pd_background.line_segment_X`, `_instr.wavelength`,
`_atom_site.B_iso_or_equiv`) as "CIF name for serialization".

Worked example for the `cell` category, in the exact content-tab syntax
to reproduce (note the four-space body indent each tab requires):

```text
=== "How to access in the code"

    | Category                             | Parameter                         | How to access in the code |
    |--------------------------------------|-----------------------------------|---------------------------|
    | :material-cube-outline: [cell][cell] | :material-ruler: [length_a][cell] | cell.length_a             |

=== "Keys in EasyDiff"

    | Category                             | Parameter                         | EasyDiff key      |
    |--------------------------------------|-----------------------------------|-----------------|
    | :material-cube-outline: [cell][cell] | :material-ruler: [length_a][cell] | \_cell.length_a |

=== "Keys in CIF"

    | Category                             | Parameter                         | CIF key         | CIF dictionary            |
    |--------------------------------------|-----------------------------------|-----------------|---------------------------|
    | :material-cube-outline: [cell][cell] | :material-ruler: [length_a][cell] | \_cell.length_a | [coreCIF][1]{:.label-cif} |
```

### Icons for Every Category and Parameter

Every category row and every parameter row must carry a `:material-*:`
icon. Fill in icons for any rows that lack one today, and reuse the same
icon for the same concept across the three tabs (the Category and
Parameter columns are shared, so each row's icon is chosen once). New
EasyDiff categories/parameters introduced by the renames — for example
`experiment_type`, `linked_structure(s)`, `preferred_orientation`,
`metadata` — get icons consistent with their nearest existing sibling.

### Tables Must Track the Code

The access paths (tab 1) and the EasyDiff keys (tab 2) must equal the
implemented v1.0.0 API and this ADR's Parameter Inventory exactly. The
same generated `CifHandler` inventory used as the migration audit
(Migration Sketch step 4) is the audit source for these hand-maintained
tables: implementation must compare the generated inventory with the
documentation rows before completing the migration, and any mismatch is
a migration blocker. Automatic generation of the docs tables or detail
pages is out of scope for this ADR and may be proposed separately.
Renamed names appear only in their post-migration form; pre-EasyDiff
names survive only as loader read aliases, never in the docs.

### Per-Parameter Detail Pages Own EasyDiff Names and Descriptions

The detail pages become EasyDiffraction-owned:

- **Page and section names use EasyDiff, not CIF.** Each section title
  is the EasyDiff data name — `## _atom_site.id`,
  `## _atom_site.adp_iso`, `## _instrument.setup_wavelength` — and the
  body is EasyDiffraction's own description of that parameter, not a
  verbatim copy of the IUCr definition. Pages currently named for CIF
  categories (`_exptl_crystal.md`, `_pd_calib.md`,
  `_diffrn_radiation*.md`, `_extinction.md`) and for soon-to-be-renamed
  owners (`linked_phases.md` → `linked_structure.md`, `pref_orient.md` →
  `preferred_orientation.md`, `expt_type.md` → `experiment_type.md`) are
  renamed to their EasyDiff category and have their reference links
  updated.
- **Every category and parameter in the tables links to its detail
  section.** Add the pages/anchors that are missing today and update the
  existing reference-link definitions to the EasyDiff names. Inter-page
  cross-references (for example `_atom_site.fract` pointing at
  `_cell_length`) move to the EasyDiff names as well.

### Versioned Parameter Documentation URLs

Every persisted descriptor/parameter must expose a read-only `url`
attribute that points to the online documentation page for that specific
parameter. This URL is display metadata only: it is not written into
EasyDiff, and loaders do not trust persisted URLs from project files.

The simplest long-term rule is to derive URLs from the EasyDiff data
name, not to hand-maintain a separate absolute URL on every descriptor.
The implementation should add a small documentation-url resolver that:

- uses the same installed-version resolution already used for tutorial
  downloads: released packages resolve to their public version folder,
  development/local builds resolve to `dev`;
- uses the versioned documentation base published by `mike`, for example
  `https://easyscience.github.io/diffraction-lib/{version}/`;
- maps an EasyDiff name to the parameter-reference route, for example
  `_cell.length_a` ->
  `user-guide/parameters/structure/cell/#cell-length-a`;
- falls back to a descriptor-specific override only for rare cases where
  a page or anchor cannot be derived from the EasyDiff name.

The shared resolver should be the only code that knows the absolute site
base and version folder. `CifHandler.project_name` (introduced by
Migration Sketch step 1) is the source value for ordinary descriptors;
descriptor classes expose `param.url` by asking the resolver to build
the URL from that project name. This keeps old installed versions linked
to the documentation version they were tested against, while future docs
reorganizations require changing one resolver or adding redirects rather
than editing every parameter declaration.

Parameter-reference detail pages must publish stable explicit anchors
derived by the same helper used by the resolver. Do not rely on MkDocs'
implicit heading slug rules as the contract. A docs verification check
must compare the generated descriptor inventory with the parameter docs
and fail if any persisted descriptor lacks a resolvable page/anchor.

Runtime display surfaces must consume the descriptor `url` instead of
hard-coding links. In notebooks, parameter tables such as
`project.display.parameters.all()` and fittable/free-parameter tables
should link the parameter label to `param.url`. The GUI/application
should use the same attribute for help links, tooltips, or details
panels.

Static MkDocs parameter tables remain hand-maintained. Their "How to
access in the code" tab should link parameter labels to the stable
relative anchors owned by the same documentation page, not to runtime
`param.url`. The generated inventory/docs check verifies that these
static anchors match the resolver's derived page/anchor contract.

### IUCr Links Become an Icon, Not the Title

Today the link to the official IUCr definition is placed on the
section-title text itself (`## [\_atom_site.label](IUCr URL)`) and on a
prose "see the IUCr page" sentence. Under EasyDiff the title is the
plain EasyDiff name, and an explicit external-resource icon follows it,
linking to the official IUCr description **only where one exists**:

```text
## _atom_site.adp_iso [:material-open-in-new:](https://www.iucr.org/__data/iucr/cifdic_html/3/CORE_DIC/Iatom_site.B_iso_or_equiv.html "IUCr definition")
```

The icon makes "this opens an external IUCr page" unambiguous, and its
absence makes EasyDiffraction-owned parameters (no official IUCr
definition — most `_peak.*`, `_pref_orient.march_random_fract`, and the
like) equally clear at a glance. The same icon convention replaces the
category-level "IUCr page" prose link. `:material-open-in-new:` renders
through the existing `pymdownx.emoji` (Material) configuration, so no
new extension is required.

## Migration Sketch

1. Introduce explicit handler names (`project_name`, `import_names`,
   `iucr_name`) while keeping current behavior.
2. Teach save/load helpers to require `.easydiff` project files and to
   reject legacy-only beta `.cif` project layouts with a clear migration
   error.
3. Add schema-marker validation and selector/body consistency checks to
   the EasyDiff load path.
4. Generate an implementation audit from all `CifHandler`-declared
   descriptors and compare it with the inventory in this ADR before
   changing write tags.
5. Rename project write tags to the suggested EasyDiff names category by
   category, preserving current and official tags as read aliases.
6. Add the shared versioned documentation-url resolver and descriptor
   `url` property, deriving ordinary parameter URLs from
   `CifHandler.project_name`.
7. Rework the user-guide parameter reference per §Documentation:
   Parameter-Reference Pages — three-tab tables ("How to access in the
   code", "Keys in EasyDiff", "Keys in CIF"), EasyDiff-named and
   EasyDiffraction-described detail pages, stable parameter anchors,
   relative links in static docs tables, icons on every
   category/parameter row, descriptor `url` links in runtime parameter
   tables/application displays, and the IUCr external-link icon — then
   update tutorials, ZIP project detection, and CLI help to say EasyDiff
   project files and report CIF exports.
8. Keep `project.report.save_cif()` as the only strict report-CIF
   writer.

## Open Questions

- Whether `.easydiff` should be exposed as a named public format in CLI
  commands or remain an implementation detail of project directories.
- Whether parameter-reference fields in the analysis categories
  (`_alias.parameter_unique_name`,
  `_fit_parameter.parameter_unique_name`,
  `_fit_parameter_correlation.parameter_unique_name_i/j`) should also
  adopt the `<target>_id` convention (e.g. `parameter_id`). They
  reference a parameter by its descriptive unique path rather than a
  datablock `id`, so the path name was kept (only `param`→`parameter`
  applied); switching to `parameter_id` is a separate decision.

## Suggested Pull Request

Title: Define EasyDiff project persistence

Description: Clarifies that saved EasyDiffraction projects use a
readable STAR-based schema, while generated report CIFs remain the
strict IUCr-facing export for publication and interoperability.
