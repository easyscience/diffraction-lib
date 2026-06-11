# ADR: Preferred-Orientation Category (March–Dollase)

**Status:** Accepted **Date:** 2026-06-11

This ADR follows the conventions in [`AGENTS.md`](../../../../AGENTS.md).

## Context

Powder samples are frequently **textured**: crystallites pack with a
preferred orientation (platy crystals lie flat, needles align), so the
measured Bragg intensities deviate from the random-powder average. Every
mature Rietveld code corrects for this. EasyDiffraction currently does
not, which blocks faithful refinement of many real powder datasets and
is a common feature request from scientists comparing against FullProf
or GSAS.

Three independent sources confirm the same simple, widely used model —
**March–Dollase** — and were checked while preparing this ADR:

1. **CrysPy backend (already supports it).** CrysPy implements the
   *Modified March–Dollase* correction as a per-phase loop:

   ```
   loop_
   _texture_g_1
   _texture_g_2
   _texture_h_ax
   _texture_k_ax
   _texture_l_ax
   _texture_label
     0.19247   0.90000   1.000   1.000   1.000   phase1
   ```

   The class is `cryspy.C_item_loop_classes.cl_1_texture.Texture` /
   `TextureL`; the math lives in
   `cryspy.A_functions_base.preferred_orientation.calc_preferred_orientation_pd`.
   The applied per-reflection factor is

   ```
   h = 1/g1 + (g1**2 - 1/g1) * sin²(α)
   P(hkl) = g2 + (1 - g2) * h**(-1.5)
   ```

   where `α` is the angle between the texture axis `(h_ax, k_ax, l_ax)`
   and the reflection. `g1` is the March coefficient (1 = no texture,
   `<1` = platy/disk, `>1` = needle); `g2` is the **random (untextured)
   fraction** that mixes the correction back toward 1. The correction is
   applied in 1D CW (`rhochi_pd`), 2D (`rhochi_pd2d`), and TOF
   (`rhochi_tof`) powder paths, keyed to a phase by `_texture_label`.

   **Verification performed for this ADR.** A standalone cubic test
   (`P m -3 m`, a = 5 Å, axis `[0 0 1]`) was run through
   `rhochi_calc_chi_sq_by_dictionary`:

   | Case | Result |
   | --- | --- |
   | No texture loop vs. `g1=1, g2=0` | identical (max Δ ≈ 1e-11) |
   | `g1=1` vs. `g1=0.5, g2=0` | pattern strongly changes (max Δ ≈ 991; Σ intensity 7166 → 22101) |
   | Per-reflection factor, `g1=0.5`, axis `[001]` | `(00l)` → 0.354, in-plane `(hk0)` → up to 8.0 |

   This confirms CrysPy applies a texture correction through this loop
   and that `g1=1` (or absence of the loop) is a true no-op default.
   Note `g2=1` collapses `P` to 1 regardless of `g1`, so the **March
   coefficient, not the fraction, is the headline parameter**.
   (CrysPy's *form* of the correction is non-standard and not
   intensity-conserving — see Decision 6; the wiring and no-op
   behaviour above are nonetheless correct.)

