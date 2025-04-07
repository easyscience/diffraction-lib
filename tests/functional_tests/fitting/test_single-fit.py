from numpy.testing import assert_almost_equal

from easydiffraction import (
    Project,
    SampleModel,
    Experiment
)


def test_single_fit_neutron_pd_cwl_lbco() -> None:
    # Create and configure sample model
    model = SampleModel("lbco")
    model.space_group.name = "P m -3 m"
    model.cell.length_a = 3.88
    model.cell.length_b = 3.88
    model.cell.length_c = 3.88
    model.atom_sites.add("La", "La", 0, 0, 0, occupancy=0.5, b_iso=0.1)
    model.atom_sites.add("Ba", "Ba", 0, 0, 0, occupancy=0.5, b_iso=0.1)
    model.atom_sites.add("Co", "Co", 0.5, 0.5, 0.5, b_iso=0.1)
    model.atom_sites.add("O", "O", 0, 0.5, 0.5, b_iso=0.1)
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
    #expt.background.add(x=10, y=168.345)
    #expt.background.add(x=165, y=175.688)
    expt.show_as_cif()

    # Create project and add sample model and experiments
    project = Project()
    project.sample_models.add(model)
    project.experiments.add(expt)

    # Set calculator, minimizer and refinement strategy
    project.analysis.current_calculator = "cryspy"
    #project.analysis.current_calculator = "crysfml"
    project.analysis.current_minimizer = "lmfit (leastsq)"

    # Compare measured and calculated patterns
    project.analysis.show_meas_vs_calc_chart('hrpt', 65, 68)

    # ------------ 1st fitting ------------

    # Define free parameters
    model.cell.length_a.free = True
    expt.linked_phases["lbco"].scale.free = True
    expt.instrument.calib_twotheta_offset.free = True
    expt.background["10"].y.free = True
    expt.background["165"].y.free = True
    project.analysis.show_free_params()

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


def test_single_fit_neutron_pd_tof_si() -> None:
    # Create and configure sample model
    model = SampleModel("si")
    model.space_group.name = "F d -3 m"
    model.space_group.setting = 2
    model.cell.length_a = 5.431
    model.cell.length_b = 5.431
    model.cell.length_c = 5.431
    model.atom_sites.add("Si", "Si", 0.125, 0.125, 0.125, b_iso=0.5)
    model.show_as_cif()

    # Create and configure experiment
    expt = Experiment("sepd", beam_mode="time-of-flight", data_path="examples/data/sepd_si.xye")
    expt.instrument.setup_twotheta_bank = 144.845
    expt.instrument.calib_d_to_tof_offset = 0.0
    expt.instrument.calib_d_to_tof_linear = 7476.91
    expt.instrument.calib_d_to_tof_quad = -1.54
    expt.peak_profile_type = "pseudo-voigt * ikeda-carpenter"
    expt.peak.broad_gauss_sigma_0 = 3.0
    expt.peak.broad_gauss_sigma_1 = 40.0
    expt.peak.broad_gauss_sigma_2 = 2.0
    expt.peak.broad_mix_beta_0 = 0.04221
    expt.peak.broad_mix_beta_1 = 0.00946
    expt.peak.asym_alpha_0 = 0.0
    expt.peak.asym_alpha_1 = 0.5971
    expt.linked_phases.add("si", scale=10.0)
    for x in range(0, 35000, 5000):
        expt.background.add(x=x, y=200)
    expt.show_as_cif()

    # Create project and add sample model and experiments
    project = Project()
    project.sample_models.add(model)
    project.experiments.add(expt)

    # Set calculator, minimizer and refinement strategy
    project.analysis.current_calculator = "cryspy"
    project.analysis.current_minimizer = "lmfit (leastsq)"

    # Compare measured and calculated patterns
    project.analysis.show_meas_vs_calc_chart('sepd', 23200, 23700)

    # ------------ 1st fitting ------------

    # Define free parameters
    model.cell.length_a.free = True
    expt.linked_phases["si"].scale.free = True
    expt.instrument.calib_d_to_tof_offset.free = True
    project.analysis.show_free_params()

    # Start fitting
    project.analysis.fit()
    project.analysis.show_meas_vs_calc_chart('sepd', 23200, 23700)

    # Compare fit quality
    assert_almost_equal(project.analysis.fit_results.reduced_chi_square, 66.72, decimal=1)

    # ------------ 2nd fitting ------------

    # Define more free parameters
    for point in expt.background:
        point.y.free = True
    project.analysis.show_free_params()

    # Start fitting
    project.analysis.fit()
    project.analysis.show_meas_vs_calc_chart('sepd', 23200, 23700, show_residual=True)

    # Compare fit quality
    assert_almost_equal(project.analysis.fit_results.reduced_chi_square, 3.38, decimal=1)

    # ------------ 3rd fitting ------------

    # Fix background points
    for point in expt.background:
        point.y.free = False

    # Define more free parameters
    expt.peak.broad_gauss_sigma_0.free = True
    expt.peak.broad_gauss_sigma_1.free = True
    expt.peak.broad_gauss_sigma_2.free = True
    project.analysis.show_free_params()

    # Start fitting
    project.analysis.fit()
    project.analysis.show_meas_vs_calc_chart('sepd', 23200, 23700, show_residual=True)

    # Compare fit quality
    assert_almost_equal(project.analysis.fit_results.reduced_chi_square, 3.21, decimal=1)

    # ------------ 4th fitting ------------

    # Define more free parameters
    model.atom_sites["Si"].b_iso.free = True
    project.analysis.show_free_params()

    # Start fitting
    project.analysis.fit()
    project.analysis.show_meas_vs_calc_chart('sepd', 23200, 23700, show_residual=True)

    # Compare fit quality
    assert_almost_equal(project.analysis.fit_results.reduced_chi_square, 3.19, decimal=1)


