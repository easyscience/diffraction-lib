'''
Single Fit Example (Basic Usage)

This example demonstrates the use of the EasyDiffraction API with a simplified,
user-friendly approach that mimics the GUI workflow. It is intended for users
with minimal programming experience who want to learn how to perform standard
fitting of crystal structures using diffraction data. The script covers
creating a project, adding sample models and experiments, performing analysis,
and refining parameters.

Only a single import is required (`import easydiffraction as ed`) and all
operations are performed through high-level project components such as
`project.sample_models`, `project.experiments`, and `project.analysis`.
'''

import easydiffraction as ed

###############################################################################
# In this section, users will learn how to create a project and define
# its metadata.
###############################################################################

print(ed.chapter('Step 1: Create a Project'))

# Create a new project
project = ed.Project(name='lbco_hrpt')

# Define project info
project.info.title = 'La0.5Ba0.5CoO3 from neutron diffraction at HRPT@PSI'
project.info.description = '''This project demonstrates a standard refinement 
of La0.5Ba0.5CoO3, which crystallizes in a perovskite-type structure, using 
neutron powder diffraction data collected in constant wavelength mode at the 
HRPT diffractometer (PSI).'''

# Save the initial project specifying the directory path
# The project will be saved in a temporary location defined by the system.
project.save_as(dir_path='lbco_hrpt', temporary=True)

# Show project metadata
project.info.show_as_cif()

###############################################################################
# This section covers how to add sample models and modify their
# parameters.
###############################################################################

print(ed.chapter('Step 2: Add Sample Model'))

# Add a sample model with default parameters
project.sample_models.add(name='lbco')

# Show names of the models added. Those names are used for accessing the
# model using this syntax: project.sample_models['model_name']. That is,
# accessing all the model parameters is done via the project object.

print(ed.section('Show defined sample models'))
project.sample_models.show_names()

print(ed.section('Modify sample model parameters'))

# Space group
project.sample_models['lbco'].space_group.name_h_m = 'P m -3 m'
project.sample_models['lbco'].space_group.it_coordinate_system_code = '1'

# Unit cell parameters
project.sample_models['lbco'].cell.length_a = 3.88

# Atom sites
project.sample_models['lbco'].atom_sites.add(label='La',
                                             type_symbol='La',
                                             fract_x=0,
                                             fract_y=0,
                                             fract_z=0,
                                             wyckoff_letter='a',
                                             b_iso=0.5,
                                             occupancy=0.5)
project.sample_models['lbco'].atom_sites.add(label='Ba',
                                             type_symbol='Ba',
                                             fract_x=0,
                                             fract_y=0,
                                             fract_z=0,
                                             wyckoff_letter='a',
                                             b_iso=0.5,
                                             occupancy=0.5)
project.sample_models['lbco'].atom_sites.add(label='Co',
                                             type_symbol='Co',
                                             fract_x=0.5,
                                             fract_y=0.5,
                                             fract_z=0.5,
                                             wyckoff_letter='b',
                                             b_iso=0.5)
project.sample_models['lbco'].atom_sites.add(label='O',
                                             type_symbol='O',
                                             fract_x=0,
                                             fract_y=0.5,
                                             fract_z=0.5,
                                             wyckoff_letter='c',
                                             b_iso=0.5)

#  Apply symmetry constraints
project.sample_models['lbco'].apply_symmetry_constraints()

print(ed.section('Show sample model as CIF'))
project.sample_models['lbco'].show_as_cif()

print(ed.section('Show sample model structure'))
project.sample_models['lbco'].show_structure()

# Save the project state after adding sample models
project.save()

###############################################################################
# This section teaches users how to add experiments, configure their
# parameters, and link to them the sample models defined in the previous step.
###############################################################################

print(ed.chapter('Step 3: Add Experiments (Instrument models and measured data)'))

# Add neutron powder diffraction experiment
project.experiments.add(name='hrpt',
                        sample_form='powder',
                        beam_mode='constant wavelength',
                        radiation_probe='neutron',
                        data_path='examples/data/hrpt_lbco.xye')

