# %%
from easydiffraction.datablocks.experiment.categories.background.factory import BackgroundFactory
# %%

# %%

import easydiffraction as ed

# %%
project = ed.Project(name='lbco_hrpt')

# %%
project.experiments.create(
    name='hrpt',
    sample_form='powder',
    beam_mode='time-of-flight',  # 'constant wavelength'
    radiation_probe='neutron',
    scattering_type='bragg',
)

# %%
expt = project.experiments['hrpt']

# %%
expt.show_current_peak_profile_type()

# %%
expt.show_supported_peak_profile_types()

# %%
expt.show_current_background_type()

# %%
expt.show_supported_background_types()

# %%
expt.background.show_supported()

# %%
expt.background_type = "chebyshev"

# %%
expt.show_current_background_type()

# %%
expt.background_type = "chebyshev"

# %%
expt.show_current_background_type()

# %%
print(expt.background)

# %%
expt.background_type = "line-segment"

# %%
print(expt.background)

# %%
expt.background.create(id='a', x=10.0, y=100.0)

# %%
print(expt.background)

# %%
expt.background['a']

# %%
print(expt.background['a'])

# %%
type(expt.background['a'])

# %%
type(expt.background)

# %%
expt.background.show()

# %%
expt.show_as_cif()

# %%
expt.background['a'].x = 2

# %%
expt.background_type = "chebyshev"

# %%
expt.background['a'].x = 2

# %%

# %%

# %%

# %%
bkg = BackgroundFactory.create("chebyshew")

# %%

# %%

# %%

# %%

# %%
project.analysis.show_supported_calculators()


# %% [markdown]
# #### Show Defined Experiments

# %%
project.experiments.show_names()

# %% [markdown]
# #### Show Measured Data

# %%
project.plot_meas(expt_name='hrpt')

# %% [markdown]
# #### Set Instrument
#
# Modify the default instrument parameters.

# %%
project.experiments['hrpt'].instrument.setup_wavelength = 1.494
project.experiments['hrpt'].instrument.calib_twotheta_offset = 0.6

# %% [markdown]
# #### Set Peak Profile
#
# Show supported peak profile types.

# %%
project.experiments['hrpt'].show_supported_peak_profile_types()

# %% [markdown]
# Show the current peak profile type.

# %%
project.experiments['hrpt'].show_current_peak_profile_type()

# %% [markdown]
# Select the desired peak profile type.

# %%
project.experiments['hrpt'].peak_profile_type = 'pseudo-voigt'

# %% [markdown]
# Modify default peak profile parameters.

# %%
project.experiments['hrpt'].peak.broad_gauss_u = 0.1
project.experiments['hrpt'].peak.broad_gauss_v = -0.1
project.experiments['hrpt'].peak.broad_gauss_w = 0.1
project.experiments['hrpt'].peak.broad_lorentz_x = 0
project.experiments['hrpt'].peak.broad_lorentz_y = 0.1

# %% [markdown]
# #### Set Background

# %% [markdown]
# Show supported background types.

# %%
project.experiments['hrpt'].show_supported_background_types()

# %% [markdown]
# Show current background type.

# %%
project.experiments['hrpt'].show_current_background_type()

# %% [markdown]
# Select the desired background type.

# %%
project.experiments['hrpt'].background_type = 'line-segment'

# %% [markdown]
# Add background points.

# %%
project.experiments['hrpt'].background.create(id='10', x=10, y=170)
project.experiments['hrpt'].background.create(id='30', x=30, y=170)
project.experiments['hrpt'].background.create(id='50', x=50, y=170)
project.experiments['hrpt'].background.create(id='110', x=110, y=170)
project.experiments['hrpt'].background.create(id='165', x=165, y=170)

# %% [markdown]
# Show current background points.

# %%
project.experiments['hrpt'].background.show()

# %% [markdown]
# #### Set Linked Phases
#
# Link the structure defined in the previous step to the experiment.

# %%
project.experiments['hrpt'].linked_phases.create(id='lbco', scale=10.0)

# %% [markdown]
# #### Show Experiment as CIF

# %%
project.experiments['hrpt'].show_as_cif()

# %% [markdown]
# #### Save Project State

# %%
project.save()

