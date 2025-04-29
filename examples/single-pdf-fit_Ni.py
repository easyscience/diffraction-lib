# for plotting
from bokeh.io import show
from bokeh.plotting import figure

import easydiffraction as ed

project = ed.Project(name="PDF_refinement")

# Define project info
project.info.title = "PDF refinement of Ni from total neutron diffraction"
project.info.description = """This project demonstrates simple refinement of neutron diffraction data,
measured using constant wavelength instruments.
The objective is to accurately fit the pair-distribution function of Ni."""

project.plotter.engine = 'plotly'
# Add a sample model with default parameters
project.sample_models.add(name="ni")

project.sample_models["ni"].space_group.name_h_m.value = "F m -3 m"

project.sample_models["ni"].cell.length_a.value = 3.52387
project.sample_models["ni"].cell.length_b.value = 3.52387
project.sample_models["ni"].cell.length_c.value = 3.52387
project.sample_models["ni"].cell.angle_alpha.value = 90.0
project.sample_models["ni"].cell.angle_beta.value = 90.0
project.sample_models["ni"].cell.angle_gamma.value = 90.0

project.sample_models["ni"].atom_sites.add(label='Ni',
                                           type_symbol='Ni',
                                           fract_x=0.,
                                           fract_y=0.,
                                           fract_z=0.,
                                           b_iso=0.005)

# Taken from https://github.com/diffpy/cmi_exchange/blob/main/cmi_scripts/fitNiPDF/ni-q27r100-neutron.gr
project.experiments.add(name="pdf",
                        sample_form="powder",
                        beam_mode="constant wavelength",
                        radiation_probe="neutron",
                        scattering_type="total",
                        data_path=r"data\ni-q27r100-neutron.gr")

x_min = project.experiments["pdf"].datastore.pattern.x[0]
x_max = project.experiments["pdf"].datastore.pattern.x[-1]

# Link sample model to experiments
project.experiments['pdf'].linked_phases.add(id='ni', scale=100.)

# Update instrument parameters
project.experiments["pdf"].peak.cutoff_q.value = 27.0
project.experiments["pdf"].peak.damp_q.value = 0.063043
project.experiments["pdf"].peak.sharp_delta_1.value = 0.0
project.experiments["pdf"].peak.sharp_delta_2.value = 5.0
project.experiments["pdf"].peak.broad_q.value = 0.1
project.experiments["pdf"].instrument.setup_wavelength.value = 1.0989
# let's limit the range of qbroad to 0.0-0.5
project.experiments["pdf"].peak.broad_q.min = 0.0
project.experiments["pdf"].peak.broad_q.max = 0.5
project.experiments["pdf"].peak.damp_particle_diameter.value = 0.5

project.analysis.current_calculator = 'pdffit'

pattern = project.analysis.calculate_pattern('pdf')

project.plot_meas_vs_calc(expt_name='pdf', x_min=1.0, x_max=x_max, show_residual=True)

# Refinable parameters are those that can be adjusted during refinement,
# while free parameters are currently set to be adjusted.
print(ed.section('Show only free parameters'))
project.analysis.show_free_params()

print(ed.section('Select specific parameters for refinement'))
project.sample_models["ni"].cell.length_a.free = True
project.sample_models["ni"].cell.length_b.free = True
project.sample_models["ni"].cell.length_c.free = True

project.experiments["pdf"].linked_phases['ni'].scale.free = True

project.experiments["pdf"].peak.cutoff_q.free = True
project.experiments["pdf"].peak.damp_q.free = True
project.experiments["pdf"].peak.sharp_delta_1.free = True
project.experiments["pdf"].peak.sharp_delta_2.free = True
project.experiments["pdf"].peak.broad_q.free = True
project.experiments["pdf"].peak.damp_particle_diameter.free = True

project.analysis.show_free_params()

print(ed.section('Start fitting'))
project.analysis.fit()

print(ed.section('Show data charts after 4th fitting'))
project.plot_meas_vs_calc(expt_name='pdf', x_min=x_min, x_max=x_max, show_residual=True)


