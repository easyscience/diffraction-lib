# ADR: Python and CIF Category Correspondence

**Status:** Accepted  
**Date:** 2026-05-17

## Context

[`edstar-project-persistence.md`](edstar-project-persistence.md)
replaces this ADR's scoped Python-to-`project.cif` correspondence with
Python-to-Edifa correspondence for regular project persistence. This
ADR remains historical context for the old CIF layout and for the
reasoning behind previous Python/CIF naming exceptions.

EasyDiffraction exposes a Python object graph and persists state in CIF
files. The public Python API should be easy for scientists to predict,
while CIF output should remain readable and semantically useful.

The current public root is `Project`, and project-level configuration is
saved in:

```text
project.cif
```

Inside that file, project-owned category names such as
`_rendering_plot.*`, `_report.*`, `_structure_view.*`,
`_structure_style.*`, and `_verbosity.*` are less ambiguous than they
would be in a single monolithic CIF file. This opens the option of a
scoped one-to-one correspondence for EasyDiffraction-owned singleton
configuration categories:

```text
project.rendering_plot.type     -> project.cif: _rendering_plot.type
project.report.cif              -> project.cif: _report.cif
project.structure_view.range_a_min -> project.cif: _structure_view.range_a_min
project.structure_style.atom_view  -> project.cif: _structure_style.atom_view
project.verbosity.fit           -> project.cif: _verbosity.fit
```

The design question is whether this rule should be applied only to
project-level configuration, or more broadly across analysis,
experiments, structures, and calculated data.

The accepted project-facade decision keeps `Project` as the public root
and keeps `project.cif` as the singleton project configuration file. It
also keeps `_project.*` as the semantic CIF category for scientific
project information and rejects `_meta.*` for that purpose. This ADR
therefore does **not** reintroduce the rejected `Workspace` rename,
`workspace.cif`, `_meta.project_*` tags, or a broad `_info.*` rewrite as
incidental cleanup.

The accepted project-summary-rendering ADR also rejected a v1
`project.publication` owner. Journal, author, publication-body, and
powder-measurement author metadata are not represented in code, are not
persisted in `project.cif`, and are not emitted as empty report-CIF
placeholders. This ADR records that as an intentional correspondence
gap, not as a missing mapping.

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

| Current Python surface                                                                                                                                                                         | Current saved location   | Current CIF block form                    | Notes                                                                        |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------ | ----------------------------------------- | ---------------------------------------------------------------------------- |
| `project.info`, `project.rendering_plot`, `project.report`, `project.rendering_table`, `project.rendering_structure`, `project.structure_view`, `project.structure_style`, `project.verbosity` | `project.cif`            | bare categories                           | Project-level singleton config.                                              |
| `project.structures[name]`                                                                                                                                                                     | `structures/<name>.cif`  | `data_<name>`                             | Each structure is one CIF data block.                                        |
| `project.experiments[name]`                                                                                                                                                                    | `experiments/<name>.cif` | `data_<name>`                             | Each experiment is one CIF data block.                                       |
| `project.analysis`                                                                                                                                                                             | `analysis/analysis.cif`  | bare categories                           | Loader also accepts legacy root-level `analysis.cif`.                        |
| `project.report.save_*()` / `project.report.{cif,html,tex,pdf}`                                                                                                                                | `reports/`               | multi-datablock CIF or rendered artifacts | Derived report outputs; generated only when configured or called explicitly. |

## Current Correspondence

### Project-Level Configuration

