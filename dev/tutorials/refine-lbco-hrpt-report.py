# %% [markdown]
# # Structure Refinement: LBCO, HRPT
#
# This example demonstrates how to use the EasyDiffraction API in a
# simplified, user-friendly manner that closely follows the GUI workflow
# for a Rietveld refinement of La0.5Ba0.5CoO3 crystal structure using
# constant wavelength neutron powder diffraction data from HRPT at PSI.
#
# It is intended for users with minimal programming experience who want
# to learn how to perform standard crystal structure fitting using
# diffraction data. This script covers creating a project, adding
# crystal structures and experiments, performing analysis, and refining
# parameters.
#
# Only a single import of `easydiffraction` is required, and all
# operations are performed through high-level components of the
# `project` object, such as `project.structures`,
# `project.experiments`, and `project.analysis`. The `project` object is
# the main container for all information.

# %% [markdown]
# ## 🛠️ Import Library

# %%
import easydiffraction as ed

# %% [markdown]
# ## 📦 Define Project
#
# This section explains how to create a project and define its metadata.

# %% [markdown]
# ### Create Project

# %%
project = ed.Project(name='lbco_hrpt')

# %% [markdown]
# ### Set Project Metadata

# %%
project.metadata.title = 'La0.5Ba0.5CoO3 at HRPT@PSI'
project.metadata.description = """This project demonstrates a standard
refinement of La0.5Ba0.5CoO3, which crystallizes in a perovskite-type
structure, using neutron powder diffraction data collected in constant
wavelength mode at the HRPT diffractometer (PSI)."""

# %% [markdown]
# ### Show Project Metadata as CIF

# %%
project.metadata.show_as_cif()

# %% [markdown]
# ### Save Project
#
# When saving the project for the first time, you need to specify the
# directory path.

# %%
project.save_as(dir_path='projects/refine-lbco-hrpt-report')

# %% [markdown]
# ## 🧩 Define Structure
#
# This section shows how to add structures and modify their
# parameters.

# %% [markdown]
# ### Add Structure

# %%
project.structures.create(name='lbco')

# %% [markdown]
# ### Show Defined Structures
#
# Show the names of the crystal structures added. These names are used
# to access the structure using the syntax:
# `project.structures[name]`. All structure parameters can be accessed
# via the `project` object.

# %%
project.structures.show_names()

# %% [markdown]
# ### Set Space Group
#
# Modify the default space group parameters.

# %%
project.structures['lbco'].space_group.name_h_m = 'P m -3 m'
project.structures['lbco'].space_group.coord_system_code = '1'

# %% [markdown]
# ### Set Unit Cell
#
# Modify the default unit cell parameters.

# %%
project.structures['lbco'].cell.length_a = 3.88

# %% [markdown]
# ### Set Atom Sites
#
# Add atom sites to the structure.

# %%
project.structures['lbco'].atom_sites.create(
    id='La',
    type_symbol='La',
    fract_x=0,
    fract_y=0,
    fract_z=0,
    adp_iso=0.5,
    occupancy=0.5,
)
project.structures['lbco'].atom_sites.create(
    id='Ba',
    type_symbol='Ba',
    fract_x=0,
    fract_y=0,
    fract_z=0,
    adp_iso=0.5,
    occupancy=0.5,
)
project.structures['lbco'].atom_sites.create(
    id='Co',
    type_symbol='Co',
    fract_x=0.5,
    fract_y=0.5,
    fract_z=0.5,
    adp_iso=0.5,
)
project.structures['lbco'].atom_sites.create(
    id='O',
    type_symbol='O',
    fract_x=0,
    fract_y=0.5,
    fract_z=0.5,
    adp_iso=0.5,
)

# %% [markdown]
# ### Show Structure as CIF

# %%
project.structures['lbco'].show_as_cif()

# %% [markdown]
# ### Display Structure
#
# EasyDiffraction can draw the structure that has just been defined. The
# renderer engine is selected through `project.rendering_structure`. The default `auto`
# engine resolves to an interactive `threejs` view inside Jupyter and a
# compact `ascii` schematic in a terminal.

