# Reply 13: Automatic Wyckoff Position Detection

## [P2] Unsupported-group stored letters are still described as explicit-only

Verdict: agree.

Action taken: the unsupported-group policy now consistently uses
"stored" non-empty letters rather than "explicit" letters only. §3 now
states that unsupported groups keep any stored non-empty letter,
including a letter preserved after a supported-to-unsupported
space-group change. §9 now writes any stored non-empty unsupported
letter verbatim and assigns it `None` multiplicity, and the CIF
round-trip test bullet covers explicit and preserved stored letters.

Affected sections: §3 "The letter is always set, and tracks the
coordinates", §9 "CIF behaviour", and "Testing".

## [P2] The trigger summary still says only coordinates re-detect

Verdict: agree.

Action taken: the closing paragraph of §4 now keeps the minimizer and
same-pass constraint-snap exclusions, but states that later coordinate
edits and later space-group / setting key edits can both re-detect.

Affected section: §4 "Detection triggers".
