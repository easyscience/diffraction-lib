# EasyDiffraction — Recommended Work (Prioritised Proposal)

**Date:** 2026-06-10

A curated, re-tiered recommendation of what to work on next, produced
from a whole-project analysis (ADRs, plans, `issues/open.md`,
`issues/closed.md`, roadmap, calculator backends, and the CI-skipped
verification pages).

This is a **priority view**, not a second tracker. [`open.md`](open.md)
remains the canonical issue list; the roadmap and ADRs remain
authoritative for features and decisions. Issue numbers below reference
`open.md` **after** the 2026-06-10 renumber that removed its duplicate
numbers.

## Meta-finding: triage has drifted

`open.md` currently labels **every** item 🟡 Medium or 🟢 Low — there
are **no 🔴 High** items — yet several genuine high-severity correctness
problems sit in the Medium tier or only in
`docs/docs/verification/ci_skip.txt`. The recommendation below re-tiers
by real impact (silent-wrong-results and crashes first). Consider
promoting the Tier 1 items to 🔴 in `open.md`.

---

## Tier 1 — Correctness / wrong science (do first)

1. **Joint-fit weight safety** — issues **3** (rebuild stale weights
   when experiments change) + **15** (validate weights before residual
   normalisation). Invalid or all-zero weights currently produce `nan` /
   division-by-zero straight into the minimiser. Crash + silent
   corruption; self-contained.
2. **Retain per-experiment fitted parameters for plotting** — issue
   **85**. In `single` mode only the last experiment's results survive,
   so earlier experiments plot incorrectly after fitting.
3. **TOF profile divergences** — issue **130** (cryspy TOF Jorgensen–Von
   Dreele Lorentzian, ~22% off) + issue **134** (crysfml TOF Jorgensen
   ~8.5% off). Both have CI-skipped verification pages.
4. **Sample absorption (Debye–Scherrer μR)** — issue **119**. Accounts
   for the entire intensity residual on the LaB₆ verification page;
   well-specified (Hewat formula). See the architecture note below.
5. **Serialise `None` as `.`/`?` in CIF** — issue **84**. Spec
   correctness and round-trip fidelity.

## Tier 2 — Tooling that prevents whole bug classes

6. **Add a static type checker to the gate** — issue **116**
   (mypy/pyright/ty). A real wrong-arity `TypeError` already shipped
   because nothing catches it. High leverage; land as its own
   baseline-cleanup effort.
7. **Explicit `create()` signatures on collections** — issue **8**.
   Typos in `create(**kwargs)` are silently dropped today.
8. **Pin the error-handling strategy** — issues **66** + **61**
   (`log.error` vs `raise`, and the logger default reaction mode).

## Tier 3 — User-visible roadmap features

9. **Plot Bragg peaks in the library** (roadmap 🗓`high`) and **basic
   preferred-orientation model via CrysPy** (roadmap 🗓`high`).
10. **Finish the BUMPS minimizer** (roadmap 🚧).
11. **Physical FCJ asymmetry model + rename `asym_empir_*`** — issue
    **133**. Unblocks further CI-skipped asymmetry pages.

## Tier 4 — Maintainability / housekeeping

- **Data `_update` refactor cluster** — issues **25** / **32** / **33**
  (decompose `_update`, lift duplicated collection methods to the base,
  make `_update_categories` abstract).
- **Bare `print()` → logging** — issue **65** (now only 3 real call
  sites).

---

## Pending design decisions (decide before/with implementation)

Four suggestion ADRs are still **Proposed**, plus one drafted this
session:

- **[`lazy-pattern-recalculation.md`](../adrs/suggestions/lazy-pattern-recalculation.md)**
  — highest-value/highest-risk: a missed dirty-flag setter yields
  silently stale refinement results.
- **[`cif-numeric-precision.md`](../adrs/suggestions/cif-numeric-precision.md)**
  — s.u.-aware CIF serialization (file size + meaningful precision).
- **[`fit-output-files-and-data-exports.md`](../adrs/suggestions/fit-output-files-and-data-exports.md)**.
- **[`documentation-ci-build.md`](../adrs/accepted/documentation-ci-build.md)**.
- **[`in-house-calculation-engine.md`](../adrs/suggestions/in-house-calculation-engine.md)**
  — drafted 2026-06-10 (in review): own the core (neutron powder
  Rietveld) in-repo, keep cryspy/crysfml/pdffit for the frontier.

## Architecture note — absorption correction (issue 119)

Both backends return only a finished, convolved profile to the
EasyDiffraction layer (`cryspy.calculate_pattern` →
`signal_plus + signal_minus`; `crysfml.calculate_pattern` →
`np.asarray(y)`), and neither exposes a CW absorption knob. So:

- An **in-project point-wise** `A(2θ)` correction is feasible now —
  multiply the summed structure profile by `A` in `bragg_pd.py` _before_
  adding the background (`_set_intensity_calc(calc + intensity_bkg)`),
  reusing the per-phase scale-factor precedent. Backend-agnostic, ~small
  change + a `μR` parameter (follows the `calib_sample_displacement`
  SyCos precedent).
- The **physically-exact per-reflection** `A(θ_hkl)`-before-convolution
  is **not** possible in our layer (both engines convolve internally);
  it requires owning the engine — which is exactly the
  in-house-calculation-engine ADR's motivation.

## Ready-to-execute / status corrections

- **β-tensor anisotropic ADP** — implementation is **in progress** as of
  2026-06-10. The plan
  [`adp-beta-tensor.md`](../plans/adp-beta-tensor.md) has entered Phase
  1 (reciprocal-cell helper and `AdpTypeEnum.BETA` committed; commit
  `678bd3c5` had earlier added only the ADR + plan).
- **Calculation without measured data** — shipped (#198).

## Housekeeping completed 2026-06-10

For the record, these were done in the session that produced this
proposal: removed `open.md` duplicate issue numbers (15–24, 93, 116–117,
119 → reassigned 120–134) and reconciled its Summary table; refreshed
the stale issue **65** bare-`print()` metadata; added issue **134** for
the previously-untracked `pd-neut-tof_j_si` page; and marked the
SyCos/SySin LIB roadmap cell 🚧 (code landed in #197, blocked on the
unreleased cryspy PR #46).