# %%
project.rendering_structure.show_supported()

# %% [markdown]
# Show all public attributes of the structure rendering engine.

# %%
project.rendering_structure.help()

# %% [markdown]
# Visual styling — the atom view and colour scheme — is configured on
# `project.structure_style`.

# %%
project.structure_style.atom_view.show_supported()
project.structure_style.color_scheme.show_supported()

# %%
project.structure_style.atom_view = 'adp'
project.structure_style.color_scheme = 'jmol'

# %% [markdown]
# Bonds are generated automatically between atoms whose separation lies
# within the per-structure cutoffs stored on `structure.geom`.

# %%
project.structures['lbco'].geom.min_bond_distance_cutoff = 0.5
project.structures['lbco'].geom.bond_distance_inc = 0.25

# %% [markdown]
# List which features the structure data and the active engine can draw.

# %%
project.display.show_structure_options(struct_name='lbco')

# %% [markdown]
# Draw the structure. With `include='auto'` (the default) every available
# feature is shown; a specific tuple such as `('atoms', 'bonds', 'cell')`
# can be requested instead.

# %%
project.display.structure(struct_name='lbco')

# %% [markdown]
# For a quick text schematic, switch to the `ascii` engine explicitly,
# then restore the automatic default.

# %%
project.rendering_structure.type = 'ascii'

# %%
project.display.structure(struct_name='lbco')

# %%
project.rendering_structure.type = 'auto'

# %% [markdown]
# ### Save Project State
#
# Save the project state after adding the structure. This ensures
# that all changes are stored and can be accessed later. The project
# state is saved in the directory specified during project creation.

# %%
project.save()

# %% [markdown]
# ## 🔬 Define Experiment
#
# This section shows how to add experiments, configure their parameters,
# and link the structures defined in the previous step.

# %% [markdown]
# ### Download Data
#
# Download the data file from the EasyDiffraction repository on GitHub.

# %%
data_path = ed.download_data('meas-lbco-hrpt', destination='data')

# %% [markdown]
# ### Create Experiment

# %%
project.experiments.add_from_data_path(
    name='hrpt',
    data_path=data_path,
    sample_form='powder',
    beam_mode='constant wavelength',
    radiation_probe='neutron',
)

# %% [markdown]
# ### Show Defined Experiments

# %%
project.experiments.show_names()

# %% [markdown]
# ### Show Measured Data

# %%
project.display.pattern(expt_name='hrpt')

# %% [markdown]
# ### Set Instrument
#
# Modify the default instrument parameters.

# %%
project.experiments['hrpt'].instrument.setup_wavelength = 1.494
project.experiments['hrpt'].instrument.calib_twotheta_offset = 0.6

# %% [markdown]
# ### Set Peak Profile
#
# Show supported peak profile types.

# %%
project.experiments['hrpt'].peak.show_supported()

# %% [markdown]
# Select the desired peak profile type.

# %%
project.experiments['hrpt'].peak.type = 'pseudo-voigt'

# %% [markdown]
# Modify default peak profile parameters.

# %%
project.experiments['hrpt'].peak.broad_gauss_u = 0.1
project.experiments['hrpt'].peak.broad_gauss_v = -0.1
project.experiments['hrpt'].peak.broad_gauss_w = 0.1
project.experiments['hrpt'].peak.broad_lorentz_x = 0
project.experiments['hrpt'].peak.broad_lorentz_y = 0.1

# %% [markdown]
# ### Set Background

# %% [markdown]
# Show supported background types.

# %%
project.experiments['hrpt'].background.show_supported()

# %% [markdown]
# Select the desired background type.

# %%
project.experiments['hrpt'].background.type = 'line-segment'

# %% [markdown]
# Add background points.

# %%
project.experiments['hrpt'].background.create(id='10', position=10, intensity=170)
project.experiments['hrpt'].background.create(id='30', position=30, intensity=170)
project.experiments['hrpt'].background.create(id='50', position=50, intensity=170)
project.experiments['hrpt'].background.create(id='110', position=110, intensity=170)
project.experiments['hrpt'].background.create(id='165', position=165, intensity=170)

