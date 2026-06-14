# %% [markdown]
# # Structure Refinement: Taurine, SENJU
#
# Crystal structure refinement of Taurine using time-of-flight single
# crystal neutron diffraction data from SENJU at J-PARC.

# %% [markdown]
# ## 🛠️ Import Library

# %%
import easydiffraction as ed

# %% [markdown]
# ## 📦 Define Project

# %%
# Create a minimal project with a short name
project = ed.Project(name='taurine_senju')

# %% [markdown]
# ## 🧩 Define Structure

# %%
# Download CIF file from repository
structure_path = ed.download_data('struct-taurine', destination='data')

# %%
project.structures.add_from_cif_path(structure_path)

# %%
project.structures.show_names()

# %%
structure = project.structures['taurine']

# %%
structure.show_as_cif()

# %%
project.display.structure(struct_name='taurine')

# %% [markdown]
# ## 🔬 Define Experiment

# %%
# Download data file from repository
data_path = ed.download_data('meas-taurine-senju', destination='data')

# %%
project.experiments.add_from_data_path(
    name='senju',
    data_path=data_path,
    sample_form='single crystal',
    beam_mode='time-of-flight',
    radiation_probe='neutron',
)

# %%
experiment = project.experiments['senju']

# %%
experiment.linked_structure.structure_id = 'taurine'
experiment.linked_structure.scale = 1.0

# %%
experiment.extinction.mosaicity = 1000.0
experiment.extinction.radius = 100.0

# %% [markdown]
# ## 🚀 Perform Analysis

# %% [markdown]
# ### ADP iso

# %%
project.display.pattern(expt_name='senju')

# %%
experiment.linked_structure.scale.free = True
experiment.extinction.radius.free = True

# %%
project.analysis.minimizer.show_supported()

# %%
project.analysis.minimizer.type = 'bumps'

# %%
# Limit number of iterations to prevent long calculation time in this tutorial.
project.analysis.minimizer.max_iterations = 500

# %%
# Start refinement. All parameters, which have standard uncertainties
# in the input CIF files, are refined by default.
project.analysis.fit()

# %%
# Show fit results summary
project.display.fit.results()

# %%
structure.show_as_cif()

# %%
project.experiments.show_names()

# %%
project.display.pattern(expt_name='senju')

# %% [markdown]
# ### ADP aniso

# %%
for atom_site in structure.atom_sites:
    atom_site.adp_type = 'Uani'

# %%
adp_components = ('adp_11', 'adp_22', 'adp_33', 'adp_12', 'adp_13', 'adp_23')
for atom_site in structure.atom_site_aniso:
    for component in adp_components:
        getattr(atom_site, component).free = True

# %%
structure.show_as_cif()

# %%
project.display.parameters.free()

# %%
project.analysis.fit()

# %%
project.display.fit.results()

# %%
project.display.fit.correlations()

# %%
project.display.pattern(expt_name='senju')

# %%
structure.show_as_cif()

# %% [markdown]
# ## 💾 Save Project

# %%
project.save_as(dir_path='projects/refine-taurine-senju')
