# CrysFML Python API feature requests

This is a request to add the following functionality into the CrysFML
Python API (`pycrysfml`). The goal is to expose through Python the
CrysFML/Fortran functionality that EasyDiffraction already needs in its
tutorials and verification notebooks, and to make the Python results
match FullProf for the same physical model.

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
- Add `--plot` to display the hardcoded FullProf reference window and
  the CrysFML CFL result on the same axes.

Each script is intended to be attached to the upstream request together
with a screenshot. The screenshot should show two cases:

- Agreement before the requested feature is enabled.
- Disagreement after the feature is enabled in the FullProf `.pcr` and
  represented, or attempted, through the CrysFML Python/CFL path.

Some requests are not fully representable by the current powder CFL
`patterns_simulation` entry point. For those cases, the related script
shows a working powder-CFL control first and then documents the missing
Python API surface explicitly.

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

CFL-side functionality requested:

```text
! Desired pycrysfml/CFL support:
! preferred-orientation model = March-Dollase
! preferred-orientation axis  = 0 0 1
! preferred-orientation value = 1.2
! random fraction             = 0.3
```

Related script and screenshot:

- Script:
  `docs/dev/crysfml-python-api-requests/request_01_preferred_orientation.py`
- Screenshot caption:
  "LBCO powder CW control agrees when preferred orientation is off; the
  same CFL calculation disagrees with the FullProf `.pcr` when
  `Pref1=1.2`, `Pref2=0.3`, axis `[0 0 1]` is enabled."

## Request 2: absorption and polarization parameters

Please add user-controlled absorption and X-ray polarization parameters
to the CrysFML Python powder pattern API.

Short description:

EasyDiffraction uses cylindrical sample absorption and X-ray
polarization/monochromator corrections. CrysFML Fortran provides the
Lorentz/absorption machinery, but the inspected Python high-level
pattern APIs do not expose `muR`, polarization coefficient,
monochromator angle, or convention selection.

FullProf `.pcr` settings used in the feature-on references:

```text
! Lambda1  Lambda2    Ratio    Bkpos    Wdt    Cthm     muR   AsyLim   Rpolarz
 1.540560 1.540560  0.00000   50.000 48.0000  0.8000  0.0000  160.00    0.5000

! Lambda1  Lambda2    Ratio    Bkpos    Wdt    Cthm     muR   AsyLim   Rpolarz
 1.540560 1.540560  0.00000   50.000 48.0000  0.0000  0.9000  160.00    0.0000
```

CFL-side functionality requested:

```text
! Desired pycrysfml/CFL support:
! polarization coefficient = 0.5
! monochromator Cthm       = 0.8
! absorption model         = Debye-Scherrer cylinder / Hewat
! muR                      = 0.9
```

Related script and screenshot:

- Script:
  `docs/dev/crysfml-python-api-requests/request_02_absorption_polarization.py`
- Screenshot caption:
  "LiF X-ray CW control agrees without absorption/polarization; the same
  CFL calculation disagrees when FullProf enables `Rpolarz=0.5`,
  `Cthm=0.8`, or `muR=0.9` because those parameters are not exposed in
  pycrysfml."

## Request 3: SyCos and SySin CW peak-position shifts

Please make the CrysFML Python CW pattern API apply `Zero_Sy`, `SyCos`,
and `SySin` when calculating reflection positions.

Short description:

CrysFML parses `ZERO_SY`, `SYCOS`, and `SYSIN` from CFL text, but the
inspected `patterns_simulation` path does not use the `SyCos`/`SySin`
values when placing CW reflections.

FullProf `.pcr` setting used in the feature-on reference:

```text
!  Zero    Code    SyCos    Code   SySin    Code  Lambda     Code MORE
 -0.45778    0.0  0.01153    0.0  0.24334    0.0 1.623899    0.00   0
```

CFL string with the requested functionality set:

```text
Zero_Sy  0.0  0.01153  0.24334
```

