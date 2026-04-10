# Peak Profile Refactoring Plan

## Current state

### CWL profiles

| Class                    | Tag                       | Mixins                                                    | CrysPy mapping                                      |
| ------------------------ | ------------------------- | --------------------------------------------------------- | --------------------------------------------------- |
| `CwlPseudoVoigt`         | `'pseudo-voigt'`          | `CwlBroadeningMixin` (U,V,W,X,Y)                          | `pd_instr_resolution`                               |
| `CwlSplitPseudoVoigt`    | `'split pseudo-voigt'`    | `CwlBroadeningMixin` + `EmpiricalAsymmetryMixin` (p1–p4)  | `pd_instr_resolution` + `pd_instr_reflex_asymmetry` |
| `CwlThompsonCoxHastings` | `'thompson-cox-hastings'` | `CwlBroadeningMixin` + `FcjAsymmetryMixin` (fcj_1, fcj_2) | CrysFML only                                        |

**Verdict:** CWL names are correct. No changes needed.

### TOF profiles

| Class                          | Tag                                | Mixins                                                        | Issues                                                                                     |
| ------------------------------ | ---------------------------------- | ------------------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| `TofPseudoVoigt`               | `'tof-pseudo-voigt'`               | `TofBroadeningMixin` (σ+γ+β)                                  | No α params, no enum member, not in defaults, not usable                                   |
| `TofPseudoVoigtIkedaCarpenter` | `'pseudo-voigt * ikeda-carpenter'` | `TofBroadeningMixin` + `IkedaCarpenterAsymmetryMixin` (α₀,α₁) | Wrong name: not Ikeda-Carpenter at all. Calculator hardcodes `peak_shape Gauss` ignoring γ |
| `TofPseudoVoigtBackToBack`     | `'pseudo-voigt * back-to-back'`    | `TofBroadeningMixin` + `IkedaCarpenterAsymmetryMixin` (α₀,α₁) | Duplicate of above (identical mixins, different tag)                                       |

### Mixin issues

- `TofBroadeningMixin` lumps σ, γ, and β together. But β₀,β₁ are
  back-to-back exponential (BBE) **decay** parameters, not broadening or
  mixing.
- `broad_mix_beta_0/1` description says "Ratio of Gaussian to Lorentzian
  contributions" — wrong, they are BBE decay params.
- `IkedaCarpenterAsymmetryMixin` — α₀,α₁ are BBE **rise** params, not
  Ikeda-Carpenter and not asymmetry params.

### Calculator issues

- Hardcodes `_tof_profile_peak_shape Gauss` — ignores selected profile.
- Does not map γ (Lorentzian broadening) params to CrysPy.
- Cannot support type0m params at all.

---

## What CrysPy actually implements

CrysPy `peak_shape` options from `cl_1_tof_profile.py`:

| CrysPy `peak_shape` | Profile                                       | Parameters                                          |
| ------------------- | --------------------------------------------- | --------------------------------------------------- |
| `"Gauss"`           | Jorgensen: BBE ⊗ Gaussian                     | σ₀,₁,₂ + α₀,α₁ + β₀,β₁                              |
| `"pseudo-Voigt"`    | Jorgensen–Von Dreele: BBE ⊗ pseudo-Voigt      | σ₀,₁,₂ + γ₀,₁,₂ + α₀,α₁ + β₀,β₁                     |
| `"type0m"`          | Z-Rietveld type 0m: double BBE ⊗ pseudo-Voigt | σ₀,₁,₂ + γ₀,₁,₂ + α₁,α₂ + β₀₀,β₀₁,β₁₀ + r₀₁,r₀₂,r₀₃ |

---

## Cross-tool naming table

### TOF profiles

| Our name             | Formalism                 | CrysPy           | Mantid                      | FullProf            | GSAS-II      |
| -------------------- | ------------------------- | ---------------- | --------------------------- | ------------------- | ------------ |
| Jorgensen            | BBE ⊗ Gaussian            | `"Gauss"`        | `BackToBackExponential`     | Profile No. 9 (η=0) | Type 3 (γ=0) |
| Jorgensen–Von Dreele | BBE ⊗ pseudo-Voigt        | `"pseudo-Voigt"` | `NeutronBk2BkExpConvPVoigt` | Profile No. 10      | Type 3       |
| Z-Rietveld type 0m   | Double BBE ⊗ pseudo-Voigt | `"type0m"`       | —                           | —                   | —            |

