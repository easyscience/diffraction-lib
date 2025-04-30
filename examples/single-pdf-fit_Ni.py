import easydiffraction as ed

project = ed.Project()

project.plotter.engine = 'plotly'

project.sample_models.add(name='ni')
project.sample_models['ni'].space_group.name_h_m = 'F m -3 m'
project.sample_models['ni'].space_group.it_coordinate_system_code = '1'
project.sample_models['ni'].cell.length_a = 3.52387
project.sample_models['ni'].atom_sites.add(label='Ni',
                                           type_symbol='Ni',
                                           fract_x=0.,
                                           fract_y=0.,
                                           fract_z=0.,
                                           wyckoff_letter='a',
                                           b_iso=0.5)

# Taken from https://github.com/diffpy/cmi_exchange/blob/main/cmi_scripts/fitNiPDF/ni-q27r100-neutron.gr
project.experiments.add(name='pdf',
                        sample_form='powder',
                        beam_mode='constant wavelength',
                        radiation_probe='neutron',
                        scattering_type='total',
                        data_path = 'examples/data/ni-q27r100-neutron_from-2.gr')
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

project.plot_meas_vs_calc(expt_name='pdf', show_residual=True)