| Current Python path                              | Current CIF path                          | Match? | Notes                                                                               |
| ------------------------------------------------ | ----------------------------------------- | ------ | ----------------------------------------------------------------------------------- |
| `project.info.name`                              | `_project.id`                             | No     | Accepted exception: Python uses user-facing `name`; CIF uses semantic project `id`. |
| `project.info.title`                             | `_project.title`                          | Partly | Accepted exception: field name matches, category name is semantic `_project`.       |
| `project.info.description`                       | `_project.description`                    | Partly | Accepted exception: field name matches, category name is semantic `_project`.       |
| `project.info.created`                           | `_project.created`                        | Partly | Accepted exception: field name matches, category name is semantic `_project`.       |
| `project.info.last_modified`                     | `_project.last_modified`                  | Partly | Accepted exception: field name matches, category name is semantic `_project`.       |
| `project.info.path`                              | none                                      | No     | Runtime storage path, not a CIF field.                                              |
| `project.rendering_plot.type`                    | `_rendering_plot.type`                    | Yes    | Direct category-owned selector mapping.                                             |
| `project.report.cif`                             | `_report.cif`                             | Yes    | Direct project-owned report-output configuration mapping.                           |
| `project.report.html`                            | `_report.html`                            | Yes    | Direct project-owned report-output configuration mapping.                           |
| `project.report.tex`                             | `_report.tex`                             | Yes    | Direct project-owned report-output configuration mapping.                           |
| `project.report.pdf`                             | `_report.pdf`                             | Yes    | Direct project-owned report-output configuration mapping.                           |
| `project.report.html_offline`                    | `_report.html_offline`                    | Yes    | Direct project-owned report-output configuration mapping.                           |
| `project.rendering_table.type`                   | `_rendering_table.type`                   | Yes    | Direct category-owned selector mapping.                                             |
| `project.rendering_structure.type`               | `_rendering_structure.type`               | Yes    | Direct category-owned selector mapping.                                             |
| `project.structure_view.show_labels`             | `_structure_view.show_labels`             | Yes    | Direct project-owned structure-view state mapping.                                  |
| `project.structure_view.show_moments`            | `_structure_view.show_moments`            | Yes    | Direct project-owned structure-view state mapping.                                  |
| `project.structure_view.range_{a,b,c}_{min,max}` | `_structure_view.range_{a,b,c}_{min,max}` | Yes    | Six scalar bounds; direct project-owned structure-view state mapping.               |
| `project.structure_style.atom_view`              | `_structure_style.atom_view`              | Yes    | Direct project-owned structure-style value selector mapping.                        |
| `project.structure_style.color_scheme`           | `_structure_style.color_scheme`           | Yes    | Direct project-owned structure-style value selector mapping.                        |
| `project.structure_style.adp_probability`        | `_structure_style.adp_probability`        | Yes    | Direct project-owned structure-style numeric setting.                               |
| `project.structure_style.atom_scale`             | `_structure_style.atom_scale`             | Yes    | Direct project-owned structure-style numeric setting.                               |
| `project.verbosity.fit`                          | `_verbosity.fit`                          | Yes    | Direct category and field mapping for fitting process output verbosity.             |
| `project.verbosity = 'short'`                    | `_verbosity.fit`                          | Alias  | Convenience setter only; canonical persisted path remains `project.verbosity.fit`.  |

### Analysis Configuration

| Current Python path                               | Current CIF path                   | Match? | Notes                                                                                               |
| ------------------------------------------------- | ---------------------------------- | ------ | --------------------------------------------------------------------------------------------------- |
| `analysis.minimizer.type`                         | `_minimizer.type`                  | Yes    | Direct category-owned selector mapping.                                                             |
| `analysis.fitting_mode.type`                      | `_fitting_mode.type`               | Yes    | Direct category-owned active-sibling selector mapping.                                              |
| `analysis.fit_result.*`                           | `_fit_result.*`                    | Yes    | Direct category mapping for scalar fit-result state; IUCr report export may use transformed tags.   |
| `analysis.fit_parameters[param].*`                | `_fit_parameter.*`                 | Yes    | Direct loop mapping for persisted per-parameter fit state.                                          |
| `analysis.fit_parameter_correlations[id].*`       | `_fit_parameter_correlation.*`     | Yes    | Direct loop mapping for deterministic and posterior correlation summaries.                          |
| `analysis.joint_fit[experiment_id].experiment_id` | `_joint_fit.experiment_id`         | Yes    | Collection key is also stored as a field.                                                           |
| `analysis.joint_fit[experiment_id].weight`        | `_joint_fit.weight`                | Yes    | Direct field mapping.                                                                               |
| `analysis.software.*`                             | `_software.*`                      | Yes    | Direct analysis-tier software provenance mapping stamped at fit time.                               |
| `analysis.sequential_fit.data_dir`                | `_sequential_fit.data_dir`         | Yes    | Direct category mapping.                                                                            |
| `analysis.sequential_fit.file_pattern`            | `_sequential_fit.file_pattern`     | Yes    | Direct category mapping.                                                                            |
| `analysis.sequential_fit.max_workers`             | `_sequential_fit.max_workers`      | Yes    | Direct category mapping.                                                                            |
| `analysis.sequential_fit.chunk_size`              | `_sequential_fit.chunk_size`       | Yes    | Direct category mapping.                                                                            |
| `analysis.sequential_fit.reverse`                 | `_sequential_fit.reverse`          | Yes    | Direct category mapping.                                                                            |
| `analysis.sequential_fit_extract[id].id`          | `_sequential_fit_extract.id`       | Yes    | Direct collection mapping.                                                                          |
| `analysis.sequential_fit_extract[id].target`      | `_sequential_fit_extract.target`   | Yes    | Direct collection mapping.                                                                          |
| `analysis.sequential_fit_extract[id].pattern`     | `_sequential_fit_extract.pattern`  | Yes    | Direct collection mapping.                                                                          |
| `analysis.sequential_fit_extract[id].required`    | `_sequential_fit_extract.required` | Yes    | Direct collection mapping.                                                                          |
| `analysis.aliases[label].label`                   | `_alias.label`                     | Partly | Python collection is plural; CIF row category is singular.                                          |
| `analysis.aliases[label].parameter_unique_name`   | `_alias.parameter_unique_name`     | Partly | Python collection is plural; CIF row category is singular.                                          |
| `analysis.constraints[id].id`                     | `_constraint.id`                   | Yes    | Direct explicit row-key mapping; older CIFs may backfill the id from the expression left-hand side. |
| `analysis.constraints[id].expression`             | `_constraint.expression`           | Yes    | Direct row-field mapping; `lhs_alias` and `rhs_expr` are derived Python helpers.                    |

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

