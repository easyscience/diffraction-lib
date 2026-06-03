# Plan: Automatic Wyckoff Position Detection

This plan follows [`AGENTS.md`](../../../AGENTS.md) and implements the
[`wyckoff-letter-detection`](../adrs/accepted/wyckoff-letter-detection.md)
ADR. No deliberate exception to `AGENTS.md` is taken.

## Status

- [x] ADR review gate closed
- [x] Phase 1 — Implementation (code + docs)
- [x] Phase 1 review gate
- [ ] Phase 2 — Verification (tests + `pixi` checks)

## ADR

This plan implements the
[`wyckoff-letter-detection`](../adrs/accepted/wyckoff-letter-detection.md)
ADR. Earlier ADR review cycles closed at review 10 and then review 16
(adding the derived `space_group_Wyckoff` category and space-group-key
re-detection); that text was committed as `0f3bc269c`
(`Finalize Wyckoff letter detection ADR`). The ADR was then **extended
with §10 (canonical `coords_xyz` templates)** after the coupled
special-position regression was found in the `ed-6` tutorial. That §10
`draft-adr` cycle closed with the final-review sentinel in
`wyckoff-letter-detection_review-2.md`; its §10 text was committed as
`9882c50cb`, with a small Testing/Compatibility follow-up still in the
worktree at planning time. The ADR `_review-*` / `_reply-*` siblings are
transient and are removed by `/draft-impl-1` Phase A before the
checklist runs, so P1.0 verifies durable signals (§10 present and
committed, and the §10 prerequisite landed) rather than a specific
review file.

