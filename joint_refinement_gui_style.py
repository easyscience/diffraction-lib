"""
Joint Refinement Example (GUI-Style API)

This example demonstrates the use of the EasyDiffraction API using a simplified,
user-friendly approach that mimics the GUI workflow. It is intended for users
with minimal programming experience who want to learn how to perform joint
refinement of crystal structures using diffraction data. The script covers
creating a project, adding sample models and experiments, performing analysis,
and refining parameters.

Only a single import is required (`import easydiffraction as ed`) and all operations
are performed through high-level project components such as `project.sample_models`,
`project.experiments`, and `project.analysis`.
"""

import easydiffraction as ed

########################################################################
# In this section, users will learn how to create a project and define
# its metadata.
########################################################################

print(ed.chapter('Step 1: Create a Project'))

# Create a new project
project = ed.Project(project_id="joint_refinement")

# Define project info
project.info.title = "Joint refinement of PbSO4 from neutron and X-ray diffraction"
project.info.description = """This project demonstrates joint refinement of neutron 
and X-ray diffraction data, both measured using constant wavelength instruments. 
The objective is to accurately refine the crystal structure of PbSO4."""

# Save the initial project specifying the directory path
project.save_as("examples/pbso4_joint")

# Show project metadata
print(ed.paragraph("Project info as cif"))
print(project.info.as_cif())

########################################################################
# This section covers how to add sample models and modify their
# parameters.
########################################################################

print(ed.chapter('Step 2: Add Sample Model'))

# Add a sample model with default parameters
project.sample_models.add(model_id="pbso4")

# Show model IDs to be used for accessing the model via project.sample_models["model_id"]
project.sample_models.show_ids()

# Modify sample model parameters via project object
project.sample_models["pbso4"].space_group.name = "P n m a"

project.sample_models["pbso4"].cell.length_a.value = 8.5
project.sample_models["pbso4"].cell.length_b.value = 5.35
project.sample_models["pbso4"].cell.length_c.value = 6.9

project.sample_models["pbso4"].atom_sites.add(label='Pb',
                                              type_symbol='Pb',
                                              fract_x=0.1876,
                                              fract_y=0.25,
                                              fract_z=0.167,
                                              b_iso=1.3729)
project.sample_models["pbso4"].atom_sites.add(label='S',
                                              type_symbol='S',
                                              fract_x=0.0654,
                                              fract_y=0.25,
                                              fract_z=0.684,
                                              b_iso=0.3777)
project.sample_models["pbso4"].atom_sites.add(label='O1',
                                              type_symbol='O',
                                              fract_x=0.9082,
                                              fract_y=0.25,
                                              fract_z=0.5954,
                                              b_iso=1.9764)
project.sample_models["pbso4"].atom_sites.add(label='O2',
                                              type_symbol='O',
                                              fract_x=0.1935,
                                              fract_y=0.25,
                                              fract_z=0.5432,
                                              b_iso=1.4456)
project.sample_models["pbso4"].atom_sites.add(label='O3',
                                              type_symbol='O',
                                              fract_x=0.0811,
                                              fract_y=0.0272,
                                              fract_z=0.8086,
                                              b_iso=1.2822)

# Show model as CIF string
print(ed.paragraph("Sample model 'pbso4' as cif"))
print(project.sample_models["pbso4"].as_cif())

# Show sample model structure
project.sample_models["pbso4"].show_structure()

# Save the project state after adding sample models
project.save()

########################################################################
# Users will learn how to add experiments, configure their parameters,
# and link them to sample models.
########################################################################

print(ed.chapter('Step 3: Add Experiments (Instrument models and measured data)'))

print(ed.section('Add experiments'))

# Add two experiments
project.experiments.add(id="expt_high",
                        diffr_mode="powder", # "powder" or "single_crystal"
                        expt_mode="constant_wavelength", # "time_of_flight" or "constant_wavelength"
                        radiation_probe="neutron", # "neutron" or "xray"
                        data_path="data/pbso4_powder_neutron_cw_60-100.dat")
project.experiments.add(id="expt_low",
                        diffr_mode="powder", # "powder" or "single_crystal"
                        expt_mode="constant_wavelength", # "time_of_flight" or "constant_wavelength"
                        radiation_probe="xray", # "neutron" or "xray"
                        data_path="data/pbso4_powder_neutron_cw_10-60.dat")

print(ed.section('Show defined experiments'))
project.experiments.show_ids()

# Show measured data
project.experiments['expt_high'].show_meas_chart(x_min=62, x_max=66)
project.experiments['expt_low'].show_meas_chart(x_min=53, x_max=57)

# Modify experiment parameters
project.experiments['expt_high'].instr_setup.wavelength = 1.91
project.experiments["expt_high"].instr_calib.twotheta_offset = -0.1406
project.experiments["expt_high"].peak_broad.gauss_u = 0.139
project.experiments["expt_high"].peak_broad.gauss_v = -0.412
project.experiments["expt_high"].peak_broad.gauss_w = 0.386
project.experiments["expt_high"].peak_broad.lorentz_x = 0
project.experiments["expt_high"].peak_broad.lorentz_y = 0.088

project.experiments['expt_low'].instr_setup.wavelength = 1.91
project.experiments["expt_low"].instr_calib.twotheta_offset = -0.1406
project.experiments["expt_low"].peak_broad.gauss_u = 0.139
project.experiments["expt_low"].peak_broad.gauss_v = -0.412
project.experiments["expt_low"].peak_broad.gauss_w = 0.386
project.experiments["expt_low"].peak_broad.lorentz_x = 0
project.experiments["expt_low"].peak_broad.lorentz_y = 0.088

