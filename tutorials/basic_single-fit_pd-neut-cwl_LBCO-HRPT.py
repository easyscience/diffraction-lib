# %% [markdown]
# # Single Fit (Basic Usage)
#
# This example demonstrates the use of the EasyDiffraction API with a
# simplified, user-friendly approach that mimics the GUI workflow. It is
# intended for users with minimal programming experience who want to learn how
# to perform standard fitting of crystal structures using diffraction data. The
# script covers creating a project, adding sample models and experiments,
# performing analysis, and refining parameters.
#
# Only a single import of `easydiffraction` is required and all
# operations are performed through high-level components of the `project`
# object, such as `project.sample_models`, `project.experiments`, and
# `project.analysis`. Project is the main object to store all the information.

# %% [markdown]
# ## Import EasyDiffraction

# %%
import easydiffraction as ed

# %% [markdown]
# ## Step 1: Create a Project
#
# In this section, you will learn how to create a project and define
# its metadata.

# %% [markdown]
# ### Create a new project object

# %%
project = ed.Project(name='lbco_hrpt')

# %% [markdown]
# ### Define project metadata

# %%
project.info.title = 'La0.5Ba0.5CoO3 at HRPT@PSI'
project.info.description = """This project demonstrates a standard 
refinement of La0.5Ba0.5CoO3, which crystallizes in a perovskite-type 
structure, using neutron powder diffraction data collected in constant 
wavelength mode at the HRPT diffractometer (PSI)."""

# %% [markdown]
# ### Show project metadata as CIF

# %%
project.info.show_as_cif()

# %% [markdown]
# ### Save the project
#
# When we save the project for the first time, we need to specify the
# directory path. In the example below, we save the project to the
# temporary location defined by the system.

# %%
project.save_as(dir_path='lbco_hrpt', temporary=True)

# %% [markdown]
# ### Setup data plotter

# %% [markdown]
# Show supported plotting engines

# %%
project.plotter.show_supported_engines()

# %% [markdown]
# Show current plotting configuration

# %%
project.plotter.show_config()

# %% [markdown]
# Set current plotting configuration

# %%
project.plotter.engine = 'plotly'

# %% [markdown]
# ## Step 2: Define Sample Model
#
# This section covers how to add sample models and modify their parameters.

# %% [markdown]
# ### Add new sample model

# %%
project.sample_models.add(name='lbco')

# %% [markdown]
# ### Show defined sample models
#
# Show names of the models added. Those names are used for accessing the
# model using this syntax: project.sample_models['model_name']. That is,
# accessing all the model parameters is done via the project object.

# %%
project.sample_models.show_names()

# %% [markdown]
# ### Define space group
#
# Modify default space group parameters

# %%
project.sample_models['lbco'].space_group.name_h_m = 'P m -3 m'
project.sample_models['lbco'].space_group.it_coordinate_system_code = '1'

# %% [markdown]
# ### Define unit cell
#
# Modify default unit cell parameters

# %%
project.sample_models['lbco'].cell.length_a = 3.88

# %% [markdown]
# ### Define atom sites
#
# Add atom sites to the sample model

# %%
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

# %% [markdown]
# ### Apply symmetry constraints

# %%
project.sample_models['lbco'].apply_symmetry_constraints()

# %% [markdown]
# ### Show sample model as CIF

# %%
project.sample_models['lbco'].show_as_cif()

# %% [markdown]
# ### Show sample model structure

# %%
project.sample_models['lbco'].show_structure()

# %% [markdown]
# ### Save the project state
#
# Save the project state after adding the sample model. This is important
# to ensure that all changes are stored and can be accessed later. The
# project state is saved in the directory specified during project
# creation.

# %%
project.save()

# %% [markdown]
# ## Step 3: Define Experiment
#
# This section teaches how to add experiments, configure their parameters, and
# link to them the sample models defined in the previous step.

# %% [markdown]
# ### Download measured data
#
# Download the data file from the EasyDiffraction repository on GitHub

# %%
ed.download_from_repository('hrpt_lbco.xye',
                            branch='docs',
                            destination='data')

# %% [markdown]
# ### Add diffraction experiment

# %%
project.experiments.add(name='hrpt',
                        sample_form='powder',
                        beam_mode='constant wavelength',
                        radiation_probe='neutron',
                        data_path='data/hrpt_lbco.xye')

# %% [markdown]
# ### Show defined experiments

# %%
project.experiments.show_names()

# %% [markdown]
# ### Show measured data

# %%
project.plot_meas(expt_name='hrpt')

# %% [markdown]
# ### Define instrument
#
# Modify default instrument parameters

# %%
project.experiments['hrpt'].instrument.setup_wavelength = 1.494
project.experiments['hrpt'].instrument.calib_twotheta_offset = 0.6

# %% [markdown]
# ### Define peak profile

# %% [markdown]
# Show supported peak profiles

# %%
project.experiments['hrpt'].show_supported_peak_profile_types()

# %% [markdown]
# Show current peak profile

# %%
project.experiments['hrpt'].show_current_peak_profile_type()

