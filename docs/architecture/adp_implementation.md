# ADP Implementation Plan

**Date:** 2026-04-12
**Status:** Design approved — awaiting implementation

---

## 1. Goal

Extend ADP (Atomic Displacement Parameter) support from the current
Biso-only implementation to all four CIF-standard types: **Biso**,
**Uiso**, **Bani**, **Uani**. The design uses type-neutral parameter
names (`adp_iso`, `adp_11`…`adp_23`) so that switching ADP type is a
one-line operation on `adp_type` without creating or destroying
parameters.

---

## 2. Design Summary

### 2.1 Two Sibling Collections on Structure

Following CIF conventions (`_atom_site` + `_atom_site_aniso` are
separate loops), the structure owns two sibling collections:

```
Structure
├── cell              (CategoryItem)
├── space_group       (CategoryItem)
├── atom_sites        (CategoryCollection of AtomSite)
└── atom_site_aniso   (CategoryCollection of AtomSiteAniso)
```

Every atom always has an entry in both collections, kept in sync by
`Structure._update_categories()`. This eliminates conditional existence
checks throughout the codebase.

### 2.2 Type-Neutral Parameter Names

Parameters on `AtomSite` and `AtomSiteAniso` use type-neutral names
whose physical meaning is determined by `atom_site.adp_type`:

| Parameter | Location | CIF names (order depends on `adp_type`) |
|-----------|----------|----------------------------------------|
| `adp_type` | `AtomSite` | `_atom_site.adp_type` |
| `adp_iso` | `AtomSite` | `_atom_site.B_iso_or_equiv`, `_atom_site.U_iso_or_equiv` |
| `adp_11` | `AtomSiteAniso` | `_atom_site_aniso.B_11`, `_atom_site_aniso.U_11` |
| `adp_22` | `AtomSiteAniso` | `_atom_site_aniso.B_22`, `_atom_site_aniso.U_22` |
| `adp_33` | `AtomSiteAniso` | `_atom_site_aniso.B_33`, `_atom_site_aniso.U_33` |
| `adp_12` | `AtomSiteAniso` | `_atom_site_aniso.B_12`, `_atom_site_aniso.U_12` |
| `adp_13` | `AtomSiteAniso` | `_atom_site_aniso.B_13`, `_atom_site_aniso.U_13` |
| `adp_23` | `AtomSiteAniso` | `_atom_site_aniso.B_23`, `_atom_site_aniso.U_23` |

### 2.3 Dual CIF Names — Static Read, Reordered Write

Each parameter's `CifHandler` carries both CIF name variants. The
existing infrastructure handles this:

- **Reading (deserialization):** `param_from_cif()` and
  `category_collection_from_cif()` iterate `_cif_handler.names` and
  stop at the first match. A CIF file with `_atom_site.U_iso_or_equiv`
  is read correctly regardless of name order.
- **Writing (serialization):** `param_to_cif()` and
  `category_collection_to_cif()` always use `names[0]`. The `adp_type`
  setter reorders the `names` list so that the correct CIF tag is
  emitted first.

Example — when `adp_type` changes from `'Biso'` to `'Uiso'`:

```python
# adp_type setter reorders CIF names on adp_iso
self._adp_iso._cif_handler._names = [
    '_atom_site.U_iso_or_equiv',
    '_atom_site.B_iso_or_equiv',
]
```

No new core CIF infrastructure is needed.

### 2.4 ADP Type Enum

```python
class AdpTypeEnum(str, Enum):
    BISO = 'Biso'
    UISO = 'Uiso'
    BANI = 'Bani'
    UANI = 'Uani'
```

`adp_type` on `AtomSite` is a `StringDescriptor` validated by
`MembershipValidator(allowed=...)` using all four enum values.

### 2.5 Auto-Conversion on Type Switch

Setting `adp_type` triggers value conversion. The physics:

- **B ↔ U (isotropic):** `B = 8π²U`
- **Iso → Ani:** diagonal `adp_11 = adp_22 = adp_33 = adp_iso`,
  off-diagonal `adp_12 = adp_13 = adp_23 = 0`
