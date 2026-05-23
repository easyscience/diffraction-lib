# Review 6: Minimizer Category Consolidation Plan

Reviewed plan:
[`minimizer-category-consolidation.md`](minimizer-category-consolidation.md)

Reviewed reply:
[`minimizer-category-consolidation_reply-5.md`](minimizer-category-consolidation_reply-5.md)

This review follows
[`.github/copilot-instructions.md`](../../../.github/copilot-instructions.md).

## Findings

### P1: `git grep -E` patterns use `\b`, which does not match here

Reply 5's specific fixes are present in the plan: P1.1a now has the
two-step `PosteriorParameterSummary` verification, P1.12 now includes
private `self._bayesian_*` fields, and the "Decisions added after Review
4" section exists.

However, the stale-reference checks now rely on `\b` word-boundary
tokens inside `git grep -nE` patterns:

- P1.12 source/category grep at line 485.
- P1.12 `analysis.py` internal-owner grep at line 501.
- P1.13 tutorial grep at line 538.
- P2.1a test grep at line 676.

In the current repo environment, `git grep -E '\banalysis\.fitting\...'`
does not match known current references. For example, it misses
`docs/docs/tutorials/ed-17.py:272`, while the same pattern without `\b`
or with `git grep -P` does match it.

That means these verification gates can return empty even when stale
`analysis.fitting.*`, `project.analysis.fitting.*`, `self.fitting`, or
`self._bayesian_*` references remain. The plan's main safety net for the
API/category removal is therefore unreliable as written.

Recommended fix: either switch these grep commands to `git grep -nP`
when using `\b`, or keep `git grep -nE` and express boundaries in
POSIX-compatible form, for example:

```text
(^|[^[:alnum:]_])analysis\.fitting\.(minimizer|show_minimizer_types|minimizer_type)([^[:alnum:]_]|$)
```

Apply the same treatment to every `\b...` pattern in P1.12, P1.13, and
P2.1a.

### P3: The file-change summary still omits two tutorial files

The detailed P1.13 tutorial step correctly lists `ed-8.py` and
`ed-20.py` because they currently call
`project.analysis.show_fitting_mode_types()`.

The "Concrete files likely to change" summary at lines 194-195 still
lists only the tutorials with `analysis.fitting.minimizer*` references:
`ed-2.py`, `ed-3.py`, `ed-4.py`, `ed-15.py`, `ed-17.py`, `ed-21.py`,
and `ed-22.py`.

This is not a design blocker because P1.13 has the correct detailed
list, but the summary is now stale and can mislead an implementer doing
the initial file sweep.

Recommended fix: add `ed-8.py` and `ed-20.py` to the concrete-files
summary, or reword that bullet so it explicitly says the remaining
show-method-only tutorial files are listed in P1.13.

## Verification

No tests were run. This was a static review of the updated plan, reply 5,
`.github/copilot-instructions.md`, and current grep behavior against
source, tests, and tutorials.