BBE = back-to-back exponential. The Jorgensen profiles use rise
parameters (α₀,α₁) and decay parameters (β₀,β₁) following Von Dreele,
Jorgensen & Windsor, J. Appl. Cryst. 15, 581–589 (1982).

Note: **Ikeda-Carpenter** (Mantid `IkedaCarpenterPV`, FullProf TOF
tutorial) is a fundamentally different formalism with parameters α, β,
R, κ modelling the moderator neutron pulse. It is **not** implemented in
CrysPy and is **not** part of this refactoring.

### CWL profiles

| Our name                           | Formalism                            | CrysPy                                              | GSAS-II                       | Notes                                    |
| ---------------------------------- | ------------------------------------ | --------------------------------------------------- | ----------------------------- | ---------------------------------------- |
| Pseudo-Voigt                       | Caglioti pV (U,V,W,X,Y)              | `pd_instr_resolution`                               | Pseudo-Voigt (U,V,W,X,Y,SH/L) | Standard CWL broadening                  |
| Pseudo-Voigt + empirical asymmetry | Caglioti pV + Bérar–Baldinozzi p1–p4 | `pd_instr_resolution` + `pd_instr_reflex_asymmetry` | — (GSAS-II uses FCJ instead)  | Empirical asymmetry, not axis-divergence |
| Thompson–Cox–Hastings              | Caglioti pV + FCJ asymmetry          | CrysFML only                                        | FCJ mode (SH/L)               | Finger–Cox–Jephcoat axial divergence     |

---

## Open design questions

### Q2. CWL: is 'split pseudo-voigt' the right name?

CrysPy does not call the profile "split". It simply applies a separate
`pd_instr_reflex_asymmetry` block (p1–p4) on top of the standard
pseudo-Voigt resolution (U,V,W,X,Y). The p1–p4 parameters implement the
empirical asymmetry correction of Bérar & Baldinozzi (1993), which is
different from FullProf's "split pseudo-Voigt" (left/right independent
widths). GSAS-II does not use this correction at all (it uses FCJ
instead).

**Decision:** rename to `'pseudo-voigt + empirical asymmetry'`. This is
descriptive, accurately reflects the CrysPy implementation, and avoids
confusion with FullProf's split-width terminology.

### Q3. TOF: naming the third profile

The type0m profile from Z-Rietveld uses **double** back-to-back
exponentials (two rise channels α₁,α₂, two decay regimes β₀₀,β₀₁/β₁₀,
with switching parameters r₀₁,r₀₂,r₀₃) convolved with pseudo-Voigt.

This profile is **unique to Z-Rietveld** (KEK/J-PARC). It has no
equivalent in Mantid, FullProf, or GSAS-II (see cross-tool table above).
Neither Mantid nor FullProf implement a double-BBE model. The name
"type0m" is only standard within the Z-Rietveld ecosystem.

Jorgensen–Von Dreele uses **single** BBE ⊗ pV. Type0m extends this to
**double** BBE ⊗ pV. So "double Jorgensen–Von Dreele" captures the
relationship, but it is **not** an established literature name.

**Options:**

| Tag                             | Pros                                  | Cons                                                                        |
| ------------------------------- | ------------------------------------- | --------------------------------------------------------------------------- |
| `'type0m'`                      | Matches CrysPy, Z-Rietveld literature | Cryptic, no meaning to non-experts, no 1-to-1 correspondence in other tools |
| `'double-jorgensen-von-dreele'` | Descriptive, systematic               | Not a literature term, may be technically imprecise                         |
| `'zrietveld-type0m'`            | Credits origin                        | Still cryptic                                                               |

