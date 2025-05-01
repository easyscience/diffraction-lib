from numpy.testing import assert_almost_equal

from easydiffraction import (
    Project,
    SampleModel,
    Experiment
)
import easydiffraction as ed


def test_single_fit_neutron_pd_cwl_lbco() -> None:
    # Create and configure sample model
    model = SampleModel('lbco')
    model.space_group.name_h_m = 'P m -3 m'
    model.cell.length_a = 3.88
    model.atom_sites.add('La', 'La', 0, 0, 0, occupancy=0.5, b_iso=0.1)
    model.atom_sites.add('Ba', 'Ba', 0, 0, 0, occupancy=0.5, b_iso=0.1)
    model.atom_sites.add('Co', 'Co', 0.5, 0.5, 0.5, b_iso=0.1)
    model.atom_sites.add('O', 'O', 0, 0.5, 0.5, b_iso=0.1)
    model.show_as_cif()

    # Create and configure experiment
    expt = Experiment('hrpt', data_path='examples/data/hrpt_lbco.xye')
    expt.instrument.setup_wavelength = 1.494
    expt.instrument.calib_twotheta_offset = 0
    expt.peak.broad_gauss_u = 0.1
    expt.peak.broad_gauss_v = -0.1
    expt.peak.broad_gauss_w = 0.2
    expt.peak.broad_lorentz_x = 0
    expt.peak.broad_lorentz_y = 0
    expt.linked_phases.add('lbco', scale=5.0)
    expt.background.add(x=10, y=170)
    expt.background.add(x=165, y=170)
    expt.show_as_cif()

    # Create project and add sample model and experiments
    project = Project()
    project.sample_models.add(model)
    project.experiments.add(expt)

    # Set calculator, minimizer and fit mode
    project.analysis.current_calculator = 'cryspy'
    #project.analysis.current_calculator = 'crysfml'
    project.analysis.current_minimizer = 'lmfit (leastsq)'

    # Compare measured and calculated patterns
    project.plot_meas_vs_calc('hrpt', 65, 68)

    # ------------ 1st fitting ------------

    # Define free parameters
    model.cell.length_a.free = True
    expt.linked_phases['lbco'].scale.free = True
    expt.instrument.calib_twotheta_offset.free = True
    expt.background['10'].y.free = True
    expt.background['165'].y.free = True
    project.analysis.show_free_params()

    # Start fitting
    project.analysis.fit()
    project.plot_meas_vs_calc('hrpt', 65, 68)

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
    project.plot_meas_vs_calc('hrpt', 65, 68)

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
    project.plot_meas_vs_calc('hrpt', 65, 68, show_residual=True)
    project.plot_meas_vs_calc('hrpt', 38, 41, show_residual=True)

    # Compare fit quality
    assert_almost_equal(project.analysis.fit_results.reduced_chi_square, 1.3, decimal=1)


def test_single_fit_neutron_pd_tof_si() -> None:
    # Create and configure sample model
    model = SampleModel('si')
    model.space_group.name_h_m = 'F d -3 m'
    model.space_group.it_coordinate_system_code = '2'
    model.cell.length_a = 5.431
    model.atom_sites.add('Si', 'Si', 0.125, 0.125, 0.125, b_iso=0.5)
    model.show_as_cif()

    # Create and configure experiment
    expt = Experiment('sepd', beam_mode='time-of-flight', data_path='examples/data/sepd_si.xye')
    expt.instrument.setup_twotheta_bank = 144.845
    expt.instrument.calib_d_to_tof_offset = 0.0
    expt.instrument.calib_d_to_tof_linear = 7476.91
    expt.instrument.calib_d_to_tof_quad = -1.54
    expt.peak_profile_type = 'pseudo-voigt * ikeda-carpenter'
    expt.peak.broad_gauss_sigma_0 = 3.0
    expt.peak.broad_gauss_sigma_1 = 40.0
    expt.peak.broad_gauss_sigma_2 = 2.0
    expt.peak.broad_mix_beta_0 = 0.04221
    expt.peak.broad_mix_beta_1 = 0.00946
    expt.peak.asym_alpha_0 = 0.0
    expt.peak.asym_alpha_1 = 0.5971
    expt.linked_phases.add('si', scale=10.0)
    for x in range(0, 35000, 5000):
        expt.background.add(x=x, y=200)
    expt.show_as_cif()

    # Create project and add sample model and experiments
    project = Project()
    project.sample_models.add(model)
    project.experiments.add(expt)

    # Set calculator, minimizer and fit mode
    project.analysis.current_calculator = 'cryspy'
    project.analysis.current_minimizer = 'lmfit (leastsq)'

    # Compare measured and calculated patterns
    project.plot_meas_vs_calc('sepd', 23200, 23700)

    # ------------ 1st fitting ------------

    # Define free parameters
    model.cell.length_a.free = True
    expt.linked_phases['si'].scale.free = True
    expt.instrument.calib_d_to_tof_offset.free = True
    project.analysis.show_free_params()

    # Start fitting
    project.analysis.fit()
    project.plot_meas_vs_calc('sepd', 23200, 23700)

    # Compare fit quality
    assert_almost_equal(project.analysis.fit_results.reduced_chi_square, 66.72, decimal=1)

    # ------------ 2nd fitting ------------

    # Define more free parameters
    for point in expt.background:
        point.y.free = True
    project.analysis.show_free_params()

    # Start fitting
    project.analysis.fit()
    project.plot_meas_vs_calc('sepd', 23200, 23700, show_residual=True)

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
    project.plot_meas_vs_calc('sepd', 23200, 23700, show_residual=True)

    # Compare fit quality
    assert_almost_equal(project.analysis.fit_results.reduced_chi_square, 3.21, decimal=1)

    # ------------ 4th fitting ------------

    # Define more free parameters
    model.atom_sites['Si'].b_iso.free = True
    project.analysis.show_free_params()

    # Start fitting
    project.analysis.fit()
    project.plot_meas_vs_calc('sepd', 23200, 23700, show_residual=True)

    # Compare fit quality
    assert_almost_equal(project.analysis.fit_results.reduced_chi_square, 3.19, decimal=1)


