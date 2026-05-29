# ADR: Python and CIF Category Correspondence

**Status:** Proposed  
**Date:** 2026-05-17

## Context

EasyDiffraction exposes a Python object graph and persists state in CIF
files. The public Python API should be easy for scientists to predict,
while CIF output should remain readable and semantically useful.

The current public root is `Project`, and project-level configuration is
saved in:

```text
project.cif
```

Inside that file, generic category names such as `_info.*`, `_chart.*`,
`_table.*`, and `_verbosity.*` are less ambiguous than they would be in
a single monolithic CIF file. This opens the option of a strict
one-to-one correspondence for project-owned singleton categories:

```text
project.info.title        -> project.cif: _info.title
project.chart.type        -> project.cif: _chart.type
project.table.type        -> project.cif: _table.type
project.verbosity.fit     -> project.cif: _verbosity.fit
```

The design question is whether this rule should be applied only to
project-level configuration, or more broadly across analysis,
experiments, structures, and calculated data.

The accepted project-facade decision keeps `Project` as the public root
and keeps `project.cif` as the singleton project configuration file. It
also keeps `_project.*` as the semantic CIF category for scientific
project information and rejects `_meta.*` for that purpose. This ADR
therefore must not reintroduce the rejected `Workspace` rename,
`workspace.cif`, or `_meta.project_*` tags as incidental cleanup.

## Scope Of Comparison

The comparison below is category-level and public-API oriented. It lists
all currently persisted Python category surfaces found in the source
code, with complete field sets where the category is small and compact
field groups where a CIF loop has many repeated parameters.

Shorthand names such as `analysis`, `experiment`, and `structure` refer
to objects reached from the current `Project` root, for example
`project.analysis`, `project.experiments[name]`, and
`project.structures[name]`.

## Current Persistence Layout

| Current Python surface                           | Current saved location   | Current CIF block form | Notes                                                                                 |
| ------------------------------------------------ | ------------------------ | ---------------------- | ------------------------------------------------------------------------------------- |
| `project.info`, `project.chart`, `project.table` | `project.cif`            | bare categories        | Project-level singleton config.                                                       |
| `project.report`                                 | `project.cif`            | bare category          | Project-owned report-output config; report methods render artifacts under `reports/`. |
| `project.publication`                            | `project.cif`            | bare categories + loop | Journal-submission metadata under `_journal_*` / `_publ_*` categories.                |
| `project.verbosity`                              | `project.cif`            | bare category          | Project-owned fit-output verbosity category backed by `VerbosityEnum`.                |
| `project.structures[name]`                       | `structures/<name>.cif`  | `data_<name>`          | Each structure is one CIF data block.                                                 |
| `project.experiments[name]`                      | `experiments/<name>.cif` | `data_<name>`          | Each experiment is one CIF data block.                                                |
| `project.analysis`                               | `analysis/analysis.cif`  | bare categories        | Loader also accepts legacy root-level `analysis.cif`.                                 |
| `project.summary`                                | `summary.cif`            | placeholder text       | Summary persistence exists as a file but `summary_to_cif()` is not implemented yet.   |

## Current Correspondence

### Project-Level Configuration

| Current Python path          | Current CIF path         | Match? | Notes                                                                                              |
| ---------------------------- | ------------------------ | ------ | -------------------------------------------------------------------------------------------------- |
| `project.info.name`          | `_project.id`            | No     | Python uses user-facing `name`; CIF uses `id`; category is `info` in Python but `_project` in CIF. |
| `project.info.title`         | `_project.title`         | Partly | Field name matches, category name does not.                                                        |
| `project.info.description`   | `_project.description`   | Partly | Field name matches, category name does not.                                                        |
| `project.info.created`       | `_project.created`       | Partly | Field name matches, category name does not.                                                        |
| `project.info.last_modified` | `_project.last_modified` | Partly | Field name matches, category name does not.                                                        |
| `project.info.path`          | none                     | No     | Runtime storage path, not a CIF field.                                                             |
| `project.chart.type`         | `_chart.type`            | Yes    | Direct category-owned selector mapping.                                                            |
| `project.report.*`           | `_report.*`              | Yes    | Direct project-owned report-output configuration mapping.                                          |
| `project.publication.*`      | `_journal.*` / `_publ_*` | Partly | Python keeps one owner with sibling categories; CIF uses journal and publication dictionary names. |
| `project.table.type`         | `_table.type`            | Yes    | Direct category-owned selector mapping.                                                            |
| `project.verbosity.fit`      | `_verbosity.fit`         | Yes    | Direct category and field mapping for fitting process output verbosity.                            |