**Decision:** use `'double-jorgensen-von-dreele'`. The descriptive name
captures the relationship to the single-BBE Jorgensen–Von Dreele
profile. "type0m" is cryptic and meaningful only within the Z-Rietveld
ecosystem.

### Q4. Class name prefixes: `Cwl`/`Tof`

After renaming, tags will not overlap:

- CWL: `'pseudo-voigt'`, `'split pseudo-voigt'`,
  `'thompson-cox-hastings'`
- TOF: `'jorgensen'`, `'jorgensen-von-dreele'`, `'type0m'`/`'...'`

**Arguments for keeping Cwl/Tof prefixes:**

- All classes share a single `PeakFactory` registry — prefixes prevent
  ambiguity (e.g. `PseudoVoigt` sounds generic).
- Easier to grep and reason about imports.
- Consistent with existing `CwlPdInstrument` / `TofPdInstrument` naming
  in the instrument package.

**Arguments for dropping prefixes:**

- Tags and compatibility metadata already encode the mode.
- Class names become shorter and cleaner.

**Recommendation:** keep prefixes for clarity and consistency with
instruments.

### Q5. Mixin prefixes: `Tof` on `BackToBackExponentialMixin`

There is no CWL equivalent, and the file is already `tof_mixins.py`.

**Recommendation:** keep `Tof` prefix anyway — same reasoning as Q4. If
a CWL BBE mixin were ever needed (unlikely), the naming is already
clean. Consistency with file name helps.

### Q6. Splitting `CwlBroadeningMixin`

For CWL, **all three** profiles use both Gaussian (U,V,W) and Lorentzian
(X,Y). There is no CWL profile that needs only one set. Splitting would
add complexity with no benefit.

For TOF, the split is needed because Jorgensen uses only σ (no γ).

**Recommendation:** keep `CwlBroadeningMixin` combined. Split only TOF.

---

## Proposed changes

### New TOF mixin structure (in `tof_mixins.py`)

| Mixin                           | Parameters                           | Used by                |
| ------------------------------- | ------------------------------------ | ---------------------- |
| `TofGaussianBroadeningMixin`    | σ₀, σ₁, σ₂                           | All three TOF profiles |
| `TofLorentzianBroadeningMixin`  | γ₀, γ₁, γ₂                           | JVD + type0m           |
| `TofBackToBackExponentialMixin` | α₀, α₁, β₀, β₁                       | Jorgensen + JVD        |
| `TofDoubleExponentialMixin`     | α₁, α₂, β₀₀, β₀₁, β₁₀, r₀₁, r₀₂, r₀₃ | type0m                 |

Delete: `TofBroadeningMixin`, `IkedaCarpenterAsymmetryMixin`.

### New TOF classes (in `tof.py`)

| Class                         | Tag                             | Composition                                                                                                  | CrysPy `peak_shape` |
| ----------------------------- | ------------------------------- | ------------------------------------------------------------------------------------------------------------ | ------------------- |
| `TofJorgensen`                | `'jorgensen'`                   | `PeakBase` + `TofGaussianBroadeningMixin` + `TofBackToBackExponentialMixin`                                  | `"Gauss"`           |
| `TofJorgensenVonDreele`       | `'jorgensen-von-dreele'`        | `PeakBase` + `TofGaussianBroadeningMixin` + `TofLorentzianBroadeningMixin` + `TofBackToBackExponentialMixin` | `"pseudo-Voigt"`    |
| `TofDoubleJorgensenVonDreele` | `'double-jorgensen-von-dreele'` | `PeakBase` + `TofGaussianBroadeningMixin` + `TofLorentzianBroadeningMixin` + `TofDoubleExponentialMixin`     | `"type0m"`          |

Delete: `TofPseudoVoigt`, `TofPseudoVoigtIkedaCarpenter`,
`TofPseudoVoigtBackToBack`.

### Enum updates (`PeakProfileTypeEnum`)

Remove: `PSEUDO_VOIGT_IKEDA_CARPENTER`, `PSEUDO_VOIGT_BACK_TO_BACK`.
Add: `JORGENSEN`, `JORGENSEN_VON_DREELE`, `DOUBLE_JORGENSEN_VON_DREELE`.

