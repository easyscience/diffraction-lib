# Plan: Rename empirical asymmetry to Bérar–Baldinozzi (`asym_beba_*`)

Follows [`AGENTS.md`](../../../AGENTS.md). No deliberate exceptions to
those instructions.

## ADR

No new ADR is required. This renames parameters and identifiers within
the **existing** switchable `peak` profile category (one peak-profile
type); it does not change the switchable-category mechanism, the
factory contract, or persistence design. Touches but does not alter the
decisions in
[`switchable-category-owned-selectors`](../adrs/accepted/switchable-category-owned-selectors.md)
and [`edstar-project-persistence`](../adrs/accepted/edstar-project-persistence.md)
(the persistence handler inventory lists the renamed tags and must be
kept in sync).

## Why

The four `asym_empir_1…4` parameters are the **Bérar–Baldinozzi (1993)**
empirical asymmetry correction. The generic `empir` tag hides the model
and the meaningless `_1…_4` suffixes hide each coefficient's role. This
plan renames them to a model-named, coefficient-named scheme consistent
with the sibling `asym_fcj_*` set, and adds a short, neutral note to the
affected Verification pages about the cryspy/FullProf implementation
difference. Implements the **rename half** of issue 133 and surfaces the
finding documented in issue 166 (issue 133 stays open for the separate
"add the physical FCJ model" item).

## Branch + PR

- Branch: `rename-asym-empir-to-beba` (flat slug off `develop`).
- PR targets `develop`, not `master`. Do not push unless asked.

## Naming scheme

`asym_empir` → `asym_beba` (BÉrar–BAldinozzi), with the numeric suffixes
replaced by the paper's coefficient names. Confirmed mapping (cryspy
`asymmetry_parameters[0..3]` and the CIF maps in both calculators):

| current | new | paper coeff | basis term | FullProf | cryspy slot |
| --- | --- | --- | --- | --- | --- |
| `asym_empir_1` | `asym_beba_a0` | `A₀` | `Fa / tan θ` | `Asy1`/`P1` | `[0]` |
| `asym_empir_2` | `asym_beba_b0` | `B₀` | `Fb / tan θ` | `Asy2`/`P2` | `[1]` |
| `asym_empir_3` | `asym_beba_a1` | `A₁` | `Fa / tan 2θ` | `Asy3`/`P3` | `[2]` |
| `asym_empir_4` | `asym_beba_b1` | `B₁` | `Fb / tan 2θ` | `Asy4`/`P4` | `[3]` |

Companion identifiers (parallel to the `Fcj…` set):

| kind | current | new |
| --- | --- | --- |
| mixin | `EmpiricalAsymmetryMixin` | `BerarBaldinozziAsymmetryMixin` |
| peak class | `CwlPseudoVoigtEmpiricalAsymmetry` | `CwlPseudoVoigtBerarBaldinozziAsymmetry` |
| enum member | `CWL_PSEUDO_VOIGT_EMPIRICAL_ASYMMETRY` | `CWL_PSEUDO_VOIGT_BERAR_BALDINOZZI_ASYMMETRY` |
| enum value | `cwl-pseudo-voigt-empirical-asymmetry` | `cwl-pseudo-voigt-berar-baldinozzi-asymmetry` |
| user type string | `pseudo-voigt + empirical asymmetry` | `pseudo-voigt + berar-baldinozzi asymmetry` |
| edi tag | `_peak.asym_empir_N` | `_peak.asym_beba_{a0,b0,a1,b1}` |
| CIF tag | `_easydiffraction_peak.asym_empir_N` | `_easydiffraction_peak.asym_beba_{a0,b0,a1,b1}` |

Each `Parameter` gains a `DisplayHandler` (matching the `broad_*` style):
display names `A₀, B₀, A₁, B₁`, LaTeX `$A_0$, $B_0$, $A_1$, $B_1$`, and
a description that states the model and term, e.g. *"Bérar–Baldinozzi
asymmetry coefficient B₀ (Fb/tan θ term)"*.

