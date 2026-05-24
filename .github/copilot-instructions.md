# Copilot Instructions for EasyDiffraction

## Project Context

- Python library for crystallographic diffraction analysis (refining
  structural models against experimental data).
- Domain axes: `sample_form` (powder, single crystal), `beam_mode`
  (time-of-flight, constant wavelength), `radiation_probe` (neutron,
  x-ray), `scattering_type` (bragg, total).
- Calculation backends: `cryspy` and `crysfml` (Bragg), `pdffit2` (total
  scattering).
- CIF maps to `DatablockItem`/`DatablockCollection` and
  `CategoryItem`/`CategoryCollection` (loops). Follow CIF naming;
  deviate only for a clearly better API.
- Metadata via frozen dataclasses: `TypeInfo`, `Compatibility`,
  `CalculatorSupport`.
- Audience is scientists, often non-programmers: prioritize
  discoverability, clear errors, and safe defaults over developer
  ergonomics.
- Critical-software rigor: every code path tested, edge cases handled
  explicitly, no silent failures.

## Code Style

- snake_case (functions/vars), PascalCase (classes), UPPER_SNAKE_CASE
  (constants).
- `from __future__ import annotations` in every module. Type-annotate
  all public signatures.
- Numpy-style docstrings on all public classes/methods (Parameters /
  Returns / Raises where applicable). Summary is one line ≤72 chars
  (`max-doc-length`); shorten wording rather than wrap.
- Flat over nested, explicit over clever, composition over deep
  inheritance. No defensive checks for unlikely edge cases.
- One class per file when substantial; group small related classes.
- No `**kwargs` — use explicit keyword arguments.
- No string-based dispatch (e.g. `getattr(self, f'_{name}')`); write
  named methods (`_set_sample_form`, `_set_beam_mode`). Narrow framework
  metadata lookups are allowed when the attribute name is a class-level
  declaration, is not user input, and is validated in one central place;
  for example, `CategoryItem._category_entry_name`.
- Public attrs are either editable (getter+setter property) or read-only
  (getter only). For internal mutation of read-only props, use a private
  `_set_<name>` method, not a public setter.
- Lint complexity thresholds in `pyproject.toml` (`max-args`,
  `max-branches`, `max-statements`, `max-locals`, `max-nested-blocks`,
  …) are guardrails. A violation means refactor (extract helpers,
  parameter objects, flatten) — do not raise thresholds, add `# noqa`,
  or otherwise silence them. For complex refactors touching many lines
  or public API, propose a plan and wait for approval.

## Architecture

- Eager top-of-module imports by default. Lazy imports only to break
  circular deps or to keep `core/` free of heavy imports on rarely-
  called paths (e.g. `help()`).
- No `pkgutil`/`importlib` auto-discovery, no background threads, no
  monkey-patching or runtime class mutation.
- No `__all__`; control public API via explicit `__init__.py` imports.
  No redundant `import X as X` aliases.
- Concrete classes use `@Factory.register`. Each package's `__init__.py`
  must explicitly import every concrete class to trigger registration —
  always update it when adding a class.
- Switchable categories (factory-swappable at runtime) follow the
  category-owned selector contract from
  [`switchable-category-owned-selectors.md`](../docs/dev/adrs/accepted/switchable-category-owned-selectors.md):
  the owner exposes `<category>` (read-only attribute on the owner),
  and the category itself exposes `<category>.type` (writable
  property) and `<category>.show_supported()`. There are no
  owner-level `<owner>.<cat>_type` setters and no owner-level
  `show_supported_<cat>_types()` / `show_current_<cat>_type()`
  methods. The owner provides a private `_swap_<name>` hook that
  the category's `type` setter calls through a back-reference;
  inside the hook the owner replaces the category instance
  (Family A), rebinds the live engine (Family B), or activates
  sibling categories (Family C) — the user-facing surface stays
  uniform. Required even if only one implementation exists.