Related script and screenshot:

- Script:
  `docs/dev/crysfml-python-api-requests/request_03_sycos_sysin.py`
- Screenshot caption:
  "LaB6 powder CW control agrees for `SyCos=0`, `SySin=0`; after FullProf
  enables `SyCos=0.01153`, `SySin=0.24334`, pycrysfml still follows the
  unshifted CFL positions."

## Request 4: single-crystal extinction corrections

Please expose single-crystal extinction corrections through the CrysFML
Python API.

Short description:

EasyDiffraction single-crystal verification uses extinction parameters
such as radius/mosaicity or an equivalent model parameter. CrysFML
Fortran contains extinction correction modules under `Src/CFML_ExtinCorr`,
but the inspected Python wrapper does not register Python-callable
extinction routines.

FullProf `.pcr` setting used in the feature-on reference:

```text
!  Extinction Parameters
!   Ext1        Ext2        Ext3        Ext4        Ext5        Ext6        Ext7   Ext-Model
  0.1834       0.000       0.000       0.000       0.000       0.000       0.000       1
```

CFL/Python functionality requested:

```text
! No powder CFL setting can represent this request today.
! Desired pycrysfml support:
! extinction model parameters + hkl/intensity input -> corrected
! intensities or correction factors
```

Related script and screenshot:

- Script:
  `docs/dev/crysfml-python-api-requests/request_04_single_crystal_extinction.py`
- Screenshot caption:
  "The script first shows a powder-CFL control agreement. It then shows
  FullProf single-crystal integrated intensities before and after
  extinction is enabled; pycrysfml has no callable extinction API to
  reproduce the feature-on table."

## Request 5: in-memory structure-factor calculation

Please add a Python API that calculates structure factors from in-memory
Python data, without requiring an intermediate CIF or MCIF file.

Short description:

EasyDiffraction already has in-memory cells, space groups, atom lists,
experiments, and reflection lists. The Python API exposes
`structure_factors_from_cif`, but not an equivalent
`structure_factors_from_dict` or object-based function.

FullProf reference used by the evidence script:

```text
! FullProf integrated intensities are used as the reference hkl window.
! This is not a FullProf feature toggle; it is an API transport gap.
```

CFL/Python functionality requested:

```text
! No CFL string should be required.
! Desired pycrysfml support:
! cell + space group + atom list + hkl list + radiation settings
! -> h, k, l, multiplicity, F, F^2, intensity
```

Related script and screenshot:

- Script:
  `docs/dev/crysfml-python-api-requests/request_05_in_memory_structure_factors.py`
- Screenshot caption:
  "The script first shows a powder-CFL control agreement. It then shows
  the FullProf hkl/intensity window that should be calculable from
  in-memory Python objects; pycrysfml currently has no equivalent API."

## Request 6: anisotropic and beta ADPs in Python inputs

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

CFL string with the requested functionality set:

```text
Atom  Y1  Y  -0.03236  0.0  0.25  0.0  0.5
BETA  0.00303  0.00272  0.00295  0.0  0.0  -0.00025
```

Related script and screenshot:

- Script: `docs/dev/crysfml-python-api-requests/request_06_beta_adps.py`
- Screenshot caption:
  "Y2O3 powder CW control uses isotropic atom records; the feature-on
  reference sets FullProf `N_t=2` beta tensors and the CFL `BETA` lines.
  The remaining request is to expose equivalent tensor input through the
  non-CFL Python API."

## Request 7: TOF support in `patterns_simulation`

Please complete TOF powder-pattern support in the CrysFML Python CFL
entry point `cfml_py_utilities.patterns_simulation`.

Short description:

CrysFML parses TOF CFL fields such as `D2TOF`, `ALPHA`, `BETA`, `SIGMA`,
`GAMMA`, and `TOF_RANGE`, and the Fortran code contains TOF profile
machinery. The inspected Python CFL `patterns_simulation` path does not
produce TOF intensities from a TOF CFL block.