2. **IUCr powder dictionary (`tmp/iucr-dicts/cif_pow.dic`).** The modern
   DDLm dictionary defines a full `PD_PREF_ORIENT` category and a
   `PD_PREF_ORIENT_MARCH_DOLLASE` subcategory with standard data names:

   | Data name | Meaning | In scope? |
   | --- | --- | --- |
   | `_pd_pref_orient_March_Dollase.r` (+`.r_su`) | March coefficient; 1 = unoriented, `(0,1)` disk, `(1,∞)` needle | yes ≡ `g1` |
   | `_pd_pref_orient_March_Dollase.index_h/_k/_l` | texture direction | yes ≡ `h_ax/k_ax/l_ax` |
   | `_pd_pref_orient_March_Dollase.hkl` | direction as a single string `[ h k l ]` | **no** |
   | `_pd_pref_orient_March_Dollase.fract` (+`.fract_su`) | weight of *each direction* when several are combined (sum = 1) | **no** (single direction) |
   | `_pd_pref_orient_March_Dollase.id` | row identity | yes |
   | `_pd_pref_orient_March_Dollase.phase_id` | links to `_pd_phase.id` | yes |
   | `_pd_pref_orient_March_Dollase.diffractogram_id` | links to `_pd_diffractogram.id` | optional |

   The **roles** line up across all three: IUCr `.r`, FullProf `Pref1`,
   and CrysPy `g1` are all "the March coefficient" of the same category
   shape, and IUCr `.index_h/_k/_l` ≡ CrysPy `h_ax/k_ax/l_ax` exactly.
   But the *role* matching `.r ↔ g1` is **not** a numerical equality:
   CrysPy's current `g1` parametrises a different, non-standard function
   (Decision 6), so `g1` equals the IUCr/Dollase/FullProf `r` only at
   `r = 1`. The category therefore adopts the IUCr name `r` for the
   coefficient slot while treating the CrysPy backend value as a
   backend-specific March-like coefficient until upstream corrects the
   formula.

   Two names are deliberately **excluded**:

   - **`.hkl`** stores the direction as a bracketed array `[ 1 0 4 ]`.
     gemmi's loop reader does not reliably round-trip this array
     syntax, so we use the three scalar integer columns
     `.index_h/_k/_l` instead.
   - **`.fract`** is the weight of *each direction* when one phase
     combines several March–Dollase directions. The initial category is
     single-direction-per-phase, so `.fract` is out of scope. This also
     removes any ambiguity with CrysPy's `g2`.

   There is **no IUCr standard name for CrysPy's `g2`** (the random,
   untextured fraction). `g2` is used non-zero in one shipped CrysPy
   example (`examples/rhochi_polarized_powder_2d_DyAl_5K_5T`, with
   `g1=0.19247, g2=0.90000`), so it is a real — if rarely used —
   capability for partially textured samples. Naming it is the main
   decision below.

3. **FullProf examples (`~/Applications/fullprof/Examples`).** The
   `CrystalStructure-SAnnPrefOr/lamn_pm_pref.pcr` example applies
   March–Dollase to LaMnO₃ (orthorhombic `Pbnm`, neutron CW, λ = 1.561 Å,
   3T2/LLB) with `Pref1 = 0.66` and a paired `lamn_pm_nor.pcr` with no
   correction. This is cited here only as **background evidence** that
   FullProf exposes the same model (`Pref1`/`Pref2` + an `h k l`
   direction); it is **not** the verification reference. Both shipped
   FullProf PO examples are simulated-annealing demos on *calculated*
   data, so the verification case is constructed separately (see the
   §Verification section, which builds on `pd-neut-cwl_pv_lbco`).

The three models agree on the **category shape** — a single scalar
March coefficient plus an integer direction (and an optional random
fraction) — so a small, well-scoped category is sufficient. They do
**not** all agree on the numerical *function* that coefficient drives:
CrysPy 0.11.0 applies a non-standard, non-conserving variant (Decision
6). The category design below is therefore stable regardless, while the
CrysPy backend value is documented as temporarily non-portable.

## Decision

### 1. A new per-phase loop category `pref_orient`

Add a loop-style category, **owned by the experiment**, that mirrors the
shape of the existing `linked_phases` category (each row keyed by a
phase id). This matches CrysPy exactly — texture is a per-phase loop on
the powder experiment, not a property of the structure — and lets a
multi-phase experiment give each phase its own correction.

```
src/easydiffraction/datablocks/experiment/categories/pref_orient/
    __init__.py
    factory.py        # PrefOrientFactory(FactoryBase), default tag
    default.py        # PrefOrient(CategoryItem), PrefOrients(CategoryCollection)
```

- `PrefOrient(CategoryItem)` — `_category_code = 'pref_orient'`,
  `_category_entry_name = 'phase_id'`.
- `PrefOrients(CategoryCollection)` — `item_type=PrefOrient`,
  `Compatibility(sample_form={POWDER}, scattering_type={BRAGG})`.

**Scope: Bragg powder only.** `PdExperimentBase`
(`item/base.py:553`) is shared by both `BraggPdExperiment`
(`item/bragg_pd.py:38`) and `TotalPdExperiment` (PDF,
`item/total_pd.py:29`, `scattering_type=TOTAL`). `linked_phases` is
created on the shared base, but preferred orientation must **not** be —
PDFFIT has no PO support and a silent no-op on a total-scattering
experiment would mislead. Therefore `_pref_orient` is created **only in
`BraggPdExperiment.__init__`** (not in `PdExperimentBase`), so
`experiment.preferred_orientation` simply **does not exist** on PDF /
single-crystal experiments. Accessing it there raises `AttributeError`
— an explicit, discoverable failure rather than a silent no-op. The
`Compatibility(scattering_type={BRAGG})` metadata documents the same
contract for factory/introspection callers.