## Neutral mismatch note (verbatim text to add to Verification pages)

Phrased to **not** assign correctness to either program:

> **Note — cryspy vs FullProf.** cryspy and FullProf implement the
> Bérar–Baldinozzi empirical asymmetry with different conventions. As a 
> result the four `asym_beba_*` parameters do **not** transfer 
> one-to-one between cryspy and FullProf — the same numbers give
> different profiles. The refinement below frees the asymmetry so it can
> absorb this convention difference; the structural results are
> unaffected. See development issue 166 for the detailed comparison.

## Decisions

- Use `beba` (not `bb` or full `berar_baldinozzi`): matches the short
  model-tag style of `fcj`, while the coefficient suffixes (`a0`, `b0`,
  `a1`, `b1`) carry the physical meaning; full "Bérar–Baldinozzi" lives
  in every `description`/docstring for discoverability.
- Beta software, **no legacy shims** (AGENTS.md): old CIF/edi tags and
  the old type string are removed, not aliased. Saved projects using the
  old tags will not round-trip; this is acceptable for beta.
- The Verification note assigns no correctness verdict (per request); the
  detailed who-matches-the-paper analysis stays in issue 166 only.
- Rename the dedicated empirical page file
  `pd-neut-cwl_pv-asym_empir_pbso4` → `pd-neut-cwl_pv-beba_pbso4`
  (keeps the page slug consistent with the new parameter tag).

## Open questions

1. Page-file rename — confirm `pd-neut-cwl_pv-beba_pbso4` as the new
   slug (vs keeping the old filename). Plan assumes the rename.
2. Display glyphs: use Unicode subscripts (`A₀`) in `display_name`, or
   ASCII (`A0`)? Plan assumes Unicode to match the `deg²` precedent;
   fall back to ASCII if any renderer/test objects.
3. Should issue 133 be edited to mark the rename done (leaving only the
   FCJ-model item)? Plan does this in P1.8; revert if you'd rather keep
   133 untouched until the FCJ work lands.

## Concrete files likely to change

Source:
- `src/easydiffraction/datablocks/experiment/categories/peak/cwl_mixins.py`
- `src/easydiffraction/datablocks/experiment/categories/peak/cwl.py`
- `src/easydiffraction/datablocks/experiment/categories/peak/__init__.py`
- `src/easydiffraction/datablocks/experiment/categories/peak/factory.py`
- `src/easydiffraction/datablocks/experiment/item/enums.py`
- `src/easydiffraction/analysis/calculators/cryspy.py`
- `src/easydiffraction/analysis/calculators/crysfml.py`

Verification / docs / tutorials:
- `docs/docs/verification/pd-neut-cwl_pv-asym_empir_pbso4.py` → renamed
  `…/pd-neut-cwl_pv-beba_pbso4.py` (+ regenerated `.ipynb`)
- `docs/docs/verification/pd-neut-cwl_pv-beta_y2o3.py` (+ `.ipynb`)
- `docs/docs/verification/index.md`, `docs/docs/verification/ci_skip.txt`
- `docs/mkdocs.yml`
- `docs/docs/tutorials/refine-cosio-d20.py`,
  `docs/docs/tutorials/refine-hs-hrpt.py` (+ regenerated `.ipynb`)
- `docs/docs/user-guide/parameters/experiment/peak.md`
- `docs/dev/adrs/accepted/edstar-project-persistence.md`,
  `docs/dev/adrs/accepted/edstar-project-persistence/handler-inventory.json`,
  `docs/dev/adrs/accepted/python-cif-category-correspondence.md`
- `docs/dev/issues/open/high_rename-asym-empir-and-add-the-physical-fcj-asymmetry-model.md`
  (mark rename done)
- `docs/dev/issues/open/medium_cryspy-fullprof-berar-baldinozzi-empirical-asymmetry-convention-mismatch.md`
  (issue 166 — rewrite current-name references to the new tags/slug; see
  P1.8)
