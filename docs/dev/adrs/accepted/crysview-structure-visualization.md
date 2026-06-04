# ADR: crysview Structure Visualization

## Status

Accepted.

**Date:** 2026-05-31

**Implementation note:** A later implementation pass split
structure-view configuration into `rendering_structure`,
`structure_view`, and `structure_style`. This ADR reflects that final
surface; no separate `structure-view-settings` ADR exists.

## Context

EasyDiffraction refines crystal structures but offers no interactive 3D
view of them. The accepted [Display UX Facade](display-ux.md) ADR
defines `project.display` for 1D pattern charts and for parameter, fit,
and posterior tables and plots, but nothing spatial: there is no way to
look at the atoms, the unit cell, or the anisotropic displacement
parameters a refinement is adjusting.

A working prototype establishes the target experience and the data it
needs. It lives at
[`crysview-threejs-demo.html`](crysview-structure-visualization/crysview-threejs-demo.html)
and demonstrates, against a non-orthogonal unit cell:

- atoms as spheres with element radius and colour;
- anisotropic ADP ellipsoids (semi-axis lengths plus orientation);
- mixed-occupancy atoms drawn as occupancy wedges (a sphere split by
  site occupancy);
- two-colour bonds split at their midpoint;
- magnetic-moment arrows;
- an a/b/c axis triad drawn longer than the cell edges;
- a Plotly-style modebar: perspective/parallel projection toggle,
  view-along-a/b/c buttons, a home/reset button, and per-feature
  visibility toggles for cell, axes, atoms, bonds, moments, and labels;
- a shrink-wrapped legend, hover tooltips, and persistent atom labels;
- orbit / zoom / pan controls and both perspective and orthographic
  cameras, with parallel projection as the default.

The prototype's input comment already separates the concerns: a
crystallography layer performs symmetry expansion, fractional →
Cartesian conversion, ADP eigendecomposition, and element-radius lookup;
a visualization layer chooses sizes, colours, bonds, and occupancy
splitting; and the renderer only consumes prepared geometry.

Relevant facts about the current codebase:

- The structure model lives under
  `src/easydiffraction/datablocks/structure/categories/`: `cell`,
  `atom_sites` (fractional coordinates, occupancy, isotropic ADP),
  `atom_site_aniso` (anisotropic ADP), and `space_group`.
- The 1D charting subsystem already uses a switchable-engine pattern.
  `project.rendering_plot.type` selects a plotter engine implemented
  under `src/easydiffraction/display/plotters/` (`ascii.py`,
  `plotly.py`), and `project.rendering_table.type` selects a tabler.
  These follow the switchable-category ADRs, with CIF tags
  `_rendering_plot.type` and `_rendering_table.type`.
- `easycrystallography` is **not** a dependency today and is not
  imported anywhere in `src/`. Any layering that places a separate
  visualization package between `easycrystallography` and
  `easydiffraction` is therefore a future direction, not the current
  state.

The audience is scientists, often non-programmers, working mostly in
Jupyter notebooks and the planned GUI. Discoverability, clear names, and
safe defaults take priority over developer ergonomics.

## Decision

This ADR records the accepted first version of the structure viewer.
Points that earlier reviews left open are settled in the sections below;
the historical open questions are retained only to document the final
choices.

### 1. Build a renderer-neutral structure scene

crysview converts a crystal structure into a prepared, renderer-neutral
**structure scene**: a flat collection of typed primitives expressed in
Cartesian space and carrying no rendering-library types. The primitive
set matches the prototype:

- atom spheres (centre, radius, colour);
- occupancy wedges for mixed-occupancy sites;
- ADP ellipsoids (semi-axes scaled to the configured probability, plus
  orientation);
- bonds (two endpoints, split colour);
- magnetic-moment arrows;
- unit-cell edges;
- the a/b/c axis triad;
- text labels.

All crystallographic computation — symmetry expansion over the
configured cell range (section 3), fractional → Cartesian conversion,
ADP eigendecomposition, radii and colours from the selected model and
colour scheme, bond detection, and occupancy splitting — happens while
building the scene, upstream of any renderer. This is the contract the
prototype already assumes.

### 2. Draw the scene with thin, pluggable renderers

Renderers consume the scene and draw it; they hold no crystallographic
logic. Renderer choice mirrors `project.rendering_plot.type`:

