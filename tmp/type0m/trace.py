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
for bg_id, bg_x, bg_y in [('1',3000,0.061),('2',6000,0.0384),('3',8000,0.0291),('4',10000,0.0273),('5',12000,0.0206),('6',20000,0.0267),('7',30000,0.0202),('8',40000,0.0157)]:
    expt.background.create(id=bg_id, x=bg_x, y=bg_y)
expt.excluded_regions.create(id='1', start=0, end=4000)
expt.excluded_regions.create(id='2', start=40015, end=100000)

project = Project()
project.structures.add(structure)
project.experiments.add(expt)

# Force a pattern generation first
project.plotter.plot_meas_vs_calc(expt_name='se')

# Access CrysPy calculator internals via experiment
calc = expt.calculator
print("Calculator type:", type(calc).__name__)

# Check the cryspy dict after calculation - just peak params
print("\n=== CrysPy peak params ===")
for combined_name, d in calc._cryspy_dicts.items():
    for k, v in sorted(d.items()):
        if hasattr(v, 'items'):
            for kk, vv in sorted(v.items()):
                kl = kk.lower()
                if any(s in kl for s in ['peak','profile','alpha','beta','sigma','gamma','switch','scale','type0']):
                    vv_str = str(vv)
                    if len(vv_str) > 200:
                        vv_str = vv_str[:200] + '...'
                    print(f"  {kk}: {vv_str}")

# Print the CIF that goes to CrysPy
print("\n=== CrysPy experiment CIF ===")
cif = calc._convert_experiment_to_cryspy_cif(expt, linked_structure=structure)
# Print only the non-data part
cif_lines = cif.split('\n')
for line in cif_lines:
    if line.startswith('loop_') and '_pd_meas' not in line and '_tof_meas' not in line:
        continue
    if any(x in line for x in ['_pd_meas', '_tof_meas']):
        print(f'{line[:80]}...(data loop)')
        break
    print(line)


# Now trigger calculation and check output
project.plotter.plot_meas_vs_calc(expt_name='se')

print("\n=== After calc ===")
y_calc = np.array(expt.data.intensity_calc)
print(f"y_calc: min={np.min(y_calc):.6f}, max={np.max(y_calc):.6f}")
y_bragg = y_calc - np.min(y_calc)  # approximate Bragg-only by subtracting floor
print(f"y_bragg_approx: max={np.max(y_bragg):.6f}")

# Check what CrysPy returns raw (before scale)
from cryspy.procedure_rhochi.rhochi_by_dictionary import rhochi_calc_chi_sq_by_dictionary
cryspy_dict = calc._cryspy_dicts['ceo2_se']
cryspy_in_out = {}
import io, contextlib
with contextlib.redirect_stderr(io.StringIO()):
    rhochi_calc_chi_sq_by_dictionary(
        cryspy_dict,
        dict_in_out=cryspy_in_out,
        flag_use_precalculated_data=False,
        flag_calc_analytical_derivatives=False,
    )

print("\n=== CrysPy raw output ===")
for bname, bdata in cryspy_in_out.items():
    print(f"Block: {bname}")
    for k, v in sorted(bdata.items()):
        if isinstance(v, np.ndarray):
            print(f"  {k}: shape={v.shape}, min={np.min(v):.6e}, max={np.max(v):.6e}")
        else:
            print(f"  {k}: {v}")

# Compare with Z-Rietveld
zr_data = np.loadtxt('tmp/type0m/MAT005500.SE.bin02Double_0_int_c/A.txt', skiprows=1, max_rows=9809)
zr_tof = zr_data[:, 0]
zr_ycalc = zr_data[:, 4]
zr_active = (zr_tof >= 4001) & (zr_tof <= 40015)
zr_max = np.max(zr_ycalc[zr_active])
print(f"\nZ-Rietveld ycalc max: {zr_max:.4f}")
print(f"Z-Rietveld scale from screenshot: 8.089773e-5")
# If CrysPy raw pattern max = X, then:
# ED y_calc = scale * X + bg
# ZR y_calc = scale * X_zr + bg
# So X_zr ≈ (zr_max - bg) / 8.089773e-5
print(f"Implied raw intensity for ZR: {(zr_max - 0.02) / 8.089773e-5:.1f}")
