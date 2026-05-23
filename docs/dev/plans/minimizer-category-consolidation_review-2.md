# Review 2: Minimizer Category Consolidation Plan

Reviewed plan:
[`minimizer-category-consolidation.md`](minimizer-category-consolidation.md)

Reviewed reply:
[`minimizer-category-consolidation_reply-1.md`](minimizer-category-consolidation_reply-1.md)

This review follows
[`.github/copilot-instructions.md`](../../../.github/copilot-instructions.md).

## Findings

### P1: P1.12 cannot pass as written

P1.12 requires stale references to be empty under `src/`, `tests/`, and
`docs/docs/tutorials/` before moving on. However, tutorials are migrated
later in P1.13, and tests are migrated later in P2.1a.

This forces either failing P1.12 or doing test/tutorial work out of
sequence.

Recommended fix: scope P1.12 greps to `src/` only, move tutorial checks
after P1.13, and leave `tests/` checks to P2.1a.

### P1: Shared descriptor bases contradict the ADR/plan decision

The plan says concrete minimizer classes declare verbose descriptors in
the class body and "No mixins". It also adds `lsq_base.py` and
`bayesian_base.py` with shared descriptor declarations, then repeats
that in P1.4.

Recommended fix: either make those bases behavior-only, or explicitly
amend the ADR and plan decision to allow inherited descriptor
declarations.

### P2: The stale-reference regex misses singular CIF category tags

The P1.12 and P2.1a greps cover plural package names such as
`bayesian_distribution_caches`, but not CIF/category names such as:

- `_bayesian_distribution_cache`
- `_bayesian_pair_cache`
- `_bayesian_predictive_dataset`
- `_bayesian_parameter_posterior`

Current source uses those singular category codes, so the verification
can pass while stale CIF/category references remain.

Recommended fix: broaden the regex to include singular forms, or use a
simpler `git grep -n 'bayesian_'` in the scopes where no Bayesian
category references should remain.

### P2: The bare-tag alias decision is timed incorrectly

The plan says aliasing `lmfit` / `bumps` should be captured "at the P1
review gate before P1.4 lands", but the only review gate is P1.15, after
P1.4.

Recommended fix: add a pre-P1.4 decision gate, or remove that caveat and
commit to keeping all nine tags for this plan.

## Minor

The reply says the deterministic-result migration is **P1.11a**, but the
updated plan calls it **P1.10a**. Align the reply so future reviewers do
not chase the wrong step.

## Verification

No tests were run. This was a static review of the updated plan, the
reply, `.github/copilot-instructions.md`, and current source references.
