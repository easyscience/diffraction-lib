# 136. Draw ADP Ellipsoids for Beta-Tensor Atoms

**Priority:** `[priority] low`

**Type:** Display / Visualization

The 3D structure view
([builder.py](src/easydiffraction/display/structure/builder.py)) draws
anisotropic displacement ellipsoids only for the `Bani`/`Uani` ADP
types. Atoms stored as the dimensionless `beta` tensor currently fall
through to a plain sphere. Drawing their ellipsoids needs a β→U
conversion in the renderer (using the reciprocal cell), analogous to the
existing B→U step. The model-layer β↔U conversion already exists
(`AtomSite._convert_adp_values_beta`) and could be reused.

**Depends on:** the β-tensor ADP support
([adp-beta-tensor plan](docs/dev/plans/adp-beta-tensor.md)).
