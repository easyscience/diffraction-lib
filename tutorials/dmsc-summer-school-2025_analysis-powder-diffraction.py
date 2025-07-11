# %% [markdown]
# # Data Analysis: Powder Diffraction
#
# This tutorial guides you through the refinement of simulated diffraction
# patterns for Si (Part 1) and La₀.₅Ba₀.₅CoO₃ (LBCO) (Part 2) using the
# EasyDiffraction Python library.
#
# The goal is to develop familiarity with the Rietveld refinement process
# for crystal structures using powder diffraction data.
#
# ## 🛠️ Import Library
#
# Start by importing the necessary library for the analysis. In this tutorial, we
# use the EasyDiffraction library, which offers tools for
# analyzing and refining powder diffraction data.
#
# This tutorial is self-contained and designed for hands-on learning.
# However, if you're interested in exploring more advanced features or learning
# about additional capabilities of the EasyDiffraction library, please refer to
# the official documentation: https://easyscience.github.io/diffraction-lib
#
# Depending on your requirements, you may choose to import only specific
# classes. However, for the sake of simplicity in this tutorial, we will import
# the entire library.

# %%
# TODO: Remove this cell in the final version of the tutorial.
# Needed for the Google Colab environment.
# Install the easydiffraction library if it is not already installed.
import builtins
import importlib.util

if hasattr(builtins, "__IPYTHON__"):
    if importlib.util.find_spec('easydiffraction') is None:
        print('Installing the easydiffraction library...')
        # !pip install git+https://github.com/easyscience/diffraction-lib@d-spacing

# %%
import easydiffraction as ed

# %% [markdown]
# ## 📘 Introduction: Simple Reference Fit – Si
#
# Before diving into the more complex fitting exercise with the La₀.₅Ba₀.₅CoO₃
# (LBCO) crystal structure, let's start with a simpler example using the
# silicon (Si) crystal structure. This will help us understand the basic
# concepts and steps involved in fitting a crystal structure using powder
# diffraction data.
#
# For this part of the tutorial, we will use the powder diffraction data
# from the [previous tutorial](#), simulated using the Si crystal structure.
#
# ### 📦 Create a Project – 'reference'
#
# In EasyDiffraction, a project serves as a container for all information
# related to the analysis of a specific experiment or set of experiments. It
# enables you to organize your data, experiments, sample models, and fitting
# parameters in a structured manner. You can think of it as a folder containing
# all the essential details about your analysis. The project also allows
# us to visualize both the measured and calculated diffraction patterns, among
# other things.

# %%
project_1 = ed.Project(name='reference')

# %% [markdown]

# You can set the title and description of the project to provide context
# and information about the analysis being performed. This is useful for
# documentation purposes and helps others (or yourself in the future) understand
# the purpose of the project at a glance.

# %%
project_1.info.title = 'Reference Silicon Fit'
project_1.info.description = 'Fitting simulated powder diffraction pattern of Si.'

# %% [markdown]
# ### 🔬 Create an Experiment
#
# Now we will create an experiment within the project. An experiment
# represents a specific diffraction measurement performed on a specific sample
# using a particular instrument. It contains
# details about the measured data, instrument parameters, and other relevant
# information.
#
# In this case, the experiment is defined as a powder diffraction measurement
# using time-of-flight neutrons. The measured data is loaded from a file
# containing the reduced diffraction pattern of Si from the previous
# tutorial.

# %%
# TODO: Remove this cell in the final version of the tutorial.
# Google Colab does not have the data files needed for this tutorial.
ed.download_from_repository('powder_reduced_Si_2large_bank.xye',
                            branch='d-spacing',
                            destination='data')

# %%
project_1.experiments.add(name='sim_si',
                          sample_form='powder',
                          beam_mode='time-of-flight',
                          radiation_probe='neutron',
                          data_path='data/powder_reduced_Si_2large_bank.xye')

# %% [markdown]
# #### Inspect Measured Data
#
# After creating the experiment, we can examine the measured data. The measured
# data consists of a diffraction pattern having time-of-flight (TOF) values
# and corresponding intensities. The TOF values are given in microseconds (μs),
# and the intensities are in arbitrary units.
#
# The data is stored in XYE format, a simple text format containing three
# columns: TOF, intensity, and intensity error (if available).
#
# The `plot_meas` method of the project enables us to visualize the measured
# diffraction pattern.
#
# Before plotting, we set the plotting engine to 'plotly', which provides
# interactive visualizations.

