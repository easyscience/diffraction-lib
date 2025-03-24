import easydiffraction as ed

# === Step 1: Create a Project ===

# Create a new project
project = ed.Project(project_id="JointDiffractionAnalysis")

# Set project metadata
project.info.title = "Joint CW/TOF Neutron Diffraction Analysis"
project.info.description = """
This project performs joint refinement of constant wavelength and 
time-of-flight neutron diffraction data for a polycrystalline sample.
"""

# Show project metadata
print(project.info.as_cif())

# Save the initial project (directory must exist)
# project.save_as("projects/my_diffraction_project")

# === Step 2: Add Sample Models ===

# Create a model with default parameters
model1 = ed.SampleModel(id="pbso4")

# Change some parameters from default
model1.space_group.name = "P n m a"

# Add model to collection of sample models in the project
project.sample_models.add(model1)

# Show model IDs to be used for accessing the model via project.sample_models["model_id"]
project.sample_models.show_ids()

# Show model parameters
#project.sample_models["model1"].show_params()

# Modify parameters via project object
project.sample_models["pbso4"].cell.length_a.value = 8.4693
project.sample_models["pbso4"].cell.length_b.value = 5.391
project.sample_models["pbso4"].cell.length_c.value = 6.9506
project.sample_models["pbso4"].atom_sites.add(label='Pb',
                                              type_symbol='Pb',
                                              fract_x=0.1876,
                                              fract_y=0.25,
                                              fract_z=0.167,
                                              b_iso=1.3729)

# Modify parameters via model object (same object reference)
model1.atom_sites.add(label='S',
                      type_symbol='S',
                      fract_x=0.0654,
                      fract_y=0.25,
                      fract_z=0.684,
                      b_iso=0.3777)
model1.atom_sites.add(label='O1',
                      type_symbol='O',
                      fract_x=0.9082,
                      fract_y=0.25,
                      fract_z=0.5954,
                      b_iso=1.9764)
model1.atom_sites.add(label='O2',
                      type_symbol='O',
                      fract_x=0.1935,
                      fract_y=0.25,
                      fract_z=0.5432,
                      b_iso=1.4456)
model1.atom_sites.add(label='O3',
                      type_symbol='O',
                      fract_x=0.0811,
                      fract_y=0.0272,
                      fract_z=0.8086,
                      b_iso=1.2822)

# Show model as CIF string
print(project.sample_models["pbso4"].as_cif())

# Show sample model structure
#project.sample_models["pbso4"].show_structure(plane='xy')


print("\n")

# === Step 3: Add Experiments (Measurements) ===


# Create a virtual experiment (no measured data) with default parameters

# Create an experiment dynamically
#expt_high = ed.Experiment(
#    id="expt_high",
#    diffr_mode="powder", # "powder" or "single_crystal"
#    expt_mode="constant_wavelength", # "time_of_flight" or "constant_wavelength"
#    radiation_probe="neutron" # "neutron" or "xray"
#)

# Load real experiment (including measured data) with default parameters

# Create an experiment dynamically
expt_high = ed.Experiment(
    id="expt_high",
    diffr_mode="powder", # "powder" or "single_crystal"
    expt_mode="constant_wavelength", # "time_of_flight" or "constant_wavelength"
    radiation_probe="neutron", # "neutron" or "xray"
    data_path="data/pbso4_powder_neutron_cw_60-100.dat" # Path to ASCII data file (x, y, sy)
)

expt_high.linked_phases.add(id='pbso4', scale=1.0)

# Show experiment with default parameters as CIF string
print(expt_high.as_cif())

# Show measured data
expt_high.show_meas_chart(x_min=62, x_max=66)

# Modify experiment parameters directly on the experiment object
expt_high.instr_setup.wavelength = 1.91

# Add experiment to collection of experiments in the project
project.experiments.add(expt_high)

# Show defined experiments
project.experiments.show_ids()




# Modify experiment parameters via project object and experiment ID
project.experiments["expt_high"].instr_calib.twotheta_offset = -0.1406

project.experiments["expt_high"].peak_broad.gauss_u = 0.139
project.experiments["expt_high"].peak_broad.gauss_v = -0.412
project.experiments["expt_high"].peak_broad.gauss_w = 0.386
project.experiments["expt_high"].peak_broad.lorentz_x = 0
project.experiments["expt_high"].peak_broad.lorentz_y = 0.088


# Show experiment as CIF string. Now via the project object
print(project.experiments["expt_high"].as_cif())





# Load 2nd real experiment (including measured data)

# Create an experiment dynamically
expt_low = ed.Experiment(
    id="expt_low",
    diffr_mode="powder", # "powder" or "single_crystal"
    expt_mode="constant_wavelength", # "time_of_flight" or "constant_wavelength"
    radiation_probe="neutron", # "neutron" or "xray"
    data_path="data/pbso4_powder_neutron_cw_10-60.dat" # Path to ASCII data file (x, y, sy)
)

expt_low.linked_phases.add(id='pbso4', scale=1.0)

# Show experiment with default parameters as CIF string
print(expt_low.as_cif())

# Show measured data
expt_low.show_meas_chart(x_min=54, x_max=57)

# Modify experiment parameters directly on the experiment object
expt_low.instr_setup.wavelength = 1.91

# Add experiment to collection of experiments in the project
project.experiments.add(expt_low)

# Show defined experiments
project.experiments.show_ids()




# Modify experiment parameters via project object and experiment ID
project.experiments["expt_low"].instr_calib.twotheta_offset = -0.1406

