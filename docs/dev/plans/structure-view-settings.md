# Plan: Uniform value-selector discovery + structure-view settings split

Follows [`AGENTS.md`](../../../AGENTS.md). It applies the standard
two-phase workflow, with one deliberate exception — the implementation
branch (see **Branch & PR** below). The slug `structure-view-settings`
is retained for continuity (it began as the `project.style`
consolidation), but the scope has broadened: Part A introduces a
project-wide selector-discovery convention, and Part B reorganises the
structure-view settings on top of it.

> **Status (closed).** Phase 1 and Phase 2 are complete on the
> `crysview-structure-visualization` branch. The
> `value-selector-discovery` and `crysview-structure-visualization` ADRs
> have both been promoted to accepted. This file is retained as the
> implementation and verification record; no same-slug
> `structure-view-settings` ADR is needed.

**Branch & PR (deliberate exception).** §Planning asks for a flat-slug
`structure-view-settings` branch off `develop`. This plan deliberately
deviates: the work continues on the in-flight
`crysview-structure-visualization` branch because it builds directly on
the structure-view rendering commits already there (not yet on
`develop`) and ships as part of the same crysview feature delivery. The
PR still targets `develop`, not `master`. If the convention work is
later split from the visualization PR, a dedicated
`structure-view-settings` branch off `develop` is the fallback.

## ADR

This plan completed the ADR work that was added during planning. Its two
architectural decisions intentionally live in existing accepted ADRs:
there is no separate `structure-view-settings` ADR because the selector
convention is project-wide and the settings split is part of the
crysview public surface.

- **Accepted ADR — `value-selector-discovery`**. Recognises a **fourth**
  selector shape beyond the three category-level families in
  [`selector-families.md`](../adrs/accepted/selector-families.md):
  - **Category-level selectors** — the backend, switchable-category, and
    active-sibling families. Each _is_ a category and owns
    `<category>.type` + category-level `<category>.show_supported()` per
    [`switchable-category-owned-selectors.md`](../adrs/accepted/switchable-category-owned-selectors.md).
    **Unchanged by this plan.**
  - **Value selectors** — enumerated descriptor _fields_ over a
    project-owned static `(str, Enum)` (no class swap, no `_swap_<name>`
    hook). They gain a descriptor-level `show_supported()` reusing the
    **same** `render_table` and `*`-marks-current convention. This is
    the new half.
- **Update — crysview ADR**
  ([`crysview-structure-visualization.md`](../adrs/accepted/crysview-structure-visualization.md)):
  the structure-view surface becomes three categories; `_style.*` →
  `_structure_style.*`; `show_labels`/`show_moments`/`range_*` move to
  `_structure_view.*`; `_rendering_structure.*` reduces to `type`;
  `atom_view`/`color_scheme` become value selectors with
  `show_supported()`.

## Motivation

Two long-standing inconsistencies, fixed together because Part B depends
on Part A:

1. **Selector discovery is half-built.** Switchable categories expose
   `show_supported()` (e.g. `rendering_plot.show_supported()`), but the
   project-owned enum-backed _value_ selectors
   (`experiment.experiment_type` axes, `verbosity`, the structure
   `atom_view`/`color_scheme`, …) have **no** uniform way to list their
   accepted values. Scientists must read source or trigger a validation
   error to learn the options. (Fields with dynamic or external
   membership — `atom_sites.type_symbol`, `space_group.name_h_m`, … —
   are _not_ value selectors and are out of scope; see the ADR.)
2. **Structure-view settings are split awkwardly.**
   `project.rendering_structure` carries engine + content + region;
   `project.style` (generic `_style.*`) carries appearance — but
   `rendering_plot`/`rendering_table` are pure engine selectors. The
   structure view should match that layering and isolate the appearance
   settings that will keep growing (bonds, polyhedra, lighting, moment
   scale).

## Decisions

- **`EnumDescriptor` (Part A).** A new `core/variable.py` descriptor
  bound to a `(str, Enum)`. It derives `allowed` (the
  `MembershipValidator`) and the default (`Enum.default()`) from the
  enum, stores the enum class, and exposes `show_supported()` rendering
  `render_table(['', 'Value', 'Description'])` with `*` on the current
  value and descriptions from `Enum.description`. Replaces the manual
  `StringDescriptor(... MembershipValidator(allowed=[m.value for m in E]))`
  pattern for value selectors.
