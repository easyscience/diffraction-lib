# Plan: β-tensor (dimensionless) anisotropic ADP support

Follows the conventions in [`AGENTS.md`](../../../AGENTS.md). No
deliberate exceptions to those instructions are taken by this plan.

## Status checklist

See [Implementation steps (Phase 1)](#implementation-steps-phase-1) for
the per-step checklist. High-level:

- [ ] Phase 1 — Implementation (code + docs + ADR)
- [ ] Phase 1 review gate
- [ ] Phase 2 — Verification (tests + `pixi` gate)

## ADR

This feature **extends an existing accepted ADR**,
[`type-neutral-adp-parameters.md`](../adrs/accepted/type-neutral-adp-parameters.md).
No new ADR is required. The ADR already mandates type-neutral parameter
names (`adp_iso`, `adp_11`…`adp_23`) interpreted through
`atom_site.adp_type`; β is a third anisotropic interpretation of the
same `adp_11`…`adp_23` objects. The ADR is updated by this work with an
**Extension** section recording the β decision, the cell-dependent
conversion, and the dimensionless-units caveat (Phase 1, step P1.1).

Related accepted ADRs to keep consistent (read before touching their
surfaces):
[`enum-backed-closed-values.md`](../adrs/accepted/enum-backed-closed-values.md)
(the `AdpTypeEnum` extension),
[`iucr-cif-tag-alignment.md`](../adrs/accepted/iucr-cif-tag-alignment.md)
and
[`python-cif-category-correspondence.md`](../adrs/accepted/python-cif-category-correspondence.md)
(the new `_atom_site_aniso.beta_*` CIF tags),
[`guarded-public-properties.md`](../adrs/accepted/guarded-public-properties.md)
(no new public setters added).

## Branch & PR

- Branch: `adp-beta-tensor` (flat slug off `develop`, no `feature/`
  prefix). PR targets `develop`. Do not push until asked.

## Background — current state

Atomic displacement parameters today support four `AdpTypeEnum` members:
`Biso`, `Uiso`, `Bani`, `Uani`
(`src/easydiffraction/datablocks/structure/categories/atom_sites/enums.py`).
Per the type-neutral ADR the public values live in `atom_site.adp_iso`
(isotropic) and the always-present sibling collection `atom_site_aniso`
(`adp_11`…`adp_23`), with `atom_site.adp_type` selecting B-vs-U and
iso-vs-ani.

The **dimensionless β tensor** — the third standard anisotropic ADP
convention, used by FullProf, SHELX-era data, and cryspy internally — is
**not** accepted on input or emitted on output. Today:

- `AdpTypeEnum` has no `beta` member.
- The B↔U type-switch conversion in `AtomSite._convert_adp_values` is a
  pure scalar (`B = 8π²U`); it has no cell access and cannot do the β
  transform.
- The aniso `adp_ij` parameters declare `units='angstrom_squared'` and
  display `Å²`; β components are dimensionless.
- The aniso **off-diagonal** validators (`adp_12`/`adp_13`/`adp_23`)
  already use an unrestricted `RangeValidator()` (negatives allowed);
  only the **diagonal** components (`adp_11`/`adp_22`/`adp_33`) carry
  `RangeValidator(ge=0.0, le=10.0)`. β diagonals are ~1e-3 (well within
  `[0, 10]`) and β off-diagonals (small, routinely negative) are already
  accepted, so **no validator change is needed** for β (resolved Q4).
- `io/cif/iucr_writer.py::_adp_family()` returns `'B'` or `'U'` from the
  first letter of `adp_type`; `'beta'` starts with `'b'` and would be
  mis-classified as `'B'`. The writer is otherwise already
  family-parameterized (`_atom_site_aniso.{family}_11`), so a `beta`
  family slots in naturally.
- The cryspy backend already converts B/U→β via
  `CryspyCalculator._update_aniso_beta` using
  `β_ij = 2π²·U_ij·a*_i·a*_j`; native β input can pass through with no
  conversion.
- The crysfml backend (`_convert_structure_to_dict`) sends **only**
  `_B_iso_or_equiv` and `_adp_type` — it does **not** currently send the
  anisotropic tensor at all. Anisotropic support on the crysfml side is
  therefore a pre-existing gap, not introduced here; β on crysfml is out
  of scope for this plan (see Open questions Q3).

Conversion math (reciprocal lengths `a* b* c*`):

```
β_11 = 2π²·a*²·U_11      U_11 = β_11 / (2π²·a*²)
β_22 = 2π²·b*²·U_22      U_22 = β_22 / (2π²·b*²)
β_33 = 2π²·c*²·U_33      U_33 = β_33 / (2π²·c*²)
β_12 = 2π²·a*·b*·U_12    U_12 = β_12 / (2π²·a*·b*)
β_13 = 2π²·a*·c*·U_13    U_13 = β_13 / (2π²·a*·c*)
β_23 = 2π²·b*·c*·U_23    U_23 = β_23 / (2π²·b*·c*)
```

with `B = 8π²U`. A reciprocal-length computation already exists
**privately** in `display/structure/builder.py` (`_reciprocal_lengths`,
used for ADP-ellipsoid rendering), but it is not reusable from the model
layer where the type-switch conversion runs. This work adds a shared
`crystallography.reciprocal_cell_lengths` (the model-layer source of
truth) and routes the existing builder helper through it (consolidation,
step P1.9), rather than leaving two copies of the same math.

## Decisions

1. **β is a first-class stored anisotropic ADP type**, symmetric with
   `Bani`/`Uani`. Add `AdpTypeEnum.BETA = 'beta'`. When
   `adp_type == 'beta'`, the `adp_11`…`adp_23` objects hold the
   dimensionless β components directly. Rationale: round-trips β CIFs,
   matches the existing first-class Bani/Uani pattern, and feeds cryspy
   (which is β-native) without a conversion. (Alternative — β as an
   I/O-only encoding that converts to Uani on read — is recorded under
   Open questions Q1 for the user to choose; this plan proceeds on the
   first-class decision unless overridden.)

2. **β has no isotropic form.** `'beta'` always implies anisotropic.
   Switching _to_ `beta` from an isotropic type seeds the tensor like
   the existing iso→ani path, then converts U→β; switching _from_ `beta`
   to an isotropic type converts β→U and collapses the diagonal, reusing
   the existing collapse path.

3. **Cell-dependent conversion via a new easydiffraction geometry
   helper.** Add a reciprocal-length helper (`a* b* c*` from
   `a b c α β γ`) to
   `src/easydiffraction/crystallography/crystallography.py` — the
   existing crystallographic-math module (Wyckoff positions,
   space-group symmetry constraints), which already hosts this kind of
   domain geometry. (`core/` is the wrong home: it must stay
   domain-free; `crystallography/` is the established place for
   crystallographic math.) β↔U/B conversion routes through the parent
   structure's `cell`; when no parent cell is reachable (atom
   constructed in isolation) the type switch raises a clear error rather
   than silently producing wrong numbers — this is a boundary-input edge
   case per §Project Context. Do **not** depend on cryspy's reciprocal
   helper for the ed-side conversion, so the model-layer type switch
   stays independent of any calculator backend. The same shared helper
   replaces the duplicate private `_reciprocal_lengths` in
   `display/structure/builder.py` (step P1.9).