- `docs/dev/package-structure/full.md` (regenerated by `pixi run fix` in
  Phase 2 — do not hand-edit)

Tests (existing references only — update, do not add new tests in P1):
- `tests/unit/easydiffraction/datablocks/experiment/categories/peak/test_cwl.py`
- `tests/.../peak/test_cwl_mixins.py`, `…/peak/test_factory.py`
- `tests/.../experiment/item/test_base.py`, `test_base_coverage.py`,
  `test_factory.py`
- `tests/unit/easydiffraction/io/cif/test_parse.py`

Use `git grep -n "asym_empir\|empirical asymmetry\|EmpiricalAsymmetry\|empirical-asymmetry"`
to catch every occurrence before each commit.

## Implementation steps (Phase 1)

Each `- [ ]` is one atomic commit. Stage only the listed paths. AGENTS.md
applies: commit each completed step locally before starting the next.

- [x] **P1.1 — Rename model parameters and mixin.** In `cwl_mixins.py`
  rename `EmpiricalAsymmetryMixin` → `BerarBaldinozziAsymmetryMixin`;
  rename the four `_asym_empir_*` parameters, properties, and setters to
  `asym_beba_{a0,b0,a1,b1}`; update `name=`, `description=`,
  `DisplayHandler` (add `A₀…B₁`), and `edi_names`/`cif_names`
  (`_peak.asym_beba_*`).
  Commit: `Rename empirical asymmetry params to beba in peak mixin`

- [ ] **P1.2 — Rename peak class, enum, factory, package init.** Update
  `cwl.py` (`CwlPseudoVoigtBerarBaldinozziAsymmetry`, mixin import,
  docstrings), `enums.py` (member, value
  `cwl-pseudo-voigt-berar-baldinozzi-asymmetry`, `description()` text),
  `factory.py` (type string `pseudo-voigt + berar-baldinozzi asymmetry`),
  `peak/__init__.py` (import the renamed class).
  Commit: `Rename pseudo-Voigt empirical-asymmetry peak type to beba`

- [ ] **P1.3 — Update calculators.** In `cryspy.py` update the four
  `experiment.peak.asym_empir_* → asym_beba_*` reads and the CIF map
  (`asym_beba_a0 → _pd_instr_reflex_asymmetry_p1`, etc., preserving the
  `p1…p4` order). Same CIF map in `crysfml.py`.
  Commit: `Map beba asymmetry params in cryspy and crysfml calculators`

- [ ] **P1.4 — Update existing test references.** Mechanically rename
  `asym_empir_*`, the mixin/class/enum names, and the type string across
  the test files listed above. No new tests (those belong to Phase 2).
  Commit: `Update tests for beba asymmetry rename`

- [ ] **P1.5 — Rename and update the PbSO₄ empirical Verification page.**
  `git mv` `pd-neut-cwl_pv-asym_empir_pbso4.py` →
  `pd-neut-cwl_pv-beba_pbso4.py`; update parameter names; add the neutral
  mismatch note (markdown cell); update its FullProf reference folder
  reference if the slug is embedded. Update `verification/index.md`,
  `ci_skip.txt`, and `mkdocs.yml` to the new slug. Run
  `pixi run notebook-prepare`; stage the regenerated `.ipynb`.
  Commit: `Rename pbso4 empirical page to beba and add mismatch note`

- [ ] **P1.6 — Update the Y₂O₃ Verification page.** In
  `pd-neut-cwl_pv-beta_y2o3.py` rename `asym_empir_1/2 → asym_beba_a0/b0`
  (and the `FULLPROF_ASY_*` constants/comments as needed); replace the
  existing "refines to opposite sign (cryspy #50)" wording with the
  neutral mismatch note. Run `pixi run notebook-prepare`; stage the
  regenerated `.ipynb`.
  Commit: `Use beba names and neutral mismatch note on y2o3 page`

