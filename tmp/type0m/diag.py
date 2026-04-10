import math
import numpy as np
import warnings
warnings.filterwarnings('ignore')

from easydiffraction import ExperimentFactory, Project, StructureFactory

structure = StructureFactory.from_scratch(name='ceo2')
structure.space_group.name_h_m = 'F m -3 m'
structure.space_group.it_coordinate_system_code = '1'
structure.cell.length_a = 5.411651
structure.atom_sites.create(label='Ce', type_symbol='Ce', fract_x=0, fract_y=0, fract_z=0, b_iso=0.260694, wyckoff_letter='a')
structure.atom_sites.create(label='O', type_symbol='O', fract_x=0.25, fract_y=0.25, fract_z=0.25, b_iso=0.448237, wyckoff_letter='c')

expt = ExperimentFactory.from_data_path(name='se', data_path='data/MAT005500.SE.bin02Double_0_int_c.histogramIgor', beam_mode='time-of-flight')
expt.linked_phases.create(id='ceo2', scale=8.089773e-5)
expt.instrument.setup_twotheta_bank = 90.0
expt.instrument.calib_d_to_tof_offset = 1.861874
expt.instrument.calib_d_to_tof_linear = 10050.037258
expt.instrument.calib_d_to_tof_quad = -0.514363
expt.peak_profile_type = 'double-jorgensen-von-dreele'
expt.peak.broad_gauss_sigma_0 = math.sqrt(0.0)
expt.peak.broad_gauss_sigma_1 = math.sqrt(225.55267)
expt.peak.broad_gauss_sigma_2 = math.sqrt(11.855817)
expt.peak.broad_lorentz_gamma_0 = 2.465982
expt.peak.broad_lorentz_gamma_1 = 0.81864
expt.peak.broad_lorentz_gamma_2 = 1.413687
expt.peak.dexp_decay_beta_10 = -0.741805
expt.peak.dexp_decay_beta_00 = 0.445145
expt.peak.dexp_decay_beta_01 = -0.276235
expt.peak.dexp_rise_alpha_1 = -0.5697
expt.peak.dexp_rise_alpha_2 = 0.002
expt.peak.dexp_switch_r_01 = 0.490923
expt.peak.dexp_switch_r_02 = 0.626017
expt.peak.dexp_switch_r_03 = 2.5
expt.background_type = 'line-segment'
expt.background.create(id='1', x=3000, y=0.061)
expt.background.create(id='2', x=6000, y=0.0384)
expt.background.create(id='3', x=8000, y=0.0291)
expt.background.create(id='4', x=10000, y=0.0273)
expt.background.create(id='5', x=12000, y=0.0206)
expt.background.create(id='6', x=20000, y=0.0267)
expt.background.create(id='7', x=30000, y=0.0202)
expt.background.create(id='8', x=40000, y=0.0157)
expt.excluded_regions.create(id='1', start=0, end=4000)
expt.excluded_regions.create(id='2', start=40015, end=100000)

project = Project()
project.structures.add(structure)
project.experiments.add(expt)
project.analysis.current_minimizer = 'lmfit'

# Load Z-Rietveld reference data
zr_data = np.loadtxt(
    'tmp/type0m/MAT005500.SE.bin02Double_0_int_c/A.txt',
    skiprows=1, max_rows=9809
)
zr_tof = zr_data[:, 0]
zr_yobs = zr_data[:, 3]
zr_ycalc = zr_data[:, 4]
zr_bg = zr_data[:, 5]

# Force a pattern generation
project.plotter.plot_meas_vs_calc(expt_name='se', show_residual=True)

y_meas = np.array(expt.data.intensity_meas)
y_calc = np.array(expt.data.intensity_calc)

print(f'\n=== EasyDiffraction ===')
print(f'Points: {len(y_meas)}')
print(f'y_meas: min={np.min(y_meas):.4f}, max={np.max(y_meas):.4f}')
print(f'y_calc: min={np.min(y_calc):.6f}, max={np.max(y_calc):.6f}')

print(f'\n=== Z-Rietveld ===')
zr_active = (zr_tof >= 4001) & (zr_tof <= 40015)
print(f'Points (active): {np.sum(zr_active)}')
print(f'yobs: min={np.min(zr_yobs[zr_active]):.4f}, max={np.max(zr_yobs[zr_active]):.4f}')
print(f'ycalc: min={np.min(zr_ycalc[zr_active]):.6f}, max={np.max(zr_ycalc[zr_active]):.6f}')
print(f'bg: min={np.min(zr_bg[zr_active]):.6f}, max={np.max(zr_bg[zr_active]):.6f}')

# Compare peak intensities  
print(f'\n=== Peak Comparison ===')
zr_peak_idx = np.argmax(zr_ycalc[zr_active])
print(f'Z-Rietveld strongest peak: TOF={zr_tof[zr_active][zr_peak_idx]:.0f}, ycalc={zr_ycalc[zr_active][zr_peak_idx]:.4f}')
print(f'Z-Rietveld ycalc-bg at strongest: {(zr_ycalc[zr_active][zr_peak_idx] - zr_bg[zr_active][zr_peak_idx]):.4f}')

if np.max(y_calc) > 0:
    ed_peak_idx = np.argmax(y_calc)
    print(f'ED strongest peak: idx={ed_peak_idx}, y_calc={y_calc[ed_peak_idx]:.4f}')
    ratio = np.max(y_calc) / np.max(zr_ycalc[zr_active])
    print(f'Intensity ratio ED/ZR: {ratio:.4f}')
else:
    print(f'ED y_calc is all zeros!')
