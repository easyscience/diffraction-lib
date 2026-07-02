# 135. More Intuitive ADP Creation API (type-aware kwargs)

**Priority:** `[priority] medium`

**Type:** API design

Creating an atom currently requires setting `adp_type` and the
type-neutral `adp_iso`/`adp_11`… values separately (for example
`add(..., adp_type='Biso', adp_iso=0.5)`). For scientists this is less
discoverable than naming the displacement convention directly. Options
to explore: a richer creation surface with type-aware convenience
keywords (`b_iso=`/`u_iso=`/`beta=`) that set `adp_type` automatically,
and/or CIF-style auto-attachment of the sibling isotropic/anisotropic
values when `adp_type` is set. This revisits the accepted
[type-neutral-adp-parameters](../../../../docs/dev/adrs/accepted/type-neutral-adp-parameters.md)
ADR — which deliberately chose type-neutral storage to keep parameter
identity stable across switches — so it needs its own ADR + plan and is
independent of the β-tensor work that surfaced it.

**Depends on:** the β-tensor ADP support (shipped in #199).