- Within `BraggPdExperiment`, `_pref_orient` is created via
  `PrefOrientFactory`, added to that class's
  `_attach_category_parents()` list, and exposed read-only as
  `experiment.preferred_orientation` (attribute, no `type` selector —
  it is a fixed, single-implementation category like `linked_phases`,
  not a switchable one, per
  [`switchable-category-owned-selectors.md`](switchable-category-owned-selectors.md)).

### 2. Parameters per row

| Python attr | Type | Default | Meaning | CrysPy | IUCr export name |
| --- | --- | --- | --- | --- | --- |
| `phase_id` | StringDescriptor | `'Si'` | phase this row corrects | `_texture_label` | `_pd_pref_orient_March_Dollase.phase_id` |
| `r` | Parameter (refinable) | `1.0` | March coefficient (1 = none) | `g_1` | `_pd_pref_orient_March_Dollase.r` |
| `index_h` / `index_k` / `index_l` | Descriptor (integer, fixed) | `0 / 0 / 1` | texture direction | `h_ax/k_ax/l_ax` | `_pd_pref_orient_March_Dollase.index_h/_k/_l` |
| `fraction` | Parameter (refinable) | `0.0` | random (untextured) fraction | `g_2` | *(see Decision 4)* |

The headline parameter is named **`r`** to match the IUCr standard
(`_pd_pref_orient_March_Dollase.r`) and the crystallographic literature
(Dollase 1986); **`fraction`** is the random/untextured fraction.

`r` uses `RangeValidator(gt=0.0)`; `fraction` uses
`RangeValidator(ge=0.0, le=1.0)`. The defaults (`r=1.0`,
`fraction=0.0`) make an empty or freshly added correction a
**mathematical no-op**, so existing projects and tutorials are
unaffected until a user opts in.

**`index_h`/`index_k`/`index_l` are integer Descriptors, not refinable
Parameters.** They use the same names as the existing `refln` categories
(and avoid a bare ambiguous `l`). CrysPy technically allows refining
`h_ax/k_ax/l_ax`, but refining a crystallographic texture direction as a
continuous variable is physically unusual and a common source of
unstable fits. The direction is a user-set Miller index; only `r` (and
optionally `fraction`) refine.
If a continuous-direction use case ever appears, promoting the
descriptors to parameters is a backward-compatible change.

### 3. User-facing API (Jupyter)

```python
import easydiffraction as ed

project = ed.Project()
project.experiments.add(name='hrpt', ...)   # CW powder, neutron
expt = project.experiments['hrpt']

# Add a March–Dollase correction for a linked phase, axis [0 0 1].
# Uses the keyword-based collection constructor `.create(...)`, exactly
# like `experiment.linked_phases.create(id=..., scale=...)`.
expt.preferred_orientation.create(
    phase_id='lbco',
    r=0.8,
    index_h=0, index_k=0, index_l=1,
)

po = expt.preferred_orientation['lbco']
po.r.value = 0.75      # platy texture
po.r.free = True       # refine the March coefficient
po.index_h.value, po.index_k.value, po.index_l.value = 0, 0, 1  # fixed Miller direction

expt.preferred_orientation.show()      # table of all corrections
```

Reading a property returns the live `Parameter`/`Descriptor`
(matching every other category); assigning sets `.value`. Refinement
follows the standard `.free = True` convention and is available on `r`
and `fraction` only. `fraction` stays optional and defaults to pure
March–Dollase, so a "simple preferred orientation" workflow only sets
`r` and the direction.

### 4. CIF serialization

EasyDiffraction keeps **two** CIF flavours, per
[`iucr-cif-tag-alignment.md`](iucr-cif-tag-alignment.md):
short category-scoped tags for the day-to-day default save (and
round-trip), and dictionary-standard tags for the on-demand IUCr report
export. Categories with no IUCr counterpart (peak profile U/V/W, FCJ
asymmetry, background, the analysis categories) already export under the
project namespace `_easydiffraction_<category>.*`; there is **no
"official-names-only" rule** for the report. `g2` follows that
established precedent.

**Default / round-trip CIF** — all fields, short tags:

```
loop_
_pref_orient.phase_id
_pref_orient.r
_pref_orient.index_h
_pref_orient.index_k
_pref_orient.index_l
_pref_orient.fraction
  lbco  0.75  0  0  1  0.0
```