- Result-output categories paired with a switchable input category
  (today: `analysis.fit_result` paired with `analysis.minimizer`
  via `<minimizer-class>._fit_result_class`) are **internal pairs**,
  not user-facing switchables: they do not expose `type` or
  `show_supported()`; the owner swaps them in lockstep with the
  paired input category. See
  [`minimizer-input-output-split.md`](../docs/dev/adrs/accepted/minimizer-input-output-split.md).
- Categories are flat siblings within their owner. Never nest a category
  as a child of another category of a different type; cross-reference
  via IDs instead.
- Every finite, closed set of values (factory tags, axes, enumerated
  descriptors) is a `(str, Enum)`; compare against members, not raw
  strings.
- Keep `core/` free of domain logic (base classes and utilities only).
- Don't introduce abstractions before a concrete second use case. Don't
  add dependencies without asking.

## Testing

- Every new module, class, or bug fix ships with tests. See
  `docs/dev/adrs/accepted/test-strategy.md` for the full strategy.
- Unit tests mirror the source tree:
  `src/easydiffraction/<pkg>/<mod>.py` →
  `tests/unit/easydiffraction/<pkg>/test_<mod>.py`. Verify with
  `pixi run test-structure-check`. Supplementary tests:
  `test_<mod>_coverage.py`. Category packages with only
  `default.py`/`factory.py` may use one parent-level
  `test_<package>.py`.
- Tests expecting `log.error()` to raise must `monkeypatch` Logger to
  RAISE mode (another test may have leaked WARN mode).
- `@typechecked` setters raise `typeguard.TypeCheckError`, not
  `TypeError`.
- No test-ordering dependence, no network, no sleeping, no real
  calculation engines in unit tests.

## Tutorials

- Notebooks in `docs/docs/tutorials/*.ipynb` are generated artifacts.
  Edit only the corresponding `*.py`, then run
  `pixi run notebook-prepare`.

## Change Discipline

- Before any structural/design change (new categories, factories,
  switchable-category wiring, datablocks, CIF serialisation), read
  `docs/dev/adrs/index.md` and the relevant accepted ADRs. Localised bug
  fixes or test updates need only this file.
- Development documentation lives under `docs/dev/`. Use
  `docs/dev/adrs/index.md` as the architecture and decision navigation
  surface; there is no separate `architecture.md` source of truth.
- Project is in beta: no legacy shims, no deprecation warnings — update
  tests and tutorials to the current API.
- Minimal diffs; don't reformat working code. Fix only what's asked;
  flag adjacent issues as comments. Don't add features or refactor
  unless asked. Don't remove TODOs or comments unless the change fully
  resolves them.
- Never remove or replace existing functionality without explicit
  confirmation — highlight every removal and wait for approval.
- When renaming or auditing usages, search the entire project (code,
  tests, tutorials, docs). Use `git grep -n` because all contributors
  have Git; do not assume `rg` is installed. If `git grep` is
  unavailable, fall back to `find ... -type f` plus `grep -n`.
- When asked to review a plan, save the review next to that plan using
  `<plan-stem>_review-N.md`, where `N` is one greater than the highest
  existing review number for that plan. For example,
  `docs/dev/plans/background-refactor.md` is reviewed in
  `docs/dev/plans/background-refactor_review-1.md`, then
  `docs/dev/plans/background-refactor_review-2.md`. A reviewer must not
  run tests, `pixi run fix`, `pixi run check`, or any other build or
  verification command; reviews are static reads of code, plan, and
  documentation only. Note in the review which checks were skipped so
  the next implementer knows the gap.
- Writing a review or a reply to a review does **not** require running
  any formatter (`prettier`, `pixi run fix`, `ruff format`, …) or any
  lint/check/test command on the review/reply file itself or any
  surrounding documentation. Review and reply files are markdown-only,
  written by hand, and committed as-is. Formatting passes happen later,
  during implementation Phase 2 verification — not in the review cycle.
  This rule applies to both `_review-N.md` and `_reply-N.md` files
  regardless of where they live (`docs/dev/plans/`, `docs/dev/adrs/…/`,
  etc.).
