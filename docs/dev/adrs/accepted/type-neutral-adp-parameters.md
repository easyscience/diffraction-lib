# ADR: Type-Neutral ADP Parameters

## Status

Accepted.

## Date

2026-05-17

## Group

Structure model.

## Context

Atomic displacement parameters support CIF-standard B/U and
isotropic/anisotropic variants. Type-specific public names such as
`b_iso` and `u_iso` would require replacing parameter objects when
`adp_type` changes, breaking references, constraints, and free flags.

## Decision

Use type-neutral parameter names:

- `atom_site.adp_iso`
- `atom_site_aniso.adp_11`
- `atom_site_aniso.adp_22`
- `atom_site_aniso.adp_33`
- `atom_site_aniso.adp_12`
- `atom_site_aniso.adp_13`
- `atom_site_aniso.adp_23`

Use `atom_site.adp_type` to determine whether those values are B or U,
isotropic or anisotropic. Keep `atom_site_aniso` as an always-present
sibling collection and synchronize it from `atom_sites`.

## Consequences

Parameter object identity remains stable across ADP type switches.
Serialization and calculator code can branch on `adp_type` without
replacing public parameter objects.
