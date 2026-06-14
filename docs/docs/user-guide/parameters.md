# Parameters

The data analysis process, introduced in the [Concept](concept.md)
section, uses parameters to describe structures, experiments, and the
analysis state.

Each parameter has:

- a Python access path used in notebooks and scripts,
- an Edifa key used when EasyDiffraction saves a project, and
- where applicable, a CIF key used for importing crystallographic data
  or writing IUCr/pdCIF reports.

Edifa is the regular EasyDiffraction project persistence format. CIF
remains important for crystallographic input and for strict report
exports. The tables below therefore separate code access, Edifa keys,
and CIF keys instead of treating one name as universal.

## Parameter Attributes

Parameters in EasyDiffraction are objects. Alongside `name` and `value`,
they can carry attributes such as uncertainty, unit, minimum and maximum
allowed values, and fit bounds. The most important day-to-day attribute
is `free`, which controls whether a parameter is refined during fitting.
It is `False` by default.

Users normally access parameters through top-level objects such as
`project`, `structures`, and `experiments`; parameters are created when
the project objects are created or loaded.

!!! warning "Important"

    Parameters are accessed through their parent objects. For example, if a
    structure has the ID `nacl`, the space-group name is accessed as:

    ```python
    project.structures['nacl'].space_group.name_h_m
    ```

For compactness, the code tables show only the last part of the access
path, such as `space_group.name_h_m`.

## Structure Parameters

### Crystal Structure Parameters

[pd-neut-cwl][3]{:.label-experiment}
[pd-neut-tof][3]{:.label-experiment} [pd-xray][3]{:.label-experiment}
[sc-neut-cwl][3]{:.label-experiment}

