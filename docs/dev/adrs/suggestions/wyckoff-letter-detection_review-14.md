# Review 14: Automatic Wyckoff Position Detection

## Findings

### [P2] Two unsupported-letter passages still say explicit-only

Review 13's main issue is mostly fixed, but two nearby passages still use
the old explicit-only framing. The no-record paragraph in §6 says a
non-empty no-record letter is a "non-empty unvalidated explicit value"
(`wyckoff-letter-detection.md` 301-313). After the Review-12/13 policy,
that value may also be a previously detected letter preserved when the
space-group key changed into an unsupported one. Section 8 similarly says
the unsupported path stores "an explicit letter" and "such a letter"
carries no multiplicity (`wyckoff-letter-detection.md` 383-393), while
the same no-record behavior also applies to preserved stored letters.

Please update those two passages to use the same "stored non-empty
letter" wording now used in §3 and §9. The implementation-facing rule
should be one rule everywhere: when no `WyckoffPosition` record is
available, multiplicity is `None` and constraints are skipped whether the
stored letter came from Python/CIF input or was preserved from a previous
supported key.

## Checks skipped

Per `AGENTS.md` review-shortcut rules, this was a static ADR/source
review only. I did not run tests, `pixi run fix`, `pixi run check`, or
other verification commands.