- an ASCII renderer for terminal, CLI, and headless contexts;
- a Three.js renderer for notebooks (embedded HTML/JS) and standalone
  HTML;
- a raster renderer that emits a static, z-buffered PNG image for the
  TeX/PDF report — a trimetric projection of the same scene with a
  per-pixel depth buffer, so hidden-surface removal is exact (atoms,
  bonds, cell edges, and axes all occlude correctly). It is **not** a
  user-selectable engine (it is invoked by the report, like `pgfplots`
  is for the fit plot). The z-buffer rasterisation is plain numpy; it
  uses `Pillow` to draw the a/b/c axis labels and the element legend and
  to encode the PNG;
- a Qt Quick 3D renderer for the GUI is planned.

ASCII and Three.js are the initial interactive engines, shipping
together exactly as the `ascii` and `plotly` chart engines do; the
raster renderer serves the TeX/PDF report, and Qt Quick 3D follows for
the GUI.

A switchable engine selector is added on the project owner, parallel to
`project.rendering_plot` / `project.rendering_table`. It is named
`rendering_structure`:

```python
project.rendering_structure.type = 'auto'   # default: 'threejs' in Jupyter, 'ascii' in a terminal
project.rendering_structure.show_supported()
```

with CIF tag `_rendering_structure.type`. The name parallels
`rendering_plot` / `rendering_table`, and follows the category-owned
selector contract: `project.rendering_structure` is a read-only
attribute on the owner; `project.rendering_structure.type` is the
writable selector; `project.rendering_structure.show_supported()` lists
engines. Switching `type` calls the owner's private
`_swap_rendering_structure` hook, which rebinds the active renderer —
the same Family B rebinding the plot engine selector uses — so no public
`rendering_structure_type` setter or
`show_supported_rendering_structure_types()` is added. The default is
`auto`, which resolves at draw time to `threejs` in a Jupyter notebook
and `ascii` in a terminal — exactly as `_rendering_plot.type` /
`_rendering_table.type` resolve their environment defaults.

### 3. Add a `structure()` entry point on the display facade

Add `project.display.structure(struct_name=...)`, parallel to the
existing `project.display.pattern(expt_name=...)`. It renders one
structure with the active `view` engine — interactive 3D in a notebook,
a schematic projection in the terminal. In the Three.js engine, feature
visibility, projection, and view-along presets are interactive through
the modebar with sensible defaults (parallel projection; cell, axes,
atoms, and bonds visible, plus moments where the data exists; labels
off). In a notebook it embeds an interactive view (an IPython HTML
representation); like the HTML report it can also write a standalone
HTML file to a path. The exact return and save signature is left to the
implementation plan.

Content selection uses an `include=` argument:

```python
project.display.structure(struct_name='lbco')
project.display.structure(struct_name='lbco', include='auto')
project.display.structure(
    struct_name='lbco',
    include=('atoms', 'bonds', 'cell', 'axes', 'moments', 'labels'),
)
```

`include='auto'` shows what the structure state supports (cell, axes,
atoms, bonds, and moments where moment data exists; labels off by
default). The option vocabulary is `auto`, `atoms`, `bonds`, `cell`,
`axes`, `moments`, and `labels`. ADP ellipsoids and mixed-occupancy
splits are not separate keywords: they are drawn automatically as part
of `atoms` (anisotropic ADP gives an ellipsoid, isotropic a sphere; a
mixed site is split), so the data decides. The interactive modebar
toggles the same features after the initial view is drawn, so `include`
sets the starting state and the modebar refines it.

A companion `project.display.show_structure_options(struct_name=...)`
lists each `include=` option with whether the active engine and the
current structure state support it, and the reason when they do not —
for example `moments` is unavailable until the structure model carries
moment fields, and the `ascii` engine reports the features only the 3D
engines draw. This gives the structure view per-option discoverability.

The view also has a spatial extent: which symmetry-equivalent atoms the
scene contains. The scene builder takes the unique (asymmetric-unit)
atoms, applies the space-group symmetry, and keeps every generated copy
whose fractional coordinates fall within a per-axis range, **borders
included**. The default range is `[0, 1]` on each of a, b, and c, so a
full unit cell is drawn with the atoms on the 0 and 1 faces, edges, and
corners all present (a corner site therefore appears at all eight
corners). The range is user-settable per axis, validated so each minimum
is below its maximum, and need not be integer — `[0, 2]` along a draws
two cells, `[-0.2, 1.2]` adds a margin. Like the other settings it is
persisted and overridable per call:

```python
# Persisted per-axis bounds — six scalar settings, like the cell
# parameters (defaults 0 and 1 on each axis = the full cell, borders
# included):
project.structure_view.range_a_max = 2                       # two cells along a
project.structure_view.range_c_min, project.structure_view.range_c_max = -0.2, 1.2   # margin on c

# A convenience tuple overrides the persisted range for one call only:
project.display.structure(
    struct_name='lbco',
    range=((0, 2), (0, 1), (0, 1)),
)
```

Symmetry expansion can map several operations onto one point — a site on
a special position, or the shared 0-and-1 faces the default range keeps
— so the scene builder applies a **scene-atom identity rule** as it
collects copies. Two generated atoms are the same scene atom when they
come from the same atom-site row _and_ their fractional coordinates
coincide within a small tolerance (`1e-4` in fractional units); the
builder keeps one and drops the rest. The tolerance is far below any
cell fraction, so a copy at 0 and its border-included copy at 1 are
distinct positions and both survive — special-position overlaps collapse
without discarding the intentional boundary translations. The atom-site
row participates in the key, so two different rows that happen to share
a position are not merged here; that case is occupancy grouping, handled
next.

When two or more atom-site rows resolve to the same position (within
that same tolerance), the scene builder groups them into one
**occupancy-wedge sphere** rather than overdrawing coincident spheres:
each row contributes a wedge whose angular share is proportional to its
occupancy. Coincident position is the only grouping signal the model
offers — atom sites carry an occupancy but no disorder-group or
occupancy-group field — so it is the documented version-1 criterion.
When the grouped occupancies sum below one, the remainder is drawn as a
vacancy wedge so the empty fraction is visible (a lone site with
occupancy below one is the one-row case); when they meet or exceed one,
the shares are normalized to their sum and no vacancy wedge is drawn.
The builder invents no occupancies — it shows exactly what the rows
carry.

Because expansion happens in the scene builder (section 1), the 3D
engines draw this expanded set in full. The `ascii` engine is the
reduced-fidelity sibling (section 7): it always renders the single
default cell and reports a wider view range as a 3D-only capability
through `show_structure_options()`, the same way it announces the other
features only the 3D engines draw.

### 4. Start internal, design for later extraction

Implement crysview first as an internal subpackage that mirrors
`display/plotters/` (for example
`src/easydiffraction/display/structure/` with renderers under a
`renderers/` subpackage). Keep the scene model free of
easydiffraction-domain imports so it can later be extracted into a
standalone `crysview` package and, eventually, consume
`easycrystallography`. Do **not** add `easycrystallography` as a
dependency now.

### 5. Pin and deliver Three.js deliberately

The prototype loads a pinned Three.js (`three@0.160.0`) plus
`OrbitControls` and `CSS2DRenderer` through a CDN importmap. Production
ships the pinned Three.js bundled with the package so the notebook and
standalone-HTML views are autonomous — they render with no network,
which is what a CDN-blocked or sandboxed context (where the demo renders
blank) needs. This mirrors how the existing report path already embeds
its JavaScript when asked: `report/html_renderer.py` exposes an
`offline` flag that sets `include_plotlyjs=True` (embed) versus `'cdn'`,
gated in the template by `html_offline`.

The HTML report's structure view follows the same rule: it honours the
report's `html_offline` flag, embedding the Three.js assets when offline
and otherwise linking them, so a structure figure behaves like the
existing Plotly figures in a report.

### 6. Source styling from standard models and colour schemes

Atom radii and colours are not typed in per element. They follow from
**standard, user-selected models** that every structure viewer
recognises, looked up automatically from each atom's element (and its
charge where the model needs it):

- a **radius model** turns an element into a sphere radius — van der
  Waals, ionic (Shannon; the site charge where a model carries one,
  otherwise a documented per-element default, see below), or covalent;
- a **colour scheme** is a named element-colour palette — the Jmol/CPK
  scheme, the VESTA scheme, and similar well-known sets.

A scientist picks one model and one scheme instead of editing dozens of
per-element rows, which keeps the view consistent and reproducible:

```python
project.structure_style.atom_view = 'covalent' # vdw | covalent | ionic | adp
project.structure_style.color_scheme = 'jmol'  # jmol | vesta
project.structure_style.atom_view.show_supported()
project.structure_style.color_scheme.show_supported()
```

