# 168. Decide X-ray Anomalous Scattering Table Source

**Priority:** `[priority] highest`

**Type:** Correctness / External backend / Verification

The PbSO4 X-ray verification discrepancy is dominated by the anomalous
dispersion table, especially Pb `f'`. The calculators and references do
not all use the same source table, so EasyDiffraction needs an explicit
decision: reproduce a reference backend exactly, or use an evaluated
physical table.

**Observed values at Cu Kα (`λ = 1.540560 Å`, `E = 8047.995 eV`):**

Convention used here: online `f1` values are converted to
crystallographic `f'` as `f1 - Z`; `f''` corresponds to `f2`.

| Element | Source                |    `f'` |  `f''` |
| ------- | --------------------- | ------: | -----: |
| O       | FullProf / CrysFML    |  0.0470 | 0.0320 |
| O       | cctbx Sasaki          |  0.0464 | 0.0322 |
| O       | cryspy                |  0.0492 | 0.0322 |
| O       | CXRO / Henke          |  0.0523 | 0.0337 |
| O       | cctbx Henke           |  0.0523 | 0.0337 |
| O       | NIST FFAST / Chantler |  0.0520 | 0.0320 |
| S       | FullProf / CrysFML    |  0.3190 | 0.5570 |
| S       | cctbx Sasaki          |  0.3191 | 0.5567 |
| S       | cryspy                |  0.3331 | 0.5567 |
| S       | CXRO / Henke          |  0.3351 | 0.5505 |
| S       | cctbx Henke           |  0.3351 | 0.5505 |
| S       | NIST FFAST / Chantler |  0.3474 | 0.5545 |
| Pb      | FullProf / CrysFML    | -4.8180 | 8.5050 |
| Pb      | cctbx Sasaki          | -4.8180 | 8.5018 |
| Pb      | cryspy                | -4.0753 | 8.5060 |
| Pb      | CXRO / Henke          | -3.7276 | 8.9350 |
| Pb      | cctbx Henke           | -3.7276 | 8.9350 |
| Pb      | NIST FFAST / Chantler | -3.1764 | 8.4175 |

**Local source findings:**

- CrysFML hard-codes line-specific anomalous factors for
  `Cr, Fe, Cu, Mo, Ag` in
  `tmp/crysfml/CFML/Src/CFML_Tables/Tab_Set_ScatterT.f90`. Its Cu values
  match FullProf for the PbSO4 verification case.
- cryspy interpolates its `DATABASE["Dispersion"]` table by wavelength
  in `tmp/cryspy/github/cryspy/A_functions_base/structure_factor.py` and
  `tmp/cryspy/github/cryspy/E_data_classes/cl_1_crystal.py`.
- The normal X-ray form-factor coefficients are not the source of the
  PbSO4 mismatch; the important difference is anomalous dispersion.

**External source findings:**

- NIST FFAST / Chantler provides evaluated `f1`/`f2` tabulations in
  Standard Reference Database 66:
  <https://www.nist.gov/pml/x-ray-form-factor-attenuation-and-scattering-tables>
  and <https://physics.nist.gov/PhysRefData/FFast/form.html>.
- CXRO / Henke provides element files with `Energy(eV), f1, f2` columns:
  <https://henke.lbl.gov/optical_constants/asf.html>.
- xraylib exposes published X-ray interaction datasets, including form
  factors and anomalous scattering functions:
  <https://github.com/tschoonj/xraylib/wiki>.
- DABAX provides Python access to X-ray database files used for
  scattering functions and related material-photon data:
  <https://github.com/oasys-kit/dabax>.