- **Enums gain `.default()` and `.description` (Part A).** Every enum
  behind a value selector must expose both; add them where missing.
  Wording is concise, scientist-facing.
- **Scope is project-owned static enum sets only.** A field migrates to
  `EnumDescriptor` only when its allowed set is a project-owned, static
  `(str, Enum)` closed set (`atom_view`, `color_scheme`, the
  `experiment_type` axes, `verbosity`). Two buckets are out of scope and
  unchanged: (a) category-level `.type` selectors — the backend,
  switchable-category, and active-sibling families — keep their
  category-level `show_supported()` per the selector-families and
  switchable ADRs; (b) **dynamic / external / context-dependent**
  membership validators — `atom_sites.type_symbol`,
  `atom_sites.wyckoff_letter`, `space_group.name_h_m`,
  `space_group.it_coordinate_system_code` — keep their current
  `MembershipValidator` (a dynamic-choice discovery surface is deferred
  per the ADR). The P1.2 audit sorts every field into one of these three
  buckets.
- **Numerics stay plain.** `adp_probability`, `atom_scale`, the
  `range_*` scalars, and similar bounded numbers remain
  `NumericDescriptor`s; their limits live in the docstring + validation
  error, not in a `show_supported()` table (nothing to enumerate). This
  resolves the earlier "list all vs enumerated only" question: selectors
  list, scalars document.
- **Three flat sibling categories (Part B).**
  - `rendering_structure` — engine only: `type` (+ the live `viewer`
    facade), `show_supported()` already lists engines. CIF:
    `_rendering_structure.type`.
  - `structure_view` — durable content/region: `show_labels`,
    `show_moments`, and six flat `range_{a,b,c}_{min,max}` scalars. CIF:
    `_structure_view.*`.
  - `structure_style` — durable appearance: `atom_view`, `color_scheme`
    (`EnumDescriptor`s), `adp_probability`, `atom_scale`. CIF:
    `_structure_style.*`.
- **Range stays six flat scalars.** API is `range_a_min … range_c_max`
  (six setters), 1:1 with the six CIF tags, mirroring the six `_cell.*`
  parameters. Keep the internal `view_range()` helper that assembles the
  `((a_min,a_max),(b_min,b_max),(c_min,c_max))` tuple, and the per-call
  `range=` override on `display.structure()` (per the crysview ADR). No
  tuple-valued public setter.
- **Per-descriptor discovery only.** `show_supported()` lives on the
  value selector itself
  (`structure_style.color_scheme.show_supported()`), never on the bundle
  category. Switchable categories keep their category-level
  `show_supported()` because the category _is_ a single selector; a
  multi-setting bundle has no single "supported values", so a method
  there would be ambiguous and redundant. An `experiment_type` overview
  (its four axes shown together) may be added later as a clearly-named
  convenience — deferred, not part of this change.
- **No nesting, no deeper tree.** `color_scheme.show_supported()` is a
  method on the descriptor the getter already returns — not a
  sub-category. The category tree depth is unchanged.
- **CIF renames (beta → no shim).** `_style.*` is dropped;
  `_structure_view.*` and `_structure_style.*` are added;
  `_rendering_structure.*` reduces to `type`. No backward-compatible
  reader.