How an atom is sized and shaped is a single **display-style switch**,
`atom_view`, because the standard radius models and the ADP probability
surface are alternative depictions and a view shows one of them at a
time:

- `'vdw'`, `'covalent'`, `'ionic'` draw every atom as a **radius-model
  sphere** for the named standard radius table; displacement parameters
  do not affect size. This is the familiar ball-and-stick depiction and
  works for any structure, with or without ADP.
- `'adp'` draws each atom as its **ADP probability surface** — a sphere
  for an atom with only isotropic ADP, an ellipsoid (semi-axes and
  orientation from the ADP tensor) for an anisotropic one. Atoms that
  carry no ADP fall back to a covalent-radius sphere. This is the
  thermal-ellipsoid (ORTEP) depiction crystallographers use to inspect
  the displacement parameters a refinement adjusts.

The default is `'covalent'`, because it gives every structure a stable
charge-free ball view. Users can switch to `'adp'` when they want to
inspect displacement surfaces.

> **Amendment — `atom_view` merge.** An earlier design split this into
> two settings: `atom_shape` (`ball`/`ortep`) and `radius_model`
> (`vdw`/`covalent`/`ionic`/`atomic`). They were merged into the single
> `atom_view` selector because `radius_model` was meaningful only in
> ball mode, so the two-field form carried four degenerate
> `ortep`×radius-model combinations. The flat list removes the dead
> states and matches how VESTA/Mercury present the choice. The
> `atomic`/empirical option was then dropped, leaving
> `{vdw, covalent, ionic, adp}`: its radii are within a few percent of
> `covalent` for most elements (and identical for some), so after
> ball-size compression it was visually indistinguishable and added a
> redundant choice. The atomic radii remain in the element database,
> unused by the public selector. The `adp` view still uses covalent
> radii for the ball fallback and for mixed-occupancy sites. CIF field:
> `_structure_style.atom_view`.

In `'adp'` the surfaces are drawn at one **probability level**,
`adp_probability`, a fraction in the open interval (0, 1) — not a
percentage — validated on assignment. It defaults to `0.5` (the ORTEP
and journal 50% convention) and is freely changeable (for example
`0.95`). It has no effect in the radius-model views.

Which bonds the view draws is **not** a styling choice — it is a
geometric property of the structure, and it follows the **standard
cif_core `_geom` auto-bonding model**, not the display `atom_view`. A
bond is drawn between two sites when their distance `d` satisfies
`_geom.min_bond_distance_cutoff ≤ d ≤ r_bond(i) + r_bond(j) + _geom.bond_distance_incr`,
where the per-type bonding radius `r_bond` is `_atom_type.radius_bond`
when the structure carries it, otherwise the element's covalent radius
from the bundled database. Matches are then pruned to the first
coordination shell — a contact is kept only when it is within `1.3×` the
nearer atom's nearest-neighbour distance — so the large covalent radii
of ionic A-site cations do not bond to every surrounding anion (a
heuristic stop-gap; see open issue #108 for the full near-neighbour
approach). These two cutoffs live on the **structure** and persist in
the structure's own CIF (see section 8), not in
`project.structure_style`. The `atom_view` radius models (vdw / covalent
/ ionic) change only the rendered sphere _size_ — they never decide
which bonds appear; bond detection is governed solely by the `_geom`
cutoffs and the per-type bonding radius. Version 1 draws bonds computed
on the fly from this rule while the scene is built and persists no bond
table. The full computed bond and angle geometry — the standard
`_geom_bond` and `_geom_angle` loops, with distances, angles, symmetry
codes, and standard uncertainties — is a separate, related feature that
reuses the same symmetry-expansion and distance math (see Deferred
Work).

`atom_view` and `color_scheme` are finite, closed value sets, so each is
a `(str, Enum)` validated on assignment per the
[Enum-Backed Closed Value Sets](enum-backed-closed-values.md) ADR, and
each selector lists its accepted values through descriptor-level
`show_supported()` — for example
`project.structure_style.atom_view.show_supported()`. `structure_style`
is a plain category, not a switchable one: it has no factory-swapped
`type`, only these validated value settings.

The defaults are the **`covalent`** atom view and the **Jmol/CPK**
colour scheme, so the view looks right with no configuration. Covalent
radii are preferred because they are backed by complete, well-documented
per-element data and need no oxidation state: today's atom-site model
carries only an element symbol — no charge, oxidation-state, or
coordination field — so a model that depends on charge cannot be
resolved per site yet.