4. **Type-aware display units for aniso components.** When the owning
   `adp_type` is `beta`, the `adp_ij` display shows no `Å²` unit (β is
   dimensionless); B/U families keep `Å²`. Implement as a display-layer
   lookup on `adp_type`, not by mutating the Parameter's stored unit
   metadata (which stays a single declared unit per the value model).

5. **CIF tags.** Register `_atom_site_aniso.beta_11`…`beta_23` on the
   aniso `adp_ij` `CifHandler` name lists (alongside the existing
   `B_ij`/`U_ij`). Extend `_adp_family()` to return `'beta'` for
   `adp_type == 'beta'` (check the full value, not the first letter), so
   the writer emits a `beta` loop and groups β atoms separately. On
   read, a CIF carrying `_atom_site_aniso.beta_*` sets
   `adp_type = 'beta'` and stores the β values verbatim. **Both** CIF
   writers need the `beta` family: the report writer
   (`iucr_writer.py::_adp_family`, step P1.7) **and** the project
   serializer (`io/cif/serialize.py` — new `_ADP_FAMILY_BETA`, a `beta`
   branch in `_adp_family_from_type`, and a `beta` entry in the
   `_group_items_by_adp_family` grouping dict, step P1.8). The serializer
   is what makes project save/load round-trip β; without it β atoms would
   silently serialize as a B loop.

6. **cryspy backend.** In `_update_aniso_beta`, add a `BETA` branch that
   writes the stored β straight into `cryspy_beta` (no U→β transform),
   and include `BETA` in the `aniso_types` set in `_set_atom_adps` so
   `b_iso` is zeroed for β atoms too. cryspy's β convention is confirmed
   to match the CIF/SHELX `β_ij = 2π²·U_ij·a*_i·a*_j`:
   `_update_aniso_beta` already documents that formula and converts B/U
   through cryspy's `calc_beta_by_u`, using reciprocal lengths from
   `calc_reciprocal_by_unit_cell_parameters` (resolved Q2).

