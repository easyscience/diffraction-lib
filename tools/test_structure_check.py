"""Check that the unit-test directory mirrors the source directory.

Every non-``__init__.py`` Python module under ``src/easydiffraction/``
should have a corresponding ``test_<module>.py`` file under
``tests/unit/easydiffraction/`` in the matching sub-package.  Modules
that are explicitly excluded (vendored code, ``__main__``, etc.) are
skipped.

The script recognises two common test-layout patterns:

1. **Direct mirror** — ``src/.../foo.py`` → ``tests/.../test_foo.py``
   (or ``test_foo_*.py`` for supplementary coverage files).
2. **Parent-level roll-up** — for category packages that contain only
   ``default.py``, ``factory.py``, etc., a single
   ``test_<package_name>.py`` at the parent level counts as coverage
   for every module inside that package.

Explicit name aliases (e.g. ``variable.py`` tested by
``test_parameters.py``) are declared in ``KNOWN_ALIASES``.

Usage::

    python tools/test_structure_check.py            # exit 1 on mismatch
    python tools/test_structure_check.py --verbose   # list all mappings

Exit code 0 when the test tree is in sync, 1 otherwise.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from _src_tree import TEST_ROOT
from _src_tree import iter_source_modules

# ---------------------------------------------------------------------------
# Known aliases: src module stem → accepted test stem(s)
# ---------------------------------------------------------------------------

# When the test file uses a different name than the source module, add
# the mapping here.  Keys are source stems, values are sets of accepted
# test stems (without ``test_`` prefix or ``.py`` suffix).
KNOWN_ALIASES: dict[str, set[str]] = {
    'singleton': {'singletons'},
    'variable': {'parameters'},
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _find_existing_tests(src_rel: Path) -> list[Path]:
    """Return existing test files that cover a source module.

    Search strategy (in order):

    1. Same directory: ``test_<name>.py`` or ``test_<name>_*.py``.
    2. Known aliases: alternative accepted test stems.
    3. Parent-level roll-up: ``test_<package>.py`` one level up (covers
       ``<package>/default.py``, ``<package>/factory.py``, etc.).
    """
    base_name = src_rel.stem  # e.g. factory, default, variable
    parent = src_rel.parent   # e.g. core, analysis/categories/aliases

    matches: list[Path] = []

    # --- Strategy 1: direct mirror in the same directory ---
    test_dir = TEST_ROOT / parent
    if test_dir.is_dir():
        for f in sorted(test_dir.iterdir()):
            if not f.is_file() or f.suffix != '.py':
                continue
            if f.stem == f'test_{base_name}' or f.stem.startswith(f'test_{base_name}_'):
                matches.append(f.relative_to(TEST_ROOT))

    # --- Strategy 2: known aliases ---
    if not matches and base_name in KNOWN_ALIASES:
        for alias in KNOWN_ALIASES[base_name]:
            if test_dir.is_dir():
                for f in sorted(test_dir.iterdir()):
                    if not f.is_file() or f.suffix != '.py':
                        continue
                    if f.stem == f'test_{alias}' or f.stem.startswith(f'test_{alias}_'):
                        matches.append(f.relative_to(TEST_ROOT))

    # --- Strategy 3: parent-level roll-up ---
    # For src/.../categories/<cat_pkg>/default.py, check if
    # tests/.../categories/test_<cat_pkg>.py exists.
    if not matches and parent.parts:
        package_name = parent.parts[-1]  # e.g. aliases, experiment_type
        parent_test_dir = TEST_ROOT / parent.parent
        if parent_test_dir.is_dir():
            for f in sorted(parent_test_dir.iterdir()):
                if not f.is_file() or f.suffix != '.py':
                    continue
                if f.stem == f'test_{package_name}' or f.stem.startswith(f'test_{package_name}_'):
                    matches.append(f.relative_to(TEST_ROOT))

    return matches


def _expected_test_path(src_rel: Path) -> Path:
    """Map a source module to its primary expected test file path."""
    return src_rel.parent / f'test_{src_rel.stem}.py'


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(
        description='Check unit-test directory mirrors src/ structure.',
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Print every mapping, not just missing tests.',
    )
    args = parser.parse_args()

    modules = iter_source_modules()
    missing: list[tuple[Path, Path]] = []
    covered: list[tuple[Path, list[Path]]] = []

    for src_rel in modules:
        existing = _find_existing_tests(src_rel)
        if existing:
            covered.append((src_rel, existing))
        else:
            expected = _expected_test_path(src_rel)
            missing.append((src_rel, expected))

    # --- Report ---
    if args.verbose:
        print('Covered modules:')
        for src_rel, tests in covered:
            tests_str = ', '.join(str(t) for t in tests)
            print(f'  ✅ {src_rel}  →  {tests_str}')
        print()

    if missing:
        print('Missing test files:')
        for src_rel, expected in missing:
            print(f'  ❌ {src_rel}  →  expected {expected}')
        print()
        total = len(modules)
        n_covered = len(covered)
        print(f'Coverage: {n_covered}/{total} modules have tests '
              f'({100 * n_covered / total:.0f}%)')
        print(f'Missing:  {len(missing)} module(s) without a test file.')
        return 1

    total = len(modules)
    print(f'✅ All {total} source modules have corresponding test files.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