### Analysis Configuration

| Current Python path                               | Current CIF path                   | Match? | Notes                                                                                            |
| ------------------------------------------------- | ---------------------------------- | ------ | ------------------------------------------------------------------------------------------------ |
| `analysis.minimizer.type`                         | `_minimizer.type`                  | Yes    | Direct category-owned selector mapping.                                                          |
| `analysis.fitting_mode.type`                      | `_fitting_mode.type`               | Yes    | Direct category-owned active-sibling selector mapping.                                           |
| `analysis.joint_fit[experiment_id].experiment_id` | `_joint_fit.experiment_id`         | Yes    | Collection key is also stored as a field.                                                        |
| `analysis.joint_fit[experiment_id].weight`        | `_joint_fit.weight`                | Yes    | Direct field mapping.                                                                            |
| `analysis.sequential_fit.data_dir`                | `_sequential_fit.data_dir`         | Yes    | Direct category mapping.                                                                         |
| `analysis.sequential_fit.file_pattern`            | `_sequential_fit.file_pattern`     | Yes    | Direct category mapping.                                                                         |
| `analysis.sequential_fit.max_workers`             | `_sequential_fit.max_workers`      | Yes    | Direct category mapping.                                                                         |
| `analysis.sequential_fit.chunk_size`              | `_sequential_fit.chunk_size`       | Yes    | Direct category mapping.                                                                         |
| `analysis.sequential_fit.reverse`                 | `_sequential_fit.reverse`          | Yes    | Direct category mapping.                                                                         |
| `analysis.sequential_fit_extract[id].id`          | `_sequential_fit_extract.id`       | Yes    | Direct collection mapping.                                                                       |
| `analysis.sequential_fit_extract[id].target`      | `_sequential_fit_extract.target`   | Yes    | Direct collection mapping.                                                                       |
| `analysis.sequential_fit_extract[id].pattern`     | `_sequential_fit_extract.pattern`  | Yes    | Direct collection mapping.                                                                       |
| `analysis.sequential_fit_extract[id].required`    | `_sequential_fit_extract.required` | Yes    | Direct collection mapping.                                                                       |
| `analysis.aliases[label].label`                   | `_alias.label`                     | Partly | Python collection is plural; CIF row category is singular.                                       |
| `analysis.aliases[label].param_unique_name`       | `_alias.param_unique_name`         | Partly | Python collection is plural; CIF row category is singular.                                       |
| `analysis.constraints[lhs_alias].expression`      | `_constraint.expression`           | Partly | Collection key is derived from the expression; there is no separate `_constraint.lhs_alias` tag. |

### Experiment Configuration