The row is keyed by `phase_id` (the linked phase this correction
applies to), paralleling how `linked_phases` keys rows by the phase
`id`. The IUCr `_pd_pref_orient_March_Dollase.id` serial (1, 2, …) is
synthesised by the report writer and has no Python field.

Per parameter, `CifHandler(names=['_pref_orient.r'],
iucr_name='_pd_pref_orient_March_Dollase.r')` — `names[0]` is the
canonical round-trip tag, `iucr_name` is what the report writer emits.
(Caveat: until CrysPy adopts the standard function — see Decision 6 —
the exported `.r` is CrysPy's `g1`, which only equals the IUCr/Dollase
`r` at `r = 1`. The mapping is kept so the CIF is forward-compatible
once the backend is corrected.)

**IUCr report CIF** — standard fields under the dictionary category, the
non-standard `g2` under the project namespace. The IUCr writer is a
bespoke per-loop writer (`io/cif/iucr_writer.py`), so a dedicated
`_write_pref_orient_loop` controls exactly which columns appear:

```
loop_
_pd_pref_orient_March_Dollase.id
_pd_pref_orient_March_Dollase.phase_id
_pd_pref_orient_March_Dollase.index_h
_pd_pref_orient_March_Dollase.index_k
_pd_pref_orient_March_Dollase.index_l
_pd_pref_orient_March_Dollase.r
_pd_pref_orient_March_Dollase.r_su
  1  lbco  0  0  1  0.75  0.0
```

**`fraction` (g2) naming — resolved.** CrysPy's `g2` has no IUCr
standard name; IUCr `.fract` is a different quantity (multi-direction
weight) and is **not** reused for it. Decision:

- The canonical default tag is `_pref_orient.fraction`.
- The report export name is `_easydiffraction_pref_orient.fraction`
  — consistent with every other non-standard field's
  `_easydiffraction_<category>.*` form (never grafted onto the official
  `_pd_pref_orient_March_Dollase` path, and never reusing `.fract`).
- Because mixing a project-namespace column into the official
  March–Dollase loop is awkward and `g2 = 0` is both the default and
  the standards-clean case, the report **omits `fraction` entirely when
  it is 0** and, only when a user has set it non-zero, emits it as a
  short separate item/loop in the `_easydiffraction_` namespace. The
  common workflow therefore produces a fully standards-compliant report
  with no project-namespace noise.

Rejected alternatives for `g2`: reusing `_pd_pref_orient_March_Dollase.fract`
(semantically wrong — would mislead external tools); dropping `g2`
altogether (discards a capability the backend exercises in its own
example). Both are recorded under Alternatives Considered.

### 5. Backend wiring

- **CrysPy** (`analysis/calculators/cryspy.py`). Two paths, matching how
  every other experiment parameter is handled:

  1. **CIF construction** (`_convert_experiment_to_cryspy_cif`): after
     `_cif_phase_section`, emit a `_texture_*` loop for the matching
     `pref_orient` row. **Constant-wavelength only** for now — TOF is
     Deferred Work, and emitting a TOF texture loop without the TOF
     pass-through (point 2) would let refined values go stale, so TOF
     emits nothing and the cache signature (point 3) is likewise
     CW-scoped. `g1 = 1` is a no-op, so a default row is harmless. Map
     `r→_texture_g_1`, `fraction→_texture_g_2`,
     `index_h/index_k/index_l→_texture_h_ax/_k_ax/_l_ax`, `phase_id→_texture_label`.
     CrysPy parses this into the experiment block (`pd_<name>`) of the
     dictionary under the array keys `texture_g1`, `texture_g2`,
     `texture_axis` (shape `(3, n_rows)`), `texture_name`, and the
     `flags_texture_*` arrays (see `cl_1_texture.TextureL.get_dictionary`).

  2. **Cached-dictionary refinement** (`_update_experiment_in_cryspy_dict`):
     the calculator caches the parsed dict in `_cryspy_dicts[combined_name]`
     and, on minimizer calls, patches scalar arrays in place rather than
     rebuilding. Texture must join that pass-through, guarded like
     `offset_sycos`:

     ```python
     if 'texture_g1' in cryspy_expt_dict:
         for i, po in enumerate(experiment.preferred_orientation):
             cryspy_expt_dict['texture_g1'][i] = po.r.value
             cryspy_expt_dict['texture_g2'][i] = po.fraction.value
     ```

     Only `r` and `fraction` **values** are patched. `index_h`/`index_k`/`index_l` are fixed
     descriptors (never refined), so `texture_axis` is never patched
     here. `r.free`/`fraction.free` are **not** pushed into the CrysPy
     dict at all: EasyDiffraction runs CrysPy with
     `flag_calc_analytical_derivatives=False`, so CrysPy's
     `flags_texture_*` are unused; the free/fixed state is consumed by
     the EasyDiffraction minimizer, which assembles the parameter list
     from the live category and writes new `.value`s each iteration
     (then this pass-through carries them into the cached dict). This is
     identical to how `r`-like scalars (wavelength, offsets, resolution)
     already work.

  3. **Cache invalidation.** The cached dict's array *shapes* and row
     identity are baked in at parse time, so any change to the **set or
     identity of rows** — adding/removing a `pref_orient` row, or
     changing a row's `phase_id` or `index_h`/`index_k`/`index_l` — must drop the cache so the
     CIF is rebuilt. Extend `_invalidate_stale_cache` with a
     `pref_orient` signature (a tuple of
     `(phase_id, index_h, index_k, index_l)` per row, in order) tracked
     per `combined_name` exactly like
     `_cached_peak_types`/`_cached_adp_types`, and only for
     constant-wavelength experiments (matching the CW-only emission
     scope): when the signature changes,
     `self._cryspy_dicts.pop(combined_name, None)`. Value-only edits to
     `r`/`fraction` do **not** invalidate — they flow through path 2.