- Each change is atomic and single-commit-sized: make one change,
  suggest the commit message, then stop and wait for confirmation.
  Exception: when the user invokes an **Agent Shortcut** (see that
  section), the matching loop runs autonomously per its own
  termination rule — neither a per-commit pause nor a per-tick
  pause applies inside that loop. The default applies again as soon
  as the shortcut terminates.
- When in doubt, ask.

## Commits

- Suggest a commit message after each change: code block, ≤72 chars,
  imperative mood, no type prefix, no `Co-authored-by: Copilot`.
  Examples:
  - Add ChebyshevPolynomialBackground class
  - Implement background_type setter on Experiment
  - Standardize switchable-category naming convention
- Stage only the files modified for the step, using explicit paths where
  practical. Do not include data, project, CIF, or other generated
  artifacts produced by integration/script/notebook tests unless the
  user explicitly asked to update them.
- Before each commit, inspect the worktree and avoid staging unrelated
  user changes. If unrelated dirty files exist, leave them untouched and
  mention them only when relevant.

## Workflow

Non-trivial changes use a two-phase workflow:

- **Phase 1 — Implementation.** Code and docs updates only. Update ADRs
  when the change affects architecture or documented decisions. Do not
  create or run tests unless the user explicitly asks. When done,
  present for review and iterate until approved.
- **Phase 2 — Verification.** Add/update tests, then run `pixi run fix`,
  `pixi run check`, `pixi run unit-tests`, `pixi run integration-tests`,
  `pixi run script-tests`.

Notes:

- `pixi run fix` regenerates `docs/dev/package-structure/full.md` and
  `docs/dev/package-structure/short.md` automatically — never edit those
  by hand. Don't review auto-fixes; accept and move on. Then
  `pixi run check` until clean.
- When a check command needs saved output for analysis, capture the log
  and preserve the command exit code with a zsh-safe variable name:
  `pixi run check > /tmp/easydiffraction-check.log 2>&1; check_exit_code=$?; tail -n 200 /tmp/easydiffraction-check.log; exit $check_exit_code`.
  Never assign to `status` in zsh; it is readonly. Use task-specific
  names such as `check_exit_code`, `unit_tests_exit_code`, or
  `script_tests_exit_code`.
- Open issues / design questions / planned improvements live in
  `docs/dev/issues/open.md` (priority-ordered). On resolution, move to
  `docs/dev/issues/closed.md` and update the relevant ADR or
  `docs/dev/adrs/index.md` if affected.

### Planning

When asked to create a plan:

- Start the plan by referencing this file:
  `.github/copilot-instructions.md`. State any deliberate exception to
  these instructions in the plan itself.
- First gather enough repository context to make the plan concrete. Ask
  all ambiguous or unclear questions in one concise batch; record
  unresolved questions in the plan if the user wants it saved before
  answering them.
- Save plans as `docs/dev/plans/<feature-name>.md` (lowercase,
  dash-separated, e.g. `docs/dev/plans/background-refactor.md`). When a
  plan implements one ADR, use the same slug as the ADR file; for
  example, `docs/dev/adrs/suggestions/foo.md` maps to
  `docs/dev/plans/foo.md`. If a plan has no corresponding ADR or spans
  multiple ADRs, choose a concise feature slug and list all related ADRs
  in the plan. Use the same `<feature-name>` as a **flat-slug
  implementation branch** off `develop` (no `feature/` prefix —
  e.g. `emcee-minimizer`, not `feature/emcee-minimizer`). PRs target
  `develop`, not `master`. Do not push the branch unless asked.
- Include a status checklist with `[ ]` items; mark `[x]` as completed
  during implementation.
