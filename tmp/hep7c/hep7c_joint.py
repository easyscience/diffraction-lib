# %% [markdown]
# # Structure Refinement: LaM7O3, Synchrotron
#
# In this example, LaM7O3 (M = Ti, Cr, Mn, Fe, Co, Ni, Cu) structure is
# refined using x-ray powder diffraction data.

# %% [markdown]
# ## Import Library

# %%
import easydiffraction as ed

# %% [markdown]
# ## Step 1: Define Project

# %%
project = ed.Project(
    name='hep7c_joint',
    description='LaM7O3 structure refinement using synchrotron data.',
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
pd_xray_1 = project.experiments['pd_xray_1']
pd_xray_2 = project.experiments['pd_xray_2']

# %%
pd_xray_1.instrument.setup_wavelength = 0.2084

# %%
#pd_xray_2.peak_profile_type = 'split pseudo-voigt'

# %%
#pd_xray_2.peak.broad_gauss_u = 0.03947720
#pd_xray_2.peak.broad_gauss_v = -0.03348092
#pd_xray_2.peak.broad_gauss_w = 0.01329175
#pd_xray_2.peak.broad_lorentz_x = 0.13411663
#pd_xray_2.peak.broad_lorentz_y = 0.0032597019

#pd_xray_2.peak.asym_empir_1 = -0.00566042
#pd_xray_2.peak.asym_empir_2 = 0.06776242
#pd_xray_2.peak.asym_empir_3 = -0.16819821
#pd_xray_2.peak.asym_empir_4 = -0.16669250

# %%
pd_xray_1.show_as_cif()
pd_xray_2.show_as_cif()


# %% [markdown]
# ## Step 5: Set free parameters
#
# All parameters with standard uncertainties in the input CIF files are
# refined by default.

# %%
pd_xray_1.instrument.setup_wavelength.free = True

# %%
#pd_xray_2.peak.asym_empir_1.free = True
#pd_xray_2.peak.asym_empir_2.free = True
#pd_xray_2.peak.asym_empir_3.free = True
#pd_xray_2.peak.asym_empir_4.free = True

#pd_xray_2.peak.broad_gauss_u.free = True
#pd_xray_2.peak.broad_gauss_v.free = True
#pd_xray_2.peak.broad_gauss_w.free = True
#pd_xray_2.peak.broad_lorentz_x.free = True

# %%
for point in pd_xray_1.background:
    point.y.free = False

# %%
for point in pd_xray_2.background:
    point.y.free = False

# %%
project.analysis.display.free_params()

# %% [markdown]
# ## Step 6: Define constraints
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
# ## Step 7: Perform Analysis

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
