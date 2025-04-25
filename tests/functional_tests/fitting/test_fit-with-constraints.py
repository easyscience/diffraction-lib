from numpy.testing import assert_almost_equal

from easydiffraction import (
    Project,
    SampleModel,
    Experiment
)


def test_single_fit_neutron_pd_cwl_lbco_with_constraints() -> None:
    # Create and configure sample model
    model = SampleModel('lbco')

    space_group = model.space_group
    space_group.name_h_m = 'P m -3 m'

    cell = model.cell
    cell.length_a = 3.8909

    atom_sites = model.atom_sites
    atom_sites.add('La', 'La', 0, 0, 0, b_iso=1.0, occupancy=0.5)
    atom_sites.add('Ba', 'Ba', 0, 0, 0, b_iso=1.0, occupancy=0.5)
    atom_sites.add('Co', 'Co', 0.5, 0.5, 0.5, b_iso=1.0)
    atom_sites.add('O', 'O', 0, 0.5, 0.5, b_iso=1.0)

    model.show_as_cif()

    # Create and configure experiment
    expt = Experiment('hrpt', data_path='examples/data/hrpt_lbco.xye')

    instrument = expt.instrument
    instrument.setup_wavelength = 1.494
    instrument.calib_twotheta_offset = 0.6225

    peak = expt.peak
    peak.broad_gauss_u = 0.0834
    peak.broad_gauss_v = -0.1168
    peak.broad_gauss_w = 0.123
    peak.broad_lorentz_x = 0
    peak.broad_lorentz_y = 0.0797

    background = expt.background
    background.add(x=10, y=174.3)
    background.add(x=20, y=159.8)
    background.add(x=30, y=167.9)
    background.add(x=50, y=166.1)
    background.add(x=70, y=172.3)
    background.add(x=90, y=171.1)
    background.add(x=110, y=172.4)
    background.add(x=130, y=182.5)
    background.add(x=150, y=173.0)
    background.add(x=165, y=171.1)

    expt.linked_phases.add('lbco', scale=9.0976)

    expt.show_as_cif()

    # Create project and add sample model and experiments
    project = Project()
    project.sample_models.add(model)
    project.experiments.add(expt)

    # Set calculator, minimizer and fit mode
    project.analysis.current_calculator = 'cryspy'  # Default
    project.analysis.current_minimizer = 'lmfit (leastsq)'  # Default
    project.analysis.fit_mode = 'single'  # Default

    # Compare measured and calculated patterns
    project.plot_meas_vs_calc('hrpt', 65, 68)

    # ------------ 1st fitting ------------

    # Define free parameters
    atom_sites['La'].occupancy.free = True
    atom_sites['Ba'].occupancy.free = True
    atom_sites['La'].b_iso.free = True
    atom_sites['Ba'].b_iso.free = True
    atom_sites['Co'].b_iso.free = True
    atom_sites['O'].b_iso.free = True

    project.analysis.show_free_params()

    # Compare parameter values
    assert_almost_equal(atom_sites['La'].b_iso.value, 1.0, decimal=2)
    assert_almost_equal(atom_sites['Ba'].b_iso.value, 1.0, decimal=2)
    assert_almost_equal(atom_sites['Co'].b_iso.value, 1.0, decimal=2)
    assert_almost_equal(atom_sites['O'].b_iso.value, 1.0, decimal=2)
    assert_almost_equal(atom_sites['La'].occupancy.value, 0.5, decimal=2)
    assert_almost_equal(atom_sites['Ba'].occupancy.value, 0.5, decimal=2)

    # Start fitting
    project.analysis.fit()

    # Compare fit quality
    assert_almost_equal(project.analysis.fit_results.reduced_chi_square, 1.24, decimal=1)

    # Compare parameter values
    assert_almost_equal(atom_sites['La'].b_iso.value, 15.0945, decimal=2)
    assert_almost_equal(atom_sites['Ba'].b_iso.value, 0.5226, decimal=2)
    assert_almost_equal(atom_sites['Co'].b_iso.value, 0.2398, decimal=2)
    assert_almost_equal(atom_sites['O'].b_iso.value, 1.4049, decimal=2)
    assert_almost_equal(atom_sites['La'].occupancy.value, 0.011, decimal=2)
    assert_almost_equal(atom_sites['Ba'].occupancy.value, 1.3206, decimal=2)

    # ------------ 2nd fitting ------------

    # User-defined constraints

    # Set aliases for parameters
    project.analysis.aliases.add(alias='biso_La',
                                 param=atom_sites['La'].b_iso)
    project.analysis.aliases.add(alias='biso_Ba',
                                 param=atom_sites['Ba'].b_iso)

    project.analysis.aliases.add('occ_La', atom_sites['La'].occupancy)
    project.analysis.aliases.add('occ_Ba', atom_sites['Ba'].occupancy)

    project.analysis.show_constraints()

    # Set constraints
    project.analysis.constraints.add(id='1',
                                     lhs_alias='biso_Ba',
                                     rhs_expr='biso_La')
    project.analysis.constraints.add('2', 'occ_Ba', '1 - occ_La')

    project.analysis.show_constraints()

    # Show free parameters before applying constraints
    project.analysis.show_free_params()

    # Apply constraints
    project.analysis.apply_constraints()

    # Show free parameters after applying constraints
    project.analysis.show_free_params()

    # Start fitting
    project.analysis.fit()

    # Show all parameters
    project.analysis.show_all_params()

    # Compare fit quality
    assert_almost_equal(project.analysis.fit_results.reduced_chi_square, 1.24, decimal=1)

    # Compare parameter values
    assert_almost_equal(atom_sites['La'].b_iso.value, 0.5443, decimal=2)
    assert_almost_equal(atom_sites['Ba'].b_iso.value, 0.5443, decimal=2)
    assert_almost_equal(atom_sites['Co'].b_iso.value, 0.2335, decimal=2)
    assert_almost_equal(atom_sites['O'].b_iso.value, 1.4056, decimal=2)
    assert_almost_equal(atom_sites['La'].occupancy.value, 0.5274, decimal=2)
    assert_almost_equal(atom_sites['Ba'].occupancy.value, 0.4726, decimal=2)

if __name__ == '__main__':
    test_single_fit_neutron_pd_cwl_lbco_with_constraints()