| Current Python path                           | Current CIF path                                                                   | Match? | Notes                                                                            |
| --------------------------------------------- | ---------------------------------------------------------------------------------- | ------ | -------------------------------------------------------------------------------- |
| `experiment.type.sample_form`                 | `_expt_type.sample_form`                                                           | Partly | Python uses the user-facing word `type`; CIF uses abbreviated `_expt_type`.      |
| `experiment.type.beam_mode`                   | `_expt_type.beam_mode`                                                             | Partly | Python uses the user-facing word `type`; CIF uses abbreviated `_expt_type`.      |
| `experiment.type.radiation_probe`             | `_expt_type.radiation_probe`                                                       | Partly | Python uses the user-facing word `type`; CIF uses abbreviated `_expt_type`.      |
| `experiment.type.scattering_type`             | `_expt_type.scattering_type`                                                       | Partly | Python uses the user-facing word `type`; CIF uses abbreviated `_expt_type`.      |
| `experiment.calculator.type`                  | `_calculator.type`                                                                 | Yes    | Direct category-owned backend selector mapping.                                  |
| `experiment.diffrn.ambient_temperature`       | `_diffrn.ambient_temperature`                                                      | Yes    | Direct category mapping.                                                         |
| `experiment.diffrn.ambient_pressure`          | `_diffrn.ambient_pressure`                                                         | Yes    | Direct category mapping.                                                         |
| `experiment.diffrn.ambient_magnetic_field`    | `_diffrn.ambient_magnetic_field`                                                   | Yes    | Direct category mapping.                                                         |
| `experiment.diffrn.ambient_electric_field`    | `_diffrn.ambient_electric_field`                                                   | Yes    | Direct category mapping.                                                         |
| `experiment.instrument.setup_wavelength`      | `_instr.wavelength`                                                                | Partly | Python name exposes setup role; CIF tag uses compact instrument name.            |
| `experiment.instrument.calib_twotheta_offset` | `_instr.2theta_offset`                                                             | Partly | Python name exposes calibration role; CIF tag uses compact instrument name.      |
| `experiment.instrument.setup_twotheta_bank`   | `_instr.2theta_bank`                                                               | Partly | Python name exposes setup role; CIF tag uses compact instrument name.            |
| `experiment.instrument.calib_d_to_tof_offset` | `_instr.d_to_tof_offset`                                                           | Partly | Python name exposes calibration role; CIF tag uses compact instrument name.      |
| `experiment.instrument.calib_d_to_tof_linear` | `_instr.d_to_tof_linear`                                                           | Partly | Python name exposes calibration role; CIF tag uses compact instrument name.      |
| `experiment.instrument.calib_d_to_tof_quad`   | `_instr.d_to_tof_quad`                                                             | Partly | Python name exposes calibration role; CIF tag uses compact instrument name.      |
| `experiment.instrument.calib_d_to_tof_recip`  | `_instr.d_to_tof_recip`                                                            | Partly | Python name exposes calibration role; CIF tag uses compact instrument name.      |
| `experiment.peak.type`                        | `_peak.type`                                                                       | Yes    | Direct category-owned selector mapping.                                          |
| `experiment.peak.broad_gauss_u`               | `_peak.broad_gauss_u`                                                              | Yes    | CWL peak field.                                                                  |
| `experiment.peak.broad_gauss_v`               | `_peak.broad_gauss_v`                                                              | Yes    | CWL peak field.                                                                  |
| `experiment.peak.broad_gauss_w`               | `_peak.broad_gauss_w`                                                              | Yes    | CWL peak field.                                                                  |
| `experiment.peak.broad_lorentz_x`             | `_peak.broad_lorentz_x`                                                            | Yes    | CWL peak field.                                                                  |
| `experiment.peak.broad_lorentz_y`             | `_peak.broad_lorentz_y`                                                            | Yes    | CWL peak field.                                                                  |
| `experiment.peak.asym_empir_1..4`             | `_peak.asym_empir_1..4`                                                            | Yes    | CWL peak field group.                                                            |
| `experiment.peak.asym_fcj_1..2`               | `_peak.asym_fcj_1..2`                                                              | Yes    | CWL peak field group.                                                            |
| `experiment.peak.broad_gauss_sigma_0..2`      | `_peak.gauss_sigma_0..2`                                                           | Partly | Python prefixes the family with `broad_`; CIF tags omit that grouping prefix.    |
| `experiment.peak.broad_lorentz_gamma_0..2`    | `_peak.lorentz_gamma_0..2`                                                         | Partly | Python prefixes the family with `broad_`; CIF tags omit that grouping prefix.    |
| `experiment.peak.exp_rise_alpha_0..1`         | `_peak.rise_alpha_0..1`                                                            | Partly | Python prefixes the family with `exp_`; CIF tags omit that grouping prefix.      |
| `experiment.peak.exp_decay_beta_0..1`         | `_peak.decay_beta_0..1`                                                            | Partly | Python prefixes the family with `exp_`; CIF tags omit that grouping prefix.      |
| `experiment.peak.dexp_*`                      | `_peak.dexp_*`                                                                     | Yes    | TOF double-exponential peak field group.                                         |
| `experiment.peak.damp_q`                      | `_peak.damp_q`                                                                     | Yes    | Total-scattering peak field.                                                     |
| `experiment.peak.broad_q`                     | `_peak.broad_q`                                                                    | Yes    | Total-scattering peak field.                                                     |
| `experiment.peak.cutoff_q`                    | `_peak.cutoff_q`                                                                   | Yes    | Total-scattering peak field.                                                     |
| `experiment.peak.sharp_delta_1`               | `_peak.sharp_delta_1`                                                              | Yes    | Total-scattering peak field.                                                     |
| `experiment.peak.sharp_delta_2`               | `_peak.sharp_delta_2`                                                              | Yes    | Total-scattering peak field.                                                     |
| `experiment.peak.damp_particle_diameter`      | `_peak.damp_particle_diameter`                                                     | Yes    | Total-scattering peak field.                                                     |
| `experiment.background[id].id` line segment   | `_pd_background.id`                                                                | Partly | Python category is `background`; CIF uses powder-background category.            |
| `experiment.background[id].x` line segment    | `_pd_background.line_segment_X` or `_pd_background_line_segment_X`                 | Partly | Python uses compact `x`; CIF tag encodes powder-background line-segment meaning. |
| `experiment.background[id].y` line segment    | `_pd_background.line_segment_intensity` or `_pd_background_line_segment_intensity` | Partly | Python uses compact `y`; CIF tag encodes powder-background line-segment meaning. |
| `experiment.background[id].id` Chebyshev      | `_pd_background.id`                                                                | Partly | Python category is `background`; CIF uses powder-background category.            |
| `experiment.background[id].order` Chebyshev   | `_pd_background.Chebyshev_order`                                                   | Partly | CIF tag encodes polynomial type and uses CIF-style capitalization.               |
| `experiment.background[id].coef` Chebyshev    | `_pd_background.Chebyshev_coef`                                                    | Partly | CIF tag encodes polynomial type and uses CIF-style capitalization.               |
| `experiment.background.type`                  | `_background.type`                                                                 | Yes    | Direct collection-level category-owned selector mapping.                         |
| `experiment.extinction.type`                  | `_extinction.type`                                                                 | Yes    | Direct category-owned selector mapping.                                          |
| `experiment.extinction.model`                 | `_extinction.model`                                                                | Yes    | Direct category mapping.                                                         |
| `experiment.extinction.mosaicity`             | `_extinction.mosaicity`                                                            | Yes    | Direct category mapping.                                                         |
| `experiment.extinction.radius`                | `_extinction.radius`                                                               | Yes    | Direct category mapping.                                                         |
| `experiment.linked_phases[id].id`             | `_pd_phase_block.id`                                                               | Partly | Python name is user-facing; CIF tag follows powder phase-block convention.       |
| `experiment.linked_phases[id].scale`          | `_pd_phase_block.scale`                                                            | Partly | Python name is user-facing; CIF tag follows powder phase-block convention.       |
| `experiment.linked_crystal.id`                | `_sc_crystal_block.id`                                                             | Partly | Python name is user-facing; CIF tag follows single-crystal block convention.     |
| `experiment.linked_crystal.scale`             | `_sc_crystal_block.scale`                                                          | Partly | Python name is user-facing; CIF tag follows single-crystal block convention.     |
| `experiment.excluded_regions[id].id`          | `_excluded_region.id`                                                              | Partly | Python collection is plural; CIF row category is singular.                       |
| `experiment.excluded_regions[id].start`       | `_excluded_region.start`                                                           | Partly | Python collection is plural; CIF row category is singular.                       |
| `experiment.excluded_regions[id].end`         | `_excluded_region.end`                                                             | Partly | Python collection is plural; CIF row category is singular.                       |

