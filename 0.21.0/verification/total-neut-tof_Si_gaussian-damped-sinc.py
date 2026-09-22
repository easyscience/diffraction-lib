# %% [markdown]
# # Si - powder neutron TOF total - gaussian-damped sinc
#
# Verifies the total-scattering gaussian-damped sinc profile by comparing
# EasyDiffraction's pdffit calculator with a direct diffpy.pdffit2
# calculation on the same synthetic r-grid.
#
# **Refinement:** none — every parameter is taken from the direct
# diffpy.pdffit2 reference; only the calculated patterns are compared.

# %%
from importlib import metadata

import numpy as np
from diffpy.pdffit2 import PdfFit
from diffpy.structure.parsers.p_cif import P_cif as pdffit_cif_parser

import easydiffraction as edi
from easydiffraction import ExperimentFactory
from easydiffraction.analysis import verification as verify

# %% [markdown]
# ## Build the project

# %%
project = edi.Project()

# %% [markdown]
# ## Define the structure

# %%
project.structures.create(name='si')
structure = project.structures['si']

structure.space_group.name_h_m = 'F d -3 m'
structure.space_group.coord_system_code = '1'
structure.cell.length_a = 5.4306

structure.atom_sites.create(
    id='Si',
    type_symbol='Si',
    fract_x=0.0,
    fract_y=0.0,
    fract_z=0.0,
    wyckoff_letter='a',
    adp_type='Biso',
    adp_iso=0.717,
)

# %% [markdown]
# ## Create the experiment

# %%
experiment = ExperimentFactory.from_scratch(
    name='si_pdf',
    sample_form='powder',
    beam_mode='time-of-flight',
    radiation_probe='neutron',
    scattering_type='total',
)

R_GRID = np.arange(1.0, 30.05, 0.05)
PDF_SCALE = 1.2728
PDF_QDAMP = 0.0251
PDF_QBROAD = 0.0183
PDF_QMAX = 35.0
PDF_DELTA_1 = 2.54
PDF_DELTA_2 = -1.7525
PDF_PARTICLE_DIAMETER = 0.0

experiment.data._create_items_set_xcoord_and_id(R_GRID)
experiment.data._set_g_r_meas(np.zeros_like(R_GRID))
experiment.data._set_g_r_meas_su(np.ones_like(R_GRID))

experiment.peak.type = 'gaussian-damped-sinc'
experiment.peak.damp_q = PDF_QDAMP
experiment.peak.broad_q = PDF_QBROAD
experiment.peak.cutoff_q = PDF_QMAX
experiment.peak.sharp_delta_1 = PDF_DELTA_1
experiment.peak.sharp_delta_2 = PDF_DELTA_2
experiment.peak.damp_particle_diameter = PDF_PARTICLE_DIAMETER

experiment.linked_structures.create(structure_id='si', scale=PDF_SCALE)

project.experiments.add(experiment)

# %% [markdown]
# ## Direct pdffit2 reference

# %%
B_TO_U_FACTOR = 8.0 * np.pi**2
SI_CIF_FOR_PDFFIT2 = f"""
data_si
_space_group_name_H-M_alt 'F d -3 m'
_space_group_IT_coordinate_system_code 1
_cell_length_a 5.4306
_cell_length_b 5.4306
_cell_length_c 5.4306
_cell_angle_alpha 90
_cell_angle_beta 90
_cell_angle_gamma 90
loop_
_atom_site_label
_atom_site_type_symbol
_atom_site_fract_x
_atom_site_fract_y
_atom_site_fract_z
_atom_site_U_iso_or_equiv
Si Si 0.0 0.0 0.0 {0.717 / B_TO_U_FACTOR:.12f}
"""

pdffit2 = PdfFit()
pdffit2.add_structure(pdffit_cif_parser().parse(SI_CIF_FOR_PDFFIT2))
pdffit2.setvar('pscale', PDF_SCALE)
pdffit2.setvar('delta1', PDF_DELTA_1)
pdffit2.setvar('delta2', PDF_DELTA_2)
pdffit2.setvar('spdiameter', PDF_PARTICLE_DIAMETER)
pdffit2.read_data_lists(
    stype='N',
    qmax=PDF_QMAX,
    qdamp=PDF_QDAMP,
    r_data=list(R_GRID),
    Gr_data=list(np.zeros_like(R_GRID)),
)
pdffit2.setvar('qbroad', PDF_QBROAD)
pdffit2.calc()

calc_direct_pdffit2 = np.array(pdffit2.getpdf_fit())
LABEL_DIRECT_PDFFIT2 = f'diffpy.pdffit2 {metadata.version("diffpy.pdffit2")}'

# %% [markdown]
# ## edi-pdffit VS direct pdffit2

# %%
experiment.calculator.type = 'pdffit'

project.analysis.calculate()
calc_ed_pdffit = experiment.data.intensity_calc
LABEL_ED_PDFFIT = verify.engine_label('pdffit')

project.display.pattern_comparison(
    'si_pdf',
    reference=calc_direct_pdffit2,
    candidate=calc_ed_pdffit,
    reference_label=LABEL_DIRECT_PDFFIT2,
    candidate_label=LABEL_ED_PDFFIT,
)

# %% [markdown]
# ## Agreement check

# %%
verify.assert_patterns_agree(
    [
        (
            f'{LABEL_ED_PDFFIT} vs {LABEL_DIRECT_PDFFIT2}',
            calc_direct_pdffit2,
            calc_ed_pdffit,
        ),
    ],
)