# %%
project_1.plotter.engine = 'plotly'

# %%
project_1.plot_meas(expt_name='sim_si')

# %% [markdown]
# If you zoom in on the highest TOF peak (around 120,000 μs), you will notice
# that it has a broad and unusual shape. This is a result of the simplified
# data reduction process. Obtaining a more accurate diffraction pattern would
# require a more advanced data reduction, which is beyond the scope of this
# tutorial. Therefore, we will simply exclude the high TOF region from the analysis by
# adding an excluded region to the experiment.

# %%
project_1.experiments['sim_si'].excluded_regions.add(minimum=108000, maximum=200000)

# %% [markdown]
# To visualize the effect of excluding the high TOF region, we can plot
# the measured data again. The excluded region will be omitted from the plot
# and is not used in the fitting process.

# %%
project_1.plot_meas(expt_name='sim_si')

# %% [markdown]
# #### Set Instrument Parameters
#
# After experiment is created and measured data are loaded, we would need
# to set the instrument parameters.
#
# In this type of experiment, the instrument parameters define how the
# measured data is converted between d-spacing and time-of-flight (TOF)
# during the data reduction process as well as the angular position of the
# detector. So, we put values based on those from the reduction.

# %%
project_1.experiments['sim_si'].instrument.setup_twotheta_bank = 101.46
project_1.experiments['sim_si'].instrument.calib_d_to_tof_linear = 61710.64
project_1.experiments['sim_si'].instrument.calib_d_to_tof_quad = -0.00001

# %% [markdown]
# #### Set Peak Profile Parameters
#
# The next set of parameters is needed to define the peak profile used in the
# fitting process. The peak profile describes shape of the diffraction peaks.
# They include parameters for the broadening and asymmetry of the peaks. Here,
# we use a pseudo-Voigt peak profile function with Ikeda-Carpenter asymmetry, which is a common
# choice for neutron powder diffraction data. The values are typically determined
# experimentally on the same instrument and under the same configuration as the
# data being analyzed based on measurements of a standard
# sample. In some cases, these parameters are refined during the fitting
# process to improve the fit between the measured and calculated diffraction, but
# in this case, we will use the values from another simulation.

# %%
project_1.experiments['sim_si'].peak_profile_type = 'pseudo-voigt * ikeda-carpenter'
project_1.experiments['sim_si'].peak.broad_gauss_sigma_0 = 47347.42
project_1.experiments['sim_si'].peak.broad_gauss_sigma_1 = -55360.02
project_1.experiments['sim_si'].peak.broad_gauss_sigma_2 = 23882.42
project_1.experiments['sim_si'].peak.broad_mix_beta_0 = 0.0055
project_1.experiments['sim_si'].peak.broad_mix_beta_1 = 0.0041
project_1.experiments['sim_si'].peak.asym_alpha_0 = 0
project_1.experiments['sim_si'].peak.asym_alpha_1 = 0.0096


# %% [markdown]
# #### Set Background
#
# The background of the diffraction pattern represents the portion of the pattern that
# is not related to the crystal structure of the sample, but rather to
# incoherent scattering from the sample itself, the sample holder, the sample
# environment, and the instrument. The background can be modeled in various
# ways. In this case, we will use a simple line segment background, which is a
# common approach for powder diffraction data. The background intensity at any
# point is defined by linear interpolation between neighboring points.
# The background points are selected
# to span the range of the diffraction pattern while avoiding the peaks.
#
# In this case, we will add several background points at specific TOF values
# (in microseconds) and corresponding intensity values. These points are
# chosen to represent the background level in the diffraction pattern free from
# any peaks. The background points are added using the `add` method of the
# `background` attribute of the experiment. The `x` parameter represents the TOF
# value, and the `y` parameter represents the intensity value at that TOF.
#
# Let's set all the background points at a constant value of 0.01, which can be
# roughly determined by the eye, and we will refine them later during the fitting
# process.

# %%
project_1.experiments['sim_si'].background_type = 'line-segment'
project_1.experiments['sim_si'].background.add(x=50000, y=0.01)
project_1.experiments['sim_si'].background.add(x=60000, y=0.01)
project_1.experiments['sim_si'].background.add(x=70000, y=0.01)
project_1.experiments['sim_si'].background.add(x=80000, y=0.01)
project_1.experiments['sim_si'].background.add(x=90000, y=0.01)
project_1.experiments['sim_si'].background.add(x=100000, y=0.01)
project_1.experiments['sim_si'].background.add(x=110000, y=0.01)

