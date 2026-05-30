# Plan: crysview Structure Visualization

Implementation plan for the
[`crysview-structure-visualization`](../adrs/suggestions/crysview-structure-visualization.md)
ADR. Follows [`AGENTS.md`](../../../AGENTS.md) — no deliberate
exceptions to those instructions.

> **Context for this plan.** This is a **greenfield feature**: there is
> no prior crysview implementation on the branch. The ADR review cycle
> closed at the review-5 sentinel ("No findings. Ready to commit."), so
> the design below is settled; this plan only makes it concrete. It is a
> **single comprehensive plan** covering both shipping engines (ASCII +
> Three.js), the new `view` and `style` categories, the
> `project.display.structure()` surface, CIF persistence, Three.js
> bundling, the HTML-report structure figure, and tutorials — one
> branch, one PR — matching the slug invoked and the project precedent
> ([`project-summary-rendering`](project-summary-rendering.md) was one
> large plan). The Phase 1 steps are ordered foundation-first (scene
> model → builder → ASCII end-to-end → Three.js), so an early increment
> is already terminal-viewable before the JavaScript work begins.

## ADR cross-reference

- **Primary (owned) ADR:**
  [`crysview-structure-visualization.md`](../adrs/suggestions/crysview-structure-visualization.md)
  (Status: Proposed; ADR review cycle closed at the review-5 sentinel).
  This plan **owns** the ADR — it was drafted via `/draft-adr` and is
  not yet committed. `/draft-impl-1` Phase A only commits the ADR
  suggestion and the plan and removes their design-phase `_review-*.md`
  / `_reply-*.md` siblings — it does **not** edit
  [`docs/dev/adrs/index.md`](../adrs/index.md). The **User-facing API**
  index row is a normal Phase 1 step (P1.16).
- **Referenced accepted ADRs** (the design builds on these; none are
  amended):
  - [`display-ux.md`](../adrs/accepted/display-ux.md) — defines
    `project.display` and the `pattern()` / `show_pattern_options()`
    surface this plan parallels with `structure()` /
    `show_structure_options()`.
  - [`switchable-category-owned-selectors.md`](../adrs/accepted/switchable-category-owned-selectors.md)
    and
    [`switchable-category-api.md`](../adrs/accepted/switchable-category-api.md)
    — the contract the new switchable `view` category follows
    (`project.view` read-only attribute; `project.view.type` writable
    selector; `project.view.show_supported()`; private `_swap_view`
    hook, Family B engine rebind).
  - [`selector-families.md`](../adrs/accepted/selector-families.md) —
    `view` is a switchable-category selector (Family B), like `chart` /
    `table`.
  - [`enum-backed-closed-values.md`](../adrs/accepted/enum-backed-closed-values.md)
    — every closed value set (`view.type`, `style.atom_shape`,
    `style.radius_model`, `style.color_scheme`) is a `(str, Enum)`.
  - [`factory-contracts.md`](../adrs/accepted/factory-contracts.md),
    [`factory-tag-naming.md`](../adrs/accepted/factory-tag-naming.md) —
    `@Factory.register` and tag-naming conventions for the new
    renderer/category factories.
  - [`category-owner-sections.md`](../adrs/accepted/category-owner-sections.md),
    [`project-facade-and-persistence.md`](../adrs/accepted/project-facade-and-persistence.md)
    — how owner-level categories persist to `project.cif`.
- No **new** ADR is required. The owned suggestion ADR is the
  authoritative reference.

## Branch and PR

- **Recommended branch:** `crysview-structure-visualization` (flat slug,
  off `develop`, per AGENTS.md §Planning). **Do not create or switch
  branches** while running the shortcut — stay on the current branch;
  the branch note is for when the work is eventually pushed.
- **PR target:** `develop`.
- Do not push the branch until both Phase 1 and Phase 2 review cycles
  close.

## Decisions already made

Settled by the accepted ADR (not re-litigated here), plus three
plan-level structural choices confirmed with the author at plan start.

### From the ADR

- **Renderer-neutral scene + thin renderers** (§1, §2): all
  crystallographic computation (symmetry expansion,
  fractional→Cartesian, ADP eigendecomposition, radius/colour lookup,
  bond detection, occupancy splitting) happens in a scene **builder**,
  upstream of any renderer. Renderers consume a flat set of typed
  Cartesian primitives carrying no rendering-library types.
- **Two shipping engines** (§2): `ascii` (terminal/headless) and
  `threejs` (notebook + standalone HTML), shipping together exactly as
  the `asciichartpy` and `plotly` chart engines do. Qt Quick 3D is
  deferred.
- **Switchable `view` selector** (§2): `project.view.type` (`'threejs'`
  default-capable / `'ascii'`), CIF `_view.type`, following the
  category-owned selector contract with a private `_swap_view` Family B
  rebind. No `view_type` setter, no `show_supported_view_types()`.
- **`structure()` entry point** (§3):
  `project.display.structure(struct_name=...)` parallel to
  `pattern(expt_name=...)`, with `include=` reusing the pattern
  vocabulary (`auto`, `atoms`, `bonds`, `cell`, `axes`, `moments`,
  `labels`); a companion `show_structure_options(struct_name=...)`
  mirrors `show_pattern_options()`. Notebook embeds an interactive view
  (IPython HTML repr); a standalone HTML file can be written to a path.
- **Per-axis fractional range** (§3): six scalar bounds
  `project.view.range_{a,b,c}_{min,max}` (defaults 0 and 1 = full cell,
  **borders included**), mirroring the six scalar cell parameters;
  non-integer allowed, validated min < max per axis, persisted; a
  per-call `range=` tuple on `structure()` overrides for one call.
- **Scene-atom identity rule** (§3): two generated atoms are the same
  scene atom iff same atom-site row **and** fractional coordinates
  coincide within `1e-4` (fractional units); keep one, drop the rest.
  Border copies at 0 and 1 are distinct positions and both survive.
- **Occupancy grouping** (§3): distinct atom-site rows resolving to the
  same position (within `1e-4`) group into one occupancy-wedge sphere,
  each wedge proportional to occupancy. Sum < 1 → vacancy wedge; sum ≥ 1
  → normalize to sum, no vacancy wedge. The builder invents no
  occupancies.
- **ASCII is the reduced-fidelity sibling** (§3, §7): always renders the
  single default cell, no bonds/labels/ellipsoids/moments; announces
  every 3D-only feature (including a wider `range`) through
  `show_structure_options()` and at draw time, exactly as the ascii
  chart engine announces Plotly-only features.
- **Styling = atom-shape mode + standard models** (§6, visual only):
  `atom_shape` (`ball` | `ortep`, default `ortep`), `radius_model`
  (`vdw` | `covalent` | `ionic` | `atomic`, default `covalent`),
  `color_scheme` (`jmol` | `vesta` | …, default `jmol`),
  `adp_probability` (fraction in open interval (0,1), default `0.5`,
  ortep-only). All enum-backed and CIF-persisted to the project CIF;
  `project.style.show_supported()` lists accepted values. Bond cutoffs
  are **not** here — they are a per-structure property (see below).
- **Bundled element database** (§6): one package asset (not
  CIF-serialized) carrying, per element, the `vdw` / `covalent` /
  `ionic` (representative Shannon) / `atomic` radii and the `jmol` /
  `vesta` colour palettes, each with documented provenance. `covalent`
  is the default model because it needs no charge and is fully
  populated. An element missing an entry for the selected model falls
  back to its covalent radius; `show_structure_options()` reports the
  substitution rather than failing.
- **Bond cutoffs are per-structure, not styling** (§6, §8): bond
  generation uses the standard cif_core `_geom` cutoffs
  (`_geom.min_bond_distance_cutoff`, `_geom.bond_distance_incr`) plus a
  per-type bonding radius (`_atom_type.radius_bond`, covalent by
  default), on the structure and persisted in the structure CIF —
  independent of the display `radius_model`. Version 1 draws bonds on
  the fly; the full computed `_geom_bond` / `_geom_angle` tables are
  deferred.
- **Dark/light theme is auto-detected** (§6): the view reuses the
  project's `is_dark()` detection (mirroring the Plotly engine's
  `plotly_dark`/`plotly_white` switch) to theme the canvas +
  annotations; element colours still come from the chosen scheme. Not
  persisted.