> **Dropped (was decision 5): off-diagonal validator relaxation.**
> Verification against current code shows the aniso off-diagonal
> validators are already unrestricted `RangeValidator()`; only the
> diagonals carry `RangeValidator(ge=0.0, le=10.0)`, and β values sit
> within those bounds. No validator change is needed, so the earlier
> planned relaxation is removed from scope (resolved Q4).

## Open questions

- **Q1 (representation). RESOLVED — first-class stored β** (confirmed
  2026-06-10). β is a persisted `adp_type` holding β values directly in
  `adp_11`…`adp_23`; the I/O-only-normalise-to-`Uani` alternative is
  rejected. Decision 1 stands.
- **Q2 (cryspy β convention). RESOLVED — convention matches** (confirmed
  2026-06-10 by code read). cryspy's `_update_aniso_beta` already
  documents `β_ij = 2π²·U_ij·a*_i·a*_j` and routes B/U through cryspy's
  `calc_beta_by_u` with reciprocal lengths from
  `calc_reciprocal_by_unit_cell_parameters`. Native β can pass through
  unscaled (decision 6, step P1.6).
- **Q3 (crysfml scope). RESOLVED — out of scope** (confirmed
  2026-06-10). β works on cryspy only this PR; crysfml's missing
  anisotropic-tensor wiring is a pre-existing gap tracked separately,
  not addressed here and not given a stop-gap.
- **Q4 (validator loosening). RESOLVED — no change needed** (confirmed
  2026-06-10 by code read). The aniso off-diagonal validators are
  already unrestricted `RangeValidator()`; only diagonals carry
  `RangeValidator(ge=0.0, le=10.0)`, and β values sit within those
  bounds. The earlier planned relaxation (former decision 5) is dropped
  from scope.
- **Q5 (creation-API UX). RESOLVED — separate ADR + plan** (confirmed
  2026-06-10). A richer atom-creation API (e.g. `b_iso=`/`u_iso=`/
  `beta=` convenience kwargs that set `adp_type` automatically, or
  CIF-style auto-attach of the sibling iso/aniso values) would improve
  discoverability but **revisits the accepted type-neutral ADP ADR** and
  is independent of the β math. It is **out of scope** for this PR;
  tracked as a follow-up issue in `docs/dev/issues/open.md` and to be
  designed in its own ADR + plan. This β work stays strictly inside the
  type-neutral model (β is a fourth `adp_type`).
- **Q6 (β ADP-ellipsoid display). RESOLVED — deferred** (confirmed
  2026-06-10). Implementation found that `display/structure/builder.py`
  draws ADP ellipsoids only for `Bani`/`Uani` and carries its own
  reciprocal-length math. Drawing β ellipsoids would need a β→U
  conversion in the renderer. That is **out of scope**: β atoms render
  as spheres for now (no crash, no wrong ellipsoid), tracked as a
  follow-up issue in `docs/dev/issues/open.md` (step P1.9). The
  duplicate `_reciprocal_lengths` helper is still consolidated onto the
  shared helper (step P1.9); only the ellipsoid math is deferred.

## Concrete files likely to change

Source:

- `src/easydiffraction/datablocks/structure/categories/atom_sites/enums.py`
  — add `AdpTypeEnum.BETA`, its `description()` entry, `default()`
  unaffected.
- `src/easydiffraction/datablocks/structure/categories/atom_sites/default.py`
  — `_convert_adp_values` β branches; cell access for the transform;
  iso↔β seeding/collapse hooks.
- `src/easydiffraction/datablocks/structure/categories/atom_site_aniso/default.py`
  — `_atom_site_aniso.beta_*` CIF names; type-aware display units (no
  validator change — off-diagonals already accept negatives).
- `src/easydiffraction/crystallography/crystallography.py` — new
  reciprocal-cell length helper (`a* b* c*` from `a b c α β γ`; pure
  geometry, sits with the existing crystallographic math).
- `src/easydiffraction/datablocks/structure/item/base.py` — only if the
  cell back-reference for conversion needs wiring through the structure.
- `src/easydiffraction/io/cif/iucr_writer.py` — `_adp_family()` β case;
  confirm `_atom_site_aniso_tags('beta')` and the section header read
  correctly.
