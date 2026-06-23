# 178. CrysFML Under-counts Lattice Centering in Powder Intensity

**Priority:** `[priority] high`

**Type:** Correctness / External backend / Verification

The CrysFML Python API (both the dict backend
`tof_powder_pattern_from_dict` / `cw_powder_pattern_from_dict` and the
CFL backend `patterns_simulation`) computes powder Bragg intensities
that are too low for **centered** Bravais lattices, by a clean,
reproducible factor that depends only on the lattice centering. cryspy
(which reproduces FullProf's absolute scale to <1% across a 16x
cell-volume range) and FullProf do not have this error.

## Measured discrepancy (`cryspy / crysfml`, absolute, no scale fit)

| Centering          | n (lattice points) | example                | ratio | `(n/(n-1))^2` |
| ------------------ | ------------------ | ---------------------- | ----- | ------------- |
| P                  | 1                  | LaB6, PbSO4            | 1.000 | 1             |
| C, I (and A/B)     | 2                  | Y2O3, NCAF, Fe, C-test | 4.000 | 4             |
| R (hexagonal axes) | 3                  | R-test                 | 2.250 | 2.25          |
| F                  | 4                  | Si, CaF2, NaCl         | 1.778 | 16/9          |

The ratio is exactly **`(n / (n - 1))^2`**, stable across wavelength, 2θ
range and chemistry. This is the signature of CrysFML applying only
`n - 1` of the `n` lattice translations in the structure-factor sum:
`|F|_crysfml = (n-1) f` vs the correct `|F| = n f`, so the intensity
`|F|^2` is low by `(n/(n-1))^2`. It affects CWL and (once the CFL TOF
branch is implemented) TOF equally. CWL is the only mode currently
affected in practice because the CFL TOF branch returns zeros (see issue
134 context and the CFL TOF gap).

## Impact

Single-phase Rietveld fits are unaffected (the scale is refined and the
peak **shape** is correct). The error matters for **absolute
intensities, multi-phase weight fractions, and any cross-engine scale
comparison**, where a centered phase is under-weighted relative to a
primitive one.

## Workaround in EasyDiffraction (implemented)

`src/easydiffraction/analysis/calculators/crysfml.py` now multiplies
each phase pattern by `(n/(n-1))^2` (method
`_apply_centering_intensity_correction`, with `n` from the
Hermann-Mauguin centering letter via `_lattice_centering_points`). After
the correction, `crysfml` matches `cryspy` to <0.2% for P/C/I/R/F. The
correction is keyed only on the centering letter (P/A/B/C/I/R/F), so it
is independent of structure and wavelength.

## Preferred upstream fix

Fix the centering loop in the CrysFML Python API (or the underlying
`crysfml08lib` powder path) to include all `n` lattice translations.
When that lands, **remove the EasyDiffraction workaround** above and
re-verify P/C/I/R/F give ratio 1.0 without it.

**Depends on:** related to crysfml backend correctness (issues 130, 134)
but independent — those are profile-shape discrepancies, this is an
intensity-scale (centering) discrepancy.
