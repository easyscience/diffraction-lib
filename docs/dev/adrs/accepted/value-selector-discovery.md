# ADR: Value-Selector Discovery

## Status

Accepted.

## Date

2026-05-31

## Group

User-facing API.

## Implementation Note

This ADR was implemented through the
[`structure-view-settings`](../../plans/structure-view-settings.md)
plan. That plan also amended
[`crysview-structure-visualization.md`](crysview-structure-visualization.md)
for the structure-view settings split; no separate
`structure-view-settings` ADR exists.

## Context

EasyDiffraction is used by scientists who explore the API in notebooks,
so every "pick one of a fixed set" choice should be discoverable in
place.

Two accepted ADRs set up that expectation but only half-deliver it:

- [`enum-backed-closed-values.md`](enum-backed-closed-values.md)
  requires every finite closed set to be a `(str, Enum)` and names
  "finite choices are discoverable" as a consequence. It also makes enum
  members the source of truth for **descriptions**.
- [`switchable-category-owned-selectors.md`](switchable-category-owned-selectors.md)
  gives the three category-level selector families from
  [`selector-families.md`](selector-families.md) — backend,
  switchable-category, and active-sibling — a uniform public shape:

  ```python
  category.type = 'new-type'
  category.show_supported()
  ```

  All three are _category-level_ selectors: each has an owner
  `_swap_<name>` hook, the category **is** the single selector, and
  `show_supported()` lives on the category.

But many enumerated choices are **not** category-level selectors. They
are plain enumerated _fields_ inside a category — there is no backend or
category to swap, only a value the consumer reads. Examples today:

- `structure_style.atom_view`, `structure_style.color_scheme`
- the `experiment.experiment_type` axes (`sample_form`, `beam_mode`,
  `radiation_probe`, `scattering_type`)
- `verbosity` levels, and similar project-owned closed sets

These value fields have **no discovery surface**. A scientist must read
source or trigger a validation error to learn the options — exactly the
gap the enum-backed ADR promised to close. They are declared ad hoc as
`StringDescriptor(... MembershipValidator(allowed=[m.value for m in E]))`,
duplicating the enum-to-allowed wiring at every site.

Not every `MembershipValidator`-backed field qualifies. Some validate
against **dynamic or external** sets rather than a project-owned closed
enum: `atom_sites.type_symbol` (CrySPY isotope symbols from
`DATABASE['Isotopes']`), `atom_sites.wyckoff_letter` (space-group
dependent), `space_group.name_h_m` (CrySPY H-M symbols), and
`space_group.it_coordinate_system_code` (derived from the current H-M
symbol). These are boundary-facing CIF/science values, not `(str, Enum)`
closed sets with a static `.default()`/`.description()`; they are out of
scope here (see Decision and Deferred Work).

## Decision

Recognize a fourth selector shape — the **value selector** — and give it
a discovery surface symmetric with the three category-level families.

1. **Definition.** A value selector is an enumerated descriptor field
   over a **project-owned, static `(str, Enum)`** closed set (per
   [`enum-backed-closed-values.md`](enum-backed-closed-values.md)) whose
   assignment sets a value (no class swap, no `_swap_<name>` hook). It
   is distinct from the three category-level families in
   [`selector-families.md`](selector-families.md), which swap a category
   instance, rebind a backend, or activate siblings. A field whose
   allowed set is **dynamic, external, or context-dependent** (validated
   against a database or another field rather than a closed enum) is
   **not** a value selector and is out of scope — see Decision 4.

2. **Discovery lives on the descriptor.** A value selector exposes
   `show_supported()` on the descriptor itself, reusing the **same**
   `render_table` presentation and `*`-marks-current convention that
   category-level `show_supported()` uses, with the value column and
   descriptions sourced from the enum (per
   [`enum-backed-closed-values.md`](enum-backed-closed-values.md)):

   ```python
   project.structure_style.color_scheme = 'vesta'      # set (string or member)
   project.structure_style.color_scheme.show_supported()
   # Color Scheme types
   #    Value  Description
   #    jmol   Jmol / CPK colour scheme
   #  * vesta  VESTA colour scheme
   ```

   This sits beside the category-level shape, not replacing it:

   ```python
   project.rendering_structure.type = 'threejs'        # category-level selector
   project.rendering_structure.show_supported()
   ```

3. **One descriptor, one source of truth.** Introduce a core
   `EnumDescriptor` bound to a `(str, Enum)` class. It derives the
   `MembershipValidator` and the default (`Enum.default()`) from the
   enum, stores the enum, and renders `show_supported()` from
   `Enum.description`. It replaces the manual
   `StringDescriptor + MembershipValidator(allowed=[...])` pattern at
   every value-selector site, so the enum is wired once.

