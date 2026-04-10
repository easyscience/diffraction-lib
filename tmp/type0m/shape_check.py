"""Compare type0m peak shapes: CrysPy vs Z-Rietveld.

Normalizes each peak individually to isolate shape differences
from overall scale or relative-intensity differences.
"""
import math
import numpy as np
import warnings
warnings.filterwarnings('ignore')

from easydiffraction import ExperimentFactory, Project, StructureFactory

# ─── Setup ───
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

project = Project()
project.structures.add(structure)
project.experiments.add(expt)
project.plotter.plot_meas_vs_calc(expt_name='se')

ed_x = np.array(expt.data.x)
ed_ycalc = np.array(expt.data.intensity_calc)
ed_ybkg = np.array(expt.data.intensity_bkg) if hasattr(expt.data, 'intensity_bkg') else np.zeros_like(ed_ycalc)

# Z-Rietveld data
zr_data = np.loadtxt('tmp/type0m/MAT005500.SE.bin02Double_0_int_c/A.txt', skiprows=1, max_rows=9809)
zr_tof = zr_data[:, 0]
zr_ycalc = zr_data[:, 4]
zr_bg = zr_data[:, 5]

# ─── 1. Find matching scale via isolated strongest peak (111) at TOF~31400 ───
hw = 600
pk_tof = 31400
ed_m = (ed_x >= pk_tof - hw) & (ed_x <= pk_tof + hw)
zr_m = (zr_tof >= pk_tof - hw) & (zr_tof <= pk_tof + hw)
ed_bragg_111 = np.max(ed_ycalc[ed_m] - ed_ybkg[ed_m]) if ed_ybkg is not None else np.max(ed_ycalc[ed_m])
zr_bragg_111 = np.max(zr_ycalc[zr_m] - zr_bg[zr_m])
best_scale = zr_bragg_111 / ed_bragg_111
print(f"Matching scale from (111) peak: ED Bragg max={ed_bragg_111:.6f}, ZR Bragg max={zr_bragg_111:.6f}, ratio={best_scale:.6f}")

# ─── 2. Check relative peak intensities (Bragg-only, scaled by single factor) ───
# Using the (111)-derived scale to predict other peaks
peak_info = [
    (31400, "(111)", 600),
    (27192, "(200)", 400),
    (19229, "(220)", 300),
    (16399, "(311)", 200),
    (15701, "(222)", 200),
    (13598, "(400)", 200),
    (10468, "(333)", 150),
    (7269,  "(642)", 100),
    (5553,  "(844)", 80),
]

print(f"\n{'Peak':>8} {'TOF':>6} {'ZR_Bragg':>10} {'ED_Bragg':>10} {'ED*scale':>10} {'ratio':>8}")
for pk_tof, hkl, hw in peak_info:
    ed_m = (ed_x >= pk_tof - hw) & (ed_x <= pk_tof + hw)
    zr_m = (zr_tof >= pk_tof - hw) & (zr_tof <= pk_tof + hw)
    if not np.any(ed_m) or not np.any(zr_m):
        continue
    ed_bg_val = np.min(ed_ycalc[ed_m])
    zr_bg_val = np.min(zr_ycalc[zr_m])
    ed_bragg = np.max(ed_ycalc[ed_m]) - ed_bg_val
    zr_bragg = np.max(zr_ycalc[zr_m]) - zr_bg_val
    ed_scaled = ed_bragg * best_scale
    ratio = zr_bragg / ed_scaled if ed_scaled > 0 else float('inf')
    print(f"{hkl:>8} {pk_tof:>6} {zr_bragg:>10.6f} {ed_bragg:>10.6f} {ed_scaled:>10.6f} {ratio:>8.4f}")

# ─── 3. Per-peak shape comparison (normalized to unit peak height) ───
print(f"\n{'='*90}")
print("Per-peak shape comparison (each peak normalized to 1.0 at its maximum)")
print(f"{'='*90}")

