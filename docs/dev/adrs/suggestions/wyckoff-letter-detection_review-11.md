# Review 11: Automatic Wyckoff Position Detection

## Findings

### [P1] `space_group_Wyckoff` still has unresolved structural decisions

The ADR now introduces `space_group_Wyckoff` as a new read-only,
auto-populated `CategoryOwner` sibling category, but then leaves its
implementation-critical choices open: whether the loop is persisted or
report-only, whether the row key is `_space_group_Wyckoff.id` or
`letter`, how `add()` / `create()` are blocked, and what update priority
rebuilt-from-space-group categories need (`wyckoff-letter-detection.md`
386-412). These are not just implementation details. Current
`CategoryOwner._serializable_categories()` serialises every owned
category by default, current `CategoryCollection` exposes mutating
`__setitem__` / `remove` paths in addition to any subclass `add()` /
`create()`, and `loop-category-key-identity.md` requires every concrete
loop collection to have a documented key field that normally serialises.

Please settle these decisions in the ADR before it is accepted: choose
whether `space_group_Wyckoff` is persisted, report-only, or explicitly
excluded from project CIF; choose and justify the collection key; and
state the read-only collection mechanism at the category/collection API
level, not only item `add()` / `create()`. Otherwise two implementers can
both follow the ADR and produce incompatible public/CIF behaviour.

### [P2] Stale atom-site `site_symmetry` wording remains

The updated ADR correctly says the site-symmetry symbol is **not** an
atom-site quantity and belongs in `space_group_Wyckoff`
(`wyckoff-letter-detection.md` 266-289). But earlier/later text still
reads like `site_symmetry` is an atom-site descriptor: the dataclass
motivation says it fills "the letter, multiplicity, and site-symmetry
descriptors" (`wyckoff-letter-detection.md` 97-101), and the Related ADR
entry for `guarded-public-properties.md` says "read-only `multiplicity`
and `site_symmetry` (getter only)" (`wyckoff-letter-detection.md`
561-562). That stale wording risks reintroducing the older
`AtomSite.site_symmetry` design that review 5 on the plan just rejected.

Please reword those passages so `multiplicity` is the atom-site
descriptor, while `site_symmetry` is the read-only descriptor on
`space_group_Wyckoff` rows.

## Checks skipped

Per `AGENTS.md` review-shortcut rules, this was a static ADR/source
review only. I did not run tests, `pixi run fix`, `pixi run check`, or
other verification commands.