The radii and colours come from a **bundled element database** — a
package asset, like the colour palettes, not a per-project value, so it
is not CIF-serialized; the project CIF records only which model and
scheme are selected. The database carries, per element, the van der
Waals, covalent, ionic (a representative Shannon radius at a documented
default oxidation state and coordination), and atomic/empirical radii,
plus the Jmol/CPK and VESTA colour palettes, each value carrying a
documented provenance. The ionic entries let `atom_view = 'ionic'` work
today against the documented default oxidation state; when a future
atom-site charge field exists the ionic model will prefer the site's
charge. An element with no entry for the selected radius model falls
back to its covalent radius, and `show_structure_options()` reports the
substitution instead of failing. Version 1 adds no per-element overrides
on top of the chosen model and scheme.

All of this is CIF-persisted, so a reopened project renders identically.
The decision is that styling is **an atom-shape mode plus model, scheme,
and probability-level selection**, not a per-element table; the exact
CIF tag names and serialization shape are pinned in the implementation
plan (Open Questions, resolved).

The view also adapts to the host's **colour theme**. Like the Plotly
chart engine — which selects the `plotly_dark` or `plotly_white`
template from the detected theme — the structure view reuses the
project's existing dark/light detection (`is_dark()` in
`utils/_vendored`) and switches the scene background and the label,
axis, and edge colours to match, so a notebook in dark mode gets a dark
canvas. Element colours still come from the selected colour scheme
regardless of theme; only the surrounding canvas and annotations follow
it. The theme is auto-detected, not a persisted styling value.

### 7. Terminal view (ASCII engine)

The `ascii` engine renders in the terminal, mirroring the existing
`ascii` chart plotter: it builds a character grid and prints it, with no
GUI or JavaScript. Like that chart engine — which openly announces the
features only Plotly can draw — it is a deliberately reduced-fidelity
sibling of the 3D engines: one schematic projection, one unit cell, and
no bonds, labels, ADP ellipsoids, or moment arrows. When an `include=`
request asks for one of those features, the engine announces it is
available with the 3D engines and skips it, just as the ascii chart
engine does for Plotly-only features. A view range wider than the
default single cell is treated the same way: the terminal view always
draws one cell and announces that multi-cell and margin ranges are
honored only by the 3D engines, so its schematic stays uncluttered and
the single parallelogram never disagrees with the atoms it frames.

Like the other engines it consumes the same renderer-neutral scene
(section 1): it projects the scene's Cartesian atom centres and
unit-cell edges onto a plane and draws a schematic 2D view. The longest
in-plane cell axis runs horizontally, the shortest vertically, and the
remaining (middle-length) axis is the viewing direction.

The cell is drawn as a schematic parallelogram. Its two side edges are
rasterized with the asciichartpy glyph set (`│ ╭ ╮ ╯ ╰ ─`), and the
staircase slope encodes the in-plane angle: near 90° gives long `│` runs
with few corners (a rectangle at exactly 90°), while a larger deviation
from 90° introduces more `╭╯` steps (mirrored to `╰╮` for the opposite
lean). The view is schematic — lengths and angles are approximate, just
enough to convey the cell — so non-orthogonal cells render the same way
as orthogonal ones, with the slant shown rather than dropped.

Atoms are drawn as coloured Unicode circles: colour by element from the
selected colour scheme (the scene colour from section 6, mapped to the
nearest terminal colour) and size by a small radius-bucketed glyph ramp
(for example `· • ● ⬤`). Each axis arrow points to its letter: the
vertical axis is the letter stacked over an up-arrow above the cell (`c`
then `↑`), and the horizontal axis is a right-arrow pointing to the
letter at the end of the bottom-border line, after a short gap (`→ a`).
Each axis arrow and its letter are tinted with that axis's colour — the
same a/b/c colours the scene gives the 3D engines, mapped to the nearest
terminal colour and reset afterwards, just as the existing ASCII chart
legend colours its entries. A legend maps each glyph to its element
name, and both the legend glyph and its element label are tinted with
that element's colour-scheme colour (mapped to the nearest terminal
colour and reset afterwards), so the atoms in the cell, the legend, and
the axis letters all share the one selected colour scheme. The mocks
below are monochrome; a real terminal shows these colours.

An orthorhombic cell viewed down b, with vertical side edges:

```
   c
   ↑
   ╭─────────────────────────╮
   │        ●            ●   │
   │    ⬤                   │
   │  •              ●       │
   ╰─────────────────────────╯  → a

   Legend:  ● La   ● Ba   ⬤ Co   • O
```

A monoclinic cell viewed down b, with slanted side edges:

```
   c
   ↑
      ╭─────────────────────────╮
     ╭╯       ●            ●   ╭╯
    ╭╯    ⬤                  ╭╯
   ╭╯   •              ●     ╭╯
   ╰─────────────────────────╯  → a

   Legend:  ● La   ● Ba   ⬤ Co   • O
```

A small gap-free line helper provides the edge rasterization: it
generalizes the asciichartpy connector (fill vertical runs with `│`, cap
bends with corner glyphs) so it can be walked row-major for the
near-vertical edges that the column-major chart code cannot express.

### 8. Configuring what is shown and how

The view has three configuration axes — _which engine_ draws it, _what_
is shown, and _how_ it is styled. They are three flat project
categories, all persisted to CIF:

- `project.rendering_structure` selects the renderer engine only.
- `project.structure_view` stores durable content and region settings.
- `project.structure_style` stores durable appearance settings.

```python
# How: renderer engine
project.rendering_structure.type = 'auto'           # default: 'threejs' in Jupyter, 'ascii' in a terminal
project.rendering_structure.show_supported()

# How: standard styling models, not per-element values (visual only)
project.structure_style.atom_view = 'covalent' # vdw | covalent | ionic | adp
project.structure_style.color_scheme = 'jmol'  # jmol | vesta
project.structure_style.adp_probability = 0.5  # ADP probability level (0, 1)
project.structure_style.atom_scale = 0.3       # overall atom scale (0, 1]
project.structure_style.atom_view.show_supported()
project.structure_style.color_scheme.show_supported()

# Which bonds exist: a per-structure geometric property, not styling.
# Standard cif_core _geom auto-bonding (r_bond defaults to covalent radius):
# bond iff  min_cutoff <= d <= r_bond(i) + r_bond(j) + incr.
structure = project.structures['lbco']
structure.geom.min_bond_distance_cutoff = 0.0   # default 0.0 Å
structure.geom.bond_distance_incr       = 0.25   # default 0.25 Å (documented, tunable)

# What (per call): content for one view, overriding the initial defaults
project.display.structure(struct_name='lbco')                    # 'auto'
project.display.structure(
    struct_name='lbco',
    include=('atoms', 'bonds', 'cell', 'axes'),
)

# Initial view state (persisted): what is shown when the view opens. The
# Three.js modebar stays active, so the user can still toggle each
# feature live afterwards. show_moments stays inert until the structure
# model carries moment fields (see Deferred Work).
project.structure_view.show_labels = False
project.structure_view.show_moments = True

# What region (persisted): six per-axis fractional bounds (defaults 0 and
# 1 = full cell, borders included), mirroring the six scalar cell
# parameters.
project.structure_view.range_a_min = 0
project.structure_view.range_a_max = 1   # range_b_min/max and range_c_min/max likewise
```

The persisted equivalent in the project CIF:

```
# In the project CIF (project-level view + style):
_rendering_structure.type           auto

_structure_view.show_labels    false
_structure_view.show_moments   true
_structure_view.range_a_min    0
_structure_view.range_a_max    1
_structure_view.range_b_min    0
_structure_view.range_b_max    1
_structure_view.range_c_min    0
_structure_view.range_c_max    1

_structure_style.atom_view        covalent
_structure_style.color_scheme     jmol
_structure_style.adp_probability  0.5
_structure_style.atom_scale       0.3

# In the structure (sample) CIF, beside _cell / _atom_site (per-structure):
_geom.min_bond_distance_cutoff   0.0
_geom.bond_distance_incr         0.25
```

The `_rendering_structure.type` tag follows `_rendering_plot.type` /
`_rendering_table.type` from the Display UX Facade ADR, including their
`auto` environment-default convention (resolved to `threejs` in Jupyter,
`ascii` in a terminal); `_geom.min_bond_distance_cutoff` and
`_geom.bond_distance_incr` are the **standard cif_core** bond-cutoff
tags (`_atom_type.radius_bond` is the standard per-type bonding radius,
used when present). The `_structure_view.*`, `_structure_style.*`, and
`_rendering_structure.type` tags are project-internal app settings.

