"""Per-peak normalised shape comparison: ED (fixed) vs Z-Rietveld.

Extracts each peak, subtracts local background, normalises to unit height,
then computes chi-squared shape residual.
"""
import math
import numpy as np

from easydiffraction import ExperimentFactory, Project, StructureFactory

# ── Build model with Z-Rietveld parameters ──
structure = StructureFactory.from_scratch(name='ceo2')
structure.space_group.name_h_m = 'F m -3 m'
structure.space_group.it_coordinate_system_code = '1'
structure.cell.length_a = 5.411651
structure.atom_sites.create(label='Ce', type_symbol='Ce',
    fract_x=0, fract_y=0, fract_z=0, b_iso=0.260694, wyckoff_letter='a')
structure.atom_sites.create(label='O', type_symbol='O',
    fract_x=0.25, fract_y=0.25, fract_z=0.25, b_iso=0.448237, wyckoff_letter='c')

expt = ExperimentFactory.from_data_path(
    name='se',
    data_path='data/MAT005500.SE.bin02Double_0_int_c.histogramIgor',
    beam_mode='time-of-flight')
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
for bg_id, bg_x, bg_y in [
    ('1',3000,0.061), ('2',6000,0.0384), ('3',8000,0.0291),
    ('4',10000,0.0273), ('5',12000,0.0206), ('6',20000,0.0267),
    ('7',30000,0.0202), ('8',40000,0.0157)]:
    expt.background.create(id=bg_id, x=bg_x, y=bg_y)
expt.excluded_regions.create(id='1', start=0, end=4000)
expt.excluded_regions.create(id='2', start=40015, end=100000)

project = Project()
project.structures.add(structure)
project.experiments.add(expt)
project.plotter.plot_meas_vs_calc(expt_name='se')

ed_tof = np.array(expt.data.x)
ed_ycalc = np.array(expt.data.intensity_calc)

# ── Load Z-Rietveld ──
zr_data = np.loadtxt('tmp/type0m/MAT005500.SE.bin02Double_0_int_c/A.txt',
                      skiprows=1, max_rows=9809)
zr_tof = zr_data[:, 0]
zr_ycalc = zr_data[:, 4]
zr_bg = zr_data[:, 5]

# ── Peak windows (wider for shape comparison) ──
peaks = [
    ("111", 31397, 3.124, 600),
    ("200", 27192, 2.706, 500),
    ("220", 19229, 1.913, 300),
    ("311", 16399, 1.632, 250),
    ("222", 15701, 1.562, 200),
    ("400", 13598, 1.353, 200),
    ("331", 12478, 1.242, 150),
    ("420", 12162, 1.210, 150),
    ("422", 11103, 1.105, 130),
]

print("=" * 80)
print("PER-PEAK NORMALISED SHAPE COMPARISON")
print("=" * 80)
print(f"{'hkl':>5} {'d':>6} {'shape_chi2':>10} {'FWHM_ZR':>8} {'FWHM_ED':>8} {'FWHM_ratio':>10}")
print("-" * 55)

total_chi2 = 0
n_peaks = 0

for hkl, tof_c, d, hw in peaks:
    # ── Z-Rietveld peak (subtract background) ──
    zr_mask = (zr_tof >= tof_c - hw) & (zr_tof <= tof_c + hw)
    zr_t = zr_tof[zr_mask]
    zr_bragg = zr_ycalc[zr_mask] - zr_bg[zr_mask]
    zr_max = np.max(zr_bragg)
    if zr_max <= 0:
        continue

    # ── ED peak (subtract local linear background) ──
    ed_mask = (ed_tof >= tof_c - hw) & (ed_tof <= tof_c + hw)
    if not np.any(ed_mask):
        continue
    ed_t = ed_tof[ed_mask]
    ed_y = ed_ycalc[ed_mask]
    ed_bg = np.interp(ed_t, [ed_t[0], ed_t[-1]], [ed_y[0], ed_y[-1]])
    ed_bragg = ed_y - ed_bg
    ed_max = np.max(ed_bragg)
    if ed_max <= 0:
        continue

    # ── Normalize ──
    zr_norm = zr_bragg / zr_max
    ed_norm = ed_bragg / ed_max

    # ── Interpolate ED onto ZR grid ──
    ed_on_zr = np.interp(zr_t, ed_t, ed_norm)

    # ── Shape chi2 (only where peak > 5% of max to exclude noise) ──
    sig_mask = zr_norm > 0.05
    if np.sum(sig_mask) < 5:
        continue
    diff = ed_on_zr[sig_mask] - zr_norm[sig_mask]
    chi2 = np.mean(diff**2)
    total_chi2 += chi2
    n_peaks += 1

    # ── FWHM ──
    dt_zr = zr_t[1] - zr_t[0]
    zr_fwhm = np.sum(zr_norm > 0.5) * dt_zr
    ed_fwhm = np.sum(ed_on_zr > 0.5) * dt_zr
    ratio = ed_fwhm / zr_fwhm if zr_fwhm > 0 else float('inf')

    print(f"{hkl:>5} {d:>6.3f} {chi2:>10.6f} {zr_fwhm:>8.0f} {ed_fwhm:>8.0f} {ratio:>10.3f}")

print("-" * 55)
print(f"{'TOTAL':>5} {'':>6} {total_chi2:>10.6f}   (avg: {total_chi2/n_peaks:.6f})")
print(f"\nNumber of peaks compared: {n_peaks}")
print(f"Average shape chi2: {total_chi2/n_peaks:.6f}")
print(f"Overall shape agreement: {'EXCELLENT' if total_chi2/n_peaks < 0.01 else 'GOOD' if total_chi2/n_peaks < 0.05 else 'MODERATE' if total_chi2/n_peaks < 0.1 else 'POOR'}")