# %% [markdown]
# ### 🧩 Create a Sample Model – Si
#
# After setting up the experiment, we need to create a sample model that
# describes the crystal structure of the sample being analyzed.
#
# In this case, we will create a sample model for silicon (Si) with a
# cubic crystal structure. The sample model contains information about the
# space group, lattice parameters, atomic positions of the atoms in the
# unit cell, atom types, occupancies and atomic displacement parameters.
# The sample model is essential for the fitting process, as it
# is used to calculate the expected diffraction pattern.
#
# EasyDiffraction refines the crystal structure of the sample,
# but does not solve it. Therefore, we need a good starting point with
# reasonable structural parameters. Here, we define the Si structure as a
# cubic structure with the space group F d -3 m. As this is a simple cubic
# structure, we only need to define the single lattice parameter, which
# is the length of the unit cell edge. The Si crystal structure has a
# single atom in the unit cell, which is located at the origin (0, 0, 0) of
# the unit cell. The symmetry of this site is defined by the Wyckoff letter 'a'.
# The atomic displacement parameter defines the thermal vibrations of the
# atoms in the unit cell and is presented as an isotropic parameter (B_iso).
#
# Sometimes, the initial crystal structure parameters can be obtained
# from one of the crystallographic databases, like for example
# the Crystallography Open Database (COD). In this case, we use the COD
# entry for silicon as a reference for the initial crystal structure model:
# https://www.crystallography.net/cod/4507226.html
#
# As with adding the experiment in the
# previous step, we will create a default sample model
# and then modify its parameters to match the Si structure.
#
# #### Add Sample Model

# %%
project_1.sample_models.add(name='si')

# %% [markdown]
# #### Set Space Group

# %%
project_1.sample_models['si'].space_group.name_h_m = 'F d -3 m'
project_1.sample_models['si'].space_group.it_coordinate_system_code = '2'

# %% [markdown]
# #### Set Lattice Parameters

# %%
project_1.sample_models['si'].cell.length_a = 5.43

# %% [markdown]
# #### Set Atom Sites

# %%
project_1.sample_models['si'].atom_sites.add(label='Si',
                                             type_symbol='Si',
                                             fract_x=0,
                                             fract_y=0,
                                             fract_z=0,
                                             wyckoff_letter='a',
                                             b_iso=0.95)

# %% [markdown]
# ### 🔗 Assign Sample Model to Experiment
#
# Now we need to assign, or link, this sample model to the experiment created above.
# This linked crystallographic phase will be used to calculate the expected diffraction
# pattern based on the crystal structure defined in the sample model.

# %%
project_1.experiments['sim_si'].linked_phases.add(id='si', scale=1.0)

# %% [markdown]
# ### 🚀 Analyze and Fit the Data
#
# After setting up the experiment and sample model, we can now analyze the
# measured diffraction pattern and perform the fitting process.
#
# The fitting process involves comparing the measured diffraction pattern with
# the calculated diffraction pattern based on the sample model and instrument
# parameters. The goal is to adjust the parameters of the sample model and
# the experiment to minimize the difference between the measured and calculated
# diffraction patterns. This is done by refining the parameters of the sample
# model and the instrument settings to achieve a better fit.
#
# #### Set Fit Parameters
#
# To perform the fit, we need to specify the refinement parameters. These
# are the parameters that will be adjusted during the fitting process to
# minimize the difference between the measured and calculated diffraction
# patterns. In this case, we will refine only the scale factor of the Si phase
# in the experiment, as well as the intensities of the background points.
# This is done by setting
# the `free` attribute of the corresponding parameters to `True`.

# %%
project_1.experiments['sim_si'].linked_phases['si'].scale.free = True
for line_segment in project_1.experiments['sim_si'].background:
    line_segment.y.free = True

# %% [markdown]
# #### Show Free Parameters
#
# We can check which parameters are free to be refined by calling the
# `show_free_params` method of the `analysis` object of the project.

# %%
project_1.analysis.show_free_params()

# %% [markdown]
# #### Visualize Diffraction Patterns
#
# Before performing the fit, we can visually compare the measured
# diffraction pattern with the calculated diffraction pattern based on the
# initial parameters of the sample model and the instrument settings.
# This provides an indication of how well the initial parameters
# match the measured data. The `plot_meas_vs_calc` method of the project
# allows this comparison.

