"""
Joint Refinement Example (Simplified API)

This example demonstrates the use of the EasyDiffraction API using a simplified,
user-friendly approach that mimics the GUI workflow. It is intended for users
with minimal programming experience who want to learn how to perform joint
fit of crystal structures using diffraction data. The script covers
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
project = ed.Project("joint_fit")

# Define project info
project.info.title = "Joint fit of PbSO4 from neutron and X-ray diffraction"
project.info.description = """This project demonstrates joint fit of neutron 
and X-ray diffraction data, both measured using constant wavelength instruments. 
The objective is to accurately fit the crystal structure of PbSO4."""

# Save the initial project specifying the directory path
#project.save_as("examples/projects/pbso4_joint")
project.save_as("pbso4_joint", temporary=True)

# Show project metadata
project.info.show_as_cif()

########################################################################
# This section covers how to add sample models and modify their
# parameters.
########################################################################

print(ed.chapter('Step 2: Add Sample Model'))

# Add a sample model with default parameters
project.sample_models.add(name="pbso4")

# Show model IDs to be used for accessing the model via project.sample_models["model_id"]
project.sample_models.show_ids()

# Modify sample model parameters via project object
project.sample_models["pbso4"].space_group.name_h_m.value = "P n m a"

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
project.sample_models["pbso4"].show_as_cif()

# Show sample model structure
project.sample_models["pbso4"].show_structure()

# Save the project state after adding sample models
project.save()

########################################################################
# Users will learn how to add experiments, configure their parameters,
# and link them to sample models.
########################################################################

print(ed.chapter('Step 3: Add Experiments (Instrument models and measured data)'))

project.experiments.add(name="npd",
                        sample_form="powder",
                        beam_mode="constant wavelength",
                        radiation_probe="neutron",
                        data_path="examples/data/d1a_pbso4.dat")
project.experiments.add(name="xrd",
                        sample_form="powder",
                        beam_mode="constant wavelength",
                        radiation_probe="xray",
                        data_path="examples/data/lab_pbso4.dat")

print(ed.section('Show defined experiments'))
project.experiments.show_ids()

# Show measured data
project.experiments['npd'].show_meas_chart(x_min=62, x_max=66)
project.experiments['xrd'].show_meas_chart(x_min=26, x_max=28)

# Modify experimental parameters
project.experiments['npd'].instrument.setup_wavelength = 1.91
project.experiments["npd"].instrument.calib_twotheta_offset = -0.1406

project.experiments["npd"].show_supported_peak_profile_types()
project.experiments["npd"].peak_profile_type = "ikeda-carpenter"
project.experiments["npd"].show_current_peak_profile_type()
project.experiments["npd"].peak_profile_type = "split pseudo-voigt"
project.experiments["npd"].peak_profile_type = "pseudo-voigt"
project.experiments["npd"].peak.broad_gauss_u = 0.139
project.experiments["npd"].peak.broad_gauss_v = -0.412
project.experiments["npd"].peak.broad_gauss_w = 0.386
project.experiments["npd"].peak.broad_lorentz_x = 0
project.experiments["npd"].peak.broad_lorentz_y = 0.088

project.experiments['xrd'].instrument.setup_wavelength = 1.540567
project.experiments["xrd"].instrument.calib_twotheta_offset = -0.05181
project.experiments["xrd"].peak.broad_gauss_u = 0.304138
project.experiments["xrd"].peak.broad_gauss_v = -0.112622
project.experiments["xrd"].peak.broad_gauss_w = 0.021272
project.experiments["xrd"].peak.broad_lorentz_x = 0
project.experiments["xrd"].peak.broad_lorentz_y = 0.057691

# Link sample model to experiments
project.experiments['npd'].linked_phases.add(id='pbso4', scale=1.0)
project.experiments['xrd'].linked_phases.add(id='pbso4', scale=0.002)

# Show experiments as CIF
project.experiments["npd"].show_as_cif()
project.experiments["xrd"].show_as_cif()

# Save the project state after adding experiments
project.save()

########################################################################
# This section will guide users through the analysis process, including
# setting up calculators and fitting models.
########################################################################

print(ed.chapter('Step 4: Analysis'))

print(ed.section('Set calculator'))
project.analysis.show_supported_calculators()
project.analysis.show_current_calculator()
project.analysis.current_calculator = 'crysfml'

print(ed.section('Show calculated data'))
project.analysis.show_calc_chart(expt_id="npd", x_min=62, x_max=66)
project.analysis.show_calc_chart(expt_id="xrd", x_min=26, x_max=28)

print(ed.section('Show calculated vs measured data'))
project.analysis.show_meas_vs_calc_chart(expt_id="npd", x_min=62, x_max=66)
project.analysis.show_meas_vs_calc_chart(expt_id="xrd", x_min=26, x_max=28)

# The following background points represent the baseline noise in the diffraction data.
print(ed.section('Add background'))
project.experiments["npd"].background_type = "point"
project.experiments["npd"].show_supported_background_types()
project.experiments["npd"].show_current_background_type()
project.experiments["npd"].background.add(x=11.0, y=206.1624)
project.experiments["npd"].background.add(x=15.0, y=194.75)
project.experiments["npd"].background.add(x=20.0, y=194.505)
project.experiments["npd"].background.add(x=30.0, y=188.4375)
project.experiments["npd"].background.add(x=50.0, y=207.7633)
project.experiments["npd"].background.add(x=70.0, y=201.7002)
project.experiments["npd"].background.add(x=120.0, y=244.4525)
project.experiments["npd"].background.add(x=153.0, y=226.0595)
project.experiments["npd"].background.show()

project.experiments["xrd"].background_type = "chebyshev polynomial"
project.experiments["xrd"].background.add(order=0, coef=119.195)
project.experiments["xrd"].background.add(order=1, coef=6.221)
project.experiments["xrd"].background.add(order=2, coef=-45.725)
project.experiments["xrd"].background.add(order=3, coef=8.119)
project.experiments["xrd"].background.add(order=4, coef=54.552)
project.experiments["xrd"].background.add(order=5, coef=-20.661)
project.experiments["xrd"].background.show()

print(ed.section('Show experiments as CIF. Now the background points are included'))
project.experiments["npd"].show_as_cif()
project.experiments["xrd"].show_as_cif()

print(ed.section('Show data chart including a background'))
project.analysis.show_meas_vs_calc_chart(expt_id="npd", x_min=62, x_max=66)
project.analysis.show_meas_vs_calc_chart(expt_id="xrd", x_min=26, x_max=28)

print(ed.section('Show all fittable parameters'))
project.analysis.show_fittable_params()

# Refinable parameters are those that can be adjusted during fitting,
# while free parameters are currently set to be adjusted.
print(ed.section('Show only free parameters'))
project.analysis.show_free_params()

print(ed.section('Select specific parameters for fitting'))
project.sample_models["pbso4"].cell.length_a.free = True
project.sample_models["pbso4"].cell.length_b.free = True
project.sample_models["pbso4"].cell.length_c.free = True

project.experiments["npd"].linked_phases['pbso4'].scale.free = True
project.experiments["xrd"].linked_phases['pbso4'].scale.free = True

project.analysis.show_free_params()

print(ed.section('Set fit mode'))
project.analysis.show_available_fit_modes()
project.analysis.show_current_fit_mode()
#project.analysis.fit_mode = 'single'

print(ed.section('Set fitting engine'))
project.analysis.show_available_minimizers()
project.analysis.show_current_minimizer()
project.analysis.current_minimizer = 'dfols'

print(ed.section('Start fitting'))
project.analysis.fit()

print(ed.section('Show data charts after fitting'))
project.analysis.show_meas_vs_calc_chart(expt_id="npd", x_min=62, x_max=66)
project.analysis.show_meas_vs_calc_chart(expt_id="xrd", x_min=26, x_max=28)

print(ed.section('Change minimizer'))
project.analysis.show_available_minimizers()
project.analysis.current_minimizer = 'lmfit (leastsq)'

print(ed.section('Start 2nd fitting'))
project.analysis.fit()

print(ed.section('Show data charts after 2nd fitting'))
project.analysis.show_meas_vs_calc_chart(expt_id="npd", x_min=62, x_max=66, show_residual=True)
project.analysis.show_meas_vs_calc_chart(expt_id="xrd", x_min=26, x_max=28, show_residual=True)

print(ed.section('Change calculator'))
project.analysis.show_supported_calculators()
project.analysis.current_calculator = 'cryspy'

print(ed.section('Start 3rd fitting'))
project.analysis.fit()

print(ed.section('Show data charts after 3rd fitting'))
project.analysis.show_meas_vs_calc_chart(expt_id="npd", x_min=62, x_max=66, show_residual=True)
project.analysis.show_meas_vs_calc_chart(expt_id="xrd", x_min=26, x_max=28, show_residual=True)

print(ed.section('Change fit mode'))
project.analysis.show_available_fit_modes()
project.analysis.show_current_fit_mode()
project.analysis.fit_mode = 'joint'

print(ed.section('Change calculator'))
project.analysis.show_supported_calculators()
project.analysis.show_current_calculator()
project.analysis.current_calculator = 'crysfml'

print(ed.section('Start 4th fitting'))
project.analysis.fit()

print(ed.section('Show data charts after 4th fitting'))
project.analysis.show_meas_vs_calc_chart(expt_id="npd", x_min=62, x_max=66, show_residual=True)
project.analysis.show_meas_vs_calc_chart(expt_id="xrd", x_min=26, x_max=28, show_residual=True)

# Show analysis as CIF
project.analysis.show_as_cif()

# Save the project state after analysis
project.save()

########################################################################
# In this final section, users will learn how to review the results and
# save their project state.
########################################################################
print(ed.chapter("Step 5: Summary"))
project.summary.show_report()
