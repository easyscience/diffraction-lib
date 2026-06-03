# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tutorial-corpus regression for Wyckoff-letter detection.

The tutorials declare explicit Wyckoff letters for known structures, so
each declared letter is ground truth. This test re-derives the letter
from the site's coordinates and space group and asserts it matches the
declared one -- broad, real-world coverage that also guards against
regressions whenever the tutorials change. It parses the tutorial
sources statically (no execution / fitting), so it stays fast and does
not depend on a calculation engine.
"""

import ast
import pathlib

from easydiffraction.crystallography import crystallography as ecr

_TUTORIALS_DIR = pathlib.Path(__file__).resolve().parents[2] / 'docs' / 'docs' / 'tutorials'


def _string_assignment(tree, attr_name):
    """Return the unique str assigned to ``*.<attr_name>`` or ``None``.

    Returns ``None`` when the attribute is assigned zero or several
    times, so callers can skip ambiguous (multi-structure) tutorials.
    """
    values = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if (
                isinstance(target, ast.Attribute)
                and target.attr == attr_name
                and isinstance(node.value, ast.Constant)
                and isinstance(node.value.value, str)
            ):
                values.append(node.value.value)
    if len(values) == 1:
        return values[0]
    return None


def _wyckoff_declarations(tree):
    """Yield ``(label, letter, (x, y, z))`` for create() calls with a letter."""
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)):
            continue
        if node.func.attr != 'create':
            continue
        kwargs = {
            kw.arg: kw.value.value
            for kw in node.keywords
            if kw.arg is not None and isinstance(kw.value, ast.Constant)
        }
        if 'wyckoff_letter' not in kwargs:
            continue
        coords = (
            float(kwargs.get('fract_x', 0.0)),
            float(kwargs.get('fract_y', 0.0)),
            float(kwargs.get('fract_z', 0.0)),
        )
        yield kwargs.get('label', '?'), kwargs['wyckoff_letter'], coords


def _corpus():
    """Collect ``(tutorial, name_hm, code, label, letter, coords)`` rows."""
    rows = []
    for path in sorted(_TUTORIALS_DIR.glob('*.py')):
        tree = ast.parse(path.read_text(encoding='utf-8'))
        name_hm = _string_assignment(tree, 'name_h_m')
        if name_hm is None:
            # No structure, or several structures we cannot unambiguously
            # associate with create() calls: skip this tutorial.
            continue
        code = _string_assignment(tree, 'it_coordinate_system_code')
        for label, letter, coords in _wyckoff_declarations(tree):
            rows.append((path.name, name_hm, code, label, letter, coords))
    return rows


def test_tutorial_declared_letters_are_reproduced_by_detection():
    rows = _corpus()
    # Guard against a silently empty corpus (e.g. parser drift): the
    # tutorials are known to declare explicit Wyckoff letters.
    assert rows, 'no tutorial Wyckoff-letter declarations were found'

    mismatches = []
    for tutorial, name_hm, code, label, letter, coords in rows:
        detected = ecr.detect_wyckoff_position(name_hm, code, coords)
        if detected is None or detected.letter != letter:
            found = None if detected is None else detected.letter
            mismatches.append((tutorial, label, name_hm, coords, letter, found))

    assert not mismatches, mismatches
