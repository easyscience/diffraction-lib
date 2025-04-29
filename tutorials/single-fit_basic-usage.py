# %% [markdown]
# # Single Fit (Basic Usage)
#
# This example demonstrates the use of the EasyDiffraction API with a
# simplified, user-friendly approach that mimics the GUI workflow. It is
# intended for users with minimal programming experience who want to learn how
# to perform standard fitting of crystal structures using diffraction data. The
# script covers creating a project, adding sample models and experiments,
# performing analysis, and refining parameters.
#
# Only a single import is required (`import easydiffraction as ed`) and all
# operations are performed through high-level components of the `project`
# object, such as `project.sample_models`, `project.experiments`, and
# `project.analysis`. Project is the main object to store all the information.

# %% [markdown]
# ## Import EasyDiffraction

# %%
import easydiffraction as ed

# %% [markdown]
# ## Step 1: Create a Project
#
# In this section, you will learn how to create a project and define
# its metadata.

# %% [markdown]
# ### Create a new project object

# %%
project = ed.Project(name='lbco_hrpt')

# %% [markdown]
# ### Define project info

# %%
project.info.title = 'La0.5Ba0.5CoO3 from neutron diffraction at HRPT@PSI'
project.info.description = '''This project demonstrates a standard 
refinement of La0.5Ba0.5CoO3, which crystallizes in a perovskite-type 
structure, using neutron powder diffraction data collected in constant 
wavelength mode at the HRPT diffractometer (PSI).'''

# %% [markdown]
# ### Show project metadata as CIF

# %%
project.info.show_as_cif()

# %% [markdown]
# ### Save the project
#
# When we save the project for the first time, we need to specify the
# directory path. In the example below, we save the project to the
# temporary location defined by the system.

# %%
project.save_as(dir_path='lbco_hrpt', temporary=True)

# %% [markdown]
# ## Step 2: Add Sample Model
#
# This section covers how to add sample models and modify their parameters.

# %% [markdown]
# ## Add a sample model with default parameters

# %%
project.sample_models.add(name='lbco')

# %% [markdown]
# ### Show defined sample models
#
# Show names of the models added. Those names are used for accessing the
# model using this syntax: project.sample_models['model_name']. That is,
# accessing all the model parameters is done via the project object.

# %%
project.sample_models.show_names()

# %% [markdown]
# ### Modify sample model parameters

# %% [markdown]
# Space group

# %%
project.sample_models['lbco'].space_group.name_h_m = 'P m -3 m'
project.sample_models['lbco'].space_group.it_coordinate_system_code = '1'

# %% [markdown]
# Unit cell parameters

# %%
project.sample_models['lbco'].cell.length_a = 3.88

# %% [markdown]
# Atom sites

# %%
project.sample_models['lbco'].atom_sites.add(label='La',
                                             type_symbol='La',
                                             fract_x=0,
                                             fract_y=0,
                                             fract_z=0,
                                             wyckoff_letter='a',
                                             b_iso=0.5,
                                             occupancy=0.5)
project.sample_models['lbco'].atom_sites.add(label='Ba',
                                             type_symbol='Ba',
                                             fract_x=0,
                                             fract_y=0,
                                             fract_z=0,
                                             wyckoff_letter='a',
                                             b_iso=0.5,
                                             occupancy=0.5)
project.sample_models['lbco'].atom_sites.add(label='Co',
                                             type_symbol='Co',
                                             fract_x=0.5,
                                             fract_y=0.5,
                                             fract_z=0.5,
                                             wyckoff_letter='b',
                                             b_iso=0.5)
project.sample_models['lbco'].atom_sites.add(label='O',
                                             type_symbol='O',
                                             fract_x=0,
                                             fract_y=0.5,
                                             fract_z=0.5,
                                             wyckoff_letter='c',
                                             b_iso=0.5)

# %% [markdown]
# ### Apply symmetry constraints

# %%
project.sample_models['lbco'].apply_symmetry_constraints()

# %% [markdown]
# ### Show sample model as CIF

# %%
project.sample_models['lbco'].show_as_cif()

# %% [markdown]
# ### Show sample model structure

# %%
project.sample_models['lbco'].show_structure()

# %% [markdown]
# ### Save the project state
#
# Save the project state after adding the sample model. This is important
# to ensure that all changes are stored and can be accessed later. The
# project state is saved in the directory specified during project
# creation.

# %%
project.save()