print(ed.section('Show defined experiments'))
project.experiments.show_names()

print(ed.section('Show measured data'))
project.plot_meas_vs_calc(expt_name='hrpt', x_min=65, x_max=68)

print(ed.section('Modify experimental parameters'))

# Instrument parameters
project.experiments['hrpt'].instrument.setup_wavelength = 1.494
project.experiments['hrpt'].instrument.calib_twotheta_offset = 0.6

# Peak profile parameters
project.experiments['hrpt'].show_supported_peak_profile_types()
project.experiments['hrpt'].show_current_peak_profile_type()
project.experiments['hrpt'].peak_profile_type = 'pseudo-voigt'  # Default
project.experiments['hrpt'].peak.broad_gauss_u = 0.1
project.experiments['hrpt'].peak.broad_gauss_v = -0.1
project.experiments['hrpt'].peak.broad_gauss_w = 0.1
project.experiments['hrpt'].peak.broad_lorentz_x = 0
project.experiments['hrpt'].peak.broad_lorentz_y = 0.1

# Add a background
project.experiments['hrpt'].show_supported_background_types()
project.experiments['hrpt'].show_current_background_type()
project.experiments['hrpt'].background_type = 'line-segment'  # Default
project.experiments['hrpt'].background.add(x=10, y=170)
project.experiments['hrpt'].background.add(x=30, y=170)
project.experiments['hrpt'].background.add(x=50, y=170)
project.experiments['hrpt'].background.add(x=110, y=170)
project.experiments['hrpt'].background.add(x=165, y=170)
project.experiments['hrpt'].background.show()

# Link sample model (defined in the previous step) to the experiment
project.experiments['hrpt'].linked_phases.add(id='lbco', scale=10.0)

print(ed.section('Show experiment as CIF'))
project.experiments['hrpt'].show_as_cif()

# Save the project state after adding experiments
project.save()

###############################################################################
# This section will guide users through the analysis process, including
# setting up calculators and fitting models.
###############################################################################

print(ed.chapter('Step 4: Analysis'))

print(ed.section('Set calculator'))
project.analysis.show_supported_calculators()
project.analysis.show_current_calculator()
project.analysis.current_calculator = 'cryspy'  # Default
#project.analysis.current_calculator = 'crysfml'

print(ed.section('Show calculated data'))
project.plot_calc(expt_name='hrpt', x_min=65, x_max=68)

print(ed.section('Show calculated vs measured data'))
project.plot_meas_vs_calc(expt_name='hrpt', x_min=65, x_max=68)

# 1. All parameters include both
#    * Descriptors (not subject to fitting), such as space group names, etc.
#    * Fittable parameters, such as unit cell dimensions, etc.
# 2. Fittable parameters are those that can be optimized during fitting.
# 3. Free parameters are a subset of fittable ones that are currently
#    selected to be optimized.

print(ed.section('Show all parameters'))
project.analysis.show_all_params()

print(ed.section('Show all fittable parameters'))
project.analysis.show_fittable_params()

print(ed.section('Show only free parameters'))
project.analysis.show_free_params()

print(ed.section('Show how to access parameters in the code'))
project.analysis.how_to_access_parameters(show_description=False)

print(ed.section('Set fit mode'))
project.analysis.show_available_fit_modes()
project.analysis.show_current_fit_mode()
project.analysis.fit_mode = 'single'  # Default

print(ed.section('Set fitting engine'))
project.analysis.show_available_minimizers()
project.analysis.show_current_minimizer()
project.analysis.current_minimizer = 'lmfit (leastsq)'  # Default

# ------------ 1st fitting ------------

print(ed.section('Select specific parameters for fitting'))
# Sample model parameters
project.sample_models['lbco'].cell.length_a.free = True
# Experimental parameters
project.experiments['hrpt'].linked_phases['lbco'].scale.free = True
project.experiments['hrpt'].instrument.calib_twotheta_offset.free = True
project.experiments['hrpt'].background['10'].y.free = True
project.experiments['hrpt'].background['30'].y.free = True
project.experiments['hrpt'].background['50'].y.free = True
project.experiments['hrpt'].background['110'].y.free = True
project.experiments['hrpt'].background['165'].y.free = True
# Show free parameters after selection
project.analysis.show_free_params()

