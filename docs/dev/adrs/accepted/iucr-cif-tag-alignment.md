# ADR: IUCr CIF Tag Alignment

**Status:** Accepted  
**Date:** 2026-05-26

Reframes the earlier "IUCr CIF Tag Alignment for Fit Outputs" suggestion
(2026-05-24, PR #181) into a tiered policy. The default saved CIFs stay
optimised for day-to-day UX; a separate IUCr export path produces clean
report CIFs on demand. Amends parts of
[`analysis-cif-fit-state.md`](analysis-cif-fit-state.md) and
[`minimizer-input-output-split.md`](minimizer-input-output-split.md);
runs alongside the
[`python-cif-category-correspondence.md`](python-cif-category-correspondence.md)
suggestion (Python-side correspondence).

Grounded in:

- COMCIFS
  [`cif_core.dic`](https://raw.githubusercontent.com/COMCIFS/cif_core/main/cif_core.dic)
  v3.4.0 (2026-05-05; 787 `_alias.definition_id` entries).
- COMCIFS
  [`cif_pow.dic`](https://raw.githubusercontent.com/COMCIFS/Powder_Dictionary/master/cif_pow.dic)
  v2.5.0 (2026-05-19; 180 `_alias.definition_id` entries).

Both reference dictionaries are DDLm CIF_2.0 files. Their canonical
identifiers are dotted (`_definition.id '_pd_instr.geometry'`); the
legacy DDL1 underscore form is recorded as `_alias.definition_id` on
every item. The project emits the **dotted DDLm form universally**
(default save and IUCr export) and accepts both forms on read via the
dictionaries' alias tables.

A corpus of 10 published IUCr submission CIFs in `tmp/iucr-cifs/`
covering single-crystal (X-ray, neutron) and powder (lab X-ray, neutron,
synchrotron) refinements informs the **structural** decisions in §2 —
multi-datablock layout, `data_global` content patterns, reflection and
profile loop column sets, GSAS-II Rietveld block split. The corpus is
**not** authoritative for tag form, casing, or item names when it
disagrees with the reference dictionaries; example CIFs in the wild are
commonly produced by tooling that has not yet caught up with the current
DDLm spec. The dictionaries are the source of truth.

The submission-specific publication dictionary (`cif_publ.dic`) is not
consulted directly. The v1 report CIF deliberately avoids empty journal
and author template fields; the retained global metadata comes from
`cif_core.dic` items such as `_audit.*`, `_computing.*`, and
`_chemical_formula.*`. Deferred journal/publication tags are listed in
[`project-summary-rendering.md`](project-summary-rendering.md) §5.1.

## Context

EasyDiffraction saves project state into per-domain CIF files
(`project.cif`, `structures/<name>.cif`, `experiments/<name>.cif`,
`analysis/analysis.cif`). Two pressures act on the choice of category
and item names:

- **External interop.** Some current names diverge from the published
  IUCr dictionaries. External tooling (publCIF, checkCIF, pdCIFplotter,
  journal submission pipelines) cannot consume the diverging fields
  without a custom mapping layer.
- **Day-to-day UX.** Users switch between Python and direct CIF editing
  in a CLI. Some IUCr-canonical structures are awkward for hand editing
  — submission templates often include multi-datablock layouts with
  `data_global` metadata and TOF calibration as a coefficient loop
  indexed by integer `power`. The v1 report keeps the structural pieces
  and omits empty `_publ_*` / `_journal_*` placeholders. Parametric
  profile shape (Caglioti, FCJ, TOF sigma/gamma) has no IUCr counterpart
  at all.

A blanket "align with IUCr everywhere" policy pays a UX cost the project
does not need to absorb for files that are not submission targets. A
blanket "keep current names everywhere" policy gives up external interop
entirely. The chosen design splits along these two pressures.

Two earlier ADRs already touch this surface:

- [`loop-category-key-identity.md`](loop-category-key-identity.md) pins
  loop-key naming on COMCIFS conventions.
- [`python-cif-category-correspondence.md`](python-cif-category-correspondence.md)
  catalogues Python-vs-CIF category mismatches and chooses which side
  should bend.

This ADR closes the remaining gap on the **CIF side**.

## Scope

In scope:

- A tiered category-and-item-name policy for the default save, split by
  domain (structure / analysis / experiment).
- A new IUCr export path that produces a single clean report CIF on
  demand, separate from the default save.
- ADP write-side single-tag emission and casing alignment in the
  structure tier.
- Loop-tag style policy: dotted DDLm form universally on write, both
  dotted and underscore forms accepted on read.
- The per-descriptor mechanism that wires both write paths (`iucr_name`
  on `CifHandler`, category-level `IucrCategoryTransformer` for
  structural reshapings).
- Multi-datablock layout in the IUCr export, including the `data_global`
  audit, software, and chemistry metadata block.

Out of scope:

- Python attribute renames. This ADR changes CIF emission only.
  Cross-reference
  [`python-cif-category-correspondence.md`](python-cif-category-correspondence.md)
  for Python-side decisions.
- Adding new CIF categories the project does not currently track
  (`_chemical.*`, `_publ.*`, `_journal.*`) **for the default save**. The
  IUCr export derives `_chemical_formula.*` for the report only and does
  not emit `_publ_*` / `_journal_*` placeholders in v1.
- imgCIF (`cif_img.dic`); no raw image persistence path exists.
- Project-level singleton categories `_info.*`, `_rendering_plot.*`,
  `_rendering_table.*`, `_verbosity.*` — out of scope here; see
  `python-cif-category-correspondence`.

## Design Philosophy: Tiered Default Save + Separate IUCr Export

Each saved file lives in a directory whose name already scopes its
contents. `structures/<name>.cif` is unambiguously structural;
`experiments/<name>.cif` is unambiguously experimental;
`analysis/analysis.cif` is unambiguously analytic. The file path does
the disambiguation that a category prefix would otherwise carry. That
observation drives the policy:

- **Structure tier** — align category and item names with IUCr verbatim
  (with casing fixes). Crystallographic CIF names have decades of
  literature backing; hand-editors recognise them.
- **Analysis tier** — keep all fit-output statistics under
  topology-neutral `_fit_result.*` in `analysis/analysis.cif`, with
  **item** names matching dictionary casing (uppercase R / wR / DOI,
  etc.). The per-topology category split into `_refine_ls.*` /
  `_pd_proc_ls.*` / `_reflns.*` happens only in the IUCr export, where
  the experiment family is known per block. This sidesteps the
  schema-choice problem for joint and sequential fits described in the
  analysis-cif-fit-state ADR. Project-specific
  minimizer/sampler/Bayesian scaffolding stays under the current
  category names — file-scoped to `analysis/analysis.cif`, no namespace
  prefix.
- **Experiment tier** — keep current UX-friendly names (`_instr.*`,
  `_peak.*`, `_background.*`, `_expt_type.*`). The pdCIF
  instrument/calibration model is awkward (radiation as a loop, TOF as a
  coefficient loop indexed by integer `power`), and pdCIF has no
  parametric peak-shape items at all. File path scopes them; no prefix
  needed.
- **Reports** — a separate `project.report` facade that pulls live
  Python state and emits journal report artifacts under `reports/`. The
  IUCr CIF one-off method is `project.report.save_cif()`; the regular
  `project.save()` call emits configured reports from the
  `project.report.{cif,html,tex,pdf}` booleans. This path applies all
  IUCr renames, structural reshapings, multi-datablock layout, and
  project-extension namespacing (`_easydiffraction_*`). It replaces the
  unimplemented `project.summary` placeholder. **Export only — no
  round-trip.**

## Current State

Project CIF categories audited against `cif_core.dic` v3.4.0 and
`cif_pow.dic` v2.5.0. The "Default-save tier" column shows whether the
category changes in the default save; the "IUCr export" column shows the
dotted DDLm tag emitted by the IUCr CIF report writer.

| Category (current)                                                                              | IUCr dictionary                                                                                                | Default-save tier                           | IUCr export (dotted DDLm)                                                                                                                                                                        |
| ----------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- | ------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `_cell.*`                                                                                       | core                                                                                                           | Structure — unchanged                       | `_cell.length_a`, `_cell.angle_alpha`, etc.                                                                                                                                                      |
| `_atom_site.*` (most fields)                                                                    | core                                                                                                           | Structure — unchanged                       | `_atom_site.label`, `_atom_site.fract_x`, …                                                                                                                                                      |
| `_atom_site.adp_type`                                                                           | core (`_atom_site.ADP_type`)                                                                                   | Structure — casing fix                      | `_atom_site.ADP_type` (uppercase ADP per dictionary).                                                                                                                                            |
| `_atom_site.wyckoff_letter`                                                                     | core (`_atom_site.Wyckoff_symbol`)                                                                             | Structure — rename                          | `_atom_site.Wyckoff_symbol` (uppercase W, "symbol" not "letter").                                                                                                                                |
| `_atom_site.B_iso_or_equiv` / `U_iso_or_equiv`                                                  | core                                                                                                           | Structure — single-tag emit                 | `_atom_site.B_iso_or_equiv` xor `_atom_site.U_iso_or_equiv` per row, based on `_atom_site.ADP_type`.                                                                                             |
| `_atom_site_aniso.B_*` / `U_*`                                                                  | core                                                                                                           | Structure — single-tag emit                 | `_atom_site_aniso.B_*` xor `_atom_site_aniso.U_*` per row.                                                                                                                                       |
| `_space_group.name_h_m`                                                                         | core (`_space_group.name_H-M_alt`)                                                                             | Structure — casing fix                      | `_space_group.name_H-M_alt`.                                                                                                                                                                     |
| `_space_group.it_coordinate_system_code`                                                        | core (`_space_group.IT_coordinate_system_code`)                                                                | Structure — casing fix                      | `_space_group.IT_coordinate_system_code`.                                                                                                                                                        |
| symmetry operations                                                                             | core (`_space_group_symop.*`)                                                                                  | (not emitted today)                         | `_space_group_symop.id` + `_space_group_symop.operation_xyz` loop alongside the H-M name.                                                                                                        |
| `_diffrn.ambient_temperature`, `ambient_pressure`                                               | core                                                                                                           | Experiment — unchanged                      | `_diffrn.ambient_temperature`, `_diffrn.ambient_pressure`.                                                                                                                                       |
| `_diffrn.ambient_magnetic_field`, `ambient_electric_field`                                      | none                                                                                                           | Experiment — unchanged                      | `_easydiffraction_diffrn.ambient_magnetic_field`, `…electric_field` (project extension).                                                                                                         |
| `_refln.*`                                                                                      | core                                                                                                           | (no default save under refln)               | `_refln.*` reflections loop (column set differs by domain — see §2.3).                                                                                                                           |
| `_pd_meas.*`, `_pd_proc.*`, `_pd_calc.*`, `_pd_data.*`                                          | pdCIF                                                                                                          | Experiment — unchanged                      | `_pd_meas.*`, `_pd_proc.*`, `_pd_calc.*` profile-data loop (see §2.3).                                                                                                                           |
| `_pd_background.*`                                                                              | pdCIF                                                                                                          | Experiment — unchanged                      | `_pd_background.*`.                                                                                                                                                                              |
| `_pd_phase_block.*`                                                                             | pdCIF                                                                                                          | Experiment — unchanged                      | `_pd_phase_block.*`.                                                                                                                                                                             |
| `_sc_crystal_block.*`                                                                           | community (no IUCr counterpart)                                                                                | Experiment — unchanged                      | `_easydiffraction_sc_crystal_block.*` in IUCr export.                                                                                                                                            |
| `_instr.wavelength`                                                                             | core (`_diffrn_radiation_wavelength.value`)                                                                    | Experiment — unchanged                      | `_diffrn_radiation_wavelength.{id, value, wt}` — single-row category for monochromatic; loop only for multi-λ.                                                                                   |
| `_instr.2theta_offset`                                                                          | pdCIF (`_pd_calib.2theta_offset`)                                                                              | Experiment — unchanged                      | `_pd_calib.2theta_offset`.                                                                                                                                                                       |
| `_instr.2theta_bank`, `d_to_tof_*`                                                              | pdCIF (`_pd_calib_d_to_tof.*` loop)                                                                            | Experiment — unchanged                      | Four-row loop `_pd_calib_d_to_tof.{id, coeff, power, coeff_su, diffractogram_id}`.                                                                                                               |
| `_peak.*` (parametric profile shape)                                                            | none (pdCIF has no shape parameters)                                                                           | Experiment — unchanged                      | `_easydiffraction_peak.*` + `_pd_proc_ls.profile_function` free-text descriptor.                                                                                                                 |
| `_extinction.*`                                                                                 | core (`_refine_ls.extinction_*` items)                                                                         | Experiment — unchanged                      | `_easydiffraction_extinction.*` + dual emit `_refine_ls.extinction_{method,coef,expression}`.                                                                                                    |
| `_excluded_region.*`                                                                            | pdCIF (`_pd_proc.info_excluded_regions` free-text)                                                             | Experiment — unchanged                      | `_easydiffraction_excluded_region.*` + `_pd_proc.info_excluded_regions` free-text rendering.                                                                                                     |
| `_expt_type.*`                                                                                  | none                                                                                                           | Experiment — unchanged                      | `_easydiffraction_experiment_type.*`.                                                                                                                                                            |
| `_calculator.type`, `_minimizer.type`                                                           | none                                                                                                           | Analysis — unchanged                        | Selection fields remain settings only; identity is read from `analysis.software` for `_easydiffraction_software.{framework, calculator, minimizer}` and `_computing.structure_refinement`.       |
| `_software.*`                                                                                   | none                                                                                                           | Analysis — new provenance category          | Source for `_easydiffraction_software.{framework, calculator, minimizer}`, `_easydiffraction_software.fit_datetime`, and `_computing.structure_refinement` in `data_global`.                     |
| `_minimizer.*` settings (tolerances, max_iter, …)                                               | none                                                                                                           | Analysis — unchanged                        | `_easydiffraction_minimizer.*` (settings only, separate from the identification triple).                                                                                                         |
| `_fitting_mode.type`, `_background.type`                                                        | none                                                                                                           | Analysis / Experiment — unchanged           | `_easydiffraction_fitting_mode.type`, `_easydiffraction_background.type` selectors.                                                                                                              |
| `_fit_result.reduced_chi_square`, `n_data_points`, `n_parameters`                               | core (`_refine_ls.*`) and pdCIF (`_pd_proc_ls.*`)                                                              | Analysis — unchanged (topology-neutral)     | Shape-shifting per topology: see §1.2 and §3 transformers.                                                                                                                                       |
| `_fit_result.*` (R-factors, counts, profile/background function)                                | core / pdCIF                                                                                                   | Analysis — new fields under `_fit_result.*` | IUCr export remaps to per-topology `_refine_ls.*` / `_pd_proc_ls.*`; item names already match dictionary casing (§1.2).                                                                          |
| `_fit_result.*` (Bayesian diagnostics, success, message, fitting_time, iterations, result_kind) | none                                                                                                           | Analysis — unchanged                        | `_easydiffraction_fit_result.*`.                                                                                                                                                                 |
| `_fit_parameter`, `_fit_parameter_correlation`                                                  | none / partial                                                                                                 | Analysis — unchanged                        | `_easydiffraction_fit_parameter*` (no IUCr counterpart for per-parameter posterior).                                                                                                             |
| `_alias`, `_constraint`                                                                         | none                                                                                                           | Analysis — unchanged                        | `_easydiffraction_alias*`, `_easydiffraction_constraint*`.                                                                                                                                       |
| `_joint_fit`, `_sequential_fit*`                                                                | none                                                                                                           | Analysis — unchanged                        | `_easydiffraction_joint_fit*`, `_easydiffraction_sequential_fit*`.                                                                                                                               |
| reflection-set aggregates                                                                       | core (`_reflns.*`)                                                                                             | Analysis — new fields                       | `_reflns.number_total`, `_reflns.number_gt`, `_reflns.threshold_expression` (e.g. `'I>3\s(I)'`).                                                                                                 |
| report metadata                                                                                 | core (`_audit.*`, `_computing.*`, `_chemical_formula.*`) and project extension (`_easydiffraction_software.*`) | Analysis / derived report state             | Emitted in `data_global` block per §2.3a. Empty `_journal.*`, `_publ_*`, and `_pd_meas.info_author_*` placeholders are excluded by the clean-report policy in `project-summary-rendering.md` §5. |
| analysis-stack identification                                                                   | core (`_computing.structure_refinement`)                                                                       | Analysis — `_software.*` persisted          | `_easydiffraction_software.{framework, calculator, minimizer}` triple + `_easydiffraction_software.fit_datetime` + `_computing.structure_refinement` derived from `analysis.software`.           |

## Decision

### 1. Three-tier default save

#### 1.1 Structure tier — IUCr alignment + casing fixes

In `structures/<name>.cif`:

- Rename `_atom_site.adp_type` → `_atom_site.ADP_type` (uppercase ADP).
- Rename `_atom_site.wyckoff_letter` → `_atom_site.Wyckoff_symbol`
  (uppercase W, "symbol" not "letter"). The dictionary item
  `_atom_site.Wyckoff_letter` does not exist; the "letter" form lives in
  a different category (`_space_group_Wyckoff.letter`).
- Rename `_space_group.name_h_m` → `_space_group.name_H-M_alt`
  (uppercase hyphenated H-M, with `_alt` suffix per dictionary).
- Rename `_space_group.it_coordinate_system_code` →
  `_space_group.IT_coordinate_system_code` (uppercase IT).
- ADP single-tag emission per row (see §4).
- All other `_cell.*`, `_atom_site.*`, `_atom_site_aniso.*`,
  `_space_group.*` items already match IUCr verbatim — unchanged.

Python attribute names stay lowercase (`atom_site.adp_type`,
`atom_site.wyckoff_letter`, `space_group.name_h_m`,
`space_group.it_coordinate_system_code`). Only emitted CIF tags change.

#### 1.2 Analysis tier — topology-neutral `_fit_result.*`, IUCr renaming on export only

In `analysis/analysis.cif`:

- **All fit-output statistics stay under topology-neutral
  `_fit_result.*` in the default save.** The IUCr-side category split
  into coreCIF `_refine_ls.*` (single-crystal) versus pdCIF
  `_pd_proc_ls.*` (powder) happens **only** in the IUCr export (§2 / §3
  transformers). This avoids the deterministic- schema problem
  reviewer-flagged for joint and sequential fits: one
  `analysis/analysis.cif` can describe a refinement that spans multiple
  experiments with different sample forms, so a per-experiment-driven
  schema choice cannot be made at the project level. Topology-neutral
  `_fit_result.*` round-trips cleanly under
  [`analysis-cif-fit-state.md`](analysis-cif-fit-state.md)'s single
  common projection.
- Existing items keep their names verbatim
  (`_fit_result.reduced_chi_square`, `_fit_result.n_data_points`,
  `_fit_result.n_parameters`, …). The IUCr export remaps them to the
  dictionary-canonical tags per topology (see §2 and §3).
- **New items added under `_fit_result.*`** using dictionary-canonical
  _item names_ (with the project-side category prefix preserved):
  - `_fit_result.R_factor_all`, `_fit_result.wR_factor_all` (uppercase R
    / wR matching the coreCIF item names).
  - `_fit_result.R_factor_gt`, `_fit_result.wR_factor_gt`
    (observed-reflection subsets).
  - `_fit_result.prof_R_factor`, `_fit_result.prof_wR_factor`,
    `_fit_result.prof_wR_expected` (powder-only, derived from profile
    residuals).
  - `_fit_result.number_restraints`, `_fit_result.number_constraints`
    (written only when positive).
  - `_fit_result.profile_function`, `_fit_result.background_function`
    (powder; free-text descriptors of the active peak and background
    categories).
  - `_fit_result.threshold_expression`,
    `_fit_result.number_reflns_total`, `_fit_result.number_reflns_gt` —
    required to make the `_gt` R-factor pair interpretable. Fields that
    are not meaningful for a given experiment family (e.g.,
    `prof_R_factor` for a single-crystal-only refinement) are omitted
    from `_fit_result.*`; the IUCr export omits them per block. Live
    deterministic fit results may still carry runtime-only convergence
    diagnostics such as `shift_over_su_max` and `shift_over_su_mean`,
    but those are not part of the default `analysis/analysis.cif`
    fit-result projection.
- Bayesian diagnostics, success/message/iterations/fitting*time,
  `result_kind`, `point_estimate_name`, fit-parameter posterior
  summaries, and the `_alias` / `_constraint` / `_joint_fit` /
  `\_sequential_fit*`registries — **stay under their current category names**. File-scoping to`analysis/analysis.cif`carries the disambiguation; no`\_easydiffraction\*\*`
  prefix is added in the default save.
- The `_minimizer.*`, `_fitting_mode.*`, `_calculator.*` selectors stay
  under their current names for the same reason.

The dictionary-canonical tag _form_ (uppercase R / wR / DOI, etc.) is
preserved in the _item_ names under `_fit_result.*`. Only the _category_
prefix changes between default save (`_fit_result.*`) and IUCr export
(`_refine_ls.*` / `_pd_proc_ls.*` / `_reflns.*` per block).

#### 1.3 Experiment tier — no changes in the default save

In `experiments/<name>.cif`: keep every current category and item name.
Specifically:

- `_instr.*`, `_peak.*`, `_background.*` / `_pd_background.*`,
  `_pd_phase_block.*`, `_sc_crystal_block.*`, `_extinction.*`,
  `_excluded_region.*`, `_expt_type.*`, `_diffrn.*`,
  `_pd_meas/proc/calc/data.*`, `_refln.*` — all unchanged.
- Wavelength stays the single scalar `_instr.wavelength`. TOF
  calibration stays the four scalar items
  `_instr.d_to_tof_{offset, linear, quad, recip}`. The structural
  reshapings happen only in the IUCr export (§2).
- Parametric profile shape (`_peak.*` Caglioti / Lorentzian / FCJ / TOF
  coefficients) stays under `_peak.*`.

### 2. Reports — IUCr-aligned report CIF

#### 2.1 API

```python
project.save()                          # project files + configured reports
project.report.save_cif()               # one-off reports/<project>.cif
project.report.save()                   # write configured reports only
```

`project.summary` (currently an unimplemented placeholder) is removed
and replaced by `project.report` — a facade slot that owns journal
report generation. The `project.report.{cif,html,tex,pdf}` booleans
control which reports `project.save()` emits. Per-format methods
(`save_cif()`, `save_html()`, `save_tex()`, `save_pdf()`) write one-off
artifacts without changing that configuration. The no-arg
`project.report.save()` uses those booleans and raises `ValueError` when
no formats are enabled.

#### 2.2 Output location

A **single CIF file** at `reports/<project_name>.cif` inside the project
root. One file per project, regardless of how many structures or
experiments live in it; the published IUCr submission convention is "one
CIF per article, multiple data blocks inside" (corroborated by 10/10
example files in the corpus).

```text
<project_root>/
  project.cif
  structures/
    phase1.cif
    phase2.cif
  experiments/
    pd_neutron.cif
    pd_xray.cif
  analysis/
    analysis.cif
  reports/                              # written by report config or save_cif()
    <project_name>.cif                  # single multi-block IUCr CIF
```

##### Worked layout examples

Concrete project layouts for the four topology types covered in §2.3.
Default-save files are one-per-object as today; the IUCr export
collapses to a single file with topology-driven data blocks. Inline
comments name the categories inside each block.

**Example A — Single-crystal, single structure (single experiment).**

```text
quartz_sc/
  project.cif
  structures/
    quartz.cif                            # _cell.*, _atom_site.* (ADP_type, Wyckoff_symbol)
  experiments/
    xray_sc.cif                           # _instr.*, _peak.*, _diffrn.*
  analysis/
    analysis.cif                          # _fit_result.* (topology-neutral: reduced_chi_square,
                                          #   R_factor_*, wR_factor_*, n_data_points, n_parameters,
                                          #   plus Bayesian / non-IUCr fields)
                                          # _easydiffraction_minimizer.* (settings)
  reports/
    quartz_sc.cif                         # data_global    — _audit.*,
                                          #                  _easydiffraction_software.{framework,
                                          #                  calculator, minimizer},
                                          #                  _computing.structure_refinement,
                                          #                  _chemical_formula.*
                                          # data_quartz   — _cell.*, _atom_site.*, _atom_site_aniso.*,
                                          #                  _space_group.*, _space_group_symop.* loop,
                                          #                  _diffrn.*, _diffrn_radiation_wavelength.*,
                                          #                  _refine_ls.*, _reflns.*,
                                          #                  _refln.* loop (F², include_status),
                                          #                  _easydiffraction_extinction.* +
                                          #                  _refine_ls.extinction_* dual emit
```

**Example B — Powder Rietveld, single phase, single experiment.**

```text
mgo_rietveld/
  project.cif
  structures/
    mgo.cif
  experiments/
    npd.cif                               # neutron powder, CWL
  analysis/
    analysis.cif
  reports/
    mgo_rietveld.cif                      # data_global               — audit, software, _chemical_formula
                                          # data_overall — _pd_proc_ls.prof_R_factor,
                                          #                .prof_wR_factor,
                                          #                .prof_wR_expected,
                                          #                .profile_function,
                                          #                .background_function,
                                          #                _refine_ls.number_parameters,
                                          #                _pd_block_id cross-refs
                                          # data_mgo     — MgO structure
                                          # data_npd     — _pd_meas.* profile loop
                                          #                (_2theta_scan, intensity_total,
                                          #                _pd_calc.intensity_total,
                                          #                _pd_proc.intensity_bkg_calc,
                                          #                _pd_proc_ls.weight),
                                          #                _refln.* powder reflections loop
```

**Example C — Joint Rietveld, multi-experiment (neutron + X-ray).**

```text
co2sio4/
  project.cif
  structures/
    co2sio4.cif
  experiments/
    npd_300K.cif
    xrd_300K.cif
  analysis/
    analysis.cif                          # _joint_fit weights
  reports/
    co2sio4.cif                           # data_global          — audit, software, chemistry
                                          # data_overall     — combined refinement stats
                                          # data_co2sio4     — Co2SiO4 structure
                                          # data_npd_300K    — NPD pattern,
                                          #                          _pd_block_diffractogram_id='npd_300K'
                                          # data_xrd_300K    — XRD pattern,
                                          #                          _pd_block_diffractogram_id='xrd_300K'
```

**Example D — Sequential fit, multi-temperature TOF Rietveld.**

```text
co2sio4_t_series/
  project.cif
  structures/
    co2sio4.cif
  experiments/
    tof_5K.cif
    tof_100K.cif
    tof_165K.cif
    tof_200K.cif
  analysis/
    analysis.cif                          # _sequential_fit configuration
  reports/
    co2sio4_t_series.cif                  # data_global                  — audit, software, chemistry
                                          # data_overall
                                          # data_co2sio4
                                          # data_tof_5K   — TOF 5K,
                                          #                                 _pd_meas.time_of_flight,
                                          #                                 _pd_calib_d_to_tof loop
                                          # data_tof_100K — TOF 100K
                                          # data_tof_165K — TOF 165K
                                          # data_tof_200K — TOF 200K
```

#### 2.3 Multi-datablock layout inside the export file

**Every export file starts with a `data_global` block carrying audit,
software, and chemistry metadata** (§2.3a). Subsequent blocks depend on
analysis topology. Block content uses dotted DDLm form throughout. The
single-block-name rule is uniform across topologies; topology-specific
GSAS-II-style suffix conventions seen in some example files (e.g.
`data_<project>_publ`, `data_<project>_overall`) are folded into
`data_global` for global metadata and `data_overall` for refinement
metadata, leaving no ambiguity about block roles.

- **Single-crystal, single structure (single experiment).**
  `data_global` + `data_<structure>` (or `data_I` if no name is set).
  Pattern in `bal5004.cif`, `bp5083.cif`, `ks5497.cif`, `ra5167.cif`:
  `data_global + data_I`.

- **Single-crystal, multiple structures or temperatures.**
  `data_global` + one block per structure or per temperature. Pattern in
  `bp5014.cif`: `data_global + data_300K + data_55K + data_2point5K`.

- **Powder Rietveld (single or multi-experiment, single or
  multi-phase).** GSAS-II-style block split, with the global metadata
  block named `data_global` per the invariant above:
  - `data_global` (audit, software, and chemistry metadata per §2.3a),
  - `data_overall` (refinement-level metadata — Rietveld R-factors,
    profile/background function descriptors, parameter counts),
  - `data_<structure-name>` (one per phase — structural data per
    `_pd_phase_block.id`),
  - `data_<experiment-name>` (one per diffraction pattern — measurement
    metadata, profile data loop, reflections loop).

  This deviates from the `data_<project>_publ` GSAS-II convention seen
  in `hb8206.cif`; the deviation buys a uniform rule across
  single-crystal and powder exports and matches the single-crystal
  corpus (`bal5004`, etc.) which uses `data_global` universally.
  `data_overall` is deliberately unprefixed because the generated report
  CIF is already scoped to one project. `global` means file/report
  metadata; `overall` means combined refinement summary. Phase and
  diffractogram blocks use the existing structure and experiment names
  after CIF block-code normalization; if two normalized names collide,
  append a short numeric suffix to preserve uniqueness.

- **Multi-experiment joint Rietveld.** Same shape as the
  single-experiment Rietveld block split above, with one
  `data_<experiment-name>` block per pattern, all cross-referenced via
  `_pd_block_diffractogram_id` and `_pd_block_id`.

  `_pd_block_id` identifies phase/model blocks; in this report that is
  the `data_<structure-name>` block ID. `_pd_block_diffractogram_id`
  identifies diffractogram/pattern blocks; in this report that is the
  `data_<experiment-name>` block ID. For single references, emit the
  scalar block ID directly (for example `_pd_block_id lbco`, not
  `_pd_block_id |lbco|`). User preference recorded for future
  multi-block expansion: "If multiple phases/patterns are needed, I'd
  rather use a proper loop or move toward the newer pdCIF replacement
  fields, not encode lists in one scalar with pipes."

- **Sequential fit.** One file per step is **not** the IUCr convention;
  sequential refinements emit one `data_<experiment-name>` block per
  step inside the same `reports/<project>.cif`. Natural sequential
  ordering matches the multi-pattern Rietveld pattern above.

#### 2.3a `data_global` block content

Items below are all defined in `cif_core.dic` v3.4.0; emit values where
the project has source data, otherwise `?`.

- `_audit.creation_method 'EasyDiffraction <version>'`,
  `_audit.creation_date <iso8601>`.
- `_computing.structure_refinement` (single string derived from
  `analysis.software`; when calculator or minimizer provenance is unset
  it falls back to the framework label only, e.g.
  `'EasyDiffraction 0.17.0 with lmfit 1.0.0 minimizer and cryspy 1.2.3 calculator'`).
  coreCIF standard channel for advertising the analysis-software stack
  to IUCr-aware tooling.
- `_easydiffraction_software.*` triple holding the same three roles in
  structured form, plus `_easydiffraction_software.fit_datetime` when a
  fit timestamp is available (see §2.3a-i below).
- No `_journal.*`, `_journal_date.*`, `_journal_coeditor.*`,
  `_publ_contact_author.*`, `_publ_author.*`, `_publ_body.*`, or
  `_pd_meas.info_author_*` placeholders are emitted in v1. The clean
  report policy and deferred tag list live in
  [`project-summary-rendering.md`](project-summary-rendering.md) §5.
- `_chemical_formula.*` chemistry summary derived from atom-site data
  where possible: `_chemical_formula.sum`, `_chemical_formula.moiety`,
  `_chemical_formula.weight`, `_chemical_formula.IUPAC` (uppercase IUPAC
  per dictionary).

User-supplied publication metadata (`publ_info.json`, `publ_info.toml`,
or a Python `project.publication` owner) is deferred — see Deferred Work
and the clean report policy in `project-summary-rendering.md` §5.

#### 2.3a-i `_easydiffraction_software` framework

The IUCr-aligned report needs to identify the analysis stack. The
project emits one structured category in `data_global` from
`analysis.software`, carrying three role-keyed strings and an optional
fit timestamp:

```
_easydiffraction_software.framework    'EasyDiffraction 0.17.0'
_easydiffraction_software.calculator  'cryspy 1.2.3'
_easydiffraction_software.minimizer   'lmfit 1.0.0'
_easydiffraction_software.fit_datetime 2026-05-26T13:45:00+00:00
```

- `_easydiffraction_software.framework` — EasyDiffraction itself, the
  orchestrating analysis software, with version.
- `_easydiffraction_software.calculator` — the active calculation
  backend (cryspy, crysfml, pdffit2) with version.
- `_easydiffraction_software.minimizer` — the active minimizer (lmfit,
  scipy-lstsq, dfo-ls, emcee, …) with version. Bayesian sampler runs use
  the sampler name and version here.
- `_easydiffraction_software.fit_datetime` — ISO-8601 UTC timestamp of
  the successful fit that populated `analysis.software`. Omitted when no
  timestamp is recorded.

The same three values are concatenated into the
`_computing.structure_refinement` free-text string for IUCr-tooling
compatibility (publCIF / checkCIF key on `_computing.*`, not on the
project extension).

The existing `_easydiffraction_minimizer.*` category in
`analysis/analysis.cif` (default save) keeps its role as the
**settings** container — convergence tolerances, max iteration counts,
sampler chain lengths, etc. — and is also emitted as
`_easydiffraction_minimizer.*` in the IUCr export, separate from the
identification triple above.

#### 2.3b Structure-block content (per-block)

For each `data_<structure>` (single-crystal) or `data_<structure-name>`
(powder Rietveld phase) block:

- `_chemical_formula.{moiety, sum, weight, IUPAC}` summary.
- `_cell.*` (`length_a`, `angle_alpha`, `volume`,
  `measurement_temperature`, etc.).
- `_space_group.name_H-M_alt`, `_space_group.IT_coordinate_system_code`,
  `_space_group.crystal_system`, plus the explicit
  `_space_group_symop.id` + `_space_group_symop.operation_xyz` loop
  alongside the H-M name.
- `_diffrn.*` (instrument, radiation, measurement conditions).
  Wavelength as the `_diffrn_radiation_wavelength` category (single-row
  category form for monochromatic, loop form for multi-λ — see §3
  transformer).
- `_exptl_crystal.*` if the project tracks crystal-specimen metadata
  (currently it does not — deferred work).
- `_atom_site.*` loop with `_atom_site.label`, `_atom_site.type_symbol`,
  `_atom_site.fract_x/y/z`, `_atom_site.occupancy`,
  `_atom_site.ADP_type`, `_atom_site.B_iso_or_equiv` xor
  `_atom_site.U_iso_or_equiv` per row, `_atom_site.Wyckoff_symbol`.
- `_atom_site_aniso.*` loop (when anisotropic ADPs present), emitting
  `B_*` xor `U_*` family per row.
- `_refine_ls.*` (single-crystal) or `_pd_proc_ls.*` (powder) refinement
  statistics.
- `_reflns.number_total`, `_reflns.number_gt`,
  `_reflns.threshold_expression`.

#### 2.3c Single-crystal reflections loop

Column set (DDLm dotted form):

```
loop_
_refln.index_h
_refln.index_k
_refln.index_l
_refln.F_squared_meas
_refln.F_squared_calc
_refln.F_squared_meas_su
_refln.include_status
```

Column set chosen from `cif_core.dic` (the dictionary defines
`_refln.include_status` for marking observed reflections; the corpus
form `_refln.observed_status` is **not** in the current dictionary and
is treated as outdated). The `_su` suffix follows DDLm convention; the
parenthesised CIF uncertainty syntax remains the preferred numeric
encoding per `free-flag-cif-encoding.md`, so `_refln.F_squared_meas_su`
is emitted only when a paired-value column is needed.

#### 2.3d Powder reflections loop

```
loop_
_refln.index_h
_refln.index_k
_refln.index_l
_refln.F_squared_meas
_refln.F_squared_calc
_pd_refln.phase_id
_refln.d_spacing
```

Column set adapted from the corpus content (`bal5001.cif`, `hb8206.cif`)
with tag form taken from `cif_core.dic` and `cif_pow.dic`. The phase
identifier uses the powder dictionary's `_pd_refln.phase_id`; it is not
the calculated structure-factor phase angle `_refln.phase_calc`.

#### 2.3e Powder profile-data loop

```
loop_
_pd_meas.2theta_scan
_pd_meas.intensity_total
_pd_calc.intensity_total
_pd_proc.intensity_bkg_calc
_pd_proc_ls.weight
```

For TOF experiments, the `_pd_meas.2theta_scan` column is replaced by
`_pd_meas.time_of_flight`. Verified against `bal5001.cif` (content set;
tag form follows `cif_pow.dic`).

#### 2.3f `data_overall` block (Rietveld only)

For powder Rietveld files, an `_overall` block carries refinement-level
metadata that applies across all phases and patterns:

- `_pd_calc.method 'Rietveld Refinement'`.
- `_pd_proc_ls.prof_R_factor`, `_pd_proc_ls.prof_wR_factor`,
  `_pd_proc_ls.prof_wR_expected`.
- `_pd_proc_ls.profile_function`, `_pd_proc_ls.background_function`
  (free-text descriptors).
- `_pd_proc_ls.pref_orient_corr` (when preferred-orientation correction
  is applied).
- `_refine_ls.number_parameters`, `_refine_ls.number_restraints`,
  `_refine_ls.number_constraints`.
- `_pd_block_id` references to phase/model blocks and
  `_pd_block_diffractogram_id` references to diffractogram/pattern
  blocks. Single references are plain scalar IDs. Multiple
  phases/patterns should use a proper loop or newer pdCIF replacement
  fields, not pipe-delimited scalar lists.

#### 2.3g `data_<experiment-name>` block (Rietveld only — constant wavelength)

For each constant-wavelength (CWL) diffraction pattern:

- `_pd_meas.*` measurement metadata (`_pd_meas.scan_method`,
  `_pd_meas.2theta_range_min/max/inc`, `_pd_meas.number_of_points`,
  `_pd_meas.datetime_initiated`). The
  `_pd_meas.info_author_{name, email, phone}` placeholders are omitted
  by the clean report policy.
- `_diffrn.*` and `_diffrn_radiation_wavelength.*` (radiation type,
  probe, wavelength).
- `_pd_proc.2theta_range_min/max/inc`, `_pd_proc.info_data_reduction`,
  `_pd_proc.info_datetime`, `_pd_proc.info_excluded_regions`.
- `_pd_proc_ls.*` profile-fit R-factors for this pattern.
- The `_pd_meas.*` profile-data loop (§2.3e).
- The `_refln.*` reflections loop (§2.3d).

#### 2.3h `data_<experiment-name>` block (Rietveld only — TOF)

For time-of-flight (TOF) diffraction patterns the block has the same
shape as §2.3g, with three TOF-specific substitutions — **all defined in
`cif_pow.dic` v2.5.0**, no project extensions needed for the standard
powder TOF surface:

- Measurement x-axis: `_pd_meas.time_of_flight` (with
  `_pd_meas.time_of_flight_su` companion when paired-value emission is
  needed). Replaces the `_pd_meas.2theta_scan` column in the
  profile-data loop.
- d-spacing → TOF calibration: the four-row
  `_pd_calib_d_to_tof.{id, coeff, coeff_su, power, diffractogram_id}`
  loop materialised by the §3 transformer. The dictionary defines the
  equation as `TOF = Σ c_i · d^(p_i)` (`_pd_calib_d_to_tof.coeff` and
  `_pd_calib_d_to_tof.power`, summed over rows; cif_pow.dic lines 2429
  ff.). The `_pd_calib_d_to_tof.id` column accepts arbitrary codes per
  the dictionary (its own example uses `0`, `DIFC`, `t2`); the project
  uses the EasyDiffraction attribute names verbatim:

  ```
  loop_
  _pd_calib_d_to_tof.id
  _pd_calib_d_to_tof.power
  _pd_calib_d_to_tof.coeff
  _pd_calib_d_to_tof.coeff_su
  _pd_calib_d_to_tof.diffractogram_id
    offset  0   <c_offset>  <su>  <diffractogram>
    linear  1   <c_linear>  <su>  <diffractogram>
    quad    2   <c_quad>    <su>  <diffractogram>
    recip  -1   <c_recip>   <su>  <diffractogram>
  ```

  Rows with a zero coefficient may be omitted. Units are determined
  per-row by `power` (μs at power 0, μs/Å at power 1, μs/Å² at power 2,
  Å/μs at power −1) per the dictionary's `_method.expression` block on
  `_pd_calib_d_to_tof.coeff`.

- Profile-data loop for TOF:

  ```
  loop_
  _pd_meas.time_of_flight
  _pd_meas.intensity_total
  _pd_calc.intensity_total
  _pd_proc.intensity_bkg_calc
  _pd_proc_ls.weight
  ```

  Same columns as §2.3e except the x-axis. The `_diffrn.*` and
  `_pd_meas.scan_method` items advertise the TOF nature for external
  readers that do not key off the column name alone.

The richer
`_pd_calib_xcoord.{actual_time_of_flight, nominal_time_of_flight, …}`
calibration pair (`cif_pow.dic` lines 3881 ff., 4167 ff.) is **not**
emitted in the first pass — the project does not currently track
actual-vs-nominal TOF calibration distinct from the polynomial
coefficients. Flagged as deferred work.

#### 2.4 Formatting (separate IUCr writer)

The IUCr writer pass differs from the default writer:

- Dotted DDLm item form (`_atom_site.label`) — same as the default save.
  The reference dictionaries declare every item in dotted form; the
  corpus' DDL1 underscore usage is treated as outdated tooling output,
  not a target convention.
- Blank line between every category, and between a category and a
  following loop.
- `# ---- <section> ----` header before each logical group within a
  block (chemical metadata, cell, space group, symmetry operations,
  diffraction, atoms, ADP, refinement, reflections / profile data,
  project extensions).
- Block separator
  `#=====================================================` between
  `data_*` blocks.
- Loop columns left-aligned to per-column widths; loop body lines
  indented two spaces.
- 80-char wrap on long string values per CIF spec.
- Numeric `_su` always written via the parenthesised CIF uncertainty
  syntax (e.g. `5.4307(2)`); `_su` companion items are not emitted as
  separate fields. Matches the existing project encoding from
  `free-flag-cif-encoding.md`.
- Project-extension `_easydiffraction_*` categories grouped at the end
  of each block under a `# ---- EasyDiffraction project extensions ----`
  header.

#### 2.5 Submission-side validation

**Superseded (2026-05-30): the runtime writer self-check described below
was removed.** The IUCr CIF writer no longer validates its own output
against `cif_core.dic` / `cif_pow.dic`; `reports/<project>.cif` is
written directly. Rationale:

- The report CIF is our own deterministic output. Checking it at write
  time and raising `EasyDiffractionWriterError` ("…file a bug") turns a
  developer-side test concern into a user-facing failure that blocks a
  scientist's report over a defect only we can fix.
- The check resolved dictionaries from `tmp/iucr-dicts/` under the
  repository root. That path never resolves for a pip-installed user, so
  the self-check was a silent no-op for everyone except a developer who
  had manually placed the dictionaries — where it only produced noise,
  because the current COMCIFS DDLm/CIF2 dictionaries do not parse under
  the helper's gemmi + regex approach.
- Spec compliance of the emitted tag set is maintained by authoring the
  writer against the COMCIFS reference dictionaries (the dotted-tag set
  is fixed in `iucr_writer.py`); a separate IUCr-server upload remains
  the authoritative compliance check before submission. No part of the
  library reads `tmp/iucr-dicts/` at runtime.

The original decision (retained for history): the writer ran generated
content through `gemmi` before writing, with public
`project.report.check()` / `check=True` entry points removed so that
dictionary compliance was an internal writer self-check rather than a
user choice. The intended gemmi checks were tag existence in
`cif_core.dic` / `cif_pow.dic` (unknown non-`_easydiffraction_*` tags
raising `EasyDiffractionWriterError`), value-type matching against
`_type.contents`, required category keys per loop row, single-category
loop columns, and well-formed DDLm dotted form. It never covered
crystallographic sanity checks (bond lengths, void volumes, density
plausibility, missed-symmetry detection, ADP positive-definiteness) or
whether future journal-submission metadata is complete — that remains a
separate IUCr-server concern. The v1 clean report CIF does not emit the
empty `_journal.*` / `_publ_*` placeholders.

### 3. Handler mechanism — `iucr_name` + `IucrCategoryTransformer`

Both write paths read the same in-memory `Parameter` /
`StringDescriptor` / `NumericDescriptor` objects. Drift between default
save and IUCr export is prevented by two complementary mechanisms.

**Per-field — `iucr_name: str | None` on `CifHandler`.** Singular,
chosen for consistency with the existing `names: list[str]`. The
exporter resolves the IUCr-side tag as `iucr_name` when set, otherwise
falls back to `names[0]`. Both forms are dotted DDLm.

```python
# Structure — casing differs from default save
self._adp_type = StringDescriptor(
    name='adp_type',
    cif_handler=CifHandler(
        names=['_atom_site.adp_type'],
        iucr_name='_atom_site.ADP_type',
    ),
)

# Analysis — default already matches IUCr; iucr_name omitted
self._goodness_of_fit = Parameter(
    name='reduced_chi_square',
    cif_handler=CifHandler(
        names=['_refine_ls.goodness_of_fit_all'],
        # exporter falls back to names[0]
    ),
)

# Project extension — IUCr export uses _easydiffraction_* prefix
self._fitting_time = Parameter(
    name='fitting_time',
    cif_handler=CifHandler(
        names=['_fit_result.fitting_time'],
        iucr_name='_easydiffraction_fit_result.fitting_time',
    ),
)
```

The mechanism scales: future export targets (mmCIF, journal dialects)
get sibling fields (`mmcif_name`, etc.) without rewriting existing
handlers. There is no clever prefix-substitution rule — explicit beats
clever.

Per-experiment-family dual mapping (e.g., `fit_result.n_data_points`
mapping to `_refine_ls.number_reflns` for single-crystal but
`_pd_proc.number_of_points` for powder) is handled at the
category-transformer level (below), not by promoting `iucr_name` to a
list. The per-field handler stays simple.

**Category-level — `IucrCategoryTransformer` subclasses for structural
reshaping.** A small number of items don't rename, they restructure:

- **Wavelength** — single-row
  `_diffrn_radiation_wavelength.{id, value, wt}` for monochromatic
  radiation (the common case); full loop form when multiple wavelengths
  are tracked.
- **TOF calibration** — four scalar Python parameters
  (`d_to_tof_offset`, `d_to_tof_linear`, `d_to_tof_quad`,
  `d_to_tof_recip`) materialise as a four-row
  `_pd_calib_d_to_tof.{id, coeff, power, coeff_su, diffractogram_id}`
  loop. Per cif_pow.dic the equation is `TOF = Σ c_i · d^(p_i)`; the
  rows use the EasyDiffraction attribute names as `id` codes (`offset`,
  `linear`, `quad`, `recip`) with corresponding `power = 0, 1, 2, -1`.
  Full row layout in §2.3h.
- **Range-form excluded regions** — free-text
  `_pd_proc.info_excluded_regions` rendering of the range list.
- **Symmetry operations** — `_space_group_symop.*` loop derived from the
  active space group (no Python-side persistence of symop strings
  today).
- **Extinction (single-crystal)** — the project's
  `_easydiffraction_extinction.{type, model, mosaicity, radius}`
  category is **also** emitted as the coreCIF `_refine_ls.extinction_*`
  triple in single-crystal IUCr export blocks. The mapping is direct
  because the dictionary text for `_refine_ls.extinction_method` defines
  it as a free-text descriptor that already enumerates the
  Becker-Coppens type 1 / type 2 / mixed, Gaussian / Lorentzian,
  isotropic / anisotropic taxonomy — exactly what the project's `type` +
  `model` selectors represent. Concrete mapping:

  | Project field                                                                         | IUCr emit                                                                        |
  | ------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------- |
  | `extinction.type = 'becker_coppens'`, `extinction.model = 'gaussian_isotropic_type1'` | `_refine_ls.extinction_method 'Becker-Coppens type 1 Gaussian isotropic'`        |
  | `extinction.type = 'zachariasen'`                                                     | `_refine_ls.extinction_method 'Zachariasen'`                                     |
  | `extinction.mosaicity` (BC type 1 or Zachariasen)                                     | `_refine_ls.extinction_coef <value>`                                             |
  | `extinction.radius` (BC type 2)                                                       | `_refine_ls.extinction_coef <value>`                                             |
  | BC mixed (both `mosaicity` and `radius` present)                                      | `_refine.special_details '<formula with both coefficients>'` per dictionary text |

  The transformer reads the active `_easydiffraction_extinction.*`
  values, picks the right coefficient channel based on `type` and
  `model`, and falls back to `_refine.special_details` when the
  Becker-Coppens "mixed" case is detected. The
  `_easydiffraction_extinction.*` block is emitted alongside (not
  instead of) the standard items, so the full project-side detail
  survives round-trip through any tool that reads `_easydiffraction_*`
  extensions while standard tools see the coreCIF triple.

These cannot be expressed as `iucr_name`; the unit of transformation is
a category, not a field. They live in the IUCr exporter as
`IucrCategoryTransformer` subclasses, registered alongside the existing
`CategoryItem` subclasses.

### 4. ADP tags — single-tag emission on write

Both `_atom_site_aniso.B_ii` and `_atom_site_aniso.U_ii` exist in
coreCIF, as do `_atom_site.B_iso_or_equiv` and
`_atom_site.U_iso_or_equiv`. The dictionary expects exactly one family
per file, declared by `_atom_site.ADP_type`. Policy applies to **both**
default save and IUCr export:

- **Read**: accept either tag family. Unchanged.
- **Write**: emit the tag matching `atom_site.ADP_type` for that row;
  omit the other.

The choice is per-row based on `ADP_type`, not a project-wide default.
The [`type-neutral-adp-parameters.md`](type-neutral-adp-parameters.md)
Python contract is unchanged.

The writer no longer propagates one file-wide B/U convention across all
atom sites before serialisation. If a structure contains both
B-convention and U-convention atoms, the emitted CIF contains one
`_atom_site_aniso.B_*` loop and one `_atom_site_aniso.U_*` loop, each
containing only the rows whose `ADP_type` matches that family.

### 5. Loop-tag style — dotted DDLm on write, dual-name on read

Both reference dictionaries declare every item in dotted DDLm form and
record the legacy DDL1 underscore form as `_alias.definition_id` (787 in
coreCIF, 180 in pdCIF). The dictionaries are the spec; corpus example
files often lag the spec because they are produced by tooling (GSAS-II,
Jana2006, SHELX, etc.) that has not yet caught up with the DDLm
conversion.

Policy:

- **Write — dotted DDLm form universally** for both the default save and
  the IUCr export. Matches the dictionaries' canonical identifiers and
  the project's current write behaviour.
- **Read — accept dotted and underscore form** for every IUCr-aligned
  category, using the dictionaries' `_alias.definition_id` table as the
  source of truth. The project already does this for
  `_pd_background.line_segment_X` / `_pd_background_line_segment_X`;
  extend the same policy to every IUCr-aligned category.

## Consequences

### Positive

- Day-to-day saved files keep current UX (no Caglioti coefficients
  hidden inside loops, no awkward `_diffrn_radiation_wavelength` loop
  for what's morally a scalar, no `_pd_calib_d_to_tof.power` integer
  rows for users to figure out).
- Structure CIFs (default save) become directly recognisable to
  crystallographers reading or hand-editing them — names match the
  literature.
- Analysis CIFs (default save) use dictionary-canonical _item_ names for
  fit statistics (uppercase R / wR, etc.) under the topology-neutral
  `_fit_result.*` category, so per-field identifiers are immediately
  recognisable to scientists familiar with `_refine_ls.*` /
  `_pd_proc_ls.*` from Rietveld publications; the IUCr export carries
  the matching dictionary-canonical category prefixes per topology.
- The report CIF becomes a single explicit report command, with no
  manual editing required for the refinement data:
  `project.report.save_cif()` produces a clean file at
  `reports/<project>.cif` matching the multi-datablock publication
  convention for structural and fit content. Users who want CIF reports
  on every project save can set `project.report.cif = True`.
- Journal and author metadata placeholders are omitted from
  `data_global`; a future submission-specific surface can add them when
  a concrete journal workflow requires them.
- External IUCr tooling (publCIF, checkCIF, pdCIFplotter) can consume
  the report file cleanly; the day-to-day saved files are not a tooling
  target.
- `_easydiffraction_*` prefix appears only in the IUCr export, where the
  explicit namespacing aids journal reviewers. It does not bloat
  day-to-day CIFs.
- Drift between default and IUCr write paths is structurally prevented:
  both paths read the same `Parameter` objects through the same
  `CifHandler` and emit the same DDLm dotted form.

### Trade-offs

- Two write paths to implement and test. Single source of truth (the
  in-memory `Parameter` objects) keeps drift bounded; the per-field
  `iucr_name` plus per-category `IucrCategoryTransformer` mechanism is
  the testable seam.
- Powder Rietveld IUCr CIFs are large because measured and calculated
  profile data is embedded. Acceptable for journal submission; the
  format is what reviewers expect. Largest inspected example:
  `hb8169.cif` at 50K lines (DDL1 form; DDLm form would be of comparable
  size).
- IUCr export is one-way. A user who hand-edits a file in `reports/`
  loses those edits on the next configured report save. Documented as
  such; treat `reports/` as generated output.
- Some external tooling chains (publCIF, journal in-house scripts) may
  still expect DDL1 underscore form. The dotted DDLm form is the
  dictionary spec; if real submissions surface a problem, a downstream
  conversion option can be added on request. Not pre-emptively built in.

### ADRs amended by this ADR

- [`analysis-cif-fit-state.md`](analysis-cif-fit-state.md) — new
  IUCr-named fields added under `_fit_result.*` in the default save
  (R-factors, positive restraint/constraint counts, profile/background
  function descriptors, reflns aggregates). `_fit_result.*` stays
  topology-neutral in `analysis/analysis.cif`; per-topology renaming to
  `_refine_ls.*` / `_pd_proc_ls.*` happens only in the IUCr export
  (§1.2, §3 transformers). A later project-report amendment adds
  `_software.*` as the persisted source for report software provenance.
- [`minimizer-input-output-split.md`](minimizer-input-output-split.md) —
  `_fit_result.*` examples updated for the new fields.
- [`project-facade-and-persistence.md`](project-facade-and-persistence.md)
  — `project.summary` facade slot is removed and replaced by
  `project.report`. The accepted `project.save(report=True)` flag is
  superseded by report booleans for configured reports and
  `project.report.save_cif()` for the IUCr CIF one-off path.
  `summary.cif` is no longer written by default `Project.save()`; the
  slot is repurposed for IUCr / journal report generation in
  `reports/<project>.cif` (see §2). The unimplemented `summary_to_cif()`
  placeholder code path
  ([`project.py:464`](../../../../src/easydiffraction/project/project.py))
  is removed as part of the implementation plan; no summary content
  survives the transition because nothing was being written there in the
  first place.
- [`help-discoverability.md`](help-discoverability.md) —
  `project.summary.help()` is removed from the documented help surface
  and replaced by `project.report.help()` (same responsibilities, new
  slot name). All other entries in the help-surface table are
  unaffected.
- [`project-summary-rendering.md`](project-summary-rendering.md) —
  amends this ADR's report API: public `check()` / `check=True` are
  removed, the `_easydiffraction_software.*` triple is read from
  `analysis.software`, and `_easydiffraction_software.fit_datetime` is
  added when fit provenance has a timestamp. (The write-path gemmi
  validation this ADR introduced was later removed — see the §2.5
  amendment.)

## Open Questions

(None blocking. Dictionary-side ambiguities have all been resolved
against `cif_core.dic` v3.4.0 / `cif_pow.dic` v2.5.0 while authoring the
writer. The runtime gemmi self-check originally described in §2.5 was
removed (see the §2.5 amendment); spec compliance now rests on authoring
discipline plus a final IUCr-server upload before submission.)

## Alternatives Considered

### A. Keep all current tags as-is

Smallest diff. Saved CIFs stay self-contained but cannot be consumed by
external IUCr tooling, and journal submission requires manual
conversion. Defensible only if external CIF interop is never a goal.

### B. Align everything by default (no separate IUCr export)

The previous broad-rewrite extension. Maximises external interop but
pays the UX cost on every saved file — TOF coefficient loops, wavelength
category form for what's morally a scalar, `_easydiffraction_*` prefixes
in `analysis/analysis.cif`. Replaced by the tiered design above.

### C. Adopt IUCr fit-output names only (the original fit-output-only ADR)

Fixes the most visible gap (`_fit_result.*`) but leaves the instrument,
calibration, casing, loop-style, ADP write-side, and journal-submission
decisions unstated. Preserved here as §1.2.

### D. Two write paths, no shared handler mechanism

Implement the IUCr export as a fully separate writer that re-implements
every tag mapping. Doubled maintenance, guaranteed drift. Rejected.

### E. Round-trip-capable IUCr files

The IUCr export could be the source of truth and the default saved files
could be derived from it. Requires retaining `_easydiffraction_*`
extension data through the IUCr writer and parsing it back on load. Adds
round-trip surface area for no day-to-day benefit. Rejected explicitly:
**IUCr export is one-way**.

### F. Multiple IUCr files (one per refined dataset)

The earlier version of §2 proposed `reports/<topology>.cif` files — one
per refinement unit. The IUCr submission convention is one file per
article with multiple data blocks inside (consistent with the corpus).
Rejected.

### G. Emit DDL1 underscore form in the IUCr export

An earlier revision proposed switching the IUCr export to DDL1
underscore form because every inspected corpus file used it. Rejected:
the COMCIFS reference dictionaries are the authoritative spec, and they
declare every item in dotted DDLm form. Corpus files frequently lag the
spec because the tooling that produced them (GSAS-II, Jana2006, SHELX,
etc.) has not yet caught up with the DDLm conversion; their tag style is
**not** a target convention. If a specific journal portal turns out to
reject DDLm input, the dual-style fallback in "Open Questions" covers
it.

## Deferred Work

- **Journal-submission metadata surface.** A future ADR may introduce a
  user-supplied `reports/publ_info.json` / `publ_info.toml` file or a
  Python `project.publication` owner for `_journal.*`, `_publ_*`, and
  `_publ_author.*` entries. V1 deliberately omits those placeholders so
  generated report CIFs stay clean; revisit only with concrete user or
  journal-portal requirements.
- **Crystallographic sanity validation.** The §2.5 validator covers spec
  compliance only. A future pass could integrate IUCr's web checkCIF
  (HTTP POST to the checkCIF endpoint) or bundle a local subset of its
  sanity checks (bond-length plausibility, void detection,
  missed-symmetry, anisotropic-ADP positive-definiteness). Treated as a
  separate concern from dictionary validation.
- **Richer TOF calibration.** `_pd_calib_xcoord.actual_time_of_flight` /
  `nominal_time_of_flight` paired calibration (cif_pow.dic lines 3881
  ff., 4167 ff.) for instruments that distinguish actual vs nominal TOF.
  EasyDiffraction tracks only the polynomial coefficients today.
- **`_atom_type_scat_*` Cromer-Mann and neutron scattering-length
  tables.** Required by GSAS-II-style files (`hb8206.cif`) for
  self-contained reflection calculation, but EasyDiffraction does not
  track these today.
- **`_exptl_crystal.*` single-crystal-specimen metadata** (size, shape,
  density, etc.). The project has no source data for these fields; emit
  as `?` placeholders or skip entirely.
- **`_audit.*` extended audit trail** (`_audit.update_record`,
  `_audit.block_DOI`).
- **mmCIF / other macromolecular-targeting export.** Same handler
  mechanism (`mmcif_name` sibling field) but a different exporter. Not
  on the roadmap.
- **Default-save `_chemical_formula.*` derivation** from `_atom_site`
  rows. No Python field exists today; the IUCr export already derives
  them for `data_global` per §2.3a.
- **imgCIF alignment.** Not on the roadmap; explicitly deferred.
