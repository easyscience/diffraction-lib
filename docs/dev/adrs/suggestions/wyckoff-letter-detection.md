# ADR: Automatic Wyckoff Position Detection

**Status:** Proposed **Date:** 2026-06-01

## Group

Structure model.

> This ADR follows [`AGENTS.md`](../../../../AGENTS.md). No deliberate
> exception to those instructions is taken. The slug stays
> `wyckoff-letter-detection` for continuity with the request, but the
> decision covers the full Wyckoff _position_ (letter, multiplicity, and
> site symmetry), since all three come from one database entry.

## Context

Every `AtomSite` carries a Wyckoff letter that records the symmetry of
the site within the space group. Today the user must supply it by hand —
in Python (`atom_sites.create(..., wyckoff_letter='a')`) or in CIF
(`_atom_site.Wyckoff_symbol`). Several parts of the model already depend
on that letter:

- `AtomSites._apply_atomic_coordinates_symmetry_constraints()`
  ([`default.py:555`](../../../../src/easydiffraction/datablocks/structure/categories/atom_sites/default.py))
  reads `atom.wyckoff_letter.value`, looks up the Wyckoff position,
  snaps coordinates onto their special values, and flags symmetry-fixed
  axes so they cannot be refined. Atoms with no letter are silently
  skipped.
- `AtomSites._apply_adp_symmetry_constraints()` uses the letter (and the
  site coordinates) to constrain the anisotropic ADP tensor.
- The cryspy calculator overrides its own multiplicity from the letter
  in `_update_atom_multiplicity()`
  ([`cryspy.py:487`](../../../../src/easydiffraction/analysis/calculators/cryspy.py)),
  because cryspy normalizes coordinates into `[0, 1)` while parsing CIF
  and can misclassify a special position as general.
- The IUCr writer emits `_atom_site.Wyckoff_symbol`
  ([`iucr_writer.py:876`](../../../../src/easydiffraction/io/cif/iucr_writer.py)).

Two gaps remain, both recorded as open issue **#51**
([`open.md:999`](../../../../docs/dev/issues/open.md)):

1. The set of letters a site may take is a hardcoded placeholder,
   `['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i']`, with a TODO to read
   the real list from the current space group
   ([`default.py:200`](../../../../src/easydiffraction/datablocks/structure/categories/atom_sites/default.py)).
2. There is no decision on what happens when the user does not provide a
   letter.

The reference data needed to close both gaps is already bundled. The
packaged `SPACE_GROUPS` table
([`space_groups.py:98`](../../../../src/easydiffraction/crystallography/space_groups.py))
is keyed by `(IT_number, IT_coordinate_system_code)` and, for each
Wyckoff position, stores the **full orbit** of symmetry-equivalent
coordinate templates plus `multiplicity` and `site_symmetry`. For
example, Pm-3m (IT 221) letter `e` lists all six templates
`(x,0,0), (-x,0,0), (0,x,0), (0,-x,0), (0,0,x), (0,0,-x)` with
`multiplicity = 6` and `site_symmetry = '4m.'`; letter `a` is the single
`(0,0,0)` with `multiplicity = 1`.

The crystallography submodule already parses these templates into
rotation/translation pairs (`_parse_rotation_matrix()`,
[`crystallography.py:350`](../../../../src/easydiffraction/crystallography/crystallography.py))
and exposes `symmetry_operators()`. cryspy independently solves the same
problem — it tests a coordinate against every Wyckoff orbit and, among
the matches, picks the position with the **lowest multiplicity** (the
most special site). That algorithm is the inspiration here, but the
detection should live in EasyDiffraction so it does not depend on any
single calculator backend.

## Decision

### 1. EasyDiffraction owns the Wyckoff position

The library — not a calculator — is the single source of truth for an
atom site's Wyckoff **letter** and **multiplicity**, and for the
space-group Wyckoff table that exposes **site symmetry**. Calculators
consume these model values and must not re-derive them. Deriving them
model-side, from the un-normalized fractional coordinates, is also the
_correct_ place: it avoids the `[0, 1)` normalization that forces the
cryspy override to exist today.