# %%
project_1.plot_meas_vs_calc(expt_name='sim_si')

# %% [markdown]
# #### Run Fitting
#
# We can now perform the fit using the `fit` method of the `analysis`
# object of the project.

# %%
project_1.analysis.fit()

# %% [markdown]
# #### Check Fit Results
# You will
# see that the fit is now much improved and that the intensities of the
# calculated peaks align much better with the measured peaks. To check the
# quality of the fit numerically, we can look at the goodness-of-fit
# chi-squared value and the R-factors. The chi-squared value is a measure of how well
# the calculated diffraction pattern matches the measured pattern, and it is
# calculated as the sum of the squared differences between the measured and
# calculated intensities, divided by the number of data points. Ideally, the
# chi-squared value should be close to 1, indicating a good fit.

# %% [markdown]
# #### Visualize Fit Results
#
# After the fit is completed, we can plot the comparison between the
# measured and calculated diffraction patterns again to see how well the fit
# improved the agreement between the two. The calculated diffraction pattern
# is now based on the refined parameters.

# %%
project_1.plot_meas_vs_calc(expt_name='sim_si')

# %% [markdown]
# #### TOF vs d-spacing
#
# The diffraction pattern is typically analyzed and plotted in the
# time-of-flight (TOF) axis, which represents the time it takes for neutrons
# to travel from the sample to the detector. However, it is sometimes more
# convenient to visualize the diffraction pattern in the d-spacing axis,
# which represents the distance between planes in the crystal lattice. The
# d-spacing can be calculated from the TOF values using the instrument
# parameters. The `plot_meas_vs_calc` method of the project allows us to
# plot the measured and calculated diffraction patterns in the d-spacing axis
# by setting the `d_spacing` parameter to `True`.

# %%
project_1.plot_meas_vs_calc(expt_name='sim_si', d_spacing=True)

# %% [markdown]
# As you can see, the calculated diffraction pattern now matches the measured
# pattern much more closely. Typically, additional parameters are included in the
# refinement process to further improve the fit. However, we will stop here,
# as the goal of this part of the tutorial is to demonstrate that the data reduction
# and fitting process function correctly. The fit is not perfect, but it is
# sufficient to show that the fitting process works and that the parameters
# are being adjusted appropriately. The next part of the tutorial will be more advanced
# and will involve fitting a more complex crystal structure: La₀.₅Ba₀.₅CoO₃ (LBCO).
#
# ## 💪 Exercise: Complex Fit – LBCO
#
# Now that you have a basic understanding of the fitting process, we will
# undertake a more complex fit of the La₀.₅Ba₀.₅CoO₃ (LBCO) crystal structure
# using simulated powder diffraction data from the [previous tutorial](#).
#
# You can use the same approach as in the previous part of the tutorial, but
# this time we will refine a more complex crystal structure LBCO with multiple atoms
# in the unit cell.
#
# ### 📦 Exercise 1: Create a Project – 'main'
#
# Create a new project for the LBCO fit.
#
# **Hint:** You can use the same approach as in the previous part of the
# tutorial, but this time we will create a new project for the LBCO fit.
#
# **Solution:**

# %%
project_2 = ed.Project(name='main')
project_2.info.title = 'La0.5Ba0.5CoO3 Fit'
project_2.info.description = 'Fitting simulated powder diffraction pattern of La0.5Ba0.5CoO3.'

# %% [markdown]
# ### 🔬 Exercise 2: Define an Experiment
#
# #### Exercise 2.1: Create an Experiment
#
# Create an experiment within the new project and load the reduced diffraction
# pattern for LBCO.
#
# **Hint:** You can use the same approach as in the previous part of the
# tutorial, but this time you need to use the data file for LBCO.
#
# **Solution:**

# %%
# TODO: Remove this cell in the final version of the tutorial.
# Google Colab does not have the data files needed for this tutorial.
ed.download_from_repository('powder_reduced_lbco_0_05si_2large_bank.xye',
                            branch='d-spacing',
                            destination='data')

# %%
project_2.experiments.add(name='sim_lbco',
                             sample_form='powder',
                             beam_mode='time-of-flight',
                             radiation_probe='neutron',
                             data_path='data/powder_reduced_lbco_0_05si_2large_bank.xye')