- cctbx has two relevant `eltbx` table families:
  - `cctbx/eltbx/sasaki.h`: Sasaki 1989, Cromer-Liberman method, 4-124
    keV, with fine steps near K/L edges:
    <https://github.com/cctbx/cctbx_project/blob/master/cctbx/eltbx/sasaki.h>.
  - `cctbx/eltbx/henke.h`: Henke / Gullikson / Davis, 10-30000 eV, based
    on photoabsorption measurements and Kramers-Kronig real-part
    reconstruction:
    <https://github.com/cctbx/cctbx_project/blob/master/cctbx/eltbx/henke.h>.
  - `cctbx/eltbx/fp_fdp.h` exposes `fp()` / `fdp()` values:
    <https://github.com/cctbx/cctbx_project/blob/master/cctbx/eltbx/fp_fdp.h>.
    Numeric comparison above was computed from cctbx reference data
    under `cctbx/reference/henke/tables` and `cctbx/reference/sasaki`,
    using the interpolation rules in the source generators.

**Sasaki vs Henke:**

- Sasaki is a Cromer-Liberman-style calculated anomalous-dispersion
  table. cctbx stores it directly as `f'`/`f''`, with broad coverage
  from 4 to 124 keV and extra resolution near K/L absorption edges. For
  the Cu Kα PbSO4 case it is effectively the FullProf / CrysFML
  compatibility family.
- Henke is an optical-constants table based on photoabsorption data:
  `f''` is tied to absorption measurements and the real component is
  reconstructed via Kramers-Kronig relations. The source tabulates
  `f1`/`f2`; crystallographic `f'` is `f1 - Z`. cctbx Henke matches the
  CXRO / Henke values used in the comparison table.

**Backend wavelength behaviour:**

- cryspy supports arbitrary X-ray wavelengths for anomalous dispersion:
  it stores `DATABASE["Dispersion"]["table_wavelength"]` and
  interpolates each atom's complex dispersion value with `numpy.interp`
  at the requested wavelength.
- CrysFML accepts a wavelength, but it does not interpolate anomalous
  dispersion continuously. In
  `tmp/crysfml/CFML/Src/CFML_Structure_Factors/SF_Scattering_Species.f90`
  and `SF_Create_Tables.f90`, the code selects the nearest Kα1 row from
  five fixed anomalous tables (`Cr`, `Fe`, `Cu`, `Mo`, `Ag`) and uses
  that row's `f'`/`f''`.
- Implication: for cryspy, changing wavelength changes anomalous
  dispersion continuously; for CrysFML, changing wavelength only changes
  anomalous dispersion when the nearest fixed lab-line row changes.

**Interpretation:**

- FullProf / CrysFML is the correct table for FullProf-compatibility
  verification.
- cctbx Sasaki is effectively the same compatibility family as FullProf
  / CrysFML for this Cu Kα case.
- cctbx Henke matches the CXRO / Henke values.
- cryspy is closer than FullProf / CrysFML to the public evaluated CXRO
  and NIST values for Pb `f'`, although it does not match either table
  exactly.
- NIST and CXRO disagree noticeably for Pb near Cu Kα, so "the correct
  table" is not unique. The chosen source must be explicit.
- Do not silently replace cryspy values with FullProf / CrysFML values
  as a physics correction. That is a compatibility override, not a
  better evaluated table.

**TODOs / decision points:**

- Document the intended anomalous-dispersion source for each backend in
  X-ray verification pages.
- Add a small diagnostic comparing backend-native, FullProf-compatible,
  CXRO / Henke, NIST / Chantler, and cctbx Sasaki / Henke values for
  representative elements near common lab wavelengths.
- Decide whether EasyDiffraction needs a user-facing anomalous table
  source, for example `backend_native`, `fullprof_compatibility`,
  `nist_chantler`, `cxro_henke`, and `cctbx_sasaki`.
- Keep FullProf-aligned overrides confined to verification or an
  explicitly named compatibility mode.
- If a user-facing source is added, decide whether this belongs in an
  X-ray-specific experiment/instrument category and exclude it from
  neutron experiments.

**Recommended-priority note:** Marked **highest** because the current
PbSO4 X-ray backend discrepancy can be misdiagnosed as a profile,
polarization, or wavelength bug unless the anomalous table source is
made explicit.