# %% [markdown]
# ## Step 4: Perform Analysis
#
# This section explains the analysis process, including how to set up
# calculation and fitting engines.
#
# #### Set Calculator
#
# Show supported calculation engines.

# %%
project.analysis.show_supported_calculators()

# %% [markdown]
# Show current calculation engine.

# %%
project.analysis.show_current_calculator()

# %% [markdown]
# Select the desired calculation engine.

# %%
project.analysis.current_calculator = 'cryspy'

# %% [markdown]
# #### Show Calculated Data

# %%
project.plot_calc(expt_name='hrpt')

# %% [markdown]
# #### Plot Measured vs Calculated

# %%
project.plot_meas_vs_calc(expt_name='hrpt', show_residual=True)

# %%
project.plot_meas_vs_calc(expt_name='hrpt', x_min=38, x_max=41, show_residual=True)

# %% [markdown]
# #### Show Parameters
#
# Show all parameters of the project.

# %%
# project.analysis.show_all_params()

# %% [markdown]
# Show all fittable parameters.

# %%
project.analysis.show_fittable_params()

# %% [markdown]
# Show only free parameters.

# %%
project.analysis.show_free_params()

# %% [markdown]
# Show how to access parameters in the code.

# %%
# project.analysis.how_to_access_parameters()

# %% [markdown]
# #### Set Fit Mode
#
# Show supported fit modes.

# %%
project.analysis.show_available_fit_modes()

# %% [markdown]
# Show current fit mode.

# %%
project.analysis.show_current_fit_mode()

# %% [markdown]
# Select desired fit mode.

# %%
project.analysis.fit_mode = 'single'

# %% [markdown]
# #### Set Minimizer
#
# Show supported fitting engines.

# %%
project.analysis.show_available_minimizers()

# %% [markdown]
# Show current fitting engine.

# %%
project.analysis.show_current_minimizer()

# %% [markdown]
# Select desired fitting engine.

# %%
project.analysis.current_minimizer = 'lmfit (leastsq)'

# %% [markdown]
# ### Perform Fit 1/5
#
# Set structure parameters to be refined.

# %%
project.structures['lbco'].cell.length_a.free = True

# %% [markdown]
# Set experiment parameters to be refined.

# %%
project.experiments['hrpt'].linked_phases['lbco'].scale.free = True
project.experiments['hrpt'].instrument.calib_twotheta_offset.free = True
project.experiments['hrpt'].background['10'].y.free = True
project.experiments['hrpt'].background['30'].y.free = True
project.experiments['hrpt'].background['50'].y.free = True
project.experiments['hrpt'].background['110'].y.free = True
project.experiments['hrpt'].background['165'].y.free = True

# %% [markdown]
# Show free parameters after selection.

# %%
project.analysis.show_free_params()

# %% [markdown]
# #### Run Fitting

# %%
project.analysis.fit()
project.analysis.show_fit_results()

# %% [markdown]
# #### Plot Measured vs Calculated

# %%
project.plot_meas_vs_calc(expt_name='hrpt', show_residual=True)

# %%
project.plot_meas_vs_calc(expt_name='hrpt', x_min=38, x_max=41, show_residual=True)

# %% [markdown]
# #### Save Project State

# %%
project.save_as(dir_path='lbco_hrpt', temporary=True)

# %% [markdown]
# ### Perform Fit 2/5
#
# Set more parameters to be refined.

# %%
project.experiments['hrpt'].peak.broad_gauss_u.free = True
project.experiments['hrpt'].peak.broad_gauss_v.free = True
project.experiments['hrpt'].peak.broad_gauss_w.free = True
project.experiments['hrpt'].peak.broad_lorentz_y.free = True

# %% [markdown]
# Show free parameters after selection.

# %%
project.analysis.show_free_params()

# %% [markdown]
# #### Run Fitting

# %%
project.analysis.fit()
project.analysis.show_fit_results()

# %% [markdown]
# #### Plot Measured vs Calculated

# %%
project.plot_meas_vs_calc(expt_name='hrpt', show_residual=True)

# %%
project.plot_meas_vs_calc(expt_name='hrpt', x_min=38, x_max=41, show_residual=True)

# %% [markdown]
# #### Save Project State

# %%
project.save_as(dir_path='lbco_hrpt', temporary=True)

