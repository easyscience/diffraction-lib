# Reply 11: Automatic Wyckoff Position Detection

Reply to
[`wyckoff-letter-detection_review-11.md`](wyckoff-letter-detection_review-11.md).

## [P1] `space_group_Wyckoff` still has unresolved structural decisions

**Verdict:** Agree.

**Action taken.** The ADR now settles the `space_group_Wyckoff`
structural decisions instead of deferring them:

- The collection key is `id`, serialized as `_space_group_Wyckoff.id`,
  so runtime identity follows the CIF category key rather than using the
  non-key `letter` descriptor.
- The category is explicitly read-only: row descriptors are getter-only,
  and public collection mutation paths (`add()`, `create()`, `remove()`,
  `__setitem__`, and `__delitem__`) raise a clear `ValueError`.
- `Structure._update_categories()` rebuilds the collection from the
  current space group via a private collection method before ordinary
  category update hooks run, so no special `_update_priority` is needed
  and no other category depends on this collection for detection.
- Project CIF excludes the derived loop via
  `Structure._serializable_categories()`, while IUCr/report output emits
  `_space_group_Wyckoff.*`; incoming loop values are ignored/overwritten
  because the category is re-derived from the space group.

The open questions about persistence, key choice, read-only mechanism,
and update priority were removed. Tests now explicitly cover the read-only
mutation paths, project-CIF omission, and report emission.

**Pointer:** Decision §6 (`space_group_Wyckoff` key/read-only/rebuild
paragraphs), Decision §9 (CIF behaviour), Open Questions, Testing.

## [P2] Stale atom-site `site_symmetry` wording remains

**Verdict:** Agree.

**Action taken.** Reworded the stale passages so `AtomSite` owns only the
read-only `multiplicity` descriptor, while `site_symmetry` is exposed on
read-only `space_group_Wyckoff` rows:

- Decision §1 now distinguishes atom-site letter/multiplicity from the
  space-group Wyckoff table that exposes site symmetry.
- Decision §2 no longer says the dataclass fills site-symmetry
  descriptors on atom sites.
- Decision §3 no longer describes unsupported explicit atom-site letters
  as carrying "site symmetry".
- The Related ADR entry for `guarded-public-properties.md` now names
  read-only `AtomSite.multiplicity` and read-only
  `space_group_Wyckoff` row descriptors.

**Pointer:** Decision §§1-3 and Related ADRs.
