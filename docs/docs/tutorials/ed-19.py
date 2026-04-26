# %% [markdown]
# # Structure Refinement: LaM7O3, X-Ray
#
# In this example,  LaM7O3 (M = Ti, Cr, Mn, Fe, Co, Ni, Cu) structure is
# refined using synchrotron x-ray powder diffraction data. The example
# includes defining the structure and experiment, setting free
# parameters and constraints, performing Rietveld refinement, and
# plotting results.

# %% [markdown]
# ## Import Library

# %%
import easydiffraction as ed

# %% [markdown]
# ## Step 1: Define Project

# %% [markdown]
# First, we need to create a project object. The project is the main
# container for all structures, experiments, and analysis. It also
# manages saving and loading of data, and provides methods for plotting
# results. The project can be given a name and description for better
# organization.

# %%
project = ed.Project(
    name='hep7c',
    description='LaM7O3 structure refinement using X-ray data.',
)

# %% [markdown]
# Save the project to a desired location. This is necessary before
# running the fit, so that results can be saved to the project
# directory. The `temporary=False` argument ensures that the project is
# saved to a user defined location rather than a temporary directory.

# %%
project.save_as(f'{project.name}', temporary=False)

# %% [markdown]
# ## Step 2: Define Structure

# %% [markdown]
# Second, we need to create a structure in the project. The structure
# will then be linked to the experiment in the next step. The structure
# can be defined in code, or loaded from an external CIF file. In this
# example, we define the structure in code.

# %%
project.structures.create(name='lam7o3')

# %% [markdown]
# Create an alias for the structure, to access its parameters in a more
# convenient way.

# %%
structure = project.structures['lam7o3']

# %% [markdown]
# Set space group. In this example, the space group is Pnma (No. 62),
# and the standard setting is used. The space group can be specified
# using the Hermann-Mauguin notation.
# If system code is not specified, the default setting is used.

# %%
structure.space_group.name_h_m = 'P n m a'
structure.space_group.it_coordinate_system_code = 'abc'

# %% [markdown]
# Set unit cell parameters. In this example, the unit cell is
# orthorhombic, and thus has three independent lengths (a, b, c) and all
# angles are 90 degrees.

# %%
structure.cell.length_a = 5.497532
structure.cell.length_b = 7.781902
structure.cell.length_c = 5.525117

# %% [markdown]
# Add atom sites to the structure, with their parameters. In this
# example, the structure contains 9 atom sites: La, Ti, Cr, Mn, Fe, Co,
# Ni, Cu, O1, and O2. The parameters include fractional coordinates,
# isotropic atomic displacement parameters (Biso), occupancy, and
# Wyckoff letters. Some parameters (e.g. occupancy) are not specified
# for all sites, and thus take default values.

# %%
structure.atom_sites.create(
    label='La',
    type_symbol='La',
    fract_x=0.48446,
    fract_y=0.25,
    fract_z=0.00021,
    wyckoff_letter='c',
    adp_type='Biso',
    adp_iso=1.30369,
)
structure.atom_sites.create(
    label='Ti',
    type_symbol='Ti',
    fract_x=0,
    fract_y=0,
    fract_z=0,
    wyckoff_letter='a',
    occupancy=0.14286,
    adp_type='Biso',
    adp_iso=1.10930,
)
structure.atom_sites.create(
    label='Cr',
    type_symbol='Cr',
    fract_x=0,
    fract_y=0,
    fract_z=0,
    wyckoff_letter='a',
    occupancy=0.14286,
    adp_type='Biso',
    adp_iso=1.10930,
)
structure.atom_sites.create(
    label='Mn',
    type_symbol='Mn',
    fract_x=0,
    fract_y=0,
    fract_z=0,
    wyckoff_letter='a',
    occupancy=0.14286,
    adp_type='Biso',
    adp_iso=1.10930,
)
structure.atom_sites.create(
    label='Fe',
    type_symbol='Fe',
    fract_x=0,
    fract_y=0,
    fract_z=0,
    wyckoff_letter='a',
    occupancy=0.14286,
    adp_type='Biso',
    adp_iso=1.10930,
)
structure.atom_sites.create(
    label='Co',
    type_symbol='Co',
    fract_x=0,
    fract_y=0,
    fract_z=0,
    wyckoff_letter='a',
    occupancy=0.14286,
    adp_type='Biso',
    adp_iso=1.10930,
)
structure.atom_sites.create(
    label='Ni',
    type_symbol='Ni',
    fract_x=0,
    fract_y=0,
    fract_z=0,
    wyckoff_letter='a',
    occupancy=0.14286,
    adp_type='Biso',
    adp_iso=1.10930,
)
structure.atom_sites.create(
    label='Cu',
    type_symbol='Cu',
    fract_x=0,
    fract_y=0,
    fract_z=0,
    wyckoff_letter='a',
    occupancy=0.14286,
    adp_type='Biso',
    adp_iso=1.10930,
)
structure.atom_sites.create(
    label='O1',
    type_symbol='O',
    fract_x=0.50628,
    fract_y=0.25,
    fract_z=0.54423,
    wyckoff_letter='c',
    adp_type='Biso',
    adp_iso=0.25033,
)
structure.atom_sites.create(
    label='O2',
    type_symbol='O',
    fract_x=0.21881,
    fract_y=0.05203,
    fract_z=0.25686,
    wyckoff_letter='d',
    adp_type='Biso',
    adp_iso=0.25033,
)

