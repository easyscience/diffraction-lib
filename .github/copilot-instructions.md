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
  named methods (`_set_sample_form`, `_set_beam_mode`).
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
- Switchable categories (factory-swappable at runtime) follow this fixed
  API on the owner (experiment / structure / analysis): `<category>`
  (read-only), `<category>_type` (getter+setter),
  `show_supported_<category>_types()`, `show_current_<category>_type()`.
  The owner owns the type setter and show methods; show methods delegate
  to `Factory.show_supported(...)`. Required even if only one
  implementation exists.
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
  `docs/architecture/architecture.md` §10 for the full strategy.
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
  `docs/architecture/architecture.md` and follow documented patterns.
  Localised bug fixes or test updates need only this file.
- Project is in beta: no legacy shims, no deprecation warnings — update
  tests and tutorials to the current API.
- Minimal diffs; don't reformat working code. Fix only what's asked;
  flag adjacent issues as comments. Don't add features or refactor
  unless asked. Don't remove TODOs or comments unless the change fully
  resolves them.
- Never remove or replace existing functionality without explicit
  confirmation — highlight every removal and wait for approval.
- When renaming, grep the entire project (code, tests, tutorials, docs).
- Each change is atomic and single-commit-sized: make one change,
  suggest the commit message, then stop and wait for confirmation.
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

- **Phase 1 — Implementation.** Code, docs, and architecture updates
  only. Do not create or run tests unless the user explicitly asks. When
  done, present for review and iterate until approved.
- **Phase 2 — Verification.** Add/update tests, then run `pixi run fix`,
  `pixi run check`, `pixi run unit-tests`, `pixi run integration-tests`,
  `pixi run script-tests`.

Notes:

- `pixi run fix` regenerates `docs/architecture/package-structure-*.md`
  automatically — never edit those by hand. Don't review auto-fixes;
  accept and move on. Then `pixi run check` until clean.
- Open issues / design questions / planned improvements live in
  `docs/architecture/issues_open.md` (priority-ordered). On resolution,
  move to `docs/architecture/issues_closed.md` and update
  `architecture.md` if affected.

### Planning

When asked to create a plan:

- First gather enough repository context to make the plan concrete. Ask
  all ambiguous or unclear questions in one concise batch; record
  unresolved questions in the plan if the user wants it saved before
  answering them.
- Save plans as `docs/dev/plan_<feature-name>.md` (lowercase,
  dash-separated, e.g. `plan_background-refactor.md`). Use the same
  `<feature-name>` for the implementation branch
  (`feature/<feature-name>`). Do not push the branch unless asked.
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
- End every plan with a "Suggested Pull Request" section containing a
  short PR title and a brief end-user-oriented description. Keep this
  section non-technical enough for scientists and other users to
  understand the benefit. Update it during implementation if extra
  approved changes become important enough to mention in the PR title or
  description.