- `src/easydiffraction/io/cif/serialize.py` — `beta` ADP family for
  project CIF round-trip (`_ADP_FAMILY_BETA`, `_adp_family_from_type`,
  `_group_items_by_adp_family`).
- `src/easydiffraction/display/structure/builder.py` — route the private
  `_reciprocal_lengths` through `crystallography.reciprocal_cell_lengths`
  (consolidation); β atoms render as spheres (ellipsoid display
  deferred, Q6).
- `src/easydiffraction/analysis/calculators/cryspy.py` —
  `_update_aniso_beta` β passthrough; `aniso_types` includes `BETA`.
- `src/easydiffraction/datablocks/structure/item/base.py` and the
  `atom_sites`/`atom_site_aniso` categories — extend the `{Bani, Uani}`
  "is-anisotropic" membership sets to include `beta` (step P1.3).

Docs / ADR:

- `docs/dev/adrs/accepted/type-neutral-adp-parameters.md` — Extension
  section (step P1.1).
- `docs/dev/issues/open.md` — add a follow-up row for the ADP
  creation-API UX (resolved Q5; step P1.1).

Tests (Phase 2):

- `tests/unit/easydiffraction/datablocks/structure/categories/test_atom_sites.py`
- `tests/unit/easydiffraction/datablocks/structure/categories/test_atom_site_aniso.py`
- `tests/functional/test_adp_switching.py`
- `tests/unit/easydiffraction/analysis/calculators/test_cryspy.py`
- `tests/unit/easydiffraction/io/cif/test_iucr_writer.py`,
  `test_serialize.py`
- reciprocal-cell helper tests in
  `tests/unit/easydiffraction/crystallography/test_crystallography.py`.
- `tests/unit/easydiffraction/display/structure/test_builder.py` — the
  reciprocal-helper consolidation regression.

## Implementation steps (Phase 1)

Each step is one atomic commit. Stage only the files the step touches
(explicit paths). Commit locally before starting the next step.

- [x] **P1.1 — ADP ADR extension + follow-up note.** Ensure the
      _Extension_ section in `type-neutral-adp-parameters.md` records the
      β decision (decisions 1–6 above): first-class `beta` type,
      cell-dependent conversion, dimensionless-units display handling,
      and the new CIF tags. Verify it states that off-diagonal negatives
      are *already* permitted (a statement of existing behaviour), not a
      newly introduced relaxation. Also add the ADP creation-API UX
      follow-up row to `docs/dev/issues/open.md` (resolved Q5). Keep the
      original Decision/Consequences intact. Stage the ADR and `open.md`.
      Commit: `Extend type-neutral ADP ADR with beta tensor`
- [x] **P1.2 — Reciprocal-cell helper.** Add a pure-geometry helper
      returning `(a*, b*, c*)` from `(a, b, c, α, β, γ)` to
      `crystallography/crystallography.py` (the crystallographic-math
      module). Commit: `Add reciprocal-cell length helper`
- [x] **P1.3 — `AdpTypeEnum.BETA`.** Add the member and its
      `description()`. Extend the "is-anisotropic" `{Bani, Uani}`
      membership sets to include `beta` so β atoms get an aniso row and
      are treated as anisotropic: `item/base.py` (aniso-row sync),
      `atom_sites/default.py` (symmetry-constrained flag and
      collapse-from-aniso), and `atom_site_aniso/default.py` (iso-only
      check). **Leave the B-vs-U sets** (`{Biso, Bani}` / `{Uiso,
      Uani}`) unchanged — β is neither B nor U. **Leave
      `display/structure/builder.py`'s display-shape sets unchanged** so
      β atoms fall through to the sphere branch (ellipsoids deferred, Q6).
      The cryspy `aniso_types` set is handled in P1.6. Search
      `git grep -n "AdpTypeEnum\."`. Commit: `Add beta member to AdpTypeEnum`
- [x] **P1.4 — aniso category: CIF names + display units.** Add
      `_atom_site_aniso.beta_*` to the `adp_ij` CIF handlers (decision
      5); type-aware display units that suppress `Å²` when
      `adp_type == 'beta'` (decision 4). No validator change — the
      off-diagonals already accept negatives. Commit:
      `Support beta tensor in atom_site_aniso category`
- [ ] **P1.5 — type-switch conversion.** Extend `_convert_adp_values`
      with β↔U/B branches using the reciprocal-cell helper and the
      parent `cell`; raise a clear error when no cell is reachable; wire
      iso↔β seeding/collapse. Commit:
      `Convert ADP values to and from the beta tensor`