FullProf `.pcr` settings used in the feature-on reference:

```text
!    Zero       Code      Dtt1      Code       Dtt2     Code  Dtt_1overd
    -9.18766    0.00  7476.91016    0.00    -1.54000    0.00     0.00000

!      Sigma-2       Sigma-1       Sigma-0       Sigma-Q
        0.0000       33.0419        3.5544        0.0000
!      Gamma-2       Gamma-1       Gamma-0
        0.0000        2.5430        0.0000
!      Pref1      Pref2        alph0       beta0       alph1       beta1
    0.000000    0.000000    0.000000    0.042210    0.597100    0.009460
```

CFL string with the requested functionality set:

```text
Patt_Type  Neutrons Powder TOF
Profile_function  tof_Jorgensen_VonDreele
D2TOF  -9.18766  7476.91016  -1.54  0.0
ALPHA  0.0  0.5971  0.0
BETA  0.04221  0.00946  0.0
SIGMA  0.0  33.0419  3.5544  0.0
GAMMA  0.0  2.543  0.0
TOF_RANGE  12000.0  14600.0  5.0
```

Related script and screenshot:

- Script:
  `docs/dev/crysfml-python-api-requests/request_07_tof_patterns_simulation.py`
- Screenshot caption:
  "The script first shows a CW powder control agreement. The TOF FullProf
  `.pcr` enables D2TOF/profile parameters, while the pycrysfml CFL TOF
  block raises/returns no matching TOF intensities."

## Request 8: TOF profile selection

Please expose TOF profile-function selection through the CrysFML Python
API.

Short description:

EasyDiffraction verification distinguishes Jorgensen and
Jorgensen-von-Dreele TOF profiles. The inspected dict-style Python TOF
path is fixed to one profile, and CFL TOF profile selection cannot yet be
validated until request 7 makes TOF CFL intensities work.

FullProf `.pcr` setting used in the feature-on reference:

```text
! Jorgensen FullProf reference uses the Jorgensen profile parameter set:
! Sigma-2 Sigma-1 Sigma-0 and alph0 beta0 alph1 beta1.
```

CFL string with the requested functionality set:

```text
Profile_function  tof_Jorgensen
D2TOF  -8.56733  7476.91016  -1.54  0.0
ALPHA  0.0  0.235422  0.0
BETA  0.03802  0.010902  0.0
SIGMA  0.0  29.6492  5.079  0.0
```

Related script and screenshot:

- Script:
  `docs/dev/crysfml-python-api-requests/request_08_tof_profile_selection.py`
- Screenshot caption:
  "The script first shows a CW powder control agreement. It then compares
  FullProf Jorgensen-von-Dreele and Jorgensen TOF references with CFL
  `Profile_function` settings; pycrysfml cannot yet demonstrate profile
  selection because TOF CFL intensities are missing."

## Request 9: CW doublet support in dict APIs

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

CFL string with the requested functionality set:

```text
LAMBDA  1.54056  1.5444  0.5
```

Related script and screenshot:

- Script: `docs/dev/crysfml-python-api-requests/request_09_cw_doublet_dict_api.py`
- Screenshot caption:
  "LiF X-ray CW control agrees for a single wavelength. The FullProf
  `.pcr` enables the doublet with `Lambda2=1.5444`, `Ratio=0.5`; the CFL
  string can express `LAMBDA lambda1 lambda2 ratio`, but the dict API has
  no equivalent input fields."

## Out of scope for this request list

The following EasyDiffraction needs were inspected but are not included
above because they were not found as existing Fortran capabilities in
the inspected CrysFML source:

- Berar-Baldinozzi empirical asymmetry (`asym_beba_*`).
- PDF / total-scattering calculations equivalent to PDFfit-style
  `broad_q`, `damp_q`, and `sharp_delta_*` parameters.