- Apply the two-phase workflow (Phase 1 implementation, Phase 2
  verification) to non-trivial plans. Stop after Phase 1 and ask the
  user to review before starting Phase 2.
- The plan must explicitly state that, when an AI agent follows it,
  every completed Phase 1 implementation step must be staged with
  explicit paths and committed locally before moving to the next
  implementation step or the Phase 1 review gate. Follow the rules in
  **Commits**. Keep commits atomic, single-purpose, and aligned with
  plan steps.
- If implementation uncovers a serious requirement, risk, design issue,
  or scope change not covered by the plan, stop and ask the user for
  clarification or approval before proceeding. Record the unresolved
  issue in the plan when useful.
- The plan should be easy to maintain while working: include concrete
  files likely to change, decisions already made, open questions,
  verification commands for Phase 2, and a short suggested commit
  message or branch name when useful.
- Verification commands in plans must include the zsh-safe log-capture
  pattern from **Workflow** whenever saved output is needed for later
  analysis.
- Before saving a plan, verify that referenced files, directories,
  scripts, and task names exist locally when that is practical. If a
  referenced tool is optional or missing, include an available fallback.
- End every plan with a "Suggested Pull Request" section containing a
  short PR title and a brief end-user-oriented description. Keep this
  section non-technical enough for scientists and other users to
  understand the benefit. Update it during implementation if extra
  approved changes become important enough to mention in the PR title or
  description.
- When replying to a plan review, save the reply alongside the review.
  Reviews live at `docs/dev/plans/<feature-name>_review-<N>.md`; the
  matching reply goes to `docs/dev/plans/<feature-name>_reply-<N>.md`
  (same slug, same number, swap `review` → `reply`). One reply file per
  review file; do not bundle replies to multiple reviews into one
  document. Structure the reply with one section per finding, each
  containing a verdict (agree / disagree / partial), the action taken in
  the plan, and a pointer to the affected plan section. After updating
  the plan, also update the reply if a numbered step shifts so that
  cross-references stay accurate.

## Agent Shortcuts

When the user enters one of these literal keywords at the start of a
message, execute the matching task instead of asking for the full
instructions every time. The keyword is the entire trigger; arguments
follow on the same line.

Common preamble for every shortcut (run once at task start):

- Ask the user, in one batch, for any permission grants needed to
  run unattended for the full task. At minimum: `Bash` with
  `run_in_background` for polling, `Edit`/`Write` on `docs/`, the
  shell primitives `git`, `until`, `sleep`, `ls`, `grep`. Cite this
  section so the user knows why.
- Stay on the current branch. Do not switch or create branches.
- Polling cadence is 60 s. Use Bash with `run_in_background` and an
  `until [ -f <path> ]; do sleep 60; done` body so the harness
  notifies you when the awaited file appears. Do not poll inline.
- Filename suffixes follow the existing convention:
  `<stem>_review-N.md` and `<stem>_reply-N.md` next to the parent
  ADR or plan, where `N` is one greater than the highest existing
  number for that stem (starting at 1).
- Each shortcut runs autonomously. Do not pause for confirmation
  between rounds; auto-apply every finding. Only stop when the
  termination condition for that shortcut is met, or the user sends
  an explicit message asking you to stop or change direction.

### `/draft-adr <topic>`

Act as the ADR author. Draft an ADR suggestion, then respond to
incoming reviews in a polling loop.

**Setup (once):**

1. Run the common preamble.
2. Pick a flat lowercase-dash slug from `<topic>`. Save the ADR at
   `docs/dev/adrs/suggestions/<slug>.md` using the project's ADR
   template (Status: Proposed; Context; Decision; Consequences;
   Alternatives Considered; Deferred Work as needed).
3. Start polling for `<slug>_review-1.md` next to the ADR.

**Loop (per tick):**

