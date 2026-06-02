# Review 1: Automatic Wyckoff Position Detection

## Findings

### [P1] Persisting resolved letters loses auto-mode semantics

The ADR defines auto mode as "provided marker false" and says auto-mode
letters re-detect after user edits, but the CIF write/read contract
materialises every resolved `_atom_site.Wyckoff_symbol` and then treats
any present symbol as explicit on reload (`wyckoff-letter-detection.md`,
sections 3, 4, and 9). That means a project saved while an atom is in
auto mode reloads with the same letter value but different behaviour:
future coordinate edits no longer re-detect the letter. This conflicts
with the persisted-state restore requirement and with the compatibility
claim that saved projects reload to the same model state. The ADR needs
to decide whether project persistence stores the auto/provided marker
separately, or whether save intentionally collapses auto-derived letters
into explicit letters and documents that behavioural change.

### [P1] Empty string cannot both mean auto and explicit assignment

Section 3 makes the empty `wyckoff_letter` value the auto sentinel, but
also says any API assignment marks the letter as provided. With that
contract, a user who previously set an explicit letter has no documented
way to clear it and return the site to auto mode: assigning
`atom.wyckoff_letter = ''` would set the provided marker true while
leaving the value empty, so detection would remain disabled and the
current "skip constraints" path would persist. The ADR should define the
public reset behaviour explicitly, for example by making assignment of
the empty sentinel clear the provided marker, or by adding a named
method/property for returning to auto mode.

### [P2] No-code space groups need an explicit key normalisation rule

Sections 2 and 8 describe direct `SPACE_GROUPS[(IT_number, coord_code)]`
lookups and use `P 1` as the example of a missing coordinate-system
code. In the current model, however, `SpaceGroup` represents
no-coordinate-code groups as the empty string because
`_it_coordinate_system_code_allowed_values` returns `codes or ['']`
(`src/easydiffraction/datablocks/structure/categories/space_group/default.py`).
The bundled table uses `None` keys for at least the no-code triclinic
groups, so an implementation that follows the ADR literally will look up
`(1, '')`, miss the tabulated `(1, None)` entry, and expose only the
empty sentinel instead of the real `a` Wyckoff position. The ADR should
state whether detection and allowed-letter discovery normalise `''` to
`None`, or intentionally treat no-code groups as unsupported despite the
packaged table containing them.

### [P2] CIF presence tracking is underspecified for the marker

Section 9 depends on distinguishing a present
`_atom_site.Wyckoff_symbol` from an absent one so the provided marker
can be set correctly. The generic CIF loader currently sets descriptor
values directly from loop cells and sets missing tags to descriptor
defaults in `category_collection_from_cif`
(`src/easydiffraction/io/cif/serialize.py`); it does not surface tag
presence to `AtomSite` or call a marker-aware setter. Without a specific
hook, a plan can easily mark defaulted missing values as user-provided,
or fail to mark present values as explicit. The ADR should name the
intended loading hook or item-level override that owns this boundary
case.

### [P3] The auto-fill path names an API that does not exist

Section 3 says auto-fill writes through `set_value_directly`, but the
current descriptor API exposes the public `value` setter plus private
paths such as `_set_value_from_minimizer`; there is no
`set_value_directly` symbol in `src/easydiffraction/core/variable.py`.
Because this write is central to avoiding a false "provided" marker, the
ADR should specify the actual private mutator to add or use, preferably
with a name tied to this derived-state update rather than the minimizer
path.

## Checks skipped

Per `AGENTS.md` review-shortcut rules, this was a static ADR/source
review only. I did not run tests, `pixi run fix`, `pixi run check`, or
other verification commands.
