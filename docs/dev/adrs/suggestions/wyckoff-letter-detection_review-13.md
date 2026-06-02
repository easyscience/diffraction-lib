# Review 13: Automatic Wyckoff Position Detection

## Findings

### [P2] Unsupported-group stored letters are still described as explicit-only

Reply 12 added the right policy for a space-group change into an
unsupported key: preserve any existing stored letter verbatim, even when
that letter was previously auto-detected, because there is no
auto/provided marker (`wyckoff-letter-detection.md` 193-204, 247-253).
Several later passages still describe the unsupported non-empty-letter
case as only an explicit Python/CIF input. Section 3's opening split says
"without an explicit letter" stays empty while an "explicit Python/CIF
letter" is stored (`wyckoff-letter-detection.md` 170-176). The CIF write
rules say any non-empty unsupported letter is written when it was
"supplied explicitly" and that "only the latter" carries `None`
multiplicity (`wyckoff-letter-detection.md` 412-419), which is now false
for a preserved auto-detected letter after a supported-to-unsupported
space-group edit. The CIF round-trip test bullet has the same explicit-
only framing (`wyckoff-letter-detection.md` 577-580).

Please reword those passages around **stored non-empty letters** rather
than **explicit letters**: unsupported groups with no stored letter stay
empty; unsupported groups with any stored letter, whether explicit or
preserved from a previous supported key, write it verbatim and carry
`None` multiplicity. That keeps §3, §4, §8, §9, and Testing aligned.

### [P2] The trigger summary still says only coordinates re-detect

The new space-group-key trigger is clear earlier in §3 and §4, but the
closing paragraph of §4 still says a user-set letter is "never silently
overwritten by an internal recompute" and that "only a real change in the
stored coordinates re-detects" (`wyckoff-letter-detection.md` 255-263).
That now contradicts the accepted Review-12 fix: a real change in the
stored `(name_hm, coord_code)` key also re-detects and may overwrite a
user-set letter for a supported new key.

Please update that paragraph so the excluded minimizer/same-pass-snap
paths remain clear while the final trigger summary includes both later
coordinate edits and later space-group-key edits.

## Checks skipped

Per `AGENTS.md` review-shortcut rules, this was a static ADR/source
review only. I did not run tests, `pixi run fix`, `pixi run check`, or
other verification commands.
