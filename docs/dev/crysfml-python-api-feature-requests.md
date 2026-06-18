# CrysFML Python API feature requests

This is a request to add the following functionality into the CrysFML
Python API (`pycrysfml`). The goal is to expose through Python the
CrysFML/Fortran functionality that EasyDiffraction needs in tutorials
and verification notebooks, and to make Python results match FullProf
for the same physical model.

Reference checkout:

- Repository: `https://code.ill.fr/scientific-software/CrysFML2008.git`
- Branch: `jrc_branch`
- Commit inspected locally: `c8dd82b`

Installed Python package inspected locally:

- Package: `crysfml`
- Version: `0.7.0`

Evidence scripts:

- Directory: `docs/dev/crysfml-python-api-requests/`
- Run one example with
  `pixi run python docs/dev/crysfml-python-api-requests/request_01_preferred_orientation.py`.
- Add `--plot` to display the request screenshot.

All screenshots follow the same evidence contract:

- Every request asks for one feature only.
- Every chart has exactly two vertical panels: without the requested
  feature and with the requested feature.
- Every profile panel uses the Y2O3 verification sample from
  `docs/docs/verification/fullprof/pd-neut-cwl_y2o3_beta-adp/`.
- Every embedded FullProf profile is the Bragg-only calculated
  intensity from 56.00 to 60.00 degrees 2theta, step 0.05.
- The plotting helper uses panels 1.5x taller than the previous
  evidence scripts.

Generated FullProf PCR inputs for the requests that have a meaningful
powder-pattern toggle are stored in
`docs/dev/crysfml-python-api-requests/fullprof/`. They were generated
from the bundled Y2O3 verification PCR. To rerun one manually, copy the
verification `y2o3.dat` beside the PCR using the same basename, then run
`fp2k <basename>`.

Some requests are Python API transport gaps rather than FullProf powder
feature toggles. Those scripts still use the common Y2O3 two-panel
chart: the first panel is the powder-CFL control, and the second panel
records the missing API surface explicitly.

## Request 1: preferred orientation in powder patterns

Please add preferred-orientation support to the CrysFML Python powder
pattern API. Python callers should be able to set the preferred
orientation model, direction, correction value, random fraction, and any
model-specific integration parameters.

Short description:

EasyDiffraction uses March-Dollase-style preferred orientation in powder
verification notebooks. The CrysFML Fortran source contains preferred
orientation routines, but the inspected Python CFL pattern path does not
apply preferred-orientation correction factors during reflection setup.

FullProf `.pcr` setting used in the feature-on reference:

```text
!  Pref1    Pref2      Asy1     Asy2     Asy3     Asy4      S_L      D_L
  1.20000  0.30000  0.00000  0.00000  0.00000  0.00000  0.00000  0.00000
```

Evidence:

- PCRs: `fullprof/y2o3_control_beta.pcr`,
  `fullprof/y2o3_preferred_orientation.pcr`
- Script:
  `docs/dev/crysfml-python-api-requests/request_01_preferred_orientation.py`
- Screenshot caption: "Y2O3 powder CW control agrees without preferred
  orientation; with FullProf `Pref1=1.2`, `Pref2=0.3`, pycrysfml has no
  equivalent Python/CFL knob to reproduce the feature-on panel."

## Request 2: cylindrical absorption

Please add user-controlled cylindrical sample absorption to the CrysFML
Python powder pattern API.

Short description:

EasyDiffraction needs Debye-Scherrer/Hewat-style cylindrical absorption
for powder samples. CrysFML Fortran provides absorption machinery, but
the inspected Python high-level pattern APIs do not expose `muR`.

FullProf `.pcr` setting used in the feature-on reference:

```text
! Lambda1  Lambda2    Ratio    Bkpos    Wdt    Cthm     muR   AsyLim   Rpolarz
 1.548220 1.548220  0.00000   10.000 20.0000  0.0000  0.9000  160.00    0.0000
```

Evidence:

- PCRs: `fullprof/y2o3_control_beta.pcr`,
  `fullprof/y2o3_absorption.pcr`
- Script: `docs/dev/crysfml-python-api-requests/request_02_absorption.py`
- Screenshot caption: "Y2O3 powder CW control agrees without
  cylindrical absorption; with FullProf `muR=0.9`, pycrysfml has no
  exposed user-controlled absorption parameter."

## Request 3: X-ray polarization

Please add user-controlled X-ray polarization and monochromator
parameters to the CrysFML Python powder pattern API.

