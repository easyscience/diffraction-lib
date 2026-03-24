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
- Avoid `**kwargs`; use explicit keyword arguments for clarity, autocomplete, and
  typo detection.

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
- Keep `core/` free of domain logic — only base classes and utilities.
- Don't introduce a new abstraction until there is a concrete second use case.
- Don't add dependencies without asking.

## Changes

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
- Every change should be atomic and self-contained; it should correspond to a
  commit message that describes the change clearly.
- When in doubt, ask for clarification before making changes.

## Workflow

- Run `pixi run unit-tests` only when I ask.
- Suggest a concise commit message after each change.