| Current Python path                          | Current CIF path                                           | Match? | Notes                                                                                                                                  |
| -------------------------------------------- | ---------------------------------------------------------- | ------ | -------------------------------------------------------------------------------------------------------------------------------------- |
| `structure.cell.length_a`                    | `_cell.length_a`                                           | Yes    | Direct category mapping.                                                                                                               |
| `structure.cell.length_b`                    | `_cell.length_b`                                           | Yes    | Direct category mapping.                                                                                                               |
| `structure.cell.length_c`                    | `_cell.length_c`                                           | Yes    | Direct category mapping.                                                                                                               |
| `structure.cell.angle_alpha`                 | `_cell.angle_alpha`                                        | Yes    | Direct category mapping.                                                                                                               |
| `structure.cell.angle_beta`                  | `_cell.angle_beta`                                         | Yes    | Direct category mapping.                                                                                                               |
| `structure.cell.angle_gamma`                 | `_cell.angle_gamma`                                        | Yes    | Direct category mapping.                                                                                                               |
| `structure.space_group.name_h_m`             | `_space_group.name_H-M_alt`                                | Partly | Default write uses dictionary-canonical casing; legacy `_space_group_name_H-M_alt` and `_symmetry*` alternatives are accepted on read. |
| `structure.space_group.coord_system_code`    | `_space_group.IT_coordinate_system_code`                   | Partly | Default write uses dictionary-canonical casing; legacy underscore-form and `_symmetry*` alternatives are accepted on read.             |
| `structure.atom_sites[label].label`          | `_atom_site.label`                                         | Yes    | Direct row-field mapping.                                                                                                              |
| `structure.atom_sites[label].type_symbol`    | `_atom_site.type_symbol`                                   | Yes    | Direct row-field mapping.                                                                                                              |
| `structure.atom_sites[label].fract_x`        | `_atom_site.fract_x`                                       | Yes    | Direct row-field mapping.                                                                                                              |
| `structure.atom_sites[label].fract_y`        | `_atom_site.fract_y`                                       | Yes    | Direct row-field mapping.                                                                                                              |
| `structure.atom_sites[label].fract_z`        | `_atom_site.fract_z`                                       | Yes    | Direct row-field mapping.                                                                                                              |
| `structure.atom_sites[label].wyckoff_letter` | `_atom_site.Wyckoff_symbol`                                | Partly | Default write uses dictionary-canonical tag; legacy `_atom_site.Wyckoff_letter` is accepted on read.                                   |
| `structure.atom_sites[label].occupancy`      | `_atom_site.occupancy`                                     | Yes    | Direct row-field mapping.                                                                                                              |
| `structure.atom_sites[label].adp_iso`        | `_atom_site.B_iso_or_equiv` or `_atom_site.U_iso_or_equiv` | No     | Python uses type-neutral ADP name; CIF uses B/U-specific tags.                                                                         |
| `structure.atom_sites[label].adp_type`       | `_atom_site.ADP_type`                                      | Partly | Default write uses dictionary-canonical capitalization; legacy `_atom_site.adp_type` is accepted on read.                              |
| `structure.atom_site_aniso[label].label`     | `_atom_site_aniso.label`                                   | Yes    | Direct row-field mapping.                                                                                                              |
| `structure.atom_site_aniso[label].adp_11`    | `_atom_site_aniso.B_11` or `_atom_site_aniso.U_11`         | No     | Python uses type-neutral ADP name; CIF uses B/U-specific tags.                                                                         |
| `structure.atom_site_aniso[label].adp_22`    | `_atom_site_aniso.B_22` or `_atom_site_aniso.U_22`         | No     | Python uses type-neutral ADP name; CIF uses B/U-specific tags.                                                                         |
| `structure.atom_site_aniso[label].adp_33`    | `_atom_site_aniso.B_33` or `_atom_site_aniso.U_33`         | No     | Python uses type-neutral ADP name; CIF uses B/U-specific tags.                                                                         |
| `structure.atom_site_aniso[label].adp_12`    | `_atom_site_aniso.B_12` or `_atom_site_aniso.U_12`         | No     | Python uses type-neutral ADP name; CIF uses B/U-specific tags.                                                                         |
| `structure.atom_site_aniso[label].adp_13`    | `_atom_site_aniso.B_13` or `_atom_site_aniso.U_13`         | No     | Python uses type-neutral ADP name; CIF uses B/U-specific tags.                                                                         |
| `structure.atom_site_aniso[label].adp_23`    | `_atom_site_aniso.B_23` or `_atom_site_aniso.U_23`         | No     | Python uses type-neutral ADP name; CIF uses B/U-specific tags.                                                                         |