# %% [markdown]
# #### Exercise 2.1: Inspect Measured Data
#
# Check the measured data of the LBCO experiment. Are there any
# peaks with the shape similar to the Si peaks? If so, exclude them from the
# analysis.
#
# **Hint:** You can use the `plot_meas` method of the project to visualize the
# measured diffraction pattern. You can also use the `excluded_regions` attribute
# of the experiment to exclude specific regions from the analysis.
#
# **Solution:**

# %%
project_2.plotter.engine = 'plotly'
project_2.plot_meas(expt_name='sim_lbco')

# %%
project_2.experiments['sim_lbco'].excluded_regions.add(minimum=108000, maximum=200000)

# %%
project_2.plot_meas(expt_name='sim_lbco')

# %% [markdown]
# #### Exercise 2.2: Set Instrument Parameters
#
# Set the instrument parameters for the LBCO experiment.
#
# **Hint:** Use the values from the data reduction process for the LBCO and
# follow the same approach as in the previous part of the tutorial.
#
# **Solution:**

# %%
project_2.experiments['sim_lbco'].instrument.setup_twotheta_bank = 94.91
project_2.experiments['sim_lbco'].instrument.calib_d_to_tof_linear = 58752.56
project_2.experiments['sim_lbco'].instrument.calib_d_to_tof_quad = -0.00001

# %% [markdown]
# #### Exercise 2.3: Set Peak Profile Parameters
#
# Set the peak profile parameters for the LBCO experiment.
#
# **Hint:** Use the values from the previous part of the tutorial.
#
# **Solution:**

# %%
project_2.peak_profile_type = 'pseudo-voigt * ikeda-carpenter'
project_2.experiments['sim_lbco'].peak.broad_gauss_sigma_0 = 47347.42
project_2.experiments['sim_lbco'].peak.broad_gauss_sigma_1 = -55360.02
project_2.experiments['sim_lbco'].peak.broad_gauss_sigma_2 = 23882.42
project_2.experiments['sim_lbco'].peak.broad_mix_beta_0 = 0.0055
project_2.experiments['sim_lbco'].peak.broad_mix_beta_1 = 0.0041
project_2.experiments['sim_lbco'].peak.asym_alpha_0 = 0
project_2.experiments['sim_lbco'].peak.asym_alpha_1 = 0.0096

# %% [markdown]
# #### Exercise 2.4: Set Background
#
# Set the background points for the LBCO experiment. What would you suggest as
# the initial intensity value for the background points?
#
# **Hint:** Use the same approach as in the previous part of the tutorial, but
# this time you need to set the background points for the LBCO experiment. You can
# zoom in on the measured diffraction pattern to determine the approximate
# background level.
#
# **Solution:**

# %%
project_2.experiments['sim_lbco'].background_type = 'line-segment'
project_2.experiments['sim_lbco'].background.add(x=50000, y=0.2)
project_2.experiments['sim_lbco'].background.add(x=60000, y=0.2)
project_2.experiments['sim_lbco'].background.add(x=70000, y=0.2)
project_2.experiments['sim_lbco'].background.add(x=80000, y=0.2)
project_2.experiments['sim_lbco'].background.add(x=90000, y=0.2)
project_2.experiments['sim_lbco'].background.add(x=100000, y=0.2)
project_2.experiments['sim_lbco'].background.add(x=110000, y=0.2)

# %% [markdown]
# ### 🧩 Exercise 3: Define a Sample Model – LBCO
#
# The LBSO structure is not as simple as the Si model, as it contains multiple
# atoms in the unit cell. It is not in COD, so we give you the structural
# parameters in CIF format to create the sample model right here:

# %% [markdown]
# ```
# data_lbco
#
# _space_group.name_H-M_alt  "P m -3 m"
# _space_group.IT_coordinate_system_code  1
#
# _cell.length_a      3.89
# _cell.length_b      3.89
# _cell.length_c      3.89
# _cell.angle_alpha  90.0
# _cell.angle_beta   90.0
# _cell.angle_gamma  90.0
#
# loop_
# _atom_site.label
# _atom_site.type_symbol
# _atom_site.fract_x
# _atom_site.fract_y
# _atom_site.fract_z
# _atom_site.wyckoff_letter
# _atom_site.occupancy
# _atom_site.ADP_type
# _atom_site.B_iso_or_equiv
# La La   0.0 0.0 0.0   a   0.5   Biso 0.10
# Ba Ba   0.0 0.0 0.0   a   0.5   Biso 0.10
# Co Co   0.5 0.5 0.5   b   1.0   Biso 0.36
# O  O    0.0 0.5 0.5   c   1.0   Biso 2.14
# ```