# %% [markdown]
# Show current background points.

# %%
project.experiments['hrpt'].background.show()

# %% [markdown]
# ### Set Linked Structures
#
# Link the structure defined in the previous step to the experiment.

# %%
project.experiments['hrpt'].linked_structures.create(structure_id='lbco', scale=10.0)

# %% [markdown]
# ### Show Experiment as CIF

# %%
project.experiments['hrpt'].show_as_cif()

# %% [markdown]
# ### Save Project State

# %%
project.save()

# %% [markdown]
# ## 🚀 Perform Analysis
#
# This section explains the analysis process, including how to set up
# calculation and fitting engines.
#
# ### Set Calculator
#
# Show supported calculation engines for this experiment.

# %%
project.experiments['hrpt'].calculator.show_supported()

# %% [markdown]
# Select the desired calculation engine.

# %%
project.experiments['hrpt'].calculator.type = 'cryspy'

# %% [markdown]
# ### Set Plotting Engine
#
# EasyDiffraction can plot the measured and calculated patterns using different rendering engines.
# The default `auto` engine resolves to an interactive `plotly` view inside Jupyter and a
# static `asciichartpy` plot for schematic representation in a terminal.
#
# Show supported data plotting engines.

# %%
project.rendering_plot.show_supported()

# %% [markdown]
# Show all public attributes of the data rendering engine.

# %%
project.rendering_plot.help()

# %% [markdown]
# ### Display Pattern

# %%
project.display.pattern(expt_name='hrpt')

# %%
project.display.pattern(expt_name='hrpt', x_min=38, x_max=41)

# %% [markdown]
# ### Display Parameters
#
# Show all parameters of the project.

# %%
project.display.parameters.all()

# %% [markdown]
# Show all fittable parameters.

# %%
project.display.parameters.fittable()

# %% [markdown]
# Show only free parameters.

# %%
project.display.parameters.free()

# %% [markdown]
# Show how to access parameters in the code.

# %%
project.display.parameters.access()

# %% [markdown]
# ### Set Fit Mode
#
# Show supported fit modes.

# %%
project.analysis.fitting_mode.show_supported()

# %% [markdown]
# Select desired fit mode.

# %%
project.analysis.fitting_mode.type = 'single'

# %% [markdown]
# ### Set Minimizer
#
# Show supported fitting engines.

# %%
project.analysis.minimizer.show_supported()

# %% [markdown]
# Select desired fitting engine.

# %%
project.analysis.minimizer.type = 'lmfit'

# %% [markdown]
# ### Perform Fit 1/5
#
# Set structure parameters to be refined.

# %%
project.structures['lbco'].cell.length_a.free = True

# %% [markdown]
# Set experiment parameters to be refined.

# %%
project.experiments['hrpt'].linked_structures['lbco'].scale.free = True
project.experiments['hrpt'].instrument.calib_twotheta_offset.free = True
project.experiments['hrpt'].background['10'].intensity.free = True
project.experiments['hrpt'].background['30'].intensity.free = True
project.experiments['hrpt'].background['50'].intensity.free = True
project.experiments['hrpt'].background['110'].intensity.free = True
project.experiments['hrpt'].background['165'].intensity.free = True

# %% [markdown]
# Show free parameters after selection.

# %%
project.display.parameters.free()

# %% [markdown]
# #### Run Fitting

# %%
project.analysis.fit()
project.display.fit.results()

# %% [markdown]
# #### Display Pattern

# %%
project.display.pattern(expt_name='hrpt')

# %%
project.display.pattern(expt_name='hrpt', x_min=38, x_max=41)

# %% [markdown]
# ### Perform Fit 2/5
#
# Set more parameters to be refined.

# %%
project.experiments['hrpt'].peak.broad_gauss_u.free = True
project.experiments['hrpt'].peak.broad_gauss_v.free = True
project.experiments['hrpt'].peak.broad_gauss_w.free = True
project.experiments['hrpt'].peak.broad_lorentz_y.free = True

# %% [markdown]
# Show free parameters after selection.