- **Pinned, bundled Three.js** (§5): `three@0.160.0` + `OrbitControls` +
  `CSS2DRenderer` ship as **vendored static assets**, embedded inline
  for the notebook and standalone HTML (autonomous, no network), and
  embedded vs linked in the HTML report under the report's existing
  `html_offline` flag — the same switch that already governs
  Plotly/MathJax.
- **Visibility precedence** (§8): explicit `include=(...)` tuple wins
  outright (ignores persisted `_view.show_*`); `include='auto'` resolves
  each feature from data-availability → persisted flag (only
  `show_labels` off, `show_moments` on-where-data) → built-in default;
  unsupported options are skipped and announced, never errored; live
  modebar toggles are runtime-only and never rewrite persisted state.
- **Moments stay gated** (§3, Deferred Work): the scene model carries a
  moment-arrow primitive, but the builder never emits it because the
  structure model has no moment fields today; `show_moments` is inert
  and `show_structure_options()` reports `moments` unavailable.

### Plan-level structural choices (confirmed at plan start)

- **Single comprehensive plan / one PR** (vs. a foundation-first split):
  ASCII and Three.js land together on one branch. The step order is
  still foundation-first so the ASCII path is end-to-end before any JS
  work.
- **Dedicated cohesive subpackage** (ADR §4): the viewer subsystem lives
  under `src/easydiffraction/display/structure/` with a `renderers/`
  subpackage, keeping the renderer-neutral scene model + renderers
  together as a future extraction unit (`crysview`). The **scene model**
  (`scene.py`) imports nothing from easydiffraction domain code; the
  **builder** (`builder.py`) is the easydiffraction-specific adapter.
  The name `display/structure/` is **fixed by ADR §4** and used verbatim
  by every Phase 1 step and Phase 2 test path below — it is **not** an
  open question. It does not collide with `datablocks/structure/`: the
  two live under different parents (`easydiffraction.display.structure`
  vs `easydiffraction.datablocks.structure.categories`), so there is no
  import ambiguity, and the rename candidate is dropped.
- **Crystallographic math centralized**: the new orthogonalization
  (fractional→Cartesian) and ADP-tensor eigendecomposition helpers are
  added to `src/easydiffraction/crystallography/crystallography.py`
  (where symmetry-operation parsing and ADP-constraint math already
  live), and the existing symmetry-op generator
  (`_get_general_position_ops`) is reused (promoted to a public entry
  point if needed). The display builder stays a thin adapter.

## Open questions — all resolved for autonomous implementation

These were open during drafting and are now **resolved** (clarified with
the author), so `/draft-impl-1` can run Phase 1 with **no
stop-and-ask**. Each item records the final decision; the data sources
below were verified reachable (HTTP 200).

- **Exact CIF tag spelling for `style`, `view`, and `geom`** (ADR Open
  Question 1) — **Resolved (final).** Project CIF: `_style.atom_shape`,
  `_style.radius_model`, `_style.color_scheme`,
  `_style.adp_probability`, and `_view.type`, `_view.show_labels`,
  `_view.show_moments`, plus the per-axis range as six scalar tags
  `_view.range_a_min` / `_view.range_a_max` / `_view.range_b_min` /
  `_view.range_b_max` / `_view.range_c_min` / `_view.range_c_max` (one
  number each, defaults 0 and 1), mirroring the cell parameters. Structure
  CIF (per-structure): the **standard
  cif_core** bond cutoffs `_geom.min_bond_distance_cutoff` (default
  `0.0`) and `_geom.bond_distance_incr` (default `0.4`), plus the
  per-type bonding radius `_atom_type.radius_bond` when present (P1.11).
  `_view.type` follows the Display-UX ADR (`_chart.type` /
  `_table.type`); `_style.*` and `_view.*` are project-internal
  app/settings tags; the bond cutoffs use the standard `_geom.*`
  category `cif_core.dic` defines (`_geom.min_bond_distance_cutoff` dic
  13084, `_geom.bond_distance_incr` dic 13044), while the computed
  `_geom_bond.*` / `_geom_angle.*` loops are a separate, deferred
  concern. No further confirmation needed during implementation.
- **ASCII rendering details** (ADR Open Question 2) — **Resolved (final
  for v1).** A **4-bucket** radius glyph ramp `· • ● ⬤`, and the **8/16
  colour ANSI** mapping the existing ascii chart legend already uses
  (`display/plotters/ascii.py`), reused verbatim. Implementers may
  fine-tune glyph/colour choices against a terminal, but the ramp size
  and the ANSI palette are fixed — no design decision remains.
- **Range boundary completion** (ADR Open Question 3) — **Resolved
  (final for v1).** The scene contains only atoms whose fractional
  coordinates fall inside the range (borders included); bonds are drawn
  **only between atoms already in the scene**, so no partner atoms
  outside the range are generated and no edge-coordination completion is
  attempted in v1. (Boundary completion can be revisited in a later
  version.)
- **Three.js asset acquisition** — **Resolved (URLs verified, HTTP
  200).** Fetch and vendor these exact pinned files in P1.13 (network
  needed for that step only), recording the URLs + version (MIT) in the
  vendored `LICENSES.md`:
  - `https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js`
  - `https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/controls/OrbitControls.js`
  - `https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/renderers/CSS2DRenderer.js`
    These are **static JS assets, not a Python dependency**, so no
    `pyproject.toml` change is required (and none is pre-approved).
- **Plain-category base for `style`.** Resolved: model `Style` on
  `project/categories/verbosity/` (and `info` / `publication` /
  `report`), which are the existing plain (non-switchable) categories
  with the `default.py` + `factory.py` shape — `Verbosity(CategoryItem)`
  registers via `@VerbosityFactory.register`, derives from
  `CategoryItem` only (no `SwitchableCategoryBase`), and uses
  enum-backed `StringDescriptor`s with a `MembershipValidator` and a
  getter/setter property per setting. `project/categories/rendering/`
  has no `default.py` / `factory.py`, so it is **not** a usable template
  and is dropped as a model.
- **Element data provenance** — **Resolved.** Covalent + vdW radii and
  Jmol colours from EasyDiffractionBeta `Tables.py` (BSD-3-Clause).
  Ionic (Shannon) from pymatgen `Shannon_Radii.csv`, atomic from
  pymatgen `radii.csv`, VESTA colours from pymatgen
  `ElementColorSchemes.yaml` (all MIT, verified reachable). Shannon
  representative selection and full URLs are pinned in P1.4. Each
  value's source is recorded in `LICENSES.md`.

## Concrete files likely to change

**New viewer subsystem (`display/structure/`):**

- `src/easydiffraction/display/structure/__init__.py` (new — package
  docstring; no `__all__`, explicit imports per AGENTS.md).
- `src/easydiffraction/display/structure/enums.py` (new —
  `ViewerEngineEnum`, `AtomShapeEnum`, `RadiusModelEnum`,
  `ColorSchemeEnum`, each `(str, Enum)` with a `default()` classmethod,
  modelled on `src/easydiffraction/display/plotting.py:50`
  `PlotterEngineEnum`).
- `src/easydiffraction/display/structure/scene.py` (new — frozen
  dataclasses for the renderer-neutral primitives + `StructureScene`
  container; **no easydiffraction-domain imports**).
- `src/easydiffraction/display/structure/builder.py` (new —
  `build_scene(...)`, the easydiffraction adapter reading structure
  categories and calling the crystallography helpers).
- `src/easydiffraction/display/structure/assets/elements.py` (new — the
  extended per-element database: `vdw`/`covalent`/`ionic`/`atomic`
  radii + `jmol`/`vesta` palettes, seeded from EasyDiffractionBeta
  `Tables.py`).
- `src/easydiffraction/display/structure/assets/radii.py` (new —
  `radius_for(element, model)` lookup over the database, covalent
  fallback).
- `src/easydiffraction/display/structure/assets/colors.py` (new —
  `color_for(element, scheme)` + a/b/c axis colours + theme-dependent
  canvas/annotation colours).
- `src/easydiffraction/display/structure/assets/LICENSES.md` (new —
  per-source provenance/licence for the vendored element data).