# %% [markdown]
# #### Exercise 3.1: Create Sample Model
#
# Create a sample model for LBCO based on the provided CIF data.
#
# **Hint:** You can use the same approach as in the previous part of the
# tutorial, but this time you need to create a sample model for LBCO.
#
# **Solution:**

# %%
project_2.sample_models.add(name='lbco')

# %% [markdown]
# #### Exercise 3.2: Set Space Group
#
# Set the space group for the LBCO sample model.
#
# **Hint:** Use the space group name and IT coordinate system code from the CIF data.
#
# **Solution:**

# %%
project_2.sample_models['lbco'].space_group.name_h_m = 'P m -3 m'
project_2.sample_models['lbco'].space_group.it_coordinate_system_code = '1'

# %% [markdown]
# #### Exercise 3.3: Set Lattice Parameters
#
# Set the lattice parameters for the LBCO sample model.
#
# **Hint:** Use the lattice parameters from the CIF data.
#
# **Solution:**

# %%
project_2.sample_models['lbco'].cell.length_a = 3.88

# %% [markdown]
# #### Exercise 3.4: Set Atom Sites
#
# Set the atom sites for the LBCO sample model.
#
# **Hint:** Use the atom sites from the CIF data. You can use the `add` method of
# the `atom_sites` attribute of the sample model to add the atom sites.
# Note that the `occupancy` of the La and Ba atoms is 0.5 and those atoms
# are located in the same position (0, 0, 0) in the unit cell. This means that
# an extra attribute `occupancy` needs to be set for those atoms.

# %%
project_2.sample_models['lbco'].atom_sites.add(label='La',
                                               type_symbol='La',
                                               fract_x=0,
                                               fract_y=0,
                                               fract_z=0,
                                               wyckoff_letter='a',
                                               b_iso=0.1,
                                               occupancy=0.5)
project_2.sample_models['lbco'].atom_sites.add(label='Ba',
                                               type_symbol='Ba',
                                               fract_x=0,
                                               fract_y=0,
                                               fract_z=0,
                                               wyckoff_letter='a',
                                               b_iso=0.1,
                                               occupancy=0.5)
project_2.sample_models['lbco'].atom_sites.add(label='Co',
                                               type_symbol='Co',
                                               fract_x=0.5,
                                               fract_y=0.5,
                                               fract_z=0.5,
                                               wyckoff_letter='b',
                                               b_iso=0.36)
project_2.sample_models['lbco'].atom_sites.add(label='O',
                                               type_symbol='O',
                                               fract_x=0,
                                               fract_y=0.5,
                                               fract_z=0.5,
                                               wyckoff_letter='c',
                                               b_iso=2.14)

# %% [markdown]
# ### 🔗 Exercise 4: Assign Sample Model to Experiment
#
# Now assign the LBCO sample model to the LBCO experiment created above.
#
# **Hint:** Use the `linked_phases` attribute of the experiment to link the sample model.
#
# **Solution:**

# %%
project_2.experiments['sim_lbco'].linked_phases.add(id='lbco', scale=1.0)

# %% [markdown]
# ### 🚀 Exercise 5: Analyze and Fit the Data
#
# #### Exercise 5.1: Set Fit Parameters
#
# Select the parameters to be refined during the fitting process.
#
# **Hint:** You can start with the same parameters as in the Si fit, but
# this time you will refine the scale factor of the LBCO phase and the
# background points for the second simulation.
#
# **Solution:**

# %%
project_2.experiments['sim_lbco'].linked_phases['lbco'].scale.free = True
for line_segment in project_2.experiments['sim_lbco'].background:
    line_segment.y.free = True

# %% [markdown]
# #### Exercise 5.2: Run Fitting
#
# Visualize the measured and calculated diffraction patterns before fitting and
# then run the fitting process.
#
# **Hint:** Use the `plot_meas_vs_calc` method of the project to visualize the
# measured and calculated diffraction patterns before fitting. Then, use the
# `fit` method of the `analysis` object of the project to perform the fitting
# process.
#
# **Solution:**

# %%
project_2.plot_meas_vs_calc(expt_name='sim_lbco')