### Experiment Data And Calculated Results

| Current Python path                                        | Current CIF path                                                                                                                 | Match? | Notes                                                                |
| ---------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- | ------ | -------------------------------------------------------------------- |
| `experiment.data[point_id].point_id`                       | `_pd_data.point_id`                                                                                                              | Partly | Python row key maps to a powder-data CIF tag.                        |
| `experiment.data[point_id].d_spacing` Bragg powder         | `_pd_proc.d_spacing`                                                                                                             | Partly | Python name is analysis-oriented; CIF tag is processed powder data.  |
| `experiment.data[point_id].intensity_meas` Bragg powder    | `_pd_meas.intensity_total` or `_pd_proc.intensity_norm`                                                                          | Partly | CIF can use measured or processed intensity tags.                    |
| `experiment.data[point_id].intensity_meas_su` Bragg powder | `_pd_meas.intensity_total_su` or `_pd_proc.intensity_norm_su`                                                                    | Partly | CIF can use measured or processed uncertainty tags.                  |
| `experiment.data[point_id].intensity_calc` Bragg powder    | `_pd_calc.intensity_total`                                                                                                       | Partly | Python name is analysis-oriented; CIF tag is calculated powder data. |
| `experiment.data[point_id].intensity_bkg` Bragg powder     | `_pd_calc.intensity_bkg`                                                                                                         | Partly | Python name is analysis-oriented; CIF tag is calculated background.  |
| `experiment.data[point_id].calc_status` Bragg powder       | `_pd_data.refinement_status`                                                                                                     | Partly | Python says calculation status; CIF tag says refinement status.      |
| `experiment.data[point_id].two_theta` Bragg powder         | `_pd_proc.2theta_scan` or `_pd_meas.2theta_scan`                                                                                 | Partly | CIF can use processed or measured x-coordinate tags.                 |
| `experiment.data[point_id].time_of_flight` Bragg powder    | `_pd_meas.time_of_flight`                                                                                                        | Partly | CIF tag is measurement-specific.                                     |
| `experiment.data[point_id].r` total powder                 | `_pd_proc.r`                                                                                                                     | Partly | Current code comments say PDF-specific CIF names are still needed.   |
| `experiment.data[point_id].g_r_meas` total powder          | `_pd_meas.intensity_total`                                                                                                       | Partly | Current code comments say PDF-specific CIF names are still needed.   |
| `experiment.data[point_id].g_r_meas_su` total powder       | `_pd_meas.intensity_total_su`                                                                                                    | Partly | Current code comments say PDF-specific CIF names are still needed.   |
| `experiment.data[point_id].g_r_calc` total powder          | `_pd_calc.intensity_total`                                                                                                       | Partly | Current code comments say PDF-specific CIF names are still needed.   |
| `experiment.data[point_id].calc_status` total powder       | `_pd_data.refinement_status`                                                                                                     | Partly | Current code comments say PDF-specific CIF names are still needed.   |
| `experiment.refln[id]` single crystal                      | `_refln.{id,d_spacing,sin_theta_over_lambda,index_h,index_k,index_l,intensity_meas,intensity_meas_su,intensity_calc,wavelength}` | Yes    | Direct reflection-loop mapping.                                      |
| `experiment.refln[id]` powder calculated reflections       | `_refln.{id,phase_id,d_spacing,sin_theta_over_lambda,index_h,index_k,index_l,f_calc,f_squared_calc,two_theta,time_of_flight}`    | Yes    | Direct calculated-reflection loop mapping.                           |