- [ ] **P1.6 — cryspy passthrough.** Add the `BETA` branch in
      `_update_aniso_beta` (store β directly, no U→β transform) and
      include `BETA` in `aniso_types`. cryspy convention already
      confirmed (resolved Q2). Commit:
      `Pass beta tensor straight through to cryspy`
- [ ] **P1.7 — CIF report writer family.** In `io/cif/iucr_writer.py`,
      extend `_adp_family()` to return `'beta'` for `adp_type == 'beta'`
      (full-value check, not first letter); verify the aniso loop tags
      and section header for the β family. Commit:
      `Emit beta tensor in the atom_site_aniso CIF loop`
- [ ] **P1.8 — Project CIF serializer family.** In `io/cif/serialize.py`
      add `_ADP_FAMILY_BETA`, return it from `_adp_family_from_type()`
      for `adp_type == 'beta'`, and add a `beta` group to
      `_group_items_by_adp_family()`. This is what makes project
      save/load round-trip β. Commit:
      `Round-trip beta tensor through the project CIF serializer`
- [ ] **P1.9 — Consolidate reciprocal helper; defer β ellipsoids.**
      Refactor `display/structure/builder.py::_reciprocal_lengths` to
      call `crystallography.reciprocal_cell_lengths` (remove the
      duplicate math; keep the `np.ndarray` return shape its callers
      expect). β atoms keep rendering as spheres; add a follow-up issue
      to `docs/dev/issues/open.md` for β→U ADP-ellipsoid display
      (resolved Q6). Commit:
      `Reuse shared reciprocal helper in structure builder`
- [ ] **P1.10 — Phase 1 review gate.** No-code step. Mark complete,
      commit the checklist update alone. Commit:
      `Reach Phase 1 review gate`

## Verification (Phase 2)

Add/extend the tests listed under _Concrete files_, then run the gate.
Capture logs with the zsh-safe pattern when output is needed:

```
pixi run fix
pixi run check > /tmp/easydiffraction-check.log 2>&1; check_exit_code=$?; tail -n 200 /tmp/easydiffraction-check.log; exit $check_exit_code
pixi run unit-tests > /tmp/easydiffraction-unit.log 2>&1; unit_tests_exit_code=$?; tail -n 200 /tmp/easydiffraction-unit.log; exit $unit_tests_exit_code
pixi run integration-tests > /tmp/easydiffraction-integration.log 2>&1; integration_tests_exit_code=$?; tail -n 200 /tmp/easydiffraction-integration.log; exit $integration_tests_exit_code
pixi run script-tests > /tmp/easydiffraction-script.log 2>&1; script_tests_exit_code=$?; tail -n 200 /tmp/easydiffraction-script.log; exit $script_tests_exit_code
```

`pixi run test-structure-check` to confirm any new test module mirrors
its source path. `pixi run fix` regenerates the package-structure docs —
do not hand-edit those.

Test coverage to add:

- reciprocal-cell helper numerics (orthorhombic + triclinic case).
- β↔U and β↔B round-trip within tolerance, using a known cell.
- type switches: `Uani↔beta`, `Bani↔beta`, `Uiso→beta`, `beta→Biso`,
  with parameter-object identity preserved (per the ADR) and a clear
  error when no parent cell is present.
- regression guard: negative off-diagonal accepted (already-existing
  behaviour that β relies on); diagonal still rejects negatives.
- CIF round-trip: read a `_atom_site_aniso.beta_*` loop →
  `adp_type == 'beta'` → write emits the β loop unchanged (both
  `iucr_writer` and the project `serialize` paths).
- project save/load round-trip: a β atom saved via `serialize.py` and
  reloaded keeps `adp_type == 'beta'` and its β values (verifies the new
  serializer `beta` family).
- builder helper consolidation: `display/structure/builder.py`
  reciprocal lengths match the pre-refactor values for a known cell
  (regression guard around the P1.9 change).
- cryspy: β atom zeroes `b_iso` and populates `atom_beta` with the
  stored values.

## Suggested Pull Request

**Title:** Support the β-tensor anisotropic displacement convention

**Description:** EasyDiffraction can now read, store, refine, and write
atomic displacement parameters in the dimensionless **β-tensor**
convention, alongside the existing B and U (isotropic and anisotropic)
forms. This lets you load structures and FullProf/SHELX-style data that
report anisotropic displacements as β values without hand-converting
them, switch an atom between β, U, and B with the values converted
automatically using the unit cell, and export β tensors back to CIF.
Off-diagonal displacement components may now be negative, as the physics
requires.