- **Ani → Iso:** `adp_iso = (adp_11 + adp_22 + adp_33) / 3`

The `adp_type` setter on `AtomSite` performs the conversion and updates
both the isotropic parameter and the aniso parameters on the sibling
collection.

### 2.6 Collection Sync via `_update_categories()`

`Structure._update_categories()` reconciles the two collections:

| Event | Sync action |
|-------|-------------|
| Atom added to `atom_sites` | Create matching `AtomSiteAniso` entry with defaults (0.0) |
| Atom removed from `atom_sites` | Remove matching `AtomSiteAniso` entry |
| Atom label renamed in `atom_sites` | Rekey the matching `AtomSiteAniso` entry |

The sync is driven by the dirty flag — any parameter or collection
change sets `_need_categories_update = True`, and the next
serialization, plot, or fit call triggers `_update_categories()`.

### 2.7 Inactive Aniso Values

When `adp_type` is `'Biso'` or `'Uiso'`, the aniso parameters exist
with value `0.0` but are not read by calculators. This avoids
introducing `None` into the `float`-based `Parameter` system.

---

## 3. User-Facing API

### 3.1 Parameter Access Pattern

Parameters are accessed via the standard two-level pattern:

```python
# CategoryItem.Parameter
structure.cell.length_a = 3.88

# CategoryCollection[item_id].Parameter
structure.atom_sites['Si'].adp_type = 'Biso'
structure.atom_sites['Si'].adp_iso = 0.47
structure.atom_site_aniso['Si'].adp_11 = 0.05
```

### 3.2 Switching ADP Type

```python
# Switch from Biso to Uiso — auto-converts value
structure.atom_sites['Si'].adp_type = 'Uiso'
# adp_iso now holds U_iso value (B / 8π²)

# Switch to anisotropic — seeds diagonal from iso
structure.atom_sites['Si'].adp_type = 'Uani'
# atom_site_aniso['Si'].adp_11/22/33 seeded from adp_iso
# adp_iso recalculated as mean of diagonal

# Switch back to isotropic — collapses tensor to scalar
structure.atom_sites['Si'].adp_type = 'Biso'
# adp_iso = mean(adp_11, adp_22, adp_33), converted B→U if needed
```

### 3.3 Creating Atoms

```python
# adp_iso replaces the old b_iso keyword
structure.atom_sites.create(
    label='Si',
    type_symbol='Si',
    fract_x=0.0,
    fract_y=0.0,
    fract_z=0.0,
    adp_type='Biso',
    adp_iso=0.47,
)
# atom_site_aniso['Si'] is auto-created by _update_categories()
```

### 3.4 CIF Output

```cif
loop_
_atom_site.label
_atom_site.type_symbol
_atom_site.fract_x
_atom_site.fract_y
_atom_site.fract_z
_atom_site.adp_type
_atom_site.B_iso_or_equiv
_atom_site.occupancy
Si  Si  0.00000000  0.00000000  0.00000000  Biso  0.47000000  1.00000000

loop_
_atom_site_aniso.label
_atom_site_aniso.B_11
_atom_site_aniso.B_22
_atom_site_aniso.B_33
_atom_site_aniso.B_12
_atom_site_aniso.B_13
_atom_site_aniso.B_23
Si  0.00000000  0.00000000  0.00000000  0.00000000  0.00000000  0.00000000
```

When `adp_type = 'Uiso'`, the CIF tag becomes `_atom_site.U_iso_or_equiv`
and the aniso loop uses `_atom_site_aniso.U_*` tags.

---

## 4. Implementation Phases

### Phase 1: Rename `b_iso` → `adp_iso` and Expand `adp_type`

**Files to modify:**

1. **`atom_sites/default.py`** — `AtomSite`:
   - Rename `_b_iso` Parameter to `_adp_iso` with dual CIF names
     `['_atom_site.B_iso_or_equiv', '_atom_site.U_iso_or_equiv']`.
   - Expand `_adp_type` validator to accept all four values from
     `AdpTypeEnum`.
   - Add `adp_type` setter logic: reorder CIF names on `_adp_iso`,
     perform B↔U conversion.
   - Rename property `b_iso` → `adp_iso`.

