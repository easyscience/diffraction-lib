"""
Joint Refinement Example (Advanced API)

This example demonstrates a more flexible and advanced usage of the EasyDiffraction
library by explicitly creating and configuring some objects. It is more suitable for
users comfortable with Python programming and those interested in custom workflows.
"""
from numpy.testing import assert_almost_equal

from easydiffraction import (
    Project,
    SampleModel,
    Experiment
)

# Create and configure sample model

model = SampleModel("pbso4")
model.space_group.name_h_m = "P n m a"
model.cell.length_a = 8.4693
model.cell.length_b = 5.3910
model.cell.length_c = 6.9506
model.atom_sites.add("Pb", "Pb", 0.1876, 0.25, 0.167, b_iso=1.37)
model.atom_sites.add("S", "S", 0.0654, 0.25, 0.684, b_iso=0.3777)
model.atom_sites.add("O1", "O", 0.9082, 0.25, 0.5954, b_iso=1.9764)
model.atom_sites.add("O2", "O", 0.1935, 0.25, 0.5432, b_iso=1.4456)
model.atom_sites.add("O3", "O", 0.0811, 0.0272, 0.8086, b_iso=1.2822)

# Create and configure experiments

# Experiment: Neutron powder diffraction (full dataset)
expt = Experiment(name="npd", radiation_probe="neutron", data_path="examples/data/pbso4_powder_neutron_cw_full.dat")
expt.instrument.setup_wavelength = 1.91
expt.instrument.calib_twotheta_offset = -0.1406
expt.peak.broad_gauss_u = 0.139
expt.peak.broad_gauss_v = -0.4124
expt.peak.broad_gauss_w = 0.386
expt.peak.broad_lorentz_x = 0
expt.peak.broad_lorentz_y = 0.0878
expt.linked_phases.add("pbso4", scale=1.46)
expt.background_type = "line-segment"
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
    expt.background.add(x, y)

# Create project and add sample model and experiments
project = Project()
project.sample_models.add(model)
project.experiments.add(expt)

# Set calculator, minimizer and refinement strategy
project.analysis.current_calculator = "cryspy"
project.analysis.current_minimizer = "lmfit (leastsq)"
project.analysis.fit_mode = 'joint'

# Set experiment weights
project.analysis.joint_fit_experiments['xrd'] = 0.5  # Default weight
project.analysis.joint_fit_experiments['npd'] = 0.5  # Default weight

# Define free parameters
model.cell.length_a.free = True
model.cell.length_b.free = True
model.cell.length_c.free = True

# Run refinement
project.analysis.fit()

# Assert results
assert_almost_equal(project.analysis.fit_results.reduced_chi_square, 4.66, decimal=1)