- When `<slug>_review-N.md` appears: read it, update the ADR to
  address every finding, and write `<slug>_reply-N.md` with one
  section per finding (verdict + action taken + pointer to the
  affected ADR section).
- Start polling for `<slug>_review-(N+1).md`.
- **Do not commit.** Leave every edit in the worktree as modified
  or untracked. The reviewer side (`/review-adr`) is responsible
  for the final commit.

**Termination:** only on an explicit user message asking you to
stop or change direction. The loop never self-terminates.

### `/review-adr [<slug>]`

Act as the ADR reviewer. Review an ADR suggestion in a polling loop
until all findings are addressed.

**Setup (once):**

1. Run the common preamble.
2. Identify the target ADR. If `<slug>` is given, target
   `docs/dev/adrs/suggestions/<slug>.md`. Otherwise monitor
   `docs/dev/adrs/suggestions/` for a `<slug>.md` with no existing
   `<slug>_review-*.md`. If none exists, report "no ADR has
   appeared yet" and start polling for it.
3. When the ADR appears, run a static review per
   [`.github/copilot-instructions.md`](.github/copilot-instructions.md)
   → **Change Discipline** plan-review rule. **Do not run tests,
   lint, build, formatters, or any `pixi` command — ADR reviews are
   static reads only.** Save the review at `<slug>_review-1.md`
   next to the ADR.

**Loop (per tick):**

- Poll for `<slug>_reply-N.md` matching the most recent review.
- When the reply appears, re-read the ADR against the new reply
  and every prior review/reply. Pick exactly one branch:
  - **Findings remain:** write `<slug>_review-(N+1).md` listing
    only the open findings, then poll for the next reply.
  - **All findings addressed:** write a final
    `<slug>_review-(N+1).md` stating "no findings; ADR is ready",
    then run the termination cleanup below and stop.

**Termination cleanup (only when the final clean review is
written):**

1. `git rm` every `<slug>_review-*.md` and `<slug>_reply-*.md`
   next to the ADR (including the final clean review just
   written).
2. `git add` the cleaned-up ADR.
3. Commit with message `Add <slug> ADR suggestion` (or an
   equivalent imperative ≤72 chars).
4. Report the commit hash and stop.

### `/draft-plan [<slug>]`

Act as the implementation-plan author. Same loop as `/draft-adr`,
applied to an implementation plan instead of an ADR.

- Source ADR: if `<slug>` is given, target the ADR at
  `docs/dev/adrs/accepted/<slug>.md` (or `suggestions/` if the ADR
  is not yet promoted). Otherwise pick the newest accepted ADR
  matching the most recent `/review-adr` cycle. Use the same slug
  for the plan.
- Save the plan at `docs/dev/plans/<slug>.md` using the project's
  plan template per
  [`.github/copilot-instructions.md`](.github/copilot-instructions.md)
  → **Planning**: ADR cross-reference, branch + PR notes,
  Decisions, Open questions, Concrete files, Phase 1 steps with
  status checklist, Phase 2 verification commands using the
  zsh-safe log-capture pattern, and a Suggested Pull Request
  section.
- Loop behaviour identical to `/draft-adr`: poll
  `docs/dev/plans/<slug>_review-N.md`; write
  `<slug>_reply-N.md`; **no commits in the loop**.

**Termination:** only on an explicit user message asking you to
stop or change direction.

### `/review-plan [<slug>]`

Act as the implementation-plan reviewer. Same loop as `/review-adr`,
applied to an implementation plan.

- Target: if `<slug>` is given, target
  `docs/dev/plans/<slug>.md`. Otherwise monitor `docs/dev/plans/`
  for the newest plan matching the most recent `/draft-plan`
  cycle.
- Static reads only — same "no tests / lint / build / formatters /
  pixi" rule applies during plan reviews.
- Loop and termination identical to `/review-adr`, with the final
  commit message `Add <slug> implementation plan` (or an
  equivalent imperative ≤72 chars).
