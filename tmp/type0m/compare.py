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
expt.linked_phases.create(id='ceo2', scale=1.0)  # scale=1 to see raw CrysPy pattern
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
for bg_id, bg_x, bg_y in [('1',3000,0.061),('2',6000,0.0384),('3',8000,0.0291),('4',10000,0.0273),('5',12000,0.0206),('6',20000,0.0267),('7',30000,0.0202),('8',40000,0.0157)]:
    expt.background.create(id=bg_id, x=bg_x, y=bg_y)
expt.excluded_regions.create(id='1', start=0, end=4000)
expt.excluded_regions.create(id='2', start=40015, end=100000)

project = Project()
project.structures.add(structure)
project.experiments.add(expt)

# Compare with Z-Rietveld
zr_data = np.loadtxt('tmp/type0m/MAT005500.SE.bin02Double_0_int_c/A.txt', skiprows=1, max_rows=9809)
zr_tof = zr_data[:, 0]
zr_ycalc = zr_data[:, 4]
zr_bg = zr_data[:, 5]
zr_active = (zr_tof >= 4001) & (zr_tof <= 40015)

# Trigger calc and get ED data
project.plotter.plot_meas_vs_calc(expt_name='se')

y_calc = np.array(expt.data.intensity_calc)
y_meas = np.array(expt.data.intensity_meas)

# Background
y_bkg = np.array(expt.data.intensity_bkg) if hasattr(expt.data, 'intensity_bkg') else None

print(f"ED y_calc (scale=1): max={np.max(y_calc):.4f}")
print(f"ZR y_calc: max={np.max(zr_ycalc[zr_active]):.4f}")

# Check what scale would match
ed_bragg = np.max(y_calc) - 0.016  # subtract approximate background
zr_bragg = np.max(zr_ycalc[zr_active]) - np.max(zr_bg[zr_active])
needed_scale = zr_bragg / ed_bragg if ed_bragg > 0 else float('inf')
print(f"ED Bragg max (scale=1): {ed_bragg:.4f}")
print(f"ZR Bragg max: {zr_bragg:.4f}")
print(f"Scale needed to match ZR: {needed_scale:.6f}")

# Compare at specific TOF positions (strongest peaks)
# ZR strongest peak is at TOF=19233
# Let's find it in ED
x = np.array(expt.data.x)
mask_peak = (x >= 19200) & (x <= 19300)
if np.any(mask_peak):
    print(f"\nPeak around TOF=19233:")
    print(f"  ED y_calc max in region: {np.max(y_calc[mask_peak]):.4f}")
    print(f"  ZR y_calc max: {np.max(zr_ycalc[(zr_tof>=19200) & (zr_tof<=19300)]):.4f}")

# Try to estimate proper scale by comparing curves
# Use a simple ratio at several peak positions
peak_tofs = [7269, 10591, 12226, 14599, 19233, 21597, 27191, 31398]
print(f"\n{'TOF':>8} {'ZR_ycalc':>10} {'ED_ycalc':>10} {'ratio':>10}")
for ptof in peak_tofs:
    zr_idx = np.argmin(np.abs(zr_tof - ptof))
    ed_idx = np.argmin(np.abs(x - ptof))
    if zr_tof[zr_idx] == x[ed_idx]:
        print(f"{ptof:>8} {zr_ycalc[zr_idx]:>10.4f} {y_calc[ed_idx]:>10.4f} {zr_ycalc[zr_idx]/(y_calc[ed_idx]) if y_calc[ed_idx] > 0 else 0:>10.2f}")
    else:
        print(f"{ptof:>8} ZR@{zr_tof[zr_idx]:.0f}={zr_ycalc[zr_idx]:.4f} ED@{x[ed_idx]:.0f}={y_calc[ed_idx]:.4f}")
