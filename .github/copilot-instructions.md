# Copilot Instructions for EasyDiffraction

## Project Context

- Python library for crystallographic diffraction analysis (refining
  structural models against experimental data).
- Axes: `sample_form` (powder, single crystal), `beam_mode` (time-of-
  flight, constant wavelength), `radiation_probe` (neutron, x-ray),
  `scattering_type` (bragg, total).
- Calculation backends: `cryspy` and `crysfml` (Bragg), `pdffit2` (total
  scattering).
- Follow CIF naming conventions; deviate only for clearly better API.
- CIF concepts map to: `DatablockItem` / `DatablockCollection` and
  `CategoryItem` / `CategoryCollection` (loops).
- Metadata via frozen dataclasses: `TypeInfo`, `Compatibility`,
  `CalculatorSupport`.
- Audience: scientists, often non-programmers. Prioritize
  discoverability, clear errors, safe defaults over developer
  ergonomics.
- Critical-software rigor: every code path tested, edge cases handled
  explicitly, no silent failures.

## Code Style

- snake_case (functions/vars), PascalCase (classes), UPPER_SNAKE_CASE
  (constants).
- `from __future__ import annotations` in every module.
- Type-annotate all public signatures.
- Numpy-style docstrings on all public classes/methods, with Parameters
  / Returns / Raises where applicable. Summary is one line ≤72 chars
  (`max-doc-length`); shorten wording rather than wrap.
- Flat over nested, explicit over clever. No defensive checks for
  unlikely edge cases. Composition over deep inheritance.
- One class per file when substantial; group small related classes.
- No `**kwargs` — use explicit keyword arguments.
- No string-based dispatch (e.g. `getattr(self, f'_{name}')`); write
  explicit named methods (`_set_sample_form`, `_set_beam_mode`).
- Public attrs are either editable (getter+setter property) or read-only
  (getter only). For internal mutation of read-only props, add a private
  `_set_<name>` method, not a public setter.
- Lint complexity thresholds in `pyproject.toml` (`max-args`,
  `max-branches`, `max-statements`, `max-locals`, `max-nested-blocks`,
  …) are guardrails. A violation means refactor (extract helpers,
  parameter objects, flatten). Do not raise thresholds, add `# noqa`, or
  otherwise silence them. For complex refactors touching many lines or
  public API, propose a plan and wait for approval.

## Architecture

- Eager top-of-module imports by default. Lazy imports only to break
  circular deps or keep `core/` free of heavy imports on rarely-called
  paths (e.g. `help()`).
- No `pkgutil` / `importlib` auto-discovery, no background threads, no
  monkey-patching or runtime class mutation.
- No `__all__`; control public API via explicit `__init__.py` imports.
- No redundant `import X as X` aliases — use plain
  `from module import X`.
- Concrete classes use `@Factory.register`. Each package's `__init__.py`
  must explicitly import every concrete class to trigger registration.
  Always add new concrete classes to the corresponding `__init__.py`.
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
  descriptors) uses a `(str, Enum)` class; compare against members, not
  raw strings.
- Keep `core/` free of domain logic (base classes and utilities only).
- Don't introduce abstractions before a concrete second use case.
- Don't add dependencies without asking.

## Tutorials

- Notebooks in `docs/docs/tutorials/*.ipynb` are generated artifacts.
  Edit only the corresponding `*.py`, then run
  `pixi run notebook-prepare`.

## Testing

- Every new module, class, or bug fix ships with tests. See
  `docs/architecture/architecture.md` §10 for the full strategy.
- Unit tests mirror the source tree:
  `src/easydiffraction/<pkg>/<mod>.py` →
  `tests/unit/easydiffraction/<pkg>/test_<mod>.py`. Verify with
  `pixi run test-structure-check`.
- Category packages with only `default.py`/`factory.py` may use one
  parent-level `test_<package>.py`.
- Supplementary tests: `test_<mod>_coverage.py`.
- Tests expecting `log.error()` to raise must `monkeypatch` Logger to
  RAISE mode (another test may have leaked WARN mode).
- `@typechecked` setters raise `typeguard.TypeCheckError`, not
  `TypeError`.
- No test-ordering dependence, no network, no sleeping, no real
  calculation engines in unit tests.

## Changes

- Before any structural/design change (new categories, factories,
  switchable-category wiring, datablocks, CIF serialisation), read
  `docs/architecture/architecture.md` and follow documented patterns.
  Localised bug fixes or test updates need only this file.
- Project is in beta: no legacy shims, no deprecation warnings — update
  tests and tutorials to current API.
- Minimal diffs; don't reformat working code.
- Never remove or replace existing functionality without explicit
  confirmation. Highlight every removal and wait for approval.
- Fix only what's asked; flag adjacent issues as comments.
- Don't add features or refactor unless asked. Don't remove TODOs or
  comments unless the change fully resolves them.
- When renaming, grep the entire project (code, tests, tutorials, docs).
- Each change is atomic, single-commit-sized. Make one change, suggest
  the commit message, then stop and wait for confirmation.
- When in doubt, ask.

## Workflow

- Two-phase workflow for non-trivial changes:
  - **Phase 1 — Implementation:** code, docs, architecture updates. Do
    not create new tests or run existing tests. Present for review and
    iterate until approved.
  - **Phase 2 — Verification:** add/update tests, then run
    `pixi run fix`, `pixi run check`, `pixi run unit-tests`,
    `pixi run integration-tests`, `pixi run script-tests`.
- Open issues / design questions / planned improvements live in
  `docs/architecture/issues_open.md` (priority-ordered). On resolution,
  move to `docs/architecture/issues_closed.md` and update
  `architecture.md` if affected.
- `pixi run fix` regenerates `docs/architecture/package-structure-*.md`
  automatically — never edit those by hand. Don't review auto-fixes;
  accept and move on. Then `pixi run check` until clean.
- Suggest a commit message (code block, ≤72 chars, imperative mood, no
  type prefix) after each change. E.g.:
  - Add ChebyshevPolynomialBackground class
  - Implement background_type setter on Experiment
  - Standardize switchable-category naming convention
