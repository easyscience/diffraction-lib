"""Test the alpha_prime fix hypothesis.

Current CrysPy bug: calc_alpha_prime returns 1/(α₁+α₂/d), then
alpha = 1/(alpha_prime * h_com) = (α₁+α₂/d)/h_com  ← double inversion!

Fix: calc_alpha_prime should return α₁+α₂/d (like beta primes), so
alpha = 1/((α₁+α₂/d) * h_com)  ← consistent with betas.

This script computes profiles both ways and compares FWHM with Z-Rietveld.
"""
import math
import numpy as np

# Import the building blocks directly
from cryspy.A_functions_base.powder_diffraction_tof_zcode import (
    calc_profile, calc_h_g, calc_h_com, calc_h_l, calc_sigma_square,
    calc_r_0, calc_beta_0_prime, calc_beta_1_prime
)

# Z-Rietveld parameters
sigma_0_sq = 0.0
sigma_1_sq = 225.55267
sigma_2_sq = 11.855817
gamma_0, gamma_1, gamma_2 = 2.465982, 0.81864, 1.413687
r_01, r_02, r_03 = 0.490923, 0.626017, 2.5
alpha_1, alpha_2 = -0.5697, 0.002
beta_00, beta_01, beta_10 = 0.445145, -0.276235, -0.741805

# ZR peak FWHMs (from shape_check.py output)
zr_fwhm_by_d = {3.12: 156, 1.91: 84, 1.05: 44, 0.72: 28}

print(f"{'d':>5} {'h_com':>7} | {'alpha_bug':>10} {'alpha_fix':>10} | {'FWHM_bug':>9} {'FWHM_fix':>9} {'FWHM_ZR':>8} | {'ratio_bug':>10} {'ratio_fix':>10}")
print("-" * 115)

for d_val in [3.12, 1.91, 1.35, 1.05, 0.72, 0.50]:
    sigma_sq = sigma_0_sq + sigma_1_sq * d_val**2 + sigma_2_sq * d_val**4
    sigma = math.sqrt(sigma_sq)
    h_l = gamma_0 + gamma_1 * d_val + gamma_2 * d_val**2
    h_g = calc_h_g(sigma)
    h_com = calc_h_com(h_g, h_l)

    A = alpha_1 + alpha_2 / d_val  # = -0.569...
    B0 = beta_00 + beta_01 / d_val
    B1 = beta_10

    r_0 = calc_r_0(d_val, r_01, r_02, r_03)

    # Betas (same in both)
    beta_0 = abs(1.0 / (B0 * h_com))
    beta_1 = abs(1.0 / (B1 * h_com))

    # Buggy alpha (current CrysPy): double inversion
    alpha_bug = abs(A / h_com)    # = abs(1/(alpha_prime * h_com)) where alpha_prime=1/A
    # Fixed alpha: consistent with betas
    alpha_fix = abs(1.0 / (A * h_com))

    # Compute profiles
    delta_t = np.linspace(-2000, 2000, 400001)
    dt = delta_t[1] - delta_t[0]

    prof_bug = calc_profile(delta_t, sigma, h_l, alpha_bug, beta_0, beta_1, r_0)
    prof_fix = calc_profile(delta_t, sigma, h_l, alpha_fix, beta_0, beta_1, r_0)

    # FWHM
    fwhm_bug = np.sum(prof_bug > 0.5 * np.max(prof_bug)) * dt
    fwhm_fix = np.sum(prof_fix > 0.5 * np.max(prof_fix)) * dt

    zr_fwhm = zr_fwhm_by_d.get(d_val, None)
    zr_str = f"{zr_fwhm:.0f}" if zr_fwhm else "?"

    # Also check asymmetry (left/right of peak)
    pk_bug = np.argmax(prof_bug)
    pk_fix = np.argmax(prof_fix)
    asym_bug = np.sum(prof_bug[:pk_bug]) / (np.sum(prof_bug[pk_bug:]) + 1e-30)
    asym_fix = np.sum(prof_fix[:pk_fix]) / (np.sum(prof_fix[pk_fix:]) + 1e-30)

    print(f"{d_val:>5.2f} {h_com:>7.1f} | {alpha_bug:>10.6f} {alpha_fix:>10.6f} | "
          f"{fwhm_bug:>9.1f} {fwhm_fix:>9.1f} {zr_str:>8} | "
          f"{asym_bug:>10.3f} {asym_fix:>10.3f}")

# Now do a full pattern test with fixed alpha and compare with ZR
print(f"\n{'='*80}")
print("Full pattern comparison: fixed alpha vs Z-Rietveld")
print(f"{'='*80}")

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
for bg_id, bg_x, bg_y in [('1',3000,0.061),('2',6000,0.0384),('3',8000,0.0291),('4',10000,0.0273),('5',12000,0.0206),('6',20000,0.0267),('7',30000,0.0202),('8',40000,0.0157)]:
    expt.background.create(id=bg_id, x=bg_x, y=bg_y)