# %% [markdown]
# ### Perform Fit 3/5
#
# Set more parameters to be refined.

# %%
project.structures['lbco'].atom_sites['La'].b_iso.free = True
project.structures['lbco'].atom_sites['Ba'].b_iso.free = True
project.structures['lbco'].atom_sites['Co'].b_iso.free = True
project.structures['lbco'].atom_sites['O'].b_iso.free = True

# %% [markdown]
# Show free parameters after selection.

# %%
project.analysis.show_free_params()

# %% [markdown]
# #### Run Fitting

# %%
project.analysis.fit()
project.analysis.show_fit_results()

# %% [markdown]
# #### Plot Measured vs Calculated

# %%
project.plot_meas_vs_calc(expt_name='hrpt', show_residual=True)

# %%
project.plot_meas_vs_calc(expt_name='hrpt', x_min=38, x_max=41, show_residual=True)

# %% [markdown]
# #### Save Project State

# %%
project.save_as(dir_path='lbco_hrpt', temporary=True)

# %% [markdown]
# ### Perform Fit 4/5
#
# #### Set Constraints
#
# Set aliases for parameters.

# %%
project.analysis.aliases.create(
    label='biso_La',
    param_uid=project.structures['lbco'].atom_sites['La'].b_iso.uid,
)
project.analysis.aliases.create(
    label='biso_Ba',
    param_uid=project.structures['lbco'].atom_sites['Ba'].b_iso.uid,
)

# %% [markdown]
# Set constraints.

# %%
project.analysis.constraints.create(lhs_alias='biso_Ba', rhs_expr='biso_La')

# %% [markdown]
# Show defined constraints.

# %%
project.analysis.show_constraints()

# %% [markdown]
# Show free parameters before applying constraints.

# %%
project.analysis.show_free_params()

# %% [markdown]
# Apply constraints.

# %%
project.analysis.apply_constraints()

# %% [markdown]
# Show free parameters after applying constraints.

# %%
project.analysis.show_free_params()

# %% [markdown]
# #### Run Fitting

# %%
project.analysis.fit()
project.analysis.show_fit_results()

# %% [markdown]
# #### Plot Measured vs Calculated

# %%
project.plot_meas_vs_calc(expt_name='hrpt', show_residual=True)

# %%
project.plot_meas_vs_calc(expt_name='hrpt', x_min=38, x_max=41, show_residual=True)

# %% [markdown]
# #### Save Project State

# %%
project.save_as(dir_path='lbco_hrpt', temporary=True)

# %% [markdown]
# ### Perform Fit 5/5
#
# #### Set Constraints
#
# Set more aliases for parameters.

# %%
project.analysis.aliases.create(
    label='occ_La',
    param_uid=project.structures['lbco'].atom_sites['La'].occupancy.uid,
)
project.analysis.aliases.create(
    label='occ_Ba',
    param_uid=project.structures['lbco'].atom_sites['Ba'].occupancy.uid,
)

# %% [markdown]
# Set more constraints.

# %%
project.analysis.constraints.create(
    lhs_alias='occ_Ba',
    rhs_expr='1 - occ_La',
)

# %% [markdown]
# Show defined constraints.

# %%
project.analysis.show_constraints()

# %% [markdown]
# Apply constraints.

# %%
project.analysis.apply_constraints()

# %% [markdown]
# Set structure parameters to be refined.

# %%
project.structures['lbco'].atom_sites['La'].occupancy.free = True

# %% [markdown]
# Show free parameters after selection.

# %%
project.analysis.show_free_params()

# %% [markdown]
# #### Run Fitting

# %%
project.analysis.fit()
project.analysis.show_fit_results()

# %% [markdown]
# #### Plot Measured vs Calculated

# %%
project.plot_meas_vs_calc(expt_name='hrpt', show_residual=True)

# %%
project.plot_meas_vs_calc(expt_name='hrpt', x_min=38, x_max=41, show_residual=True)

# %% [markdown]
# #### Save Project State

# %%
project.save_as(dir_path='lbco_hrpt', temporary=True)

# %% [markdown]
# ## Step 5: Summary
#
# This final section shows how to review the results of the analysis.

# %% [markdown]
# #### Show Project Summary

# %%
project.summary.show_report()

# %%
