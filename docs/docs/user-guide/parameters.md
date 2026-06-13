# Parameters

The data analysis process, introduced in the [Concept](concept.md)
section, uses parameters to describe structures, experiments, and the
analysis state.

Each parameter has:

- a Python access path used in notebooks and scripts,
- an EdSTAR key used when EasyDiffraction saves a project, and
- where applicable, a CIF key used for importing crystallographic data
  or writing IUCr/pdCIF reports.

EdSTAR is the regular EasyDiffraction project persistence format. CIF
remains important for crystallographic input and for strict report
exports. The tables below therefore separate code access, EdSTAR keys,
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
    | :material-space-station: [space_group][space_group] | :material-tag: [name_h_m](parameters/space_group.md#space-group-name-h-m-alt) | space_group.name_h_m |
    |  | :material-numeric: [it_coordinate_system_code](parameters/space_group.md#space-group-it-coordinate-system-code) | space_group.it_coordinate_system_code |
    | :material-cube-outline: [cell][cell] | :material-ruler: [length_a](parameters/cell.md#cell-length-a) | cell.length_a |
    |  | :material-ruler: [length_b](parameters/cell.md#cell-length-b) | cell.length_b |
    |  | :material-ruler: [length_c](parameters/cell.md#cell-length-c) | cell.length_c |
    |  | :material-angle-acute: [angle_alpha](parameters/cell.md#cell-angle-alpha) | cell.angle_alpha |
    |  | :material-angle-acute: [angle_beta](parameters/cell.md#cell-angle-beta) | cell.angle_beta |
    |  | :material-angle-acute: [angle_gamma](parameters/cell.md#cell-angle-gamma) | cell.angle_gamma |
    | :material-atom: [atom_site][atom_site] | :material-tag: [id](parameters/atom_site.md#atom-site-id) | atom_sites['ID'].id |
    |  | :material-periodic-table: [type_symbol](parameters/atom_site.md#atom-site-type-symbol) | atom_sites['ID'].type_symbol |
    |  | :material-map-marker: [fract_x](parameters/atom_site.md#atom-site-fract-x) | atom_sites['ID'].fract_x |
    |  | :material-map-marker: [fract_y](parameters/atom_site.md#atom-site-fract-y) | atom_sites['ID'].fract_y |
    |  | :material-map-marker: [fract_z](parameters/atom_site.md#atom-site-fract-z) | atom_sites['ID'].fract_z |
    |  | :material-format-color-fill: [occupancy](parameters/atom_site.md#atom-site-occupancy) | atom_sites['ID'].occupancy |
    |  | :material-cursor-move: [adp_type](parameters/atom_site.md#atom-site-adp-type) | atom_sites['ID'].adp_type |
    |  | :material-cursor-move: [adp_iso](parameters/atom_site.md#atom-site-b-iso-or-equiv) | atom_sites['ID'].adp_iso |
    |  | :material-reflect-horizontal: [multiplicity](parameters/atom_site.md#atom-site-site-symmetry-multiplicity) | atom_sites['ID'].multiplicity |
    |  | :material-reflect-horizontal: [wyckoff_letter](parameters/atom_site.md#atom-site-wyckoff-symbol) | atom_sites['ID'].wyckoff_letter |

=== "Keys in EdSTAR"

    | Category | Parameter | Key in EdSTAR |
    | --- | --- | --- |
    | :material-space-station: [space_group][space_group] | :material-tag: [name_h_m](parameters/space_group.md#space-group-name-h-m-alt) | `_space_group.name_H-M_alt` |
    |  | :material-numeric: [it_coordinate_system_code](parameters/space_group.md#space-group-it-coordinate-system-code) | `_space_group.IT_coordinate_system_code` |
    | :material-cube-outline: [cell][cell] | :material-ruler: [length_a](parameters/cell.md#cell-length-a) | `_cell.length_a` |
    |  | :material-ruler: [length_b](parameters/cell.md#cell-length-b) | `_cell.length_b` |
    |  | :material-ruler: [length_c](parameters/cell.md#cell-length-c) | `_cell.length_c` |
    |  | :material-angle-acute: [angle_alpha](parameters/cell.md#cell-angle-alpha) | `_cell.angle_alpha` |
    |  | :material-angle-acute: [angle_beta](parameters/cell.md#cell-angle-beta) | `_cell.angle_beta` |
    |  | :material-angle-acute: [angle_gamma](parameters/cell.md#cell-angle-gamma) | `_cell.angle_gamma` |
    | :material-atom: [atom_site][atom_site] | :material-tag: [id](parameters/atom_site.md#atom-site-id) | `_atom_site.id` |
    |  | :material-periodic-table: [type_symbol](parameters/atom_site.md#atom-site-type-symbol) | `_atom_site.type_symbol` |
    |  | :material-map-marker: [fract_x](parameters/atom_site.md#atom-site-fract-x) | `_atom_site.fract_x` |
    |  | :material-map-marker: [fract_y](parameters/atom_site.md#atom-site-fract-y) | `_atom_site.fract_y` |
    |  | :material-map-marker: [fract_z](parameters/atom_site.md#atom-site-fract-z) | `_atom_site.fract_z` |
    |  | :material-format-color-fill: [occupancy](parameters/atom_site.md#atom-site-occupancy) | `_atom_site.occupancy` |
    |  | :material-cursor-move: [adp_type](parameters/atom_site.md#atom-site-adp-type) | `_atom_site.ADP_type` |
    |  | :material-cursor-move: [adp_iso](parameters/atom_site.md#atom-site-b-iso-or-equiv) | `_atom_site.B_iso_or_equiv` |
    |  | :material-reflect-horizontal: [multiplicity](parameters/atom_site.md#atom-site-site-symmetry-multiplicity) | `_atom_site.site_symmetry_multiplicity` |
    |  | :material-reflect-horizontal: [wyckoff_letter](parameters/atom_site.md#atom-site-wyckoff-symbol) | `_atom_site.Wyckoff_symbol` |

=== "Keys in CIF"

    | Category | Parameter | Key in CIF | CIF dictionary |
    | --- | --- | --- | --- |
    | :material-space-station: [space_group][space_group] | :material-tag: [name_h_m](parameters/space_group.md#space-group-name-h-m-alt) | `_space_group.name_H-M_alt` | [coreCIF][1]{:.label-cif} |
    |  | :material-numeric: [it_coordinate_system_code](parameters/space_group.md#space-group-it-coordinate-system-code) | `_space_group.IT_coordinate_system_code` | [coreCIF][1]{:.label-cif} |
    | :material-cube-outline: [cell][cell] | :material-ruler: [length_a](parameters/cell.md#cell-length-a) | `_cell.length_a` | [coreCIF][1]{:.label-cif} |
    |  | :material-ruler: [length_b](parameters/cell.md#cell-length-b) | `_cell.length_b` | [coreCIF][1]{:.label-cif} |
    |  | :material-ruler: [length_c](parameters/cell.md#cell-length-c) | `_cell.length_c` | [coreCIF][1]{:.label-cif} |
    |  | :material-angle-acute: [angle_alpha](parameters/cell.md#cell-angle-alpha) | `_cell.angle_alpha` | [coreCIF][1]{:.label-cif} |
    |  | :material-angle-acute: [angle_beta](parameters/cell.md#cell-angle-beta) | `_cell.angle_beta` | [coreCIF][1]{:.label-cif} |
    |  | :material-angle-acute: [angle_gamma](parameters/cell.md#cell-angle-gamma) | `_cell.angle_gamma` | [coreCIF][1]{:.label-cif} |
    | :material-atom: [atom_site][atom_site] | :material-tag: [id](parameters/atom_site.md#atom-site-id) | `_atom_site.label` | [coreCIF][1]{:.label-cif} |
    |  | :material-periodic-table: [type_symbol](parameters/atom_site.md#atom-site-type-symbol) | `_atom_site.type_symbol` | [coreCIF][1]{:.label-cif} |
    |  | :material-map-marker: [fract_x](parameters/atom_site.md#atom-site-fract-x) | `_atom_site.fract_x` | [coreCIF][1]{:.label-cif} |
    |  | :material-map-marker: [fract_y](parameters/atom_site.md#atom-site-fract-y) | `_atom_site.fract_y` | [coreCIF][1]{:.label-cif} |
    |  | :material-map-marker: [fract_z](parameters/atom_site.md#atom-site-fract-z) | `_atom_site.fract_z` | [coreCIF][1]{:.label-cif} |
    |  | :material-format-color-fill: [occupancy](parameters/atom_site.md#atom-site-occupancy) | `_atom_site.occupancy` | [coreCIF][1]{:.label-cif} |
    |  | :material-cursor-move: [adp_type](parameters/atom_site.md#atom-site-adp-type) | `_atom_site.ADP_type` | [coreCIF][1]{:.label-cif} |
    |  | :material-cursor-move: [adp_iso](parameters/atom_site.md#atom-site-b-iso-or-equiv) | `_atom_site.B_iso_or_equiv` | [coreCIF][1]{:.label-cif} |
    |  | :material-reflect-horizontal: [multiplicity](parameters/atom_site.md#atom-site-site-symmetry-multiplicity) | `_atom_site.site_symmetry_multiplicity` | [coreCIF][1]{:.label-cif} |
    |  | :material-reflect-horizontal: [wyckoff_letter](parameters/atom_site.md#atom-site-wyckoff-symbol) | `_atom_site.Wyckoff_symbol` | [coreCIF][1]{:.label-cif} |

## Experiment Parameters

### Common Parameters

[pd-neut-cwl][3]{:.label-experiment}
[pd-neut-tof][3]{:.label-experiment} [pd-xray][3]{:.label-experiment}
[sc-neut-cwl][3]{:.label-experiment}

=== "How to access in the code"

    | Category | Parameter | How to access in the code |
    | --- | --- | --- |
    | :material-flask: [experiment_type][experiment_type] | :material-sawtooth-wave: [beam_mode](parameters/experiment_type.md#experiment-type-beam-mode) | experiment_type.beam_mode |
    |  | :material-radiology-box-outline: [radiation_probe](parameters/experiment_type.md#experiment-type-radiation-probe) | experiment_type.radiation_probe |
    |  | :material-diamond-stone: [sample_form](parameters/experiment_type.md#experiment-type-sample-form) | experiment_type.sample_form |
    |  | :material-chart-bell-curve: [scattering_type](parameters/experiment_type.md#experiment-type-scattering-type) | experiment_type.scattering_type |

=== "Keys in EdSTAR"

    | Category | Parameter | Key in EdSTAR |
    | --- | --- | --- |
    | :material-flask: [experiment_type][experiment_type] | :material-sawtooth-wave: [beam_mode](parameters/experiment_type.md#experiment-type-beam-mode) | `_experiment_type.beam_mode` |
    |  | :material-radiology-box-outline: [radiation_probe](parameters/experiment_type.md#experiment-type-radiation-probe) | `_experiment_type.radiation_probe` |
    |  | :material-diamond-stone: [sample_form](parameters/experiment_type.md#experiment-type-sample-form) | `_experiment_type.sample_form` |
    |  | :material-chart-bell-curve: [scattering_type](parameters/experiment_type.md#experiment-type-scattering-type) | `_experiment_type.scattering_type` |

=== "Keys in CIF"

    | Category | Parameter | Key in CIF | CIF dictionary |
    | --- | --- | --- | --- |
    | :material-flask: [experiment_type][experiment_type] | :material-sawtooth-wave: [beam_mode](parameters/experiment_type.md#experiment-type-beam-mode) | `_expt_type.beam_mode` | [easydiffractionCIF][0]{:.label-cif} |
    |  | :material-radiology-box-outline: [radiation_probe](parameters/experiment_type.md#experiment-type-radiation-probe) | `_expt_type.radiation_probe` | [easydiffractionCIF][0]{:.label-cif} |
    |  | :material-diamond-stone: [sample_form](parameters/experiment_type.md#experiment-type-sample-form) | `_expt_type.sample_form` | [easydiffractionCIF][0]{:.label-cif} |
    |  | :material-chart-bell-curve: [scattering_type](parameters/experiment_type.md#experiment-type-scattering-type) | `_expt_type.scattering_type` | [easydiffractionCIF][0]{:.label-cif} |

### Standard Powder Diffraction

[pd-neut-cwl][3]{:.label-experiment}
[pd-neut-tof][3]{:.label-experiment} [pd-xray][3]{:.label-experiment}

=== "How to access in the code"

    | Category | Parameter | How to access in the code |
    | --- | --- | --- |
    | :material-waveform: [background][background] | :material-arrow-collapse-right: [position](parameters/background.md#background-position) | background.position |
    |  | :material-arrow-collapse-up: [intensity](parameters/background.md#background-intensity) | background.intensity |
    |  | :material-format-superscript: [order](parameters/pd_background.md#pd-background-chebyshev-order) | background.order |
    |  | :material-arrow-collapse-up: [coef](parameters/pd_background.md#pd-background-chebyshev-coef) | background.coef |
    | :material-puzzle: [linked_structure][linked_structure] | :material-identifier: [structure_id](parameters/linked_structure.md#linked-structure-structure-id) | linked_structures['ID'].structure_id |
    |  | :material-scale: [scale](parameters/linked_structure.md#linked-structure-scale) | linked_structures['ID'].scale |
    | :material-compass-outline: [preferred_orientation][preferred_orientation] | :material-identifier: [structure_id](parameters/preferred_orientation.md#preferred-orientation-structure-id) | preferred_orientation['ID'].structure_id |
    |  | :material-chart-bell-curve-cumulative: [march_r](parameters/preferred_orientation.md#preferred-orientation-march-r) | preferred_orientation['ID'].march_r |
    |  | :material-shuffle-variant: [march_random_fract](parameters/preferred_orientation.md#preferred-orientation-march-random-fract) | preferred_orientation['ID'].march_random_fract |
    |  | :material-axis-arrow: [index_h](parameters/preferred_orientation.md#preferred-orientation-index-h) | preferred_orientation['ID'].index_h |
    |  | :material-axis-arrow: [index_k](parameters/preferred_orientation.md#preferred-orientation-index-k) | preferred_orientation['ID'].index_k |
    |  | :material-axis-arrow: [index_l](parameters/preferred_orientation.md#preferred-orientation-index-l) | preferred_orientation['ID'].index_l |

=== "Keys in EdSTAR"

    | Category | Parameter | Key in EdSTAR |
    | --- | --- | --- |
    | :material-waveform: [background][background] | :material-arrow-collapse-right: [position](parameters/background.md#background-position) | `_background.position` |
    |  | :material-arrow-collapse-up: [intensity](parameters/background.md#background-intensity) | `_background.intensity` |
    |  | :material-format-superscript: [order](parameters/pd_background.md#pd-background-chebyshev-order) | `_pd_background.Chebyshev_order` |
    |  | :material-arrow-collapse-up: [coef](parameters/pd_background.md#pd-background-chebyshev-coef) | `_pd_background.Chebyshev_coef` |
    | :material-puzzle: [linked_structure][linked_structure] | :material-identifier: [structure_id](parameters/linked_structure.md#linked-structure-structure-id) | `_linked_structure.structure_id` |
    |  | :material-scale: [scale](parameters/linked_structure.md#linked-structure-scale) | `_linked_structure.scale` |
    | :material-compass-outline: [preferred_orientation][preferred_orientation] | :material-identifier: [structure_id](parameters/preferred_orientation.md#preferred-orientation-structure-id) | `_preferred_orientation.structure_id` |
    |  | :material-chart-bell-curve-cumulative: [march_r](parameters/preferred_orientation.md#preferred-orientation-march-r) | `_preferred_orientation.march_r` |
    |  | :material-shuffle-variant: [march_random_fract](parameters/preferred_orientation.md#preferred-orientation-march-random-fract) | `_preferred_orientation.march_random_fract` |
    |  | :material-axis-arrow: [index_h](parameters/preferred_orientation.md#preferred-orientation-index-h) | `_preferred_orientation.index_h` |
    |  | :material-axis-arrow: [index_k](parameters/preferred_orientation.md#preferred-orientation-index-k) | `_preferred_orientation.index_k` |
    |  | :material-axis-arrow: [index_l](parameters/preferred_orientation.md#preferred-orientation-index-l) | `_preferred_orientation.index_l` |

=== "Keys in CIF"

    | Category | Parameter | Key in CIF | CIF dictionary |
    | --- | --- | --- | --- |
    | :material-waveform: [background][background] | :material-arrow-collapse-right: [position](parameters/background.md#background-position) | `_pd_background.line_segment_X` | [pdCIF][2]{:.label-cif} |
    |  | :material-arrow-collapse-up: [intensity](parameters/background.md#background-intensity) | `_pd_background.line_segment_intensity` | [pdCIF][2]{:.label-cif} |
    |  | :material-format-superscript: [order](parameters/pd_background.md#pd-background-chebyshev-order) | `_pd_background.Chebyshev_order` | [pdCIF][2]{:.label-cif} |
    |  | :material-arrow-collapse-up: [coef](parameters/pd_background.md#pd-background-chebyshev-coef) | `_pd_background.Chebyshev_coef` | [pdCIF][2]{:.label-cif} |
    | :material-puzzle: [linked_structure][linked_structure] | :material-identifier: [structure_id](parameters/linked_structure.md#linked-structure-structure-id) | `_pd_phase_block.id` | [pdCIF][2]{:.label-cif} |
    |  | :material-scale: [scale](parameters/linked_structure.md#linked-structure-scale) | `_pd_phase_block.scale` | [pdCIF][2]{:.label-cif} |
    | :material-compass-outline: [preferred_orientation][preferred_orientation] | :material-identifier: [structure_id](parameters/preferred_orientation.md#preferred-orientation-structure-id) | `_pd_pref_orient_March_Dollase.phase_id` | [pdCIF][2]{:.label-cif} |
    |  | :material-chart-bell-curve-cumulative: [march_r](parameters/preferred_orientation.md#preferred-orientation-march-r) | `_pd_pref_orient_March_Dollase.r` | [pdCIF][2]{:.label-cif} |
    |  | :material-shuffle-variant: [march_random_fract](parameters/preferred_orientation.md#preferred-orientation-march-random-fract) | `_preferred_orientation.march_random_fract` | [easydiffractionCIF][0]{:.label-cif} |
    |  | :material-axis-arrow: [index_h](parameters/preferred_orientation.md#preferred-orientation-index-h) | `_pd_pref_orient_March_Dollase.index_h` | [pdCIF][2]{:.label-cif} |
    |  | :material-axis-arrow: [index_k](parameters/preferred_orientation.md#preferred-orientation-index-k) | `_pd_pref_orient_March_Dollase.index_k` | [pdCIF][2]{:.label-cif} |
    |  | :material-axis-arrow: [index_l](parameters/preferred_orientation.md#preferred-orientation-index-l) | `_pd_pref_orient_March_Dollase.index_l` | [pdCIF][2]{:.label-cif} |

[pd-neut-cwl][3]{:.label-experiment} [pd-xray][3]{:.label-experiment}

=== "How to access in the code"

    | Category | Parameter | How to access in the code |
    | --- | --- | --- |
    | :material-microscope: [instrument][instrument] | :material-wrench: [setup_wavelength](parameters/instrument.md#instrument-setup-wavelength) | instrument.setup_wavelength |
    |  | :material-tune: [calib_twotheta_offset](parameters/instrument.md#instrument-calib-twotheta-offset) | instrument.calib_twotheta_offset |
    | :material-shape: [peak][peak] | :material-arrow-expand-horizontal: [broad_gauss_u](parameters/peak.md#peak-broad-gauss-u) | peak.broad_gauss_u |
    |  | :material-arrow-expand-horizontal: [broad_gauss_v](parameters/peak.md#peak-broad-gauss-v) | peak.broad_gauss_v |
    |  | :material-arrow-expand-horizontal: [broad_gauss_w](parameters/peak.md#peak-broad-gauss-w) | peak.broad_gauss_w |
    |  | :material-arrow-expand-horizontal: [broad_lorentz_x](parameters/peak.md#peak-broad-lorentz-x) | peak.broad_lorentz_x |
    |  | :material-arrow-expand-horizontal: [broad_lorentz_y](parameters/peak.md#peak-broad-lorentz-y) | peak.broad_lorentz_y |

=== "Keys in EdSTAR"

    | Category | Parameter | Key in EdSTAR |
    | --- | --- | --- |
    | :material-microscope: [instrument][instrument] | :material-wrench: [setup_wavelength](parameters/instrument.md#instrument-setup-wavelength) | `_instrument.setup_wavelength` |
    |  | :material-tune: [calib_twotheta_offset](parameters/instrument.md#instrument-calib-twotheta-offset) | `_instrument.calib_twotheta_offset` |
    | :material-shape: [peak][peak] | :material-arrow-expand-horizontal: [broad_gauss_u](parameters/peak.md#peak-broad-gauss-u) | `_peak.broad_gauss_u` |
    |  | :material-arrow-expand-horizontal: [broad_gauss_v](parameters/peak.md#peak-broad-gauss-v) | `_peak.broad_gauss_v` |
    |  | :material-arrow-expand-horizontal: [broad_gauss_w](parameters/peak.md#peak-broad-gauss-w) | `_peak.broad_gauss_w` |
    |  | :material-arrow-expand-horizontal: [broad_lorentz_x](parameters/peak.md#peak-broad-lorentz-x) | `_peak.broad_lorentz_x` |
    |  | :material-arrow-expand-horizontal: [broad_lorentz_y](parameters/peak.md#peak-broad-lorentz-y) | `_peak.broad_lorentz_y` |

=== "Keys in CIF"

    | Category | Parameter | Key in CIF | CIF dictionary |
    | --- | --- | --- | --- |
    | :material-microscope: [instrument][instrument] | :material-wrench: [setup_wavelength](parameters/instrument.md#instrument-setup-wavelength) | `_instr.wavelength` | [easydiffractionCIF][0]{:.label-cif} |
    |  | :material-tune: [calib_twotheta_offset](parameters/instrument.md#instrument-calib-twotheta-offset) | `_instr.2theta_offset` | [easydiffractionCIF][0]{:.label-cif} |
    | :material-shape: [peak][peak] | :material-arrow-expand-horizontal: [broad_gauss_u](parameters/peak.md#peak-broad-gauss-u) | `_peak.broad_gauss_u` | [easydiffractionCIF][0]{:.label-cif} |
    |  | :material-arrow-expand-horizontal: [broad_gauss_v](parameters/peak.md#peak-broad-gauss-v) | `_peak.broad_gauss_v` | [easydiffractionCIF][0]{:.label-cif} |
    |  | :material-arrow-expand-horizontal: [broad_gauss_w](parameters/peak.md#peak-broad-gauss-w) | `_peak.broad_gauss_w` | [easydiffractionCIF][0]{:.label-cif} |
    |  | :material-arrow-expand-horizontal: [broad_lorentz_x](parameters/peak.md#peak-broad-lorentz-x) | `_peak.broad_lorentz_x` | [easydiffractionCIF][0]{:.label-cif} |
    |  | :material-arrow-expand-horizontal: [broad_lorentz_y](parameters/peak.md#peak-broad-lorentz-y) | `_peak.broad_lorentz_y` | [easydiffractionCIF][0]{:.label-cif} |

[pd-neut-tof][3]{:.label-experiment}

=== "How to access in the code"

    | Category | Parameter | How to access in the code |
    | --- | --- | --- |
    | :material-microscope: [instrument][instrument] | :material-wrench: [setup_twotheta_bank](parameters/instrument.md#instrument-setup-twotheta-bank) | instrument.setup_twotheta_bank |
    |  | :material-tune: [calib_d_to_tof_reciprocal](parameters/instrument.md#instrument-calib-d-to-tof-reciprocal) | instrument.calib_d_to_tof_reciprocal |
    |  | :material-tune: [calib_d_to_tof_offset](parameters/instrument.md#instrument-calib-d-to-tof-offset) | instrument.calib_d_to_tof_offset |
    |  | :material-tune: [calib_d_to_tof_linear](parameters/instrument.md#instrument-calib-d-to-tof-linear) | instrument.calib_d_to_tof_linear |
    |  | :material-tune: [calib_d_to_tof_quadratic](parameters/instrument.md#instrument-calib-d-to-tof-quadratic) | instrument.calib_d_to_tof_quadratic |
    | :material-shape: [peak][peak] | :material-arrow-expand-horizontal: [broad_gauss_sigma_0](parameters/peak.md#peak-gauss-sigma-0) | peak.broad_gauss_sigma_0 |
    |  | :material-arrow-expand-horizontal: [broad_gauss_sigma_1](parameters/peak.md#peak-gauss-sigma-1) | peak.broad_gauss_sigma_1 |
    |  | :material-arrow-expand-horizontal: [broad_gauss_sigma_2](parameters/peak.md#peak-gauss-sigma-2) | peak.broad_gauss_sigma_2 |
    |  | :material-arrow-bottom-right: [exp_decay_beta_0](parameters/peak.md#peak-decay-beta-0) | peak.exp_decay_beta_0 |
    |  | :material-arrow-bottom-right: [exp_decay_beta_1](parameters/peak.md#peak-decay-beta-1) | peak.exp_decay_beta_1 |
    |  | :material-scale-unbalanced: [exp_rise_alpha_0](parameters/peak.md#peak-rise-alpha-0) | peak.exp_rise_alpha_0 |
    |  | :material-scale-unbalanced: [exp_rise_alpha_1](parameters/peak.md#peak-rise-alpha-1) | peak.exp_rise_alpha_1 |

=== "Keys in EdSTAR"

    | Category | Parameter | Key in EdSTAR |
    | --- | --- | --- |
    | :material-microscope: [instrument][instrument] | :material-wrench: [setup_twotheta_bank](parameters/instrument.md#instrument-setup-twotheta-bank) | `_instrument.setup_twotheta_bank` |
    |  | :material-tune: [calib_d_to_tof_reciprocal](parameters/instrument.md#instrument-calib-d-to-tof-reciprocal) | `_instrument.calib_d_to_tof_reciprocal` |
    |  | :material-tune: [calib_d_to_tof_offset](parameters/instrument.md#instrument-calib-d-to-tof-offset) | `_instrument.calib_d_to_tof_offset` |
    |  | :material-tune: [calib_d_to_tof_linear](parameters/instrument.md#instrument-calib-d-to-tof-linear) | `_instrument.calib_d_to_tof_linear` |
    |  | :material-tune: [calib_d_to_tof_quadratic](parameters/instrument.md#instrument-calib-d-to-tof-quadratic) | `_instrument.calib_d_to_tof_quadratic` |
    | :material-shape: [peak][peak] | :material-arrow-expand-horizontal: [broad_gauss_sigma_0](parameters/peak.md#peak-gauss-sigma-0) | `_peak.gauss_sigma_0` |
    |  | :material-arrow-expand-horizontal: [broad_gauss_sigma_1](parameters/peak.md#peak-gauss-sigma-1) | `_peak.gauss_sigma_1` |
    |  | :material-arrow-expand-horizontal: [broad_gauss_sigma_2](parameters/peak.md#peak-gauss-sigma-2) | `_peak.gauss_sigma_2` |
    |  | :material-arrow-bottom-right: [exp_decay_beta_0](parameters/peak.md#peak-decay-beta-0) | `_peak.decay_beta_0` |
    |  | :material-arrow-bottom-right: [exp_decay_beta_1](parameters/peak.md#peak-decay-beta-1) | `_peak.decay_beta_1` |
    |  | :material-scale-unbalanced: [exp_rise_alpha_0](parameters/peak.md#peak-rise-alpha-0) | `_peak.rise_alpha_0` |
    |  | :material-scale-unbalanced: [exp_rise_alpha_1](parameters/peak.md#peak-rise-alpha-1) | `_peak.rise_alpha_1` |

=== "Keys in CIF"

    | Category | Parameter | Key in CIF | CIF dictionary |
    | --- | --- | --- | --- |
    | :material-microscope: [instrument][instrument] | :material-wrench: [setup_twotheta_bank](parameters/instrument.md#instrument-setup-twotheta-bank) | `_instr.2theta_bank` | [easydiffractionCIF][0]{:.label-cif} |
    |  | :material-tune: [calib_d_to_tof_reciprocal](parameters/instrument.md#instrument-calib-d-to-tof-reciprocal) | `_instr.d_to_tof_recip` | [easydiffractionCIF][0]{:.label-cif} |
    |  | :material-tune: [calib_d_to_tof_offset](parameters/instrument.md#instrument-calib-d-to-tof-offset) | `_instr.d_to_tof_offset` | [easydiffractionCIF][0]{:.label-cif} |
    |  | :material-tune: [calib_d_to_tof_linear](parameters/instrument.md#instrument-calib-d-to-tof-linear) | `_instr.d_to_tof_linear` | [easydiffractionCIF][0]{:.label-cif} |
    |  | :material-tune: [calib_d_to_tof_quadratic](parameters/instrument.md#instrument-calib-d-to-tof-quadratic) | `_instr.d_to_tof_quad` | [easydiffractionCIF][0]{:.label-cif} |
    | :material-shape: [peak][peak] | :material-arrow-expand-horizontal: [broad_gauss_sigma_0](parameters/peak.md#peak-gauss-sigma-0) | `_peak.gauss_sigma_0` | [easydiffractionCIF][0]{:.label-cif} |
    |  | :material-arrow-expand-horizontal: [broad_gauss_sigma_1](parameters/peak.md#peak-gauss-sigma-1) | `_peak.gauss_sigma_1` | [easydiffractionCIF][0]{:.label-cif} |
    |  | :material-arrow-expand-horizontal: [broad_gauss_sigma_2](parameters/peak.md#peak-gauss-sigma-2) | `_peak.gauss_sigma_2` | [easydiffractionCIF][0]{:.label-cif} |
    |  | :material-arrow-bottom-right: [exp_decay_beta_0](parameters/peak.md#peak-decay-beta-0) | `_peak.decay_beta_0` | [easydiffractionCIF][0]{:.label-cif} |
    |  | :material-arrow-bottom-right: [exp_decay_beta_1](parameters/peak.md#peak-decay-beta-1) | `_peak.decay_beta_1` | [easydiffractionCIF][0]{:.label-cif} |
    |  | :material-scale-unbalanced: [exp_rise_alpha_0](parameters/peak.md#peak-rise-alpha-0) | `_peak.rise_alpha_0` | [easydiffractionCIF][0]{:.label-cif} |
    |  | :material-scale-unbalanced: [exp_rise_alpha_1](parameters/peak.md#peak-rise-alpha-1) | `_peak.rise_alpha_1` | [easydiffractionCIF][0]{:.label-cif} |

### Total Scattering

[pd-neut-total][3]{:.label-experiment}
[pd-xray-total][3]{:.label-experiment}

=== "How to access in the code"

    | Category | Parameter | How to access in the code |
    | --- | --- | --- |
    | :material-shape: [peak][peak] | :material-content-cut: [cutoff_q](parameters/peak.md#peak-cutoff-q) | peak.cutoff_q |
    |  | :material-arrow-expand-horizontal: [broad_q](parameters/peak.md#peak-broad-q) | peak.broad_q |
    |  | :material-knife: [sharp_delta_1](parameters/peak.md#peak-sharp-delta-1) | peak.sharp_delta_1 |
    |  | :material-knife: [sharp_delta_2](parameters/peak.md#peak-sharp-delta-2) | peak.sharp_delta_2 |
    |  | :material-arrow-bottom-right: [damp_q](parameters/peak.md#peak-damp-q) | peak.damp_q |
    |  | :material-arrow-bottom-right: [damp_particle_diameter](parameters/peak.md#peak-damp-particle-diameter) | peak.damp_particle_diameter |

=== "Keys in EdSTAR"

    | Category | Parameter | Key in EdSTAR |
    | --- | --- | --- |
    | :material-shape: [peak][peak] | :material-content-cut: [cutoff_q](parameters/peak.md#peak-cutoff-q) | `_peak.cutoff_q` |
    |  | :material-arrow-expand-horizontal: [broad_q](parameters/peak.md#peak-broad-q) | `_peak.broad_q` |
    |  | :material-knife: [sharp_delta_1](parameters/peak.md#peak-sharp-delta-1) | `_peak.sharp_delta_1` |
    |  | :material-knife: [sharp_delta_2](parameters/peak.md#peak-sharp-delta-2) | `_peak.sharp_delta_2` |
    |  | :material-arrow-bottom-right: [damp_q](parameters/peak.md#peak-damp-q) | `_peak.damp_q` |
    |  | :material-arrow-bottom-right: [damp_particle_diameter](parameters/peak.md#peak-damp-particle-diameter) | `_peak.damp_particle_diameter` |

=== "Keys in CIF"

    | Category | Parameter | Key in CIF | CIF dictionary |
    | --- | --- | --- | --- |
    | :material-shape: [peak][peak] | :material-content-cut: [cutoff_q](parameters/peak.md#peak-cutoff-q) | `_peak.cutoff_q` | [easydiffractionCIF][0]{:.label-cif} |
    |  | :material-arrow-expand-horizontal: [broad_q](parameters/peak.md#peak-broad-q) | `_peak.broad_q` | [easydiffractionCIF][0]{:.label-cif} |
    |  | :material-knife: [sharp_delta_1](parameters/peak.md#peak-sharp-delta-1) | `_peak.sharp_delta_1` | [easydiffractionCIF][0]{:.label-cif} |
    |  | :material-knife: [sharp_delta_2](parameters/peak.md#peak-sharp-delta-2) | `_peak.sharp_delta_2` | [easydiffractionCIF][0]{:.label-cif} |
    |  | :material-arrow-bottom-right: [damp_q](parameters/peak.md#peak-damp-q) | `_peak.damp_q` | [easydiffractionCIF][0]{:.label-cif} |
    |  | :material-arrow-bottom-right: [damp_particle_diameter](parameters/peak.md#peak-damp-particle-diameter) | `_peak.damp_particle_diameter` | [easydiffractionCIF][0]{:.label-cif} |

<!-- prettier-ignore-start -->
[0]: #
[1]: https://www.iucr.org/resources/cif/dictionaries/browse/cif_core
[2]: https://www.iucr.org/resources/cif/dictionaries/browse/cif_pd
[3]: glossary.md#experiment-type-labels
[space_group]: parameters/space_group.md
[cell]: parameters/cell.md
[atom_site]: parameters/atom_site.md
[experiment_type]: parameters/experiment_type.md
[instrument]: parameters/instrument.md
[peak]: parameters/peak.md
[background]: parameters/background.md
[pd_background]: parameters/pd_background.md
[linked_structure]: parameters/linked_structure.md
[preferred_orientation]: parameters/preferred_orientation.md
<!-- prettier-ignore-end -->
