# Reply 14: Automatic Wyckoff Position Detection

## [P2] Two unsupported-letter passages still say explicit-only

Verdict: agree.

Action taken: §6 now describes no-record multiplicity in terms of stored
non-empty letters, not explicit-only values. §8 now covers both explicit
Python/CIF input and letters preserved after a later change into an
unsupported space-group key; both become stored but unvalidated letters
with `None` multiplicity and no constraints.

Affected sections: §6 "Per-atom multiplicity, and a new
`space_group_Wyckoff` category" and §8 "Allowed letters come from the
current space group (closes #51)".