project.experiments["expt_low"].peak_broad.gauss_u = 0.139
project.experiments["expt_low"].peak_broad.gauss_v = -0.412
project.experiments["expt_low"].peak_broad.gauss_w = 0.386
project.experiments["expt_low"].peak_broad.lorentz_x = 0
project.experiments["expt_low"].peak_broad.lorentz_y = 0.088


# Show experiment as CIF string. Now via the project object
print(project.experiments["expt_low"].as_cif())








print('\n=== Step 4: Analysis ===')

print('\n### Set calculator')
project.analysis.show_available_calculators()
project.analysis.set_calculator_by_name('cryspy')
project.analysis.set_calculator_by_name('crysfml')

print('\n### Show data charts')
project.analysis.show_calc_chart("expt_high", x_min=62, x_max=66)
project.analysis.show_meas_vs_calc_chart("expt_high", x_min=62, x_max=66)

project.analysis.show_calc_chart("expt_low", x_min=54, x_max=57)
project.analysis.show_meas_vs_calc_chart("expt_low", x_min=54, x_max=57)

print('\n### Add background points')
project.experiments["expt_high"].background.add(x=11.0, y=206.1624)
project.experiments["expt_high"].background.add(x=15.0, y=194.75)
project.experiments["expt_high"].background.add(x=20.0, y=194.505)
project.experiments["expt_high"].background.add(x=30.0, y=188.4375)
project.experiments["expt_high"].background.add(x=50.0, y=207.7633)
project.experiments["expt_high"].background.add(x=70.0, y=201.7002)
project.experiments["expt_high"].background.add(x=120.0, y=244.4525)
project.experiments["expt_high"].background.add(x=153.0, y=226.0595)

project.experiments["expt_low"].background.add(x=11.0, y=206.1624)
project.experiments["expt_low"].background.add(x=15.0, y=194.75)
project.experiments["expt_low"].background.add(x=20.0, y=194.505)
project.experiments["expt_low"].background.add(x=30.0, y=188.4375)
project.experiments["expt_low"].background.add(x=50.0, y=207.7633)
project.experiments["expt_low"].background.add(x=70.0, y=201.7002)
project.experiments["expt_low"].background.add(x=120.0, y=244.4525)
project.experiments["expt_low"].background.add(x=153.0, y=226.0595)

print('\n### Show data chart including a background')
project.analysis.show_meas_vs_calc_chart("expt_high", x_min=62, x_max=66)

project.analysis.show_meas_vs_calc_chart("expt_low", x_min=54, x_max=57)

print('\n### Show all refinable parameters')
project.analysis.show_refinable_params()

print('\n### Show only free parameters')
project.analysis.show_free_params()

print('\n### Select specific parameters for refinement')
expt_high.linked_phases['pbso4'].scale.value = 1.0
expt_low.linked_phases['pbso4'].scale.value = 1.0

#project.sample_models["pbso4"].cell.length_a.value = 8.4
project.sample_models["pbso4"].cell.length_a.value = 8.5
project.sample_models["pbso4"].cell.length_b.value = 5.35
project.sample_models["pbso4"].cell.length_c.value = 6.9

expt_high.linked_phases['pbso4'].scale.free = True
expt_low.linked_phases['pbso4'].scale.free = True

project.sample_models["pbso4"].cell.length_a.free = True
project.sample_models["pbso4"].cell.length_b.free = True
project.sample_models["pbso4"].cell.length_c.free = True
#project.sample_models["pbso4"].atom_sites["Pb"].fract_x.free = True
#project.experiments["expt_high"].peak_broad.gauss_u.free = True

print('\n### Show free parameters again')
project.analysis.show_free_params()

print('\n### Set refinement strategy')
project.analysis.refinement_strategy = 'single'
#print(project.analysis.describe_refinement_strategy())

print('\n### Start fitting')

project.analysis.show_meas_vs_calc_chart("expt_high", x_min=62, x_max=66)
project.analysis.show_meas_vs_calc_chart("expt_low", x_min=54, x_max=57)

project.analysis.show_available_minimizers()
project.analysis.show_current_minimizer()
#project.analysis.current_minimizer = 'lmfit (least_squares)'
project.analysis.current_minimizer = 'lmfit (leastsq)'


#project.analysis.show_meas_vs_calc_chart("expt_high", x_min=10, x_max=150, show_residual=True, chart_height=30)


project.analysis.fit()


project.analysis.show_meas_vs_calc_chart("expt_high", x_min=62, x_max=66)
project.analysis.show_meas_vs_calc_chart("expt_low", x_min=54, x_max=57)


#project.analysis.show_meas_vs_calc_chart("expt_high", x_min=10, x_max=150, show_residual=True, chart_height=30)

#exit()

print('\n### Change minimizer, and start fitting again')

expt_high.linked_phases['pbso4'].scale.value = 1.0
expt_low.linked_phases['pbso4'].scale.value = 1.0
project.sample_models["pbso4"].cell.length_a.value = 8.5
project.sample_models["pbso4"].cell.length_b.value = 5.35
project.sample_models["pbso4"].cell.length_c.value = 6.9


project.analysis.show_meas_vs_calc_chart("expt_high", x_min=62, x_max=66)
project.analysis.show_meas_vs_calc_chart("expt_low", x_min=54, x_max=57)

project.analysis.current_minimizer = 'dfols'
project.analysis.fit()

project.analysis.show_meas_vs_calc_chart("expt_high", x_min=62, x_max=66)
project.analysis.show_meas_vs_calc_chart("expt_low", x_min=54, x_max=57)


# === Step 5: Summary & Save ===
# Generate final report (HTML or CIF)
#project.summary.show_report()

# Save the final state of the project
#project.save()

#print("Analysis completed successfully!")