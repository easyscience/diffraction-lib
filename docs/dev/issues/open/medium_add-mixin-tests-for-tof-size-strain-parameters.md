# 183. Add Mixin Tests for TOF Size/Strain Parameters

**Priority:** `[priority] medium`

**Type:** Testing

The microstructural size/strain feature added four `Parameter`s to the
TOF peak mixin (`broad_gauss_size_g`, `broad_gauss_strain_g`,
`broad_lorentz_size_l`, `broad_lorentz_strain_l` in
`src/easydiffraction/datablocks/experiment/categories/peak/tof_mixins.py`),
but they are never asserted at the mixin-test level. Their value
hand-off is covered indirectly via
`tests/unit/.../analysis/calculators/test_cryspy.py`, yet the public
mixin properties themselves (read returns a `Parameter`, assignment
updates the value, range validation) have no direct test — unlike every
sibling parameter in `test_tof_mixins.py`.

**Fix:** in
`tests/unit/easydiffraction/datablocks/experiment/categories/peak/test_tof_mixins.py`,
assert that the four parameters appear in `p.parameters`, default to
`0.0`, and update via their setters (mirroring the existing σ₀/α₁ setter
checks).

**Depends on:** nothing.
