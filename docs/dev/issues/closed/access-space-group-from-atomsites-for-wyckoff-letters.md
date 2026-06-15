# 51. Access Space Group from `AtomSites` for Wyckoff Letters

Closed by the Wyckoff-letter-detection implementation. `AtomSite` now
derives its allowed Wyckoff letters from the parent structure's space
group (via `_resolve_structure_space_group`) instead of a hardcoded
list, and the missing-letter case is handled explicitly: untabulated
space groups leave the Wyckoff letter and multiplicity unset, while
tabulated groups detect and fill them during the update flow.