# %%
project.display.parameters.free()

# %% [markdown]
# #### Run Fitting

# %%
project.analysis.fit()
project.display.fit.results()

# %% [markdown]
# #### Display Pattern

# %%
project.display.pattern(expt_name='hrpt')

# %%
project.display.pattern(expt_name='hrpt', x_min=38, x_max=41)

# %% [markdown]
# #### Save Project State

# %%
project.save()

# %% [markdown]
# ### Perform Fit 3/5
#
# Set more parameters to be refined.

# %%
project.structures['lbco'].atom_sites['La'].adp_iso.free = True
project.structures['lbco'].atom_sites['Ba'].adp_iso.free = True
project.structures['lbco'].atom_sites['Co'].adp_iso.free = True
project.structures['lbco'].atom_sites['O'].adp_iso.free = True

# %% [markdown]
# Show free parameters after selection.

# %%
project.display.parameters.free()

# %% [markdown]
# #### Run Fitting

# %%
project.analysis.fit()
project.display.fit.results()

# %% [markdown]
# #### Display Pattern

# %%
project.display.pattern(expt_name='hrpt')

# %%
project.display.pattern(expt_name='hrpt', x_min=38, x_max=41)

# %% [markdown]
# ### Perform Fit 4/5
#
# #### Set Constraints
#
# Set aliases for parameters.

# %%
project.analysis.aliases.create(
    id='biso_La',
    param=project.structures['lbco'].atom_sites['La'].adp_iso,
)
project.analysis.aliases.create(
    id='biso_Ba',
    param=project.structures['lbco'].atom_sites['Ba'].adp_iso,
)

# %% [markdown]
# Set constraints.

# %%
project.analysis.constraints.create(expression='biso_Ba = biso_La')

# %% [markdown]
# Show defined constraints.

# %%
project.analysis.constraints.show()

# %% [markdown]
# Show free parameters.

# %%
project.display.parameters.free()

# %% [markdown]
# #### Run Fitting

# %%
project.analysis.fit()
project.display.fit.results()

# %% [markdown]
# #### Display Pattern

# %%
project.display.pattern(expt_name='hrpt')

# %%
project.display.pattern(expt_name='hrpt', x_min=38, x_max=41)

# %% [markdown]
# ### Perform Fit 5/5
#
# #### Set Constraints
#
# Set more aliases for parameters.

# %%
project.analysis.aliases.create(
    id='occ_La',
    param=project.structures['lbco'].atom_sites['La'].occupancy,
)
project.analysis.aliases.create(
    id='occ_Ba',
    param=project.structures['lbco'].atom_sites['Ba'].occupancy,
)

# %% [markdown]
# Set more constraints.

# %%
project.analysis.constraints.create(
    expression='occ_Ba = 1 - occ_La',
)

# %% [markdown]
# Show defined constraints.

# %%
project.analysis.constraints.show()


# %% [markdown]
# Set structure parameters to be refined.

# %%
project.structures['lbco'].atom_sites['La'].occupancy.free = True

# %% [markdown]
# Show free parameters after selection.

# %%
project.display.parameters.free()

# %% [markdown]
# #### Run Fitting

# %%
project.analysis.fit()
project.display.fit.results()
project.display.fit.correlations()

# %% [markdown]
# #### Display Pattern

# %%
project.display.pattern(expt_name='hrpt')

# %%
project.display.pattern(expt_name='hrpt', x_min=38, x_max=41)

# %% [markdown]
# #### Display Structure

# %%
project.display.structure(struct_name='lbco')

# %% [markdown]
# ## 📊 Report
#
# This final section shows how to review the results of the analysis.
#
# By default, HTML report is generated after fitting. Here we also
# show how to activate generation of CIF, TEX and PDF reports with
# regular project saves.
# Keep in mind, that PDF report generation requires additional
# dependencies and is not that fast to be generated after each fit, so
# use it with caution.
# The generated report files will be saved in the `reports` folder of
# the project directory.

# %%
project.report.cif = True
project.report.tex = True
project.report.pdf = True
project.save()