# %% [markdown]
# Show the structure in CIF format.

# %%
structure.show_as_cif()

# %% [markdown]
# ## Step 3: Define Experiment

# %% [markdown]
# Third, we need to load the experimentally measured data from an
# external file. The data file is plain text, with two columns: the
# first column contains 2-theta values, and the second column contains
# the corresponding intensity values.
# If third column with standard uncertainties for the intensity values
# is absent, it will be automatically generated as the square root of
# the intensity values.

# %%
data_path = ed.download_data(id=32, destination='data')

# %% [markdown]
# Add an experiment to the project, using the measured data from the
# specified path. The radiation probe is set to 'xray' for this example.

# %%
project.experiments.add_from_data_path(
    name='xrd',
    data_path=data_path,
    radiation_probe='xray',
    sample_form='powder',
)

# %% [markdown]
# Create an alias for the structure, to access its parameters in a more
# convenient way.

# %%
experiment = project.experiments['xrd']

# %% [markdown]
# Show all the public attributes and methods of the experiment object,
# which can be used to define the experiment and set parameters.

# %%
experiment.help()

# %% [markdown]
# Link the structure to the experiment and set its scale factor.

# %%
experiment.linked_phases.create(id='lam7o3', scale=0.35960e-02)

# %% [markdown]
# Show all the public attributes and methods of the linked_phases
# category of the experiment object. The same help method can also be
# used for other categories, defined below.

# %%
experiment.linked_phases.help()

# %% [markdown]
# Set instrumental parameters. In this example, the wavelength and
# 2-theta offset are set.

# %%
experiment.instrument.setup_wavelength = 1.54056
experiment.instrument.calib_twotheta_offset = 0.048

# %% [markdown]
# Set peak shape parameters. In this example, a pseudo-Voigt profile is
# used, with Gaussian and Lorentzian contributions to the peak
# broadening.

# %%
experiment.show_peak_profile_types()

# %%
experiment.peak.help()

# %%
experiment.peak_profile_type = 'pseudo-voigt + empirical asymmetry'

# %%
experiment.peak.help()

# %%
experiment.peak.broad_gauss_u = 0.009618201
experiment.peak.broad_gauss_v = -0.012946068
experiment.peak.broad_gauss_w = 0.0058880704
experiment.peak.broad_lorentz_x = 0.020095311
experiment.peak.broad_lorentz_y = 0.0032597019

experiment.peak.asym_empir_1 = 0.0
experiment.peak.asym_empir_2 = 0.0
experiment.peak.asym_empir_3 = 0.0
experiment.peak.asym_empir_4 = 0.0

# %%
experiment.peak.help()

# %% [markdown]
# Define background points. In this example, multiple points are defined
# across the 2-theta range of the experiment, with their x and y values
# taken from the measured data.
# Some points are commented out and thus not used.

# %%
experiment.show_background_types()

# %%
for x, y in [
    (10.1697, 15191.8789),
    (11.0891, 14639.7656),
    (11.8670, 13974.3184),
    (12.8100, 12506.7393),
    (13.6351, 10947.9717),
    (14.7430, 8589.5996),
    (16.0160, 6800.0322),
    (17.0533, 5837.3257),
    (18.5620, 4922.7090),
    (20.4715, 4156.3442),
    (22.4281, 3339.8083),
    (23.3710, 3090.7004),
    (24.9741, 2824.6865),
    (26.6007, 2480.6602),
    (29.4295, 2072.3389),
    (31.5012, 1613.6263),
    (33.8586, 1398.0791),
    (36.8053, 1324.0001),
    (38.8798, 1163.8712),
    (41.2371, 1090.6232),
    (42.7459, 1031.0789),
    (45.6921, 942.9998),
    (47.6629, 944.0351),
    (49.1150, 858.3295),
    (50.4635, 886.5879),
    (51.8897, 835.0275),
    (53.4456, 843.0234),
    (55.0273, 773.7563),
    (56.7907, 836.8652),
    (60.0495, 805.0693),
    (61.5111, 780.1295),
    (62.9962, 775.5878),
    (65.5658, 733.4941),
    (67.1924, 785.8816),
    (68.9840, 785.5795),
    (71.0113, 725.6704),
    (75.7704, 752.8492),
    (79.7779, 774.0583),
    (81.1924, 728.9919),
    (82.6775, 762.2854),
    (85.1056, 753.4788),
    (88.5002, 760.7822),
    (91.7586, 734.2062),
    (93.8850, 824.3625),
    (98.1377, 791.0035),
    (99.8232, 760.6655),
    (103.4795, 787.4377),
    (107.2654, 798.0887),
    (109.9057, 746.7008),
]:
    experiment.background.create(
        id=str(x).replace('.', '_'),
        x=x,
        y=y,
    )