=== "How to access in the code"

    | Category | Parameter | How to access in the code |
    | --- | --- | --- |
    | :material-space-station: [space_group][space_group] | :material-tag: [name_h_m](parameters/structure/space_group.md#space-group-name-h-m) | space_group.name_h_m |
    |  | :material-numeric: [coord_system_code](parameters/structure/space_group.md#space-group-coord-system-code) | space_group.coord_system_code |
    | :material-cube-outline: [cell][cell] | :material-ruler: [length_a](parameters/structure/cell.md#cell-length-a) | cell.length_a |
    |  | :material-ruler: [length_b](parameters/structure/cell.md#cell-length-b) | cell.length_b |
    |  | :material-ruler: [length_c](parameters/structure/cell.md#cell-length-c) | cell.length_c |
    |  | :material-angle-acute: [angle_alpha](parameters/structure/cell.md#cell-angle-alpha) | cell.angle_alpha |
    |  | :material-angle-acute: [angle_beta](parameters/structure/cell.md#cell-angle-beta) | cell.angle_beta |
    |  | :material-angle-acute: [angle_gamma](parameters/structure/cell.md#cell-angle-gamma) | cell.angle_gamma |
    | :material-atom: [atom_site][atom_site] | :material-tag: [id](parameters/structure/atom_site.md#atom-site-id) | atom_sites['ID'].id |
    |  | :material-periodic-table: [type_symbol](parameters/structure/atom_site.md#atom-site-type-symbol) | atom_sites['ID'].type_symbol |
    |  | :material-map-marker: [fract_x](parameters/structure/atom_site.md#atom-site-fract-x) | atom_sites['ID'].fract_x |
    |  | :material-map-marker: [fract_y](parameters/structure/atom_site.md#atom-site-fract-y) | atom_sites['ID'].fract_y |
    |  | :material-map-marker: [fract_z](parameters/structure/atom_site.md#atom-site-fract-z) | atom_sites['ID'].fract_z |
    |  | :material-format-color-fill: [occupancy](parameters/structure/atom_site.md#atom-site-occupancy) | atom_sites['ID'].occupancy |
    |  | :material-cursor-move: [adp_type](parameters/structure/atom_site.md#atom-site-adp-type) | atom_sites['ID'].adp_type |
    |  | :material-cursor-move: [adp_iso](parameters/structure/atom_site.md#atom-site-adp-iso) | atom_sites['ID'].adp_iso |
    |  | :material-reflect-horizontal: [multiplicity](parameters/structure/atom_site.md#atom-site-multiplicity) | atom_sites['ID'].multiplicity |
    |  | :material-reflect-horizontal: [wyckoff_letter](parameters/structure/atom_site.md#atom-site-wyckoff-letter) | atom_sites['ID'].wyckoff_letter |

=== "Keys in Edifa"

    | Category | Parameter | Key in Edifa |
    | --- | --- | --- |
    | :material-space-station: [space_group][space_group] | :material-tag: [name_h_m](parameters/structure/space_group.md#space-group-name-h-m) | `_space_group.name_h_m` |
    |  | :material-numeric: [coord_system_code](parameters/structure/space_group.md#space-group-coord-system-code) | `_space_group.coord_system_code` |
    | :material-cube-outline: [cell][cell] | :material-ruler: [length_a](parameters/structure/cell.md#cell-length-a) | `_cell.length_a` |
    |  | :material-ruler: [length_b](parameters/structure/cell.md#cell-length-b) | `_cell.length_b` |
    |  | :material-ruler: [length_c](parameters/structure/cell.md#cell-length-c) | `_cell.length_c` |
    |  | :material-angle-acute: [angle_alpha](parameters/structure/cell.md#cell-angle-alpha) | `_cell.angle_alpha` |
    |  | :material-angle-acute: [angle_beta](parameters/structure/cell.md#cell-angle-beta) | `_cell.angle_beta` |
    |  | :material-angle-acute: [angle_gamma](parameters/structure/cell.md#cell-angle-gamma) | `_cell.angle_gamma` |
    | :material-atom: [atom_site][atom_site] | :material-tag: [id](parameters/structure/atom_site.md#atom-site-id) | `_atom_site.id` |
    |  | :material-periodic-table: [type_symbol](parameters/structure/atom_site.md#atom-site-type-symbol) | `_atom_site.type_symbol` |
    |  | :material-map-marker: [fract_x](parameters/structure/atom_site.md#atom-site-fract-x) | `_atom_site.fract_x` |
    |  | :material-map-marker: [fract_y](parameters/structure/atom_site.md#atom-site-fract-y) | `_atom_site.fract_y` |
    |  | :material-map-marker: [fract_z](parameters/structure/atom_site.md#atom-site-fract-z) | `_atom_site.fract_z` |
    |  | :material-format-color-fill: [occupancy](parameters/structure/atom_site.md#atom-site-occupancy) | `_atom_site.occupancy` |
    |  | :material-cursor-move: [adp_type](parameters/structure/atom_site.md#atom-site-adp-type) | `_atom_site.adp_type` |
    |  | :material-cursor-move: [adp_iso](parameters/structure/atom_site.md#atom-site-adp-iso) | `_atom_site.adp_iso` |
    |  | :material-reflect-horizontal: [multiplicity](parameters/structure/atom_site.md#atom-site-multiplicity) | `_atom_site.multiplicity` |
    |  | :material-reflect-horizontal: [wyckoff_letter](parameters/structure/atom_site.md#atom-site-wyckoff-letter) | `_atom_site.wyckoff_letter` |

=== "Keys in CIF"

    | Category | Parameter | Key in CIF | CIF dictionary |
    | --- | --- | --- | --- |
    | :material-space-station: [space_group][space_group] | :material-tag: [name_h_m](parameters/structure/space_group.md#space-group-name-h-m) | `_space_group.name_H-M_alt` | [coreCIF][1]{:.label-cif} |
    |  | :material-numeric: [coord_system_code](parameters/structure/space_group.md#space-group-coord-system-code) | `_space_group.IT_coordinate_system_code` | [coreCIF][1]{:.label-cif} |
    | :material-cube-outline: [cell][cell] | :material-ruler: [length_a](parameters/structure/cell.md#cell-length-a) | `_cell.length_a` | [coreCIF][1]{:.label-cif} |
    |  | :material-ruler: [length_b](parameters/structure/cell.md#cell-length-b) | `_cell.length_b` | [coreCIF][1]{:.label-cif} |
    |  | :material-ruler: [length_c](parameters/structure/cell.md#cell-length-c) | `_cell.length_c` | [coreCIF][1]{:.label-cif} |
    |  | :material-angle-acute: [angle_alpha](parameters/structure/cell.md#cell-angle-alpha) | `_cell.angle_alpha` | [coreCIF][1]{:.label-cif} |
    |  | :material-angle-acute: [angle_beta](parameters/structure/cell.md#cell-angle-beta) | `_cell.angle_beta` | [coreCIF][1]{:.label-cif} |
    |  | :material-angle-acute: [angle_gamma](parameters/structure/cell.md#cell-angle-gamma) | `_cell.angle_gamma` | [coreCIF][1]{:.label-cif} |
    | :material-atom: [atom_site][atom_site] | :material-tag: [id](parameters/structure/atom_site.md#atom-site-id) | `_atom_site.label` | [coreCIF][1]{:.label-cif} |
    |  | :material-periodic-table: [type_symbol](parameters/structure/atom_site.md#atom-site-type-symbol) | `_atom_site.type_symbol` | [coreCIF][1]{:.label-cif} |
    |  | :material-map-marker: [fract_x](parameters/structure/atom_site.md#atom-site-fract-x) | `_atom_site.fract_x` | [coreCIF][1]{:.label-cif} |
    |  | :material-map-marker: [fract_y](parameters/structure/atom_site.md#atom-site-fract-y) | `_atom_site.fract_y` | [coreCIF][1]{:.label-cif} |
    |  | :material-map-marker: [fract_z](parameters/structure/atom_site.md#atom-site-fract-z) | `_atom_site.fract_z` | [coreCIF][1]{:.label-cif} |
    |  | :material-format-color-fill: [occupancy](parameters/structure/atom_site.md#atom-site-occupancy) | `_atom_site.occupancy` | [coreCIF][1]{:.label-cif} |
    |  | :material-cursor-move: [adp_type](parameters/structure/atom_site.md#atom-site-adp-type) | `_atom_site.ADP_type` | [coreCIF][1]{:.label-cif} |
    |  | :material-cursor-move: [adp_iso](parameters/structure/atom_site.md#atom-site-adp-iso) | `_atom_site.B_iso_or_equiv` | [coreCIF][1]{:.label-cif} |
    |  | :material-reflect-horizontal: [multiplicity](parameters/structure/atom_site.md#atom-site-multiplicity) | `_atom_site.site_symmetry_multiplicity` | [coreCIF][1]{:.label-cif} |
    |  | :material-reflect-horizontal: [wyckoff_letter](parameters/structure/atom_site.md#atom-site-wyckoff-letter) | `_atom_site.Wyckoff_symbol` | [coreCIF][1]{:.label-cif} |

## Experiment Parameters

### Common Parameters

[pd-neut-cwl][3]{:.label-experiment}
[pd-neut-tof][3]{:.label-experiment} [pd-xray][3]{:.label-experiment}
[sc-neut-cwl][3]{:.label-experiment}

=== "How to access in the code"

    | Category | Parameter | How to access in the code |
    | --- | --- | --- |
    | :material-flask: [experiment_type][experiment_type] | :material-sawtooth-wave: [beam_mode](parameters/experiment/experiment_type.md#experiment-type-beam-mode) | experiment_type.beam_mode |
    |  | :material-radiology-box-outline: [radiation_probe](parameters/experiment/experiment_type.md#experiment-type-radiation-probe) | experiment_type.radiation_probe |
    |  | :material-diamond-stone: [sample_form](parameters/experiment/experiment_type.md#experiment-type-sample-form) | experiment_type.sample_form |
    |  | :material-chart-bell-curve: [scattering_type](parameters/experiment/experiment_type.md#experiment-type-scattering-type) | experiment_type.scattering_type |

=== "Keys in Edifa"

    | Category | Parameter | Key in Edifa |
    | --- | --- | --- |
    | :material-flask: [experiment_type][experiment_type] | :material-sawtooth-wave: [beam_mode](parameters/experiment/experiment_type.md#experiment-type-beam-mode) | `_experiment_type.beam_mode` |
    |  | :material-radiology-box-outline: [radiation_probe](parameters/experiment/experiment_type.md#experiment-type-radiation-probe) | `_experiment_type.radiation_probe` |
    |  | :material-diamond-stone: [sample_form](parameters/experiment/experiment_type.md#experiment-type-sample-form) | `_experiment_type.sample_form` |
    |  | :material-chart-bell-curve: [scattering_type](parameters/experiment/experiment_type.md#experiment-type-scattering-type) | `_experiment_type.scattering_type` |

=== "Keys in CIF"

    | Category | Parameter | Key in CIF | CIF dictionary |
    | --- | --- | --- | --- |
    | :material-flask: [experiment_type][experiment_type] | :material-sawtooth-wave: [beam_mode](parameters/experiment/experiment_type.md#experiment-type-beam-mode) | `_easydiffraction_experiment_type.beam_mode` | [edifaCIF][0]{:.label-cif} |
    |  | :material-radiology-box-outline: [radiation_probe](parameters/experiment/experiment_type.md#experiment-type-radiation-probe) | `_easydiffraction_experiment_type.radiation_probe` | [edifaCIF][0]{:.label-cif} |
    |  | :material-diamond-stone: [sample_form](parameters/experiment/experiment_type.md#experiment-type-sample-form) | `_easydiffraction_experiment_type.sample_form` | [edifaCIF][0]{:.label-cif} |
    |  | :material-chart-bell-curve: [scattering_type](parameters/experiment/experiment_type.md#experiment-type-scattering-type) | `_easydiffraction_experiment_type.scattering_type` | [edifaCIF][0]{:.label-cif} |

### Standard Powder Diffraction

[pd-neut-cwl][3]{:.label-experiment}
[pd-neut-tof][3]{:.label-experiment} [pd-xray][3]{:.label-experiment}

=== "How to access in the code"

    | Category | Parameter | How to access in the code |
    | --- | --- | --- |
    | :material-waveform: [background][background] | :material-arrow-collapse-right: [position](parameters/experiment/background.md#background-position) | background.position |
    |  | :material-arrow-collapse-up: [intensity](parameters/experiment/background.md#background-intensity) | background.intensity |
    |  | :material-format-superscript: [order](parameters/experiment/background.md#background-order) | background.order |
    |  | :material-arrow-collapse-up: [coef](parameters/experiment/background.md#background-coef) | background.coef |
    | :material-puzzle: [linked_structure][linked_structure] | :material-identifier: [structure_id](parameters/experiment/linked_structure.md#linked-structure-structure-id) | linked_structures['ID'].structure_id |
    |  | :material-scale: [scale](parameters/experiment/linked_structure.md#linked-structure-scale) | linked_structures['ID'].scale |
    | :material-compass-outline: [preferred_orientation][preferred_orientation] | :material-identifier: [structure_id](parameters/experiment/preferred_orientation.md#preferred-orientation-structure-id) | preferred_orientation['ID'].structure_id |
    |  | :material-chart-bell-curve-cumulative: [march_r](parameters/experiment/preferred_orientation.md#preferred-orientation-march-r) | preferred_orientation['ID'].march_r |
    |  | :material-shuffle-variant: [march_random_fract](parameters/experiment/preferred_orientation.md#preferred-orientation-march-random-fract) | preferred_orientation['ID'].march_random_fract |
    |  | :material-axis-arrow: [index_h](parameters/experiment/preferred_orientation.md#preferred-orientation-index-h) | preferred_orientation['ID'].index_h |
    |  | :material-axis-arrow: [index_k](parameters/experiment/preferred_orientation.md#preferred-orientation-index-k) | preferred_orientation['ID'].index_k |
    |  | :material-axis-arrow: [index_l](parameters/experiment/preferred_orientation.md#preferred-orientation-index-l) | preferred_orientation['ID'].index_l |

=== "Keys in Edifa"

    | Category | Parameter | Key in Edifa |
    | --- | --- | --- |
    | :material-waveform: [background][background] | :material-arrow-collapse-right: [position](parameters/experiment/background.md#background-position) | `_background.position` |
    |  | :material-arrow-collapse-up: [intensity](parameters/experiment/background.md#background-intensity) | `_background.intensity` |
    |  | :material-format-superscript: [order](parameters/experiment/background.md#background-order) | `_background.order` |
    |  | :material-arrow-collapse-up: [coef](parameters/experiment/background.md#background-coef) | `_background.coef` |
    | :material-puzzle: [linked_structure][linked_structure] | :material-identifier: [structure_id](parameters/experiment/linked_structure.md#linked-structure-structure-id) | `_linked_structure.structure_id` |
    |  | :material-scale: [scale](parameters/experiment/linked_structure.md#linked-structure-scale) | `_linked_structure.scale` |
    | :material-compass-outline: [preferred_orientation][preferred_orientation] | :material-identifier: [structure_id](parameters/experiment/preferred_orientation.md#preferred-orientation-structure-id) | `_preferred_orientation.structure_id` |
    |  | :material-chart-bell-curve-cumulative: [march_r](parameters/experiment/preferred_orientation.md#preferred-orientation-march-r) | `_preferred_orientation.march_r` |
    |  | :material-shuffle-variant: [march_random_fract](parameters/experiment/preferred_orientation.md#preferred-orientation-march-random-fract) | `_preferred_orientation.march_random_fract` |
    |  | :material-axis-arrow: [index_h](parameters/experiment/preferred_orientation.md#preferred-orientation-index-h) | `_preferred_orientation.index_h` |
    |  | :material-axis-arrow: [index_k](parameters/experiment/preferred_orientation.md#preferred-orientation-index-k) | `_preferred_orientation.index_k` |
    |  | :material-axis-arrow: [index_l](parameters/experiment/preferred_orientation.md#preferred-orientation-index-l) | `_preferred_orientation.index_l` |

=== "Keys in CIF"

    | Category | Parameter | Key in CIF | CIF dictionary |
    | --- | --- | --- | --- |
    | :material-waveform: [background][background] | :material-arrow-collapse-right: [position](parameters/experiment/background.md#background-position) | `_pd_background.line_segment_X` | [pdCIF][2]{:.label-cif} |
    |  | :material-arrow-collapse-up: [intensity](parameters/experiment/background.md#background-intensity) | `_pd_background.line_segment_intensity` | [pdCIF][2]{:.label-cif} |
    |  | :material-format-superscript: [order](parameters/experiment/background.md#background-order) | `_pd_background.Chebyshev_order` | [pdCIF][2]{:.label-cif} |
    |  | :material-arrow-collapse-up: [coef](parameters/experiment/background.md#background-coef) | `_pd_background.Chebyshev_coef` | [pdCIF][2]{:.label-cif} |
    | :material-puzzle: [linked_structure][linked_structure] | :material-identifier: [structure_id](parameters/experiment/linked_structure.md#linked-structure-structure-id) | `_pd_phase_block.id` | [pdCIF][2]{:.label-cif} |
    |  | :material-scale: [scale](parameters/experiment/linked_structure.md#linked-structure-scale) | `_pd_phase_block.scale` | [pdCIF][2]{:.label-cif} |
    | :material-compass-outline: [preferred_orientation][preferred_orientation] | :material-identifier: [structure_id](parameters/experiment/preferred_orientation.md#preferred-orientation-structure-id) | `_pd_pref_orient_March_Dollase.phase_id` | [pdCIF][2]{:.label-cif} |
    |  | :material-chart-bell-curve-cumulative: [march_r](parameters/experiment/preferred_orientation.md#preferred-orientation-march-r) | `_pd_pref_orient_March_Dollase.r` | [pdCIF][2]{:.label-cif} |
    |  | :material-shuffle-variant: [march_random_fract](parameters/experiment/preferred_orientation.md#preferred-orientation-march-random-fract) | `_easydiffraction_pref_orient.march_random_fract` | [edifaCIF][0]{:.label-cif} |
    |  | :material-axis-arrow: [index_h](parameters/experiment/preferred_orientation.md#preferred-orientation-index-h) | `_pd_pref_orient_March_Dollase.index_h` | [pdCIF][2]{:.label-cif} |
    |  | :material-axis-arrow: [index_k](parameters/experiment/preferred_orientation.md#preferred-orientation-index-k) | `_pd_pref_orient_March_Dollase.index_k` | [pdCIF][2]{:.label-cif} |
    |  | :material-axis-arrow: [index_l](parameters/experiment/preferred_orientation.md#preferred-orientation-index-l) | `_pd_pref_orient_March_Dollase.index_l` | [pdCIF][2]{:.label-cif} |

[pd-neut-cwl][3]{:.label-experiment} [pd-xray][3]{:.label-experiment}

=== "How to access in the code"

    | Category | Parameter | How to access in the code |
    | --- | --- | --- |
    | :material-microscope: [instrument][instrument] | :material-wrench: [setup_wavelength](parameters/experiment/instrument.md#instrument-setup-wavelength) | instrument.setup_wavelength |
    |  | :material-tune: [calib_twotheta_offset](parameters/experiment/instrument.md#instrument-calib-twotheta-offset) | instrument.calib_twotheta_offset |
    | :material-shape: [peak][peak] | :material-arrow-expand-horizontal: [broad_gauss_u](parameters/experiment/peak.md#peak-broad-gauss-u) | peak.broad_gauss_u |
    |  | :material-arrow-expand-horizontal: [broad_gauss_v](parameters/experiment/peak.md#peak-broad-gauss-v) | peak.broad_gauss_v |
    |  | :material-arrow-expand-horizontal: [broad_gauss_w](parameters/experiment/peak.md#peak-broad-gauss-w) | peak.broad_gauss_w |
    |  | :material-arrow-expand-horizontal: [broad_lorentz_x](parameters/experiment/peak.md#peak-broad-lorentz-x) | peak.broad_lorentz_x |
    |  | :material-arrow-expand-horizontal: [broad_lorentz_y](parameters/experiment/peak.md#peak-broad-lorentz-y) | peak.broad_lorentz_y |

=== "Keys in Edifa"

    | Category | Parameter | Key in Edifa |
    | --- | --- | --- |
    | :material-microscope: [instrument][instrument] | :material-wrench: [setup_wavelength](parameters/experiment/instrument.md#instrument-setup-wavelength) | `_instrument.setup_wavelength` |
    |  | :material-tune: [calib_twotheta_offset](parameters/experiment/instrument.md#instrument-calib-twotheta-offset) | `_instrument.calib_twotheta_offset` |
    | :material-shape: [peak][peak] | :material-arrow-expand-horizontal: [broad_gauss_u](parameters/experiment/peak.md#peak-broad-gauss-u) | `_peak.broad_gauss_u` |
    |  | :material-arrow-expand-horizontal: [broad_gauss_v](parameters/experiment/peak.md#peak-broad-gauss-v) | `_peak.broad_gauss_v` |
    |  | :material-arrow-expand-horizontal: [broad_gauss_w](parameters/experiment/peak.md#peak-broad-gauss-w) | `_peak.broad_gauss_w` |
    |  | :material-arrow-expand-horizontal: [broad_lorentz_x](parameters/experiment/peak.md#peak-broad-lorentz-x) | `_peak.broad_lorentz_x` |
    |  | :material-arrow-expand-horizontal: [broad_lorentz_y](parameters/experiment/peak.md#peak-broad-lorentz-y) | `_peak.broad_lorentz_y` |

=== "Keys in CIF"

    | Category | Parameter | Key in CIF | CIF dictionary |
    | --- | --- | --- | --- |
    | :material-microscope: [instrument][instrument] | :material-wrench: [setup_wavelength](parameters/experiment/instrument.md#instrument-setup-wavelength) | `_diffrn_radiation_wavelength.value` | [coreCIF][1]{:.label-cif} |
    |  | :material-tune: [calib_twotheta_offset](parameters/experiment/instrument.md#instrument-calib-twotheta-offset) | `_pd_calib.2theta_offset` | [pdCIF][2]{:.label-cif} |
    | :material-shape: [peak][peak] | :material-arrow-expand-horizontal: [broad_gauss_u](parameters/experiment/peak.md#peak-broad-gauss-u) | `_easydiffraction_peak.broad_gauss_u` | [edifaCIF][0]{:.label-cif} |
    |  | :material-arrow-expand-horizontal: [broad_gauss_v](parameters/experiment/peak.md#peak-broad-gauss-v) | `_easydiffraction_peak.broad_gauss_v` | [edifaCIF][0]{:.label-cif} |
    |  | :material-arrow-expand-horizontal: [broad_gauss_w](parameters/experiment/peak.md#peak-broad-gauss-w) | `_easydiffraction_peak.broad_gauss_w` | [edifaCIF][0]{:.label-cif} |
    |  | :material-arrow-expand-horizontal: [broad_lorentz_x](parameters/experiment/peak.md#peak-broad-lorentz-x) | `_easydiffraction_peak.broad_lorentz_x` | [edifaCIF][0]{:.label-cif} |
    |  | :material-arrow-expand-horizontal: [broad_lorentz_y](parameters/experiment/peak.md#peak-broad-lorentz-y) | `_easydiffraction_peak.broad_lorentz_y` | [edifaCIF][0]{:.label-cif} |

[pd-neut-tof][3]{:.label-experiment}

=== "How to access in the code"

    | Category | Parameter | How to access in the code |
    | --- | --- | --- |
    | :material-microscope: [instrument][instrument] | :material-wrench: [setup_twotheta_bank](parameters/experiment/instrument.md#instrument-setup-twotheta-bank) | instrument.setup_twotheta_bank |
    |  | :material-tune: [calib_d_to_tof_reciprocal](parameters/experiment/instrument.md#instrument-calib-d-to-tof-reciprocal) | instrument.calib_d_to_tof_reciprocal |
    |  | :material-tune: [calib_d_to_tof_offset](parameters/experiment/instrument.md#instrument-calib-d-to-tof-offset) | instrument.calib_d_to_tof_offset |
    |  | :material-tune: [calib_d_to_tof_linear](parameters/experiment/instrument.md#instrument-calib-d-to-tof-linear) | instrument.calib_d_to_tof_linear |
    |  | :material-tune: [calib_d_to_tof_quadratic](parameters/experiment/instrument.md#instrument-calib-d-to-tof-quadratic) | instrument.calib_d_to_tof_quadratic |
    | :material-shape: [peak][peak] | :material-arrow-expand-horizontal: [broad_gauss_sigma_0](parameters/experiment/peak.md#peak-broad-gauss-sigma-0) | peak.broad_gauss_sigma_0 |
    |  | :material-arrow-expand-horizontal: [broad_gauss_sigma_1](parameters/experiment/peak.md#peak-broad-gauss-sigma-1) | peak.broad_gauss_sigma_1 |
    |  | :material-arrow-expand-horizontal: [broad_gauss_sigma_2](parameters/experiment/peak.md#peak-broad-gauss-sigma-2) | peak.broad_gauss_sigma_2 |
    |  | :material-arrow-expand-horizontal: [broad_lorentz_gamma_0](parameters/experiment/peak.md#peak-broad-lorentz-gamma-0) | peak.broad_lorentz_gamma_0 |
    |  | :material-arrow-expand-horizontal: [broad_lorentz_gamma_1](parameters/experiment/peak.md#peak-broad-lorentz-gamma-1) | peak.broad_lorentz_gamma_1 |
    |  | :material-arrow-expand-horizontal: [broad_lorentz_gamma_2](parameters/experiment/peak.md#peak-broad-lorentz-gamma-2) | peak.broad_lorentz_gamma_2 |
    |  | :material-arrow-bottom-right: [decay_beta_0](parameters/experiment/peak.md#peak-exp-decay-beta-0) | peak.decay_beta_0 |
    |  | :material-arrow-bottom-right: [decay_beta_1](parameters/experiment/peak.md#peak-exp-decay-beta-1) | peak.decay_beta_1 |
    |  | :material-scale-unbalanced: [rise_alpha_0](parameters/experiment/peak.md#peak-exp-rise-alpha-0) | peak.rise_alpha_0 |
    |  | :material-scale-unbalanced: [rise_alpha_1](parameters/experiment/peak.md#peak-exp-rise-alpha-1) | peak.rise_alpha_1 |

=== "Keys in Edifa"

    | Category | Parameter | Key in Edifa |
    | --- | --- | --- |
    | :material-microscope: [instrument][instrument] | :material-wrench: [setup_twotheta_bank](parameters/experiment/instrument.md#instrument-setup-twotheta-bank) | `_instrument.setup_twotheta_bank` |
    |  | :material-tune: [calib_d_to_tof_reciprocal](parameters/experiment/instrument.md#instrument-calib-d-to-tof-reciprocal) | `_instrument.calib_d_to_tof_reciprocal` |
    |  | :material-tune: [calib_d_to_tof_offset](parameters/experiment/instrument.md#instrument-calib-d-to-tof-offset) | `_instrument.calib_d_to_tof_offset` |
    |  | :material-tune: [calib_d_to_tof_linear](parameters/experiment/instrument.md#instrument-calib-d-to-tof-linear) | `_instrument.calib_d_to_tof_linear` |
    |  | :material-tune: [calib_d_to_tof_quadratic](parameters/experiment/instrument.md#instrument-calib-d-to-tof-quadratic) | `_instrument.calib_d_to_tof_quadratic` |
    | :material-shape: [peak][peak] | :material-arrow-expand-horizontal: [broad_gauss_sigma_0](parameters/experiment/peak.md#peak-broad-gauss-sigma-0) | `_peak.broad_gauss_sigma_0` |
    |  | :material-arrow-expand-horizontal: [broad_gauss_sigma_1](parameters/experiment/peak.md#peak-broad-gauss-sigma-1) | `_peak.broad_gauss_sigma_1` |
    |  | :material-arrow-expand-horizontal: [broad_gauss_sigma_2](parameters/experiment/peak.md#peak-broad-gauss-sigma-2) | `_peak.broad_gauss_sigma_2` |
    |  | :material-arrow-expand-horizontal: [broad_lorentz_gamma_0](parameters/experiment/peak.md#peak-broad-lorentz-gamma-0) | `_peak.broad_lorentz_gamma_0` |
    |  | :material-arrow-expand-horizontal: [broad_lorentz_gamma_1](parameters/experiment/peak.md#peak-broad-lorentz-gamma-1) | `_peak.broad_lorentz_gamma_1` |
    |  | :material-arrow-expand-horizontal: [broad_lorentz_gamma_2](parameters/experiment/peak.md#peak-broad-lorentz-gamma-2) | `_peak.broad_lorentz_gamma_2` |
    |  | :material-arrow-bottom-right: [decay_beta_0](parameters/experiment/peak.md#peak-exp-decay-beta-0) | `_peak.decay_beta_0` |
    |  | :material-arrow-bottom-right: [decay_beta_1](parameters/experiment/peak.md#peak-exp-decay-beta-1) | `_peak.decay_beta_1` |
    |  | :material-scale-unbalanced: [rise_alpha_0](parameters/experiment/peak.md#peak-exp-rise-alpha-0) | `_peak.rise_alpha_0` |
    |  | :material-scale-unbalanced: [rise_alpha_1](parameters/experiment/peak.md#peak-exp-rise-alpha-1) | `_peak.rise_alpha_1` |

=== "Keys in CIF"

    | Category | Parameter | Key in CIF | CIF dictionary |
    | --- | --- | --- | --- |
    | :material-microscope: [instrument][instrument] | :material-wrench: [setup_twotheta_bank](parameters/experiment/instrument.md#instrument-setup-twotheta-bank) | `_instr.2theta_bank` | [edifaCIF][0]{:.label-cif} |
    |  | :material-tune: [calib_d_to_tof_reciprocal](parameters/experiment/instrument.md#instrument-calib-d-to-tof-reciprocal) | `_instr.d_to_tof_recip` | [edifaCIF][0]{:.label-cif} |
    |  | :material-tune: [calib_d_to_tof_offset](parameters/experiment/instrument.md#instrument-calib-d-to-tof-offset) | `_instr.d_to_tof_offset` | [edifaCIF][0]{:.label-cif} |
    |  | :material-tune: [calib_d_to_tof_linear](parameters/experiment/instrument.md#instrument-calib-d-to-tof-linear) | `_instr.d_to_tof_linear` | [edifaCIF][0]{:.label-cif} |
    |  | :material-tune: [calib_d_to_tof_quadratic](parameters/experiment/instrument.md#instrument-calib-d-to-tof-quadratic) | `_instr.d_to_tof_quad` | [edifaCIF][0]{:.label-cif} |
    | :material-shape: [peak][peak] | :material-arrow-expand-horizontal: [broad_gauss_sigma_0](parameters/experiment/peak.md#peak-broad-gauss-sigma-0) | `_easydiffraction_peak.gauss_sigma_0` | [edifaCIF][0]{:.label-cif} |
    |  | :material-arrow-expand-horizontal: [broad_gauss_sigma_1](parameters/experiment/peak.md#peak-broad-gauss-sigma-1) | `_easydiffraction_peak.gauss_sigma_1` | [edifaCIF][0]{:.label-cif} |
    |  | :material-arrow-expand-horizontal: [broad_gauss_sigma_2](parameters/experiment/peak.md#peak-broad-gauss-sigma-2) | `_easydiffraction_peak.gauss_sigma_2` | [edifaCIF][0]{:.label-cif} |
    |  | :material-arrow-expand-horizontal: [broad_lorentz_gamma_0](parameters/experiment/peak.md#peak-broad-lorentz-gamma-0) | `_easydiffraction_peak.lorentz_gamma_0` | [edifaCIF][0]{:.label-cif} |
    |  | :material-arrow-expand-horizontal: [broad_lorentz_gamma_1](parameters/experiment/peak.md#peak-broad-lorentz-gamma-1) | `_easydiffraction_peak.lorentz_gamma_1` | [edifaCIF][0]{:.label-cif} |
    |  | :material-arrow-expand-horizontal: [broad_lorentz_gamma_2](parameters/experiment/peak.md#peak-broad-lorentz-gamma-2) | `_easydiffraction_peak.lorentz_gamma_2` | [edifaCIF][0]{:.label-cif} |
    |  | :material-arrow-bottom-right: [decay_beta_0](parameters/experiment/peak.md#peak-exp-decay-beta-0) | `_easydiffraction_peak.decay_beta_0` | [edifaCIF][0]{:.label-cif} |
    |  | :material-arrow-bottom-right: [decay_beta_1](parameters/experiment/peak.md#peak-exp-decay-beta-1) | `_easydiffraction_peak.decay_beta_1` | [edifaCIF][0]{:.label-cif} |
    |  | :material-scale-unbalanced: [rise_alpha_0](parameters/experiment/peak.md#peak-exp-rise-alpha-0) | `_easydiffraction_peak.rise_alpha_0` | [edifaCIF][0]{:.label-cif} |
    |  | :material-scale-unbalanced: [rise_alpha_1](parameters/experiment/peak.md#peak-exp-rise-alpha-1) | `_easydiffraction_peak.rise_alpha_1` | [edifaCIF][0]{:.label-cif} |

### Total Scattering

[pd-neut-total][3]{:.label-experiment}
[pd-xray-total][3]{:.label-experiment}

=== "How to access in the code"

    | Category | Parameter | How to access in the code |
    | --- | --- | --- |
    | :material-shape: [peak][peak] | :material-content-cut: [cutoff_q](parameters/experiment/peak.md#peak-cutoff-q) | peak.cutoff_q |
    |  | :material-arrow-expand-horizontal: [broad_q](parameters/experiment/peak.md#peak-broad-q) | peak.broad_q |
    |  | :material-knife: [sharp_delta_1](parameters/experiment/peak.md#peak-sharp-delta-1) | peak.sharp_delta_1 |
    |  | :material-knife: [sharp_delta_2](parameters/experiment/peak.md#peak-sharp-delta-2) | peak.sharp_delta_2 |
    |  | :material-arrow-bottom-right: [damp_q](parameters/experiment/peak.md#peak-damp-q) | peak.damp_q |
    |  | :material-arrow-bottom-right: [damp_particle_diameter](parameters/experiment/peak.md#peak-damp-particle-diameter) | peak.damp_particle_diameter |

=== "Keys in Edifa"

    | Category | Parameter | Key in Edifa |
    | --- | --- | --- |
    | :material-shape: [peak][peak] | :material-content-cut: [cutoff_q](parameters/experiment/peak.md#peak-cutoff-q) | `_peak.cutoff_q` |
    |  | :material-arrow-expand-horizontal: [broad_q](parameters/experiment/peak.md#peak-broad-q) | `_peak.broad_q` |
    |  | :material-knife: [sharp_delta_1](parameters/experiment/peak.md#peak-sharp-delta-1) | `_peak.sharp_delta_1` |
    |  | :material-knife: [sharp_delta_2](parameters/experiment/peak.md#peak-sharp-delta-2) | `_peak.sharp_delta_2` |
    |  | :material-arrow-bottom-right: [damp_q](parameters/experiment/peak.md#peak-damp-q) | `_peak.damp_q` |
    |  | :material-arrow-bottom-right: [damp_particle_diameter](parameters/experiment/peak.md#peak-damp-particle-diameter) | `_peak.damp_particle_diameter` |

=== "Keys in CIF"

    | Category | Parameter | Key in CIF | CIF dictionary |
    | --- | --- | --- | --- |
    | :material-shape: [peak][peak] | :material-content-cut: [cutoff_q](parameters/experiment/peak.md#peak-cutoff-q) | `_easydiffraction_peak.cutoff_q` | [edifaCIF][0]{:.label-cif} |
    |  | :material-arrow-expand-horizontal: [broad_q](parameters/experiment/peak.md#peak-broad-q) | `_easydiffraction_peak.broad_q` | [edifaCIF][0]{:.label-cif} |
    |  | :material-knife: [sharp_delta_1](parameters/experiment/peak.md#peak-sharp-delta-1) | `_easydiffraction_peak.sharp_delta_1` | [edifaCIF][0]{:.label-cif} |
    |  | :material-knife: [sharp_delta_2](parameters/experiment/peak.md#peak-sharp-delta-2) | `_easydiffraction_peak.sharp_delta_2` | [edifaCIF][0]{:.label-cif} |
    |  | :material-arrow-bottom-right: [damp_q](parameters/experiment/peak.md#peak-damp-q) | `_easydiffraction_peak.damp_q` | [edifaCIF][0]{:.label-cif} |
    |  | :material-arrow-bottom-right: [damp_particle_diameter](parameters/experiment/peak.md#peak-damp-particle-diameter) | `_easydiffraction_peak.damp_particle_diameter` | [edifaCIF][0]{:.label-cif} |

<!-- prettier-ignore-start -->
[0]: #
[1]: https://www.iucr.org/resources/cif/dictionaries/browse/cif_core
[2]: https://www.iucr.org/resources/cif/dictionaries/browse/cif_pd
[3]: glossary.md#experiment-type-labels
[space_group]: parameters/structure/space_group.md
[cell]: parameters/structure/cell.md
[atom_site]: parameters/structure/atom_site.md
[experiment_type]: parameters/experiment/experiment_type.md
[instrument]: parameters/experiment/instrument.md
[peak]: parameters/experiment/peak.md
[background]: parameters/experiment/background.md
[pd_background]: parameters/experiment/pd_background.md
[linked_structure]: parameters/experiment/linked_structure.md
[preferred_orientation]: parameters/experiment/preferred_orientation.md
<!-- prettier-ignore-end -->
