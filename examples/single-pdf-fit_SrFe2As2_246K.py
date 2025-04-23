import easydiffraction as ed

print(ed.chapter('Step 1: Create a Project'))

# Create a new project
project = ed.Project(name='PDF_refinement')

# Define project info
project.info.title = 'PDF refinement of SrFe2As2 from total neutron diffraction'
project.info.description = '''This project demonstrates simple refinement of 
X-ray diffraction data, measured using constant wavelength instruments.
The objective is to fit the pair-distribution function of SrFe2As2.'''

# Show project metadata
project.info.show_as_cif()

print(ed.chapter('Step 2: Add Sample Model'))

project.sample_models.add(name='sfa')

project.sample_models['sfa'].space_group.name_h_m = 'I 4/m m m'

project.sample_models['sfa'].cell.length_a = 3.93
project.sample_models['sfa'].cell.length_c = 12.37

project.sample_models['sfa'].atom_sites.add(label='Sr',
                                            type_symbol='Sr',
                                            fract_x=0,
                                            fract_y=0,
                                            fract_z=0,
                                            b_iso=0.5)
project.sample_models['sfa'].atom_sites.add(label='Fe',
                                            type_symbol='Fe',
                                            fract_x=0,
                                            fract_y=0.5,
                                            fract_z=0.25,
                                            b_iso=0.5)
project.sample_models['sfa'].atom_sites.add(label='As',
                                            type_symbol='As',
                                            fract_x=0,
                                            fract_y=0,
                                            fract_z=0.361,
                                            b_iso=0.5)

print(ed.section('Show sample model as CIF'))
project.sample_models['sfa'].show_as_cif()

print(ed.chapter('Step 3: Add Experiments (Instrument models and measured data)'))

# Load measured data and create a new experiment
# https://gitlab.thebillingegroup.com/tutorials/uppsalaschool2019/-/blob/master/diffpy_tutorial_3/data/SrFe2As2_246K.gr
project.experiments.add(name='pdf',
                        sample_form='powder',
                        beam_mode='constant wavelength',
                        radiation_probe='xray',
                        diffraction_type='total',
                        data_path='examples/data/SrFe2As2_246K.gr')

print(ed.section('Setup data plotter'))
project.plotter.show_config()
project.plotter.show_supported_engines()
project.plotter.engine = 'asciichartpy'
project.plotter.x_min = 8.0
project.plotter.x_max = 9.5
#project.plotter_config.engine = 'plotly'
#project.plotter_config.x_min = 2
#project.plotter_config.x_max = 50

print(ed.section('Show measured data'))
project.plot_meas(expt_name='pdf')

print(ed.section('Modify experimental parameters'))

# Instrument parameters
project.experiments['pdf'].instrument.setup_wavelength = 0.1

#project.experiments['pdf'].instrument.qmin = 0.1  # Left Q-value cutoff for PDF calculation. Not implemented.
#project.experiments['pdf'].instrument.qmax = 23   # Right Q-value cutoff for PDF calculation. Implemented, but will not be needed, when excluded regions are implemented.

# Currently instrumental parameters, but need to be moved to the peak profile class.
project.experiments['pdf'].instrument.qdamp = 0.0349  # Instrumental Q-resolution factor
project.experiments['pdf'].instrument.delta1 = 1.6    # 1/R peak sharpening factor
project.experiments['pdf'].instrument.delta2 = 0      # (1/R^2) sharpening factor
project.experiments['pdf'].instrument.qbroad = 0.0176 # Quadratic peak broadening factor
project.experiments['pdf'].instrument.spdiameter = 0  # Diameter value for the spherical particle PDF correction

# Add a background. Not needed for PDF?
project.experiments['pdf'].background.add(x=0, y=0.0)
project.experiments['pdf'].background.add(x=50, y=0.0)

# Link sample model (defined in the previous step) to the experiment
project.experiments['pdf'].linked_phases.add(id='sfa', scale=1.0)

# Show experiment as CIF
project.experiments['pdf'].show_as_cif()

print(ed.chapter('Step 4: Analysis'))

print(ed.section('Set calculator'))
project.analysis.show_supported_calculators()  # Need to hide the ones not suitable for PDF
project.analysis.show_current_calculator()
project.analysis.current_calculator = 'pdffit'

print(ed.section('Show calculated data'))
project.plot_calc(expt_name='pdf')

print(ed.section('Show calculated vs measured data'))
project.plot_meas_vs_calc(expt_name='pdf', show_residual=True)

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
project.sample_models['sfa'].cell.length_a.free = True
project.sample_models['sfa'].cell.length_c.free = True
project.sample_models['sfa'].atom_sites['Sr'].b_iso.free = True
project.sample_models['sfa'].atom_sites['Fe'].b_iso.free = True
project.sample_models['sfa'].atom_sites['As'].b_iso.free = True
project.sample_models['sfa'].atom_sites['As'].fract_z.free = True
# Experimental parameters
project.experiments['pdf'].linked_phases['sfa'].scale.free = True
project.experiments['pdf'].instrument.delta2.free = True
# Show free parameters after selection
project.analysis.show_free_params()

print(ed.section('Start fitting'))
project.analysis.fit()

print(ed.section('Show data charts after fitting'))
project.plot_meas_vs_calc(expt_name='pdf', show_residual=True)

# Show analysis as CIF
project.analysis.show_as_cif()

print(ed.chapter('Step 5: Summary'))
project.summary.show_report()
