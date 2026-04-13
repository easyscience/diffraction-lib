# CrysPy Bug: Wrong Rotation Matrix Indices in `calc_power_dwf_aniso`

## Summary

`calc_power_dwf_aniso` in CrysPy 0.7.8 reads the rotation matrix from
the wrong slice of `reduced_symm_elems`, producing incorrect
Debye–Waller factors for every anisotropic atom.

## Affected Version

CrysPy **0.7.8** (and likely all versions sharing this code path).

## Location

`cryspy/A_functions_base/debye_waller_factor.py`, function
`calc_power_dwf_aniso`, around line 177.

## Root Cause

`reduced_symm_elems` has shape `(13, N_symmetry_operations)` with the
following layout per column:

| Indices | Content                             |
| ------- | ----------------------------------- |
| 0–3     | Translation: $b_1, b_2, b_3, b_d$   |
| 4–12    | Rotation matrix $R$ (row-major 3×3) |

The buggy code extracts the rotation matrix from indices **0–8** (i.e.
`symm_elems_r[0:9]`), which mixes the translation vector into the
rotation matrix:

```python
# BUGGY (current code)
r_11, r_12, r_13 = symm_elems_r[0], symm_elems_r[1], symm_elems_r[2]
r_21, r_22, r_23 = symm_elems_r[3], symm_elems_r[4], symm_elems_r[5]
r_31, r_32, r_33 = symm_elems_r[6], symm_elems_r[7], symm_elems_r[8]
```

The correct indices are **4–12**:

```python
# FIXED
r_11, r_12, r_13 = symm_elems_r[4], symm_elems_r[5], symm_elems_r[6]
r_21, r_22, r_23 = symm_elems_r[7], symm_elems_r[8], symm_elems_r[9]
r_31, r_32, r_33 = symm_elems_r[10], symm_elems_r[11], symm_elems_r[12]
```

For comparison, `calc_pr1` in the same codebase (structure factor phase
calculation) correctly uses indices 4–12 for the rotation.

## Impact

Every structure-factor calculation that uses anisotropic ADPs produces
wrong results. The isotropic DWF (`calc_power_dwf_iso`) is unaffected
and works correctly, so the bug only manifests when anisotropic
displacement parameters ($B_\text{ani}$ or $U_\text{ani}$) are used.

## Verification

We verified the fix by comparing isotropic and anisotropic calculations
for the LBCO structure (space group $I\,4/m\,m\,m$) where $B_\text{iso}$
and the equivalent diagonal anisotropic tensor must give identical
$|F|^2$ values:

| Metric                      | Buggy code                  | Patched code |
| --------------------------- | --------------------------- | ------------ | ------------------------------ | ---------------------- |
| $\max                       | y*\text{iso} - y*\text{ani} | $            | ~11 (first peak: 72.1 vs 61.0) | $1.78 \times 10^{-13}$ |
| $\chi^2$ (Biso)             | 14.98                       | 14.98        |
| $\chi^2$ (Bani, equivalent) | 184.10                      | 14.98        |

## Workaround

Monkey-patch at import time (used in EasyDiffraction):

```python
from cryspy.A_functions_base import debye_waller_factor as _dwf_mod

def _patched_calc_power_dwf_aniso(index_hkl, beta, symm_elems_r, flag_beta=False):
    b_11, b_22, b_33 = beta[0], beta[1], beta[2]
    b_12, b_13, b_23 = beta[3], beta[4], beta[5]
    h, k, l = index_hkl[0], index_hkl[1], index_hkl[2]
    # Corrected indices: rotation starts at 4, not 0
    r_11, r_12, r_13 = symm_elems_r[4], symm_elems_r[5], symm_elems_r[6]
    r_21, r_22, r_23 = symm_elems_r[7], symm_elems_r[8], symm_elems_r[9]
    r_31, r_32, r_33 = symm_elems_r[10], symm_elems_r[11], symm_elems_r[12]
    h_s = h * r_11 + k * r_21 + l * r_31
    k_s = h * r_12 + k * r_22 + l * r_32
    l_s = h * r_13 + k * r_23 + l * r_33
    power = (
        b_11 * np.square(h_s) + b_22 * np.square(k_s) + b_33 * np.square(l_s)
        + 2.0 * b_12 * h_s * k_s
        + 2.0 * b_13 * h_s * l_s
        + 2.0 * b_23 * k_s * l_s
    )
    dder = {}
    if flag_beta:
        ones_b = np.ones_like(b_11)
        dder['beta'] = np.stack([
            ones_b * np.square(h_s),
            ones_b * np.square(k_s),
            ones_b * np.square(l_s),
            ones_b * 2.0 * h_s * k_s,
            ones_b * 2.0 * h_s * l_s,
            ones_b * 2.0 * k_s * l_s,
        ], axis=0)
    return power, dder

_dwf_mod.calc_power_dwf_aniso = _patched_calc_power_dwf_aniso
```

## Suggested Fix

In `cryspy/A_functions_base/debye_waller_factor.py`, function
`calc_power_dwf_aniso`, change:

```diff
-    r_11, r_12, r_13 = symm_elems_r[0], symm_elems_r[1], symm_elems_r[2]
-    r_21, r_22, r_23 = symm_elems_r[3], symm_elems_r[4], symm_elems_r[5]
-    r_31, r_32, r_33 = symm_elems_r[6], symm_elems_r[7], symm_elems_r[8]
+    r_11, r_12, r_13 = symm_elems_r[4], symm_elems_r[5], symm_elems_r[6]
+    r_21, r_22, r_23 = symm_elems_r[7], symm_elems_r[8], symm_elems_r[9]
+    r_31, r_32, r_33 = symm_elems_r[10], symm_elems_r[11], symm_elems_r[12]
```

The same correction must be applied to the analytical-derivative branch
of the same function if it shares the same index convention.