4. **Scope.** A non-switchable field adopts `EnumDescriptor` **only when
   its allowed set is a project-owned, static `(str, Enum)`** — e.g.
   `atom_view`, `color_scheme`, the `experiment_type` axes, `verbosity`.
   Each such enum must expose `.default()` and `.description`; add them
   where missing. Explicitly **out of scope**:
   - Category-level `.type` selectors (the three families) — unchanged;
     they keep their category-level `show_supported()`.
   - **Dynamic / external / context-dependent** membership validators —
     `atom_sites.type_symbol`, `atom_sites.wyckoff_letter`,
     `space_group.name_h_m`, `space_group.it_coordinate_system_code`,
     and any field whose allowed values come from a database, another
     field, or runtime context. These keep their existing
     `MembershipValidator` and current validation behavior; they do
     **not** become `EnumDescriptor`s and do **not** gain
     `show_supported()` under this ADR. A separate dynamic-choice
     discovery surface is deferred.

   An implementation audit classifies each `MembershipValidator` field
   as value selector, category-level selector, or dynamic/external
   before any migration.

5. **No category-level `show_supported()` on bundle categories.** A
   category that holds several value selectors (e.g. `structure_style`,
   `experiment.experiment_type`) does **not** gain a category-level
   `show_supported()`. "Supported values of what?" has no single answer
   on a multi-field bundle; discovery is per value selector. (A
   clearly-named grouped overview may be added later for tightly-related
   axis bundles — see Deferred Work.)

6. **Numbers are not selectors.** Bounded numeric fields
   (`adp_probability`, `atom_scale`, `range_*`, …) keep plain numeric
   descriptors. Their limits live in the docstring and the validation
   error; they have nothing to enumerate, so no `show_supported()`.

7. **`help()` integration.** Because descriptors already expose `help()`
   (per [`help-discoverability.md`](help-discoverability.md)),
   `show_supported()` is surfaced automatically when a user calls
   `help()` on the descriptor — `help()` says what the field is,
   `show_supported()` lists its values.

## Consequences

- Every finite choice is discoverable at its own selector, finally
  delivering the enum-backed ADR's "discoverable" promise for value
  fields, with one table format shared across all selector shapes.
- The public surface is uniform: _every_ selector answers
  `show_supported()`. Category-level selectors answer at
  `category.show_supported()`; value selectors at
  `category.field.show_supported()`. The asymmetry is intentional — a
  category-level selector _is_ the category, whereas a value field is
  one of several on its category.
- No deeper category tree: `show_supported()` is a method on the
  descriptor the getter already returns, not a nested sub-category.
- Immutable categories (per
  [`immutable-experiment-type.md`](immutable-experiment-type.md)) still
  expose `show_supported()` as read-only discovery, even where the value
  is creation-time only.
- This is a project-wide migration of the **enum-backed** value
  selectors only (the audit pins the exact set; the dynamic/external
  validators above are excluded and keep their current behavior).
  Affected enums gain `.default()`/`.description` where missing. The
  phased rollout — and the matching narrowing of which
  `atom_sites`/`space_group` fields are touched — is tracked by the
  [`structure-view-settings`](../../plans/structure-view-settings.md)
  implementation plan, which also reorganizes the structure-view
  categories that motivated this ADR.

## Alternatives Considered

- **Promote each value selector to a switchable category.** Rejected:
  the three families in [`selector-families.md`](selector-families.md)
  swap a category instance, a backend, or siblings via a `_swap_<name>`
  hook; a colour scheme or atom-view mode swaps nothing. Forcing that
  machinery would either nest a category under a category
  (`structure_style.color_scheme.type` — a deeper tree, which violates
  the flat-sibling rule) or pollute the top level
  (`project.color_scheme`).
- **Category-level `show_supported()` listing every enumerated field on
  the bundle.** Rejected as the primary surface: ambiguous on a
  multi-field category and redundant with the per-descriptor method.
  Kept open only as an optional, clearly-named grouped overview for
  related axis bundles (Deferred Work).
- **Rely on `help()`, docstrings, and validation errors.** Rejected:
  `help()` describes the field but does not enumerate accepted values
  with the active one marked, and users should not have to trigger an
  error to learn the options.
- **Keep `StringDescriptor + MembershipValidator(allowed=[...])` and
  bolt on `show_supported()` per site.** Rejected: duplicates the
  enum-to-allowed wiring, is easy to forget, and has no single source of
  truth. `EnumDescriptor` binds the enum once and derives validation,
  default, and discovery together.

## Deferred Work

- A separate **dynamic-choice descriptor** giving a discovery surface (a
  `show_supported()`-style listing) to fields whose allowed set is
  dynamic, external, or context-dependent — `atom_sites.type_symbol`,
  `atom_sites.wyckoff_letter`, `space_group.name_h_m`,
  `space_group.it_coordinate_system_code`, and similar. Out of scope
  here; these keep their current `MembershipValidator` until such a
  descriptor exists.
- An optional, clearly-named grouped overview for tightly-related axis
  bundles (notably `experiment.experiment_type`'s four axes shown
  together). Not part of the initial rollout.
- Adopting `EnumDescriptor` at value-selector sites beyond those the
  motivating plan touches, if any remain after the audit.
