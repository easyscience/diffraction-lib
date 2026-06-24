# pycrysfml feature requests from verification examples

Feature requests to open as individual issues in
`https://github.com/easyscience/deps-pycrysfml/issues`.

Each request below maps to one EasyDiffraction FullProf verification
example and asks for **one main feature** so that pycrysfml can
reproduce that example's calculated powder pattern. For every request,
the only files attached to the issue are the FullProf **`.pcr`** (model
and instrument definition) and **`.dat`** (measured data) — they are
attached purely as a reference for what the feature should produce, not
as files pycrysfml is expected to read.

Source examples live under `docs/docs/verification/fullprof/<example>/`.

---

## Request 1: TOF Jorgensen profile for neutron powder patterns

**Short description:**

Add time-of-flight (TOF) neutron powder-pattern calculation using the
**Jorgensen** peak shape — back-to-back exponentials convoluted with a
Gaussian (FullProf `NPROF=9` with the Lorentzian component switched off,
`Gamma=0`). The example is a constant-time-step TOF Si pattern on the
backscattering bank (`2theta=144.845`), with the peak shape supplied
through a numerical TOF IRF look-up table (`D2TOF`, `Sigma`, `Alpha`,
`Beta`). pycrysfml should map TOF d-spacing to time-of-flight via the
`Dtt1`/`Dtt2`/`Zero` calibration and return the calculated intensity.

- Example: `pd-neut-tof_si_jorgensen`
- Reference files: `arg_si.pcr`, `arg_si.dat`

---

## Request 2: TOF Jorgensen-Von Dreele profile for neutron powder patterns

**Short description:**

Add the **Jorgensen-Von Dreele** TOF peak shape — back-to-back
exponentials convoluted with a full **pseudo-Voigt** (FullProf `NPROF=9`
with a non-zero Lorentzian component, `Gamma>0`). This extends Request 1
with the Lorentzian broadening term so that pycrysfml can select between
the pure-Gaussian Jorgensen profile and the Gaussian+Lorentzian Von
Dreele profile for the same Si TOF backscattering pattern.

- Example: `pd-neut-tof_si_jorgensen-von-dreele`
- Reference files: `arg_si.pcr`, `arg_si.dat`

---

## Request 3: TOF size/strain broadening parameters

**Short description:**

Expose the d-dependent **size and strain broadening** terms of the TOF
peak shape: the Gaussian `Sigma-1`/`Sigma-2` and Lorentzian
`Gamma-1`/`Gamma-2` coefficients (FullProf TOF profile parameters). This
example is identical to the Jorgensen-Von Dreele Si pattern but with
non-zero `Sigma-2` and `Gamma-2`, which widen the peaks through
microstructural (size/strain) broadening. pycrysfml should accept these
coefficients and apply the corresponding d-dependent peak widths.

- Example: `pd-neut-tof_si_jorgensen-von-dreele-size-strain`
- Reference files: `arg_si.pcr`, `arg_si.dat`

---

## Request 4: March-Dollase preferred orientation in CW powder patterns

**Short description:**

Add **March-Dollase preferred-orientation** correction to constant-
wavelength neutron powder patterns. The example is La0.5Ba0.5CoO3 (cubic
`P m -3 m`) with FullProf preferred orientation enabled (`Nor=1`,
`Pref1=1.2`, `Pref2=0.3`). pycrysfml should accept the preferred-
orientation model, the March-Dollase value (`Pref1`), and the random
fraction (`Pref2`) and apply the resulting per-reflection intensity
correction.

- Example: `pd-neut-cwl_lbco_preferred-orientation`
- Reference files: `lbco.pcr`, `lbco.dat`

---

## Request 5: X-ray constant-wavelength powder patterns

**Short description:**

Add **X-ray constant-wavelength** powder-pattern calculation, including
the Cu Kα **two-wavelength doublet** (`Lambda1=1.54056`,
`Lambda2=1.5444`, `Ratio=0.5`) and X-ray Lorentz-polarization. The
example is LiF (`F m -3 m`) measured with a Cu Kα doublet. pycrysfml
should use X-ray scattering factors and the X-ray Lorentz-polarization
factor, and superimpose the two wavelength components at the correct
intensity ratio.

- Example: `pd-xray-cwl_lif`
- Reference files: `lif_doublet_unpolarized.pcr`,
  `lif_doublet_unpolarized.dat`
