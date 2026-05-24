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

When the user's message starts with one of these literal keywords,
treat it as an operational command, not as ordinary prose. Execute the
matching task instead of asking for the full instructions every time.
The first non-whitespace token is the trigger; arguments follow on the
same line. This applies in future turns and after context compaction:
if the newest user message begins with `/draft-adr`, `/review-adr`,
`/draft-plan`, or `/review-plan`, enter that shortcut's stateful loop.

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
  If the current harness exposes a native recurring automation or
  heartbeat mechanism instead of background Bash, use that mechanism
  with the same cadence and file target. Do not downgrade the shortcut
  into a one-shot review/reply because background Bash is unavailable.
- Filename suffixes follow the existing convention:
  `<stem>_review-N.md` and `<stem>_reply-N.md` next to the parent
  ADR or plan, where `N` is one greater than the highest existing
  number for that stem (starting at 1).
- Each shortcut runs autonomously. Do not pause for confirmation
  between rounds; auto-apply every finding. Only stop when the
  termination condition for that shortcut is met, or the user sends
  an explicit message asking you to stop or change direction.
- Before starting any poll, first check whether the file being awaited
  already exists. If it does, process it immediately, then continue the
  loop from the next expected suffix.
- Never stop after writing only the first review, first reply, or first
  draft. After every loop action, immediately arrange the next poll
  unless the shortcut's termination condition has been reached.
- **Final-review sentinel.** When a reviewer shortcut decides no
  findings remain, it writes a final review file whose body begins
  with the literal sentinel line
  `**No findings. Ready to commit.**` on its own line (immediately
  after the title and any boilerplate header). The matching author
  shortcut, before writing a reply, runs
  `grep -q "^\*\*No findings\. Ready to commit\.\*\*$"
  docs/dev/{adrs/suggestions,plans}/<stem>_review-<N>.md` on the
  newest review. If the sentinel is found, the author shortcut
  **stops the polling loop** without writing a reply and reports
  that the review cycle is closed. The sentinel is the only
  termination signal between author and reviewer — no other phrase
  triggers it.
- **Existing shortcuts never delete files and never commit.** The
  four shortcuts in this section
  (`/draft-adr`, `/review-adr`, `/draft-plan`, `/review-plan`)
  only read existing files and write new ones. They never call
  `git rm`, `git add`, or `git commit`. Cleanup and commit happen
  in a separate dedicated shortcut (`/implement-plan`).

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

- When `<slug>_review-N.md` appears, first check for the
  final-review sentinel (see Common preamble). If
  `**No findings. Ready to commit.**` is the first body line,
  stop the polling loop: report that the review cycle is closed
  and that `/implement-plan` (or a manual commit) is the next
  step. Do not write a reply.
- Otherwise read the review, update the ADR to address every
  finding, and write `<slug>_reply-N.md` with one section per
  finding (verdict + action taken + pointer to the affected ADR
  section).
- Start polling for `<slug>_review-(N+1).md`.
- **Do not commit and do not delete any file.** Leave every edit
  in the worktree as modified or untracked. Commit and cleanup
  happen later in `/implement-plan`.

**Termination:** either the sentinel-driven stop above or an
explicit user message asking you to stop or change direction.

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
  - **All findings addressed:** write the final review file
    `<slug>_review-(N+1).md` whose body begins with the
    final-review sentinel from the Common preamble:
    `**No findings. Ready to commit.**` on its own line, followed
    by a short paragraph summarising the round (no findings list).
    Then **stop the loop**. **Do not delete any review or reply
    file. Do not commit anything.** Cleanup and commit happen in
    `/implement-plan`.

**Termination:** either the sentinel-written final review above
or an explicit user message asking you to stop or change
direction.

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
- Loop behaviour identical to `/draft-adr`, including the
  sentinel-driven stop: before writing a reply, check the newest
  `docs/dev/plans/<slug>_review-N.md` for the final-review
  sentinel and stop if present. Otherwise read the review, update
  the plan, write `<slug>_reply-N.md`, poll for the next review.
  **No commits and no file deletions in this loop.**

**Termination:** either the sentinel-driven stop or an explicit
user message asking you to stop or change direction.

### `/review-plan [<slug>]`

Act as the implementation-plan reviewer. Same loop as `/review-adr`,
applied to an implementation plan.

- Target: if `<slug>` is given, target
  `docs/dev/plans/<slug>.md`. Otherwise monitor `docs/dev/plans/`
  for the newest plan matching the most recent `/draft-plan`
  cycle.
- Static reads only — same "no tests / lint / build / formatters /
  pixi" rule applies during plan reviews.
- Loop and termination identical to `/review-adr`, including the
  final-review-sentinel rule: when all findings are addressed,
  write the final review with `**No findings. Ready to commit.**`
  as the first body line and stop. **Do not delete any review or
  reply file and do not commit anything** — those steps belong to
  `/implement-plan`.