- `src/easydiffraction/display/structure/viewing.py` (new —
  `Viewer(RendererBase)` facade + `ViewerFactory(RendererFactoryBase)`,
  modelled on `src/easydiffraction/display/plotting.py` `PlotterFactory`
  and `src/easydiffraction/display/tables.py` `TableRendererFactory`).
- `src/easydiffraction/display/structure/renderers/__init__.py` (new).
- `src/easydiffraction/display/structure/renderers/base.py` (new —
  `StructureRendererBase(ABC)`).
- `src/easydiffraction/display/structure/renderers/ascii.py` (new —
  `AsciiStructureRenderer`, `@ViewerFactory.register`).
- `src/easydiffraction/display/structure/renderers/threejs.py` (new —
  `ThreeJsStructureRenderer`, `@ViewerFactory.register`).
- `src/easydiffraction/display/structure/renderers/vendor/threejs/` (new
  — vendored `three.module.js`, `OrbitControls.js`, `CSS2DRenderer.js` +
  `LICENSES.md`).
- `src/easydiffraction/display/structure/templates/structure.html.j2`
  (new — the Three.js HTML/JS shell; mirrors
  `report/templates/html/report.html.j2`'s offline/online asset switch).

**Core validation (exclusive-bound support for `adp_probability`):**

- `src/easydiffraction/core/validation.py` (existing — extend
  `RangeValidator` (`core/validation.py:169`) with optional exclusive
  `gt` / `lt` bounds so a value can be validated in the **open**
  interval `(0, 1)`; the current `ge` / `le` inclusive bounds stay
  unchanged and default to ±∞, so every existing caller is unaffected).
  Needed because the only numeric validator today is inclusive-only and
  cannot reject `0.0` / `1.0` for `adp_probability` (ADR §6).

**New project categories:**

- `src/easydiffraction/project/categories/view/__init__.py`,
  `default.py`, `factory.py` (new —
  `View(CategoryItem, SwitchableCategoryBase)`,
  `ViewFactory(FactoryBase)`, modelled on
  `src/easydiffraction/project/categories/chart/`).
- `src/easydiffraction/project/categories/style/__init__.py`,
  `default.py`, `factory.py` (new — `Style` plain category +
  `StyleFactory`, modelled on the existing plain category under
  `src/easydiffraction/project/categories/verbosity/`).

**New per-structure datablock category (bond cutoffs):**

- `src/easydiffraction/datablocks/structure/categories/geom/__init__.py`,
  `default.py`, `factory.py` (new — `Geom` single-record `CategoryItem`
  with `min_bond_distance_cutoff` / `bond_distance_incr`, modelled on
  the structure `cell` / `space_group` categories; standard CIF
  `_geom.*` in the structure datablock).
- `src/easydiffraction/datablocks/structure/item/base.py` (existing —
  add the `geom` category to `Structure`, mirroring how `cell` /
  `atom_sites` are owned).

**Crystallography helpers:**

- `src/easydiffraction/crystallography/crystallography.py` (existing —
  add public `orthogonalization_matrix(a,b,c,alpha,beta,gamma)`,
  `fractional_to_cartesian(...)`, `adp_principal_axes(tensor)`
  (eigendecomposition → semi-axis lengths + orientation); reuse /
  promote `_get_general_position_ops` for symmetry expansion).
- `src/easydiffraction/crystallography/__init__.py` (existing — export
  any newly public helpers per the explicit-`__init__` rule).

**Project wiring + persistence:**

- `src/easydiffraction/project/project.py` (existing — add `view` /
  `style` read-only properties and the private `_swap_view` hook,
  mirroring `_swap_chart` at `project.py:238`).
- `src/easydiffraction/project/project_config.py` (existing — import +
  instantiate `ViewFactory` / `StyleFactory` defaults, mirroring the
  chart/table wiring at `project_config.py:36`).
- The CIF read-side hook that restores chart/table (in
  `project_config.py` / the project-config CIF deserializer) — extend to
  restore `_view.*` / `_style.*` (mirrors the chart `from_cif` at
  `project/categories/chart/default.py:94`).

**Display facade:**

- `src/easydiffraction/project/display.py` (existing — add
  `structure(struct_name=..., include='auto', range=None, path=None)`
  and `show_structure_options(struct_name=...)` to the class that backs
  `project.display` and already owns `pattern()` /
  `show_pattern_options()`; add the structure `include`-option
  descriptions alongside `_PATTERN_OPTION_DESCRIPTIONS`).

**HTML report integration:**

- `src/easydiffraction/report/html_renderer.py` (existing — embed the
  structure figure honoring `html_offline`, mirroring the Plotly/MathJax
  offline path at `html_renderer.py:170` and the MathJax copy at
  `_copy_mathjax`).
- `src/easydiffraction/report/templates/html/report.html.j2` (existing —
  optional structure-figure block under the same `html_offline` switch).

**Packaging + lint/coverage excludes (vendored assets):**

- `pyproject.toml` (existing — add the new vendored Three.js path to the
  `[tool.ruff]`, `[tool.coverage.run]`, `[tool.interrogate]`, pydoclint,
  and format-docstring `exclude` lists, mirroring the existing
  `report/templates/html/vendor` entries; confirm hatchling's wheel
  packaging ships the new `display/structure/renderers/vendor/` and
  `display/structure/templates/` subtrees, adding a `force-include` rule
  only if the defaults miss them).
- `THIRD_PARTY_LICENSES.md` (existing at repo root — add the Three.js
  entry and the element-data provenance entry).

**ADR index + ADR promotion (handled by `/draft-impl-1` Phase A /
P1.16):**

- `docs/dev/adrs/index.md` (existing — add a **User-facing API** row for
  the crysview ADR).
- `docs/dev/adrs/suggestions/crysview-structure-visualization.md`
  (committed by `/draft-impl-1` Phase A; its `_review-*` / `_reply-*`
  siblings removed there).

**Tutorials and docs:**

- `docs/docs/tutorials/*.py` (existing — add a structure-view example to
  a representative tutorial; regenerate notebooks via
  `pixi run notebook-prepare`).
- `docs/docs/tutorials/*.ipynb` (regenerated artefacts).
- `docs/docs/user-guide/` and `docs/docs/api-reference/` (existing — add
  `project.display.structure()`, `project.view`, `project.style`
  reference + a short user-guide section).

## Commit discipline

When an AI agent follows this plan, **every completed Phase 1
implementation step must be staged with explicit paths and committed
locally before moving to the next implementation step or the Phase 1
review gate.** Follow the rules in [`AGENTS.md`](../../../AGENTS.md) →
**Commits**. Keep commits atomic, single-purpose, and aligned with the
plan steps. Stage only the files a step enumerates; do not include
generated artifacts (project directories, data CIFs, benchmark CSVs,
built wheels) unless a step explicitly produces them — see **Workflow**
in [`AGENTS.md`](../../../AGENTS.md) for the generated-artifact
exceptions.

## Implementation steps (Phase 1)

Ordered foundation-first: the scene model, builder, and ASCII engine
reach end-to-end (P1.1–P1.12) before any Three.js work (P1.13–P1.15).

- [x] **P1.1 — Add viewer + styling enums**
  - Files: new `src/easydiffraction/display/structure/__init__.py`,
    `src/easydiffraction/display/structure/enums.py`.
  - Define four `(str, Enum)` classes per the Enum-Backed Closed Values
    ADR, each with a `default()` classmethod (model on
    `PlotterEngineEnum` at `display/plotting.py:50`):
    - `ViewerEngineEnum`: `ASCII = 'ascii'`, `THREEJS = 'threejs'`
      (default `THREEJS` — the rich engine, matching `chart`'s
      default-to-rich-engine precedent and the ADR §8 persisted example
      `_view.type threejs`). `project.view.type` therefore defaults to
      `threejs`; see P1.9 and the headless note there.
    - `AtomShapeEnum`: `BALL = 'ball'`, `ORTEP = 'ortep'` (default
      `ORTEP`).
    - `RadiusModelEnum`: `VDW = 'vdw'`, `COVALENT = 'covalent'`,
      `IONIC = 'ionic'`, `ATOMIC = 'atomic'` (default `COVALENT` — the
      charge-free model with complete per-element data).
    - `ColorSchemeEnum`: `JMOL = 'jmol'`, `VESTA = 'vesta'` (default
      `JMOL`).
  - `__init__.py`: package docstring only; explicit imports added as
    later steps land modules (no `__all__`).
  - Commit: `Add crysview viewer and styling enums`.

- [x] **P1.2 — Add the renderer-neutral scene model**
  - Files: new `src/easydiffraction/display/structure/scene.py`.
  - `@dataclass(frozen=True, slots=True)` primitives in Cartesian space,
    carrying only stdlib / numpy / RGB-tuple types — **no
    easydiffraction-domain imports** (extraction constraint, ADR §4):
    - `AtomSphere` (centre, radius, colour, label).
    - `OccupancyWedgeSphere` (centre, radius, ordered
      `(fraction, colour)` wedges incl. an optional vacancy wedge,
      label).
    - `AdpEllipsoid` (centre, semi-axis lengths, orientation
      matrix/quaternion, colour, label).
    - `Bond` (two endpoints, two colours split at midpoint).
    - `MomentArrow` (origin, vector, colour) — **defined but never
      emitted in version 1** (gated, ADR §1 + Deferred Work). It still
      carries a numpy-style docstring like every other primitive (so
      `interrogate` passes) and is exercised by a direct construction
      test in Phase 2 (so it is not a coverage gap despite the builder
      never emitting it).
    - `CellEdges` (the 12 edges, as Cartesian segment endpoints).
    - `AxisTriad` (a/b/c arrow vectors + per-axis colours + letters).
    - `TextLabel` (anchor, text).
    - `StructureScene` — the flat container holding lists of the above
      plus the cell basis used for projection.
  - Numpy-style docstrings ≤72-char summaries on every public class.
  - Commit: `Add renderer-neutral structure scene model`.

- [x] **P1.3 — Add crystallographic geometry helpers**
  - Files: existing
    `src/easydiffraction/crystallography/crystallography.py`,
    `src/easydiffraction/crystallography/__init__.py`.
  - Add public helpers (centralized math decision):
    - `orthogonalization_matrix(a, b, c, alpha, beta, gamma) -> np.ndarray`
      — the 3×3 fractional→Cartesian matrix from cell parameters
      (standard crystallographic convention; document the chosen axis
      setting).
    - `fractional_to_cartesian(frac, matrix) -> np.ndarray`.
    - `adp_principal_axes(tensor) -> tuple[np.ndarray, np.ndarray]` —
      eigendecomposition (`numpy.linalg.eigh`) of a symmetric 3×3 ADP
      tensor returning semi-axis lengths + orientation; document the
      U-vs-B and Cartesian-vs-crystal convention used.
    - A public symmetry-expansion entry point reusing the existing
      `_get_general_position_ops` / `_parse_rotation_matrix`
      (`crystallography.py:399`, `:350`) — either promote
      `_get_general_position_ops` to public or add a thin public wrapper
      that yields `(rotation, translation)` ops for a space group.
  - Export any newly public helpers from `crystallography/__init__.py`.
  - Commit: `Add orthogonalization and ADP eigendecomposition helpers`.

- [x] **P1.4 — Build the extended element database (radii + colours)**
  - Files: new
    `src/easydiffraction/display/structure/assets/__init__.py`,
    `assets/elements.py` (or a vendored data file + loader),
    `assets/radii.py`, `assets/colors.py`, `assets/LICENSES.md`.
  - Build **one extended per-element database** as a package asset (not
    CIF-serialized), complete for the elements EasyDiffraction handles,
    carrying for each element the four radii (`vdw`, `covalent`, `ionic`
    representative Shannon at a documented default oxidation
    state/coordination, `atomic`) and the `jmol`/CPK and `vesta` colour
    palettes, every value tagged with its provenance.
  - **Seed from our own prior data, then extend from verified sources.**
    EasyDiffractionBeta's `easyDiffractionApp/Logic/Tables.py`
    `PERIODIC_TABLE` (BSD-3-Clause, our project) provides the Jmol/CPK
    `color` and the `covalent` and `vdW` radii per element — reuse
    verbatim with provenance. Fetch the remaining values from
    **pymatgen** (MIT; each URL verified reachable, HTTP 200),
    **extracting the data values, not adding a runtime dependency**. Raw
    URLs under
    `https://raw.githubusercontent.com/materialsproject/pymatgen/master/`:
    - **Ionic (Shannon)** radii →
      `dev_scripts/periodic_table_resources/Shannon_Radii.csv` (columns
      `Element, Charge, Coordination, Spin State, Crystal Radius, Ionic Radius`;
      original: R. D. Shannon, Acta Cryst. (1976) A32, 751).
    - **Atomic** radii →
      `dev_scripts/periodic_table_resources/radii.csv` (`Atomic radius`
      column; `Van der waals radius` there is a cross-check of the
      seed).
    - **VESTA** (and Jmol cross-check) colours →
      `src/pymatgen/vis/ElementColorSchemes.yaml` (`Jmol:` / `VESTA:`
      RGB maps; VESTA original: Momma & Izumi, J. Appl. Cryst. 2011).
      Cite each pymatgen file URL **and** the primary scientific
      reference in `LICENSES.md`. **Network access is needed for this
      step** to fetch these.
  - **Shannon representative-radius policy (deterministic,
    reproducible).** The atom-site model carries only an element symbol,
    so pick exactly one Shannon row per element by a fixed rule:
    **charge** = walk the element's oxidation states from pymatgen
    `dev_scripts/periodic_table_resources/oxidation_states.yaml` (same
    repo/raw-URL base, verified reachable HTTP 200) in listed order,
    keeping those that have a Shannon entry, then any remaining Shannon
    charges (lowest `|charge|` first) — this keeps anions such as O²⁻ /
    F⁻, not just cations; **coordination** = `VI` (else the lowest
    coordination present); **spin** = high-spin where a spin state is
    listed; take the `Ionic Radius` column, skipping non-physical
    (non-positive) entries such as the H⁺ value. The first charge that
    yields a positive radius wins; if none does, fall back to the
    covalent radius (the `substituted` flag). Record the chosen
    `(charge, coordination)` per element in `LICENSES.md`. Ionic is not
    the default model, so this only applies when the user selects
    `radius_model = 'ionic'`. (Result: 93/118 elements carry a Shannon
    radius; the rest fall back to covalent.)
  - `radii.py`: `radius_for(element, model) -> tuple[float, bool]`
    lookup returning the radius and a `substituted` flag; a miss for the
    selected model (e.g. an element with no ionic entry) falls back to
    **covalent** (the default model, always populated), surfaced by
    `show_structure_options()` per ADR §6.
  - `colors.py`: `color_for(element, scheme) -> RGB` for `jmol` /
    `vesta`, plus the a/b/c axis colours the scene gives every engine,
    plus the theme-dependent canvas/annotation colours the renderers
    read from `is_dark()` (P1.14).
  - `assets/LICENSES.md`: per-source provenance + licence (Tables.py
    seed; Shannon ionic; atomic; VESTA), no hand-guessed values.
  - Commit: `Add extended element database for radii and colours`.

- [x] **P1.5 — Add the scene builder**
  - Files: new `src/easydiffraction/display/structure/builder.py`.
  - `build_scene(structure, *, style, view_range, features) -> StructureScene`,
    the easydiffraction adapter. **`features` is the already-resolved
    concrete set of primitives to emit (e.g.
    `frozenset({'atoms', 'bonds', 'cell', 'axes'})`), never the raw
    `'auto'` request** — the builder only decides which primitive lists
    to populate and **never re-implements ADR §8 precedence** (that is
    the facade's job, P1.12):
    - Read cell (`cell.length_a…angle_gamma`), atom sites (`atom_sites`:
      label, `type_symbol`, `fract_x/y/z`, `occupancy`, `adp_iso`,
      `adp_type`), anisotropic ADP (`atom_site_aniso.adp_11…adp_23`),
      and the space group (`space_group.name_h_m`,
      `it_coordinate_system_code`).
    - **Symmetry expansion** over `view_range` using the P1.3 ops; keep
      every generated copy whose fractional coords fall in the per-axis
      range, **borders included**.
    - **Scene-atom identity dedup**: same atom-site row + coords within
      `1e-4` → keep one (ADR §3).
    - **Occupancy grouping**: distinct rows at the same position (within
      `1e-4`) → one `OccupancyWedgeSphere` with proportional wedges; sum
      < 1 → vacancy wedge; sum ≥ 1 → normalize (ADR §3).
    - **fractional→Cartesian** via P1.3.
    - **Atom shape** (style.atom*shape): `ortep` → `AdpEllipsoid` from
      `adp_principal_axes` scaled to `adp_probability` (anisotropic) or
      a radius-model sphere (isotropic / no ADP); `ball` → radius-model
      sphere always. The display radius model sets sphere \_size* only —
      it does **not** drive bond detection (bonds use the `_geom`
      cutoffs below).
    - **Bonds**: between in-scene atoms whose separation `d` satisfies
      the standard cif_core `_geom` auto-bonding rule (P1.11) —
      `geom.min_bond_distance_cutoff ≤ d ≤ r_bond(A) + r_bond(B) + geom.bond_distance_incr`,
      where `r_bond` is `_atom_type.radius_bond` when the structure
      carries it, else the element's covalent radius from the bundled DB
      (P1.4). Split-coloured at midpoint; only atoms already in the
      scene (no out-of-range partners, see Open Questions). The builder
      reads the cutoffs from `structure.geom`, like cell/atom data —
      they are not styling and are independent of the display
      `radius_model`.
    - **Cell edges + axis triad + labels** always built; **moments never
      emitted** (gated).
  - **Single source of truth for visibility.** The builder receives the
    facade-resolved `features` set and populates exactly those primitive
    lists — it does not see `'auto'`, persisted `show_*` flags, or the
    `include=` request, so ADR §8 precedence lives only in the facade
    (P1.12).
  - **Data-availability probe (same module).** Add
    `structure_feature_availability(structure, *, style) -> FeatureAvailability`
    — a lightweight read of the structure (no full scene build)
    reporting, per feature, whether the data exists (e.g. `moments`
    always absent in version 1; `bonds`/`axes`/`cell` always available;
    `labels` always available) **plus** the ionic→covalent radius
    substitutions the chosen `radius_model` would trigger. The builder
    is the only place that reads the structure, so this probe is the one
    source both the facade's `'auto'` resolution **and**
    `show_structure_options()` (P1.12) call; neither re-reads the
    structure for availability.
  - Commit: `Add structure scene builder`.

- [x] **P1.6 — Add base + ASCII structure renderer**
  - Files: new
    `src/easydiffraction/display/structure/renderers/__init__.py`,
    `renderers/base.py`, `renderers/ascii.py`.
  - `StructureRendererBase(ABC)`: abstract `render(scene, *, features)`
    contract (the content-resolved feature set from the facade, per
    P1.12) and a `supported_features()` capability hook with two
    distinct readers: (a) the **renderer** uses it to filter the passed
    `features` set and announce + skip what it cannot draw (the
    render-time owner, per P1.12); (b) the **facade** queries it **only
    to preview** availability through `show_structure_options()` — the
    facade never intersects or drops features itself.
  - **Registration import point (AGENTS.md §Architecture).**
    `renderers/__init__.py` explicitly imports the concrete renderer
    class — `AsciiStructureRenderer` now, `ThreeJsStructureRenderer` in
    P1.14 — so the package `__init__.py` is the single import point per
    the convention, **not** an import side-effect in `viewing.py`. At
    this step `ViewerFactory` does not exist yet (it lands in P1.7), so
    `AsciiStructureRenderer` carries **no** decorator and importing the
    package registers nothing yet. P1.7 attaches
    `@ViewerFactory.register` once the factory exists, and that is when
    importing the package triggers registration.
  - `AsciiStructureRenderer` (ADR §7), the reduced-fidelity sibling:
    - Project the scene's Cartesian atom centres + cell edges onto a
      plane (longest in-plane axis horizontal, shortest vertical, middle
      axis = viewing direction).
    - Draw the cell as a schematic parallelogram using the asciichartpy
      glyph set (`│ ╭ ╮ ╯ ╰ ─`); add a **row-major gap-free line
      helper** generalizing the existing asciichartpy connector used by
      `display/plotters/ascii.py` (column-major) so near-vertical
      slanted edges rasterize.
    - Atoms as colour-by-element Unicode circles on a radius-bucketed
      glyph ramp; axis arrows tinted with the a/b/c scheme colours
      (nearest terminal colour, reset after); a colour-tinted legend.
    - Always one default cell; **announce** any 3D-only request (bonds,
      labels, ellipsoids, moments, multi-cell/margin `range`) and skip
      it, mirroring the ascii chart engine.
  - Renderer is developed against a hand-built `StructureScene`, so it
    is testable before the facade exists.
  - Commit: `Add ASCII structure renderer`.

- [x] **P1.7 — Add the Viewer facade + factory; register ASCII**
  - Files: new `src/easydiffraction/display/structure/viewing.py`;
    update `display/structure/renderers/ascii.py` with
    `@ViewerFactory.register`; update `display/structure/__init__.py`.
  - `ViewerFactory(RendererFactoryBase)` + `Viewer(RendererBase)`
    modelled on `PlotterFactory` / `Plotter`
    (`display/plotting.py:5980`) and `TableRendererFactory` /
    `TableRenderer` (`display/tables.py:142`): a `_registry()` of
    `{engine: {'description', 'class'}}`, `descriptions()`, and the
    active-engine binding the `_swap_view` hook rebinds. Add the
    `@ViewerFactory.register` decorator to `AsciiStructureRenderer` in
    this step (the factory now exists).
  - **Registration wiring (AGENTS.md §Architecture).**
    `display/structure/__init__.py` explicitly imports the `renderers`
    package (which imports the concrete renderer classes, P1.6) **and**
    `Viewer` / `ViewerFactory` from `viewing.py`, so importing the
    `display.structure` package triggers every
    `@ViewerFactory.register`. `viewing.py` itself does **not** import
    the renderer modules (that would create an import cycle, since the
    renderers import `ViewerFactory` for the decorator) — the package
    `__init__.py` is the single import point, exactly as the
    registration convention requires.
  - Commit: `Add Viewer facade and factory with ASCII engine`.

- [x] **P1.8 — Add the plain `style` category**
  - Files: existing `src/easydiffraction/core/validation.py`; new
    `src/easydiffraction/project/categories/style/__init__.py`,
    `default.py`, `factory.py`.
  - **First, enable open-interval validation.** Extend `RangeValidator`
    (`core/validation.py:169`) with optional exclusive `gt` / `lt`
    bounds alongside the existing inclusive `ge` / `le` (all four
    default to ±∞, so existing callers are unchanged): a value passes
    when `ge <= value <= le` **and** `gt < value < lt`. Update the
    docstring and `Diagnostics.range_mismatch` reporting to name
    whichever bound was violated. This is bundled into P1.8's single
    commit because it is the enabling prerequisite for
    `adp_probability`; the validator change ships with the only caller
    that needs it. (Its dedicated unit test is a Phase 2 item.)
  - `Style` plain category (model on `project/categories/verbosity/`,
    the plain-category-with-factory shape — `Verbosity(CategoryItem)` +
    `@VerbosityFactory.register`, no `SwitchableCategoryBase`,
    enum-backed `StringDescriptor`s with a `MembershipValidator` and a
    getter/setter per setting) with descriptors validated on assignment:
    `atom_shape` (`AtomShapeEnum`), `radius_model` (`RadiusModelEnum`),
    `color_scheme` (`ColorSchemeEnum`), and `adp_probability` (float
    validated in the **open** interval `(0, 1)` via the extended
    `RangeValidator` with `gt=0.0, lt=1.0`). Bond cutoffs are **not**
    here — they are a per-structure property (P1.11). CIF tags
    `_style.*` (see Open Questions). `show_supported()` lists accepted
    values for every styling setting (ADR §6). No factory-swapped
    `type`.
  - Register `Style` in `project/categories/style/__init__.py`.
  - Commit: `Add style category for structure view styling`.

- [x] **P1.9 — Add the switchable `view` category**
  - Files: new
    `src/easydiffraction/project/categories/view/__init__.py`,
    `default.py`, `factory.py`.
  - `View(CategoryItem, SwitchableCategoryBase)` modelled on `Chart`
    (`project/categories/chart/default.py`): `_category_code='view'`,
    `_owner_attr_name='view'`, `_swap_method_name='_swap_view'`; a
    `type` `StringDescriptor` with CIF `_view.type` validated against
    `ViewerEngineEnum` + `ViewerFactory.descriptions()` and **defaulting
    to `ViewerEngineEnum.default()` (`threejs`)**, matching P1.1;
    `from_cif` calling `self._parent._swap_view`. Plus persisted
    view-state descriptors: `show_labels` (`BoolDescriptor`, default off),
    `show_moments` (`BoolDescriptor`, default on-where-data), and the
    per-axis range as **six scalar `NumericDescriptor`s**
    `range_a_min` / `range_a_max` / `range_b_min` / `range_b_max` /
    `range_c_min` / `range_c_max` (CIF `_view.range_a_min` … , defaults 0
    and 1, each axis validated `min < max` in the setter), mirroring the
    six scalar cell parameters; `structure()`'s `range=` tuple arg
    overrides them per call. `show_supported()` lists engines.
  - **Headless implication of the `threejs` default.** With `threejs`
    default, `project.display.structure(...)` returns/writes an HTML
    string and needs **no browser**, so it runs unattended in CI,
    `script-tests`, and notebooks out of the box. The
    terminal/CLI/headless `ascii` engine the ADR §2 names is opt-in via
    `project.view.type = 'ascii'`. The P1.16 tutorial and the Phase 2
    script-test coverage item therefore exercise **both** paths: the
    default `threejs` HTML emission and an explicit
    `view.type = 'ascii'` terminal render (see the Phase 2 "Integration
    / script-test coverage" item).
  - Register `View` in `project/categories/view/__init__.py`.
  - Commit: `Add switchable view category for renderer selection`.

- [x] **P1.10 — Wire `project.view` / `project.style` + CIF
      persistence**
  - Files: existing `src/easydiffraction/project/project.py`,
    `src/easydiffraction/project/project_config.py` (+ the
    project-config CIF deserializer hook).
  - Add read-only `view` / `style` properties on `Project` (mirror
    `chart` / `table` at `project.py:315`) and the private `_swap_view`
    hook (mirror `_swap_chart` at `project.py:238`) that rebinds the
    active `Viewer` engine.
  - Instantiate `ViewFactory` / `StyleFactory` defaults in
    `project_config.py` (mirror `project_config.py:36`) and extend the
    CIF read side to restore `_view.*` / `_style.*` (mirror the chart
    `from_cif`).
  - Round-trip check is deferred to the Phase 2 tests; this step only
    wires the surfaces.
  - Commit: `Wire project.view and project.style with CIF persistence`.

- [x] **P1.11 — Add the per-structure `geom` bond-cutoff category**
  - Files: new
    `src/easydiffraction/datablocks/structure/categories/geom/__init__.py`,
    `default.py`, `factory.py`; existing
    `src/easydiffraction/datablocks/structure/item/base.py` (add the
    category to `Structure`).
  - `Geom` per-structure category — a **single-record `CategoryItem`**
    (model on `cell` / `space_group`, not the `atom_sites` loop) holding
    the standard cif_core bond-generation cutoffs:
    - `min_bond_distance_cutoff` (float Å, default `0.0`) — CIF
      `_geom.min_bond_distance_cutoff`.
    - `bond_distance_incr` (float Å, default `0.4`, documented and
      tunable) — CIF `_geom.bond_distance_incr`. A bond forms between
      two in-scene atoms when
      `min_bond_distance_cutoff ≤ d ≤ r_bond(A) + r_bond(B) + bond_distance_incr`,
      where `r_bond` is `_atom_type.radius_bond` when the structure
      carries it, else the element's covalent radius from the bundled DB
      (P1.4); version 1 has no `_atom_type` category, so covalent is
      used. Both tags are the **standard** `cif_core.dic` definitions
      (`_geom.min_bond_distance_cutoff`, `_geom.bond_distance_incr`) and
      always serialize in the **structure datablock**.
  - Add `geom` to `Structure` (the `CategoryOwner` auto-discovers any
    `CategoryItem` attribute) and register the concrete class in
    `datablocks/structure/categories/geom/__init__.py`.
  - This is the per-structure home the builder reads bond cutoffs from
    (P1.5), so multi-phase projects can carry different cutoffs per
    phase; the computed `_geom_bond` / `_geom_angle` loops and the
    angle/contact cutoffs are deferred (ADR Deferred Work).
  - Commit: `Add per-structure geom bond-cutoff category`.

- [x] **P1.12 — Add `display.structure()` + `show_structure_options()`**
  - Files: existing `src/easydiffraction/project/display.py`.
  - Add to the class backing `project.display` (owner of `pattern()` /
    `show_pattern_options()`):
    - `structure(struct_name, include='auto', range=None, path=None)`:
      resolve the structure by name; **resolve the concrete `features`
      set here** (see precedence below) by calling P1.5's
      `structure_feature_availability(structure, style=project.style)`;
      build the scene via
      `build_scene(structure, style=project.style, view_range=<resolved range>, features=<resolved set>)`
      (per-call `range` overrides the persisted view range for
      that call); render with the active `project.view` engine.
      **Signature mirrors `pattern()`**: `structure(...) -> None`,
      displaying directly as a side effect (notebook: `IPython.display`
      of the engine's HTML; terminal: print the ASCII view); when `path`
      is given, also write a standalone, self-contained HTML file
      (Three.js embedded). (`pattern()` is `-> None` and displays
      directly — verified in `display.py` — so no open signature
      decision remains.)
    - `show_structure_options(struct_name)`: mirror
      `show_pattern_options()` — list each `include=` option with engine
      - data support and the reason when unavailable, reading the
        **same** `structure_feature_availability(...)` probe (P1.5) plus
        the active engine's `supported_features()` (P1.6), so it never
        re-reads the structure: ascii's 3D-only skips; `moments` until
        moment fields exist; ionic→covalent radius substitutions from
        P1.4.
    - **Content precedence — resolved only here (ADR §8).** The facade
      is the single resolver of **which features the data and flags
      select**; it does **not** filter by what the engine can draw. It
      resolves content in a fixed order:
      1. explicit `include=(...)` tuple → that set wins outright,
         ignoring persisted `show_*`;
      2. `include='auto'` → per feature, data-availability (from the
         probe) → persisted `show_*` flag where one exists → built-in
         default;
      3. live modebar toggles are runtime-only and never rewrite the
         resolved/persisted state.
    - **Supported-feature filtering + announce/skip — the renderer's
      job, not the facade's.** The content-resolved set is passed to
      `build_scene(..., features=...)` and on to the active renderer;
      the **renderer** is the authority on what it can draw, so it draws
      the features `supported_features()` allows and **announces +
      skips** any it cannot (ascii's 3D-only
      bonds/labels/ellipsoids/moments/wider `range`), never erroring
      (P1.6). The facade never drops features and never announces at
      render time — it only queries `supported_features()` to
      **preview** the same information through
      `show_structure_options()`, so an unsupported feature is announced
      exactly once.
    - Add structure `include`-option descriptions next to
      `_PATTERN_OPTION_DESCRIPTIONS`.
  - End-to-end ASCII path works after this step
    (`project.view.type='ascii'`).
  - Commit:
    `Add structure() and show_structure_options() display surface`.

- [x] **P1.13 — Vendor pinned Three.js assets + lint/coverage excludes**
  - Files: new
    `src/easydiffraction/display/structure/renderers/vendor/threejs/three.module.js`,
    `OrbitControls.js`, `CSS2DRenderer.js`, and a sibling `LICENSES.md`;
    existing `pyproject.toml`, `THIRD_PARTY_LICENSES.md`.
  - Fetch `three@0.160.0` + the two addons from the upstream the
    prototype pins; record exact source URLs + version + licence (MIT)
    in the vendored `LICENSES.md`. **Network access is needed for this
    step only.**
  - Add the vendored path to the `exclude` lists for ruff, coverage,
    interrogate, pydoclint, and format-docstring in `pyproject.toml`
    (mirror the existing `report/templates/html/vendor` entries). Add
    the Three.js row to `THIRD_PARTY_LICENSES.md`.
  - If hatchling's defaults don't ship the new `vendor/` (and the P1.14
    `templates/`) subtree, add a `force-include` rule under
    `[tool.hatch.build.targets.wheel]`. The actual `pixi run dist-build`
    wheel check is a Phase 2 step.
  - Commit: `Vendor pinned Three.js assets`.

- [x] **P1.14 — Add the Three.js structure renderer**
  - Files: new
    `src/easydiffraction/display/structure/renderers/threejs.py`; new
    `src/easydiffraction/display/structure/templates/structure.html.j2`;
    update `display/structure/renderers/__init__.py` to add the explicit
    `ThreeJsStructureRenderer` import (so its `@ViewerFactory.register`
    fires on package import, per the registration convention — not via a
    `viewing.py` side-effect).
  - `ThreeJsStructureRenderer` (`@ViewerFactory.register`):
    - Serialize the `StructureScene` to JSON (primitive arrays).
    - Render the HTML/JS shell from `structure.html.j2`: pinned Three.js
      - `OrbitControls` + `CSS2DRenderer`, the Plotly-style modebar
        (perspective/parallel toggle, view-along a/b/c, home/reset,
        per-feature visibility toggles for
        cell/axes/atoms/bonds/moments/ labels), shrink-wrapped legend,
        hover tooltips, persistent labels, orbit/zoom/pan; **parallel
        projection default**; initial visibility from the resolved
        `include` (P1.12).
    - **Offline-autonomous by default** for notebook + standalone HTML
      (assets embedded inline, no network — what a CDN-blocked context
      needs); expose an `offline`/embed switch so the HTML-report path
      (P1.15) can link vs embed.
    - **Dark/light theme.** Detect the host theme via the project's
      `is_dark()` (`utils/_vendored` — the same call the Plotly plotter
      uses to pick `plotly_dark`/`plotly_white`) and set the scene
      background and the label/axis/edge colours from the
      theme-dependent colours in `assets/colors.py` (P1.4); element
      colours still come from the selected scheme. Auto-detected, not
      persisted.
    - Provide the IPython HTML representation the facade returns and the
      standalone-HTML write path.
  - Commit: `Add Three.js structure renderer`.

- [x] **P1.15 — Embed the structure figure in the HTML report**
  - Files: existing `src/easydiffraction/report/html_renderer.py`,
    `src/easydiffraction/report/templates/html/report.html.j2`.
  - Render a structure figure into the HTML report honoring the report's
    existing `html_offline` flag — embed the Three.js assets when
    offline, link them otherwise — so a structure figure behaves like
    the existing Plotly figures (ADR §5). Reuse the offline-copy pattern
    at `html_renderer.py` `_copy_mathjax` / the `include_plotlyjs`
    switch at `html_renderer.py:170`.
  - Commit: `Embed structure figure in HTML report under html_offline`.

- [ ] **P1.16 — Promote ADR index row, tutorials, and docs**
  - Files: existing [`docs/dev/adrs/index.md`](../adrs/index.md);
    `docs/docs/tutorials/*.py` (+ regenerated `*.ipynb`);
    `docs/docs/user-guide/`, `docs/docs/api-reference/`.
  - Add the **User-facing API** index row for the crysview ADR (the ADR
    file itself is committed/promoted by `/draft-impl-1` Phase A).
  - Add a structure-view example to a representative tutorial
    (`project.view.type`, `project.style.*`,
    `structure.geom.min_bond_distance_cutoff` /
    `structure.geom.bond_distance_incr`,
    `project.display.structure(...)`, `show_structure_options(...)`);
    regenerate notebooks via `pixi run notebook-prepare` and stage the
    `.py` + regenerated `.ipynb` together.
  - Add `project.display.structure()` / `project.view` / `project.style`
    and the per-structure `structure.geom` bond cutoffs to the API
    reference and a short user-guide section.
  - Commit: `Document structure view in tutorials and reference`.

- [ ] **P1.17 — Reach Phase 1 review gate**
  - No-code step. Mark every `[ ]` above as `[x]`; commit the plan-file
    update alone.
  - Commit: `Reach Phase 1 review gate`.

## Test plan (Phase 2)

Per AGENTS.md §Testing, every new module/class ships with tests; unit
tests mirror the source tree (`src/easydiffraction/<pkg>/<mod>.py` →
`tests/unit/easydiffraction/<pkg>/test_<mod>.py`) — verify with
`pixi run test-structure-check`. No network, no sleeping, no real
calculation engines, no test-ordering dependence. Vendored Three.js +
element-data assets are excluded from test-structure mirroring and
coverage (configured in P1.13).

- [ ] **`tests/unit/easydiffraction/display/structure/test_enums.py`**
      (new) — each enum's members, values, and `default()`. P1.1.
- [ ] **`tests/unit/easydiffraction/display/structure/test_scene.py`**
      (new) — primitives are frozen/slotted; `StructureScene` holds the
      primitive lists; the module imports **nothing** from
      `easydiffraction` domain packages (assert via an import-graph
      check). Includes a **direct `MomentArrow` construction test**
      (build it, assert its fields) so the gated, never-emitted
      primitive is covered. P1.2.
- [ ] **`tests/unit/easydiffraction/crystallography/test_crystallography.py`**
      (extend) — `orthogonalization_matrix` for orthorhombic (diagonal)
      and a known monoclinic/triclinic cell (compare to a hand-computed
      matrix and check `|det| = unit-cell volume`);
      `fractional_to_cartesian` round-trips a known site;
      `adp_principal_axes` diagonalizes a known tensor to expected
      semi-axes/orientation and recovers an isotropic tensor as equal
      axes; the public symmetry-expansion wrapper returns the right
      operation count for a known space group. P1.3.
- [ ] **`tests/unit/easydiffraction/display/structure/assets/test_radii.py`**
      and **`test_colors.py`** (new) — a known element resolves to the
      documented radius for each of the four models; a miss for the
      selected model falls back to covalent with the `substituted` flag
      set; the database is complete for the seeded covalent/vdW/Jmol
      values from `Tables.py`; `jmol` and `vesta` palettes return RGB
      for known elements; the a/b/c axis colours and the dark/light
      canvas colours are returned. P1.4.
- [ ] **`tests/unit/easydiffraction/display/structure/test_builder.py`**
      (new) — against small hand-built structures (no real engine):
  - Special-position overlap collapses to one scene atom; a corner site
    with the default `[0,1]³` range appears at all eight corners (border
    inclusion + identity rule). P1.5.
  - Two rows at one position → one occupancy-wedge sphere; sum < 1 adds
    a vacancy wedge; sum ≥ 1 normalizes with no vacancy wedge. P1.5.
  - `ortep` anisotropic atom → `AdpEllipsoid` scaled to
    `adp_probability`; isotropic/no-ADP → sphere; `ball` → sphere
    always. P1.5.
  - Bonds appear only between in-scene atoms satisfying the `_geom`
    auto-bonding rule
    `min_bond_distance_cutoff ≤ d ≤ r_bond(A)+r_bond(B)+ bond_distance_incr`
    (`r_bond` = covalent radius in v1); varying `bond_distance_incr`
    adds/drops bonds; nothing below `min_bond_distance_cutoff`; no
    out-of-range partner atoms are generated. P1.5.
  - Moments are never emitted. P1.5.
  - The builder emits exactly the primitive lists named in the passed
    `features` set and reads neither `'auto'` nor persisted `show_*`
    flags (precedence is the facade's job);
    `structure_feature_availability(...)` reports `moments` unavailable
    and flags ionic→covalent substitutions without building a scene.
    P1.5.
- [ ] **`tests/unit/easydiffraction/display/structure/renderers/test_ascii.py`**
      (new) — orthorhombic cell renders a rectangular parallelogram;
      monoclinic renders the slanted staircase; atoms map to the
      bucketed glyph ramp; a 3D-only `include` (bonds/labels/moments)
      and a wider `range` are announced and skipped; legend lists
      elements. P1.6.
- [ ] **`tests/unit/easydiffraction/display/structure/test_viewing.py`**
      (new) — `ViewerFactory` registers `ascii` (and `threejs` after
      P1.14); `descriptions()` lists them; the facade rebinds the active
      engine. P1.7, P1.14.
- [ ] **`tests/unit/easydiffraction/core/test_validation.py`** (extend)
      — the extended `RangeValidator` with exclusive `gt` / `lt` bounds
      rejects the endpoints (`gt=0.0` rejects `0.0`, `lt=1.0` rejects
      `1.0`) and accepts an interior value; a validator with only `ge` /
      `le` still behaves exactly as before (no regression for existing
      callers). P1.8.
- [ ] **`tests/unit/easydiffraction/project/categories/style/test_style.py`**
      (new — single parent-level test if the package is only
      `default.py`/`factory.py`) — enum assignment validates (bad value
      raises `typeguard.TypeCheckError` / `ValueError`);
      `adp_probability` accepts an interior value (e.g. `0.5`) and
      **rejects both endpoints `0.0` and `1.0`** (open interval, via the
      extended `RangeValidator`); `show_supported()` lists every
      setting's accepted values; `_style.*` CIF round-trips. P1.8.
- [ ] **`tests/unit/easydiffraction/project/categories/view/test_view.py`**
      (new) — `type` validates against `ViewerEngineEnum`; setting
      `type` calls `_swap_view`; a `range_a_max` below `range_a_min` is
      rejected (per-axis `min < max`); `_view.type` / `_view.show_*` /
      `_view.range_a_min` … `_view.range_c_max` CIF round-trip;
      `show_supported()` lists engines. P1.9.
- [ ] **`tests/unit/easydiffraction/project/test_project.py`** (extend)
      — `project.view` / `project.style` are read-only attributes;
      switching `project.view.type` rebinds the active engine; a saved +
      reloaded project restores `_view.*` / `_style.*` identically.
      P1.10.
- [ ] **`tests/unit/easydiffraction/datablocks/structure/categories/geom/test_geom.py`**
      (new — single parent-level test if the package is only
      `default.py`/`factory.py`) — defaults are
      `min_bond_distance_cutoff = 0.0` and `bond_distance_incr = 0.4`;
      both `_geom.min_bond_distance_cutoff` and
      `_geom.bond_distance_incr` round-trip in the **structure**
      datablock; a multi-phase project keeps independent cutoffs per
      structure. P1.11.
- [ ] **`tests/unit/easydiffraction/project/test_display.py`** (extend)
      — `structure()` returns the expected representation per engine;
      per-call `range=` overrides the persisted range for that call
      only; `include='auto'` resolves per ADR §8 (data → persisted →
      default); an explicit tuple ignores persisted `show_*`;
      unsupported options are skipped, never raised;
      `show_structure_options()` reports support + reasons (ascii
      3D-only, moments gated, ionic→covalent substitution). P1.12.
- [ ] **`tests/unit/easydiffraction/display/structure/renderers/test_threejs.py`**
      (new) — the renderer emits an HTML string containing the scene
      JSON and the modebar controls; **offline** mode embeds the
      Three.js asset text inline (no CDN URL), online mode links it; the
      standalone write path produces a self-contained file; the resolved
      dark/light theme drives the canvas/annotation colours (assert the
      dark vs light background differs when `is_dark()` is
      monkeypatched), while element colours stay scheme-driven. Assert
      on emitted markup, not a live browser. P1.14.
- [ ] **`tests/unit/easydiffraction/report/test_html_renderer.py`**
      (extend) — `html_offline=True` embeds the Three.js assets next to
      / inside the report; `html_offline=False` links them; the
      structure figure block appears when a structure is present. P1.15.
- [ ] **Wheel-packaging verification** — `pixi run dist-build` then
      `unzip -l dist/*.whl | grep -E 'three.module.js|OrbitControls|CSS2DRenderer|structure.html.j2'`
      confirms the vendored Three.js + HTML template ship in the wheel.
      `dist/*.whl` is a verification artefact — do not stage it. P1.13.
- [ ] **Integration / script-test coverage** — confirm
      `pixi run script-tests` exercises the tutorial that calls
      `project.display.structure(...)` along **both** engine paths: the
      **default `threejs`** HTML emission (no browser, runs headless in
      CI) and an explicit `project.view.type = 'ascii'` terminal render.
      Extend a tutorial if not. P1.16.

Use `pixi run test-structure-check` to confirm the unit-test layout
mirrors the source tree per AGENTS.md §Testing.

## Verification commands (Phase 2)

Per AGENTS.md §Workflow, save any required check output with the
zsh-safe pattern. Variable names per task (never assign to `status` in
zsh — it is readonly):

```sh
pixi run fix > /tmp/easydiffraction-fix.log 2>&1; fix_exit_code=$?; tail -n 200 /tmp/easydiffraction-fix.log; exit $fix_exit_code
pixi run check > /tmp/easydiffraction-check.log 2>&1; check_exit_code=$?; tail -n 200 /tmp/easydiffraction-check.log; exit $check_exit_code
pixi run test-structure-check > /tmp/easydiffraction-test-structure-check.log 2>&1; test_structure_check_exit_code=$?; tail -n 200 /tmp/easydiffraction-test-structure-check.log; exit $test_structure_check_exit_code
pixi run unit-tests > /tmp/easydiffraction-unit-tests.log 2>&1; unit_tests_exit_code=$?; tail -n 200 /tmp/easydiffraction-unit-tests.log; exit $unit_tests_exit_code
pixi run integration-tests > /tmp/easydiffraction-integration-tests.log 2>&1; integration_tests_exit_code=$?; tail -n 200 /tmp/easydiffraction-integration-tests.log; exit $integration_tests_exit_code
pixi run script-tests > /tmp/easydiffraction-script-tests.log 2>&1; script_tests_exit_code=$?; tail -n 200 /tmp/easydiffraction-script-tests.log; exit $script_tests_exit_code
```

Run in order; each must complete clean before the next. Per AGENTS.md
§Workflow: `pixi run fix` regenerates
`docs/dev/package-structure/full.md` and `short.md` automatically —
never edit those by hand. The vendored Three.js assets, the HTML
template, and the element-data assets are intentional sources (included
in commits); the built wheel under `dist/`, benchmark CSVs under
`docs/dev/benchmarking/`, and any tutorial project output under
`tmp/tutorials/` are verification artefacts — do not stage them. Lint
complexity thresholds are guardrails: if the scene builder or a renderer
trips `max-branches` / `max-statements`, refactor (extract helpers,
parameter objects) rather than raising thresholds or adding `# noqa`.

## Suggested Pull Request

**Title:** `[display] Interactive 3D structure view (crysview)`

**Description:**

Adds an interactive 3D view of the crystal structure a refinement is
adjusting — the atoms, the unit cell, the bonds, and the thermal (ADP)
ellipsoids — alongside the existing 1D pattern view.

- **`project.display.structure('lbco')`.** A new display method,
  parallel to `project.display.pattern(...)`, draws one structure. In a
  Jupyter notebook it renders an interactive Three.js scene (rotate,
  zoom, pan, view down a/b/c, toggle features, switch
  perspective/parallel projection); in a terminal it prints a schematic,
  colour-coded ASCII view.
  `project.display.show_structure_options('lbco')` lists what each
  engine and the current structure can show, with reasons when something
  is unavailable.
- **Choose the engine and the styling, once.** `project.view.type`
  selects `threejs` or `ascii`; `project.style` picks the depiction
  (`ortep` thermal ellipsoids — the default — or `ball`-and-stick), a
  standard radius model (covalent by default, or vdw/ionic/atomic), and
  a colour scheme (Jmol/CPK, VESTA) and ADP probability level — standard
  models drawn from a built-in element database, not dozens of
  per-element rows. The view also follows your notebook's dark or light
  theme automatically. It all persists to `project.cif`, so a reopened
  project looks the same.
- **Tune which bonds are drawn, per structure.** `structure.geom` sets
  the standard bond cut-offs (a minimum distance and a tolerance added
  to the atoms' bonding radii) for each structure, saved in that
  structure's own file, so different phases can use different cut-offs.
- **See a single cell, a margin, or several cells.** `project.view` sets
  a per-axis fractional range (default: the
  full cell with border atoms drawn); widen it for a margin or multiple
  cells.
- **Works offline.** The notebook and standalone-HTML views embed a
  pinned Three.js so they render with no network, and a structure figure
  can be embedded in the HTML report under the existing
  `html_offline = True` switch — just like the Plotly figures.

Full bond/angle geometry tables (`_geom_bond` / `_geom_angle`),
magnetic-moment arrows, the Qt Quick 3D GUI renderer, and extraction of
a standalone `crysview` package are intentionally deferred (see the
ADR's Deferred Work).

**Scope label:** `[display]`.
