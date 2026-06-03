# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tutorial-corpus regression for Wyckoff-letter detection.

Each tutorial structure has a known Wyckoff letter for every site, so the
letter is ground truth. This test re-derives the letter from the site's
coordinates and space group and asserts it matches the known one -- broad,
real-world coverage that also guards against regressions whenever the
tutorials change.

Coverage comes from two sources:

1. Tutorials that still declare ``wyckoff_letter`` explicitly are parsed
   statically (no execution / fitting) and checked directly.
2. Many tutorials were switched to rely on auto-detection (the explicit
   letters were removed from the source). Their original declarations are
   preserved here as an explicit ``_GROUND_TRUTH`` table so the regression
   still exercises those structures -- including the R-3m coupled special
   position ``(x, -x, z)`` from ed-6 that motivated the canonical-template
   work.
"""

import ast
import pathlib

from easydiffraction.crystallography import crystallography as ecr

_TUTORIALS_DIR = pathlib.Path(__file__).resolve().parents[2] / 'docs' / 'docs' / 'tutorials'

# Known (space group, coordinate code, fractional coordinates, Wyckoff
# letter) for tutorial sites that no longer declare the letter in source
# (they now exercise auto-detection). Detection must reproduce each letter.
_GROUND_TRUTH = [
    ('F d -3 m', '1', (0.0, 0.0, 0.0), 'a'),
    ('F m -3 m', '1', (0.0, 0.0, 0.0), 'a'),
    ('F m -3 m', '1', (0.5, 0.5, 0.5), 'b'),
    ('I 21 3', '1', (0.0851, 0.0851, 0.0851), 'a'),
    ('I 21 3', '1', (0.1377, 0.3054, 0.1195), 'c'),
    ('I 21 3', '1', (0.2521, 0.2521, 0.2521), 'a'),
    ('I 21 3', '1', (0.3625, 0.3633, 0.1867), 'c'),
    ('I 21 3', '1', (0.4612, 0.4612, 0.4612), 'a'),
    ('I 21 3', '1', (0.4663, 0.0, 0.25), 'b'),
    ('P m -3 m', '1', (0.0, 0.0, 0.0), 'a'),
    ('P m -3 m', '1', (0.0, 0.5, 0.5), 'c'),
    ('P m -3 m', '1', (0.5, 0.5, 0.5), 'b'),
    ('P n m a', 'abc', (0.0, 0.0, 0.0), 'a'),
    ('P n m a', 'abc', (0.0654, 0.25, 0.684), 'c'),
    ('P n m a', 'abc', (0.0811, 0.0272, 0.8086), 'd'),
    ('P n m a', 'abc', (0.091, 0.25, 0.771), 'c'),
    ('P n m a', 'abc', (0.094, 0.25, 0.429), 'c'),
    ('P n m a', 'abc', (0.164, 0.032, 0.28), 'd'),
    ('P n m a', 'abc', (0.1876, 0.25, 0.167), 'c'),
    ('P n m a', 'abc', (0.1935, 0.25, 0.5432), 'c'),
    ('P n m a', 'abc', (0.279, 0.25, 0.985), 'c'),
    ('P n m a', 'abc', (0.448, 0.25, 0.217), 'c'),
    ('P n m a', 'abc', (0.9082, 0.25, 0.5954), 'c'),
    ('R -3 m', 'h', (0.0, 0.0, 0.197), 'c'),
    ('R -3 m', 'h', (0.0, 0.0, 0.5), 'b'),
    ('R -3 m', 'h', (0.13, -0.13, 0.08), 'h'),
    ('R -3 m', 'h', (0.21, -0.21, 0.06), 'h'),
    ('R -3 m', 'h', (0.5, 0.0, 0.0), 'e'),
]


def _const(node):
    """Return a literal value for a Constant or a negated Constant.

    Returns ``None`` for any other node so non-literal arguments are
    ignored. Handles negative numeric literals such as ``-0.21``, which
    parse as ``UnaryOp(USub, Constant)`` rather than a bare ``Constant``.
    """
    if isinstance(node, ast.Constant):
        return node.value
    if (
        isinstance(node, ast.UnaryOp)
        and isinstance(node.op, ast.USub)
        and isinstance(node.operand, ast.Constant)
    ):
        return -node.operand.value
    return None


def _string_assignment(tree, attr_name):
    """Return the unique str assigned to ``*.<attr_name>`` or ``None``.

    Returns ``None`` when the attribute is assigned zero or several
    times, so callers can skip ambiguous (multi-structure) tutorials.
    """
    values = [
        _const(node.value)
        for node in ast.walk(tree)
        if isinstance(node, ast.Assign) and isinstance(_const(node.value), str)
        for target in node.targets
        if isinstance(target, ast.Attribute) and target.attr == attr_name
    ]
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
            kw.arg: _const(kw.value)
            for kw in node.keywords
            if kw.arg is not None and _const(kw.value) is not None
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
    # Guard against a silently empty corpus (e.g. parser drift): some
    # tutorials still declare explicit Wyckoff letters.
    assert rows, 'no tutorial Wyckoff-letter declarations were found'

    mismatches = []
    for tutorial, name_hm, code, label, letter, coords in rows:
        detected = ecr.detect_wyckoff_position(name_hm, code, coords)
        if detected is None or detected.letter != letter:
            found = None if detected is None else detected.letter
            mismatches.append((tutorial, label, name_hm, coords, letter, found))

    assert not mismatches, mismatches


def test_ground_truth_letters_are_reproduced_by_detection():
    # Structures whose explicit letters were removed in favour of
    # auto-detection are covered here so the regression still exercises
    # them (notably the R-3m coupled special position).
    mismatches = []
    for name_hm, code, coords, letter in _GROUND_TRUTH:
        detected = ecr.detect_wyckoff_position(name_hm, code, coords)
        if detected is None or detected.letter != letter:
            found = None if detected is None else detected.letter
            mismatches.append((name_hm, code, coords, letter, found))

    assert not mismatches, mismatches