def test_single_fit_neutron_pd_tof_ncaf() -> None:
    # Create and configure sample model
    model = SampleModel('ncaf')
    model.space_group.name_h_m = 'I 21 3'
    model.space_group.it_coordinate_system_code = '1'
    model.cell.length_a = 10.250256
    model.atom_sites.add('Ca', 'Ca', 0.4661, 0.0, 0.25, b_iso=0.9)
    model.atom_sites.add('Al', 'Al', 0.25171, 0.25171, 0.25171, b_iso=0.66)
    model.atom_sites.add('Na', 'Na', 0.08481, 0.08481, 0.08481, b_iso=1.9)
    model.atom_sites.add('F1', 'F', 0.1375, 0.3053, 0.1195, b_iso=0.9)
    model.atom_sites.add('F2', 'F', 0.3626, 0.3634, 0.1867, b_iso=1.28)
    model.atom_sites.add('F3', 'F', 0.4612, 0.4612, 0.4612, b_iso=0.79)
    model.show_as_cif()

    # Create and configure experiment
    expt = Experiment('wish', beam_mode='time-of-flight', data_path='examples/data/wish_ncaf.xye')
    expt.instrument.setup_twotheta_bank = 152.827
    expt.instrument.calib_d_to_tof_offset = 0.0
    expt.instrument.calib_d_to_tof_linear = 20770
    expt.instrument.calib_d_to_tof_quad = -1.08308
    expt.peak_profile_type = 'pseudo-voigt * ikeda-carpenter'
    expt.peak.broad_gauss_sigma_0 = 0.0
    expt.peak.broad_gauss_sigma_1 = 0.0
    expt.peak.broad_gauss_sigma_2 = 5.0
    expt.peak.broad_mix_beta_0 = 0.01
    expt.peak.broad_mix_beta_1 = 0.01
    expt.peak.asym_alpha_0 = 0.0
    expt.peak.asym_alpha_1 = 0.1
    expt.linked_phases.add('ncaf', scale=0.5)
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

    # Set calculator, minimizer and fit mode
    project.analysis.current_calculator = 'cryspy'
    project.analysis.current_minimizer = 'lmfit (leastsq)'

    # Compare measured and calculated patterns
    project.plot_meas_vs_calc('wish', 37000, 40000)

    # ------------ 1st fitting ------------

    # Define free parameters
    #model.cell.length_a.free = True
    expt.linked_phases['ncaf'].scale.free = True
    expt.instrument.calib_d_to_tof_offset.free = True
    project.analysis.show_free_params()

    # Start fitting
    project.analysis.fit()
    project.plot_meas_vs_calc('wish', 37000, 40000)

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
    project.plot_meas_vs_calc('wish', 37000, 40000, show_residual=True)

    # Compare fit quality
    assert_almost_equal(project.analysis.fit_results.reduced_chi_square, 15.59, decimal=1)