Its prerequisite — the
[`space-group-database`](../adrs/accepted/space-group-database.md) ADR
(the complete, self-owned 230-group `SPACE_GROUPS` table) — is already
accepted and merged (PR #187), and its ADR promotion is already
committed on this branch (`c84183662`). No new dependency is introduced:
detection reuses `SPACE_GROUPS`, NumPy, and the existing
rotation/translation parser.

## Branch and PR

- Target implementation branch: `wyckoff-letter-detection` (off
  `develop`; already exists and already carries the space-group ADR
  promotion commit `c84183662`).
- Implementation shortcuts must stay on the current branch. Before
  `/draft-impl-1` starts code work, verify `git branch --show-current`
  is `wyckoff-letter-detection`. If it is not, stop before editing and
  ask the user to switch to the target branch outside the shortcut. This
  planning session is currently on `plotting-docs-performance`, so
  implementation must not start from the current branch.
- PR targets `develop` (not `master`). Scope label:
  `[scope] enhancement` (adds a user-facing feature and closes #51).
- Do not push the branch until the user asks.

## Decisions

1. **EasyDiffraction owns the Wyckoff position.** The model owns the
   atom-site Wyckoff letter and multiplicity, plus the per-space-group
   site-symmetry table. Calculators consume these model values and never
   re-derive them.
2. **Detection lives in `crystallography.py`.** Add
   `detect_wyckoff_position(name_hm, coord_code, fract_xyz, tol=...)`
   and
   `wyckoff_position_info(name_hm, coord_code, letter, fract_xyz=None, tol=...)`,
   returning a frozen
   `WyckoffPosition(letter, multiplicity, site_symmetry, coord_template)`.
   When coordinates are supplied, `coord_template` is the nearest
   representative in the matched orbit and drives snapping/constraints.
3. **Orbit test.** Test `R·v + b ≡ p (mod 1)` with NumPy least-squares;
   choose by `(multiplicity ascending, residual ascending)`;
   same-multiplicity ties within `tol` log a warning.
4. **Coordinate-code normalisation.** A shared `_normalize_coord_code()`
   maps the empty string `''` to `None` and is used by detection,
   allowed letter discovery, `_get_wyckoff_exprs()`, and
   `_get_general_position_ops()`.
5. **The atom-site letter is concrete for supported groups.** Missing
   letters are filled on create/load, coordinate edits re-detect with a
   warning when the letter changes, space-group / setting edits
   re-detect all sites for supported new keys, and user letter edits
   persist until a later coordinate edit or space-group-key edit.
6. **Detection triggers live in the atom-site update flow.** The flow
   tracks both the coordinate baseline and the `(name_hm, coord_code)`
   key used for each atom site's last Wyckoff derivation. Fill-if-empty,
   later coordinate edits, and later supported space-group / setting
   edits all derive from this one update path; unsupported key changes
   preserve stored letters as unvalidated values. The currently unused
   `called_by_minimizer` flag at `default.py:674` is honoured so
   minimizer-driven updates skip re-detection.
7. **`AtomSite` gains only read-only `multiplicity`.** It carries the
   `_atom_site.site_symmetry_multiplicity` CIF tag, has empty form
   `None`, and tracks record availability rather than letter emptiness.
   `site_symmetry` is **not** an `AtomSite` descriptor.
8. **`space_group_Wyckoff` owns site symmetry.** Add a derived,
   read-only structure sibling category exposed as
   `structure.space_group_wyckoff` with CIF category code
   `space_group_Wyckoff`. It lists every Wyckoff position for the
   current space group with `id` (e.g. `6e`), `letter`, `multiplicity`,
   `site_symmetry`, and representative `coords_xyz`.
9. **`space_group_Wyckoff` identity and mutability.** The collection key
   is `id`, serialized as `_space_group_Wyckoff.id`, because the letter
   alone is not the CIF category key and `id` keeps the row identity
   stable. Public mutation paths (`add`, `create`, `remove`,
   `__setitem__`, `__delitem__`) raise `ValueError`, while a private
   `_replace_from_space_group()` path rebuilds the derived collection
   through internal adoption.
10. **`space_group_Wyckoff` serialization policy.** The category is
    model-owned and report-facing, but not persisted in project CIF.
    `Structure._serializable_categories()` excludes it from
    `structure.as_cif` / project saves, the IUCr/report writer emits the
    `_space_group_Wyckoff.*` loop from the derived category, and
    incoming `_space_group_Wyckoff.*` values are ignored/overwritten on
    project load because the category is re-derived from the space
    group.
11. **Allowed letters come from the current space group.**
    `_wyckoff_letter_allowed_values` returns `['', *tabulated_letters]`
    for supported groups and `[]` for absent groups.
12. **Unsupported-group validation is explicit.** The stock
    `MembershipValidator` falls back on mismatch, so `_wyckoff_letter`
    uses a dedicated permissive-when-empty validator: an empty allowed
    set accepts explicit user/CIF letters verbatim, and the update flow
    preserves any stored non-empty letter when a later space-group
    change moves the site into an unsupported key. Those stored letters
    are unvalidated, carry `None` multiplicity, skip constraints, and
    warn; a non-empty allowed set enforces membership. A temporary
    no-parent context during
    `atom_sites.create(..., wyckoff_letter=...)` is not treated as
    unsupported: the raw letter is marked as requiring context
    validation and is checked against the parent structure's space group
    on the first parented update.
13. **CIF atom-site behaviour.** Project CIF writes
    `_atom_site.Wyckoff_symbol` and
    `_atom_site.site_symmetry_multiplicity` for every atom (`?` for
    `None` multiplicity). Read loads the letter but ignores incoming
    `site_symmetry_multiplicity` by re-populating multiplicity from the
    resolved Wyckoff record during update. Unsupported groups write any
    stored non-empty letter verbatim with `?` multiplicity.
14. **Tolerance.** `_WYCKOFF_DETECTION_TOL = 1e-3` is the default; a
    user/project-level tolerance setting remains deferred.
15. **Canonical Wyckoff templates are a prerequisite (ADR §10), owned by
    the space-group database.** The orbit matcher (Decisions 2–3),
    snapping (Decision 5), and the existing coordinate constraints
    assume `coords_xyz` in canonical ITA parametric form (`(x,-x,z)`),
    but the bundled `space_groups.json.gz` ships cctbx operator-form
    templates (`(1/2*x-1/2*y,…)`) for 288 coupled special positions
    across 117 IT numbers. That spelling silently breaks
    `_fract_constrained_flags()` / `_apply_fract_constraints()`, so a
    refined special-position coordinate drifts off-site (the `ed-6`
    fit-3 → fit-4 regression). **Decision: fix this as a standalone
    prerequisite** against the
    [`space-group-database`](../adrs/accepted/space-group-database.md)
    ADR, not inside this feature. The generator
    (`tmp/space-groups/helper-tools/generate_space_groups.py`, cctbx-
    dependent and not in this repo's environment) and the bundled
    `space_groups.json.gz` are that ADR's artifacts, and the live
    refinement regression should ship on its own small PR rather than
    wait for this feature. That fix re-parametrises every operator-form
    template to canonical form (deterministic; verified for all 288),
    adds a generation-time invariant check (and a
    `tools/check_packaged_db.py` assertion) rejecting operator-form
    leakage, and adds a coupled- position constraint regression. This
    plan **depends on** that fix, **verifies it at P1.0**, and does not
    modify the database generator itself.

## Open questions

- **Tolerance default.** `1e-3` is the ADR's starting point; it may be
  tuned against the tutorial corpus during Phase 2. Not a blocker.

## Concrete files likely to change

Phase 1 (implementation):

- `src/easydiffraction/crystallography/crystallography.py` — detection,
  `WyckoffPosition` including the selected `coord_template`,
  `_WYCKOFF_DETECTION_TOL`, `_normalize_coord_code`, and normalisation
  adopted by `_get_wyckoff_exprs` / `_get_general_position_ops`; reuse
  `_parse_rotation_matrix`.
- `src/easydiffraction/crystallography/__init__.py` — export the new
  public names if they are part of the public surface.
- `src/easydiffraction/datablocks/structure/categories/atom_sites/default.py`
  — read-only `multiplicity`, `_set_wyckoff_letter_detected`, dynamic
  `_wyckoff_letter_allowed_values`, permissive unsupported-group
  validator wiring, pending parent-context validation for
  `create(wyckoff_letter=...)`, coordinate and space-group-key
  baselines, update-flow detection triggers, and nearest-template
  coordinate snapping. Do **not** add `site_symmetry` to `AtomSite`.
- `src/easydiffraction/datablocks/structure/categories/space_group_wyckoff/default.py`
  — new `SpaceGroupWyckoff` item and read-only
  `SpaceGroupWyckoffCollection` with `id`, `letter`, `multiplicity`,
  `site_symmetry`, and `coords_xyz` descriptors plus private rebuild.
- `src/easydiffraction/datablocks/structure/categories/space_group_wyckoff/factory.py`
  and
  `src/easydiffraction/datablocks/structure/categories/space_group_wyckoff/__init__.py`
  — register/import the new concrete collection.
- `src/easydiffraction/datablocks/structure/item/base.py` — add the
  `space_group_wyckoff` sibling category, expose it read-only, rebuild
  it from the current `space_group` before ordinary category update
  hooks, and exclude it from project CIF through
  `_serializable_categories()`.
- `src/easydiffraction/analysis/calculators/cryspy.py` —
  `_update_atom_multiplicity` reads `atom_site.multiplicity.value`.
- `src/easydiffraction/io/cif/serialize.py` — only if atom-site CIF read
  needs an explicit post-load hook to ignore incoming
  `_atom_site.site_symmetry_multiplicity`; avoid changing the ADP loop
  path solely to omit `site_symmetry`.
- `src/easydiffraction/io/cif/iucr_writer.py` — emit
  `_atom_site.site_symmetry_multiplicity` and the report-only
  `_space_group_Wyckoff.*` loop.
- `docs/dev/issues/open.md` → `docs/dev/issues/closed.md` — move #51 and
  remove the resolved TODOs at `default.py` ~200–211, ~225, ~569.
- `docs/dev/adrs/suggestions/wyckoff-letter-detection.md` →
  `docs/dev/adrs/accepted/wyckoff-letter-detection.md` and
  `docs/dev/adrs/index.md` — ADR promotion after the ADR review cycle
  closes.

Phase 2 (tests):

- `tests/unit/easydiffraction/crystallography/test_crystallography_wyckoff.py`
  (+ `_coverage.py` if needed) — matcher edge cases.
- `tests/unit/easydiffraction/datablocks/structure/categories/test_atom_sites.py`
  — atom-site descriptor/update-flow behaviours.
- `tests/unit/easydiffraction/datablocks/structure/categories/test_space_group_wyckoff.py`
  — derived category rows, read-only mutation paths, rebuild on space
  group change, absent-group emptiness, and project-CIF exclusion.
- A tutorial-corpus regression check (functional/script level) that
  strips each declared letter and asserts re-detection reproduces it.
- `tests/unit/easydiffraction/crystallography/test_space_groups.py` (or
  `_coverage.py`) — the §10 canonical-template data invariant (no
  operator-form `coords_xyz`).

**Prerequisite, out of scope for this plan (Decision 15).** The
canonical-table regeneration itself —
`tmp/space-groups/helper-tools/generate_space_groups.py`,
`src/easydiffraction/crystallography/space_groups.json.gz`,
`tools/check_packaged_db.py`, and
[`space-group-database.md`](../adrs/accepted/space-group-database.md) —
lands as a standalone space-group-database fix. This plan only
**verifies** it (P1.0) and guards it from the consuming side (the Phase
2 invariant test).

## Implementation steps (Phase 1)

Code and docs only — **no tests in Phase 1** (they belong to Phase 2).
When an AI agent executes this plan, **every completed step below must
be staged with explicit paths (`git add <path> …`) and committed locally
before moving to the next step or the Phase 1 review gate**, per
`AGENTS.md` §Commits. Keep each commit atomic and aligned with its step.
The ADR commit + design-phase review/reply cleanup are handled by
`/draft-impl-1` Phase A before P1.1.

- [x] **P1.0 — Verify the ADR gate and the §10 prerequisite.** No code.
      Ensure `git branch --show-current` is `wyckoff-letter-detection`;
      if not, stop before editing and ask the user to switch to the
      target branch outside the shortcut. Confirm the ADR on disk
      includes §10 (the canonical-`coords_xyz` decision) and that its
      most recent `draft-adr` cycle closed with a final-review sentinel.
      **Gate on the §10 prerequisite (Decision 15):** confirm the
      standalone canonical-table fix has landed by asserting no bundled
      `SPACE_GROUPS` `coords_xyz` template is in operator form — every
      component is canonical parametric, with no component containing
      its own axis variable in a coupled term, so R-3m `h` reads
      `(x,-x,z)`, not `(1/2*x-1/2*y,…)`. If any operator-form template
      remains, **stop**: the space-group-database prerequisite must land
      before this plan's detection and snapping can be implemented.
      Commit: `Confirm wyckoff letter detection ADR gate`
- [x] **P1.1 — Orbit matcher in the crystallography submodule.** Add to
      `crystallography.py`: frozen
      `WyckoffPosition(letter, multiplicity, site_symmetry, coord_template)`,
      `_WYCKOFF_DETECTION_TOL = 1e-3`, `_normalize_coord_code()`,
      `detect_wyckoff_position(...)`, and `wyckoff_position_info(...)`.
      Match all representatives in an orbit, choose by lowest
      multiplicity then nearest residual, and return the selected
      representative template for snapping. Make `_get_wyckoff_exprs`
      and `_get_general_position_ops` use `_normalize_coord_code`.
      Export new public names via `crystallography/__init__.py` if
      public. Commit:
      `Add Wyckoff orbit detection to crystallography module`
- [x] **P1.2 — Derived `space_group_wyckoff` category.** Add the
      `space_group_wyckoff` package with a `SpaceGroupWyckoff` item
      keyed by `id` (`_space_group_Wyckoff.id`) and read-only
      descriptors for `id`, `letter`, `multiplicity`, `site_symmetry`,
      and `coords_xyz`. Add `SpaceGroupWyckoffCollection` with public
      mutation methods raising and a private `_replace_from_space_group`
      rebuild method that creates/adopts rows from `SPACE_GROUPS[key]`.
      Commit: `Add derived space group Wyckoff category`
- [x] **P1.3 — Wire `space_group_wyckoff` into `Structure`.** Add it as
      a read-only sibling category on `Structure`, rebuild it when
      structure categories update so it tracks the current space group,
      keep it empty for absent groups, and exclude it from project CIF
      by overriding `_serializable_categories()`. Rebuild it from
      `Structure._update_categories()` before ordinary category update
      hooks, with no special `_update_priority`; atom-site detection
      reads `SPACE_GROUPS` through the crystallography helpers rather
      than depending on this collection. Commit:
      `Wire derived Wyckoff table into Structure`
- [x] **P1.4 — Read-only multiplicity + detection mutator on
      `AtomSite`.** Add only `multiplicity` as a read-only derived
      descriptor on `AtomSite` with `CifHandler` for
      `_atom_site.site_symmetry_multiplicity`, empty form `None`, and no
      public setter. Add `_set_wyckoff_letter_detected()` modelled on
      `_set_value_from_minimizer`. Do not add `site_symmetry` to
      `AtomSite`. Commit: `Add read-only multiplicity to AtomSite`
- [x] **P1.5 — Dynamic allowed letters + unsupported-group validation.**
      Make `_wyckoff_letter_allowed_values` return
      `['', *list(SPACE_GROUPS[key]['Wyckoff_positions'])]` for a
      supported group and `[]` for an absent one. Add the
      permissive-when-empty Wyckoff-letter validator so explicit
      unsupported-group letters are stored verbatim, and so later
      supported-to-unsupported transitions can preserve stored non-empty
      letters as unvalidated values with a warning. When a public
      `atom_sites.create(..., wyckoff_letter=...)` call sets the letter
      before parent context exists, store the raw value with a private
      "needs context validation" marker instead of treating missing
      context as an unsupported group. Commit:
      `Derive allowed Wyckoff letters from the space group`
- [x] **P1.6 — Detection triggers in the atom-site update flow.** In
      `_update(*, called_by_minimizer=False)`, implement fill-if-empty,
      re-detect-on-coordinate-change, and re-detect-on-space-group-key
      change with per-atom coordinate and `(name_hm, coord_code)`
      baselines. First resolve any pending no-parent-context
      `wyckoff_letter` value: for a supported key, validate it against
      the parent structure's allowed letters and raise `ValueError` if
      it is invalid; for an unsupported key, keep it as an unvalidated
      stored letter. For supported keys, refresh letter, multiplicity,
      and selected representative; for unsupported keys, preserve stored
      letters as unvalidated values, set multiplicity to `None`, skip
      constraints, and warn. Snap by **solving the free parameters** —
      least-squares project the coordinate onto the selected
      `coord_template`'s manifold, then set every axis to that manifold
      point — so centering copies and off-canonical-slot representatives
      (e.g. 6e `(0,x,0)`) snap correctly; derive constrained-axis flags
      from the same representative. This free-parameter-solving snap
      **replaces the positional `_apply_fract_constraints` substitution**
      (a deliberate deviation from ADR §5's "existing constraint step",
      decided during P1.1; reflect it in ADR §5 at the P1.9 promotion).
      Warn when coordinate or
      supported space-group edits move the letter, when a user
      letter-set snaps coordinates, and when a same-letter coordinate
      edit snaps coordinates. Honour `called_by_minimizer=True`;
      populate `multiplicity` from `wyckoff_position_info`.
      Site-symmetry display data comes from
      `structure.space_group_wyckoff`, not from `AtomSite`. Commit:
      `Detect and track Wyckoff letters in the update flow`

  _P1.6 implementation decisions (implemented):_

  - **Snap = slot-aware free-parameter-solving**
    (`crystallography.snap_to_wyckoff_template`, already committed): solve
    the free params from the **free (refinable) axes**, keep those axes,
    and derive the constrained axes. **Not** manifold projection — that
    averaged/moved the free axis and fought the minimizer. Handles
    off-canonical reps like 6e `(0,x,0)` (keep `fract_y`, set
    `fract_x=fract_z=0`); matches the old substitution for canonical
    sites, so the fit is unaffected. Per-axis constraint flags are
    slot-based (first-occurrence), not symbol-based.
  - **Warning gating (per the chosen option):** pass
    `called_by_minimizer=True` **only at the per-iteration minimizer
    objective** — `analysis/fit_helpers/metrics.py:181` (residual calc;
    verify `analysis/fitting.py:382` too) — and **leave** the fit-setup
    (`fitting.py:209`) and flush (`analysis.py:174`) sites `False` so
    detection still runs there. Gate re-detection **and** the
    "adjusted"/"moved-letter" warnings on `not called_by_minimizer`, so
    they never fire per fit step.
  - **Remaining:** rewrite `_apply_atomic_coordinates_symmetry_constraints`
    (per atom: resolve the `_wyckoff_letter_needs_validation` marker →
    decide detect/trigger → snap → set `multiplicity` + constrained flags
    → refresh baselines), thread `called_by_minimizer` through
    `AtomSites._update`, change the objective call site(s), then **verify
    by running `test_fit_neutron_pd_cwl_hs`** and smoke tests.
- [x] **P1.7 — Calculator consumes model multiplicity.** Replace the
      `SPACE_GROUPS` lookup in `cryspy._update_atom_multiplicity` with
      `atom_site.multiplicity.value`; when it is `None`, leave the
      backend's inferred multiplicity in place. Commit:
      `Read multiplicity from the model in the cryspy calculator`
- [x] **P1.8 — CIF and report output.** Ensure project CIF writes
      `_atom_site.Wyckoff_symbol` and
      `_atom_site.site_symmetry_multiplicity` but excludes the derived
      `space_group_Wyckoff` loop. Ensure read ignores incoming
      `_atom_site.site_symmetry_multiplicity` by re-deriving
      multiplicity during update, and ignores/overwrites incoming
      `_space_group_Wyckoff.*` values because the category is derived
      from the space group. Extend IUCr/report output with
      `_atom_site.site_symmetry_multiplicity` and the report-only
      `_space_group_Wyckoff.{id,letter,multiplicity,site_symmetry,coords_xyz}`
      loop. Commit:
      `Serialize Wyckoff multiplicity and report Wyckoff table`

      _P1.8 implementation decisions (implemented):_
      - **Project-CIF write of `_atom_site.site_symmetry_multiplicity`**
        is already automatic: P1.4 added the `multiplicity` descriptor
        with that CIF handler, and it is part of `AtomSite.parameters`,
        so the atom-site loop emits it (value `?` for untabulated
        sites). The `_space_group_Wyckoff` loop exclusion is already
        provided by P1.3's `Structure._serializable_categories`
        override. No new write-side code was needed in P1.8.
      - **Read ignore of incoming `_space_group_Wyckoff.*`** is done by
        a no-op `SpaceGroupWyckoffCollection.from_cif` override (the
        structure read loop iterates *all* categories, including the
        derived one). A hand-edited `_space_group_Wyckoff` loop is
        discarded; the table is rebuilt from the space group on update.
      - **Read ignore of incoming `_atom_site.site_symmetry_multiplicity`**
        relies on re-derivation: the value is parsed into the
        descriptor but overwritten by detection on the next
        `_update_categories` (verified: file value `777` → re-derived
        `1`). No extra read-side code.
      - **Report `_space_group_Wyckoff.coords_xyz` = representative
        coordinate only** (first orbit member, e.g. `(x,x,z)`), not the
        full orbit. The collection stores the full centred orbit (up to
        ~3551 chars for multiplicity-192 cubic positions), but the IUCr
        report loop formatter rejects loop cells > 80 chars. Emitting
        the representative keeps every space group's report valid and
        matches the conventional ITA "Coordinates" entry. Decision
        confirmed with the user during P1.8. The full orbit remains
        available on the in-memory `space_group_wyckoff` category.
- [x] **P1.9 — Promote ADR, close #51, remove stale TODOs.** `git mv`
      `wyckoff-letter-detection.md` from `suggestions/` to `accepted/`,
      set `**Status:** Accepted`, flip its `docs/dev/adrs/index.md` row
      to `Accepted`, and fix links with `git grep -n`. Move issue #51
      from `open.md` to `closed.md` and delete the resolved TODOs in
      `default.py` (~200–211, ~225, ~569). Commit:
      `Promote wyckoff-letter-detection ADR and close issue #51`

      _P1.9 notes (implemented):_
      - ADR moved with `git mv` to `accepted/`, `**Status:** Accepted`,
        `index.md` row flipped to `Accepted` with the `accepted/` link.
      - Inbound links to the old `suggestions/` path fixed in
        `accepted/space-group-database.md` (5) and
        `plans/space-group-database.md` (2), plus this plan's own ADR
        cross-references. The ADR's `../../../../` root paths are
        depth-invariant and its `../accepted/` sibling links still
        resolve, so they were left unchanged (minimal diff).
      - #51 moved from `open.md` (detailed section + summary-table row)
        to `closed.md`.
      - The `default.py` TODOs #51 referenced (old lines ~163/179/353,
        about the hardcoded allowed-letter list and the missing-letter
        case) were **already removed** when P1.5/P1.6 rewrote those
        methods to resolve #51, so there is no `default.py` change in
        this step. The only remaining TODO (label-regex/dict-key, line
        ~68) is unrelated to #51 and was intentionally left.
- [x] **P1.10 — Phase 1 review gate.** No code. Mark this `[x]`, commit
      the checklist update alone, then stop for the Phase 1 review.
      Commit: `Reach Phase 1 review gate`

## Phase 2 — Verification

Add/update tests (per the ADR _Testing_ section), then run the checks.
Stop after Phase 1 for review before starting Phase 2.

Tests to add or update:

- **Tutorial-corpus regression** (functional/script level): for each
  `docs/docs/tutorials/*.py` structure with a declared letter, strip it
  and assert `detect_wyckoff_position` reproduces the declared letter.
- **Targeted crystallography unit tests** in
  `tests/unit/easydiffraction/crystallography/test_crystallography_wyckoff.py`:
  general vs special positions and the `(multiplicity, residual)`
  tie-break; non-first orbit representatives, including auto-detection
  and explicit-letter lookup selecting the nearest representative rather
  than `coords_xyz[0]`; rounded inputs (`0.3333→1/3`, `0.4999→1/2`) at
  `1e-3`; `''`→`None` normalisation; genuinely absent group returns no
  record; and the **§10 coupled-position guard** — a coupled special
  position (R-3m `h`, `(x,-x,z)`) flags `fract_y` symmetry-constrained
  and re-slaves it to `-fract_x` after a `fract_x` edit (the `ed-6`
  regression). This unit-level guard complements the prerequisite fix in
  the space-group-database (Decision 15); the existing constraint tests
  covered only all-fixed and all-free sites, which never exercised the
  coupled case.
- **Canonical-template data invariant (§10)** in
  `tests/unit/easydiffraction/crystallography/test_space_groups.py` (or
  its `_coverage.py`): assert every `SPACE_GROUPS` `coords_xyz` template
  is canonical parametric form — no component contains its own axis
  variable in a coupled term (operator-form leakage) — so a future table
  regeneration cannot silently reintroduce the bug. This is the same
  invariant P1.0 gates on, asserted from the test side.
- **Atom-site behaviours** in
  `tests/unit/easydiffraction/datablocks/structure/categories/test_atom_sites.py`:
  fill-if-empty on create/load; re-detect via both `atom.fract_x = …`
  and `atom.fract_x.value = …` with the warning; user letter override
  with the snap warning; `atom_sites.create(..., wyckoff_letter=...)`
  validating against the parent structure once context exists;
  same-letter coordinate edits whose snap moves stored coordinates;
  supported space-group / setting edits re-detecting all atom sites;
  unsupported space-group transitions preserving stored non-empty
  letters as unvalidated values with `None` multiplicity; minimizer
  leaves the letter fixed; no-record contract (`None` multiplicity, `?`
  in CIF, calculator skip); CIF round-trip stability.
- **`space_group_wyckoff` behaviours** in
  `tests/unit/easydiffraction/datablocks/structure/categories/test_space_group_wyckoff.py`:
  auto-populates from `SPACE_GROUPS`, uses `id` keys, preserves
  site-symmetry dots verbatim, rebuilds when the space group changes,
  refuses all public mutation paths, stays empty for absent groups, is
  omitted from project CIF, and appears in report/IUCr output if that
  output is generated.

Verification commands (capture logs with the zsh-safe pattern when
output is needed for analysis):

```
pixi run fix
pixi run test-structure-check > /tmp/easydiffraction-test-structure.log 2>&1; test_structure_exit_code=$?; tail -n 50 /tmp/easydiffraction-test-structure.log; exit $test_structure_exit_code
pixi run check > /tmp/easydiffraction-check.log 2>&1; check_exit_code=$?; tail -n 200 /tmp/easydiffraction-check.log; exit $check_exit_code
pixi run unit-tests > /tmp/easydiffraction-unit.log 2>&1; unit_tests_exit_code=$?; tail -n 100 /tmp/easydiffraction-unit.log; exit $unit_tests_exit_code
pixi run integration-tests > /tmp/easydiffraction-integration.log 2>&1; integration_exit_code=$?; tail -n 100 /tmp/easydiffraction-integration.log; exit $integration_exit_code
pixi run script-tests > /tmp/easydiffraction-script.log 2>&1; script_tests_exit_code=$?; tail -n 100 /tmp/easydiffraction-script.log; exit $script_tests_exit_code
```

`pixi run fix` regenerates `docs/dev/package-structure/{full,short}.md`
automatically — include those in the fix commit; never edit by hand.
`pixi run check` already runs `test-structure-check` among its
pre-commit hooks; the standalone line above gives an early, focused
signal that the new unit tests mirror the source tree (`AGENTS.md`
§Testing, review-2 [P2]).

## Suggested Pull Request

**Title:** Detect Wyckoff positions automatically from coordinates

**Description:** When you build or load a crystal structure,
EasyDiffraction can work out each atom site's Wyckoff letter and
multiplicity from its coordinates and the space group. The full
space-group Wyckoff table is also available as a read-only derived
category, including site-symmetry symbols with their International
Tables notation. Existing projects and CIF files keep their supplied
letters, unsupported groups can still preserve stored letters safely,
and the same multiplicity is used consistently across calculators and
reports.

**Scope note (per Decision 15).** The special-position constraint
correction for coupled sites (the `ed-6` regression, where a refined
atom at a site like `(x, -x, z)` drifted off its symmetry position) is
**not** part of this PR. It ships first as a standalone
space-group-database correction, and this feature builds on it; that
user-facing benefit belongs in the prerequisite's PR description, not
here.
