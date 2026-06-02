# Review 4: Automatic Wyckoff Position Detection

## Findings

### [P1] Live descriptor edits can bypass re-detection

Sections 3 and 4 make "public coordinate setter" edits the trigger for
re-detecting an existing Wyckoff letter. In the current public API,
however, `atom.fract_x` returns the live `Parameter`, and assigning
`atom.fract_x.value = ...` is also a normal public edit path. That path
goes through `GenericDescriptorBase.value`, marks the owner dirty, and
does not call the `AtomSite.fract_x` property setter. If implementation
follows the ADR literally, `atom.fract_x = 0.1` would re-detect but
`atom.fract_x.value = 0.1` would leave a stale non-empty
`wyckoff_letter`, because the fill-if-empty update path is a no-op once
the letter is populated. The ADR should state that **all public
coordinate value edits**, including live descriptor `.value` assignment,
are user coordinate edits for this purpose, or choose an update-flow
change-tracking mechanism that covers both property assignment and
descriptor-value assignment while still excluding minimizer and symmetry
constraint writes.

### [P2] Unsupported groups contradict "always concrete" CIF writes

The revised decision says the `wyckoff_letter` descriptor holds a
concrete value at all times and that project CIF always emits the
resolved `_atom_site.Wyckoff_symbol` for every atom. Section 8 still
preserves the unsupported-space-group path: when the space group is
absent from `SPACE_GROUPS`, only the empty placeholder is allowed,
detection is a no-op, and the site keeps no letter. Those two rules
conflict. An implementation needs a defined behaviour for genuinely
unsupported groups and for any pre-update transient empty value: should
project CIF write `?`, omit the column, or fail with a clear error? The
ADR should qualify "always concrete" and the §9 write rule so this
boundary case is explicit rather than left to the serializer default.

## Checks skipped

Per `AGENTS.md` review-shortcut rules, this was a static ADR/source
review only. I did not run tests, `pixi run fix`, `pixi run check`, or
other verification commands.