- **CrysFML / PDFFIT**: declare no support for now (like sample
  displacement on CrysFML). `CalculatorSupport(calculators={CRYSPY})`
  on the category; document the gap in a comment.

### 6. Known backend limitation — CrysPy's texture function is non-standard

CrysPy 0.11.0's "Modified March's function"
(`A_functions_base/preferred_orientation.py`) is **not** the standard
March–Dollase function that FullProf and GSAS-II use, and it does **not
conserve scattered intensity**. With `g2 = 0` it applies

```
P_cryspy(α) = [ (1/g1) cos²α + g1² sin²α ]^(-3/2)
```

whereas the textbook March–Dollase (Dollase 1986) is

```
P_dollase(α) = [ r² cos²α + (1/r) sin²α ]^(-3/2)
```

The exponent pattern differs (`{1/g1, g1²}` vs `{r², 1/r}`), so no
single `r = f(g1)` makes them equal; and the orientation average of
CrysPy's form is `g1^(-3/2)`, not `1`, so it rescales the integrated
total instead of only redistributing it. Numerically, CrysPy `g1=0.5`
spans 0.354 (axis) → 8.0 (perpendicular) and averages to 2.83, while
every standard `r` averages to exactly 1.0.

Consequences for this category:

- The decision is to **implement against CrysPy as-is** — the category,
  API, serialization, and wiring are correct and useful regardless of
  the backend's internal formula. `r` is passed straight through to
  CrysPy's `g_1`.
- **The exported `_pd_pref_orient_March_Dollase.r` value is therefore
  not yet portable** to/from FullProf/GSAS-II for `r ≠ 1`. This is a
  documented backend limitation, not a category-design choice; it
  resolves itself once CrysPy adopts the standard function.
- The divergence is captured for upstream reporting in
  `tmp/cryspy/preferred-orientation/` (minimal `rcif`, a comparison
  script calling the real CrysPy routine, and an `ISSUE.md` with
  equations and FullProf/GSAS/Dollase references). A CrysPy issue is
  to be filed; this ADR should link it once it has a number.

## Consequences

- Textured powder data can be refined against the CrysPy backend with a
  small, discoverable API and standards-aligned CIF.
- One new category package plus experiment wiring and a CrysPy
  serialization branch; no changes to the structure model.
