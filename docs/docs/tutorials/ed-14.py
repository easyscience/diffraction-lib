# %% [markdown]
# # Structure Refinement: Tb2TiO7, HEiDi
#
# Crystal structure refinement of Tb2TiO7 using single crystal neutron
# diffraction data from HEiDi at FRM II.

# %% [markdown]
# ## 🛠️ Import Library

# %%
import easydiffraction as ed

# %% [markdown]
# ## 📦 Define Project

# %%
# Create a minimal project with a short name
project = ed.Project(name='tbti_heidi')
project.metadata.title = 'Tb2Ti2O7 at HEiDi@FRMII'
project.metadata.description = """This project demonstrates a standard
refinement of the crystal structure of Tb2Ti2O7 using single crystal 
neutron diffraction data from HEiDi at FRM II."""

project.save_as(dir_path='projects/ed_14_tbti_heidi')

# %% [markdown]
# ## 🧩 Define Structure

# %%
# Download CIF file from repository
structure_path = ed.download_data(id=20, destination='data')

# %%
project.structures.add_from_cif_path(structure_path)

# %%
project.structures.show_names()

# %%
structure = project.structures['tbti']

# %%
structure.show_as_cif()

# %%
structure.atom_sites['Tb'].adp_type = 'Uiso'
structure.atom_sites['Ti'].adp_type = 'Uiso'
structure.atom_sites['O1'].adp_type = 'Uiso'
structure.atom_sites['O2'].adp_type = 'Uiso'

# %%
print(structure.atom_sites.as_cif)

# %%
structure.atom_sites['Tb'].adp_iso = 0.0
structure.atom_sites['Ti'].adp_iso = 0.0
structure.atom_sites['O1'].adp_iso = 0.0
structure.atom_sites['O2'].adp_iso = 0.0

# %% [markdown]
# ### Display Structure (ADP)
#
# Select the ADP atom view. With the starting isotropic displacements every
# atom is drawn as a sphere; after the anisotropic refinement below, the same
# view will draw probability ellipsoids for the anisotropic sites.

# %%
project.structure_style.atom_view = 'adp'

# %%
project.display.structure(struct_name='tbti')

# %% [markdown]
# ## 🔬 Define Experiment

# %%
# Download data file from repository
data_path = ed.download_data(id=19, destination='data')

# %%
project.experiments.add_from_data_path(
    name='heidi',
    data_path=data_path,
    sample_form='single crystal',
    beam_mode='constant wavelength',
    radiation_probe='neutron',
)

# %%
experiment = project.experiments['heidi']

# %%
experiment.linked_crystal.id = 'tbti'
experiment.linked_crystal.scale = 1.0

# %%
experiment.instrument.setup_wavelength = 0.793

# %%
experiment.extinction.mosaicity = 35000
experiment.extinction.radius = 10

# %% [markdown]
# ## 🚀 Perform Analysis

# %% [markdown]
# ### ADP iso

# %%
project.display.pattern(expt_name='heidi')

# %%
structure.atom_sites['O1'].fract_x.free = True

structure.atom_sites['Ti'].occupancy.free = True
structure.atom_sites['O1'].occupancy.free = True
structure.atom_sites['O2'].occupancy.free = True

structure.atom_sites['Tb'].adp_iso.free = True
structure.atom_sites['Ti'].adp_iso.free = True
structure.atom_sites['O1'].adp_iso.free = True
structure.atom_sites['O2'].adp_iso.free = True

# %%
experiment.linked_crystal.scale.free = True
experiment.extinction.radius.free = True

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
project.display.structure(struct_name='tbti')

# %%
project.experiments.show_names()

# %%
project.display.pattern(expt_name='heidi')

# %% [markdown]
# ### ADP aniso

# %%
structure.atom_sites['Tb'].adp_type = 'Uani'
structure.atom_sites['Ti'].adp_type = 'Uani'
structure.atom_sites['O1'].adp_type = 'Uani'
# structure.atom_sites['O2'].adp_type = 'Uani'

# %%
print(structure.atom_site_aniso.as_cif)

# %%
structure.atom_site_aniso['Tb'].adp_11.free = True
structure.atom_site_aniso['Tb'].adp_12.free = True
structure.atom_site_aniso['Ti'].adp_11.free = True
structure.atom_site_aniso['Ti'].adp_12.free = True
structure.atom_site_aniso['O1'].adp_11.free = True
structure.atom_site_aniso['O1'].adp_22.free = True
structure.atom_site_aniso['O1'].adp_23.free = True
# structure.atom_site_aniso['O2'].adp_11.free = True

# %%
project.analysis.fit()

# %%
project.display.fit.results()

# %%
project.display.fit.correlations()

# %%
project.display.pattern(expt_name='heidi')

# %%
structure.show_as_cif()

# %% [markdown]
# ### Display Structure (final)
#
# Tb, Ti and O1 were refined with anisotropic displacements (`Uani`), so the
# ADP view now draws them as probability ellipsoids, while O2 stayed isotropic
# (`Uiso`) and remains a sphere — highlighting how the view changed from the
# initial spheres to ellipsoids.

# %%
project.display.structure(struct_name='tbti')

# %% [markdown]
# ## 📊 Report

# %%
# Enable PDF report generation before the last save (time consuming)
project.report.pdf = True
project.save()
