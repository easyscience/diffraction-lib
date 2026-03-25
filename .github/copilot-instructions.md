# Copilot Instructions for EasyDiffraction

## Project Context

- Python library for crystallographic diffraction analysis, such as refinement
  of the structural model against experimental data.
- Support for
  - sample_form: powder and single crystal
  - beam_mode: time-of-flight and constant wavelength
  - radiation_probe: neutron and x-ray
  - scattering_type: bragg and total scattering
- Calculations are done using external calculation libraries:
  - `cryspy` for Bragg diffraction
  - `crysfml` for Bragg diffraction
  - `pdffit2` for Total scattering
- Follow CIF naming conventions where possible. In some places, we deviate for
  better API design, but we try to keep the spirit of the CIF names.
- Reusing the concept of datablocks and categories from CIF. We have
  `DatablockItem` (structure or experiment) and `DatablockCollection`
  (collection of structures or experiments), as well as `CategoryItem` (single
  categories in CIF) and `CategoryCollection` (loop categories in CIF).
- Metadata via frozen dataclasses: `TypeInfo`, `Compatibility`,
  `CalculatorSupport`.
- The API is designed for scientists who use EasyDiffraction as a final product
  in a user-friendly, intuitive way. The target users are not software
  developers and may have little or no Python experience. The design is not
  oriented toward developers building their own tooling on top of the library,
  although experienced developers will find their own way. Prioritize
  discoverability, clear error messages, and safe defaults so that
  non-programmers are not stuck by standard API conventions.
- This project must be developed to be as error-free as possible, with the same
  rigour applied to critical software (e.g. nuclear-plant control systems).
  Every code path must be tested, edge cases must be handled explicitly, and
  silent failures are not acceptable.

## Code Style

- Use snake_case for functions and variables, PascalCase for classes, and
  UPPER_SNAKE_CASE for constants.
- Use `from __future__ import annotations` in every module.
- Type-annotate all public function signatures.
- Docstrings on all public classes and methods (Google style).
- Prefer flat over nested, explicit over clever.
- Write straightforward code; do not add defensive checks for unlikely edge
  cases.
- Prefer composition over deep inheritance.
- One class per file when the class is substantial; group small related classes.
- Avoid `**kwargs`; use explicit keyword arguments for clarity, autocomplete,
  and typo detection.
- Do not use string-based dispatch (e.g. `getattr(self, f'_{name}')`) to route
  to attributes or methods. Instead, write explicit named methods (e.g.
  `_set_sample_form`, `_set_beam_mode`). This keeps the code greppable,
  autocomplete-friendly, and type-safe.
- Public parameters and descriptors are either **editable** (property with both
  getter and setter) or **read-only** (property with getter only). If internal
  code needs to mutate a read-only property, add a private `_set_<name>` method
  instead of exposing a public setter.

## Architecture

- Eager imports unless profiling proves a lazy alternative is needed.
- No `pkgutil` / `importlib` auto-discovery patterns.
- No background/daemon threads.
- No monkey-patching or runtime class mutation.
- Do not use `__all__` in modules; instead, rely on explicit imports in
  `__init__.py` to control the public API.
- Do not use redundant `import X as X` aliases in `__init__.py`. Use plain
  `from module import X`.
- Concrete classes use `@Factory.register` decorators. To trigger registration,
  each package's `__init__.py` must explicitly import every concrete class (e.g.
  `from .chebyshev import ChebyshevPolynomialBackground`). When adding a new
  concrete class, always add its import to the corresponding `__init__.py`.
- Switchable categories (those whose implementation can be swapped at runtime
  via a factory) follow a fixed naming convention on the owner (experiment,
  structure, or analysis): `<category>` (read-only property), `<category>_type`
  (getter + setter), `show_supported_<category>_types()`,
  `show_current_<category>_type()`. The owner class owns the type setter and the
  show methods; the show methods delegate to `Factory.show_supported(...)`
  passing context. Every factory-created category must have this full API, even
  if only one implementation exists today.
- Categories are flat siblings within their owner (datablock or analysis). A
  category must never be a child of another category of a different type.
  Categories can reference each other via IDs, but not via parent-child nesting.
- Every finite, closed set of values (factory tags, experiment axes, category
  descriptors with enumerated choices) must use a `(str, Enum)` class. Internal
  code compares against enum members, never raw strings.
- Keep `core/` free of domain logic — only base classes and utilities.
- Don't introduce a new abstraction until there is a concrete second use case.
- Don't add dependencies without asking.

## Changes

- Before implementing any structural or design change (new categories, new
  factories, switchable-category wiring, new datablocks, CIF serialisation
  changes), read `docs/architecture/architecture.md` to understand the current
  design choices and conventions. Follow the documented patterns (factory
  registration, switchable-category naming, metadata classification, etc.) to
  stay consistent with the rest of the codebase. For localised bug fixes or test
  updates, the rules in this file are sufficient.
- The project is in beta; do not keep legacy code or add deprecation warnings.
  Instead, update tests and tutorials to follow the current API.
- Minimal diffs: don't rewrite working code just to reformat it.
- Never remove or replace existing functionality as part of a new change without
  explicit confirmation. If a refactor would drop features, options, or
  configurations, highlight every removal and wait for approval.
- Fix only what's asked; flag adjacent issues as comments, don't fix them
  silently.
- Don't add new features or refactor existing code unless explicitly asked.
- Do not remove TODOs or comments unless the change fully resolves them.
- When renaming, grep the entire project (code, tests, tutorials, docs).
- Every change should be atomic and self-contained, small enough to be described
  by a single commit message. Make one change, suggest the commit message, then
  stop and wait for confirmation before starting the next change.
- When in doubt, ask for clarification before making changes.

## Workflow

- All open issues, design questions, and planned improvements are tracked in
  `docs/architecture/issues_open.md`, ordered by priority. When an issue is
  fully implemented, move it from that file to
  `docs/architecture/issues_closed.md`. When the resolution affects the
  architecture, update the relevant sections of
  `docs/architecture/architecture.md`.
- After changes, run linting and formatting fixes with `pixi run fix`. Do not
  check what was auto-fixed, just accept the fixes and move on.
- After changes, run unit tests with `pixi run unit-tests`.
- After changes, run integration tests with `pixi run integration-tests`.
- Suggest a concise commit message (as a code block) after each change (less
  than 72 characters, imperative mood, without prefixing with the type of
  change). E.g.:
  - Add ChebyshevPolynomialBackground class
  - Implement background_type setter on Experiment
  - Standardize switchable-category naming convention