- [ ] **P1.7 — Update tutorials.** Rename the parameter references in
  `refine-cosio-d20.py` and `refine-hs-hrpt.py`. Run
  `pixi run notebook-prepare`; stage the regenerated `.ipynb` siblings.
  Commit: `Use beba asymmetry names in tutorials`

- [ ] **P1.8 — Update remaining docs, issue 133, and issue 166.** Update
  `user-guide/parameters/experiment/peak.md`, the persistence ADR +
  `handler-inventory.json`, and `python-cif-category-correspondence.md`
  to the new tags. In issue 133, mark the rename item done (leave the
  "add physical FCJ model" item open). In **issue 166** rewrite every
  current-name reference to the new terminology — `asym_empir_1…4` →
  `asym_beba_a0/b0/a1/b1`, the page slug
  `pd-neut-cwl_pv-asym_empir_pbso4` → `pd-neut-cwl_pv-beba_pbso4`, and the
  type string / class / enum names — so the open mismatch issue does not
  point readers at removed names; preserve any deliberate historical
  "formerly `asym_empir_*`" context that stays useful (e.g. the
  FullProf-side `P1…P4`/`Asy1…4` labels and any "previously named"
  aside). Add a cross-reference to issue 166 from the affected pages
  where natural.
  Commit: `Update docs, issue 133, and issue 166 for beba asymmetry rename`

- [ ] **P1.9 — Phase 1 review gate.** No-code step; mark `[x]` and
  commit the checklist update alone.
  Commit: `Reach Phase 1 review gate`

## Phase 2 — Verification

Run from the repo root; capture logs with the zsh-safe pattern when
output is needed for analysis.

- `pixi run fix` — regenerates `docs/dev/package-structure/{full,short}.md`;
  commit those with the auto-fixes.
  `pixi run fix > /tmp/edi-fix.log 2>&1; fix_exit_code=$?; tail -n 80 /tmp/edi-fix.log; exit $fix_exit_code`
- `pixi run check > /tmp/edi-check.log 2>&1; check_exit_code=$?; tail -n 200 /tmp/edi-check.log; exit $check_exit_code`
- `pixi run unit-tests > /tmp/edi-unit.log 2>&1; unit_tests_exit_code=$?; tail -n 120 /tmp/edi-unit.log; exit $unit_tests_exit_code`
- `pixi run integration-tests > /tmp/edi-int.log 2>&1; integration_tests_exit_code=$?; tail -n 120 /tmp/edi-int.log; exit $integration_tests_exit_code`
- `pixi run script-tests > /tmp/edi-script.log 2>&1; script_tests_exit_code=$?; tail -n 120 /tmp/edi-script.log; exit $script_tests_exit_code`
- Confirm `pixi run test-structure-check` still passes (any renamed test
  file must keep mirroring its renamed source).

Add/adjust **new** unit tests in Phase 2 only: a parse/round-trip test
for the new `_peak.asym_beba_*` CIF tags, and a peak-factory test for the
new type string and class.

## Status checklist

- [x] P1.1 model params + mixin
- [ ] P1.2 peak class + enum + factory + init
- [ ] P1.3 calculators
- [ ] P1.4 existing test references
- [ ] P1.5 PbSO₄ page rename + note
- [ ] P1.6 Y₂O₃ page note
- [ ] P1.7 tutorials
- [ ] P1.8 docs + issues 133 & 166
- [ ] P1.9 Phase 1 review gate
- [ ] Phase 2 verification green

## Suggested Pull Request

**Title:** Clearer names for the Bérar–Baldinozzi peak-asymmetry settings

**Description:** The four "empirical asymmetry" settings on a
constant-wavelength pseudo-Voigt peak are now named after the
Bérar–Baldinozzi model they implement — `asym_beba_a0`, `asym_beba_b0`,
`asym_beba_a1`, `asym_beba_b1` — so each value's role is clear instead of
an anonymous `1…4`. The relevant verification pages gain a short note
explaining that cryspy and FullProf apply this asymmetry with different
conventions, so the same parameter values are not directly interchangeable
between the two programs. No change to fitted structures or to any other
peak setting.
