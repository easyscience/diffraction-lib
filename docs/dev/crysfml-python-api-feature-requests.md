# CrysFML Python API feature requests

This document lists CrysFML capabilities that are present in the
Fortran code on `jrc_branch` but are missing, incomplete, or not wired
through the Python API surface needed by EasyDiffraction tutorials and
verification notebooks.

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
- Add `--plot` to show the hardcoded FullProf reference window and the
  CrysFML CFL result on the same axes.

All scripts use the pycrysfml CFL entry point,
`cfml_py_utilities.patterns_simulation`. Some requests are not fully
representable through a CFL powder-profile call. In particular,
single-crystal extinction and in-memory structure factors need APIs
outside `patterns_simulation`; beta ADPs and CW doublets can be carried
by CFL syntax, so their scripts separate CFL behavior from the remaining
request for equivalent non-CFL Python input paths.

## Request 1: expose preferred orientation in powder patterns

EasyDiffraction uses preferred orientation corrections in powder
verification notebooks, including March-Dollase-style corrections.
CrysFML Fortran contains `Preferred_orientation` in
`Src/CFML_Diffraction.f90` and
`Src/CFML_Diffraction/Pow_Preferred_Orientation.f90`. The CFL phase
data structures also carry preferred-orientation fields.

The Python API does not expose a usable way to set preferred-orientation
parameters for powder pattern simulation. In the latest Fortran pattern
path, the preferred-orientation calls in
`Src/CFML_Utilities/Utilities_Reflections.f90` are still commented out,
so parsed preferred-orientation data is not applied to calculated
reflection corrections.

Requested Python support:

- Accept preferred-orientation model, axes, values, fractions, and
  integration steps in `patterns_simulation` and/or
  `cw_powder_pattern_from_dict`.
- Apply the correction when building reflection correction factors.
- Return clear errors for unsupported preferred-orientation models.

## Request 2: expose absorption and polarization parameters

EasyDiffraction uses sample absorption and X-ray polarization /
monochromator corrections in constant-wavelength powder tutorials and
verification notebooks.

CrysFML Fortran provides the relevant machinery through
`Powder_Lorentz_IntegInt_CW` and `Lorentz_abs_CW` in
`Src/CFML_Diffraction.f90` and
`Src/CFML_Diffraction/Pow_Lorentz_Absorption.f90`. The latest
`patterns_simulation` reflection setup calls `Lorentz_abs_CW`, but with
fixed arguments rather than user-controlled absorption and polarization
inputs.

The registered Python API does not expose direct callables for these
Fortran routines, and the high-level pattern APIs do not let Python
users set the absorption model, `muR`/sample absorption parameter,
monochromator coefficient, monochromator angle, or Lorentz convention.

Requested Python support:

- Expose absorption and polarization controls in the powder pattern API.
- Allow users to choose supported absorption and Lorentz/polarization
  conventions.
- Make the parameters available through both CFL-style and dict-style
  high-level pattern calls where practical.

## Request 3: apply SyCos and SySin in CW pattern simulation

EasyDiffraction verification notebooks cover sample displacement and
transparency terms represented by SyCos and SySin.

CrysFML Fortran parses `ZERO_SY`, `SYCOS`, and `SYSIN` in
`Src/CFML_IOForm/Format_CFL.f90`, and the condition type stores these
values. However, the latest inspected pattern calculation path does not
use `sycos` or `sysin` when placing CW reflections.

Requested Python support:

- Apply parsed `ZERO_SY`, `SYCOS`, and `SYSIN` values in CW reflection
  positions.
- Expose equivalent fields through the dict-style Python API.
- Document the convention and units used for these terms.

## Request 4: expose single-crystal extinction corrections

EasyDiffraction single-crystal tutorials use extinction parameters such
as mosaicity and radius.

CrysFML Fortran contains extinction correction modules under
`Src/CFML_ExtinCorr`, including Becker-Coppens and SHELX-style
corrections. In the Python wrapper source, `Wraps_ExtinCorr.f90` is
empty, and no extinction methods are registered in
`PythonAPI/Fortran/crysfml08lib.f90`.

Requested Python support:

- Provide Python-callable extinction correction routines.
- Support the extinction models already implemented in Fortran.
- Accept reflection data, wavelength/radiation information, and model
  parameters such as mosaicity and radius.
- Return corrected intensities or correction factors with documented
  units and conventions.

