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
model.space_group.name_h_m.value = "P n m a"
model.cell.length_a.value = 8.4693
model.cell.length_b.value = 5.3910
model.cell.length_c.value = 6.9506
model.atom_sites.add("Pb", "Pb", 0.1876, 0.25, 0.167, b_iso=1.37)
model.atom_sites.add("S", "S", 0.0654, 0.25, 0.684, b_iso=0.3777)
model.atom_sites.add("O1", "O", 0.9082, 0.25, 0.5954, b_iso=1.9764)
model.atom_sites.add("O2", "O", 0.1935, 0.25, 0.5432, b_iso=1.4456)
model.atom_sites.add("O3", "O", 0.0811, 0.0272, 0.8086, b_iso=1.2822)

# Create and configure experiments

# Experiment 1: Neutron powder diffraction (first half of the dataset)
expt1 = Experiment(name="npd1", radiation_probe="neutron", data_path="examples/data/pbso4_powder_neutron_cw_first-half.dat")
expt1.instrument.setup_wavelength = 1.91
expt1.instrument.calib_twotheta_offset = -0.1406
expt1.peak.broad_gauss_u = 0.139
expt1.peak.broad_gauss_v = -0.4124
expt1.peak.broad_gauss_w = 0.386
expt1.peak.broad_lorentz_x = 0
expt1.peak.broad_lorentz_y = 0.0878
expt1.linked_phases.add("pbso4", scale=1.46)
expt1.background_type = "line-segment"
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

# Experiment 2: Neutron powder diffraction (second half of the dataset)
expt2 = Experiment(name="npd2", radiation_probe="neutron", data_path="examples/data/pbso4_powder_neutron_cw_second-half.dat")
expt2.instrument.setup_wavelength = 1.91
expt2.instrument.calib_twotheta_offset = -0.1406
expt2.peak.broad_gauss_u = 0.139
expt2.peak.broad_gauss_v = -0.4124
expt2.peak.broad_gauss_w = 0.386
expt2.peak.broad_lorentz_x = 0
expt2.peak.broad_lorentz_y = 0.0878
expt2.linked_phases.add("pbso4", scale=1.46)
expt2.background_type = "line-segment"
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
    expt2.background.add(x, y)

# Create project and add sample model and experiments
project = Project()
project.sample_models.add(model)
project.experiments.add(expt1)
project.experiments.add(expt2)

# Set calculator, minimizer and refinement strategy
project.analysis.current_calculator = "cryspy"
project.analysis.current_minimizer = "lmfit (leastsq)"
project.analysis.fit_mode = 'joint'
# project.analysis.joint_fit.add("expt1", weight=0.4)  # Default weight could be 0.5
# project.analysis.joint_fit.add("expt2", weight=0.6)  # Default weight could be 0.5
print(project.analysis.joint_fit_experiments["npd1"])
project.analysis.joint_fit_experiments["npd1"] = 0.5  # Default weight could be 0.5
project.analysis.joint_fit_experiments["npd2"] = 0.5  # Default weight could be 0.5

# Define free parameters
model.cell.length_a.free = True
model.cell.length_b.free = True
model.cell.length_c.free = True
#expt1.linked_phases["pbso4"].scale.free = True
#expt2.linked_phases["pbso4"].scale.free = True

# Run refinement
project.analysis.fit()

# Assert results
assert_almost_equal(project.analysis.fit_results.reduced_chi_square, 4.66, decimal=1)