Initial visibility resolves in a fixed order, so a reopened project and
a per-call request behave predictably:

1. **An explicit `include=(...)` tuple wins outright.** The view opens
   showing exactly those features; persisted `_structure_view.show_*`
   flags are ignored for that call. So `include=('atoms',)` shows only
   atoms even when `show_labels=True` is persisted.
2. **`include='auto'`** — the default, and what a bare `structure()`
   call uses — resolves each feature in turn from: data availability
   first (a feature with no data is off, such as moments without moment
   fields), then the persisted `_structure_view.show_*` flag where one
   exists, then the built-in default otherwise. Version 1 persists flags
   only for the two features whose default a scientist most often flips
   — `show_labels` (off) and `show_moments` (on where data exists);
   atoms, bonds, cell, and axes follow their built-in 'auto' defaults
   and are set per call through an explicit `include=` tuple. So
   `show_labels=True` with `include='auto'` opens with labels on.
3. **Unsupported options are skipped and announced, never errored.**
   Whether it arrived through an explicit tuple or 'auto', a feature the
   engine cannot draw (any 3D-only feature under `ascii`) or the data
   does not support (moments without fields) is reported by
   `show_structure_options()` and at draw time.
4. **Live modebar changes apply on top of that initial state and are
   runtime-only.** Toggling a feature in the Three.js modebar never
   rewrites the persisted `_structure_view.show_*` flags or the
   `include=` set, so reopening the project restores the resolved
   initial state rather than the last live toggle.

## Consequences

- `project.display` gains a spatial view (`structure()`) that
  complements the 1D `pattern()` view with an `include=` feature
  selector.
- `project.display` also gains `show_structure_options()`, so the
  supported content for a given structure and engine is discoverable
  with reasons.
- Keeping crystallography in the scene builder and out of renderers lets
  several front-ends (Three.js now, Qt Quick 3D later) share one model.
- A switchable `rendering_structure` category
  (`project.rendering_structure.type`, CIF `_rendering_structure.type`)
  selects only the engine, per the switchable-category and
  category-owner ADRs. Plain `structure_view` and `structure_style`
  sibling categories hold content/region and appearance settings.
- The `ascii` and `threejs` engines ship together, mirroring the chart
  engines: `ascii` needs no JavaScript and renders a schematic view in
  the terminal, CLI, and headless contexts, while `threejs` covers
  notebooks and HTML.
- Content selection (`include=`) and a small set of visibility flags
  become persisted _initial-view_ settings, so a project reopens looking
  the same; the interactive engines still let the user toggle features
  live.
- The scene's spatial extent is configurable: a per-axis fractional
  range (default `[0, 1]`, borders included) decides which
  symmetry-equivalent atoms are generated, so a single cell, an added
  margin, or several cells need no new primitives. The 3D engines draw
  the expanded set; the `ascii` engine draws the single default cell and
  reports wider ranges as a 3D-only capability.
- The styling category lets scientists choose a standard atom view
  (`vdw`, `covalent`, `ionic`, or `adp`), a colour scheme, an ADP
  probability level, and an overall atom scale — not hand-edit
  per-element rows — all CIF-persisted, with defaults that work
  unconfigured. The radii and colours come from a bundled element
  database (covalent, vdW, ionic, and atomic radii; Jmol/CPK and VESTA
  palettes) shipped as a package asset.
- Bond generation is a per-structure geometric property, not styling: it
  uses the standard cif_core `_geom` auto-bonding cutoffs
  (`_geom.min_bond_distance_cutoff`, `_geom.bond_distance_incr`) plus a
  per-type bonding radius (`_atom_type.radius_bond`, defaulting to the
  covalent radius), all on the structure and persisted in the structure
  CIF — not in `project.structure_style`, and independent of the display
  `atom_view`. Version 1 draws bonds on the fly and persists no bond
  table; the full computed `_geom_bond` / `_geom_angle` tables are
  deferred to a separate feature.
- The structure view auto-detects the host's dark/light theme (reusing
  the project's existing `is_dark()` detection) and adapts its
  background and annotation colours, mirroring how the Plotly chart
  engine switches templates; element colours still come from the
  selected colour scheme.
- The scene builder must expose occupancy splitting, anisotropic ADP,
  and magnetic moments. Where the current structure model lacks a field
  (magnetic moments are not in `atom_sites`/`atom_site_aniso` today),
  that feature stays gated until the model provides the data.
