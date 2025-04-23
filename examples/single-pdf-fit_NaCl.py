import easydiffraction as ed

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

project.sample_models['nacl'].cell.length_a = 5.62

project.sample_models['nacl'].atom_sites.add(label='Na',
                                             type_symbol='Na',
                                             fract_x=0,
                                             fract_y=0,
                                             fract_z=0,
                                             b_iso=0.01 * 8 * 3.14159**2)
project.sample_models['nacl'].atom_sites.add(label='Cl',
                                             type_symbol='Cl',
                                             fract_x=0.5,
                                             fract_y=0.5,
                                             fract_z=0.5,
                                             b_iso=0.01 * 8 * 3.14159**2)

print(ed.section('Show sample model as CIF'))
project.sample_models['nacl'].show_as_cif()

print(ed.chapter('Step 3: Add Experiments (Instrument models and measured data)'))

# Load measured data and create a new experiment
project.experiments.add(name='pdf',
                        sample_form='powder',
                        beam_mode='constant wavelength',
                        radiation_probe='xray',
                        diffraction_type='total',
                        data_path='examples/data/NaCl.gr')

print(ed.section('Setup data plotter'))
project.plotter.show_config()
project.plotter.show_supported_engines()
#project.plotter.engine = 'plotly'
project.plotter.x_min = 3.5
project.plotter.x_max = 4.5

print(ed.section('Show measured data'))
project.plot_meas(expt_name='pdf')

print(ed.section('Modify experimental parameters'))

# Instrument parameters
project.experiments['pdf'].instrument.setup_wavelength = 0.21281

#project.experiments['pdf'].instrument.qmin = 0.1  # Left Q-value cutoff for PDF calculation. Not implemented.
#project.experiments['pdf'].instrument.qmax = 23   # Right Q-value cutoff for PDF calculation. Implemented, but will not be needed, when excluded regions are implemented.

# Currently instrumental parameters, but need to be moved to the peak profile class.
project.experiments['pdf'].instrument.qdamp = 0.03   # Instrumental Q-resolution factor
project.experiments['pdf'].instrument.delta1 = 0     # 1/R peak sharpening factor
project.experiments['pdf'].instrument.delta2 = 5     # (1/R^2) sharpening factor
project.experiments['pdf'].instrument.qbroad = 0     # Quadratic peak broadening factor
project.experiments['pdf'].instrument.spdiameter = 0 # Diameter value for the spherical particle PDF correction

# Add a background. Not needed for PDF?
project.experiments['pdf'].background.add(x=0, y=0.0)
project.experiments['pdf'].background.add(x=50, y=0.0)

# Link sample model (defined in the previous step) to the experiment
project.experiments['pdf'].linked_phases.add(id='nacl', scale=1.0)

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
project.sample_models['nacl'].cell.length_a.free = True
project.sample_models['nacl'].atom_sites['Na'].b_iso.free = True
project.sample_models['nacl'].atom_sites['Cl'].b_iso.free = True
# Experimental parameters
project.experiments['pdf'].linked_phases['nacl'].scale.free = True
project.experiments['pdf'].instrument.qdamp.free = True
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