# Link sample model to experiments
project.experiments['expt_high'].linked_phases.add(id='pbso4', scale=1.0)
project.experiments['expt_low'].linked_phases.add(id='pbso4', scale=1.0)

# Show experiments as CIF
print(ed.paragraph("Experiment 'expt_high' as cif"))
print(project.experiments["expt_high"].as_cif())

print(ed.paragraph("Experiment 'expt_low' as cif"))
print(project.experiments["expt_low"].as_cif())

# Save the project state after adding experiments
project.save()

########################################################################
# This section will guide users through the analysis process, including
# setting up calculators and fitting models.
########################################################################

print(ed.chapter('Step 4: Analysis'))

print(ed.section('Set calculator'))
project.analysis.show_available_calculators()
project.analysis.show_current_calculator()
project.analysis.current_calculator = 'crysfml'

print(ed.section('Show calculated data'))
project.analysis.show_calc_chart("expt_high", x_min=62, x_max=66)
project.analysis.show_calc_chart("expt_low", x_min=53, x_max=57)

print(ed.section('Show calculated vs measured data'))
project.analysis.show_meas_vs_calc_chart("expt_high", x_min=62, x_max=66)
project.analysis.show_meas_vs_calc_chart("expt_low", x_min=53, x_max=57)

# The following background points represent the baseline noise in the diffraction data.
print(ed.section('Add background'))
project.experiments["expt_high"].background.add(x=11.0, y=206.1624)
project.experiments["expt_high"].background.add(x=15.0, y=194.75)
project.experiments["expt_high"].background.add(x=20.0, y=194.505)
project.experiments["expt_high"].background.add(x=30.0, y=188.4375)
project.experiments["expt_high"].background.add(x=50.0, y=207.7633)
project.experiments["expt_high"].background.add(x=70.0, y=201.7002)
project.experiments["expt_high"].background.add(x=120.0, y=244.4525)
project.experiments["expt_high"].background.add(x=153.0, y=226.0595)
project.experiments["expt_high"].background.show()

project.experiments["expt_low"].background.add(x=11.0, y=206.1624)
project.experiments["expt_low"].background.add(x=15.0, y=194.75)
project.experiments["expt_low"].background.add(x=20.0, y=194.505)
project.experiments["expt_low"].background.add(x=30.0, y=188.4375)
project.experiments["expt_low"].background.add(x=50.0, y=207.7633)
project.experiments["expt_low"].background.add(x=70.0, y=201.7002)
project.experiments["expt_low"].background.add(x=120.0, y=244.4525)
project.experiments["expt_low"].background.add(x=153.0, y=226.0595)
project.experiments["expt_low"].background.show()

print(ed.section('Show data chart including a background'))
project.analysis.show_meas_vs_calc_chart("expt_high", x_min=62, x_max=66)
project.analysis.show_meas_vs_calc_chart("expt_low", x_min=53, x_max=57)

print(ed.section('Show all refinable parameters'))
project.analysis.show_refinable_params()

# Refinable parameters are those that can be adjusted during refinement,
# while free parameters are currently set to be adjusted.
print(ed.section('Show only free parameters'))
project.analysis.show_free_params()

print(ed.section('Select specific parameters for refinement'))
project.sample_models["pbso4"].cell.length_a.free = True
project.sample_models["pbso4"].cell.length_b.free = True
project.sample_models["pbso4"].cell.length_c.free = True

project.experiments["expt_high"].linked_phases['pbso4'].scale.free = True
project.experiments["expt_low"].linked_phases['pbso4'].scale.free = True

project.analysis.show_free_params()

print(ed.section('Set refinement strategy'))
project.analysis.show_available_refinement_strategies()
project.analysis.show_current_refinement_strategy()
project.analysis.refinement_strategy = 'combined'

print(ed.section('Set fitting engine'))
project.analysis.show_available_minimizers()
project.analysis.show_current_minimizer()
project.analysis.current_minimizer = 'dfols'

print(ed.section('Start fitting'))
project.analysis.fit()

print(ed.section('Show data charts after fitting'))
project.analysis.show_meas_vs_calc_chart("expt_high", x_min=62, x_max=66)
project.analysis.show_meas_vs_calc_chart("expt_low", x_min=53, x_max=57)

print(ed.section('Change minimizer'))
project.analysis.show_available_minimizers()
project.analysis.current_minimizer = 'lmfit (leastsq)'

print(ed.section('Start 2nd fitting'))
project.analysis.fit()

print(ed.section('Show data charts after 2nd fitting'))
project.analysis.show_meas_vs_calc_chart("expt_high", x_min=62, x_max=66)
project.analysis.show_meas_vs_calc_chart("expt_low", x_min=53, x_max=57)

print(ed.section('Change calculator'))
project.analysis.show_available_calculators()
project.analysis.current_calculator = 'cryspy'

print(ed.section('Start 3rd fitting'))
project.analysis.fit()

print(ed.section('Show data charts after 3rd fitting'))
project.analysis.show_meas_vs_calc_chart("expt_high", x_min=62, x_max=66, show_residual=True)
project.analysis.show_meas_vs_calc_chart("expt_low", x_min=53, x_max=57, show_residual=True)

# Save the project state after analysis
project.save()

########################################################################
# In this final section, users will learn how to review the results and
# save their project state.
########################################################################
print(ed.chapter("Step 5: Summary"))
project.summary.show_report()