- A pinned Three.js version becomes a bundled package asset to keep up
  to date, and the HTML report embeds it under `html_offline`.
- Tutorials and public API docs gain a structure-view example.

## Alternatives Considered

- **Reuse the 1D chart engines (Plotly) for 3D.** Rejected: Plotly's 3D
  primitives do not express ADP ellipsoids, occupancy wedges, or
  crystallographic camera/axis controls cleanly.
- **Put rendering directly in easydiffraction with no scene
  abstraction.** Rejected: it couples crystallography to one rendering
  library and blocks the planned GUI renderer.
- **Start as a standalone `crysview` package and adopt
  `easycrystallography` now.** Rejected for the first step as a
  premature dependency and repo split before the design is proven;
  retained as the strategic direction.
- **Server-rendered static images instead of an interactive scene.**
  Rejected: it loses the interactivity (rotate, toggle, view-along)
  scientists expect when inspecting a structure.

## Open Questions

All items below are now **resolved** so the implementation plan can be
executed autonomously; the plan records the verified data sources and
the final names.

- **CIF tag spelling — resolved (see the §8 _Updated_ note for the final
  split).** Project CIF: `_structure_style.atom_view` /
  `_structure_style.color_scheme` / `_structure_style.adp_probability` /
  `_structure_style.atom_scale`; `_structure_view.show_labels` /
  `_structure_view.show_moments` /
  `_structure_view.range_{a,b,c}_{min,max}`; and
  `_rendering_structure.type` (engine only). These are project-internal
  app/settings tags (`_rendering_structure.type` follows the Display-UX
  `_rendering_plot.type` / `_rendering_table.type` precedent); the radii
  and colours are a bundled element-database asset, not CIF-serialized.
- **Per-structure bond-cutoff category — resolved (standard
  `_geom.*`).** A single-record `structure.geom` category holding the
  cif_core cutoffs `_geom.min_bond_distance_cutoff` (default `0.0` Å)
  and `_geom.bond_distance_incr` (default `0.25` Å, documented and
  tunable), in the structure datablock. A bond is drawn when
  `min_bond_distance_cutoff ≤ d ≤ r_bond(i) + r_bond(j) + bond_distance_incr`,
  with `r_bond` = `_atom_type.radius_bond` when present, else the
  covalent radius. These are the **standard** cif_core tags (review-4
  finding 1): `_geom.min_bond_distance_cutoff` (dic 13084),
  `_geom.bond_distance_incr` (dic 13044), `_atom_type.radius_bond` (dic
  25419); the earlier project-internal `_bonds.*` proposal was dropped.
  The computed `_geom_bond.*` / `_geom_angle.*` loops remain reserved
  for the deferred geometry tables.
- **ASCII rendering details — resolved.** A 4-bucket radius glyph ramp
  (`· • ● ⬤`) and the 8/16-colour ANSI mapping the existing ascii chart
  legend already uses.
- **Per-axis range boundary completion — resolved.** Version 1 draws
  only atoms inside the range (borders included) and bonds only between
  in-scene atoms — no out-of-range partner atoms or edge-coordination
  completion. The range is persisted as six scalar tags
  `_structure_view.range_{a,b,c}_{min,max}` (one number each, defaults 0
  and 1), mirroring the six scalar cell parameters; a per-call `range=`
  tuple on `structure()` overrides them for one call.

## Deferred Work

- The computed bond and angle geometry tables — the standard
  `_geom_bond` and `_geom_angle` loops (atom-pair/triplet labels,
  distances, angles, site-symmetry codes, standard uncertainties,
  `publ_flag`) — as a separate, related feature. It reuses crysview's
  symmetry-expansion and distance math and the same per-structure
  `_geom` cutoffs (extended with the angle/contact increments cif_core
  already defines). Version 1 draws bonds on the fly from the `_geom`
  bond cutoffs and persists no geometry table.
- The Qt Quick 3D renderer for the GUI.
- Magnetic-moment fields on the structure model (a separate
  magnetic-structure effort); the scene's moment-arrow primitive stays
  gated until they exist.
- Extraction of a standalone `crysview` package and the
  `easycrystallography` layering.
- Advanced depictions beyond atoms, bonds, and ADP surfaces, such as
  coordination polyhedra. Symmetry expansion and multiple-cell views are
  in scope through the per-axis range (section 3).