for pk_tof, hkl, hw in [(31400,"(111)",600), (19229,"(220)",300), (10468,"(333)",150), (7269,"(642)",100)]:
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

    ed_tof = ed_x[ed_m]
    zr_tof_w = zr_tof[zr_m]

    # Peak position
    ed_pk_pos = ed_tof[np.argmax(ed_peak)]
    zr_pk_pos = zr_tof_w[np.argmax(zr_peak)]

    # FWHM: count points above 0.5
    ed_step = ed_tof[1] - ed_tof[0] if len(ed_tof) > 1 else 2
    zr_step = zr_tof_w[1] - zr_tof_w[0] if len(zr_tof_w) > 1 else 2
    ed_fwhm = np.sum(ed_norm > 0.5) * ed_step
    zr_fwhm = np.sum(zr_norm > 0.5) * zr_step

    # Asymmetry (integrated left/right of peak)
    ed_left = np.sum(ed_peak[ed_tof < ed_pk_pos])
    ed_right = np.sum(ed_peak[ed_tof > ed_pk_pos])
    zr_left = np.sum(zr_peak[zr_tof_w < zr_pk_pos])
    zr_right = np.sum(zr_peak[zr_tof_w > zr_pk_pos])
    ed_asym = ed_left / (ed_right + 1e-30)
    zr_asym = zr_left / (zr_right + 1e-30)

    d_approx = (pk_tof - 1.86) / 10050.0
    print(f"\n{hkl} at TOF≈{pk_tof}, d≈{d_approx:.3f} Å:")
    print(f"  ED: pk_pos={ed_pk_pos:.0f}, FWHM≈{ed_fwhm:.0f} μs, asym(L/R)={ed_asym:.3f}")
    print(f"  ZR: pk_pos={zr_pk_pos:.0f}, FWHM≈{zr_fwhm:.0f} μs, asym(L/R)={zr_asym:.3f}")

    # Sample the normalized profile at offsets from peak center
    offsets = list(range(-hw, hw+1, max(hw//10, 1)))
    # Interpolate both to same TOF grid
    common_tof = np.arange(pk_tof - hw, pk_tof + hw + 1, 2)
    ed_interp = np.interp(common_tof, ed_tof, ed_norm, left=0, right=0)
    zr_interp = np.interp(common_tof, zr_tof_w, zr_norm, left=0, right=0)
    diff = ed_interp - zr_interp
    max_diff = np.max(np.abs(diff))
    rms_diff = np.sqrt(np.mean(diff**2))
    print(f"  Shape diff: max|Δ|={max_diff:.4f}, RMS(Δ)={rms_diff:.4f}")

    # Print comparison at selected points
    pts = [pk_tof + off for off in [-hw, -hw//2, -hw//4, -20, 0, 20, hw//4, hw//2, hw]]
    print(f"  {'TOF':>8} {'ED_norm':>8} {'ZR_norm':>8} {'Δ':>8}")
    for pt in pts:
        idx = np.argmin(np.abs(common_tof - pt))
        print(f"  {common_tof[idx]:>8.0f} {ed_interp[idx]:>8.4f} {zr_interp[idx]:>8.4f} {diff[idx]:>+8.4f}")

# ─── 4. Profile function normalization check ───
print(f"\n{'='*90}")
print("Profile function normalization (integral should ≈ 1.0)")
print(f"{'='*90}")
from cryspy.A_functions_base.powder_diffraction_tof_zcode import calc_profile_by_zcode_parameters

for d_val in [3.12, 1.91, 1.35, 1.05, 0.72, 0.50]:
    delta_t = np.linspace(-2000, 2000, 400001)
    d_arr = np.full_like(delta_t, d_val)
    profile = calc_profile_by_zcode_parameters(
        delta_t, d_arr,
        0.0, 225.55267, 11.855817,
        2.465982, 0.81864, 1.413687,
        0.490923, 0.626017, 2.5,
        -0.5697, 0.002,
        0.445145, -0.276235,
        -0.741805
    )
    dt = delta_t[1] - delta_t[0]
    integral = np.sum(profile) * dt
    peak_val = np.max(profile)
    fwhm_pts = np.sum(profile > 0.5 * peak_val)
    fwhm = fwhm_pts * dt
    print(f"  d={d_val:.2f}: integral={integral:.6f}, peak={peak_val:.6e}, FWHM≈{fwhm:.1f} μs")

# ─── 5. Check what happens with alpha_prime/h_com vs 1/(alpha_prime*h_com) ───
print(f"\n{'='*90}")
print("alpha/beta values at each d (current CrysPy formula)")
print(f"{'='*90}")
from cryspy.A_functions_base.powder_diffraction_tof_zcode import (
    calc_alpha_prime, calc_beta_0_prime, calc_beta_1_prime,
    calc_h_g, calc_h_com, calc_h_l, calc_sigma_square
)

for d_val in [3.12, 1.91, 1.35, 1.05, 0.72, 0.62, 0.50]:
    sigma_sq = 0.0 + 225.55267 * d_val**2 + 11.855817 * d_val**4
    sigma = math.sqrt(sigma_sq)
    h_l = 2.465982 + 0.81864 * d_val + 1.413687 * d_val**2
    h_g = calc_h_g(sigma)
    h_com = calc_h_com(h_g, h_l)

    a_prime = 1.0 / (-0.5697 + 0.002 / d_val)
    b0_prime = 0.445145 + (-0.276235) / d_val
    b1_prime = -0.741805

    # CrysPy: alpha = |1/(a_prime * h_com)| = |A(d)| / h_com
    alpha_cryspy = abs(1.0 / (a_prime * h_com))
    beta0_cryspy = abs(1.0 / (b0_prime * h_com))
    beta1_cryspy = abs(1.0 / (b1_prime * h_com))

    # Alternative: alpha = |a_prime| / h_com = 1/(|A(d)| * h_com)
    alpha_alt = abs(a_prime) / h_com
    beta0_alt = abs(b0_prime) / h_com
    beta1_alt = abs(b1_prime) / h_com

    print(f"  d={d_val:.2f}: sigma={sigma:.2f}, h_l={h_l:.2f}, h_com={h_com:.2f}")
    print(f"    primes: a'={a_prime:.4f}, b0'={b0_prime:.4f}, b1'={b1_prime:.4f}")
    print(f"    CrysPy:  alpha={alpha_cryspy:.6f}, beta0={beta0_cryspy:.6f}, beta1={beta1_cryspy:.6f}")
    print(f"    Alt:     alpha={alpha_alt:.6f}, beta0={beta0_alt:.6f}, beta1={beta1_alt:.6f}")
    print(f"    Ratio (CrysPy/Alt): alpha={alpha_cryspy/alpha_alt:.4f}, beta0={beta0_cryspy/(beta0_alt+1e-30):.4f}, beta1={beta1_cryspy/beta1_alt:.4f}")
