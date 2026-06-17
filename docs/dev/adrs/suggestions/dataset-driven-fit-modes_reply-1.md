# Reply 1: Dataset-Driven Fit Modes and Sequential Redefinition

## P1 — Resolve the `sequential_fit` category before redefining `sequential`

**Verdict:** Agree.

The redefinition and the deferred folder sweep genuinely cannot share
the `sequential_fit` / `sequential_fit_extract` surface — and the two
input models cannot live under one count-gated mode, since the folder
sweep needs _exactly one_ template while loaded-dataset `sequential`
needs _≥2_ (opposite preconditions). The ADR now commits to a first-step
contract instead of leaving the surface ambiguous.

**Action taken:**

- Added **Decision 5a — "The folder-of-files sweep is parked for the
  first step"**: loaded-dataset `sequential` uses neither folder
  category; the folder-sweep path and its categories are retained in
  code but parked (not selectable, hidden from display, omitted from CIF
  so stale folder settings cannot survive under a mode that no longer
  reads them). Restoration is the deferred input-source ADR.
- Flagged the parking as a **temporary removal of a tested workflow
  requiring owner sign-off** (per §Change Discipline), with the
  no-removal alternative spelled out.
- Added **Alternatives Considered — "Split the folder sweep into a
  `scan` mode now"** as the documented fallback (keeps the feature
  continuously available at the cost of adding `scan` to the one-dataset
  availability row).
- Rewrote the **Open Questions** folder-sweep item to separate the now-
  settled first-step contract from the still-open long-term home, and
  updated the **Trade-offs** bullet accordingly.

Affected sections: `## Decision` (5a), `## Alternatives Considered`,
`## Open Questions` (long-term home of the folder sweep),
`## Consequences` (Trade-offs).

## P1 — Define replay semantics so plotting does not corrupt live state

**Verdict:** Agree.

Applying a stored per-point parameter set to the single shared structure
is itself a mutation, so the issue-85 fix needed an explicit rule to
avoid replacing one correctness bug with another (plotting point A
changing point B / `save` / `undo`).

**Action taken:**

- Added **Decision 4a — "Replay contract"**: the live model is
  authoritative and never perturbed by viewing; per-point recomputation
  is a scoped, self-restoring apply (captures live values, computes,
  restores on exit including on error, internal-only); plotting prefers
  reading persisted/cached per-point calculated arrays over recomputing;
  and `save` / `undo` operate on the live model only, independent of
  whichever point was last plotted.

Affected section: `## Decision` (4a).

## P1 — Specify what makes loaded experiments a valid sequential series

**Verdict:** Agree.

"Two loaded experiments" is not the same as "a fittable series," and the
preconditions belong in the decision rather than the plan.

**Action taken:**

- Extended **Decision 3** to make the carry-forward scope precise
  (shared structure parameters carry forward; per-experiment parameters
  are fit independently per point; deterministic project-order with an
  opt-in reverse).
- Added **Decision 3a — "Preconditions that make loaded experiments a
  valid series"**: `show_supported()` is gated by experiment **count
  only** (predictable, explainable); the richer rules — measured data on
  every experiment, a shared structure model across the series, each
  experiment individually fittable (valid calculator + non-empty free
  set), stable order — are enforced at **fit time** with errors that
  name the offending experiment and rule. Experiment/calculator types
  may differ across points.

Affected sections: `## Decision` (3, 3a).
