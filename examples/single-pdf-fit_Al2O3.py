# for plotting
from bokeh.io import show
from bokeh.plotting import figure

import easydiffraction as ed

project = ed.Project(name="PDF_refinement")

# Define project info
project.info.title = "PDF refinement of Al2O3 from total neutron diffraction"
project.info.description = """This project demonstrates simple refinement of neutron diffraction data,
measured using constant wavelength instruments.
The objective is to accurately fit the pair-distribution function of Al2O3."""

project.plotter.engine = 'plotly'
# Add a sample model with default parameters
project.sample_models.add(name="al2o3")

project.sample_models["al2o3"].space_group.name_h_m.value = "R -3 c"

project.sample_models["al2o3"].cell.length_a.value = 3.52
project.sample_models["al2o3"].cell.length_b.value = 3.52
project.sample_models["al2o3"].cell.length_c.value = 3.52
project.sample_models["al2o3"].cell.angle_alpha.value = 90.0
project.sample_models["al2o3"].cell.angle_beta.value = 90.0
project.sample_models["al2o3"].cell.angle_gamma.value = 90.0

project.sample_models["al2o3"].atom_sites.add(label='Al',
                                           type_symbol='Al',
                                           fract_x=0.,
                                           fract_y=0.,
                                           fract_z=0.35228,
                                           b_iso=0.0182)
project.sample_models["al2o3"].atom_sites.add(label='O',
                                           type_symbol='O',
                                           fract_x=0.30640,
                                           fract_y=0.0,
                                           fract_z=0.25,
                                           b_iso=0.0161)


# Taken from https://github.com/diffpy/diffpy.github.io/blob/source/static_root/doc/pdfgetx/2.2.1/pdfgetxn3-examples.zip
# n-Sapphire example project
project.experiments.add(name="pdf",
                        sample_form="powder",
                        beam_mode="constant wavelength",
                        radiation_probe="neutron",
                        scattering_type="total",
                        data_path=r"data\sapphire755-expected.gr")

x_min = project.experiments["pdf"].datastore.pattern.x[0]
x_max = project.experiments["pdf"].datastore.pattern.x[-1]

# Link sample model to experiments
project.experiments['pdf'].linked_phases.add(id='al2o3', scale=0.72)

# Update instrument parameters
project.experiments["pdf"].peak.cutoff_q.value = 11.2
project.experiments["pdf"].peak.damp_q.value = 0.0723
project.experiments["pdf"].peak.sharp_delta_1.value = 0.001
project.experiments["pdf"].peak.sharp_delta_2.value = 2.253193
project.experiments["pdf"].peak.broad_q.value = 0.12
project.experiments["pdf"].instrument.setup_wavelength.value = 1.0989
project.experiments["pdf"].peak.damp_particle_diameter.value = 0.0

project.analysis.current_calculator = 'pdffit'

pattern = project.analysis.calculate_pattern('pdf')

project.plot_meas_vs_calc(expt_name='pdf', x_min=x_min, x_max=x_max)

# obtain data from PdfFit calculator object
x_data = project.experiments["pdf"].datastore.pattern.x

# while free parameters are currently set to be adjusted.
print(ed.section('Show only free parameters'))
project.analysis.show_free_params()

print(ed.section('Select specific parameters for refinement'))
project.sample_models["al2o3"].cell.length_a.free = True
project.sample_models["al2o3"].atom_sites['Al'].b_iso.free = True
project.sample_models["al2o3"].atom_sites['O'].b_iso.free = True

project.experiments["pdf"].linked_phases['al2o3'].scale.free = True
project.experiments["pdf"].peak.cutoff_q.free = True
project.experiments["pdf"].peak.damp_q.free = True
project.experiments["pdf"].peak.sharp_delta_2.free = True
project.experiments["pdf"].peak.broad_q.free = True
project.experiments["pdf"].instrument.setup_wavelength.free = True
project.experiments["pdf"].peak.damp_particle_diameter.free = True

project.analysis.show_free_params()

print(ed.section('Start fitting'))
project.analysis.fit()

print(ed.section('Show data charts after fitting'))
project.plot_meas_vs_calc(expt_name='pdf', x_min=x_min, x_max=x_max, show_residual=True)