Short description:

EasyDiffraction uses X-ray polarization/monochromator corrections.
CrysFML Fortran provides the relevant Lorentz/polarization machinery,
but the inspected Python high-level pattern APIs do not expose the
polarization coefficient, monochromator angle, or convention selection.

FullProf `.pcr` setting used in the feature-on reference:

```text
! Lambda1  Lambda2    Ratio    Bkpos    Wdt    Cthm     muR   AsyLim   Rpolarz
 1.540560 1.540560  0.00000   50.000 20.0000  0.8000  0.0000  160.00    0.5000
```

Evidence:

- PCRs: `fullprof/y2o3_xray_single.pcr`,
  `fullprof/y2o3_polarization.pcr`
- Script:
  `docs/dev/crysfml-python-api-requests/request_03_polarization.py`
- Screenshot caption: "Y2O3 X-ray CW control agrees without
  polarization; with FullProf `Cthm=0.8`, `Rpolarz=0.5`, pycrysfml has
  no equivalent Python/CFL inputs."

## Request 4: SyCos and SySin CW peak-position shifts

Please make the CrysFML Python CW pattern API apply `Zero_Sy`, `SyCos`,
and `SySin` when calculating reflection positions.

Short description:

CrysFML parses `ZERO_SY`, `SYCOS`, and `SYSIN` from CFL text, but the
inspected `patterns_simulation` path does not use the `SyCos`/`SySin`
values when placing CW reflections.

FullProf `.pcr` setting used in the feature-on reference:

```text
!  Zero    Code    SyCos    Code   SySin    Code  Lambda     Code MORE
 -0.01625    0.0  0.01153    0.0  0.24334    0.0 0.000000    0.00   0
```

Evidence:

- PCRs: `fullprof/y2o3_control_beta.pcr`,
  `fullprof/y2o3_sycos_sysin.pcr`
- Script:
  `docs/dev/crysfml-python-api-requests/request_04_sycos_sysin.py`
- Screenshot caption: "Y2O3 powder CW control agrees with
  `SyCos=0`, `SySin=0`; after FullProf enables `SyCos=0.01153`,
  `SySin=0.24334`, pycrysfml still follows the unshifted positions."

## Request 5: single-crystal extinction corrections

Please expose single-crystal extinction corrections through the CrysFML
Python API.

Short description:

EasyDiffraction single-crystal verification uses extinction parameters
such as radius/mosaicity or an equivalent model parameter. CrysFML
Fortran contains extinction correction modules under
`Src/CFML_ExtinCorr`, but the inspected Python wrapper does not register
Python-callable extinction routines.

Python functionality requested:

```text
extinction model parameters + hkl/intensity input
-> corrected intensities or correction factors
```

Evidence:

- Common control PCR: `fullprof/y2o3_control_beta.pcr`
- Script:
  `docs/dev/crysfml-python-api-requests/request_05_single_crystal_extinction.py`
- Screenshot caption: "The first Y2O3 powder CW panel is the common
  control. The second panel records that pycrysfml has no callable
  single-crystal extinction API for corrected integrated intensities or
  correction factors."

## Request 6: in-memory structure-factor calculation

Please add a Python API that calculates structure factors from in-memory
Python data, without requiring an intermediate CIF or MCIF file.

Short description:

EasyDiffraction already has in-memory cells, space groups, atom lists,
experiments, and reflection lists. The Python API exposes
`structure_factors_from_cif`, but not an equivalent
`structure_factors_from_dict` or object-based function.

Python functionality requested:

```text
cell + space group + atom list + hkl list + radiation settings
-> h, k, l, multiplicity, F, F^2, intensity
```

Evidence:

- Common control PCR: `fullprof/y2o3_control_beta.pcr`
- Script:
  `docs/dev/crysfml-python-api-requests/request_06_in_memory_structure_factors.py`
- Screenshot caption: "The first Y2O3 powder CW panel is the common
  control. The second panel records that pycrysfml has no in-memory
  structure-factor API equivalent to the CIF/MCIF file-based path."

## Request 7: anisotropic and beta ADPs in Python inputs

Please make anisotropic ADP tensors, including beta-style ADPs,
available through CrysFML Python high-level inputs.

Short description:

CrysFML CFL atom records can carry `BETA`, `U_IJ`, and `B_IJ` tensor
records, but the inspected dict-style Python powder path reads only
`_B_iso_or_equiv`. EasyDiffraction needs the non-CFL Python API to carry
the ADP convention and tensor components explicitly.