### Factory default update

TOF Bragg default: `PSEUDO_VOIGT_IKEDA_CARPENTER` → `JORGENSEN` (Gauss
profile — simplest, fastest, most common default).

### CrysPy calculator updates

1. Emit `_tof_profile_peak_shape` dynamically based on profile type.
2. Map γ₀,γ₁,γ₂ to CrysPy `gamma0/1/2` for JVD and type0m.
3. Map type0m-specific params: `alpha1`, `alpha2`, `beta00`, `beta01`,
   `beta10`, `r01`, `r02`, `r03`.
4. In `_update_cryspy_dict`: update dict keys for `profile_gammas`,
   `profile_rs` arrays (used by type0m).

### Parameter naming fixes (in mixins)

| Current              | Problem                  | New                  |
| -------------------- | ------------------------ | -------------------- |
| `broad_mix_beta_0/1` | Not mixing — BBE decay   | `exp_decay_beta_0/1` |
| `asym_alpha_0/1`     | Not asymmetry — BBE rise | `exp_rise_alpha_0/1` |

### Files to update

1. `tof_mixins.py` — rewrite with new mixins
2. `tof.py` — rewrite with new classes
3. `enums.py` — update `PeakProfileTypeEnum`
4. `factory.py` — update default rules
5. `__init__.py` — update imports
6. `cryspy.py` — update calculator mapping
7. Unit tests: `test_peak.py`, `test_peak_tof.py`
8. Integration tests with TOF data
9. Tutorials: `ed-7.py` (TOF), any others using TOF profiles
10. Architecture docs: `architecture.md`, `package-structure-*.md`
11. ROADMAP.md — mark JVD as ✅, add type0m as 🗓

---

## Future: Ikeda-Carpenter ⊗ pseudo-Voigt (CrysFML)

The Ikeda-Carpenter profile (IC ⊗ pV) is a fundamentally different
formalism from the Jorgensen BBE profiles. It models the moderator
neutron pulse shape with parameters α, β, R, κ (Ikeda & Carpenter, Nucl.
Instr. Meth. A 239, 536–544, 1985).

- **Not in CrysPy.** Will be provided by CrysFML in the future.
- Mantid: `IkedaCarpenterPV` — α₀, α₁, β₀, κ, σ², γ.
- FullProf: TOF tutorial uses IC formalism.

### Planned class

| Class               | Tag                 | Composition                                                                                           | Calculator   |
| ------------------- | ------------------- | ----------------------------------------------------------------------------------------------------- | ------------ |
| `TofIkedaCarpenter` | `'ikeda-carpenter'` | `PeakBase` + `TofIkedaCarpenterMixin` + `TofGaussianBroadeningMixin` + `TofLorentzianBroadeningMixin` | CrysFML only |

### Planned mixin

| Mixin                    | Parameters    | Notes                               |
| ------------------------ | ------------- | ----------------------------------- |
| `TofIkedaCarpenterMixin` | α₀, α₁, β₀, κ | Moderator pulse shape (IC-specific) |

The Gaussian (σ²) and Lorentzian (γ) broadening for IC ⊗ pV can reuse
`TofGaussianBroadeningMixin` and `TofLorentzianBroadeningMixin` if the
parametrisation is compatible, or new IC-specific broadening mixins if
the functional form differs.

### Enum

`IKEDA_CARPENTER = 'ikeda-carpenter'`

### CalculatorSupport

```python
CalculatorSupport(
    cryspy=False,
    crysfml=True,
    pdffit2=False,
)
```

This profile will be added once CrysFML TOF support is integrated.

### CWL tag and class rename

Rename tag from `'split pseudo-voigt'` to
`'pseudo-voigt + empirical asymmetry'` (Q2 decision). Rename class from
`CwlSplitPseudoVoigt` to `CwlPseudoVoigtEmpiricalAsymmetry` to match.

Also rename `SPLIT_PSEUDO_VOIGT` enum member to
`PSEUDO_VOIGT_EMPIRICAL_ASYMMETRY`.
