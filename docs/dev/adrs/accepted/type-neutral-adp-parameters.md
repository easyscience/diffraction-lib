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

## Extension (2026-06-10): β-tensor support

The dimensionless **β tensor** — the third standard anisotropic ADP
convention (FullProf, SHELX-era data, cryspy's internal representation)
— is added as a first-class `adp_type` value, `beta`, reusing the same
type-neutral `adp_11`…`adp_23` objects. This keeps the core decision
intact: parameter object identity is still stable across a switch to or
from `beta`. Implications specific to β:

- **No isotropic form.** `beta` always implies anisotropic; there is no
  `adp_iso` β counterpart.
- **Cell-dependent conversion.** Unlike the scalar `B = 8π²U`, the β↔U
  transform depends on the reciprocal cell: `β_ij = 2π²·U_ij·a*_i·a*_j`.
  Type switches to/from `beta` therefore require the parent structure's
  `cell`; with no reachable cell the switch raises rather than producing
  wrong values.
- **Dimensionless units.** β components carry no `Å²` unit. The stored
  Parameter keeps a single declared unit; the display layer suppresses
  the unit when `adp_type == 'beta'` rather than mutating parameter
  metadata.
- **Negative off-diagonals.** Off-diagonal components (any convention, β
  included) may be negative; the aniso off-diagonal validator allows
  negatives.
- **CIF.** `_atom_site_aniso.beta_11`…`beta_23` join the existing
  `B_ij`/`U_ij` tag lists; the writer's ADP-family grouping gains a
  `beta` family.
- **Minimizer write path bypasses validation.** Applying site-symmetry
  constraints to the aniso tensor during a fit
  (`AtomSites._apply_adp_symmetry_constraints(called_by_minimizer=True)`)
  writes components through `Parameter._set_value_from_minimizer`, which
  skips the diagonal `RangeValidator(ge=0, le=10)`. The minimizer
  explores trial values that may transiently fall below zero, and the
  symmetry-averaged write-back can too; validating it would abort the
  refinement. The interactive path keeps full validation. Applies to
  every aniso convention (Bani/Uani/beta).
- **cryspy (two β paths).** β reaches cryspy two ways: the refinement
  loop writes stored β straight into `cryspy_beta` (β is cryspy's native
  convention), while cryspy's CIF parser — which understands only U/B
  aniso tags — is fed a transient `Uani` relabel
  (`U_ij = β_ij/(2π²·a*_i·a*_j)`) during structure-CIF generation, then
  β is restored. The round-trip is mathematically exact, so the net
  behaviour is β-in/β-out.

Plan: [`adp-beta-tensor.md`](../../plans/adp-beta-tensor.md).
