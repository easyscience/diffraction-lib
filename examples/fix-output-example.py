from numpy.testing import assert_almost_equal

from easydiffraction import (
    Project,
    SampleModel,
    Experiment
)

# Create and configure sample model
model = SampleModel("lbco")
model.space_group.name_h_m = "P m -3 m"
model.space_group.it_coordinate_system_code = "1"
model.cell.length_a = 3.88
model.atom_sites.add("La", "La", 0, 0, 0, wyckoff_letter='a', occupancy=0.5, b_iso=0.1)
model.atom_sites.add("Ba", "Ba", 0, 0, 0, wyckoff_letter='a', occupancy=0.5, b_iso=0.1)
model.atom_sites.add("Co", "Co", 0.5, 0.5, 0.5, wyckoff_letter='b', b_iso=0.1)
model.atom_sites.add("O", "O", 0, 0.5, 0.5, wyckoff_letter='c', b_iso=0.1)
model.apply_symmetry_constraints()
model.show_as_cif()

# Create and configure experiment
expt = Experiment("hrpt", data_path="examples/data/hrpt_lbco.xye")
expt.instrument.setup_wavelength = 1.494
expt.instrument.calib_twotheta_offset = 0
expt.peak.broad_gauss_u = 0.1
expt.peak.broad_gauss_v = -0.1
expt.peak.broad_gauss_w = 0.2
expt.peak.broad_lorentz_x = 0
expt.peak.broad_lorentz_y = 0
expt.linked_phases.add("lbco", scale=5.0)
expt.background.add(x=10, y=170)
expt.background.add(x=165, y=170)
expt.show_as_cif()

# Create project and add sample model and experiments
project = Project()
project.sample_models.add(model)
project.experiments.add(expt)




#project.analysis.show_all_params()
#project.analysis.show_fittable_params()
#model.cell.length_a.free = True
#expt.linked_phases["lbco"].scale.free = True
#expt.instrument.calib_twotheta_offset.free = True
#expt.background["10"].y.free = True
#expt.background["165"].y.free = True
#project.analysis.show_free_params()
#exit()




# Set calculator, minimizer and fit mode
project.analysis.current_calculator = "cryspy"
project.analysis.current_minimizer = "lmfit (leastsq)"

# Compare measured and calculated patterns
project.analysis.show_meas_vs_calc_chart('hrpt', 65, 68)

# ------------ 1st fitting ------------

# Show parameters
#project.analysis.show_all_params()
#exit()
project.analysis.show_fittable_params()
#exit()

# Define free parameters
model.cell.length_a.free = True
expt.linked_phases["lbco"].scale.free = True
expt.instrument.calib_twotheta_offset.free = True
expt.background["10"].y.free = True
expt.background["165"].y.free = True
project.analysis.show_free_params()
#exit()

# Start fitting
project.analysis.fit()
project.analysis.show_meas_vs_calc_chart('hrpt', 65, 68)


# Compare fit quality
assert_almost_equal(project.analysis.fit_results.reduced_chi_square, 5.79, decimal=1)

# ------------ 2nd fitting ------------

# Define free parameters
expt.peak.broad_gauss_u.free = True
expt.peak.broad_gauss_v.free = True
expt.peak.broad_gauss_w.free = True
expt.peak.broad_lorentz_y.free = True
project.analysis.show_free_params()

# Start fitting
project.analysis.fit()
project.analysis.show_meas_vs_calc_chart('hrpt', 65, 68)

# Compare fit quality
assert_almost_equal(project.analysis.fit_results.reduced_chi_square, 4.41, decimal=1)

# ------------ 3rd fitting ------------

# Define free parameters
model.atom_sites['La'].b_iso.free = True
model.atom_sites['Ba'].b_iso.free = True
model.atom_sites['Co'].b_iso.free = True
model.atom_sites['O'].b_iso.free = True
project.analysis.show_free_params()

# Start fitting
project.analysis.fit()
project.analysis.show_meas_vs_calc_chart('hrpt', 65, 68, show_residual=True)
project.analysis.show_meas_vs_calc_chart('hrpt', 38, 41, show_residual=True)

# Compare fit quality
assert_almost_equal(project.analysis.fit_results.reduced_chi_square, 1.3, decimal=1)
