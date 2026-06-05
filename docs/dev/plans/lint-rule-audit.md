# Lint-rule audit and adoption roadmap

Reference: [`AGENTS.md`](../../../AGENTS.md). This plan follows the
project conventions there. One **deliberate exception** to the literal
brief is recorded under [Methodology](#methodology): the per-rule
violation counts were gathered with a single comprehensive
`ruff check --statistics`/`--output-format=json` pass that layers the
disabled rules onto the **unmodified** `pyproject.toml` at the command
line, rather than by literally enabling one rule at a time. In
`ruff check` (no `--fix`) the rules do not interact, so the per-rule
numbers are identical to enabling each rule on its own; the
comprehensive pass is just faster and reproducible.

## Purpose

`pyproject.toml` carries a deliberately ambitious `[tool.ruff.lint]`
configuration. Several rule families are still **commented out** in
`select`, and several more are **ignored** — globally and, especially,
for `tests/**` and `docs/**`. This document:

1. Enumerates every currently-disabled rule.
2. Measures exactly how many violations each would raise today, split by
   scope (`src/`, `tests/`, `docs/docs/tutorials/`).
3. Groups the violations by theme and effort.
4. Recommends, per rule, whether to **adopt** (enable + fix) or **keep
   disabled** (with rationale).

It is the **first draft** of a roadmap for tightening code quality — and
it has begun acting on it. This branch lands the tutorial-baseline fix,
this document, the regeneration helper (`tools/lint_rule_audit.py`), the
**Priority 0** cleanup (R1), all of **Priority 1** (P1a `D100`/`D104`
docstrings, P1b `DTZ005` + `TD004`/`TD005`, P1c `I001`/`E501`/`F841`),
and two **Tier-B** adoptions: **D1** (`PLR0402`/`PLR1711`/`PLR6104` +
the `PLW` family in tests, via splitting the `tests/**` PLR ignore) and
**D2** (`T20` — the library's stray `print()` diagnostics routed through
the `Logger`). The remaining Tier-B/C items (R6 `PLC1901`, the
test-complexity rules, R7 `SLF001`) are **recommended to stay disabled**
— see the Adoption roadmap — rather than planned for adoption.

## ADR

No new ADR is required **for the audit itself** — it adds a document and
a regeneration helper, not an architectural decision. The audit does
overlap existing lint policy, so two points of coordination apply:

- **Cross-reference:** the accepted
  [`lint-complexity-thresholds.md`](../adrs/accepted/lint-complexity-thresholds.md)
  ADR already governs the `PLR` complexity rules — it treats those
  thresholds as design guardrails (_refactor; do not raise thresholds or
  add `# noqa`_). The `PLR0913`/`PLR0914`/`PLR0915`/`PLR0917` items in
  [Tier B](#tier-b--adopt-with-moderate-effort--a-judgment-call) and
  [Tier C](#tier-c--keep-disabled-intentional-idioms-policy-or-high-noise)
  must be read in that light: in `tests/**` they are currently silenced
  by a per-file ignore, which is a _standing exception_ to that ADR.
- **Recommendations are non-binding.** Every "keep disabled" entry in
  Tier C (and the "`tests/**` stays permissive" and CIF-aligned
  `id`/`type` observations) is a **recommendation pending user/ADR
  approval**, not a decision taken by this document. Where a _permanent_
  keep-disabled would conflict with or extend existing policy, it needs
  an explicit follow-up ADR before implementation — specifically:
  - **`PLR` complexity ignored for
    `tests/**`** — conflicts with `lint-complexity-thresholds.md`;
    making it permanent needs an ADR amendment (or a new ADR that scopes
    the test-file exception).
  - **`A` kept disabled for CIF-aligned `id`/`type`** — a short new ADR
    ("CIF field names may shadow Python builtins") would record the
    rationale.
  - **`N812` `MUT` import convention** — either a one-line note in
    `AGENTS.md` §Testing or a short ADR.

  Until such an ADR exists, treat these as proposals only.

## Branch and PR

- Branch: `lint-rule-audit` (off `develop`); the deferred / Tier-B/C
  follow-on work continues on `lint-rule-deferred-adoption` (branched
  off `lint-rule-audit`).
- PR target: `develop`.
- This PR bundles two things: the tutorial-baseline refresh that the
  merged `auto_estimate` background work (#193) made necessary, and this
  audit document.

## Methodology

- **Baseline (current `develop` + baseline fix):** all three check tasks
  pass clean — `pixi run py-lint-check` → _All checks passed!_,
  `pixi run py-format-check` → _591 files already formatted_,
  `pixi run docstring-lint-check` (pydoclint) → no findings. So every
  violation below is attributable purely to a disabled rule.
- **Audit overlay (no file edits):** the disabled rules are enabled **at
  the command line** against the _unmodified, tracked_ `pyproject.toml`,
  so the working tree is never touched and no `git checkout`-style
  restore is involved:
  - `--extend-select A,FIX,SLF,T20,TD,D100,D104,DTZ005` turns on the
    commented `select` families (`A`, `FIX`, `SLF`, `T20`, `TD`) plus
    the three _Temporary_ global-ignore codes. (`--select` /
    `--extend-select` override the global `ignore` list for an exact
    code, which is why `D100`/`D104`/`DTZ005` are listed here rather
    than removed from `ignore`.)
  - `--config "lint.per-file-ignores = { … }"` **replaces** the
    per-file-ignore table with the **structural-only** set, dropping the
    _Temporary_ `tests/**` and `docs/**` entries while keeping the
    documented ones (`*/__init__.py` → `F401`; `tests/**` → `ANN`, `D`,
    `DOC`, `INP001`, `RUF012`, `RUF069`, `S101`; `docs/**` → `INP001`,
    `RUF001-003`, `T201`; `docs/docs/tutorials/**` → `E402`). A bare
    `--select` cannot lift a per-file-ignore, so the table is overridden
    via `--config` instead of edited in place.
- **Exact commands** (run from the repo root; these reproduce the
  7144-row inventory and the fix counts exactly — 168 fixes total, of
  which 121 are safe (`ruff --fix`) and 47 need `--unsafe-fixes`):

  ```
  # per-rule counts
  pixi run ruff check src/ tests/ docs/docs/tutorials/ \
    --extend-select "A,FIX,SLF,T20,TD,D100,D104,DTZ005" \
    --config "lint.per-file-ignores = {'*/__init__.py' = ['F401'], 'tests/**' = ['ANN','D','DOC','INP001','RUF012','RUF069','S101'], 'docs/**' = ['INP001','RUF001','RUF002','RUF003','T201'], 'docs/docs/tutorials/**' = ['E402']}" \
    --statistics

  # full records (group by rule + path for the src/tests/tutorials split)
  pixi run ruff check src/ tests/ docs/docs/tutorials/ \
    --extend-select "A,FIX,SLF,T20,TD,D100,D104,DTZ005" \
    --config "lint.per-file-ignores = {'*/__init__.py' = ['F401'], 'tests/**' = ['ANN','D','DOC','INP001','RUF012','RUF069','S101'], 'docs/**' = ['INP001','RUF001','RUF002','RUF003','T201'], 'docs/docs/tutorials/**' = ['E402']}" \
    --output-format=json
  ```

- **Regeneration helper (added in P1.3):** the JSON-grouping step is
  wrapped by a checked-in helper, `tools/lint_rule_audit.py`, so the
  whole inventory regenerates with one non-destructive command —
  `pixi run python tools/lint_rule_audit.py` — that builds the overlay
  above and prints the per-rule/scope/fixability table. It never
  modifies the tracked `pyproject.toml`.

## Full violation inventory

> **Snapshot.** This inventory is the disabled-rule state at the
> **start** of the audit, before any adoption. Rules enabled since
> (Priority 0; `D100`/`D104` in P1a; `DTZ005`/`TD004`/`TD005` in P1b;
> `I001`/`E501`/`F841` in P1c; `PLR0402`/`PLR1711`/`PLR6104` and the
> `PLW` family in D1; `T20` in D2) are now enforced and would no longer
> appear here — see the Adoption roadmap below. Re-run
> `pixi run python tools/lint_rule_audit.py` for live counts.

7144 violations total across all disabled rules. Scope columns: `src` =
`src/`, `tst` = `tests/`, `tut` = `docs/docs/tutorials/`. `fix` = fixes
Ruff offers for the rule; the column counts **both** safe and unsafe
fixes. Of the 168 total fixes, **121 are safe** (applied by
`ruff --fix`: `I001` 114, `PLR0402` 5, `PLR1711` 2) and **47 need
`--unsafe-fixes`** (`PLW0108` 18, `T201` 17, `PLW1514` 5, `PLR6104` 4,
`W291` 2, `F841` 1).

| Rule    | Total | src |  tst | tut | fix | Disabled via                      | Meaning                             |
| ------- | ----: | --: | ---: | --: | --: | --------------------------------- | ----------------------------------- |
| PLC0415 |  1948 |   0 | 1948 |   0 |   0 | tests-ignore                      | import not at top of file           |
| SLF001  |  1830 | 517 | 1313 |   0 |   0 | select(SLF)+tests-ignore          | private member accessed             |
| PLR6301 |  1114 |   0 | 1114 |   0 |   0 | tests-ignore                      | method could be static (no `self`)  |
| PLR2004 |   505 |   0 |  505 |   0 |   0 | tests-ignore                      | magic value in comparison           |
| W505    |   252 |   0 |  189 |  63 |   0 | tests-ignore(W505)+docs-ignore(W) | doc line too long (>72)             |
| ARG005  |   229 |   0 |  229 |   0 |   0 | tests-ignore                      | unused lambda argument              |
| N812    |   152 |   0 |  152 |   0 |   0 | tests-ignore                      | lowercase imported as non-lowercase |
| ARG002  |   132 |   0 |  132 |   0 |   0 | tests-ignore                      | unused method argument              |
| TD002   |   114 | 112 |    2 |   0 |   0 | select(TD)                        | missing TODO author                 |
| TD003   |   114 | 112 |    2 |   0 |   0 | select(TD)                        | missing TODO issue link             |
| FIX002  |   114 | 112 |    2 |   0 |   0 | select(FIX)                       | line contains TODO                  |
| I001    |   114 |   0 |  114 |   0 | 114 | tests-ignore                      | import block unsorted               |
| PLC2701 |   112 |   0 |  112 |   0 |   0 | tests-ignore                      | import of private name              |
| ARG001  |    76 |   0 |   76 |   0 |   0 | tests-ignore                      | unused function argument            |
| D100    |    59 |  34 |    0 |  25 |   0 | global-ignore + docs-ignore(D)    | missing module docstring            |
| PLC1901 |    50 |   0 |   50 |   0 |   0 | tests-ignore                      | `== ''` simplifiable                |
| D104    |    45 |  45 |    0 |   0 |   0 | global-ignore                     | missing package docstring           |
| A002    |    23 |  17 |    6 |   0 |   0 | select(A)                         | argument shadows builtin            |
| ARG004  |    21 |   0 |   21 |   0 |   0 | tests-ignore                      | unused static-method argument       |
| N801    |    21 |   0 |   21 |   0 |   0 | tests-ignore                      | class name not CapWords             |
| PLW0108 |    18 |   0 |   18 |   0 |  18 | tests-ignore                      | unnecessary lambda                  |
| T201    |    17 |  14 |    3 |   0 |  17 | select(T20)                       | `print` found                       |
| A003    |    16 |  16 |    0 |   0 |   0 | select(A)                         | builtin shadowed by method          |
| A001    |     9 |   0 |    4 |   5 |   0 | select(A)                         | variable shadows builtin            |
| PLR0913 |     7 |   0 |    7 |   0 |   0 | tests-ignore                      | too many arguments                  |
| PLR0915 |     7 |   0 |    7 |   0 |   0 | tests-ignore                      | too many statements                 |
| PLC2801 |     5 |   0 |    5 |   0 |   0 | tests-ignore                      | unnecessary dunder call             |
| PLR0402 |     5 |   0 |    5 |   0 |   5 | tests-ignore                      | manual `from` import                |
| PLW1514 |     5 |   0 |    5 |   0 |   5 | tests-ignore                      | `read_text` without encoding        |
| PLR6104 |     4 |   0 |    4 |   0 |   4 | tests-ignore                      | non-augmented assignment            |
| TD004   |     4 |   4 |    0 |   0 |   0 | select(TD)                        | missing TODO colon                  |
| A006    |     3 |   0 |    3 |   0 |   0 | select(A)                         | lambda arg shadows builtin          |
| E741    |     3 |   0 |    3 |   0 |   0 | tests-ignore                      | ambiguous variable name `l`         |
| B018    |     2 |   0 |    2 |   0 |   0 | tests-ignore                      | useless expression                  |
| PLR1711 |     2 |   0 |    2 |   0 |   2 | tests-ignore                      | useless `return`                    |
| SIM117  |     2 |   0 |    2 |   0 |   0 | tests-ignore                      | nested `with`                       |
| TD005   |     2 |   2 |    0 |   0 |   0 | select(TD)                        | missing TODO description            |
| W291    |     2 |   0 |    0 |   2 |   2 | docs-ignore(W)                    | trailing whitespace                 |
| DTZ005  |     1 |   1 |    0 |   0 |   0 | global-ignore                     | `datetime.now()` without tz         |
| E501    |     1 |   0 |    1 |   0 |   0 | tests-ignore                      | line too long (>99)                 |
| F841    |     1 |   0 |    1 |   0 |   1 | tests-ignore                      | unused local variable               |
| PLR0914 |     1 |   0 |    1 |   0 |   0 | tests-ignore                      | too many locals                     |
| PLR0917 |     1 |   0 |    1 |   0 |   0 | tests-ignore                      | too many positional args            |
| TRY301  |     1 |   0 |    1 |   0 |   0 | tests-ignore                      | `raise` inside `try`                |

**Listed-but-clean ignores (zero violations today):** `B011`, `B017`,
`N805`, `PLE` are in the `tests/**` _Temporary_ ignore block but flag
nothing. `ANN` is in the `docs/**` _Temporary_ block but flags nothing
(tutorials are linear scripts with almost no annotated function
signatures). These can be dropped from the ignore lists at no cost.

### By family

| Family          | Total | src |  tst | tut |
| --------------- | ----: | --: | ---: | --: |
| PLC             |  2115 |   0 | 2115 |   0 |
| SLF             |  1830 | 517 | 1313 |   0 |
| PLR             |  1646 |   0 | 1646 |   0 |
| ARG             |   458 |   0 |  458 |   0 |
| W               |   254 |   0 |  189 |  65 |
| TD              |   234 | 230 |    4 |   0 |
| N               |   173 |   0 |  173 |   0 |
| FIX             |   114 | 112 |    2 |   0 |
| I               |   114 |   0 |  114 |   0 |
| D               |   104 |  79 |    0 |  25 |
| A               |    51 |  33 |   13 |   5 |
| PLW             |    23 |   0 |   23 |   0 |
| T               |    17 |  14 |    3 |   0 |
| E               |     4 |   0 |    4 |   0 |
| B/SIM/DTZ/TRY/F |     7 |   1 |    6 |   0 |

The headline finding: **~92%** of all violations live in `tests/**`, and
most of them reflect deliberate, idiomatic test patterns rather than
defects.

## Analysis and recommendations

Recommendations are grouped into three tiers.

### Tier A — Adopt now (clean wins, low effort, aligns with rigor)

These are small, mostly mechanical, and improve real quality. Target:
one or two follow-up PRs.

| Rule(s)                                                                                                                        | Scope | Count | Why adopt                                                                           | Work                                                                                                                                                                                                       |
| ------------------------------------------------------------------------------------------------------------------------------ | ----- | ----: | ----------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `D100`                                                                                                                         | src   |    34 | Module docstrings match the project's docstring rigor; helps MkDocs/IDE.            | Add one-line module docstrings; remove `D100` from global ignore.                                                                                                                                          |
| `D104`                                                                                                                         | src   |    45 | Package (`__init__.py`) docstrings, same rationale.                                 | Add short package docstrings; remove `D104`.                                                                                                                                                               |
| `DTZ005`                                                                                                                       | src   |     1 | Single `datetime.now()` in `project/categories/info/default.py:177`.                | Use a tz-aware timestamp or a justified inline `# noqa: DTZ005` with reason; remove `DTZ005`.                                                                                                              |
| `I001`                                                                                                                         | tests |   114 | Import sorting is already enforced in `src/`; tests should match. **Auto-fixable.** | `ruff check --fix`; drop `I001` from tests-ignore.                                                                                                                                                         |
| `TD004`, `TD005`                                                                                                               | src   |     6 | Well-formed TODOs (colon + description) without demanding author/link.              | Edit 6 TODO comments; enable only the `TD004`/`TD005` subset (not `TD002`/`TD003`).                                                                                                                        |
| `E501`                                                                                                                         | tests |     1 | One over-length line in `tests/.../io/test_ascii.py:3`.                             | Wrap it; drop `E501` from tests-ignore.                                                                                                                                                                    |
| Fixable tests cluster — **safe:** `PLR0402`(5), `PLR1711`(2); **unsafe:** `PLW0108`(18), `PLW1514`(5), `PLR6104`(4), `F841`(1) | tests |    35 | Small, low-risk hygiene.                                                            | `ruff check --fix` clears the 7 safe ones; the 28 unsafe ones need `ruff check --fix --unsafe-fixes` (quick review). (`PLW1514` encoding fixes are a genuine portability win.) Drop all from tests-ignore. |
| Dead ignores: `B011`, `B017`, `N805`, `PLE`, `ANN`(docs)                                                                       | —     |     0 | Listed as _Temporary_ but flag nothing.                                             | Remove from ignore lists — config cleanup, no code change.                                                                                                                                                 |

### Tier B — Adopt with moderate effort / a judgment call

Worth doing, but each needs review, not a blind `--fix`.

| Rule(s)                                    | Scope | Count | Notes                                                                                                                                                                                                                                                                                               |
| ------------------------------------------ | ----- | ----: | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `T20` (`T201`)                             | src   |    14 | Mostly debug-style `print`s in calculators/fitting; **but** `display/plotters/ascii.py` legitimately prints chart output to the terminal. Recommend: convert the non-display prints to the project's output mechanism, add a targeted per-file-ignore for `display/plotters/**`, then enable `T20`. |
| `PLC1901`                                  | tests |    50 | `x == ''` → `not x`. Mechanical and readable; enable for tests after fixing.                                                                                                                                                                                                                        |
| `PLR0913`, `PLR0915`, `PLR0914`, `PLR0917` | tests |    16 | A handful of long/wide test functions. Either refactor (extract helpers) or accept that integration tests are legitimately long and keep ignored. Low priority.                                                                                                                                     |
| `PLC2801`                                  | tests |     5 | `unnecessary-dunder-call`; check each — some dunder calls in tests are intentional behavioural assertions.                                                                                                                                                                                          |

### Tier C — Keep disabled (intentional idioms, policy, or high noise)

These are the bulk of the count. Enforcing them would fight deliberate
conventions or project policy.

| Rule(s)                                   | Scope     | Count | Why keep disabled                                                                                                                                                                                                                                       |
| ----------------------------------------- | --------- | ----: | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `PLC0415`                                 | tests     |  1948 | Tests deliberately import inside functions to isolate state and exercise import-time behaviour.                                                                                                                                                         |
| `SLF001`                                  | tests     |  1313 | Tests legitimately reach into private members to assert internal state. This is the point of unit tests.                                                                                                                                                |
| `PLR6301`                                 | tests     |  1114 | `no-self-use` fires on every `pytest` method that does not touch `self`; idiomatic test classes trip it constantly. Noise.                                                                                                                              |
| `PLR2004`                                 | tests     |   505 | Expected literals in assertions (`assert x == 3.526`) are not "magic values".                                                                                                                                                                           |
| `ARG001/002/004/005`                      | tests     |   458 | `pytest` fixtures requested for side effects and stub/mock signatures routinely leave arguments unused.                                                                                                                                                 |
| `PLC2701`                                 | tests     |   112 | Tests import private names of the module under test on purpose.                                                                                                                                                                                         |
| `N812`                                    | tests     |   152 | Deliberate convention: the module under test is imported as `MUT` (and helpers as `M`). Consistent and readable. Document the convention rather than fight it.                                                                                          |
| `N801`                                    | tests     |    21 | Test-double classes mirror lowercase domain attribute/category names (`_analysis`, `display`, `_fit`) to stand in for them. Intentional.                                                                                                                |
| `SLF001`                                  | src       |   517 | Large; mostly legitimate intra-package access between cooperating objects. Worth a _separate, focused_ review later, not a blanket enable.                                                                                                              |
| `FIX002`, `TD002`, `TD003`                | src       |   338 | TODOs are intentional tracking; `AGENTS.md` forbids removing unresolved TODOs, and the project does not require author/issue-link annotations.                                                                                                          |
| `A` (`A001/2/3/6`, the `id`/`type` cases) | src+tests |   ~45 | `id` and `type` are CIF field names; `AGENTS.md` mandates CIF-aligned naming. Shadowing here is deliberate API design. (The few non-CIF cases — `iter`, `range` — can be renamed opportunistically, but the family is not worth enabling project-wide.) |
| `W505`, `D100`                            | tutorials |    88 | Tutorials carry narration in Markdown cells and use longer prose lines; module docstrings and 72-col doc lines do not fit the notebook-source format.                                                                                                   |
| `B018`                                    | tests     |     2 | Bare expressions in tests are intentional (asserting attribute access / property side effects).                                                                                                                                                         |
| `E741`, `SIM117`, `TRY301`                | tests     |     6 | Tiny counts; `l` as a loop index, nested `with`, and `raise`-in-`try` are acceptable in test scaffolding. Not worth the churn.                                                                                                                          |

## Decisions already made

These are the only firm decisions; everything in
[Tier C](#tier-c--keep-disabled-intentional-idioms-policy-or-high-noise)
and the policy notes in the [ADR](#adr) section are **recommendations**,
not decisions.

- **Rule enablement is incremental and reviewed.** This branch has
  landed the Priority 0 cleanup (R1), all of Priority 1 — P1a
  (`D100`/`D104` docstrings), P1b (`DTZ005`, `TD004`/`TD005`), P1c
  (`I001`/`E501`/`F841` test hygiene) — and two Tier-B adoptions: D1
  (`PLR`/`PLW` sub-codes in tests) and D2 (`T20`; src diagnostics routed
  through the `Logger`). Each remaining tier is implemented only after
  explicit approval, per the roadmap below.
- **Measurement method** is a non-destructive command-line overlay on
  the _unmodified_ `pyproject.toml` (see [Methodology](#methodology)),
  not literal one-at-a-time toggling — equivalent results because
  `ruff check` rules do not interact without `--fix`.
- **Structural ignores stay.** `COM812`, `DOC`, `D200`, and the
  documented `tests`/`docs` ignores (`ANN`/`D`/`S101`/…) are out of
  scope; they have standing reasons in `pyproject.toml`.

Recorded as a recommendation (not yet decided): the audit _supports_
keeping `tests/**` mostly permissive, but that judgement is deferred to
review and, where it conflicts with existing policy, to a follow-up ADR
(see the [ADR](#adr) section). Only the small, clean Tier-A/B items are
proposed for un-ignoring.

## Open questions (for the reviewer)

1. **Scope of this PR:** _resolved_ — this branch lands the Priority 0
   cleanup (R1), all of Priority 1 (P1a, P1b, P1c), and two Tier-B
   adoptions D1 (`PLR`/`PLW` sub-codes) and D2/R5 (`T20`). The remaining
   items (R6 `PLC1901`, R7 src `SLF001`, and the test-complexity rules)
   are **recommended to stay disabled** — see the Adoption roadmap and
   Tier B/C rationale — pending any final user/ADR sign-off.
2. **`T201` in `display/plotters/ascii.py`:** _resolved_ in D2 — those
   prints are the intended terminal-output path and are now
   per-file-ignored (`display/plotters/ascii.py`, `project/display.py`);
   the other src `print()` diagnostics were routed through the `Logger`.
3. **`N812` `MUT` convention:** keep ignored and document it (in
   `AGENTS.md` §Testing), or adopt `flake8-import-conventions` aliases
   instead?
4. **src `SLF001` (517):** schedule a dedicated review pass, or accept
   as intentional intra-package access and leave disabled?
5. **TODO policy:** _resolved_ — the `TD004`/`TD005` _formatting_ subset
   (not author/link) is enabled in P1b; `TD002`/`TD003` stay off, so the
   TODOs themselves are kept per `AGENTS.md`.

## Concrete files likely to change

- Landed in this branch: `tests/tutorials/baseline.json`, this plan
  file, `tools/lint_rule_audit.py` (helper) + its unit test
  `tests/unit/tools/test_lint_rule_audit.py`, `pyproject.toml`
  (`[tool.ruff.lint]` — Priority 0 ignores removed; `D100`/`D104` and
  `TD004`/`TD005` enabled; `DTZ005` un-ignored), the 34 module + 45
  `__init__.py` docstrings (P1a), the `DTZ005` timestamp fix plus four
  TODO-comment fixes (P1b), and sorted imports + an `E501`/`F841` fix
  across ~60 test files (P1c); the `tests/**` PLR/PLW ignore split plus
  the `PLR0402`/`PLR1711`/`PLR6104`/`PLW0108`/`PLW1514` fixes across ~17
  test files (D1); and `T20` enabled, with src `print()` diagnostics
  converted to `log` calls (calculators/fitting/singleton/datablocks)
  and the two display sinks per-file-ignored (D2).
- Not planned (recommended keep-disabled, see Adoption roadmap): R6
  `PLC1901`, the test-complexity rules, and R7 src `SLF001`.

## Implementation steps (Phase 1)

- [x] **P1.1 — Refresh tutorial baselines for `auto_estimate`.** Re-ran
      ed-2/ed-6/ed-20, regenerated their entries in
      `tests/tutorials/baseline.json`. Commit:
      `Update tutorial baselines for auto_estimate background`.
- [x] **P1.2 — Add this audit + roadmap document.** Commit:
      `Add lint-rule audit and adoption roadmap`.
- [x] **P1.3 — Add `tools/lint_rule_audit.py` regeneration helper.**
      Builds the non-destructive `ruff check` overlay from
      [Methodology](#methodology) and prints the
      per-rule/scope/fixability table; never modifies the tracked
      `pyproject.toml`. **Structure it for testability:** a _pure_
      `aggregate(records)` function (plus a `scope(filename)` helper and
      the family rollup) that takes parsed Ruff JSON records and returns
      the per-rule/scope/fixability totals, kept separate from the thin
      CLI shim that invokes Ruff via `subprocess` and prints. The Phase
      2 unit tests target the pure functions only (no subprocess, no
      Ruff run). Commit: `Add lint-rule audit regeneration helper`.
- [x] **P1.4 — Phase 1 review gate.** No code; await review.

## Adoption roadmap

Adopted in this branch (reviewed step by step):

- [x] **R1 / Priority 0 — Config cleanup:** removed the dead ignores
      `B011`, `B017`, `N805`, `PLE`, and docs `ANN` (all had 0
      violations).
- [x] **R3 / P1a — Source docstrings:** enabled `D100`/`D104` and added
      the 79 missing module and package docstrings.
- [x] **P1b — Misc src wins:** fixed `DTZ005` (naive `datetime.now()` →
      UTC-aware, also correcting a latent local-vs-UTC bug) and enabled
      `TD004`/`TD005`, fixing the four flagged TODO comments.
- [x] **P1c — Tests clean items:** enabled `I001` (114 imports sorted
      via safe `ruff --fix`), `E501` (wrapped one over-long docstring),
      and `F841` (removed one dead assignment). `W291` skipped.
- [x] **D1 — PLR/PLW sub-codes:** split the `tests/**` `PLR` family
      ignore (kept the `PLR2004`/`PLR6301` idioms and the complexity
      rules ignored; enforced the rest, fixing `PLR0402`/`PLR1711`/
      `PLR6104`) and dropped the `PLW` family ignore, fixing `PLW0108`
      (incl. two monkeypatch-adapter false positives) and `PLW1514`.
- [x] **D2 / R5 — `T20` (no `print`):** enabled `T20`; routed the src
      `print()` diagnostics (calculators, fitting, singleton,
      datablocks) through the `Logger` (`log.warning`/`log.debug`),
      per-file-ignored the two intentional display sinks
      (`display/plotters/ascii.py`, `project/display.py`), and allowed
      `print` in tests.

Remaining — **recommended to stay disabled** (grounded in the Tier-B/C
analysis); revisit only if a future need arises:

- **R6 — `PLC1901`** (tests): marginal value — `== ''` is explicit and
  safe, whereas `not x` conflates with `None`/`0`. Keep disabled.
- **Test complexity** (`PLR0913`/`PLR0914`/`PLR0915`/`PLR0917`): the
  complexity ADR targets `src`; forcing the ~16 long _test_ functions to
  split usually hurts test locality. Keep the standing test exception.
- **R7 — src `SLF001`** (517): blanket-enabling would force public-API
  bloat or `# noqa` noise. A _targeted_ review of genuine
  cross-subsystem reach-ins could help someday, but that is a separate
  investigation, not a rule adoption.

Deferred — none outstanding. The `PLR`/`PLW` sub-codes that needed the
`tests/**` family-ignore split (`PLR0402`, `PLR1711`, `PLR6104`,
`PLW0108`, `PLW1514`) were adopted in **D1** above.

## Phase 2 — Verification

The **full standard verification set is mandatory** for this PR (per
`AGENTS.md` non-trivial-change workflow) and for every future adoption
batch. It is not optional or narrowed: P1.1 edits
`tests/tutorials/baseline.json`, P1.3 adds a helper script, and P1.2
adds a developer document, so the whole set runs.

**Tests to add first.** Per the two-phase workflow, the helper's tests
are written in Phase 2 (not Phase 1). Add
`tests/unit/tools/test_lint_rule_audit.py` — mirroring the existing
`tests/unit/tools/test_bump_vendored_js.py` precedent for testing a
`tools/` script — covering the helper's _pure_ aggregation logic with
representative, synthetic Ruff JSON records (no subprocess, no network,
no real Ruff run, per `AGENTS.md` §Testing):

- per-rule total counts;
- `scope()` bucketing into `src` / `tests` / `tutorials` from filenames;
- fixability counting (records whose `fix` field is non-null);
- family rollup (leading-alpha-prefix grouping, e.g. `PLC0415` → `PLC`);
- edge cases: an empty record list, and a path outside the three scopes.

`AGENTS.md` §Testing requires every new module to ship with tests; the
two-phase workflow simply places that test-writing here in Phase 2.
(`tools/` is outside the `test_structure_check.py` mirror, which only
covers `src/easydiffraction/`, so no structure-check entry is needed.)

After the tests are added, run the mandatory set in order, fixing and
re-running until clean. Use the zsh-safe capture pattern where output
must be saved:

```
pixi run fix
pixi run check > /tmp/easydiffraction-check.log 2>&1; check_exit_code=$?; tail -n 200 /tmp/easydiffraction-check.log; exit $check_exit_code
pixi run unit-tests
pixi run integration-tests
pixi run script-tests
```

**Additional, baseline-specific checks** — these _supplement_ the
mandatory set above; they do not replace any of it:

- `pixi run script-tests-checked` — a superset of `script-tests`: it
  `depends-on` `script-tests` (so it runs the tutorials first) and then
  additionally asserts the refreshed `tests/tutorials/baseline.json`.
  Running it satisfies the mandatory `script-tests` step _and_ confirms
  the baseline fix; it is the recommended way to cover both for this PR.
- `pixi run python tools/lint_rule_audit.py` — regenerates the inventory
  in this document from the current tree (sanity-check after P1.3).
- `pixi run py-lint-check` / `py-format-check` / `docstring-lint-check`
  — already inside `pixi run check`; listed only for a quick local
  confirmation that nothing introduced lint/format/docstring drift.

## Suggested Pull Request

**Title:** Refresh tutorial baselines and draft a lint-rule adoption
roadmap

**Description:** Updates the saved tutorial fit-result baselines so the
automatic-background feature's slightly different (and correct) results
pass the tutorial checks again. Adds a developer document that
inventories every disabled code-style rule, measures how many issues
each would surface today, and recommends — rule by rule — which to
switch on (with fixes) and which to keep off because they reflect
deliberate, well-reasoned conventions, plus a small helper
(`tools/lint_rule_audit.py`) that regenerates that inventory on demand.
As concrete first steps it also enforces the "Priority 0" cleanup
(removing five ignores that currently flag nothing — `B011`, `B017`,
`N805`, `PLE`, docs `ANN`) and all of "Priority 1": the source-docstring
rules `D100`/`D104` (adding the 79 missing module and package
docstrings), a couple of source fixes (`DTZ005` and the `TD004`/`TD005`
TODO-formatting rules), and test hygiene (`I001` import sorting plus
`E501`/`F841`); plus two Tier-B wins — enforcing more pytest-lint rules
(the `PLR`/`PLW` sub-codes in tests) and routing the library's stray
diagnostic `print()`s through its logging system (`T20`). It sets up a
clear, low-risk path to gradually raise code quality; the remaining
Tier-B/C rules are documented as deliberate keep-disabled
recommendations rather than planned work.

## Appendix: all rules by priority (quick reference)

Every rule code that fired in the audit (plus the dead ignores), grouped
by priority. Scope counts are `src` / `tests` / `tut`; **[fix]** = safe
auto-fix (`ruff --fix`), **[fix!]** = needs `--unsafe-fixes`. This
condenses the
[Analysis and recommendations](#analysis-and-recommendations) tiers into
a single lookup.

### Priority 0 — Free cleanup (0 violations today; just remove from ignore)

| Rule           | Description                 | Scope    | Recommendation                                            |
| -------------- | --------------------------- | -------- | --------------------------------------------------------- |
| `B011`         | `assert False` in code      | tests    | Drop from ignore — costs nothing                          |
| `B017`         | assert on blind `Exception` | tests    | Drop from ignore                                          |
| `N805`         | first method arg not `self` | tests    | Drop from ignore                                          |
| `PLE` (family) | pylint **errors**           | tests    | Drop from ignore — real errors should never be silenced   |
| `ANN` (family) | missing type annotations    | docs/tut | Drop from docs ignore (tutorials have ~no annotated defs) |

### Priority 1 — Adopt now (clean wins, low effort)

| Rule      | Description                  | Scope (count)         | Recommendation                                             |
| --------- | ---------------------------- | --------------------- | ---------------------------------------------------------- |
| `I001`    | unsorted import block        | tests (114) **[fix]** | Adopt — `ruff --fix` sorts them (safe)                     |
| `D104`    | missing package docstring    | src (45)              | Adopt — add `__init__.py` docstrings                       |
| `D100`    | missing module docstring     | src (34)              | Adopt **for src** — add one-liners                         |
| `PLW0108` | unnecessary lambda           | tests (18) **[fix!]** | Adopt — `--unsafe-fixes` (quick review)                    |
| `TD004`   | missing colon in TODO        | src (4)               | Adopt — TODO formatting subset                             |
| `PLW1514` | `read_text` without encoding | tests (5) **[fix!]**  | Adopt — `--unsafe-fixes`; portability win                  |
| `PLR0402` | manual `from` import         | tests (5) **[fix]**   | Adopt — `ruff --fix` (safe)                                |
| `PLR6104` | non-augmented assignment     | tests (4) **[fix!]**  | Adopt — `--unsafe-fixes` (quick review)                    |
| `TD005`   | missing TODO description     | src (2)               | Adopt — TODO formatting subset                             |
| `PLR1711` | useless `return`             | tests (2) **[fix]**   | Adopt — `ruff --fix` (safe)                                |
| `W291`    | trailing whitespace          | tut (2) **[fix!]**    | Adopt — `--unsafe-fixes`; keep `W505` ignored in tutorials |
| `DTZ005`  | `datetime.now()` without tz  | src (1)               | Adopt — fix the one case (or justified `# noqa`)           |
| `E501`    | line too long (>99)          | tests (1)             | Adopt — wrap the single line                               |
| `F841`    | unused local variable        | tests (1) **[fix!]**  | Adopt — `--unsafe-fixes` (quick review)                    |

### Priority 2 — Adopt with judgment (review each, not a blind fix)

| Rule      | Description              | Scope (count)                  | Recommendation                                                                                       |
| --------- | ------------------------ | ------------------------------ | ---------------------------------------------------------------------------------------------------- |
| `PLC1901` | `x == ''` simplifiable   | tests (50)                     | Adopt after rewriting to `not x`                                                                     |
| `T201`    | `print` found            | src (14), tests (3) **[fix!]** | Adopt **after** per-file-ignoring `display/plotters/ascii.py` (legit terminal output); fix is unsafe |
| `PLR0915` | too many statements      | tests (7)                      | Refactor or keep — governed by complexity ADR                                                        |
| `PLR0913` | too many arguments       | tests (7)                      | Refactor or keep — complexity ADR                                                                    |
| `PLC2801` | unnecessary dunder call  | tests (5)                      | Review each — some are intentional behavioural asserts                                               |
| `PLR0914` | too many locals          | tests (1)                      | Refactor or keep — complexity ADR                                                                    |
| `PLR0917` | too many positional args | tests (1)                      | Refactor or keep — complexity ADR                                                                    |

### Priority 3 — Keep disabled (intentional idioms, policy, or high noise)

| Rule      | Description                            | Scope (count)           | Recommendation                                                                    |
| --------- | -------------------------------------- | ----------------------- | --------------------------------------------------------------------------------- |
| `PLC0415` | import not at top level                | tests (1948)            | Keep — tests import inside functions to isolate state                             |
| `SLF001`  | private member accessed                | src (517), tests (1313) | Keep in tests (the point of unit tests); src warrants a _separate_ focused review |
| `PLR6301` | method could be static (`no-self-use`) | tests (1114)            | Keep — fires on every `pytest` method; pure noise                                 |
| `PLR2004` | magic value in comparison              | tests (505)             | Keep — expected literals in assertions aren't "magic"                             |
| `ARG005`  | unused lambda argument                 | tests (229)             | Keep — stub/mock signatures                                                       |
| `N812`    | lowercase imported as non-lowercase    | tests (152)             | Keep — deliberate `MUT` (module-under-test) convention; document it               |
| `ARG002`  | unused method argument                 | tests (132)             | Keep — stub/mock signatures                                                       |
| `PLC2701` | import of private name                 | tests (112)             | Keep — tests import internals on purpose                                          |
| `FIX002`  | line contains TODO                     | src (112)               | Keep — TODOs are intentional tracking (`AGENTS.md`)                               |
| `TD002`   | missing TODO author                    | src (112)               | Keep — project doesn't require authors                                            |
| `TD003`   | missing TODO issue link                | src (112)               | Keep — project doesn't require links                                              |
| `ARG001`  | unused function argument               | tests (76)              | Keep — `pytest` fixtures used for side effects                                    |
| `ARG004`  | unused static-method argument          | tests (21)              | Keep — stub/mock signatures                                                       |
| `N801`    | class name not CapWords                | tests (21)              | Keep — test doubles mirror lowercase domain names (`_analysis`, `display`)        |
| `A002`    | argument shadows builtin               | src (17), tests (6)     | Keep — `id`/`type` are CIF field names (CIF-aligned naming)                       |
| `A003`    | builtin shadowed by method             | src (16)                | Keep — CIF `id`/`type` properties                                                 |
| `W505`    | doc line too long (>72)                | tests (189), tut (63)   | Keep — tutorial narration / longer prose lines                                    |
| `A001`    | variable shadows builtin               | tests (4), tut (5)      | Keep — CIF `id` / notebook `display` builtin                                      |
| `D100`    | missing module docstring               | tut (25)                | Keep **for tutorials** — they use Markdown cells                                  |
| `A006`    | lambda arg shadows builtin             | tests (3)               | Keep — CIF `id`                                                                   |
| `E741`    | ambiguous variable name `l`            | tests (3)               | Keep — trivial test scaffolding                                                   |
| `B018`    | useless expression                     | tests (2)               | Keep — intentional attribute-access / property tests                              |
| `SIM117`  | nested `with` statements               | tests (2)               | Keep — not worth the churn                                                        |
| `TRY301`  | `raise` inside `try`                   | tests (1)               | Keep — trivial                                                                    |

Parent families currently commented out in `select`: `A`, `FIX`, `SLF`,
`T20`, `TD` — their subrules appear above. Structural ignores left
untouched (documented reasons, out of scope): `COM812`, `DOC`, `D200`,
and the `tests`/`docs` `ANN`/`D`/`S101`/… set.