### 2. Detection lives in the crystallography submodule

Add to
[`crystallography.py`](../../../../src/easydiffraction/crystallography/crystallography.py):

- `detect_wyckoff_position(name_hm, coord_code, fract_xyz, tol=...) -> WyckoffPosition | None`
  — the orbit matcher. It resolves `(IT_number, coord_code)` (after the
  key normalisation below); returns `None` only when that pair is
  genuinely absent from `SPACE_GROUPS`, preserving today's "no letter,
  skip constraints" behaviour. Otherwise it tests the coordinate for
  membership in each Wyckoff orbit and returns the matched position plus
  the nearest matched representative template.
- `wyckoff_position_info(name_hm, coord_code, letter, fract_xyz=None, tol=...) -> WyckoffPosition | None`
  — a table lookup for an already-known letter (auto-detected or
  user-set). When `fract_xyz` is supplied, it selects the nearest orbit
  representative for that letter before returning the record; when
  `fract_xyz` is omitted, it returns the record without a selected
  representative. This populates derived values and supports explicit-
  letter snapping without re-running the all-letter matcher.

Both return a small frozen
`WyckoffPosition(letter, multiplicity, site_symmetry, coord_template)`
dataclass rather than bare tuples: the named values are consumed
together when a position is detected or looked up (the atom site stores
the letter and multiplicity; the derived `space_group_Wyckoff` table
exposes the site-symmetry symbol), and the selected `coord_template` is
what coordinate snapping and constrained-axis flags use.
`coord_template` is `None` only for plain table lookups that do not
provide coordinates. Named fields read better at the call sites, and the
record can later carry the equivalent-position orbit without a breaking
positional change. This matches the project's frozen-dataclass metadata
idiom (`TypeInfo`, `Compatibility`); the bare-tuple alternative is
rejected as less readable and fragile to extension.

**Orbit-membership test.** For a coordinate `p = (x, y, z)` and an orbit
template parsed into rotation `R` and translation `b`, the point lies on
that template when `R·v + b ≡ p (mod 1)` is solvable for some real `v`.
The general position (templates with all of `x, y, z` free) always
matches, so a space group present in the table always yields a letter.
Among all matching positions the winner is chosen by **(multiplicity
ascending, then residual ascending)**: the most special site first, and
— in the rare case where two distinct positions of the _same_
multiplicity both lie within `tol` — the one the coordinate is actually
closest to. The matcher already computes that residual while testing
membership, so the tie-break costs nothing extra. A genuine
same-multiplicity tie within `tol` (which a small tolerance makes almost
impossible, since distinct special positions are separated by fractions
like 1/2) is reported with a `log.warning` naming both candidates.
Refusing to guess (raising) was rejected because it would break the
"always resolve a letter" guarantee for an essentially unreachable case,
and an arbitrary table-order pick was rejected as less physical than
nearest-position.

**Representative selection.** The matcher also records the nearest
template inside the winning orbit. That selected `coord_template`, not
the first `coords_xyz[0]` entry in the table, drives the existing
coordinate-snap and constrained-axis logic. For example, in Pm-3m letter
`6e`, a point near `(0,x,0)` must snap and constrain according to the
`(0,x,0)` representative, not the first table representative `(x,0,0)`.
The explicit-letter path uses
`wyckoff_position_info(..., fract_xyz=current_coords)` to select the
nearest representative for the chosen letter before snapping.

**Numeric kernel.** Solve the modular linear system with NumPy
least-squares and check the residual modulo 1 against `tol` (reduce
`p − b` to its nearest unit cell, solve `R·v = d`, require the residual
≡ 0 mod 1 within `tol`). This is simple, fast, and naturally
tolerance-based. cryspy's exact rational kernel
(`Fraction.limit_denominator` + Gaussian elimination mod 1) is the
fallback option if numeric edge cases appear — see _Alternatives_.