def test_single_fit_pdf_xray_pd_cw_nacl() -> None:
    print(ed.chapter('Step 1: Create a Project'))

    # Create a new project
    project = ed.Project(name='PDF_refinement')

    # Define project info
    project.info.title = 'PDF refinement of Ni from total neutron diffraction'
    project.info.description = '''This project demonstrates simple refinement of 
    neutron diffraction data, measured using constant wavelength instruments.
    The objective is to fit the pair-distribution function of NaCl.'''

    # Show project metadata
    project.info.show_as_cif()

    print(ed.chapter('Step 2: Add Sample Model'))

    project.sample_models.add(name='nacl')

    print(ed.section('Modify sample model parameters'))

    project.sample_models['nacl'].space_group.name_h_m = 'F m -3 m'
    project.sample_models['nacl'].space_group.it_coordinate_system_code = '1'

    project.sample_models['nacl'].cell.length_a = 5.62

    project.sample_models['nacl'].atom_sites.add(label='Na',
                                                 type_symbol='Na',
                                                 fract_x=0,
                                                 fract_y=0,
                                                 fract_z=0,
                                                 wyckoff_letter='a',
                                                 b_iso=1.0)
    project.sample_models['nacl'].atom_sites.add(label='Cl',
                                                 type_symbol='Cl',
                                                 fract_x=0.5,
                                                 fract_y=0.5,
                                                 fract_z=0.5,
                                                 wyckoff_letter='b',
                                                 b_iso=1.0)

    print(ed.section('Show sample model as CIF'))
    project.sample_models['nacl'].show_as_cif()

    print(ed.chapter('Step 3: Add Experiments (Instrument models and measured data)'))

    # Load measured data and create a new experiment
    project.experiments.add(name='xray_pdf',
                            sample_form='powder',
                            beam_mode='constant wavelength',
                            radiation_probe='xray',
                            scattering_type='total',
                            data_path='examples/data/NaCl.gr')

    print(ed.section('Setup data plotter'))
    project.plotter.show_config()
    project.plotter.show_supported_engines()
    # project.plotter.engine = 'plotly'
    project.plotter.x_min = 3.5
    project.plotter.x_max = 4.5

    print(ed.section('Show measured data'))
    project.plot_meas(expt_name='xray_pdf')

    print(ed.section('Modify experimental parameters'))

    # Peak profile parameters
    project.experiments['xray_pdf'].show_supported_peak_profile_types()
    project.experiments['xray_pdf'].show_current_peak_profile_type()
    project.experiments['xray_pdf'].peak_profile_type = 'gaussian-damped-sinc'
    project.experiments['xray_pdf'].peak.damp_q = 0.03
    project.experiments['xray_pdf'].peak.broad_q = 0
    project.experiments['xray_pdf'].peak.cutoff_q = 21
    project.experiments['xray_pdf'].peak.sharp_delta_1 = 0
    project.experiments['xray_pdf'].peak.sharp_delta_2 = 5
    project.experiments['xray_pdf'].peak.damp_particle_diameter = 0

    # Link sample model (defined in the previous step) to the experiment
    project.experiments['xray_pdf'].linked_phases.add(id='nacl', scale=1.0)

    # Show experiment as CIF
    project.experiments['xray_pdf'].show_as_cif()

    print(ed.chapter('Step 4: Analysis'))

    print(ed.section('Set calculator'))
    project.analysis.show_supported_calculators()  # Need to hide the ones not suitable for PDF
    project.analysis.show_current_calculator()
    project.analysis.current_calculator = 'pdffit'

    print(ed.section('Show calculated data'))
    project.plot_calc(expt_name='xray_pdf')

    print(ed.section('Show calculated vs measured data'))
    project.plot_meas_vs_calc(expt_name='xray_pdf', show_residual=True)

    print(ed.section('Show all parameters'))
    project.analysis.show_all_params()

    print(ed.section('Show all fittable parameters'))
    project.analysis.show_fittable_params()

    print(ed.section('Show only free parameters'))
    project.analysis.show_free_params()

    print(ed.section('Show how to access parameters in the code'))
    project.analysis.how_to_access_parameters(show_description=False)

    print(ed.section('Select specific parameters for fitting'))
    # Sample model parameters
    project.sample_models['nacl'].cell.length_a.free = True
    project.sample_models['nacl'].atom_sites['Na'].b_iso.free = True
    project.sample_models['nacl'].atom_sites['Cl'].b_iso.free = True
    # Experimental parameters
    project.experiments['xray_pdf'].linked_phases['nacl'].scale.free = True
    project.experiments['xray_pdf'].peak.damp_q.free = True
    project.experiments['xray_pdf'].peak.sharp_delta_2.free = True
    # Show free parameters after selection
    project.analysis.show_free_params()

    print(ed.section('Start fitting'))
    project.analysis.fit()

    print(ed.section('Show data charts after fitting'))
    project.plot_meas_vs_calc(expt_name='xray_pdf', show_residual=True)

    # Show analysis as CIF
    project.analysis.show_as_cif()

    print(ed.chapter('Step 5: Summary'))
    project.summary.show_report()

    # Compare fit quality
    assert_almost_equal(project.analysis.fit_results.reduced_chi_square, 1.48, decimal=2)