### Structure Configuration

| Current Python path                               | Current CIF path                                                                                                                                                    | Match? | Notes                                                                             |
| ------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------ | --------------------------------------------------------------------------------- |
| `structure.cell.length_a`                         | `_cell.length_a`                                                                                                                                                    | Yes    | Direct category mapping.                                                          |
| `structure.cell.length_b`                         | `_cell.length_b`                                                                                                                                                    | Yes    | Direct category mapping.                                                          |
| `structure.cell.length_c`                         | `_cell.length_c`                                                                                                                                                    | Yes    | Direct category mapping.                                                          |
| `structure.cell.angle_alpha`                      | `_cell.angle_alpha`                                                                                                                                                 | Yes    | Direct category mapping.                                                          |
| `structure.cell.angle_beta`                       | `_cell.angle_beta`                                                                                                                                                  | Yes    | Direct category mapping.                                                          |
| `structure.cell.angle_gamma`                      | `_cell.angle_gamma`                                                                                                                                                 | Yes    | Direct category mapping.                                                          |
| `structure.space_group.name_h_m`                  | `_space_group.name_H-M_alt`, `_space_group_name_H-M_alt`, `_symmetry.space_group_name_H-M`, or `_symmetry_space_group_name_H-M`                                     | Partly | CIF naming follows crystallographic conventions and supports legacy alternatives. |
| `structure.space_group.it_coordinate_system_code` | `_space_group.IT_coordinate_system_code`, `_space_group_IT_coordinate_system_code`, `_symmetry.IT_coordinate_system_code`, or `_symmetry_IT_coordinate_system_code` | Partly | CIF naming follows crystallographic conventions and supports legacy alternatives. |
| `structure.atom_sites[label].label`               | `_atom_site.label`                                                                                                                                                  | Yes    | Direct row-field mapping.                                                         |
| `structure.atom_sites[label].type_symbol`         | `_atom_site.type_symbol`                                                                                                                                            | Yes    | Direct row-field mapping.                                                         |
| `structure.atom_sites[label].fract_x`             | `_atom_site.fract_x`                                                                                                                                                | Yes    | Direct row-field mapping.                                                         |
| `structure.atom_sites[label].fract_y`             | `_atom_site.fract_y`                                                                                                                                                | Yes    | Direct row-field mapping.                                                         |
| `structure.atom_sites[label].fract_z`             | `_atom_site.fract_z`                                                                                                                                                | Yes    | Direct row-field mapping.                                                         |
| `structure.atom_sites[label].wyckoff_letter`      | `_atom_site.Wyckoff_letter` or `_atom_site.Wyckoff_symbol`                                                                                                          | Partly | CIF uses capitalized/legacy Wyckoff tags.                                         |
| `structure.atom_sites[label].occupancy`           | `_atom_site.occupancy`                                                                                                                                              | Yes    | Direct row-field mapping.                                                         |
| `structure.atom_sites[label].adp_iso`             | `_atom_site.B_iso_or_equiv` or `_atom_site.U_iso_or_equiv`                                                                                                          | No     | Python uses type-neutral ADP name; CIF uses B/U-specific tags.                    |
| `structure.atom_sites[label].adp_type`            | `_atom_site.adp_type`                                                                                                                                               | Yes    | Direct row-field mapping.                                                         |
| `structure.atom_site_aniso[label].label`          | `_atom_site_aniso.label`                                                                                                                                            | Yes    | Direct row-field mapping.                                                         |
| `structure.atom_site_aniso[label].adp_11`         | `_atom_site_aniso.B_11` or `_atom_site_aniso.U_11`                                                                                                                  | No     | Python uses type-neutral ADP name; CIF uses B/U-specific tags.                    |
| `structure.atom_site_aniso[label].adp_22`         | `_atom_site_aniso.B_22` or `_atom_site_aniso.U_22`                                                                                                                  | No     | Python uses type-neutral ADP name; CIF uses B/U-specific tags.                    |
| `structure.atom_site_aniso[label].adp_33`         | `_atom_site_aniso.B_33` or `_atom_site_aniso.U_33`                                                                                                                  | No     | Python uses type-neutral ADP name; CIF uses B/U-specific tags.                    |
| `structure.atom_site_aniso[label].adp_12`         | `_atom_site_aniso.B_12` or `_atom_site_aniso.U_12`                                                                                                                  | No     | Python uses type-neutral ADP name; CIF uses B/U-specific tags.                    |
| `structure.atom_site_aniso[label].adp_13`         | `_atom_site_aniso.B_13` or `_atom_site_aniso.U_13`                                                                                                                  | No     | Python uses type-neutral ADP name; CIF uses B/U-specific tags.                    |
| `structure.atom_site_aniso[label].adp_23`         | `_atom_site_aniso.B_23` or `_atom_site_aniso.U_23`                                                                                                                  | No     | Python uses type-neutral ADP name; CIF uses B/U-specific tags.                    |