- **Defaults preserved.** Keep current defaults during the move
  (`adp_probability`, `atom_scale`, the show flags, range bounds, every
  migrated selector's default).

## Open questions

None outstanding:

- **Naming — resolved.** `structure_view` / `structure_style` (CIF
  `_structure_view.*` / `_structure_style.*`), confirmed.
- **Discovery surface — resolved.** Per-descriptor `show_supported()`
  only; no category-level method on the non-switchable bundle categories
  (see Decisions).
- **Selector classification** is handled by the P1.2 audit (three
  buckets: value selector / category-level selector / dynamic-external)
  and recorded in this plan during implementation.

## Concrete files likely to change

**Part A — convention + project-wide migration**

- `src/easydiffraction/core/variable.py` — add `EnumDescriptor`; reuse
  `render_table` from `utils/utils.py`.
- `src/easydiffraction/core/validation.py` — only if a small helper
  eases deriving `allowed` from an enum.
- Value-selector enums (add `.default()`/`.description` where missing):
  `display/structure/enums.py` (`AtomViewEnum`, `ColorSchemeEnum`),
  `datablocks/experiment/categories/experiment_type/*` (sample_form,
  beam_mode, radiation_probe, scattering_type),
  `project/categories/verbosity/*`, and any others the audit confirms as
  project-owned closed sets. **Excluded** (dynamic or external
  membership, unchanged): `atom_sites.type_symbol`,
  `atom_sites.wyckoff_letter`, `space_group.name_h_m`,
  `space_group.it_coordinate_system_code`.
- The category files that declare those value selectors → switch the
  field declarations to `EnumDescriptor` (one commit per area; see Phase
  1).

**Part B — structure-view three-way split**

- `src/easydiffraction/project/categories/rendering_structure/default.py`
  — remove `show_labels`/`show_moments`/`range_*`; keep `type` +
  `viewer`.
- `src/easydiffraction/project/categories/structure_view/` — **new**
  package (`__init__.py`, `default.py`, `factory.py`): the moved
  content/region settings
  - `view_range()`.
- `src/easydiffraction/project/categories/structure_style/` —
  **renamed** from `style/`: `atom_view`/`color_scheme` as
  `EnumDescriptor`, `adp_probability`/ `atom_scale` as
  `NumericDescriptor`; CIF `_structure_style.*`.
- `src/easydiffraction/project/categories/style/` — **removed**.
- `src/easydiffraction/project/project.py`,
  `src/easydiffraction/project/project_config.py` — add
  `project.structure_view` / `project.structure_style`; drop
  `project.style`.
- `src/easydiffraction/io/cif/serialize.py` — swap the `style` block for
  the `structure_view` + `structure_style` blocks; trim
  `rendering_structure`.
- `src/easydiffraction/display/structure/builder.py`,
  `src/easydiffraction/project/display.py`,
  `src/easydiffraction/report/html_renderer.py`,
  `src/easydiffraction/report/tex_renderer.py` — repoint `style=` to
  `project.structure_style` and read the view window/flags from
  `project.structure_view`.

**Docs / tutorials / tests**

- `docs/docs/user-guide/analysis-workflow/model.md` (the
  `project.style.*` examples); the crysview ADR; the new
  `value-selector-discovery` ADR.
- `docs/docs/tutorials/ed-3.py`, `ed-14.py`, `ed-17.py` (any
  `project.style.*`), then `pixi run notebook-prepare`.
- Tests mirroring every changed module: `EnumDescriptor` +
  `show_supported`, each migrated category, new
  `structure_view`/`structure_style`, removed `style`; repoint
  `tests/.../project/test_project_config.py`, `test_project_load.py`,
  `display/plotters/test_plotly.py`. Verify the mirror with
  `pixi run test-structure-check`.

## Implementation steps (Phase 1)

Each step is one atomic commit (stage explicit paths; commit before the
next) per §Commits. When an AI agent follows this plan, every completed
Phase 1 step is staged and committed locally before moving on.

**Part A — value-selector discovery convention**

- [x] **P1.1 — Add `EnumDescriptor`.** Implement in `core/variable.py`
      with the `show_supported()` table (reuse `render_table`). Commit:
      `Add EnumDescriptor with show_supported listing`.
- [x] **P1.2 — Classify selectors.** Audit every `MembershipValidator`
      usage; record a three-bucket table in this plan (value selector /
      category-level selector / dynamic-external), doc-only. See
      _Selector classification_ below. Commit:
      `Classify enumerated selectors for discovery`.
- [x] **P1.3 — Enum metadata.** Add `.default()`/`.description()` to the
      in-scope value-selector enums that lack them (no field migration
      yet). Commit:
      `Add default and description to value-selector enums`. _(Only
      `VerbosityEnum`, `FitResultKindEnum`, `FitCorrelationSourceEnum`
      lacked `description()`; the rest already had both.)_
- [x] **P1.4 — Migrate experiment_type axes.** `sample_form`,
      `beam_mode`, `radiation_probe`, `scattering_type` →
      `EnumDescriptor`. Commit:
      `Use EnumDescriptor for experiment_type axes`.
- [x] **P1.5 — Migrate `atom_sites.adp_type`.** The P1.2 audit confirms
      `adp_type` (`AdpTypeEnum`) is the one in-scope structure-data
      value selector → `EnumDescriptor` (preserve its dual CIF names
      `_atom_site.ADP_type` / `_atom_site.adp_type` and the category's
      `adp_type` setter). The dynamic/external validators
      (`atom_sites.type_symbol`, `atom_sites.wyckoff_letter`,
      `space_group.name_h_m`, `space_group.it_coordinate_system_code`)
      are **out of scope** and keep their current `MembershipValidator`.
      Commit: `Use EnumDescriptor for atom_sites adp_type`.
- [x] **P1.6 — Migrate remaining value selectors.** Per the P1.2 audit:
      `verbosity.fit` (`VerbosityEnum`), `fit_result.result_kind`
      (`FitResultKindEnum`), `fit_parameter_correlations.source_kind`
      (`FitCorrelationSourceEnum`), and `extinction.model`
      (`ExtinctionModelEnum`) → `EnumDescriptor`, one commit per area.
      Commit (per area): `Use EnumDescriptor for <area> selector`.

**Part B — structure-view three-way split.** Ordered additive-first: the
new categories and their consumers land before the old surfaces are
removed, so **every commit imports and renders** — no intermediate
revision loses a live API. A short bridge period where old and new
surfaces coexist is intentional.

- [x] **P1.7 — Add `structure_view` (additive).** New category +
      `project.structure_view` + a new `_structure_view.*` CIF block
      carrying `show_labels`, `show_moments`, six `range_*` scalars, and
      `view_range()`. `rendering_structure` keeps its copies for now.
      Commit: `Add structure_view content/region category`.
- [x] **P1.8 — Add `structure_style` (additive).** New category +
      `project.structure_style` + a new `_structure_style.*` CIF block;
      `atom_view`/`color_scheme` as `EnumDescriptor`,
      `adp_probability`/`atom_scale` as `NumericDescriptor`. The old
      `style` category / `project.style` stay for now. Commit:
      `Add structure_style appearance category`.
- [x] **P1.9 — Repoint consumers to the new categories.** Builder,
      display facade, and report renderers read appearance from
      `project.structure_style` and the window/flags from
      `project.structure_view` (`builder.py`, `display.py`,
      `html_renderer.py`, `tex_renderer.py`). After this commit nothing
      reads `project.style` or `rendering_structure.view_range()`, but
      both still exist — so the revision builds and renders. Commit:
      `Read structure view and style from new categories`.
- [x] **P1.10 — Remove the old surfaces.** Now that no consumer uses
      them: remove `show_labels`/`show_moments`/`range_*`/`view_range()`
      from `rendering_structure` (leaving engine `type` + `viewer`);
      remove the `style` package, `project.style`, and the bespoke
      `Style.show_supported()`; drop the `_style.*` block and the moved
      `_rendering_structure.*` tags from CIF serialise. Commit:
      `Remove the old style and rendering_structure surfaces`.
- [x] **P1.11 — Docs, ADRs, tutorials.** `model.md` (commit
      `e24a42571`), crysview ADR §8 surface note + final CIF tags
      (commit `44abff413`), `value-selector-discovery` ADR already
      current. Tutorials `ed-3/14/17.py` migrated to
      `project.structure_style.*` (per-descriptor `show_supported()`)
      and notebooks regenerated via `pixi run notebook-prepare`,
      committed in `6fb2df3c7` (user approved committing their
      playground edits alongside).
- [x] **P1.12 — Phase 1 review gate.** No-code step: mark complete and
      commit the checklist update alone. (Reopened once by
      `_impl-review-1` [P1]; re-gated after the tutorial migration
      landed in `6fb2df3c7`.) Commit: `Reach Phase 1 review gate`.

### Selector classification (P1.2 audit)

Every `MembershipValidator` site, sorted into the three buckets from the
`value-selector-discovery` ADR, plus a fourth not-yet-enum-backed group.

**Migrate to `EnumDescriptor` (project-owned static `(str, Enum)`):**

| Field                                    | Enum                       | Step | Note                            |
| ---------------------------------------- | -------------------------- | ---- | ------------------------------- |
| `experiment_type.sample_form`            | `SampleFormEnum`           | P1.4 | has `display_handler`           |
| `experiment_type.beam_mode`              | `BeamModeEnum`             | P1.4 | has `display_handler`           |
| `experiment_type.radiation_probe`        | `RadiationProbeEnum`       | P1.4 | has `display_handler`           |
| `experiment_type.scattering_type`        | `ScatteringTypeEnum`       | P1.4 | has `display_handler`           |
| `atom_sites.adp_type`                    | `AdpTypeEnum`              | P1.5 | dual CIF names; category setter |
| `verbosity.fit`                          | `VerbosityEnum`            | P1.6 |                                 |
| `fit_result.result_kind`                 | `FitResultKindEnum`        | P1.6 |                                 |
| `fit_parameter_correlations.source_kind` | `FitCorrelationSourceEnum` | P1.6 |                                 |
| `extinction.model`                       | `ExtinctionModelEnum`      | P1.6 |                                 |
| `style.atom_view`                        | `AtomViewEnum`             | P1.8 | already has metadata            |
| `style.color_scheme`                     | `ColorSchemeEnum`          | P1.8 | already has metadata            |

**Category-level `.type` selectors — unchanged** (backend /
switchable-category / active-sibling families): `rendering_plot`,
`rendering_table`, `rendering_structure`, `minimizer`, `background`,
`peak`, `calculator`, `extinction`, `fitting_mode`.

**Dynamic / external / context-dependent — unchanged:**
`atom_sites.type_symbol` (isotope database), `atom_sites.wyckoff_letter`
(space-group dependent), `space_group.name_h_m` /
`space_group.it_coordinate_system_code` (callable, H-M-derived),
minimizer `initialization_method` (per-class enum **subset**, not the
full set).

**Bucket 4 — closed but not `(str, Enum)`, out of scope** (candidates
for a future enum-ification per `enum-backed-closed-values`, tracked
separately): `data.calc_status` (`['incl', 'excl']`),
`emcee.proposal_moves` (raw tuple).

## Phase 2 — Verification

This Phase 2 also discharges the crysview feature's originally planned
unit tests (the
[`crysview-structure-visualization`](crysview-structure-visualization.md)
plan's original Phase 2 checklist was superseded), written **once**
against the final post-split API:

- **This plan's surfaces:** `EnumDescriptor` + per-selector
  `show_supported()`; each migrated value selector; the new
  `structure_view` / `structure_style` categories; removal of `style`;
  the slimmed `rendering_structure`.
- **Crysview surfaces still untested:** `display/structure/` —
  `test_enums.py`, `test_scene.py`, `test_builder.py`,
  `renderers/test_ascii.py`, `renderers/test_raster.py`,
  `renderers/test_threejs.py`, `test_viewing.py`; the crystallography
  geometry helpers; the element-radii asset;
  `report/test_html_renderer.py` (structure figure); and the structure
  surfaces of `project/test_display.py`.

Mirror the source tree per §Testing (verify with
`pixi run test-structure-check`), then run, capturing logs with the
zsh-safe pattern:

```sh
pixi run fix
pixi run check > /tmp/easydiffraction-check.log 2>&1; check_exit_code=$?; tail -n 200 /tmp/easydiffraction-check.log; exit $check_exit_code
pixi run test-structure-check
pixi run unit-tests > /tmp/easydiffraction-unit.log 2>&1; unit_tests_exit_code=$?; tail -n 100 /tmp/easydiffraction-unit.log; exit $unit_tests_exit_code
pixi run integration-tests > /tmp/easydiffraction-integration.log 2>&1; integration_tests_exit_code=$?; tail -n 100 /tmp/easydiffraction-integration.log; exit $integration_tests_exit_code
pixi run script-tests > /tmp/easydiffraction-script.log 2>&1; script_tests_exit_code=$?; tail -n 100 /tmp/easydiffraction-script.log; exit $script_tests_exit_code
```

## Suggested Pull Request

**Title:** Make every option list discoverable, and tidy structure-view
settings

**Description:** Any setting that takes one of a fixed list of values —
the experiment type, atom depiction, colour scheme, verbosity, and more
— can now show its options the same way, with the active one marked, via
`show_supported()`. Separately, the structure-view settings are
reorganised to match the rest of the project:
`project.rendering_structure` now just selects the engine,
`project.structure_view` holds what and where to draw, and
`project.structure_style` holds how it looks. Structure-view settings
saved by older versions (the `_style.*` block) need re-applying (beta:
no automatic migration).