2. **`atom_sites/enums.py`** (new) — `AdpTypeEnum` with BISO, UISO,
   BANI, UANI members plus `default()` and `description()` methods.

3. **Calculator bridges** — update `cryspy.py` and `crysfml.py` to read
   `atom.adp_iso.value` instead of `atom.b_iso.value`, and pass the
   correct type based on `atom.adp_type.value`.

4. **CIF data files** — update all `.cif` files in `data/` that
   reference `b_iso`.

5. **Tutorials** — update all `*.py` scripts that use `b_iso`.

6. **Tests** — update all unit/functional/integration tests.

### Phase 2: Add `AtomSiteAniso` Sibling Collection

**Files to create:**

1. **`atom_site_aniso/`** package under
   `datablocks/structure/categories/`:
   - `__init__.py` — imports `AtomSiteAniso` and `AtomSiteAnisoCollection`.
   - `default.py` — `AtomSiteAniso` (CategoryItem) with `label`
     (StringDescriptor) and six Parameters (`adp_11`…`adp_23`) each
     with dual CIF names. `AtomSiteAnisoCollection`
     (CategoryCollection).
   - `factory.py` — `AtomSiteAnisoFactory`.
   - `enums.py` — if needed (likely shared with Phase 1 enum).

2. **`structure/item/base.py`** — add `_atom_site_aniso` attribute and
   `atom_site_aniso` read-only property on Structure.

3. **`structure/item/base.py`** — override `_update_categories()` to
   reconcile `atom_sites` and `atom_site_aniso` collections (add
   missing, remove stale, rekey on label change).

**Files to modify:**

4. **`atom_sites/default.py`** — `adp_type` setter also reorders CIF
   names on all six aniso parameters (accessed via parent structure's
   `atom_site_aniso` collection).

5. **Calculator bridges** — when `adp_type` is `'Bani'` or `'Uani'`,
   read from `atom_site_aniso[label]` instead of `adp_iso`.

6. **CIF serialization** — works automatically (Structure's `as_cif`
   emits all CategoryCollections found in `vars(self)`).

### Phase 3: ADP Symmetry Constraints

1. **`crystallography.py`** — add symmetry constraint functions for
   anisotropic ADPs based on space group and Wyckoff position.

2. **`AtomSites._update()`** — call aniso symmetry constraints in
   addition to coordinate constraints.

---

## 5. Breaking Changes

| Change | Scope | Migration |
|--------|-------|-----------|
| `b_iso` → `adp_iso` | All code referencing `atom.b_iso` | Mechanical rename (greppable) |
| `b_iso=0.5` → `adp_iso=0.5` in `create()` | Tutorials, tests, user scripts | Mechanical rename |
| New `atom_site_aniso` on Structure | Structure API surface grows | Additive — no existing code breaks |

The project is in beta, so no deprecation path is needed.

---

## 6. Design Decisions

### Why type-neutral names (`adp_iso`) instead of type-specific (`b_iso`, `u_iso`)?

With type-specific names, switching ADP type would require
creating/destroying parameters, migrating constraints and free flags,
and updating every reference. Type-neutral names make switching a
one-liner on `adp_type` — the parameter object stays the same, only its
value and CIF tag change.

### Why always-present aniso collection instead of on-demand?

Conditional existence of `atom_site_aniso` would require guards
everywhere: serialization, calculators, parameter tables, constraint
wiring, UI. Always-present with 0.0 defaults eliminates all those
branches.

### Why sync via `_update_categories()` instead of coupled add/remove?

Loose coupling: `AtomSites` and `AtomSiteAnisoCollection` don't know
about each other. `Structure` coordinates them at update time. This
follows the existing dirty-flag pattern and keeps categories independent.

### Why reorder `_cif_handler.names` instead of dynamic CIF handler?

The existing serialization/deserialization pipeline uses `names[0]` for
writing and iterates all names for reading. Reordering the list is a
2-line operation in the `adp_type` setter with zero core infrastructure
changes.