- A new cross-engine verification case (on the `pd-neut-cwl_pv_lbco`
  base) extends the existing FullProf suite (consistent with the
  cross-engine work in commits #195–#199) and **documents** the CrysPy
  texture-function divergence rather than hiding it.
- The `fraction` non-standard tag is a documented, opt-in wart;
  pure March–Dollase remains the standards-clean default.
- CrysPy's non-standard texture formula (Decision 6) means refined `r`
  values are not yet portable to FullProf/GSAS-II; the limitation is
  documented, reproduced for upstream in
  `tmp/cryspy/preferred-orientation/`, and clears once CrysPy is fixed.

## Alternatives Considered

- **Attach PO to the structure/phase instead of the experiment.**
  Rejected: texture is a property of *how this sample was packed for
  this measurement*, not of the crystal structure; the same phase in
  two experiments can have different textures. CrysPy keys it to the
  experiment, and `linked_phases` already establishes the
  experiment-owns-per-phase pattern.
- **Switchable `pref_orient.type` category (March–Dollase vs. spherical
  harmonics).** Deferred, not rejected — see Deferred Work. Introducing
  the switchable machinery now would violate "no abstraction before a
  second use case."
- **Scalar fields on the instrument category** (like sample
  displacement). Rejected: PO is inherently per-phase and a loop; a flat
  scalar cannot represent a multi-phase experiment.
- **Export `g2` as `_pd_pref_orient_March_Dollase.fract`.** Rejected:
  `.fract` is the IUCr multi-direction weight, a different quantity;
  reusing it would mislead any external program (checkCIF, pdCIFplotter)
  reading the report.
- **Drop `g2`, fix pure March–Dollase (`g2 = 0`).** Rejected as the
  default-only model: it discards the partially-textured capability the
  backend exercises in its own DyAl example. Instead `g2` is kept but
  defaults to `0.0`, so the standards-clean case is the default and the
  non-standard tag only appears on explicit opt-in.

## Deferred Work

- **Spherical-harmonics texture.** The IUCr dictionary and CrysPy both
  describe it; when a second model is actually needed, promote
  `pref_orient` to a switchable category (`pref_orient.type`) per
  [`switchable-category-owned-selectors.md`](switchable-category-owned-selectors.md),
  with March–Dollase as the default implementation.
- **Multi-direction March–Dollase** (several axes per phase with
  `.fract` weights). The IUCr names exist; CrysPy's loop already allows
  multiple rows per label. Out of scope until requested.
- **TOF and 2D PO.** CrysPy supports both; the category is beam-mode
  agnostic, but initial wiring, verification, and the tutorial target
  CW powder.
- **User tutorial.** A new `ed-XX` tutorial follows *after* the
  verification case below lands, so the documented workflow rests on a
  validated reference. Out of scope for the first implementation plan
  beyond a placeholder.

## Verification (cross-engine reference)

FullProf ships **no standard Rietveld example that uses preferred
orientation**. The only two examples with a non-zero `Pref1`
(`CrystalStructure-SAnnPrefOr/lamn_pm_pref.pcr`,
`MagneticStructure-SAnnPrefOr/hobk_pm_pref.pcr`) are *simulated-
annealing* demos run against *calculated* data, not Rietveld
refinements against measured data — unsuitable as a verification
reference.

Because of the backend limitation in Decision 6, the verification
notebook **documents the CrysPy↔FullProf mismatch** rather than
asserting agreement. It is built on the existing
**`pd-neut-cwl_pv_lbco`** case (La₀.₅Ba₀.₅CoO₃, neutron CW,
pseudo-Voigt — chosen as the base on request):

1. Copy `docs/docs/verification/fullprof/pd-neut-cwl_pv_lbco/lbco.pcr`,
   enable a single March–Dollase direction (texture axis `h k l` via the
   phase `Pr1 Pr2 Pr3` line and a non-zero `Pref1`), and re-run FullProf
   locally (`~/Applications/fullprof`) to regenerate `.prf`/`.bac`/`.sum`
   with the standard March–Dollase correction active.
2. Add `pd-neut-cwl_pv-march_lbco` (paired `.py`/`.ipynb`) that builds
   the same LBCO model in EasyDiffraction, sets
   `expt.preferred_orientation` with `r` mapped to FullProf's `Pref1`,
   and overlays the CrysPy pattern on the FullProf reference. The
   notebook is expected to **show agreement at `r = 1` and a visible,
   quantified divergence for `r ≠ 1`**, with a markdown cell explaining
   the CrysPy formula difference and linking the upstream issue.
   Because PO is CrysPy-only, the case compares CrysPy vs FullProf only
   (no CrysFML column, unlike the base `lbco` case).

This verification notebook is built **before any user tutorial**, so the
tutorial can cite a validated, well-understood workflow (including the
documented caveat). Producing the FullProf reference and the
verification notebook is the first deliverable of the implementation
plan's Phase 2.
