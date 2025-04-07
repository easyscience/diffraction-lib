from numpy.testing import assert_almost_equal

from easydiffraction import (
    Project,
    SampleModel,
    Experiment
)


def test_fit_neutron_pd_cwl_hs() -> None:
    # Create and configure sample model
    model = SampleModel("hs")
    model.space_group.name = "R -3 m"
    model.space_group.setting = "h"
    model.cell.length_a = 6.9
    model.cell.length_c = 14.1
    model.atom_sites.add("Zn", "Zn", 0, 0, 0.5, wyckoff_letter="b", b_iso=0.5)
    model.atom_sites.add("Cu", "Cu", 0.5, 0, 0, wyckoff_letter="e", b_iso=0.5)
    model.atom_sites.add("O", "O", 0.21, -0.21, 0.06, wyckoff_letter="h", b_iso=0.5)
    model.atom_sites.add("Cl", "Cl", 0, 0, 0.197, wyckoff_letter="c", b_iso=0.5)
    model.atom_sites.add("H", "2H", 0.13, -0.13, 0.08, wyckoff_letter="h", b_iso=0.5)
    model.show_as_cif()
    model.apply_symmetry_constraints()
    model.show_as_cif()

    # Create and configure experiment
    expt = Experiment("hrpt", data_path="examples/data/hrpt_hs.xye")
    expt.instrument.setup_wavelength = 1.89
    expt.instrument.calib_twotheta_offset = 0.0
    expt.peak.broad_gauss_u = 0.1
    expt.peak.broad_gauss_v = -0.2
    expt.peak.broad_gauss_w = 0.2
    expt.peak.broad_lorentz_x = 0.0
    expt.peak.broad_lorentz_y = 0
    expt.linked_phases.add("hs", scale=0.5)
    expt.background.add(x=4.4196, y=500)
    expt.background.add(x=6.6207, y=500)
    expt.background.add(x=10.4918, y=500)
    expt.background.add(x=15.4634, y=500)
    expt.background.add(x=45.6041, y=500)
    expt.background.add(x=74.6844, y=500)
    expt.background.add(x=103.4187, y=500)
    expt.background.add(x=121.6311, y=500)
    expt.background.add(x=159.4116, y=500)
    expt.show_as_cif()

    # Create project and add sample model and experiments
    project = Project()
    project.sample_models.add(model)
    project.experiments.add(expt)

    # Set calculator, minimizer and refinement strategy
    project.analysis.current_calculator = "cryspy"
    project.analysis.current_minimizer = "lmfit (leastsq)"

    # Compare measured and calculated patterns
    project.analysis.show_meas_vs_calc_chart('hrpt', 48, 51)

    # ------------ 1st fitting ------------

    # Define free parameters
    model.cell.length_a.free = True
    model.cell.length_c.free = True
    expt.linked_phases["hs"].scale.free = True
    expt.instrument.calib_twotheta_offset.free = True
    project.analysis.show_free_params()

    # Start fitting
    project.analysis.fit()
    project.analysis.show_meas_vs_calc_chart('hrpt', 48, 51)

    # Compare fit quality
    assert_almost_equal(project.analysis.fit_results.reduced_chi_square, 51.57, decimal=1)

    # ------------ 2nd fitting ------------

    # Define free parameters
    expt.peak.broad_gauss_u.free = True
    expt.peak.broad_gauss_v.free = True
    expt.peak.broad_gauss_w.free = True
    expt.peak.broad_lorentz_x.free = True
    for point in expt.background:
        point.y.free = True
    project.analysis.show_free_params()

    # Start fitting
    project.analysis.fit()
    project.analysis.show_meas_vs_calc_chart('hrpt', 48, 51)

    # Compare fit quality
    assert_almost_equal(project.analysis.fit_results.reduced_chi_square, 12.41, decimal=1)

    # ------------ 3rd fitting ------------

    # Define free parameters
    model.atom_sites['O'].fract_x.free = True
    model.atom_sites['O'].fract_z.free = True
    model.atom_sites['Cl'].fract_z.free = True
    model.atom_sites['H'].fract_x.free = True
    model.atom_sites['H'].fract_z.free = True
    project.analysis.show_free_params()

    # Start fitting
    project.analysis.fit()
    project.analysis.show_meas_vs_calc_chart('hrpt', 48, 51)

    # Compare fit quality
    assert_almost_equal(project.analysis.fit_results.reduced_chi_square, 4.34, decimal=1)

    # ------------ 3rd fitting ------------

    # Define free parameters
    model.atom_sites['Zn'].b_iso.free = True
    model.atom_sites['Cu'].b_iso.free = True
    model.atom_sites['O'].b_iso.free = True
    model.atom_sites['Cl'].b_iso.free = True
    model.atom_sites['H'].b_iso.free = True
    project.analysis.show_free_params()

    # Start fitting
    project.analysis.fit()
    project.analysis.show_meas_vs_calc_chart('hrpt', 48, 51, show_residual=True)

    # Show parameters
    project.analysis.show_refinable_params()
    project.analysis.show_free_params()

    # Compare fit quality
    assert_almost_equal(project.analysis.fit_results.reduced_chi_square, 2.11, decimal=1)


if __name__ == '__main__':
    test_fit_neutron_pd_cwl_hs()