**Key normalisation.** `SpaceGroup` represents a group with no
coordinate-system code as the empty string `''` (its
`_it_coordinate_system_code_allowed_values` returns `codes or ['']`),
but the bundled table stores those groups under a `None` code — the
triclinic groups are `(1, None)` (P1, Wyckoff `a`, multiplicity 1) and
`(2, None)` (P-1), and there are no empty-string keys at all. Detection
and allowed-letter discovery therefore normalise `''` to `None` before
indexing `SPACE_GROUPS`, so P1 and P-1 resolve to their real Wyckoff
positions instead of being mistaken for unsupported groups. A shared
`_normalize_coord_code()` helper owns this mapping; the existing
`_get_wyckoff_exprs()` and `_get_general_position_ops()` lookups
([`crystallography.py`](../../../../src/easydiffraction/crystallography/crystallography.py))
should adopt it too, since they currently miss the `None`-keyed groups.

### 3. The letter is always set, and tracks the coordinates

The `wyckoff_letter` descriptor holds a concrete value whenever the
space group is supported — there is no persistent "auto vs explicit"
mode and no marker bit. The one exception is a space group absent from
`SPACE_GROUPS` (§8), where auto-detection is a no-op. If no letter is
currently stored, the value stays empty; if any non-empty letter is
stored, whether supplied by Python/CIF input or preserved after a later
change from a supported key into an unsupported one, it is kept verbatim
but carries no Wyckoff record, derived multiplicity, or constraints
(§6). §9 defines how each of those cases serialises. For a supported
group the letter changes in three ways:

- **Creation or load without a letter.** When `atom_sites.create()` is
  called without `wyckoff_letter`, or a CIF row has no
  `_atom_site.Wyckoff_symbol`, detection runs against the coordinates
  and stores the result. The descriptor default is a transient
  placeholder that detection replaces; it is never surfaced as a lasting
  state.
- **User edits the coordinates** (any public path — `atom.fract_x = …`
  or the live-descriptor `atom.fract_x.value = …`). The letter is
  re-detected from the new coordinates and stored again; if it differs
  from the current one, a warning is logged (§5). This keeps the letter
  honest as the structure is edited. The trigger is update-flow
  change-tracking, not a single setter (§4), so every public coordinate
  edit is covered.
- **User edits the space group or setting.** A change to
  `structure.space_group.name_h_m` or
  `structure.space_group.it_coordinate_system_code` invalidates every
  atom site's Wyckoff record even when coordinates are unchanged. For a
  supported new key, all sites re-detect from their current coordinates
  and refresh letter, multiplicity, and selected representative. For an
  unsupported new key, auto-detection is a no-op: existing letters are
  preserved verbatim as unvalidated values, multiplicities become
  `None`, constraints are skipped, and a warning records that the group
  is untabulated. Preserving the stored letter is chosen over clearing
  it because, without a persistent auto/provided marker, deleting it
  could remove valid user or CIF input.
- **User edits the letter** (public letter setter). The chosen letter is
  applied as-is and persists. Its site-symmetry constraints snap the
  constrained axes onto the special position (§5); if the pre-set
  coordinates lay beyond `tol` of that letter's orbit — they did not fit
  — a warning is logged that the coordinates were adjusted, but the
  change is still made. A user-set letter is not re-detected until the
  user next edits the coordinates or space-group key. (For a space group
  absent from the table the letter is accepted unvalidated and carries
  no derived data or constraints — §8.)

Detection writes the resolved letter through a dedicated internal
mutator, `_set_wyckoff_letter_detected()`, modelled on the existing
non-validating writer `_set_value_from_minimizer`
([`variable.py:171`](../../../../src/easydiffraction/core/variable.py))
(there is no `set_value_directly` method). Assigning the empty value to
the public setter is permitted and simply requests re-detection on the
next update.

### 4. Detection triggers

All triggers live in the atom-site update flow
([`default.py:674`](../../../../src/easydiffraction/datablocks/structure/categories/atom_sites/default.py)),
not on any individual setter. A single setter hook would be wrong: a
coordinate is a live `Parameter`, so `atom.fract_x = 0.1` and
`atom.fract_x.value = 0.1` are both public edits — and the latter is the
common one — yet neither must be missed. Both coordinate paths mark the
owner dirty and run `_update()`, so the update flow is the single place
that sees every edit.

