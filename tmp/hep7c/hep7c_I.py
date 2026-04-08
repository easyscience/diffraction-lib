# %% [markdown]
# # Structure Refinement: LaM7O3, Synchrotron
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
    name='hep7c_I',
    description='LaM7O3 structure refinement using synchrotron data.',
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
structure.cell.length_a = 5.488218
structure.cell.length_b = 7.787738
structure.cell.length_c = 5.524247

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
    b_iso=1.30369,
)
structure.atom_sites.create(
    label='Ti',
    type_symbol='Ti',
    fract_x=0,
    fract_y=0,
    fract_z=0,
    wyckoff_letter='a',
    b_iso=1.10930,
    occupancy=0.14286,
)
structure.atom_sites.create(
    label='Cr',
    type_symbol='Cr',
    fract_x=0,
    fract_y=0,
    fract_z=0,
    wyckoff_letter='a',
    b_iso=1.10930,
    occupancy=0.14286,
)
structure.atom_sites.create(
    label='Mn',
    type_symbol='Mn',
    fract_x=0,
    fract_y=0,
    fract_z=0,
    wyckoff_letter='a',
    b_iso=1.10930,
    occupancy=0.14286,
)
structure.atom_sites.create(
    label='Fe',
    type_symbol='Fe',
    fract_x=0,
    fract_y=0,
    fract_z=0,
    wyckoff_letter='a',
    b_iso=1.10930,
    occupancy=0.14286,
)
structure.atom_sites.create(
    label='Co',
    type_symbol='Co',
    fract_x=0,
    fract_y=0,
    fract_z=0,
    wyckoff_letter='a',
    b_iso=1.10930,
    occupancy=0.14286,
)
structure.atom_sites.create(
    label='Ni',
    type_symbol='Ni',
    fract_x=0,
    fract_y=0,
    fract_z=0,
    wyckoff_letter='a',
    b_iso=1.10930,
    occupancy=0.14286,
)
structure.atom_sites.create(
    label='Cu',
    type_symbol='Cu',
    fract_x=0,
    fract_y=0,
    fract_z=0,
    wyckoff_letter='a',
    b_iso=1.10930,
    occupancy=0.14286,
)
structure.atom_sites.create(
    label='O1',
    type_symbol='O',
    fract_x=0.50628,
    fract_y=0.25,
    fract_z=0.54423,
    wyckoff_letter='c',
    b_iso=0.25033,
)
structure.atom_sites.create(
    label='O2',
    type_symbol='O',
    fract_x=0.21881,
    fract_y=0.05203,
    fract_z=0.25686,
    wyckoff_letter='d',
    b_iso=0.25033,
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
# data_path = ed.download_data(id=3, destination='data')
data_path = 'data/hep7c_4.dat'

# %% [markdown]
# Add an experiment to the project, using the measured data from the
# specified path. The radiation probe is set to 'xray' for this example.

# %%
project.experiments.add_from_data_path(
    name='pd_xray_1',
    data_path=data_path,
    radiation_probe='xray',
    sample_form='powder',
)

# %% [markdown]
# Create an alias for the structure, to access its parameters in a more
# convenient way.

# %%
experiment = project.experiments['pd_xray_1']

# %% [markdown]
# Show all the public attributes and methods of the experiment object,
# which can be used to define the experiment and set parameters.

# %%
experiment.help()

# %% [markdown]
# Link the structure to the experiment and set its scale factor.

# %%
experiment.linked_phases.create(id='lam7o3', scale=0.39828e-05)

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
experiment.instrument.setup_wavelength = 0.207109
experiment.instrument.calib_twotheta_offset = 0.00164

# %% [markdown]
# Set peak shape parameters. In this example, a pseudo-Voigt profile is
# used, with Gaussian and Lorentzian contributions to the peak
# broadening.

# %%
experiment.peak.broad_gauss_u = 0.197204
experiment.peak.broad_gauss_v = -0.034604
experiment.peak.broad_gauss_w = 0.002123
experiment.peak.broad_lorentz_x = 0.285201

# %% [markdown]
# Define background points. In this example, multiple points are defined
# across the 2-theta range of the experiment, with their x and y values
# taken from the measured data.
# Some points are commented out and thus not used.

# %%
for x, y in [
    (2.0737, 608.8809),
    (2.2421, 678.6176),
    (2.3865, 752.2546),
    (2.5601, 861.4917),
    (2.6865, 934.2341),
    (2.8128, 995.3818),
    (2.9098, 997.7123),
    (2.9910, 943.8851),
    (3.1353, 885.0516),
    # (3.2323, 848.1264),
    (3.3654, 760.3870),
    (3.4827, 706.2471),
    # (3.5729, 690.3240),
    (3.7188, 640.4757),
    # (3.8496, 610.7817),
    # (3.9917, 571.7743),
    (4.0910, 598.2051),
    # (4.1925, 467.5903),
    (4.5444, 498.1868),
    # (4.6797, 499.2691),
    # (4.7789, 485.5768),
    (4.9654, 469.5414),
    # (5.1752, 437.5768),
    (5.4616, 455.5295),
    # (5.6263, 451.5172),
    # (5.8135, 452.1605),
    # (5.9353, 460.1805),
    # (6.0210, 370.4761),
    # (6.2489, 424.1192),
    # (6.3872, 438.6293),
    # (6.4368, 453.2097),
    (6.5609, 446.7849),
    # (6.7459, 446.0796),
    # (6.9511, 445.5063),
    # (7.1316, 450.2400),
    (7.2887, 427.1046),
    # (7.7353, 476.8405),
    # (7.8707, 472.0285),
    # (8.0895, 475.8980),
    # (8.3850, 474.2686),
    (8.5181, 476.3667),
    # (8.8970, 481.0705),
    (9.0030, 464.8356),
    (9.4015, 479.2689),
    (9.9090, 486.0254),
    # (10.0038, 461.4817),
    # (10.3804, 441.1648),
    (10.5113, 424.9026),
    (10.9030, 383.8461),
    (11.3384, 382.8329),
    (11.7083, 398.6385),
    (11.8842, 385.8449),
    # (12.1496, 387.6461),
    (12.5195, 380.2116),
    (12.8714, 372.2346),
    # (13.2256, 369.5088),
    (13.6226, 352.0260),
    (13.9293, 351.0161),
    # (14.2564, 340.2247),
    (14.5992, 342.4929),
    (14.9647, 296.1931),
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
experiment.excluded_regions.create(id='1', start=0, end=2)
experiment.excluded_regions.create(id='2', start=14.97, end=180)

# %% [markdown]
# Show the experiment in CIF format.

# %%
experiment.show_as_cif()

# %% [markdown]
# ## Step 5: Set free parameters
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

structure.atom_sites['La'].b_iso.free = True
structure.atom_sites['Ti'].b_iso.free = True
structure.atom_sites['O1'].b_iso.free = True

# %% [markdown]
# Now, set free parameters for the experiment. In this example, the
# scale factor, instrumental calibration parameter, peak shape
# parameters, and background points are set free.

# %%
experiment.linked_phases['lam7o3'].scale.free = True

experiment.instrument.calib_twotheta_offset.free = True

experiment.peak.broad_lorentz_x.free = True

for point in experiment.background:
    point.y.free = True


# %% [markdown]
# Show all free parameters in the experiment.

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

# %% [markdown]
# Before performing the fit, we can plot the measured data and compare
# it with the calculated pattern using the initial parameters. This can
# be helpful to check if the initial parameters are reasonable and to
# identify any issues with the data or the model before running the fit.

# %%
project.plotter.plot_meas_vs_calc(expt_name='pd_xray_1')

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
project.plotter.plot_meas_vs_calc(expt_name='pd_xray_1', x_min=6.00, x_max=6.25)

# %%
experiment.instrument.help()

# %%
