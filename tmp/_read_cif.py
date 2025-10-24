# %% [markdown]
# # Structure Refinement: LBCO, HRPT
#
# This minimalistic example is designed to be as compact as possible for
# a Rietveld refinement of a crystal structure using constant-wavelength
# neutron powder diffraction data for La0.5Ba0.5CoO3 from HRPT at PSI.
#
# It does not contain any advanced features or options, and includes no
# comments or explanations—these can be found in the other tutorials.
# Default values are used for all parameters if not specified. Only
# essential and self-explanatory code is provided.
#
# The example is intended for users who are already familiar with the
# EasyDiffraction library and want to quickly get started with a simple
# refinement. It is also useful for those who want to see what a
# refinement might look like in code. For a more detailed explanation of
# the code, please refer to the other tutorials.

# %% [markdown]
# ## Import Library

# %%
import easydiffraction as ed

# %%
from easydiffraction.utils.logging import Logger
Logger.configure(
    level=Logger.Level.INFO,
    mode=Logger.Mode.COMPACT,
    reaction=Logger.Reaction.WARN,
)

# %% [markdown]
# ## Step 1: Define Project

# %%
project = ed.Project()

# %% [markdown]
# ## Step 2: Define Sample Model

# %%
project.sample_models.add_from_cif_path("data/lbco.cif")

# %%
project.sample_models.show_names()

# %%
# Create an alias for easier access
lbco = project.sample_models['lbco']

# %%
lbco.show_as_cif()

# %% [markdown]
# ## Step 3: Define Experiment

# %%
project.experiments.add_from_cif_path("data/hrpt.cif")

# %%
project.experiments.show_names()

# %%
# Create an alias for easier access
hrpt = project.experiments['hrpt']

# %%
hrpt.show_as_cif()

# %% [markdown]
# ## Step 4: Perform Analysis

# %%
# Select sample model parameters to refine
lbco.cell.length_a.free = True

#lbco.atom_sites['La'].b_iso.free = True
#lbco.atom_sites['Ba'].b_iso.free = True
#lbco.atom_sites['Co'].b_iso.free = True
#lbco.atom_sites['O'].b_iso.free = True
for atom_site in lbco.atom_sites:
    atom_site.b_iso.free = True

# %%
# Select experiment parameters to refine
hrpt.linked_phases['lbco'].scale.free = True

hrpt.instrument.calib_twotheta_offset.free = True

hrpt.peak.broad_gauss_u.free = True
hrpt.peak.broad_gauss_v.free = True
hrpt.peak.broad_gauss_w.free = True
hrpt.peak.broad_lorentz_y.free = True

#hrpt.background['10'].y.free = True
#hrpt.background['30'].y.free = True
#hrpt.background['50'].y.free = True
#hrpt.background['110'].y.free = True
#hrpt.background['165'].y.free = True
for line_segment in hrpt.background:
    line_segment.y.free = True

# %%
project.analysis.fit()

# %%
project.plot_meas_vs_calc(expt_name='hrpt', show_residual=True)

# %%
