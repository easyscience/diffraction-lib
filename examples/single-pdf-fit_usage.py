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

# Add a sample model with default parameters
project.sample_models.add(name="Ni")

project.sample_models["Ni"].space_group.name_h_m.value = "F m -3 m"

project.sample_models["Ni"].cell.length_a.value = 3.52
project.sample_models["Ni"].cell.length_b.value = 3.52
project.sample_models["Ni"].cell.length_c.value = 3.52
project.sample_models["Ni"].cell.angle_alpha.value = 90.0
project.sample_models["Ni"].cell.angle_beta.value = 90.0
project.sample_models["Ni"].cell.angle_gamma.value = 90.0

project.sample_models["Ni"].atom_sites.add(label='Ni',
                                           type_symbol='Ni',
                                           fract_x=0.,
                                           fract_y=0.,
                                           fract_z=0.,
                                           b_iso=0.005445)


project.experiments.add(name="ni_pdf",
                        sample_form="powder",
                        beam_mode="constant wavelength",
                        radiation_probe="xray",
                        diffraction_type="total",
                        data_path=r"examples\data\Ni-xray.gr")

x_min = project.experiments["ni_pdf"].datastore.pattern.x[0]
x_max = project.experiments["ni_pdf"].datastore.pattern.x[-1]

project.experiments['ni_pdf'].linked_phases.add(id='Ni', scale=0.77)

# Update instrument parameters
project.experiments["ni_pdf"].instrument.qmax.value = 20
project.experiments["ni_pdf"].instrument.qdamp.value = 0.073
project.experiments["ni_pdf"].instrument.delta1.value = -26.0
project.experiments["ni_pdf"].instrument.delta2.value = 60.36
project.experiments["ni_pdf"].instrument.qbroad.value = 0.078
project.experiments["ni_pdf"].instrument.setup_wavelength.value = 0.126514
# let's limit the range of qbroad to 0.0-0.5
project.experiments["ni_pdf"].instrument.qbroad.min = 0.0
project.experiments["ni_pdf"].instrument.qbroad.max = 0.5
project.experiments["ni_pdf"].instrument.spdiameter.value = 0.0

project.experiments['ni_pdf'].background.add(x=0.0, y=0.)
project.experiments['ni_pdf'].background.add(x=20.0, y=0.0)

project.analysis.current_calculator = 'pdffit'

pattern = project.analysis.calculate_pattern('ni_pdf')


# obtain data from PdfFit calculator object
x_data = project.experiments["ni_pdf"].datastore.pattern.x
Gobs = project.experiments["ni_pdf"].datastore.pattern.meas
Gfit = project.experiments["ni_pdf"].datastore.pattern.calc

Gdiff = Gobs - Gfit
Gdiff_baseline = -10

Gdiff_show = Gdiff + Gdiff_baseline

fig = figure()
fig.xaxis.axis_label = 'r (Å)'
fig.yaxis.axis_label = r"$$G (Å^{-2})\$$"
fig.title.text = 'Fit of nickel to x-ray experimental PDF'

fig.scatter(x_data, Gobs, legend_label='G(r) Data', fill_alpha=0., line_color='steelblue', marker='circle')
fig.line(x_data, Gfit, legend_label='G(r) Fit', color='orangered', line_width=2)
fig.line(x_data, Gdiff_show, legend_label='G(r) Diff', color='grey', line_width=2)
show(fig)

print(ed.section('Show all parameters'))
project.analysis.show_all_params()

print(ed.section('Show all fittable parameters'))
project.analysis.show_fittable_params()

print(ed.section('Select specific parameters for refinement'))
project.sample_models["Ni"].cell.length_a.free = True

project.experiments["ni_pdf"].linked_phases['Ni'].scale.free = True

project.experiments["ni_pdf"].instrument.qdamp.free = True
project.experiments["ni_pdf"].instrument.delta1.free = True
project.experiments["ni_pdf"].instrument.delta2.free = True
project.experiments["ni_pdf"].instrument.qbroad.free = True

project.analysis.show_free_params()

print(ed.section('Start fitting'))
project.analysis.fit()

Gfit = project.experiments["ni_pdf"].datastore.pattern.calc
Gdiff = Gobs - Gfit
Gdiff_baseline = -10

Gdiff_show = Gdiff + Gdiff_baseline

fig = figure()
fig.xaxis.axis_label = 'r (Å)'
fig.yaxis.axis_label = r"$$G (Å^{-2})\$$"
fig.title.text = 'Fit of nickel to x-ray experimental PDF'

fig.scatter(x_data, Gobs, legend_label='G(r) Data', fill_alpha=0., line_color='steelblue', marker='circle')
fig.line(x_data, Gfit, legend_label='G(r) Fit', color='orangered', line_width=2)
fig.line(x_data, Gdiff_show, legend_label='G(r) Diff', color='grey', line_width=2)
show(fig)

# # Show analysis as CIF
project.analysis.show_as_cif()
