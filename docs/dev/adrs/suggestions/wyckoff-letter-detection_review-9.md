# Review 9: Automatic Wyckoff Position Detection

## Findings

### [P2] No-record descriptors still imply an empty letter

Reply 8 correctly splits unsupported groups into empty/no-explicit and
non-empty/explicit-letter cases in §3 and §9. Section 6 still says the
empty `multiplicity` / `site_symmetry` descriptors "follow the letter's
empty state in lockstep." That is no longer true for an unsupported
group with an explicit Python/CIF letter: the stored letter is
non-empty, but there is still no `WyckoffPosition` record, so
multiplicity remains `None` and site symmetry remains empty. The Testing
section has the same minor drift in the CIF round-trip bullet, which
only says an unsupported-group row stays empty. Please rephrase these
spots so the derived descriptor state follows **record availability**,
not letter emptiness: no record means empty derived descriptors whether
the letter is empty or an unvalidated explicit value.

## Checks skipped

Per `AGENTS.md` review-shortcut rules, this was a static ADR/source
review only. I did not run tests, `pixi run fix`, `pixi run check`, or
other verification commands.
