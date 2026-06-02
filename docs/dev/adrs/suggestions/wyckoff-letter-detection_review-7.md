# Review 7: Automatic Wyckoff Position Detection

## Findings

### [P2] Explicit letters for unsupported groups are undefined

Sections 3 and 9 say a user-set letter is applied as-is and a present
`_atom_site.Wyckoff_symbol` is loaded as the letter. Section 8 says that
when the space group is absent from `SPACE_GROUPS`, only the empty
placeholder is allowed, detection is a no-op, and the site keeps no
letter. Those rules conflict for boundary input the public API can
produce: a user can set `atom.wyckoff_letter = 'a'` after choosing an
unsupported group, or load a CIF that contains a Wyckoff symbol for a
group not present in the bundled table. The ADR should explicitly choose
the behaviour for this case — for example, reject the explicit letter
with a clear validation error, or allow the stored letter while leaving
`multiplicity` / `site_symmetry` empty and skipping calculator
multiplicity overrides. Without that decision, implementation can
accidentally make Python assignment, CIF loading, allowed-value
discovery, and derived descriptor handling disagree.

## Checks skipped

Per `AGENTS.md` review-shortcut rules, this was a static ADR/source
review only. I did not run tests, `pixi run fix`, `pixi run check`, or
other verification commands.
