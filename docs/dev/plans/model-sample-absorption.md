# Implementation Plan: Model Sample Absorption (Debye–Scherrer, μR)

This plan follows the conventions in [`AGENTS.md`](../../../AGENTS.md).
No deliberate exceptions are taken.

## ADR

Implements
[`docs/dev/adrs/suggestions/model-sample-absorption.md`](../adrs/suggestions/model-sample-absorption.md)
(Status: Proposed; review cycle 1 closed). This plan **owns** that ADR.

**ADR promotion happens in `/draft-impl-1` Phase A (design-history
cleanup), at task start — not as a numbered Phase 1 step.** Before P1.1,
the Phase A setup: `git mv` the ADR `suggestions/ → accepted/`, set
`**Status:** Accepted`, flip the `docs/dev/adrs/index.md` row to
`Accepted` with the `accepted/...` link, fix any link still pointing at
`suggestions/...` (`git grep -n model-sample-absorption`), remove the
design-phase `model-sample-absorption_review-*.md` /
`_reply-*.md` siblings, and commit
(`Promote model-sample-absorption ADR to accepted`). The review-1 fixes
currently uncommitted in the worktree travel with that commit. This
aligns with [`AGENTS.md`](../../../AGENTS.md) §Change Discipline (promote
before opening the PR) and the `/draft-impl-1` Phase A workflow, so the
autonomous setup does not commit the ADR as a suggestion and then move
it later.

Related accepted ADRs the work must respect:

- [`switchable-category-owned-selectors.md`](../adrs/accepted/switchable-category-owned-selectors.md)
  — the `category.type` / `category.show_supported()` surface and the
  owner `_swap_<name>` hook.