- A bare `/review-plan` is still enough to start the full reviewer
  loop. If a target plan already exists, write the first static review
  and then immediately wait for `<slug>_reply-1.md`; do not return a
  final answer that implies the task is complete after the first review.

### `/implement-plan [<slug>]`

Clean up the review/reply deliberation history, commit the latest
ADR + plan, then execute the plan's Phase 1 implementation steps
autonomously. This is the only shortcut in this section that
deletes files and commits changes.

**Setup (once):**

1. Ask the user, **in one batch**, to grant every permission this
   shortcut will need so the implementation phase runs without
   per-step prompts. List explicitly:
   - `Bash` (general, including `run_in_background`) for `git`,
     `ls`, `grep`, `find`, `until`, `sleep`, and any plan-step
     command (`pixi run notebook-prepare`, etc.).
   - `Read` / `Edit` / `Write` on `src/`, `tests/`,
     `docs/dev/adrs/`, `docs/dev/plans/`, `docs/docs/tutorials/`,
     `pyproject.toml`, `pixi.toml`, `pixi.lock`, and any other
     paths the plan's `Concrete files likely to change` section
     enumerates.
   - `git rm`, `git add`, `git commit` (subsumed under Bash).
   - Cite this section so the user knows the scope.
2. **Do not** run tests, lint, `pixi run fix`, `pixi run check`,
   or the integration/script-test suites during this shortcut —
   those belong to the plan's Phase 2 verification gate and run
   only after the Phase 1 review gate the plan defines.
3. Stay on the current branch.
4. Identify targets:
   - **Plan**: if `<slug>` is given, target
     `docs/dev/plans/<slug>.md`. Otherwise pick the most recently
     modified plan in `docs/dev/plans/` whose stem matches the
     current branch slug.
   - **ADR**: derive from the plan's `## ADR` reference. The ADR
     usually lives in `docs/dev/adrs/suggestions/<slug>.md` at
     this point (a Phase 1 plan step typically promotes it to
     `accepted/`); accept either location.

**Phase A — cleanup + commits (two atomic commits):**

1. **ADR commit.**
   - `git rm` every `docs/dev/adrs/<dir>/<adr-slug>_review-*.md`
     and `<adr-slug>_reply-*.md` next to the ADR.
   - `git add docs/dev/adrs/<dir>/<adr-slug>.md`.
   - Commit with message `Add <adr-slug> ADR suggestion` (or
     `Promote <adr-slug> ADR to accepted` if the ADR was already
     under `accepted/`).
2. **Plan commit.**
   - `git rm` every `docs/dev/plans/<plan-slug>_review-*.md` and
     `<plan-slug>_reply-*.md`.
   - `git add docs/dev/plans/<plan-slug>.md`.
   - Commit with message `Add <plan-slug> implementation plan`.

If the ADR or plan has no review/reply siblings (e.g. the user
drafted it directly without running the loop), skip the `git rm`
step but still stage + commit the clean artifact.

**Phase B — implementation:**

3. Parse the plan's `## Implementation steps (Phase 1)` section
   in order. Each `- [ ] **P1.X — <summary>**` item is one
   atomic commit. For each step in turn:
   1. Read the step body to identify the files and edits.
   2. Apply the edits exactly as the step prescribes. If the
      step says to run a build-step command (e.g.
      `pixi run notebook-prepare`, `pixi lock`), run it — those
      are part of the plan, not Phase 2 verification.
   3. Stage the files the step enumerates with explicit paths
      (per **Commits** rule "Stage only the files modified for
      the step"). Do not stage unrelated dirty files.
   4. Commit with the suggested commit message from the step
      (the `Commit:` line). Edit the `- [ ]` checkbox to `- [x]`
      in the plan file before staging, so the checklist tracks
      progress, and include the checklist update in the same
      commit.
4. **Phase 1 review gate.** The plan's final P1 step is always
   "Phase 1 review gate. No code change. Stop and request user
   review." When you reach that step, mark it `[x]`, commit the
   checklist update alone, and **stop**. Report:
   - How many P1 commits landed.
   - The current branch and tip commit hash.
   - That Phase 2 verification (`pixi run fix`, `pixi run check`,
     `pixi run unit-tests`, `pixi run integration-tests`,
     `pixi run script-tests`) is still pending and is the user's
     next action.

**If a step fails:** stop immediately, do not skip ahead, report
the failure with the step ID and the error. Do not run Phase 2
verification commands as a debugging tool — fix the step or wait
for user input.

**Permissions / approval flow.** The setup-step permission batch
is the only prompt this shortcut emits during normal operation.
If the plan introduces a step that requires a permission the user
did not pre-approve (e.g. an `npm` invocation when the upfront
batch only covered `pixi`), pause at that step and ask for the
extra grant rather than blocking on a single tool call. Resume
the loop once granted.