- **Fill-if-empty.** An empty letter on a site whose space group is
  supported is detected and stored. Idempotent — a no-op once the letter
  is non-empty — and it is what fills letters on `create()` and project
  load.
- **Re-detect on a coordinate change.** The flow records, per atom, the
  coordinates a letter was last detected from. When the current
  coordinates differ from that baseline it re-detects; if the letter
  changes it stores the new one and warns (§5). The baseline is
  refreshed to the current coordinates whenever the letter is set or
  detected — on load, on a user letter-set, and after auto-detection
  (including the constraint snap that follows in the same pass) — so
  only a genuine _later_ coordinate change re-detects, and a freshly
  loaded or user-set letter is not re-detected spuriously.
- **Re-detect on a space-group key change.** The flow also records the
  `(name_hm, coord_code)` key used for the last Wyckoff derivation. If
  that key changes, every atom site re-runs the supported/unsupported
  policy from §3 even when coordinates are unchanged. A supported new
  key re-detects all letters and multiplicities; an unsupported key
  preserves stored letters as unvalidated values, clears derived
  multiplicity to `None`, and skips constraints.

Two write paths are deliberately excluded. The minimizer runs
`_update()` with `called_by_minimizer=True`, which skips re-detection
entirely, so a free Wyckoff parameter (such as `x` in `(x, 0, 0)`)
varies throughout a fit while the letter stays fixed. The constraint
pipeline's snap does not re-trigger detection because it writes within
the same pass and its result becomes the new baseline. A user-set letter
— even a deliberately less-special one — is therefore never silently
overwritten by a minimizer update or by the same-pass constraint snap.
It can be re-detected only by a later user coordinate edit or a later
space-group / setting key edit, both of which are explicit model changes
tracked by the stored baselines above.

### 5. Lenient proximity matching, with transparent snapping

