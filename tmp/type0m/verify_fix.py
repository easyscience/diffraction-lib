"""Compare EasyDiffraction (with fixed CrysPy) vs Z-Rietveld pattern.

Uses the same Z-Rietveld parameters (no fitting) and overlays patterns.
Reports per-peak FWHM and shape comparison.
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

# ── Generate ED pattern ──
project.plotter.plot_meas_vs_calc(expt_name='se')

ed_tof = np.array(expt.data.x)
ed_ycalc = np.array(expt.data.intensity_calc)

# ── Load Z-Rietveld pattern ──
zr_data = np.loadtxt('tmp/type0m/MAT005500.SE.bin02Double_0_int_c/A.txt',
                      skiprows=1, max_rows=9809)
zr_tof = zr_data[:, 0]
zr_ycalc = zr_data[:, 4]
zr_bg = zr_data[:, 5]

# ── Per-peak comparison ──
peaks = [
    ("111", 31397, 3.124, 500),
    ("200", 27192, 2.706, 400),
    ("220", 19229, 1.913, 250),
    ("311", 16399, 1.632, 180),
    ("222", 15701, 1.562, 150),
    ("400", 13598, 1.353, 150),
    ("331", 12478, 1.242, 120),
    ("420", 12162, 1.210, 120),
    ("422", 11103, 1.105, 100),
]

print("=" * 90)
print("PER-PEAK FWHM COMPARISON: EasyDiffraction (fixed) vs Z-Rietveld")
print("=" * 90)
print(f"{'hkl':>5} {'d':>6} {'ZR FWHM':>8} {'ED FWHM':>8} {'ratio':>7} {'ZR peak':>9} {'ED peak':>9} {'peak ratio':>10}")
print("-" * 80)

for hkl, tof_c, d, hw in peaks:
    # ZR peak
    zr_mask = (zr_tof >= tof_c - hw) & (zr_tof <= tof_c + hw)
    zr_t = zr_tof[zr_mask]
    zr_bragg = zr_ycalc[zr_mask] - zr_bg[zr_mask]
    zr_peak_max = np.max(zr_bragg)
    dt_zr = zr_t[1] - zr_t[0]
    zr_fwhm = np.sum(zr_bragg > 0.5 * zr_peak_max) * dt_zr

    # ED peak
    ed_mask = (ed_tof >= tof_c - hw) & (ed_tof <= tof_c + hw)
    if not np.any(ed_mask):
        print(f"{hkl:>5} {d:>6.3f}  -- no ED data in range --")
        continue
    ed_t = ed_tof[ed_mask]
    # Approximate ED background by interpolating between edges
    ed_y = ed_ycalc[ed_mask]
    ed_bg = np.interp(ed_t, [ed_t[0], ed_t[-1]], [ed_y[0], ed_y[-1]])
    ed_bragg = ed_y - ed_bg
    ed_peak_max = np.max(ed_bragg)
    dt_ed = ed_t[1] - ed_t[0] if len(ed_t) > 1 else dt_zr
    ed_fwhm = np.sum(ed_bragg > 0.5 * ed_peak_max) * dt_ed

    ratio_fwhm = ed_fwhm / zr_fwhm if zr_fwhm > 0 else float('inf')
    ratio_peak = ed_peak_max / zr_peak_max if zr_peak_max > 0 else float('inf')
    print(f"{hkl:>5} {d:>6.3f} {zr_fwhm:>8.0f} {ed_fwhm:>8.0f} {ratio_fwhm:>7.3f} {zr_peak_max:>9.5f} {ed_peak_max:>9.5f} {ratio_peak:>10.3f}")

# ── Global pattern statistics ──
active = (ed_tof >= 4001) & (ed_tof <= 40014)
ed_active = ed_ycalc[active]

# Interpolate ZR onto ED grid for comparison
zr_interp = np.interp(ed_tof[active], zr_tof, zr_ycalc)

# Scale ED to match ZR (find optimal scale by least-squares on the active region)
# ED = scale * ed_raw + offset; but we already have scale=8.089773e-5 baked in
# Just compare directly
print(f"\n{'='*90}")
print("GLOBAL PATTERN COMPARISON (TOF 4001-40014)")
print(f"{'='*90}")
print(f"  ED ycalc: min={np.min(ed_active):.6f}, max={np.max(ed_active):.6f}")
print(f"  ZR ycalc: min={np.min(zr_interp):.6f}, max={np.max(zr_interp):.6f}")
print(f"  ED/ZR max ratio: {np.max(ed_active)/np.max(zr_interp):.4f}")

# Shape comparison: normalise both to unit max
ed_norm = ed_active / np.max(ed_active)
zr_norm = zr_interp / np.max(zr_interp)
rms = np.sqrt(np.mean((ed_norm - zr_norm)**2))
print(f"  Normalised RMS difference: {rms:.6f}")

# Rwp-like metric (normalised)
residual = ed_active - zr_interp
w = np.where(zr_interp > 0, 1.0 / zr_interp, 0)
rwp = np.sqrt(np.sum(w * residual**2) / np.sum(w * zr_interp**2)) * 100
print(f"  Rwp(ED vs ZR): {rwp:.2f}%")