FullProf `.pcr` setting used in the feature-on reference:

```text
!Atom   Typ       X        Y        Z     Biso       Occ     In Fin N_t Spc
Y1     Y      -0.03236  0.00000  0.25000  0.00000   0.50000   0   0   2    0
!    beta11   beta22   beta33   beta12   beta13   beta23
      0.00303  0.00272  0.00295  0.00000  0.00000  -0.00025
```

Evidence:

- PCRs: `fullprof/y2o3_isotropic_adp.pcr`,
  `fullprof/y2o3_control_beta.pcr`
- Script: `docs/dev/crysfml-python-api-requests/request_07_beta_adps.py`
- Screenshot caption: "Y2O3 powder CW control uses isotropic atom
  records; the feature-on panel enables FullProf `N_t=2` beta tensors.
  The remaining request is to expose equivalent tensor input through the
  non-CFL Python API."

## Request 8: TOF support in `patterns_simulation`

Please complete TOF powder-pattern support in the CrysFML Python CFL
entry point `cfml_py_utilities.patterns_simulation`.

Short description:

CrysFML parses TOF CFL fields such as `D2TOF`, `ALPHA`, `BETA`, `SIGMA`,
`GAMMA`, and `TOF_RANGE`, and the Fortran code contains TOF profile
machinery. The inspected Python CFL `patterns_simulation` path does not
produce TOF intensities from a TOF CFL block.

CFL functionality requested:

```text
Patt_Type  Neutrons Powder TOF
Profile_function  tof_Jorgensen_VonDreele
D2TOF / ALPHA / BETA / SIGMA / GAMMA / TOF_RANGE parameters
```

Evidence:

- Common control PCR: `fullprof/y2o3_control_beta.pcr`
- Script:
  `docs/dev/crysfml-python-api-requests/request_08_tof_patterns_simulation.py`
- Screenshot caption: "The first Y2O3 powder CW panel is the common
  control. The second panel records that the pycrysfml CFL TOF block
  raises or returns no matching TOF intensities."

## Request 9: TOF profile selection

Please expose TOF profile-function selection through the CrysFML Python
API.

Short description:

EasyDiffraction verification distinguishes Jorgensen and
Jorgensen-von-Dreele TOF profiles. The inspected dict-style Python TOF
path is fixed to one profile, and CFL TOF profile selection cannot yet
be validated until request 8 makes TOF CFL intensities work.

CFL functionality requested:

```text
Profile_function  tof_Jorgensen
Profile_function  tof_Jorgensen_VonDreele
```

Evidence:

- Common control PCR: `fullprof/y2o3_control_beta.pcr`
- Script:
  `docs/dev/crysfml-python-api-requests/request_09_tof_profile_selection.py`
- Screenshot caption: "The first Y2O3 powder CW panel is the common
  control. The second panel records that TOF profile-function selection
  is not exposed through the inspected Python API."

## Request 10: CW doublet support in dict APIs

Please expose native CW two-wavelength/doublet input through
`cw_powder_pattern_from_dict` and any equivalent high-level Python API.

Short description:

The CFL path has `LAMBDA lambda1 lambda2 ratio` syntax, while the
dict-style Python CW path reads only one wavelength. EasyDiffraction
needs the Python dict API to accept the second wavelength and the
relative intensity ratio.

FullProf `.pcr` setting used in the feature-on reference:

```text
! Lambda1  Lambda2    Ratio
 1.540560 1.544400  0.50000
```

Evidence:

- PCRs: `fullprof/y2o3_xray_single.pcr`,
  `fullprof/y2o3_doublet.pcr`
- Script:
  `docs/dev/crysfml-python-api-requests/request_10_cw_doublet_dict_api.py`
- Screenshot caption: "Y2O3 X-ray CW control agrees for a single
  wavelength. The feature-on panel enables `Lambda2=1.5444`,
  `Ratio=0.5`; the CFL string can express this, but the dict API has no
  equivalent input fields."

## Out of scope for this request list

The following EasyDiffraction needs were inspected but are not included
above because they were not found as existing Fortran capabilities in
the inspected CrysFML source:

- Berar-Baldinozzi empirical asymmetry (`asym_beba_*`).
- PDF / total-scattering calculations equivalent to PDFfit-style
  `broad_q`, `damp_q`, and `sharp_delta_*` parameters.