### Not Represented In V1

| Candidate surface        | Current CIF status | Notes                                                                                                                                                                                                             |
| ------------------------ | ------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `project.summary`        | removed            | Replaced by `project.report`; no `summary.cif` placeholder is written.                                                                                                                                            |
| `project.publication`    | none               | Rejected for v1 by the accepted project-summary-rendering ADR.                                                                                                                                                    |
| journal/publication tags | not emitted        | `_journal.*`, `_journal_date.*`, `_journal_coeditor.*`, `_publ_contact_author.*`, `_publ_author.*`, `_publ_body.*`, and `_pd_meas.info_author_*` placeholders are deferred and intentionally omitted while empty. |

## Decision

Adopt a scoped one-to-one rule for EasyDiffraction-owned project-level
singleton configuration:

```text
project.<category>.<field> -> project.cif: _<category>.<field>
```

The rule applies to:

- `project.rendering_plot.type -> _rendering_plot.type`
- `project.report.{cif,html,tex,pdf,html_offline} -> _report.*`
- `project.rendering_table.type -> _rendering_table.type`
- `project.rendering_structure.type -> _rendering_structure.type`
- `project.structure_view.* -> _structure_view.*`
- `project.structure_style.* -> _structure_style.*`
- `project.verbosity.fit -> _verbosity.fit`

Keep `project.info` as the accepted exception:

```text
project.info.name -> _project.id
project.info.title -> _project.title
project.info.description -> _project.description
project.info.created -> _project.created
project.info.last_modified -> _project.last_modified
```

The exception is deliberate. `_project.*` is the semantic CIF category
for scientific project identity in this project file, and `name` remains
the user-facing Python property. This ADR does not rename `name` to
`id`, does not rename `_project.*` to `_info.*`, and does not add an
`_info.*` compatibility layer.

Do not force strict one-to-one correspondence globally. Analysis,
experiment, structure, measured-data, calculated-data, and report-export
categories may keep CIF-domain names where those names are clearer,
dictionary-aligned, or intentionally different from Python convenience
names.

Do not add a v1 `project.publication` owner or empty publication tags to
make the correspondence table appear complete. Publication metadata is a
future feature with its own sourcing and completeness questions.

## Rationale

### Project-Level Categories Are Repository-Owned

Project-level configuration categories are not external crystallographic
CIF categories. They are EasyDiffraction project-file categories, so the
repository can optimize them for API/persistence symmetry.

### `project.cif` Scopes Project-Owned Categories

`_report.cif`, `_structure_view.show_labels`, and `_verbosity.fit` are
generic in isolation, but inside `project.cif` they read as
project-level report, structure-view, and verbosity configuration. The
file scope supplies the project root; the category and field names
identify the specific setting.

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

### `project.info` Is A Deliberate Exception

`project.info` is the user-facing Python grouping, but `_project.*` is
the accepted CIF grouping for project identity. Preserving this
exception avoids a beta-period churn-only rename from `name` to `id` in
Python and avoids a persistence migration from `_project.*` to `_info.*`
without a scientific benefit.

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

### Convenience Aliases Do Not Define Persistence

`project.verbosity = 'short'` remains acceptable as a user-facing
shortcut because it writes the canonical `project.verbosity.fit` value.
The persistence contract is still the category/field path, not every
convenience setter that happens to reach it.

## Consequences

### Positive

- Project-level configuration becomes easier to explain and inspect.
- Users can predict project-level CIF tags from Python paths.
- The decision can focus on project-owned singleton config without
  forcing scientific CIF categories to mirror Python convenience names.
- The clean-report decision remains intact: empty journal/publication
  placeholders stay out of both `project.cif` and generated report CIFs.

### Trade-Offs

- `project.info` does not follow the strict category-name rule; this
  exception must be explained alongside the other project config.
- Future publication metadata needs a separate ADR rather than a quiet
  extension of this correspondence table.
- Persisted verbosity remains a category object. The initial field is
  `project.verbosity.fit`, leaving room for future coverage-specific
  verbosity fields.
- Chart and table renderers are separate selector categories
  (`project.rendering_plot.type`, `project.rendering_table.type`), so a
  future collapsed renderer setting would need a separate ADR.

## Open Questions

None for this ADR.