print(ed.section('Start fitting'))
project.analysis.fit()

print(ed.section('Show data charts after 1st fitting'))
project.plot_meas_vs_calc(expt_name='hrpt', x_min=65, x_max=68)

# ------------ 2nd fitting ------------

print(ed.section('Select more parameters for fitting'))
# Experimental parameters
project.experiments['hrpt'].peak.broad_gauss_u.free = True
project.experiments['hrpt'].peak.broad_gauss_v.free = True
project.experiments['hrpt'].peak.broad_gauss_w.free = True
project.experiments['hrpt'].peak.broad_lorentz_y.free = True
# Show free parameters after selection
project.analysis.show_free_params()

print(ed.section('Start 2nd fitting'))
project.analysis.fit()

print(ed.section('Show data charts after 2nd fitting'))
project.plot_meas_vs_calc(expt_name='hrpt', x_min=65, x_max=68, show_residual=True)

# ------------ 3rd fitting ------------

print(ed.section('Select more parameters for fitting'))
# Sample model parameters
project.sample_models['lbco'].atom_sites['La'].b_iso.free = True
project.sample_models['lbco'].atom_sites['Ba'].b_iso.free = True
project.sample_models['lbco'].atom_sites['Co'].b_iso.free = True
project.sample_models['lbco'].atom_sites['O'].b_iso.free = True
# Show free parameters after selection
project.analysis.show_free_params()

print(ed.section('Start 3rd fitting'))
project.analysis.fit()

print(ed.section('Show data charts after 3rd fitting'))
project.plot_meas_vs_calc(expt_name='hrpt', x_min=65, x_max=68, show_residual=True)

# ------------ 4th fitting ------------

# User-defined constraints

# Set aliases for parameters
project.analysis.aliases.add(
    label='biso_La',
    param_uid=project.sample_models['lbco'].atom_sites['La'].b_iso.uid
)
project.analysis.aliases.add(
    label='biso_Ba',
    param_uid=project.sample_models['lbco'].atom_sites['Ba'].b_iso.uid
)

# Set constraints
project.analysis.constraints.add(
    lhs_alias='biso_Ba',
    rhs_expr='biso_La'
)
project.analysis.show_constraints()

# Show free parameters before applying constraints
project.analysis.show_free_params()
# Apply constraints
project.analysis.apply_constraints()
# Show free parameters after applying constraints
project.analysis.show_free_params()

print(ed.section('Start 4th fitting'))
project.analysis.fit()

print(ed.section('Show data charts after 4th fitting'))
project.plot_meas_vs_calc(expt_name='hrpt', x_min=65, x_max=68, show_residual=True)

# ------------ 5th fitting ------------

# Set more aliases for parameters
project.analysis.aliases.add(
    label='occ_La',
    param_uid=project.sample_models['lbco'].atom_sites['La'].occupancy.uid
)
project.analysis.aliases.add(
    label='occ_Ba',
    param_uid=project.sample_models['lbco'].atom_sites['Ba'].occupancy.uid
)

# Set more constraints
project.analysis.show_constraints()
project.analysis.constraints.add(
    lhs_alias='occ_Ba',
    rhs_expr='1 - occ_La'
)
project.analysis.show_constraints()

# Apply constraints
project.analysis.apply_constraints()

print(ed.section('Select more parameters for fitting'))
project.sample_models['lbco'].atom_sites['La'].occupancy.free = True

print(ed.section('Start 5th fitting'))
project.analysis.fit()

print(ed.section('Show data charts after 5th fitting'))
project.plot_meas_vs_calc(expt_name='hrpt', x_min=65, x_max=68, show_residual=True)

# Show analysis as CIF
project.analysis.show_as_cif()

# Save the project state after analysis
project.save()

###############################################################################
# In this final section, users will learn how to review the results of
# the analysis
###############################################################################
print(ed.chapter('Step 5: Summary'))
project.summary.show_report()
