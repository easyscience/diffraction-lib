# %% [markdown]
# # Joint Fit (Advanced Usage)
#
# This example demonstrates a more flexible and advanced usage of the
# EasyDiffraction library by explicitly creating and configuring some objects.
# It is more suitable for users comfortable with Python programming and those
# interested in custom workflows.

# %% [markdown]
# ## Import EasyDiffraction

# %%
from easydiffraction import (
    Project,
    SampleModel,
    Experiment,
    download_from_repository
)

# %% [markdown]
# ## Define Sample Model
#
# This section covers how to add sample models and modify their parameters.
#
# ### Create sample model object

# %%
model = SampleModel('pbso4')

# %% [markdown]
# ### Define space group

# %%
model.space_group.name_h_m = 'P n m a'

# %% [markdown]
# ### Define unit cell

# %%
model.cell.length_a = 8.47
model.cell.length_b = 5.39
model.cell.length_c = 6.95

# %% [markdown]
# ### Define atom sites

# %%
model.atom_sites.add('Pb', 'Pb', 0.1876, 0.25, 0.167, b_iso=1.37)
model.atom_sites.add('S', 'S', 0.0654, 0.25, 0.684, b_iso=0.3777)
model.atom_sites.add('O1', 'O', 0.9082, 0.25, 0.5954, b_iso=1.9764)
model.atom_sites.add('O2', 'O', 0.1935, 0.25, 0.5432, b_iso=1.4456)
model.atom_sites.add('O3', 'O', 0.0811, 0.0272, 0.8086, b_iso=1.2822)


# %% [markdown]
# ## Define Experiments
#
# This section teaches how to add experiments, configure their parameters, and
# link to them the sample models defined in the previous step.
#
# ### Experiment 1: npd
#
# #### Download measured data

# %%
download_from_repository('d1a_pbso4.dat',
                         branch='docs',
                         destination='data')

# %% [markdown]
# #### Create experiment object

# %%
expt1 = Experiment('npd',
                   radiation_probe='neutron',
                   data_path='data/d1a_pbso4.dat')

# %% [markdown]
# #### Define instrument

# %%
expt1.instrument.setup_wavelength = 1.91
expt1.instrument.calib_twotheta_offset = -0.1406

# %% [markdown]
# #### Define peak profile

# %%
expt1.peak.broad_gauss_u = 0.139
expt1.peak.broad_gauss_v = -0.412
expt1.peak.broad_gauss_w = 0.386
expt1.peak.broad_lorentz_x = 0
expt1.peak.broad_lorentz_y = 0.088

# %% [markdown]
# #### Define background

# %% [markdown]
# Select desired background type

# %%
expt1.background_type = 'line-segment'

# %% [markdown]
# Add background points

# %%
for x, y in [
    (11.0, 206.1624),
    (15.0, 194.75),
    (20.0, 194.505),
    (30.0, 188.4375),
    (50.0, 207.7633),
    (70.0, 201.7002),
    (120.0, 244.4525),
    (153.0, 226.0595),
]:
    expt1.background.add(x, y)

# %% [markdown]
# #### Define linked phases

# %%
expt1.linked_phases.add('pbso4', scale=1.5)

# %% [markdown]
# ### Experiment 2: xrd
#
# #### Download measured data

# %%
download_from_repository('lab_pbso4.dat',
                         branch='docs',
                         destination='data')

# %% [markdown]
# #### Create experiment object

# %%
expt2 = Experiment('xrd',
                   radiation_probe='xray',
                   data_path='data/lab_pbso4.dat')

# %% [markdown]
# #### Define instrument

# %%
expt2.instrument.setup_wavelength = 1.540567
expt2.instrument.calib_twotheta_offset = -0.05181

# %% [markdown]
# #### Define peak profile

# %%
expt2.peak.broad_gauss_u = 0.304138
expt2.peak.broad_gauss_v = -0.112622
expt2.peak.broad_gauss_w = 0.021272
expt2.peak.broad_lorentz_x = 0
expt2.peak.broad_lorentz_y = 0.057691

# %% [markdown]
# #### Define background

# %% [markdown]
# Select desired background type

# %%
expt2.background_type = 'chebyshev polynomial'

# %% [markdown]
# Add background points

# %%
for x, y in [
    (0, 119.195),
    (1, 6.221),
    (2, -45.725),
    (3, 8.119),
    (4, 54.552),
    (5, -20.661),
]:
    expt2.background.add(x, y)

# %% [markdown]
# #### Define linked phases

# %%
expt2.linked_phases.add('pbso4', scale=0.001)

# %% [markdown]
# ## Define Project
#
# The project object is used to manage the sample model, experiments, and
# analysis
#
# ### Create project object

# %%
project = Project()

# %% [markdown]
# ### Add sample model

# %%
project.sample_models.add(model)

# %% [markdown]
# ### Add experiments

# %%
project.experiments.add(expt1)
project.experiments.add(expt2)

# %% [markdown]
# ## Analysis
#
# This section will guide you through the analysis process, including setting
# up calculators and fitting models.
#
# ### Set calculation engine

# %%
project.analysis.current_calculator = 'cryspy'

# %% [markdown]
# ### Set fit mode

# %%
project.analysis.fit_mode = 'joint'

# %% [markdown]
# ### Set fitting engine

# %%
project.analysis.current_minimizer = 'lmfit (leastsq)'

# %% [markdown]
# ### Set fitting parameters
#
# Set sample model parameters to be fitted

# %%
model.cell.length_a.free = True
model.cell.length_b.free = True
model.cell.length_c.free = True

# %% [markdown]
# Set experimental parameters to be fitted

# %%
expt1.linked_phases['pbso4'].scale.free = True

expt1.instrument.calib_twotheta_offset.free = True

expt1.peak.broad_gauss_u.free = True
expt1.peak.broad_gauss_v.free = True
expt1.peak.broad_gauss_w.free = True
expt1.peak.broad_lorentz_y.free = True

# %%
expt2.linked_phases['pbso4'].scale.free = True

expt2.instrument.calib_twotheta_offset.free = True

expt2.peak.broad_gauss_u.free = True
expt2.peak.broad_gauss_v.free = True
expt2.peak.broad_gauss_w.free = True
expt2.peak.broad_lorentz_y.free = True

for term in expt2.background:
    term.coef.free = True

# %% [markdown]
# ### Fitting step

# %%
project.analysis.fit()

# %% [markdown]
# ### Show fitting results

# %%
project.plot_meas_vs_calc(expt_name='npd',
                          x_min=35.5, x_max=38.3,
                          show_residual=True)

# %%
project.plot_meas_vs_calc(expt_name='xrd',
                          x_min=29.0, x_max=30.4,
                          show_residual=True)