expt.excluded_regions.create(id='1', start=0, end=4000)
expt.excluded_regions.create(id='2', start=40015, end=100000)

# MONKEY-PATCH calc_alpha_prime to test the fix
import cryspy.A_functions_base.powder_diffraction_tof_zcode as zcode
_orig_calc_alpha_prime = zcode.calc_alpha_prime
def _fixed_calc_alpha_prime(d, alpha_1, alpha_2):
    """Fixed: return alpha_1 + alpha_2/d (consistent with beta primes)."""
    import numpy
    return alpha_1 + alpha_2/d
zcode.calc_alpha_prime = _fixed_calc_alpha_prime

project = Project()
project.structures.add(structure)
project.experiments.add(expt)
project.plotter.plot_meas_vs_calc(expt_name='se')

ed_x = np.array(expt.data.x)
ed_ycalc = np.array(expt.data.intensity_calc)

# Z-Rietveld data
zr_data = np.loadtxt('tmp/type0m/MAT005500.SE.bin02Double_0_int_c/A.txt', skiprows=1, max_rows=9809)
zr_tof = zr_data[:, 0]
zr_ycalc = zr_data[:, 4]
zr_bg = zr_data[:, 5]

# Compare peaks
peak_info = [
    (31400, "(111)", 600),
    (19229, "(220)", 300),
    (10468, "(333)", 150),
    (7269,  "(642)", 100),
]

# Find global scale from (111) peak
hw = 600
ed_m = (ed_x >= 31400 - hw) & (ed_x <= 31400 + hw)
zr_m = (zr_tof >= 31400 - hw) & (zr_tof <= 31400 + hw)
ed_bragg = np.max(ed_ycalc[ed_m]) - np.min(ed_ycalc[ed_m])
zr_bragg = np.max(zr_ycalc[zr_m] - zr_bg[zr_m])
scale_match = zr_bragg / ed_bragg
print(f"Scale match from (111): {scale_match:.4f}")

print(f"\n{'Peak':>8} {'ED_FWHM':>8} {'ZR_FWHM':>8} {'asym_ED':>8} {'asym_ZR':>8} {'shape_RMS':>10}")
for pk_tof, hkl, hw in peak_info:
    ed_m = (ed_x >= pk_tof - hw) & (ed_x <= pk_tof + hw)
    zr_m = (zr_tof >= pk_tof - hw) & (zr_tof <= pk_tof + hw)
    if not np.any(ed_m) or not np.any(zr_m):
        continue

    ed_bg_val = np.min(ed_ycalc[ed_m])
    zr_bg_val = np.min(zr_ycalc[zr_m])
    ed_peak = ed_ycalc[ed_m] - ed_bg_val
    zr_peak = zr_ycalc[zr_m] - zr_bg_val
    ed_max = np.max(ed_peak)
    zr_max = np.max(zr_peak)
    if ed_max <= 0 or zr_max <= 0:
        continue

    ed_norm = ed_peak / ed_max
    zr_norm = zr_peak / zr_max
    ed_tof_w = ed_x[ed_m]
    zr_tof_w = zr_tof[zr_m]

    # FWHM
    ed_step = ed_tof_w[1] - ed_tof_w[0]
    zr_step = zr_tof_w[1] - zr_tof_w[0]
    ed_fwhm = np.sum(ed_norm > 0.5) * ed_step
    zr_fwhm = np.sum(zr_norm > 0.5) * zr_step

    # Asymmetry
    ed_pk = ed_tof_w[np.argmax(ed_peak)]
    zr_pk = zr_tof_w[np.argmax(zr_peak)]
    ed_asym = np.sum(ed_peak[ed_tof_w < ed_pk]) / (np.sum(ed_peak[ed_tof_w > ed_pk]) + 1e-30)
    zr_asym = np.sum(zr_peak[zr_tof_w < zr_pk]) / (np.sum(zr_peak[zr_tof_w > zr_pk]) + 1e-30)

    # RMS shape diff
    common_tof = np.arange(pk_tof - hw, pk_tof + hw + 1, 2)
    ed_interp = np.interp(common_tof, ed_tof_w, ed_norm, left=0, right=0)
    zr_interp = np.interp(common_tof, zr_tof_w, zr_norm, left=0, right=0)
    rms = np.sqrt(np.mean((ed_interp - zr_interp)**2))

    print(f"{hkl:>8} {ed_fwhm:>8.0f} {zr_fwhm:>8.0f} {ed_asym:>8.3f} {zr_asym:>8.3f} {rms:>10.4f}")

# Restore
zcode.calc_alpha_prime = _orig_calc_alpha_prime