# %%
project_2.analysis.fit()

# %% [markdown]
# #### Exercise 5.3: Find the Misfit in the Fit
#
# Visualize the measured and calculated diffraction patterns after the fit. As
# you can see, the fit shows noticeable discrepancies. If you zoom in on different regions of the pattern,
# you will observe that all the calculated peaks are shifted to the left.
#
# What could be the reason for the misfit?
#
# **Hint**: Consider the following options:
# - The conversion parameters from TOF to d-spacing are not correct.
# - The lattice parameters of the LBCO phase are not correct.
# - The peak profile parameters are not correct.
# - The background points are not correct.
#
# **Solution**:
# - ❌ The conversion parameters from TOF to d-spacing were set based on the data reduction process and this was verified in
# the Si fit.
# - ✅ The lattice parameters of the LBCO phase were set based on the CIF data, which is a good starting point.
# - ❌ The peak profile parameters do not change the position of the peaks, but rather their shape.
# - ❌ The background points affect the background level, but not the peak positions.

# %%
project_2.plot_meas_vs_calc(expt_name='sim_lbco')

# %% [markdown]
# #### Exercise 5.4: Refine the LBCO Lattice Parameter
#
# To improve the fit, refine the lattice parameter of the LBCO phase.
#
# **Hint**: To accomplish this, we will set the `free` attribute of the `length_a` parameter
# of the LBCO cell to `True`. This will allow the fitting process to adjust
# the lattice parameter in addition to the scale factor of the LBCO phase
# and the background points. Then, you can run the fitting process again.
#
# **Solution**:

# %%
project_2.sample_models['lbco'].cell.length_a.free = True

# %%
project_2.analysis.fit()

# %%
project_2.plot_meas_vs_calc(expt_name='sim_lbco')

# %% [markdown]
# #### Exercise 5.5: Visualize the Fit Results in d-spacing
#
# Plot measured vs calculated diffraction patterns in d-spacing instead of TOF.
#
# **Hint**: Use the `plot_meas_vs_calc` method of the project and set the
# `d_spacing` parameter to `True`.
#
# **Solution**:

# %%
project_2.plot_meas_vs_calc(expt_name='sim_lbco', d_spacing=True)

# %% [markdown]
# #### Exercise 5.6: Find Undefined Features
#
# After refining the lattice parameter, the fit is significantly improved, but
# inspect the diffraction pattern again. Are you noticing anything undefined?
#
# **Hint**: While the fit is now significantly better, there are still some unexplained peaks
# in the diffraction pattern. These peaks are not accounted for by the LBCO phase.
# For example, if you zoom in on the region around 1.6 Å (or 95,000 μs), you will
# notice that the rightmost peak is not explained by the LBCO phase at all.
#
# Solution:

# %%
project_2.plot_meas_vs_calc(expt_name='sim_lbco', x_min=1.53, x_max=1.7, d_spacing=True)

# %% [markdown]
# #### Exercise 5.7: Identify the Cause of the Unexplained Peaks
#
# **Hint**: Consider the following options:
# - The LBCO phase is not correctly modeled.
# - The LBCO phase is not the only phase present in the sample.
# - The data reduction process introduced artifacts.
#
# **Solution**:
# - ❌ In principle, this could be the case, but in this case, the LBCO phase is correctly modeled.
# - ✅ The LBCO phase is not the only phase present in the sample. The unexplained peaks
# are likely due to the presence of an impurity phase in the sample, which is not
# included in the current model.
# - ❌ The data reduction process is not likely to introduce such specific peaks, as it is
# tested and verified in the previous part of the tutorial.

# %% [markdown]
# #### Exercise 5.8: Identify the impurity phase
#
# Identify the impurity phase.
#
# **Hint**: Check the positions of the unexplained peaks in the diffraction pattern.
# Compare them with the known diffraction patterns in the introduction section of the
# tutorial.
#
# **Solution**:
# The unexplained peaks are likely due to the presence of silicon (Si) in the sample.
# You can visalize both the patterns of the Si and LBCO phases to confirm this hypothesis.

# %%
project_1.plot_meas_vs_calc(expt_name='sim_si', x_min=1, x_max=1.7, d_spacing=True)
project_2.plot_meas_vs_calc(expt_name='sim_lbco', x_min=1, x_max=1.7, d_spacing=True)