- [`preferred-orientation-category.md`](../adrs/accepted/preferred-orientation-category.md)
  — the most recent powder-correction category (#200); its package,
  owner wiring, and verification-page pattern are the closest template.
- [`factory-contracts.md`](../adrs/accepted/factory-contracts.md),
  [`factory-tag-naming.md`](../adrs/accepted/factory-tag-naming.md),
  [`enum-backed-closed-values.md`](../adrs/accepted/enum-backed-closed-values.md).

## Branch and PR

- **Branch:** `model-sample-absorption` (already created off `develop`,
  in sync with `origin/develop`). PRs target `develop`.
- Do not push unless asked.
- The `/draft-impl-1` shortcut commits each Phase 1 step with explicit
  paths before moving to the next, per [`AGENTS.md`](../../../AGENTS.md)
  §Commits. Each `- [ ] P1.X` item below is one atomic commit.

## Decisions (settled in the ADR)

1. **Switchable `absorption` category** mirroring `extinction`
   (`base.py` + concrete classes + factory + `__init__.py`), **not** a
   flat instrument parameter.
2. **Calculator-independent application:** A(θ) is computed in
   EasyDiffraction and multiplied onto the final pattern in **both**
   backends via one shared helper — neither cryspy nor crysfml applies
   it internally (cryspy has no slot; crysfml's Fortran routine is
   unwrapped).
3. **Pointwise 2θ envelope:** `y(2θ_i) ← A(θ_i)·y(2θ_i)` (slow-envelope
   approximation, validated to 4 decimals vs FullProf).
4. **Phase 1 builds only `none` + `cylinder-hewat`.** Lobanov,
   flat-plate, TOF are future classes on the same factory (ADR §Deferred
   Work). TOF additionally needs a separate λ-aware calculation path
   (ADR §3a) — out of scope here.
5. **Owner scope = Bragg powder only:** `Compatibility(powder, bragg)`,
   `CalculatorSupport(cryspy, crysfml)`. Total/pdffit experiments do not
   get the category at all (ADR §1 "Owner scope").
6. **`mu_r`:** `Parameter`, `RangeValidator(ge=0.0)`, default `0.0`,
   `free=False` by default. **Out-of-range policy:** no hard ceiling,
   but a single `log.warning` above `HEWAT_MAX_VALIDATED_MU_R = 1.5`
   pointing to the (deferred) `cylinder-lobanov` form (ADR §4).
7. **Persistence:** project-namespaced `_absorption.type` / `_absorption.mu_r`
   via the descriptors' `CifHandler`, IUCr export
   `_easydiffraction_absorption.*` (ADR §7).
8. **`type` selector is enum-backed (`AbsorptionTypeEnum`).** Per
   [`enum-backed-closed-values.md`](../adrs/accepted/enum-backed-closed-values.md)
   (which names factory tags as a finite closed set requiring
   `(str, Enum)`), the `type` selector follows the **peak** precedent —
   `peak/base.py:42` validates against
   `[member.value for member in PeakProfileTypeEnum]` and `peak/cwl.py:29`
   sets `TypeInfo(tag=PeakProfileTypeEnum.X.value)`. Absorption mirrors
   this: a new `AbsorptionTypeEnum` (`NONE = 'none'`,
   `CYLINDER_HEWAT = 'cylinder-hewat'`; future members for Lobanov /
   flat-plate / TOF), the concrete classes set
   `TypeInfo(tag=AbsorptionTypeEnum.X.value)`, and the `type` validator
   uses `[m.value for m in AbsorptionTypeEnum]`. This is the
   enum-compliant path — **not** `extinction`'s raw
   `Factory.supported_tags()`, which is the non-compliant outlier — so
   the plan's "No deliberate exceptions" statement holds.

## Open questions

(Open Question 1 — `type` selector enum — is now **resolved**; see
Decision 8.)

1. **Where to fire the out-of-range warning.** Per-iteration spam is a
   risk if fired at calculation time. **Proposed:** fire from the Hewat
   helper, guarded by a module-level "already-warned" set keyed on the
   rounded μR value, so each distinct out-of-range value warns once.
   Alternative: a custom validating descriptor on `mu_r`.
2. **IUCr export scope for Phase 1.** Round-trip of `_absorption.*` is
   required; the optional standard provenance
   (`_exptl_absorpt.correction_type cylinder`) can land in Phase 1 or
   defer. **Proposed:** Phase 1 does round-trip + the
   `_easydiffraction_absorption.*` IUCr names; standard-provenance
   provenance is deferred.

## Concrete files likely to change

**New (Phase 1):**

- `src/easydiffraction/datablocks/experiment/categories/absorption/__init__.py`
- `…/categories/absorption/base.py` — `AbsorptionBase(CategoryItem, SwitchableCategoryBase)`
- `…/categories/absorption/factory.py` — `AbsorptionFactory`
- `…/categories/absorption/none.py` — `NoAbsorption` (tag `none`, A≡1)
- `…/categories/absorption/cylinder_hewat.py` — `CylinderHewatAbsorption` (tag `cylinder-hewat`, `mu_r`)
- `src/easydiffraction/analysis/calculators/absorption.py` — shared
  `factor(two_theta, absorption) → np.ndarray` + Hewat + `HEWAT_MAX_VALIDATED_MU_R`
- `docs/docs/user-guide/parameters/absorption.md` (template:
  `parameters/pref_orient.md`)

**Phase A — design-history cleanup (in `/draft-impl-1` setup, before
P1.1; see §ADR):**

- `docs/dev/adrs/suggestions/model-sample-absorption.md` →
  `docs/dev/adrs/accepted/model-sample-absorption.md` (`git mv`,
  `**Status:** Accepted`).
- `docs/dev/adrs/index.md` — flip the row `Suggestion → Accepted` with
  the `accepted/...` link; fix any `suggestions/...` links
  (`git grep -n model-sample-absorption`).
- Remove the design-phase `model-sample-absorption_review-*.md` /
  `_reply-*.md` siblings (ADR and plan) per the Phase A cleanup.

**Modified (Phase 1):**

- `src/easydiffraction/datablocks/experiment/item/enums.py` — add
  `AbsorptionTypeEnum` (Decision 8 / P1.1).
- `src/easydiffraction/datablocks/experiment/item/base.py` —
  `_swap_absorption` / `_replace_absorption` (mirror extinction
  lines ~210–241), `absorption` read-only property, parent-attach,
  `_serializable_categories`.
- `src/easydiffraction/datablocks/experiment/item/bragg_pd.py` —
  create `self._absorption = AbsorptionFactory.create(AbsorptionFactory.default_tag())`
  alongside `_pref_orient` (line ~67); expose `absorption` property;
  extend `_restore_switchable_types()` (line ~201) to restore
  `_absorption.type` (P1.2).
- `src/easydiffraction/analysis/calculators/cryspy.py` — multiply A(θ)
  before `return y_calc` (line ~303), guarded for the empty/no-data
  path.
- `src/easydiffraction/analysis/calculators/crysfml.py` — multiply A(θ)
  in `calculate_pattern` before `return np.asarray(y)` (line ~169),
  guarded for the empty/no-data path.
- `src/easydiffraction/io/cif/iucr_writer.py` — absorption export
  (mirror the pref_orient hook from #200), if needed.
- `docs/docs/user-guide/parameters.md` — add `absorption.type` /
  `absorption.mu_r` rows + reference link to `parameters/absorption.md`
  (P1.6). `docs/mkdocs.yml` is **not** changed for the leaf page (that
  directory is excluded from global nav); touch it only if the #200
  `pref_orient` precedent did.

**Phase 2 (tests / verification):**

- Category tests **mirror the package per-module** (the parent-level
  `test_<package>.py` exception applies only to packages with just
  `default.py`/`factory.py`; this package has more):
  - `tests/unit/easydiffraction/datablocks/experiment/categories/absorption/test_base.py`
  - `…/categories/absorption/test_factory.py`
  - `…/categories/absorption/test_none.py`
  - `…/categories/absorption/test_cylinder_hewat.py`
  Confirm with `pixi run test-structure-check`.
- `tests/unit/easydiffraction/analysis/calculators/test_absorption.py`
  (helper, including the warning and the 4-decimal FullProf check)
- `tests/unit/easydiffraction/analysis/calculators/test_cryspy.py`,
  `…/test_crysfml.py` — A(θ) application, including the empty/no-data
  path guard from P1.4.
- `docs/docs/verification/pd-neut-cwl_tch-fcj_lab6.py` — enable
  `absorption.type='cylinder-hewat'`, `mu_r=0.7`; expect it to reach the
  corr that `pd-neut-cwl_tch-fcj-noabs_lab6.py` (μR=0) already passes.

## Implementation steps (Phase 1)

> Code and docs only. No tests in Phase 1 (added in Phase 2). Commit
> each step atomically with explicit paths.

- [x] **P1.1 — Add the `absorption` switchable-category package**
  First add `AbsorptionTypeEnum` (`NONE='none'`,
  `CYLINDER_HEWAT='cylinder-hewat'`) to
  `datablocks/experiment/item/enums.py`, with a `description()` per
  member, mirroring `PeakProfileTypeEnum` (Decision 8). Then create
  `absorption/{base,factory,none,cylinder_hewat,__init__}.py`.
  `AbsorptionBase` mirrors `ExtinctionBase`'s structure
  (`_category_code='absorption'`, `_owner_attr_name='absorption'`,
  `_swap_method_name='_swap_absorption'`) **but the `type` validator
  follows peak**: `MembershipValidator(allowed=[m.value for m in
  AbsorptionTypeEnum])`; `_supported_types` via
  `AbsorptionFactory.supported_for(...)`. `NoAbsorption`
  (`TypeInfo(tag=AbsorptionTypeEnum.NONE.value)`, no params).
  `CylinderHewatAbsorption`
  (`TypeInfo(tag=AbsorptionTypeEnum.CYLINDER_HEWAT.value)`, `mu_r`
  Parameter per Decision 6, CIF
  `_absorption.mu_r` / `_easydiffraction_absorption.mu_r`). Both:
  `Compatibility(powder, bragg)`, `CalculatorSupport(cryspy, crysfml)`.
  `__init__.py` imports all concrete classes (registration).
  `AbsorptionFactory._default_rules = {frozenset(): 'none'}`.
  *Commit:* `Add absorption switchable category package`

- [x] **P1.2 — Wire `absorption` into the powder-Bragg experiment owner**
  In `item/base.py` add `_swap_absorption`/`_replace_absorption`
  mirroring extinction (create via factory, reparent, set `type`),
  include `absorption` in parent-attach and `_serializable_categories`.
  In `item/bragg_pd.py` create `self._absorption` alongside
  `_pref_orient` and expose a read-only `absorption` property. Verify
  total/pdffit experiments never construct it (Compatibility gate).
  **Restore the active type on load (persisted-state boundary):** extend
  `BraggPdExperiment._restore_switchable_types()` in `item/bragg_pd.py`
  (line ~201, where `_background.type` is already read) to also
  `read_cif_str(block, '_absorption.type')` and swap **before** category
  descriptors are loaded — without this a saved `cylinder-hewat`
  experiment is rebuilt as the default `none`, leaving `_absorption.mu_r`
  with no descriptor to receive its value. Mirror the existing
  background/peak restore exactly.
  *Commit:* `Wire absorption category into powder experiment owner`

- [x] **P1.3 — Add the shared Hewat A(θ) helper**
  New `analysis/calculators/absorption.py`:
  `HEWAT_MAX_VALIDATED_MU_R = 1.5`;
  `factor(two_theta, absorption) -> np.ndarray` returning all-ones for
  `type='none'` and the Hewat envelope for `cylinder-hewat`
  (`A = exp(-(1.7133-0.0368·sin²θ)·μR + (0.0927+0.375·sin²θ)·μR²)`,
  θ = radians(two_theta)/2). Emit the single guarded `log.warning`
  when `mu_r > HEWAT_MAX_VALIDATED_MU_R` (Open question 2). Pure NumPy,
  no backend imports.
  *Commit:* `Add Hewat cylindrical absorption factor helper`

- [x] **P1.4 — Apply A(θ) in both backends**
  `cryspy.py`: before `return y_calc`, multiply by
  `absorption.factor(experiment.data.x, experiment.absorption)` when the
  experiment exposes `absorption`. `crysfml.py`: same, in
  `calculate_pattern` before `return np.asarray(y)`, against the same x
  grid. Guard on `hasattr(experiment, 'absorption')` so single-crystal /
  total experiments are unaffected. Identical helper call in both.
  **Preserve the existing "no calculated data" paths:** both backends
  return an empty array on failure — `crysfml.py` catches `KeyError`
  and sets `y = []` (line ~166–168); `cryspy.py` has `return []` paths
  (lines ~289, 301). Apply the correction **only when the pattern is
  non-empty and its length equals `len(experiment.data.x)`**; otherwise
  return the empty/unchanged result. This avoids a NumPy broadcast error
  combining shapes `(0,)` and `(n,)` and keeps the empty-result contract
  intact. (Verified by a Phase 2 no-data test.)
  *Commit:* `Apply absorption correction in cryspy and crysfml backends`

- [ ] **P1.5 — Persist the absorption category in experiment CIF**
  Confirm `_absorption.type` / `_absorption.mu_r` round-trip through the
  standard category serialization (descriptor `CifHandler`); add
  `absorption` to the experiment's serializable categories if not picked
  up automatically. Add IUCr export
  (`_easydiffraction_absorption.*`) in `iucr_writer.py` if the standard
  path does not already emit it.
  *Commit:* `Persist absorption category in experiment CIF`

  > (ADR promotion is **not** a numbered step — it is done in the
  > `/draft-impl-1` Phase A design-history cleanup before P1.1; see the
  > §ADR section.)

- [ ] **P1.6 — Document the sample-absorption parameters**
  Add `docs/docs/user-guide/parameters/absorption.md` (template:
  `parameters/pref_orient.md`): the `absorption.type` selector,
  `cylinder-hewat`, `mu_r`, the Hewat range note and out-of-range
  warning. **Then surface it through the parameter guide:** add
  `absorption.type` and `absorption.mu_r` rows (with the reference link
  to `parameters/absorption.md`) to
  `docs/docs/user-guide/parameters.md` — the leaf page is **not** in the
  global `docs/mkdocs.yml` nav (that directory is deliberately excluded);
  it is discovered only via `parameters.md`. Mirror exactly what #200
  did for `pref_orient`. Touch `docs/mkdocs.yml` only if that precedent
  did.
  *Commit:* `Document sample-absorption parameters`

- [ ] **P1.7 — Phase 1 review gate** (no code)
  Mark this checklist complete and stop for Phase 1 review.
  *Commit:* `Reach Phase 1 review gate`

## Verification (Phase 2)

> Added after Phase 1 review approval. Tests mirror the source tree
> (`test-structure-check`). Use the zsh-safe log-capture pattern when
> saving output.

1. **Add/extend tests** (see Phase-2 file list), including:
   - helper: `none` → ones; Hewat at μR=0.7 matches FullProf to 4
     decimals; warning fires once for μR>1.5.
   - category: factory tags, `show_supported()`, swap, Compatibility
     gating (absent for single-crystal / total).
   - both backends apply A(θ); single-crystal/total unaffected.
   - CIF round-trip of `_absorption.*`.
   - verification page `pd-neut-cwl_tch-fcj_lab6` reaches the target
     corr with `cylinder-hewat`, `mu_r=0.7`.
2. **Run the suite** (capture logs where useful):

   ```bash
   pixi run fix
   pixi run check > /tmp/easydiffraction-check.log 2>&1; check_exit_code=$?; tail -n 200 /tmp/easydiffraction-check.log; exit $check_exit_code
   pixi run test-structure-check
   pixi run unit-tests > /tmp/easydiffraction-unit.log 2>&1; unit_tests_exit_code=$?; tail -n 100 /tmp/easydiffraction-unit.log; exit $unit_tests_exit_code
   pixi run integration-tests
   pixi run script-tests
   ```

   Leave generated `docs/dev/benchmarking/*.csv` untracked. Do not edit
   `docs/dev/package-structure/*.md` by hand (regenerated by
   `pixi run fix`).

## Status checklist

- [ ] Phase A — Promote the ADR to accepted + clean design history
      (done in `/draft-impl-1` setup, before P1.1; see §ADR)
- [x] P1.1 Add the `absorption` switchable-category package
- [x] P1.2 Wire `absorption` into the powder-Bragg experiment owner
      (incl. `_absorption.type` restore on load)
- [x] P1.3 Add the shared Hewat A(θ) helper
- [x] P1.4 Apply A(θ) in both backends (incl. empty/no-data guard)
- [ ] P1.5 Persist the absorption category in experiment CIF
- [ ] P1.6 Document the sample-absorption parameters
- [ ] P1.7 Phase 1 review gate
- [ ] Phase 2 verification complete

## Suggested Pull Request

**Title:** Correct for sample absorption in cylindrical powder
diffraction

**Description:** Powder samples in a cylindrical (Debye–Scherrer)
holder absorb the beam by an amount that varies with scattering angle,
slightly distorting measured peak intensities. EasyDiffraction can now
model this: switch it on with `experiment.absorption.type =
'cylinder-hewat'` and set the sample's `mu_r` (absorption coefficient ×
radius). The correction is applied consistently for both the CrysPy and
CrysFML calculation engines and matches FullProf's cylindrical
correction to four decimal places, removing an intensity mismatch of
several percent for absorbing samples (for example the LaB₆ reference at
μR = 0.7). Values beyond the validated range are still calculated but
now raise a clear warning instead of failing silently. Time-of-flight
and flat-plate geometries are designed for but not yet enabled.