# %% [markdown]
# Select desired peak profile type

# %%
project.experiments['hrpt'].peak_profile_type = 'pseudo-voigt'

# %% [markdown]
# Modify default peak profile parameters

# %%
project.experiments['hrpt'].peak.broad_gauss_u = 0.1
project.experiments['hrpt'].peak.broad_gauss_v = -0.1
project.experiments['hrpt'].peak.broad_gauss_w = 0.1
project.experiments['hrpt'].peak.broad_lorentz_x = 0
project.experiments['hrpt'].peak.broad_lorentz_y = 0.1

# %% [markdown]
# ### Define background

# %% [markdown]
# Show supported background types

# %%
project.experiments['hrpt'].show_supported_background_types()

# %% [markdown]
# Show current background type

# %%
project.experiments['hrpt'].show_current_background_type()

# %% [markdown]
# Select desired background type

# %%
project.experiments['hrpt'].background_type = 'line-segment'

# %% [markdown]
# Add background points

# %%
project.experiments['hrpt'].background.add(x=10, y=170)
project.experiments['hrpt'].background.add(x=30, y=170)
project.experiments['hrpt'].background.add(x=50, y=170)
project.experiments['hrpt'].background.add(x=110, y=170)
project.experiments['hrpt'].background.add(x=165, y=170)

# %% [markdown]
# Show current background points

# %%
project.experiments['hrpt'].background.show()

# %% [markdown]
# ### Define linked phases
#
# Link sample model defined in the previous step to the experiment

# %%
project.experiments['hrpt'].linked_phases.add(id='lbco', scale=10.0)

# %% [markdown]
# ### Show experiment as CIF

# %%
project.experiments['hrpt'].show_as_cif()

# %% [markdown]
# ### Save the project state

# %%
project.save()

# %% [markdown]
# ## Step 4: Analysis
#
# This section will guide you through the analysis process, including setting
# up calculators and fitting models.
#
# ### Set calculation engine
#
# Show supported calculation engines

# %%
project.analysis.show_supported_calculators()

# %% [markdown]
# Show current calculation engine

# %%
project.analysis.show_current_calculator()

# %% [markdown]
# Select desired calculation engine

# %%
project.analysis.current_calculator = 'cryspy'

# %% [markdown]
# ### Show calculated data

# %%
project.plot_calc(expt_name='hrpt')

# %% [markdown]
# ### Show measured vs calculated

# %%
project.plot_meas_vs_calc(expt_name='hrpt', show_residual=True)
project.plot_meas_vs_calc(expt_name='hrpt', x_min=38, x_max=41, show_residual=True)

# %% [markdown]
# ### Show parameters
#
# Show all parameters of the project

# %%
project.analysis.show_all_params()

# %% [markdown]
# Show all fittable parameters

# %%
project.analysis.show_fittable_params()

# %% [markdown]
# Show only free parameters

# %%
project.analysis.show_free_params()

# %% [markdown]
# Show how to access parameters in the code

# %%
project.analysis.how_to_access_parameters()

# %% [markdown]
# ### Set fit mode
#
# Show supported fit modes

# %%
project.analysis.show_available_fit_modes()

# %% [markdown]
# Show current fit mode

# %%
project.analysis.show_current_fit_mode()

# %% [markdown]
# Select desired fit mode

# %%
project.analysis.fit_mode = 'single'

# %% [markdown]
# ### Set fitting engine
#
# Show supported fitting engines

# %%
project.analysis.show_available_minimizers()

# %% [markdown]
# Show current fitting engine

# %%
project.analysis.show_current_minimizer()

# %% [markdown]
# Select desired fitting engine

# %%
project.analysis.current_minimizer = 'lmfit (leastsq)'

# %% [markdown]
# ### Fitting Step 1/5
#
# Set sample model parameters to be fitted

# %%
project.sample_models['lbco'].cell.length_a.free = True

# %% [markdown]
# Set experimental parameters to be fitted

# %%
project.experiments['hrpt'].linked_phases['lbco'].scale.free = True
project.experiments['hrpt'].instrument.calib_twotheta_offset.free = True
project.experiments['hrpt'].background['10'].y.free = True
project.experiments['hrpt'].background['30'].y.free = True
project.experiments['hrpt'].background['50'].y.free = True
project.experiments['hrpt'].background['110'].y.free = True
project.experiments['hrpt'].background['165'].y.free = True

# %% [markdown]
# Show free parameters after selection

# %%
project.analysis.show_free_params()

# %% [markdown]
# #### Start fitting

# %%
project.analysis.fit()

# %% [markdown]
# #### Show fitting results

# %%
project.plot_meas_vs_calc(expt_name='hrpt', show_residual=True)
project.plot_meas_vs_calc(expt_name='hrpt', x_min=38, x_max=41, show_residual=True)

# %% [markdown]
# #### Save the project state

# %%
project.save_as(dir_path='lbco_hrpt', temporary=True)

# %% [markdown]
# ### Fitting Step 2/5
#
# Set experimental parameters to be fitted