## Request 5: expose in-memory structure-factor calculation

EasyDiffraction has in-memory structure and experiment objects and needs
single-crystal and powder structure factors without first writing a CIF
file.

CrysFML Fortran exposes structure-factor machinery through routines such
as `init_structure_factors` and `structure_factors`. The Python API
currently exposes `structure_factors_from_cif`, which requires a CIF or
MCIF file path, but does not expose an equivalent high-level API for an
already constructed Python dictionary, wrapped crystal object, cell,
space group, atom list, and reflection list.

Requested Python support:

- Add a high-level `structure_factors_from_dict` or equivalent
  in-memory API.
- Accept radiation type, wavelength, reflection range, uniqueness, and
  Friedel options.
- Return reflection indices, multiplicity, structure factors, and
  intensities in a stable Python data shape.

## Request 6: carry anisotropic and beta ADPs through Python APIs

EasyDiffraction verification includes anisotropic displacement
parameters, including beta-style ADPs.

CrysFML Fortran atom types support anisotropic displacement parameters
through `UType` values such as `U_ij`, `B_ij`, and `beta`; CIF and CFL
readers parse anisotropic displacement data. The dict-style Python
powder path in `Src/CFML_Py_Utilities/Py_Utilities_Patterns.f90`
currently reads only `_B_iso_or_equiv` for atoms.

Requested Python support:

- Accept anisotropic ADP tensors in dict-style structure input.
- Preserve the ADP convention (`U_ij`, `B_ij`, or `beta`) explicitly.
- Use anisotropic ADPs in structure-factor and powder-pattern
  calculations where the Fortran code already supports them.

## Request 7: complete TOF support in `patterns_simulation`

EasyDiffraction tutorials and verification notebooks use TOF powder
patterns with calibration terms and Jorgensen/Jorgensen-von-Dreele peak
parameters.

CrysFML Fortran parses TOF CFL fields such as `D2TOF`, `ALPHA`, `BETA`,
`SIGMA`, `GAMMA`, and `TOF_RANGE`. The dict API exposes
`tof_powder_pattern_from_dict`, and the Fortran utility code implements a
TOF powder profile calculation. However, the CFL
`patterns_simulation` path still lacks the TOF profile contribution in
`compute_patterns`, so Python callers using CFL-style pattern simulation
cannot obtain TOF intensities through that path.

Requested Python support:

- Make `patterns_simulation` calculate TOF powder intensities from CFL
  pattern blocks.
- Use the parsed TOF profile/calibration parameters.
- Keep behavior consistent with `tof_powder_pattern_from_dict`.

## Request 8: expose TOF profile selection

EasyDiffraction distinguishes Jorgensen and Jorgensen-von-Dreele TOF
profile models in tutorials and verification notebooks.

CrysFML Fortran profile code includes multiple TOF profile functions,
including Jorgensen, Jorgensen-von-Dreele, and Carpenter-style profiles.
The dict-style Python TOF utility path is currently fixed to
`tof_Jorgensen_VonDreele`.

Requested Python support:

- Allow Python callers to select the TOF profile function.
- Validate that the required parameters for the selected profile are
  present.
- Document how the profile names map to Fortran routines and CFL
  `PROFILE_FUNCTION` values.

## Request 9: expose native CW doublet support in dict APIs

EasyDiffraction X-ray tutorials and verification notebooks use
two-wavelength constant-wavelength patterns.

The latest inspected Fortran CFL pattern path supports two wavelengths:
reflection contributions are duplicated when `twowaves` is set, and the
second wavelength ratio is applied. The dict-style Python CW pattern path
currently reads only `_diffrn_radiation_wavelength` and does not expose
second-wavelength and ratio inputs.

Requested Python support:

- Add second wavelength and wavelength-ratio fields to
  `cw_powder_pattern_from_dict`.
- Align dict-style behavior with the CFL `LAMBDA lambda1 lambda2 ratio`
  behavior.
- Document whether the ratio is interpreted as `I2/I1`.

## Out of scope for this request list

The following EasyDiffraction needs were inspected but are not included
above because they were not found as existing Fortran capabilities in
the inspected CrysFML source:

- Berar-Baldinozzi empirical asymmetry (`asym_beba_*`).
- PDF / total-scattering calculations equivalent to PDFfit-style
  `broad_q`, `damp_q`, and `sharp_delta_*` parameters.
