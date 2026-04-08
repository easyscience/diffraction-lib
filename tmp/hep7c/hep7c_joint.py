# %% [markdown]
# # Structure Refinement: LaM7O3, X-rays
#
# In this example, LaM7O3 (M = Ti, Cr, Mn, Fe, Co, Ni, Cu) structure is
# refined using two X-ray powder diffraction datasets collected at room
# temperature. The two datasets are from the same sample, but collected
# at different beamlines with different instrumental setups. A joint
# refinement is performed using both datasets simultaneously, with
# constraints applied to ensure that the Biso values of all M sites are
# the same, and the Biso values of the two O sites are the same.

# %% [markdown]
# ## Import Library

# %%
import easydiffraction as ed

# %% [markdown]
# ## Step 1: Define Project

# %%
project = ed.Project(
    name='hep7c_joint',
    description='LaM7O3 structure refinement using X-ray data.',
)

# %%
project.save_as(f'{project.name}', temporary=False)

# %% [markdown]
# ## Step 2: Define Structure

# %%
project.structures.add_from_cif_path('hep7c_II/structures/lam7o3.cif')

# %%
project.structures.show_names()

# %%
structure = project.structures['lam7o3']

# %% [markdown]
# ## Step 3: Define Experiment

# %%
project.experiments.add_from_cif_path('hep7c_I/experiments/pd_xray_1.cif')
project.experiments.add_from_cif_path('hep7c_II/experiments/pd_xray_2.cif')

# %%
project.experiments.show_names()

# %%
experiment_1 = project.experiments['pd_xray_1']
experiment_2 = project.experiments['pd_xray_2']

# %%
# As we have a slight mismatch in the cell parameter values of the two
# experiments, let's assume that this is due to a mismatch of the
# wavelength in the first experiment, and that the wavelength of the
# second experiment is correct. In this case, we can adjust the
# wavelength of the first experiment to align the cell parameter values.
# This is needed during joint refinement to ensure that the same
# structure is being refined against both datasets.
experiment_1.instrument.setup_wavelength = 0.2084

# %% [markdown]
# ## Step 4: Set free parameters
#
# All parameters with standard uncertainties in the input CIF files are
# refined by default.
#
# Allow the wavelength of the first experiment to vary during
# refinement, as it was adjusted manually in the previous step to align
# the cell parameters of the two experiments.

# %%
experiment_1.instrument.setup_wavelength.free = True

# %% [markdown]
# Let's assume that the background of both experiments is
# well-characterized and should not be refined.

# %%
for point in experiment_1.background:
    point.y.free = False
for point in experiment_2.background:
    point.y.free = False

# %%
project.analysis.display.free_params()

# %% [markdown]
# ## Step 5: Define constraints
#
# Create aliases for those parameters that we want to reference in
# constraint expressions. In this example, we want to constrain the Biso
# values of all M sites to be the same, and the Biso values of the two O
# sites to be the same.

# %%
# M sites: Ti, Cr, Mn, Fe, Co, Ni, Cu
project.analysis.aliases.create(
    label='biso_Ti',
    param=structure.atom_sites['Ti'].b_iso,
)
project.analysis.aliases.create(
    label='biso_Cr',
    param=structure.atom_sites['Cr'].b_iso,
)
project.analysis.aliases.create(
    label='biso_Mn',
    param=structure.atom_sites['Mn'].b_iso,
)
project.analysis.aliases.create(
    label='biso_Fe',
    param=structure.atom_sites['Fe'].b_iso,
)
project.analysis.aliases.create(
    label='biso_Co',
    param=structure.atom_sites['Co'].b_iso,
)
project.analysis.aliases.create(
    label='biso_Ni',
    param=structure.atom_sites['Ni'].b_iso,
)
project.analysis.aliases.create(
    label='biso_Cu',
    param=structure.atom_sites['Cu'].b_iso,
)

# O sites: O1, O2
project.analysis.aliases.create(
    label='biso_O1',
    param=structure.atom_sites['O1'].b_iso,
)
project.analysis.aliases.create(
    label='biso_O2',
    param=structure.atom_sites['O2'].b_iso,
)

# %% [markdown]
# Set constraints using the aliases. In this example, all M sites are
# constrained to have the same Biso, and the two O sites are constrained
# to have the same Biso.

# %%
project.analysis.constraints.create(expression='biso_Cr = biso_Ti')
project.analysis.constraints.create(expression='biso_Mn = biso_Ti')
project.analysis.constraints.create(expression='biso_Fe = biso_Ti')
project.analysis.constraints.create(expression='biso_Co = biso_Ti')
project.analysis.constraints.create(expression='biso_Ni = biso_Ti')
project.analysis.constraints.create(expression='biso_Cu = biso_Ti')
project.analysis.constraints.create(expression='biso_O2 = biso_O1')

# %% [markdown]
# Show defined constraints.

# %%
project.analysis.display.constraints()

# %% [markdown]
# ## Step 6: Perform Analysis

# %%
project.plotter.plot_meas_vs_calc(expt_name='pd_xray_1')
project.plotter.plot_meas_vs_calc(expt_name='pd_xray_2')

# %% [markdown]
# #### Set Fit Mode and Weights

# %%
project.analysis.show_supported_fit_mode_types()

# %%
project.analysis.fit_mode.mode = 'joint'
project.analysis.joint_fit_experiments.create(id='pd_xray_1', weight=0.5)
project.analysis.joint_fit_experiments.create(id='pd_xray_2', weight=0.5)

# %%
project.analysis.show_current_fit_mode_type()

# %% [markdown]
# Rietveld refinement is performed by calling the `fit()` method of the
# `analysis` object of the project.

# %%
project.analysis.fit()

# %% [markdown]
# Show results of the fit.

# %%
project.analysis.display.fit_results()

# %% [markdown]
# Plot measured vs calculated data for the experiment, including the residual.

# %%
project.plotter.plot_meas_vs_calc(expt_name='pd_xray_1', show_residual=True)

# %%
project.plotter.plot_meas_vs_calc(expt_name='pd_xray_2', show_residual=True)

# %% [markdown]
# Plot measured vs calculated data with the x-axis in d-spacing instead
# of 2-theta.

# %%
project.plotter.plot_meas_vs_calc(
    expt_name='pd_xray_1',
    x='d_spacing',
    x_min=0.95,
    x_max=4.5,
)

# %%
project.plotter.plot_meas_vs_calc(
    expt_name='pd_xray_2',
    x='d_spacing',
    x_min=0.95,
    x_max=4.5,
)

# %% [markdown]
# ## Step 7: Show Project Summary

# %%
project.summary.show_report()