### Not Yet Mapped

| Current Python path | Current CIF status    | Notes                                        |
| ------------------- | --------------------- | -------------------------------------------- |
| `project.summary`   | placeholder text only | `summary_to_cif()` currently returns a stub. |

## Decision To Discuss

Adopt a scoped one-to-one rule for project-level configuration:

```text
project.<category>.<field> -> project.cif: _<category>.<field>
```

This ADR does not propose renaming the public root object. The current
root object is already `Project`; the proposal is about category and tag
correspondence inside project-owned singleton configuration.

The accepted baseline is:

```text
project.info.<field> -> project.cif: _project.<field>
```

Future one-to-one correspondence work may still discuss whether the
public identity field should be `name` or `id`, and whether verbosity
should gain additional coverage-specific fields.

Possible strict-correspondence target if a future ADR explicitly changes
the accepted `_project.*` baseline:

| Python path                  | Target CIF path       | Current state                                    |
| ---------------------------- | --------------------- | ------------------------------------------------ |
| `project.info.name`          | `_info.name`          | Currently `_project.id`.                         |
| `project.info.title`         | `_info.title`         | Currently `_project.title`.                      |
| `project.info.description`   | `_info.description`   | Currently `_project.description`.                |
| `project.info.created`       | `_info.created`       | Currently `_project.created`.                    |
| `project.info.last_modified` | `_info.last_modified` | Currently `_project.last_modified`.              |
| `project.chart.type`         | `_chart.type`         | Already matches.                                 |
| `project.table.type`         | `_table.type`         | Already matches.                                 |
| `project.verbosity.fit`      | `_verbosity.fit`      | Implemented direct fit-output verbosity mapping. |