The tolerance is a module-level constant in `crystallography.py`
(`_WYCKOFF_DETECTION_TOL`, default `1e-3`), used as the default of the
matcher's `tol` argument so tests can override it. `1e-3` (fractional)
is lenient enough to recognise rounded inputs — a database CIF with
`0.3333` for `1/3`, or `0.4999` for `1/2` — as the special position, yet
tight enough not to mislabel a genuinely general site (distinct special
positions are separated by fractions like 1/2). A user-facing or
project-level tolerance setting is intentionally deferred (see Deferred
Work) until users ask for it. Once a letter is assigned, the existing
constraint step snaps the constrained axes onto their exact special
values. Neither the letter nor the coordinates change silently in
response to a user edit; `log.warning` messages cover the cases (per the
project's "safe defaults, clear errors" principle):

- a user coordinate edit or supported space-group edit that changes the
  detected letter → _"change moved the Wyckoff letter of <site> from X
  to Y"_;
- a user letter change whose snap moves coordinates beyond `tol` →
  _"coordinates of <site> did not fit letter L and were adjusted"_;
- a user coordinate edit whose constraint snap changes coordinates even
  when the letter stays the same → _"coordinates of <site> were adjusted
  to satisfy Wyckoff letter L"_;
- a space-group change into an unsupported key with a stored letter →
  _"Wyckoff letter of <site> is stored but not validated because the
  space group is untabulated"_.

Fill-if-empty detection on `create()` / load is the expected baseline
and is not warned per atom.

### 6. Per-atom multiplicity, and a new `space_group_Wyckoff` category

The per-atom **multiplicity** stays on `AtomSite` as a read-only derived
descriptor, populated from the `WyckoffPosition` record (via
`wyckoff_position_info()`) for the resolved letter and re-derived
alongside it. It is read-only (getter only, no setter) per the
guarded-public-properties contract — the user influences it only through
the coordinates and the (optional) stored letter — and carries the
standard CIF tag `_atom_site.site_symmetry_multiplicity`. Its empty form
is `None`, and that empty state follows **record availability**, not the
letter: a no-record site (an unsupported space group, with or without a
stored non-empty letter; or a transient empty letter before the first
update) has `None` multiplicity whether its letter is empty or stored
but unvalidated (§8). `None` serialises to CIF `?` (§9) and the
calculator skips it (§7).

The **site-symmetry symbol is not an atom-site quantity.** In the CIF
core dictionary it belongs to the `space_group_Wyckoff` loop
(`_space_group_Wyckoff.site_symmetry` — "the subgroup of the space group
that leaves the point fixed"), alongside the Wyckoff `letter`,
`multiplicity`, and `coords_xyz`. EasyDiffraction therefore gains a new
read-only `space_group_Wyckoff` category on the crystal structure (a
sibling of `space_group`, `cell`, `atom_sites`). It lists every Wyckoff
position of the structure's current space group — `id` (the CIF category
key, e.g. `6e`), `letter`, `multiplicity`, `site_symmetry`, and the
representative `coords_xyz` — sourced from `SPACE_GROUPS[key]` (`key`
via the §2 normalisation). This is the symbol's correct home and the
natural place for the deferred "expose the full orbit" work.

The collection key is `id`, serialized as `_space_group_Wyckoff.id`.
That follows the CIF category-key identity rather than using `letter` as
a Python-only shortcut: the `letter` field remains a meaningful
descriptor, but `id` is the stable row identity (for example `6e`) and
keeps the runtime key aligned with the CIF key rule from
[`loop-category-key-identity.md`](../accepted/loop-category-key-identity.md).

The category is **derived and read-only**: the user neither creates nor
edits its entries. Every item descriptor is getter-only, and the
collection rejects public mutation paths (`add()`, `create()`,
`remove()`, `__setitem__`, and `__delitem__`) with a clear `ValueError`.
`Structure._update_categories()` rebuilds it from the current space
group through a private collection method (for example
`_replace_from_space_group()` using internal adoption) before running
ordinary category update hooks, so no special `_update_priority` is
needed and no other category depends on it for detection. This
read-only, auto-populated collection is a **new pattern** in the model —
no prior instance exists (the closest, `atom_site_aniso`, is
sync-managed but user-editable) — and is justified by being a
CIF-defined category whose contents are fully determined by the space
group. When the space group is absent from `SPACE_GROUPS`, the category
is empty.

`site_symmetry` stores the International Tables site-symmetry symbol
**verbatim** from the table, including its positional dots (for example
`'4/mm.'`, `'.3m'`, `'..m'`). The dots are not noise: they encode which
crystallographic directions the site's symmetry elements lie along, so
stripping or "normalising" them would be lossy and is rejected. Verbatim
is also the simplest form and the one crystallographers expect from
International Tables.

### 7. Calculators consume, never re-derive

`_update_atom_multiplicity()` in the cryspy calculator is **replaced**:
instead of looking multiplicity up from `SPACE_GROUPS`, it reads
`atom_site.multiplicity.value`. This is behaviour-preserving — same
table, same letter, same number — but removes the duplicated lookup and
makes multiplicity uniform across backends. crysfml and pdffit2 do not
compute multiplicity today (no other usages in `src/`), so nothing
diverges. Removing the calculator's private derivation is an explicit,
called-out replacement, not a silent change. When
`atom_site.multiplicity.value` is `None` (no Wyckoff record — an
unsupported group), the calculator leaves the backend's own inferred
multiplicity in place rather than writing `None` into its array; this
too is behaviour-preserving, since today's `_update_atom_multiplicity()`
already returns early when the group is absent from `SPACE_GROUPS`.

### 8. Allowed letters come from the current space group (closes #51)

`_wyckoff_letter_allowed_values` stops returning the hardcoded list and
instead returns the empty placeholder value plus the tabulated letters
for the current space group,
`list(SPACE_GROUPS[key]['Wyckoff_positions'])`, where `key` applies the
§2 coordinate-code normalisation. The bundled table now covers all 230
groups, so a genuinely absent group is rare — an exotic non-standard
setting, or a transient pre-update state — and the absent-group path
below is a guard, not a common case. When the space group is genuinely
absent from the table its letters cannot be enumerated, so membership
validation is not applied — the validator accepts whatever the user or a
CIF supplies. Auto-detection is still a no-op there, but an explicit
letter from Python/CIF input is stored verbatim rather than rejected,
and a previously stored letter is preserved when a later space-group
change moves the site into an unsupported key. Blocking a valid
assignment, failing to load an otherwise-valid CIF, or deleting a
possibly valid stored value is worse than keeping an unverifiable
letter. A stored non-empty letter in this no-record state carries no
`multiplicity` (§6), drives no symmetry constraints, and a `log.warning`
records that the group is untabulated so the letter could not be
validated. Rejecting with a validation error was the considered
alternative, declined as too brittle for boundary input that Python
assignment and CIF loading routinely produce. The atom site reaches its
space group through the parent chain
`atom → atom_sites → structure → space_group`, the same access already
used for ADP synchronisation
([`default.py:252`](../../../../src/easydiffraction/datablocks/structure/categories/atom_sites/default.py)).
This keeps Wyckoff letters a space-group-dependent, boundary-facing
selector rather than a project-owned enum, consistent with
[`value-selector-discovery.md`](../accepted/value-selector-discovery.md)
and
[`enum-backed-closed-values.md`](../accepted/enum-backed-closed-values.md).

### 9. CIF behaviour

Because the letter is concrete for every supported space group (§3), the
project CIF treats it as an ordinary value — none of the earlier draft's
column-omission or null-token juggling is needed. An unsupported group
is the only special case, and it splits in two — no stored letter stays
empty, while any stored non-empty letter is written verbatim — both of
which fall out naturally below.

- **Write.** Emit `_atom_site.Wyckoff_symbol` for every atom, plus the
  standard `_atom_site.site_symmetry_multiplicity` derived from the
  model multiplicity (written as `?` when that multiplicity is `None`).
  **Any** non-empty letter is written verbatim — whether detected for a
  supported group, supplied explicitly for an unsupported one, or
  preserved after a later change into an unsupported key (§3, §8). A
  non-empty letter in an unsupported group carries a `None` multiplicity
  because it is stored but unvalidated. A letter is empty, and
  serialises as the CIF null `?`, only when it is neither detected nor
  otherwise stored — an unsupported group with no stored letter, or a
  transient not-yet-updated state. `?` is already the serializer's
  output for an empty string
  ([`serialize.py:62`](../../../../src/easydiffraction/io/cif/serialize.py))
  and reads back as empty. The column is therefore always present and
  well-defined for the columnar atom-site loops emitted through the
  ADP-family path
  ([`serialize.py:301`](../../../../src/easydiffraction/io/cif/serialize.py)),
  whether or not every row has a resolved letter, and saving never fails
  on an unsupported group.
- **Read.** A present `_atom_site.Wyckoff_symbol` is loaded as the
  letter; an absent column — or a CIF-null `?` / `.`, which loads as the
  empty default
  ([`serialize.py:1091`](../../../../src/easydiffraction/io/cif/serialize.py))
  — leaves the letter empty, and fill-if-empty detection (§4) resolves
  it from the coordinates. A round trip is therefore stable: a written
  letter reloads verbatim, and an omitted one re-derives to the same
  value (same coordinates + space group → same letter), or stays empty
  when the space group is unsupported.
- **IUCr report export.** The report writer
  ([`iucr_writer.py:876`](../../../../src/easydiffraction/io/cif/iucr_writer.py))
  already emits the resolved `Wyckoff_symbol` for every atom and now
  also emits `_atom_site.site_symmetry_multiplicity`.
- **`space_group_Wyckoff` loop.** The derived category is model-owned
  and report-facing, but it is not persisted in project CIF. `Structure`
  explicitly excludes it from project-save serialization via
  `_serializable_categories()`, overriding `CategoryOwner`'s default of
  serializing all owned categories. The IUCr/report writer emits the
  `_space_group_Wyckoff.*` loop from the derived category because that
  loop is useful report output even though it is redundant persisted
  state.
- **Derived values on read.** Multiplicity is recomputed from the
  letter, so any incoming `_atom_site.site_symmetry_multiplicity` is
  ignored rather than trusted; the `space_group_Wyckoff` category is
  re-derived from the space group, so any incoming
  `_space_group_Wyckoff.*` values are ignored/overwritten too — the
  library does not validate its own derived output at runtime.

## Open Questions

- The default tolerance value (`1e-3`) is a reasonable starting point
  but may be tuned against real datasets during implementation and
  testing.

## Consequences

### Positive

- Users who omit the Wyckoff letter still get correct symmetry
  constraints, multiplicities, and site symmetries.
- Closes issue #51: the allowed-letter list becomes real and
  space-group-aware.
- Multiplicity becomes calculator-independent and is derived where the
  coordinates are still un-normalized, which is the correct place.
- No new dependency: detection reuses `SPACE_GROUPS`, NumPy, and the
  existing rotation/translation parser.
- CIF round-trips are stable: a written letter reloads verbatim, and an
  omitted one is re-derived deterministically from the coordinates (§9).

### Trade-offs

- Lenient matching can move a coordinate by up to the tolerance; this is
  surfaced by a warning but is a behavioural change for atoms that
  previously had no letter and were left untouched.
- A user-set letter is **not** a permanent pin: editing the coordinates
  or changing the space-group key re-detects the letter and may change
  it (with a warning). A user who needs a letter held must avoid editing
  its coordinates or space-group setting, or re-set the letter
  afterwards. This is the deliberate cost of keeping the letter,
  coordinates, and space-group key consistent.
- `AtomSite` gains one read-only derived descriptor (`multiplicity`),
  and a new read-only, auto-populated `space_group_Wyckoff` category
  exposes the per-position `site_symmetry` (and the full Wyckoff table)
  — a new derived-collection pattern in the model.

### Compatibility Outcomes

- Projects that already specify every Wyckoff letter keep those letters:
  explicit letters are respected and reload verbatim. Their constraints
  remain unchanged except where the current first-representative
  shortcut was wrong for coordinates on another representative of the
  same orbit; that case is intentionally fixed by nearest-representative
  selection.
- A saved project reloads to the same letters: every letter is written
  (whether the user supplied it or detection filled it), so all reload
  verbatim — and an auto-filled one would re-derive to the same value
  anyway.
- cryspy fit results are unchanged: the multiplicity value is identical,
  only its source moves from the calculator to the model.

## Alternatives Considered

- **cryspy exact rational kernel.** Use `Fraction.limit_denominator` and
  Gaussian elimination mod 1 (cryspy's method). Exact and robust, but
  heavier than needed when a tolerance is wanted anyway. Kept as the
  fallback if the NumPy kernel shows numeric edge cases.
- **Delegate detection to a calculator** (for example cryspy's
  `calc_xyz_mult`). Rejected: it recouples a core model property to a
  specific backend — the opposite of this ADR — and inherits cryspy's
  `[0, 1)` normalization problem.
- **Add spglib or gemmi for symmetry datasets.** Rejected: a new
  dependency for data the bundled `SPACE_GROUPS` table already contains
  as full orbits.
- **Detect once, then freeze permanently.** Rejected: the letter would
  go stale when the user edits coordinates. The adopted model instead
  re-detects on a user coordinate edit (§4), so the letter follows the
  structure.
- **A persistent auto/provided marker** (an earlier draft of this ADR).
  Rejected as unnecessary complexity: it required an empty-sentinel
  state, a marker bit, and column-omission / null-token rules in the
  project CIF. Always materialising the letter and re-detecting on user
  coordinate or space-group-key edits yields the same user-facing
  behaviour with no marker and a plain, fully-populated CIF column.
- **Keep the letter purely derived and never stored.** Rejected: the
  calculator and the Python↔CIF correspondence read `.value`, and users
  need to be able to override the letter; a never-stored value cannot be
  overridden.

## Testing

Detection comes with a ready-made regression corpus: the ~20 tutorial
scripts in `docs/docs/tutorials/*.py`. Most build structures with
explicit Wyckoff letters and a few load structures from CIF, so in every
case the declared letter is ground truth. Stripping a site's explicit
letter and re-detecting from its coordinates and space group must
reproduce that declared letter — a single assertion that yields broad,
real-world coverage across many space groups, settings, and site types
at almost no authoring cost, and guards against regressions whenever the
tutorials change.

Targeted tests in `tests/unit/easydiffraction/crystallography/`
(mirroring the source per the
[test-strategy ADR](../accepted/test-strategy.md)) cover what the corpus
may miss:

- general vs special positions, and the lowest-multiplicity / nearest
  tie-break (§2);
- non-first orbit representatives, including auto-detection of a point
  near a representative such as `(0,x,0)` and explicit-letter snapping
  via the nearest representative rather than `coords_xyz[0]` (§2, §5);
- lenient matching of rounded inputs (`0.3333 → 1/3`, `0.4999 → 1/2`) at
  the `1e-3` tolerance (§5);
- the `''`→`None` coordinate-code normalisation — P1/P-1 under their
  `None` keys, and a genuinely-absent group resolving to the empty
  letter (§2, §8);
- the §3–§4 behaviours: fill-if-empty on `create()` / load; re-detect on
  a user coordinate edit via _both_ `atom.fract_x = …` and
  `atom.fract_x.value = …`, with the change warning; the user letter
  override with the snap warning; same-letter coordinate edits whose
  snap moves stored coordinates; supported space-group / setting changes
  re-detecting all atom sites; unsupported space-group transitions
  preserving stored letters as unvalidated values with `None`
  multiplicity; and the minimizer leaving the letter fixed;
- the no-record contract (§6–§7, §9): `None` `multiplicity`, `?` in CIF,
  the calculator skip, and an empty `space_group_Wyckoff` category for
  an absent group;
- the new `space_group_Wyckoff` category: it auto-populates from the
  structure's space group (each entry's letter / multiplicity /
  site_symmetry / coords match `SPACE_GROUPS`), rebuilds when the space
  group changes, refuses all public mutation paths, is empty for an
  absent group, is omitted from project CIF, and is emitted in
  IUCr/report output;
- CIF round-trip stability — a written letter reloads verbatim, an
  omitted one re-derives to the same value, and an unsupported-group row
  keeps `None` multiplicity whether its letter is empty, explicitly
  supplied, or preserved from prior supported detection; non-empty
  unsupported letters round-trip verbatim.

The edge-case tests are unit-level (no calculation engine, no network,
no sleeping) per the test-strategy ADR; the tutorial-corpus checks fit
at the functional / script level where the tutorial structures are
already built.

## Deferred Work

- Exposing the full equivalent-position orbit for an atom (the
  visualization path already derives general-position operators via
  `symmetry_operators()`).
- Suggesting or validating the space group from the complete set of atom
  positions (the reverse problem).
- A user-facing or project-level tolerance setting, if users ask to
  control the `_WYCKOFF_DETECTION_TOL` module-constant default.
- Using multiplicity in occupancy-normalization helpers.

## Related ADRs

- [`space-group-database.md`](../accepted/space-group-database.md) — the
  complete, self-owned `SPACE_GROUPS` reference table (all 230 groups,
  every setting and full Wyckoff orbit) that this detection reads.
- [`category-owner-sections.md`](../accepted/category-owner-sections.md)
  — the new read-only, auto-populated `space_group_Wyckoff` category is
  a `CategoryOwner`-held sibling category on the crystal structure.
- [`iucr-cif-tag-alignment.md`](../accepted/iucr-cif-tag-alignment.md) —
  `_atom_site.Wyckoff_symbol` and
  `_atom_site.site_symmetry_multiplicity` tags.
- [`python-cif-category-correspondence.md`](../accepted/python-cif-category-correspondence.md)
  — `wyckoff_letter` ↔ `_atom_site.Wyckoff_symbol`.
- [`type-neutral-adp-parameters.md`](../accepted/type-neutral-adp-parameters.md)
  — the ADP symmetry constraints that already consume site symmetry.
- [`value-selector-discovery.md`](../accepted/value-selector-discovery.md)
  and
  [`enum-backed-closed-values.md`](../accepted/enum-backed-closed-values.md)
  — why Wyckoff letters are a dynamic, space-group-dependent selector
  rather than a project-owned enum.
- [`guarded-public-properties.md`](../accepted/guarded-public-properties.md)
  — read-only `AtomSite.multiplicity` and read-only
  `space_group_Wyckoff` row descriptors, including `site_symmetry`
  (getter only).