def test_single_fit_neutron_pd_tof_ncaf() -> None:
    # Create and configure sample model
    model = SampleModel("ncaf")
    model.space_group.name = "I 21 3"
    model.space_group.setting = 1
    model.cell.length_a = 10.250256
    model.cell.length_b = 10.250256
    model.cell.length_c = 10.250256
    model.atom_sites.add("Ca", "Ca", 0.4661, 0.0, 0.25, b_iso=0.9)
    model.atom_sites.add("Al", "Al", 0.25171, 0.25171, 0.25171, b_iso=0.66)
    model.atom_sites.add("Na", "Na", 0.08481, 0.08481, 0.08481, b_iso=1.9)
    model.atom_sites.add("F1", "F", 0.1375, 0.3053, 0.1195, b_iso=0.9)
    model.atom_sites.add("F2", "F", 0.3626, 0.3634, 0.1867, b_iso=1.28)
    model.atom_sites.add("F3", "F", 0.4612, 0.4612, 0.4612, b_iso=0.79)
    model.show_as_cif()

    # Create and configure experiment
    expt = Experiment("wish", beam_mode="time-of-flight", data_path="examples/data/wish_ncaf.xye")
    expt.instrument.setup_twotheta_bank = 152.827
    expt.instrument.calib_d_to_tof_offset = 0.0
    expt.instrument.calib_d_to_tof_linear = 20770
    expt.instrument.calib_d_to_tof_quad = -1.08308
    expt.peak_profile_type = "pseudo-voigt * ikeda-carpenter"
    expt.peak.broad_gauss_sigma_0 = 0.0
    expt.peak.broad_gauss_sigma_1 = 0.0
    expt.peak.broad_gauss_sigma_2 = 5.0
    expt.peak.broad_mix_beta_0 = 0.01
    expt.peak.broad_mix_beta_1 = 0.01
    expt.peak.asym_alpha_0 = 0.0
    expt.peak.asym_alpha_1 = 0.1
    expt.linked_phases.add("ncaf", scale=0.5)
    for x, y in [
        (9162, 465),
        (11136, 593),
        (13313, 497),
        (14906, 546),
        (16454, 533),
        (17352, 496),
        (18743, 428),
        (20179, 452),
        (21368, 397),
        (22176, 468),
        (22827, 477),
        (24644, 380),
        (26439, 381),
        (28257, 378),
        (31196, 343),
        (34034, 328),
        (37265, 310),
        (41214, 323),
        (44827, 283),
        (49830, 273),
        (52905, 257),
        (58204, 260),
        (62916, 261),
        (70186, 262),
        (74204, 262),
        (82103, 268),
        (91958, 268),
        (102712, 262)
    ]:
        expt.background.add(x, y)
    expt.show_as_cif()

    # Create project and add sample model and experiments
    project = Project()
    project.sample_models.add(model)
    project.experiments.add(expt)

    # Set calculator, minimizer and refinement strategy
    project.analysis.current_calculator = "cryspy"
    project.analysis.current_minimizer = "lmfit (leastsq)"

    # Compare measured and calculated patterns
    project.analysis.show_meas_vs_calc_chart('wish', 37000, 40000)

    # ------------ 1st fitting ------------

    # Define free parameters
    #model.cell.length_a.free = True
    expt.linked_phases["ncaf"].scale.free = True
    expt.instrument.calib_d_to_tof_offset.free = True
    project.analysis.show_free_params()

    # Start fitting
    project.analysis.fit()
    project.analysis.show_meas_vs_calc_chart('wish', 37000, 40000)

    # Compare fit quality
    assert_almost_equal(project.analysis.fit_results.reduced_chi_square, 78.40, decimal=1)

    # ------------ 2nd fitting ------------

    # Define more free parameters
    expt.peak.broad_gauss_sigma_2.free = True
    expt.peak.broad_mix_beta_0.free = True
    expt.peak.broad_mix_beta_1.free = True
    expt.peak.asym_alpha_1.free = True
    project.analysis.show_free_params()

    # Start fitting
    project.analysis.fit()
    project.analysis.show_meas_vs_calc_chart('wish', 37000, 40000, show_residual=True)

    # Compare fit quality
    assert_almost_equal(project.analysis.fit_results.reduced_chi_square, 15.59, decimal=1)


if __name__ == '__main__':
    #test_single_fit_neutron_pd_cwl_lbco()
    #test_single_fit_neutron_pd_tof_si()
    test_single_fit_neutron_pd_tof_ncaf()