Alternative target if the project identity field should be called `id`
rather than `name`:

```text
project.info.id -> _info.id
```

Do not force strict one-to-one correspondence globally where CIF-domain
names are clearer or where the Python API intentionally abstracts over
CIF details.

## Rationale

### Project-Level Categories Are Repository-Owned

Project-level configuration categories are not external crystallographic
CIF categories. They are EasyDiffraction project-file categories, so the
repository can optimize them for API/persistence symmetry.

### `project.cif` Scopes Generic Categories

`_info.title` is generic in isolation, but inside `project.cif` it reads
as project information. This is similar to `_verbosity.fit`: the file
scope tells the reader this is project-level verbosity, and the field
name identifies the fitting-process coverage.

### The Current `Project` Root Already Matches User Language

The current public root object is already `Project`. Keeping it avoids a
broad user-facing root rename and aligns with scientific workflows where
a project is the container for structures, experiments, analysis, and
saved files.

### `_project.*` Is More Semantic Than `_meta.*`

The project-information category stores the scientific project identity,
title, description, and timestamps. `_project.id` and `_project.title`
say that directly, while `_meta.project_id` and `_meta.project_title`
make the CIF less domain-oriented and repeat the concept in every item
name.

### Scientific CIF/Domain Categories Should Stay Domain-Oriented

For structures, experiments, measured data, and calculated results, many
CIF names are standard or domain-specific. Exact Python mirroring would
make those tags less meaningful to CIF readers and could weaken
compatibility with scientific conventions.

### Some Python Names Are Deliberate Abstractions

Type-neutral ADP parameters and analysis-friendly data names
intentionally do not mirror individual CIF fields. Switchable selectors
are no longer an exception: the accepted
[`switchable-category-owned-selectors.md`](../accepted/switchable-category-owned-selectors.md)
decision uses `category.type` in Python and `_<cat>.type` in CIF across
switchable-category, backend, and active-sibling selector families.
These should remain exceptions unless a separate ADR changes the
underlying API pattern.

## Consequences

### Positive

- Project-level configuration becomes easier to explain and inspect.
- Users can predict project-level CIF tags from Python paths.
- The decision can focus on project-owned singleton config without
  forcing scientific CIF categories to mirror Python convenience names.

### Trade-Offs

- `_info.*` is less self-describing if copied out of `project.cif`.
- Existing `_project.*` project files would need migration or a
  deliberate compatibility decision.
- Persisted verbosity is now a category object. The initial field is
  `project.verbosity.fit`, leaving room for future coverage-specific
  verbosity fields.
- Chart and table renderers are separate selector categories
  (`project.chart.type`, `project.table.type`), so a future collapsed
  renderer setting would need a separate ADR.

## Open Questions

- Should the project identity remain `project.info.name`, or should it
  become `project.info.id` to mirror the saved identifier field?
- Should `project.chart.type` and `project.table.type` remain separate,
  or should the public API and CIF collapse to one renderer field?
- Should `project.verbosity = 'short'` remain as a convenience alias for
  `project.verbosity.fit = 'short'`, or should strict correspondence
  remove the alias?
