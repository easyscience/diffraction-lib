"""
Joint Refinement Example (Advanced API)

This example demonstrates a more flexible and advanced usage of the EasyDiffraction
library by explicitly creating and configuring some objects. It is more suitable for
users comfortable with Python programming and those interested in custom workflows.
"""
from numpy.testing import assert_almost_equal
from numpy import isclose

from easydiffraction import (
    Project,
    SampleModel,
    Experiment
)

# Create and configure sample model
model = SampleModel('pbso4')
model.space_group.name_h_m = 'P n m a'
model.cell.length_a = 8.47
model.cell.length_b = 5.39
model.cell.length_c = 6.95
model.atom_sites.add('Pb', 'Pb', 0.1876, 0.25, 0.167, b_iso=1.37)
model.atom_sites.add('S', 'S', 0.0654, 0.25, 0.684, b_iso=0.3777)
model.atom_sites.add('O1', 'O', 0.9082, 0.25, 0.5954, b_iso=1.9764)
model.atom_sites.add('O2', 'O', 0.1935, 0.25, 0.5432, b_iso=1.4456)
model.atom_sites.add('O3', 'O', 0.0811, 0.0272, 0.8086, b_iso=1.2822)

# Create and configure experiments

# Experiment 1: Neutron powder diffraction
expt1 = Experiment(name='npd', radiation_probe='neutron', data_path='examples/data/d1a_pbso4.dat')
expt1.instrument.setup_wavelength = 1.91
expt1.instrument.calib_twotheta_offset = -0.1406
expt1.peak.broad_gauss_u = 0.139
expt1.peak.broad_gauss_v = -0.412
expt1.peak.broad_gauss_w = 0.386
expt1.peak.broad_lorentz_x = 0
expt1.peak.broad_lorentz_y = 0.088
expt1.linked_phases.add('pbso4', scale=1.5)
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

# Experiment 2: X-ray powder diffraction
expt2 = Experiment(name='xrd', radiation_probe='xray', data_path='examples/data/lab_pbso4.dat')
expt2.instrument.setup_wavelength = 1.540567
expt2.instrument.calib_twotheta_offset = -0.05181
expt2.peak.broad_gauss_u = 0.304138
expt2.peak.broad_gauss_v = -0.112622
expt2.peak.broad_gauss_w = 0.021272
expt2.peak.broad_lorentz_x = 0
expt2.peak.broad_lorentz_y = 0.057691
expt2.linked_phases.add('pbso4', scale=0.001)
for x, y in [
    (11.0, 141.8516),
    (13.0, 102.8838),
    (16.0, 78.0551),
    (20.0, 124.0121),
    (30.0, 123.7123),
    (50.0, 120.8266),
    (90.0, 113.7473),
    (110.0, 132.4643),
]:
    expt2.background.add(x, y)

# Create project and add sample model and experiments
project = Project()
project.sample_models.add(model)
project.experiments.add(expt1)
project.experiments.add(expt2)

# Set calculator, minimizer and fit mode
project.analysis.current_calculator = 'cryspy'
project.analysis.current_minimizer = 'lmfit (leastsq)'

# Define free parameters
model.cell.length_a.free = True
model.cell.length_b.free = True
model.cell.length_c.free = True
expt1.linked_phases['pbso4'].scale.free = True
expt2.linked_phases['pbso4'].scale.free = True

# ------------ 1st fitting ------------

project.analysis.fit_mode = 'single'  # Default
project.analysis.fit()
assert_almost_equal(project.analysis.fit_results.reduced_chi_square, 26.05, decimal=1)

# ------------ 2nd fitting ------------

project.analysis.fit_mode = 'joint'
project.analysis.fit()
assert_almost_equal(project.analysis.fit_results.reduced_chi_square, 21.09, decimal=1)

# ------------ 3rd fitting ------------

project.analysis.joint_fit_experiments['xrd'].weight = 0.5  # Default
project.analysis.joint_fit_experiments['npd'].weight = 0.5  # Default
project.analysis.fit_mode = 'joint'
project.analysis.fit()
assert_almost_equal(project.analysis.fit_results.reduced_chi_square, 21.09, decimal=1)

# ------------ 4th fitting ------------

project.analysis.joint_fit_experiments['xrd'].weight = 0.3
project.analysis.joint_fit_experiments['npd'].weight = 0.7
project.analysis.fit_mode = 'joint'
project.analysis.fit()
assert_almost_equal(project.analysis.fit_results.reduced_chi_square, 14.39, decimal=1)