def test_single_fit_pdf_neutron_pd_cw_ni():
    project = ed.Project()

    # Set sample model
    project.sample_models.add(name='ni')
    project.sample_models['ni'].space_group.name_h_m.value = 'F m -3 m'
    project.sample_models['ni'].space_group.it_coordinate_system_code = '1'
    project.sample_models['ni'].cell.length_a = 3.52387
    project.sample_models['ni'].atom_sites.add(label='Ni',
                                               type_symbol='Ni',
                                               fract_x=0.,
                                               fract_y=0.,
                                               fract_z=0.,
                                               wyckoff_letter='a',
                                               b_iso=0.5)

    # Set experiment
    # Data from https://github.com/diffpy/cmi_exchange/blob/main/cmi_scripts/fitNiPDF/ni-q27r100-neutron.gr
    project.experiments.add(name='pdf',
                            sample_form='powder',
                            beam_mode='constant wavelength',
                            radiation_probe='neutron',
                            scattering_type='total',
                            data_path='examples/data/ni-q27r100-neutron_from-2.gr')
    project.experiments['pdf'].linked_phases.add(id='ni', scale=1.)
    project.experiments['pdf'].peak.damp_q = 0
    project.experiments['pdf'].peak.broad_q = 0.03
    project.experiments['pdf'].peak.cutoff_q = 27.0
    project.experiments['pdf'].peak.sharp_delta_1 = 0.0
    project.experiments['pdf'].peak.sharp_delta_2 = 2.0
    project.experiments['pdf'].peak.damp_particle_diameter = 0

    project.sample_models['ni'].cell.length_a.free = True
    project.sample_models['ni'].atom_sites['Ni'].b_iso.free = True
    project.experiments['pdf'].linked_phases['ni'].scale.free = True
    project.experiments['pdf'].peak.broad_q.free = True
    project.experiments['pdf'].peak.sharp_delta_2.free = True

    project.analysis.current_calculator = 'pdffit'
    project.analysis.fit()

    assert_almost_equal(project.analysis.fit_results.reduced_chi_square, 207.1, decimal=1)


def test_single_fit_pdf_neutron_pd_tof_si():
    project = ed.Project()

    # Set sample model
    project.sample_models.add(name='si')
    sample_model = project.sample_models['si']
    sample_model.space_group.name_h_m.value = 'F d -3 m'
    sample_model.space_group.it_coordinate_system_code = '1'
    sample_model.cell.length_a = 5.43146
    sample_model.atom_sites.add(label='Si',
                                type_symbol='Si',
                                fract_x=0,
                                fract_y=0,
                                fract_z=0,
                                wyckoff_letter='a',
                                b_iso=0.5)

    # Set experiment
    project.experiments.add(name='nomad',
                            sample_form='powder',
                            beam_mode='time-of-flight',
                            radiation_probe='neutron',
                            scattering_type='total',
                            data_path='examples/data/NOM_9999_Si_640g_PAC_50_ff_ftfrgr_up-to-50.gr')
    experiment = project.experiments['nomad']
    experiment.linked_phases.add(id='si', scale=1.)
    experiment.peak.damp_q = 0.02
    experiment.peak.broad_q = 0.03
    experiment.peak.cutoff_q = 35.0
    experiment.peak.sharp_delta_1 = 0.0
    experiment.peak.sharp_delta_2 = 4.0
    experiment.peak.damp_particle_diameter = 0

    # Select fitting parameters
    project.sample_models['si'].cell.length_a.free = True
    project.sample_models['si'].atom_sites['Si'].b_iso.free = True
    experiment.linked_phases['si'].scale.free = True
    experiment.peak.damp_q.free = True
    experiment.peak.broad_q.free = True
    experiment.peak.sharp_delta_1.free = True
    experiment.peak.sharp_delta_2.free = True

    # Fit
    project.analysis.current_calculator = 'pdffit'
    project.analysis.fit()

    # Compare fit quality
    assert_almost_equal(project.analysis.fit_results.reduced_chi_square, 170.54, decimal=1)


if __name__ == '__main__':
    test_single_fit_neutron_pd_cwl_lbco()
    #test_single_fit_neutron_pd_tof_si()
    #test_single_fit_neutron_pd_tof_ncaf()
    #test_single_fit_pdf_xray_pd_cw_nacl()
    #test_single_fit_pdf_neutron_pd_cw_ni()
    #test_single_fit_pdf_neutron_pd_tof_si()