# %% [markdown]
# Set excluded regions. In this example, the region from 0 to 2 degrees
# and the region from 14.97 to 180 degrees are excluded from the fit.

# %%
experiment.excluded_regions.create(id='1', start=0, end=10)
experiment.excluded_regions.create(id='2', start=110, end=180)

# %% [markdown]
# Show the experiment in CIF format.

# %%
experiment.show_as_cif()

# %% [markdown]
# ## Step 4: Set free parameters
#
# Now, set free parameters for the structure. In this example,
# cell parameters, the fractional coordinates of atoms, as well as
# isotropic atomic displacement parameters (Biso) are set free.

# %%
structure.cell.length_a.free = True
structure.cell.length_b.free = True
structure.cell.length_c.free = True

structure.atom_sites['La'].fract_x.free = True
structure.atom_sites['La'].fract_z.free = True
structure.atom_sites['O1'].fract_x.free = True
structure.atom_sites['O1'].fract_z.free = True
structure.atom_sites['O2'].fract_x.free = True
structure.atom_sites['O2'].fract_y.free = True
structure.atom_sites['O2'].fract_z.free = True

structure.atom_sites['La'].adp_iso.free = True
structure.atom_sites['Ti'].adp_iso.free = True
structure.atom_sites['O1'].adp_iso.free = True

# %% [markdown]
# Now, set free parameters for the experiment. In this example, the
# scale factor, instrumental calibration parameter, peak shape
# parameters, and background points are set free.

# %%
experiment.linked_phases['lam7o3'].scale.free = True

experiment.instrument.calib_twotheta_offset.free = True

experiment.peak.broad_gauss_u.free = True
experiment.peak.broad_gauss_v.free = True
experiment.peak.broad_gauss_w.free = True
experiment.peak.broad_lorentz_x.free = True

experiment.peak.asym_empir_2.free = True
experiment.peak.asym_empir_4.free = True

for point in experiment.background:
    point.y.free = True


# %% [markdown]
# Show all free parameters in the experiment.

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
    param=structure.atom_sites['Ti'].adp_iso,
)
project.analysis.aliases.create(
    label='biso_Cr',
    param=structure.atom_sites['Cr'].adp_iso,
)
project.analysis.aliases.create(
    label='biso_Mn',
    param=structure.atom_sites['Mn'].adp_iso,
)
project.analysis.aliases.create(
    label='biso_Fe',
    param=structure.atom_sites['Fe'].adp_iso,
)
project.analysis.aliases.create(
    label='biso_Co',
    param=structure.atom_sites['Co'].adp_iso,
)
project.analysis.aliases.create(
    label='biso_Ni',
    param=structure.atom_sites['Ni'].adp_iso,
)
project.analysis.aliases.create(
    label='biso_Cu',
    param=structure.atom_sites['Cu'].adp_iso,
)

# O sites: O1, O2
project.analysis.aliases.create(
    label='biso_O1',
    param=structure.atom_sites['O1'].adp_iso,
)
project.analysis.aliases.create(
    label='biso_O2',
    param=structure.atom_sites['O2'].adp_iso,
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

# %% [markdown]
# Before performing the fit, we can plot the measured data and compare
# it with the calculated pattern using the initial parameters. This can
# be helpful to check if the initial parameters are reasonable and to
# identify any issues with the data or the model before running the fit.

# %%
project.display.plotter.plot_meas_vs_calc(expt_name='xrd')

# %% [markdown]
# Show supported fitting engines.

# %%
project.analysis.fit.show_minimizer_types()

# %% [markdown]
# Select desired fitting engine.

# %%
project.analysis.fit.minimizer_type = 'bumps (lm)'

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
# Show parameter correlations.

# %%
project.display.plotter.plot_param_correlations()

# %% [markdown]
# Plot measured vs calculated data for the experiment, including the residual.

# %%
project.display.plotter.plot_meas_vs_calc(expt_name='xrd', show_residual=True)

# %%
project.display.plotter.plot_meas_vs_calc(expt_name='xrd', x_min=46.00, x_max=47.4)

# %% [markdown]
# ## Step 7: Show Project Summary

# %%
project.summary.show_report()