# %% [markdown]
# #### Exercise 5.9: Create a Second Sample Model – Si as Impurity
#
# Create a second sample model for the Si phase, which is the impurity phase
# identified in the previous step. Link this sample model to the LBCO
# experiment.
#
# **Hint**: You can use the same approach as in the previous part of the
# tutorial, but this time you need to create a sample model for Si and link it
# to the LBCO experiment.
#
# **Solution:**

# %% [markdown]
# **Set Space Group**

# %%
project_2.sample_models.add(name='si')

# %%
project_2.sample_models['si'].space_group.name_h_m = 'F d -3 m'
project_2.sample_models['si'].space_group.it_coordinate_system_code = '2'

# %% [markdown]
# **Set Lattice Parameters**

# %%
project_2.sample_models['si'].cell.length_a = 5.43

# %% [markdown]
# **Set Atom Sites**

# %%
project_2.sample_models['si'].atom_sites.add(label='Si',
                                             type_symbol='Si',
                                             fract_x=0,
                                             fract_y=0,
                                             fract_z=0,
                                             wyckoff_letter='a',
                                             b_iso=0.95)

# %% [markdown]
# **🔗 Assign Sample Model to Experiment**

# %%
project_2.experiments['sim_lbco'].linked_phases.add(id='si', scale=1.0)

# %% [markdown]
# #### Exercise 5.10: Refine the Scale of the Si Phase
#
# Visualize the measured diffraction pattern and the calculated diffraction
# pattern. Check if the Si phase is contributing to the calculated diffraction
# pattern. Refine the scale factor of the Si phase to improve the fit.
#
# **Hint**: You can use the `plot_meas_vs_calc` method of the project to
# visualize the patterns. Then, set the `free` attribute of the `scale`
# parameter of the Si phase to `True` to allow the fitting process to adjust
# the scale factor.
#
# **Solution:**
#
# Before optimizing the parameters, we can visualize the measured
# diffraction pattern and the calculated diffraction pattern based on the
# two phases: LBCO and Si.
#
# **Visualize Diffraction Patterns**

# %%
project_2.plot_meas_vs_calc(expt_name='sim_lbco')

# %% [markdown]
# As you can see, the calculated pattern is now the sum of both phases,
# and Si peaks are visible in the calculated pattern. However, their intensities
# are much too high. Therefore, we need to refine the scale factor of the Si phase.
#
# **Set Fit Parameters**

# %%
project_2.experiments['sim_lbco'].linked_phases['si'].scale.free = True

# %% [markdown]
# **Run Fitting**
#
# Now we can perform the fit with both phases included.

# %%
project_2.analysis.fit()

# %% [markdown]
# **Visualize Fit Results**

# Let's plot the measured diffraction pattern and the calculated diffraction
# pattern both for the full range and for a zoomed-in region around the previously unexplained
# peak near 90,000 μs. The calculated pattern will be the sum of the two phases.

# %%
project_2.plot_meas_vs_calc(expt_name='sim_lbco')

# %%
project_2.plot_meas_vs_calc(expt_name='sim_lbco', x_min=85000, x_max=105000)

# %% [markdown]
# All previously unexplained peaks are now accounted for in the pattern, and the fit is improved.
# Some discrepancies in the peak intensities remain, but
# further improvements would require more advanced data reduction and analysis,
# which are beyond the scope of this tutorial.

# %% [markdown]
# ## 📑 Summary
#
# In this tutorial, you refined two simulated diffraction patterns:
# - **Si** as a simple reference system, and
# - **LBCO** as a more complex, realistic case with an initially unknown impurity.
#
# Along the way, you learned how to:
# - Define a project, experiment, and sample model in EasyDiffraction
# - Set up instrument and peak profile parameters
# - Visualize measured and calculated patterns
# - Identify and interpret misfits in the diffraction data
# - Add and refine multiple phases to improve the model
#
# Key Takeaways:
# - A good refinement starts with a reasonable structural model and
#   well-defined instrument parameters.
# - Visual inspection is a critical part of model validation. Residual peaks
#   often reveal missing physics or contamination.

# %% [markdown]
# ## 🎁 Bonus
#
# You've now completed the analysis part of the Summer School workflow,
# demonstrating the practical use of EasyDiffraction for refining simulated
# powder diffraction data.
#
# To continue learning and exploring more features of
# the EasyDiffraction library, you can visit the official tutorial page
# and select one of the many available tutorials:
# https://easyscience.github.io/diffraction-lib/tutorials/
