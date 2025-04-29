import easydiffraction as ed

project = ed.Project()

project.plotter.engine = 'plotly'

project.sample_models.add(name='si')
project.sample_models['si'].space_group.name_h_m.value = 'F d -3 m'
project.sample_models['si'].space_group.it_coordinate_system_code = '1'
project.sample_models['si'].cell.length_a = 5.43146
project.sample_models['si'].atom_sites.add(label='Si',
                                           type_symbol='Si',
                                           fract_x=0,
                                           fract_y=0,
                                           fract_z=0,
                                           wyckoff_letter='a',
                                           b_iso=0.5)

project.experiments.add(name='nomad',
                        sample_form='powder',
                        beam_mode='constant wavelength',  # this is time-of-flight!
                        radiation_probe='neutron',
                        scattering_type='total',
                        data_path = 'examples/data/NOM_9999_Si_640g_PAC_50_ff_ftfrgr_up-to-50.gr')
project.experiments['nomad'].linked_phases.add(id='si', scale=1.)
project.experiments['nomad'].peak.damp_q = 0.02
project.experiments['nomad'].peak.broad_q = 0.03
project.experiments['nomad'].peak.cutoff_q = 35.0
project.experiments['nomad'].peak.sharp_delta_1 = 0.0
project.experiments['nomad'].peak.sharp_delta_2 = 4.0
project.experiments['nomad'].peak.damp_particle_diameter = 0

project.sample_models['si'].cell.length_a.free = True
project.sample_models['si'].atom_sites['Si'].b_iso.free = True
project.experiments['nomad'].linked_phases['si'].scale.free = True
project.experiments['nomad'].peak.damp_q.free = True
project.experiments['nomad'].peak.broad_q.free = True
project.experiments['nomad'].peak.sharp_delta_1.free = True
project.experiments['nomad'].peak.sharp_delta_2.free = True

project.analysis.current_calculator = 'pdffit'
project.analysis.fit()

project.plot_meas_vs_calc(expt_name='nomad')