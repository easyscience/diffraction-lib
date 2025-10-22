# %%
# ## Import Library
import easydiffraction as ed

# %%
# ## Step 1: Define Project
project = ed.Project()
#project.tabler.engine = 'rich'
#project.tabler.engine = 'pandas'

# %%
# ## Step 2: Define Sample Model
project.sample_models.add_minimal(name='lbco')

sample_model = project.sample_models['lbco']
sample_model.space_group.name_h_m = 'P m -3 m'
sample_model.space_group.it_coordinate_system_code = '1'
sample_model.cell.length_a = 3.88
sample_model.atom_sites.add_from_args(
    label='La',
    type_symbol='La',
    fract_x=0,
    fract_y=0,
    fract_z=0,
    wyckoff_letter='a',
    b_iso=0.5,
    occupancy=0.5,
)
sample_model.atom_sites.add_from_args(
    label='Ba',
    type_symbol='Ba',
    fract_x=0,
    fract_y=0,
    fract_z=0,
    wyckoff_letter='a',
    b_iso=0.5,
    occupancy=0.5,
)
sample_model.atom_sites.add_from_args(
    label='Co',
    type_symbol='Co',
    fract_x=0.5,
    fract_y=0.5,
    fract_z=0.5,
    wyckoff_letter='b',
    b_iso=0.5,
)
sample_model.atom_sites.add_from_args(
    label='O', type_symbol='O', fract_x=0, fract_y=0.5, fract_z=0.5, wyckoff_letter='c', b_iso=0.5
)

# %%
# ## Step 3: Define Experiment
ed.download_from_repository('hrpt_lbco.xye', destination='data')

project.experiments.add_from_data_path(
    name='hrpt',
    data_path='data/hrpt_lbco.xye',
    sample_form='powder',
    beam_mode='constant wavelength',
    radiation_probe='neutron',
)

experiment = project.experiments['hrpt']
experiment.instrument.setup_wavelength = 1.494
experiment.instrument.calib_twotheta_offset = 0.6
experiment.peak.broad_gauss_u = 0.1
experiment.peak.broad_gauss_v = -0.1
experiment.peak.broad_gauss_w = 0.1
experiment.peak.broad_lorentz_y = 0.1
experiment.background.add_from_args(x=10, y=170)
experiment.background.add_from_args(x=30, y=170)
experiment.background.add_from_args(x=50, y=170)
experiment.background.add_from_args(x=110, y=170)
experiment.background.add_from_args(x=165, y=170)
experiment.excluded_regions.add_from_args(start=0, end=5)
experiment.excluded_regions.add_from_args(start=165, end=180)
experiment.linked_phases.add_from_args(id='lbco', scale=10.0)

# %%
# ## Step 4: Perform Analysis
sample_model.cell.length_a.free = True
sample_model.atom_sites['La'].b_iso.free = True
sample_model.atom_sites['Ba'].b_iso.free = True
sample_model.atom_sites['Co'].b_iso.free = True
sample_model.atom_sites['O'].b_iso.free = True

experiment.instrument.calib_twotheta_offset.free = True
experiment.peak.broad_gauss_u.free = True
experiment.peak.broad_gauss_v.free = True
experiment.peak.broad_gauss_w.free = True
experiment.peak.broad_lorentz_y.free = True
experiment.background['10'].y.free = True
experiment.background['30'].y.free = True
experiment.background['50'].y.free = True
experiment.background['110'].y.free = True
experiment.background['165'].y.free = True
experiment.linked_phases['lbco'].scale.free = True

# %%
sample_model.cell.length_a = 3.88
project.analysis.fit()

# %%
#project.plot_meas_vs_calc(expt_name='hrpt', show_residual=True)

# %%
project.analysis.show_all_params()

# %%
project.analysis.show_fittable_params()

# %%
project.analysis.show_free_params()

# %%
project.analysis.how_to_access_parameters()

# %%
project.analysis.show_parameter_cif_uids()
