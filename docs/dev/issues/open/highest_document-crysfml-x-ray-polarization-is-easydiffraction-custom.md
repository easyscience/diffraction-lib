# 170. Document CrysFML X-ray Polarization as EasyDiffraction-Custom

**Priority:** `[priority] highest`

**Type:** Correctness / External backend / Verification

EasyDiffraction currently applies X-ray Lorentz-polarization handling to
the CrysFML calculator as a calculator-independent pointwise correction
after the CrysFML Python CFL calculation returns the convolved profile.
That is **not** a native CrysFML CFL binding.

**Source finding:** CrysFML's CW CFL pattern-condition parser accepts
`WDT`, `ASYM`, `LAMBDA`, `PROFILE_FUNCTION`, `THETA_RANGE`, `UVWXY`,
`ZERO_SY`, `ZERO`, `SYCOS`, and `SYSIN`, but no direct `CTHM`, `RKK`,
`Rpolarz`, or polarization keyword. CrysFML does read `CTHM` and `RKK`
through its separate IRF reader, but the Python-facing
`patterns_simulation(strings)` path used by EasyDiffraction calls
`read_cfl_pattern` and does not call `Read_Patt_IRF`, so those IRF
fields are not consumed by the current CFL API route.

**Implication:** verification pages and user-facing documentation must
not imply that `crysfml` receives polarization through native CFL input.
For now, `crysfml` polarization in EasyDiffraction is our own
post-processing convention. It should be described as such until either
CrysFML exposes a native Python/CFL polarization field or
EasyDiffraction switches to an API path that reads and applies CrysFML
IRF `CTHM`/`RKK` values.

**TODOs / decision points:**

- Document the current CrysFML behavior in X-ray verification pages and
  calculator support notes.
- Decide whether the public polarization API is a backend-independent
  EasyDiffraction correction, a backend-native binding where available,
  or an explicitly selectable compatibility mode.
- If native CrysFML support is required, raise an upstream request or
  add a CrysFML API binding that parses/applies `CTHM` and `RKK` through
  the same path as `patterns_simulation`.
- Add regression coverage that verifies the generated CrysFML CFL does
  not pretend to pass unsupported polarization keywords.

**Depends on:** issue 168 (X-ray anomalous table source) for PbSO4
verification interpretation, but this issue is independently actionable.

**Recommended-priority note:** Marked **highest** because X-ray
verification discrepancies can otherwise be misattributed to CrysFML
native behavior when the active correction is EasyDiffraction-owned.
