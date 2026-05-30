# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""ASCII terminal renderer: a schematic single-cell structure view."""

from __future__ import annotations

import numpy as np

from easydiffraction.display.structure.renderers.base import StructureRendererBase
from easydiffraction.display.structure.scene import StructureScene

Rgb = tuple[int, int, int]

GLYPH_RAMP = ('·', '•', '●', '⬤')
GRID_WIDTH = 56
PAD = 2
CHAR_ASPECT = 0.5  # terminal cells are roughly twice as tall as wide


def _ansi256(rgb: Rgb) -> int:
    """Map an RGB triple to the nearest xterm-256 cube colour."""
    return 16 + 36 * round(rgb[0] / 255 * 5) + 6 * round(rgb[1] / 255 * 5) + round(rgb[2] / 255 * 5)


def _tint(rgb: Rgb, text: str) -> str:
    return f'\x1b[38;5;{_ansi256(rgb)}m{text}\x1b[0m'


def _collect_atoms(scene: StructureScene):
    """Flatten every drawable atom to (centre, radius, colour, label)."""
    atoms = [(a.centre, a.radius, a.colour, a.label) for a in scene.atoms]
    atoms += [(s.centre, s.radius, s.wedges[0].colour, s.label) for s in scene.occupancy_spheres]
    atoms += [(e.centre, float(np.mean(e.semi_axes)) or 0.4, e.colour, e.label)
              for e in scene.ellipsoids]
    return atoms


class AsciiStructureRenderer(StructureRendererBase):
    """Reduced-fidelity terminal renderer (one schematic cell)."""

    SUPPORTED = frozenset({'atoms', 'cell', 'axes'})

    def supported_features(self) -> frozenset[str]:
        """Return the features the ASCII engine can draw."""
        return self.SUPPORTED

    def render(self, scene: StructureScene, *, features: frozenset[str]) -> str:
        """Render a schematic ASCII view and announce 3D-only features."""
        atoms = _collect_atoms(scene)
        basis = np.array(scene.cell_basis, dtype=float)
        lengths = [float(np.linalg.norm(v)) for v in basis]
        h_vec = basis[int(np.argmax(lengths))]
        v_vec = basis[int(np.argmin(lengths))]
        h_hat = h_vec / (np.linalg.norm(h_vec) or 1.0)
        v_hat = v_vec / (np.linalg.norm(v_vec) or 1.0)

        def project(point) -> tuple[float, float]:
            p = np.array(point, dtype=float)
            return float(p @ h_hat), float(p @ v_hat)

        corners = [project((0, 0, 0)), project(h_vec), project(v_vec), project(h_vec + v_vec)]
        points = [project(a[0]) for a in atoms] + corners
        grid, place = _make_grid(points)

        if 'cell' in features:
            _draw_cell(grid, place, corners)
        if 'atoms' in features and atoms:
            _draw_atoms(grid, place, atoms)

        lines = _grid_to_lines(grid)
        if 'axes' in features:
            lines = _annotate_axes(lines)
        text = '\n'.join(lines)
        if 'atoms' in features and atoms:
            text += '\n\n' + _legend(atoms)
        notes = _announcements(scene, features, self.SUPPORTED)
        if notes:
            text += '\n\n' + '\n'.join(notes)
        return text


def _make_grid(points):
    xs = [p[0] for p in points] or [0.0]
    ys = [p[1] for p in points] or [0.0]
    min_x, max_x, min_y, max_y = min(xs), max(xs), min(ys), max(ys)
    span_x = (max_x - min_x) or 1.0
    span_y = (max_y - min_y) or 1.0
    width = GRID_WIDTH
    height = max(8, int((width - 2 * PAD) * span_y / span_x * CHAR_ASPECT))
    grid: dict = {}

    def place(point) -> tuple[int, int]:
        col = PAD + int((point[0] - min_x) / span_x * (width - 1 - 2 * PAD))
        row = PAD + int((max_y - point[1]) / span_y * (height - 1 - 2 * PAD))
        return row, col

    grid['_size'] = (height, width)
    return grid, place


def _draw_line(grid, p0, p1, glyph, colour):
    (r0, c0), (r1, c1) = p0, p1
    steps = max(abs(r1 - r0), abs(c1 - c0)) or 1
    for i in range(steps + 1):
        row = round(r0 + (r1 - r0) * i / steps)
        col = round(c0 + (c1 - c0) * i / steps)
        grid.setdefault((row, col), (glyph, colour))


def _draw_cell(grid, place, corners):
    grey = (150, 150, 150)
    c00, c10, c01, c11 = (place(c) for c in corners)
    for a, b in ((c00, c10), (c01, c11)):
        _draw_line(grid, a, b, '─', grey)
    for a, b in ((c00, c01), (c10, c11)):
        _draw_line(grid, a, b, '│', grey)


def _draw_atoms(grid, place, atoms):
    max_radius = max(a[1] for a in atoms) or 1.0
    for centre, radius, colour, _label in atoms:
        bucket = min(len(GLYPH_RAMP) - 1, int(radius / max_radius * len(GLYPH_RAMP)))
        grid[place(centre)] = (GLYPH_RAMP[bucket], colour)


def _grid_to_lines(grid):
    height, width = grid['_size']
    lines = []
    for row in range(height):
        chars = []
        for col in range(width):
            cell = grid.get((row, col))
            chars.append(_tint(cell[1], cell[0]) if cell else ' ')
        lines.append(''.join(chars).rstrip())
    return lines


def _annotate_axes(lines):
    if lines:
        lines[0] = '  c ↑' + lines[0][5:] if len(lines[0]) > 5 else '  c ↑'
        lines[-1] = lines[-1] + '  → a'
    return lines


def _legend(atoms) -> str:
    seen: dict = {}
    for _centre, radius, colour, label in atoms:
        element = ''.join(ch for ch in label if ch.isalpha()) or label
        seen.setdefault(element, (radius, colour))
    max_radius = max(r for r, _ in seen.values()) or 1.0
    items = []
    for element, (radius, colour) in seen.items():
        bucket = min(len(GLYPH_RAMP) - 1, int(radius / max_radius * len(GLYPH_RAMP)))
        items.append(_tint(colour, f'{GLYPH_RAMP[bucket]} {element}'))
    return 'Legend:  ' + '   '.join(items)


def _announcements(scene, features, supported) -> list[str]:
    notes = []
    skipped = [f for f in ('bonds', 'labels', 'moments') if f in features and f not in supported]
    if skipped:
        notes.append('Shown only by the 3D engines: ' + ', '.join(skipped) + '.')
    if scene.ellipsoids:
        notes.append('ADP ellipsoids are flattened to dots; use a 3D engine for ellipsoids.')
    notes.append('Schematic single-cell view; wider ranges are shown only by the 3D engines.')
    return notes