# %%
project.experiments['hrpt'].peak.broad_gauss_u.free = True
project.experiments['hrpt'].peak.broad_gauss_v.free = True
project.experiments['hrpt'].peak.broad_gauss_w.free = True
project.experiments['hrpt'].peak.broad_lorentz_y.free = True

# %% [markdown]
# Show free parameters after selection

# %%
project.analysis.show_free_params()

# %% [markdown]
# #### Start fitting

# %%
project.analysis.fit()

# %% [markdown]
# #### Show fitting results

# %%
project.plot_meas_vs_calc(expt_name='hrpt', show_residual=True)
project.plot_meas_vs_calc(expt_name='hrpt', x_min=38, x_max=41, show_residual=True)

# %% [markdown]
# #### Save the project state

# %%
project.save_as(dir_path='lbco_hrpt', temporary=True)

# %% [markdown]
# ### Fitting Step 3/5
#
# Set sample model parameters to be fitted

# %%
project.sample_models['lbco'].atom_sites['La'].b_iso.free = True
project.sample_models['lbco'].atom_sites['Ba'].b_iso.free = True
project.sample_models['lbco'].atom_sites['Co'].b_iso.free = True
project.sample_models['lbco'].atom_sites['O'].b_iso.free = True

# %% [markdown]
# Show free parameters after selection

# %%
project.analysis.show_free_params()

# %% [markdown]
# #### Start fitting

# %%
project.analysis.fit()

# %% [markdown]
# #### Show fitting results

# %%
project.plot_meas_vs_calc(expt_name='hrpt', show_residual=True)
project.plot_meas_vs_calc(expt_name='hrpt', x_min=38, x_max=41, show_residual=True)

# %% [markdown]
# #### Save the project state

# %%
project.save_as(dir_path='lbco_hrpt', temporary=True)

# %% [markdown]
# ### Fitting Step 4/5
#
# #### Define constraints
#
# Set aliases for parameters

# %%
project.analysis.aliases.add(
    label='biso_La',
    param_uid=project.sample_models['lbco'].atom_sites['La'].b_iso.uid
)
project.analysis.aliases.add(
    label='biso_Ba',
    param_uid=project.sample_models['lbco'].atom_sites['Ba'].b_iso.uid
)

# %% [markdown]
# Set constraints

# %%
project.analysis.constraints.add(
    lhs_alias='biso_Ba',
    rhs_expr='biso_La'
)

# %% [markdown]
# Show defined constraints

# %%
project.analysis.show_constraints()

# %% [markdown]
# Show free parameters before applying constraints

# %%
project.analysis.show_free_params()

# %% [markdown]
# Apply constraints

# %%
project.analysis.apply_constraints()

# %% [markdown]
# Show free parameters after applying constraints

# %%
project.analysis.show_free_params()

# %% [markdown]
# #### Start fitting

# %%
project.analysis.fit()

# %% [markdown]
# #### Show fitting results

# %%
project.plot_meas_vs_calc(expt_name='hrpt', show_residual=True)
project.plot_meas_vs_calc(expt_name='hrpt', x_min=38, x_max=41, show_residual=True)

# %% [markdown]
# #### Save the project state

# %%
project.save_as(dir_path='lbco_hrpt', temporary=True)

# %% [markdown]
# ### Fitting Step 5/5
#
# #### Define constraints
#
# Set aliases for parameters

# %%
project.analysis.aliases.add(
    label='occ_La',
    param_uid=project.sample_models['lbco'].atom_sites['La'].occupancy.uid
)
project.analysis.aliases.add(
    label='occ_Ba',
    param_uid=project.sample_models['lbco'].atom_sites['Ba'].occupancy.uid
)

# %% [markdown]
# Set constraints

# %%
project.analysis.constraints.add(
    lhs_alias='occ_Ba',
    rhs_expr='1 - occ_La'
)

# %% [markdown]
# Show defined constraints

# %%
project.analysis.show_constraints()

# %% [markdown]
# Show free parameters before applying constraints

# %%
project.analysis.show_free_params()

# %% [markdown]
# Apply constraints

# %%
project.analysis.apply_constraints()

# %% [markdown]
# Show free parameters after applying constraints

# %%
project.analysis.show_free_params()

# %% [markdown]
# Set sample model parameters to be fitted

# %%
project.sample_models['lbco'].atom_sites['La'].occupancy.free = True

# %% [markdown]
# Show free parameters after selection

# %%
project.analysis.show_free_params()

# %% [markdown]
# #### Start fitting

# %%
project.analysis.fit()

# %% [markdown]
# #### Show fitting results

# %%
project.plot_meas_vs_calc(expt_name='hrpt', show_residual=True)
project.plot_meas_vs_calc(expt_name='hrpt', x_min=38, x_max=41, show_residual=True)

# %% [markdown]
# #### Save the project state

# %%
project.save_as(dir_path='lbco_hrpt', temporary=True)

# %% [markdown]
# ## Step 5: Summary
#
# In this final section, you will learn how to review the results of the
# analysis

# %% [markdown]
# ### Show project summary report

# %%
project.summary.show_report()
