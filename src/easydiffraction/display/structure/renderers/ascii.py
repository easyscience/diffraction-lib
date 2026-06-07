# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""ASCII terminal renderer: a schematic single-cell structure view."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np

from easydiffraction.display.structure.renderers.base import StructureRendererBase

Rgb = tuple[int, int, int]
# Grid cell coordinate (row, column) from a placement closure.
Cell = tuple[int, int]
# A projected 2D point (horizontal, vertical) in cell space.
Point2D = tuple[float, float]
# Maps cell coordinates to (glyph, colour); plus a '_size' entry.
Grid = dict

if TYPE_CHECKING:
    from collections.abc import Callable
    from collections.abc import Sequence

    from easydiffraction.display.structure.scene import StructureScene
    from easydiffraction.display.structure.scene import Vec3

    # Coordinates fed to the projection/placement closures.
    Coords = Sequence[float] | np.ndarray
    # A flattened drawable atom: (centre, radius, colour, label).
    Atom = tuple[Vec3, float, Rgb, str]
    # A placement closure mapping coordinates to a grid cell.
    Place = Callable[[Coords], Cell]
    # A 2D projection closure mapping coordinates to a point.
    Project = Callable[[Coords], Point2D]

# Single-width glyphs only: '⬤' (U+2B24) is absent from common
# monospace fonts and falls back to a proportional glyph, which renders
# wider than one cell and pushes the right border out of alignment.
GLYPH_RAMP = ('·', '•', '●')
GRID_WIDTH = 56
PAD = 2
CHAR_ASPECT = 0.5  # terminal cells are roughly twice as tall as wide


def _ansi256(rgb: Rgb) -> int:
    """Map an RGB triple to the nearest xterm-256 cube colour."""
    return (
        16 + 36 * round(rgb[0] / 255 * 5) + 6 * round(rgb[1] / 255 * 5) + round(rgb[2] / 255 * 5)
    )


def _tint(rgb: Rgb, text: str) -> str:
    """Wrap text in an xterm-256 foreground colour escape."""
    return f'\x1b[38;5;{_ansi256(rgb)}m{text}\x1b[0m'


def _collect_atoms(scene: StructureScene) -> list[Atom]:
    """Flatten each drawable atom to (centre, radius, colour, label)."""
    atoms = [(a.centre, a.radius, a.colour, a.label) for a in scene.atoms]
    atoms += [(s.centre, s.radius, s.wedges[0].colour, s.label) for s in scene.occupancy_spheres]
    atoms += [
        (e.centre, float(np.mean(e.semi_axes)) or 0.4, e.colour, e.label) for e in scene.ellipsoids
    ]
    return atoms


@dataclass(frozen=True, slots=True)
class _Orientation:
    """The 2D projection setup for the schematic single-cell view."""

    project: Project
    h_vec: np.ndarray
    v_vec: np.ndarray
    v_idx: int
    h_idx: int


class AsciiStructureRenderer(StructureRendererBase):
    """Reduced-fidelity terminal renderer (one schematic cell)."""

    SUPPORTED = frozenset({'atoms', 'cell', 'axes'})

    def supported_features(self) -> frozenset[str]:
        """Return the features the ASCII engine can draw."""
        return self.SUPPORTED

    @staticmethod
    def _orient(basis: np.ndarray) -> _Orientation:
        """
        Build the projection closure and the in-plane cell axes.

        Match the 3D default orientation by axis length: longest axis
        horizontal, second-longest vertical, shortest the dropped depth
        axis, so the ASCII and 3D engines share the up axis and the
        width-to-height ratio.

        Parameters
        ----------
        basis : np.ndarray
            The 3x3 Cartesian cell basis, one row per cell vector.

        Returns
        -------
        _Orientation
            The projection closure and the in-plane cell axes.
        """
        lengths = [float(np.linalg.norm(v)) for v in basis]
        order = sorted(range(3), key=lambda i: lengths[i], reverse=True)
        h_idx, v_idx = order[0], order[1]
        h_vec = basis[h_idx]
        v_vec = basis[v_idx]
        h_hat = h_vec / (np.linalg.norm(h_vec) or 1.0)
        v_hat = v_vec / (np.linalg.norm(v_vec) or 1.0)

        def project(point: Coords) -> Point2D:
            """Project a Cartesian point onto the in-plane axes."""
            p = np.array(point, dtype=float)
            return float(p @ h_hat), float(p @ v_hat)

        return _Orientation(project, h_vec, v_vec, v_idx, h_idx)

    @staticmethod
    def _annotate_with_axes(
        lines: list[str],
        place: Place,
        corners: list[Point2D],
        v_letter: str,
        h_letter: str,
    ) -> list[str]:
        """
        Add the a/b/c axis labels around the schematic cell.

        Parameters
        ----------
        lines : list[str]
            The rendered grid rows (ANSI-tinted).
        place : Place
            The grid-placement closure from :func:`_make_grid`.
        corners : list[Point2D]
            The four projected cell corners.
        v_letter : str
            The vertical-axis crystallographic letter.
        h_letter : str
            The horizontal-axis crystallographic letter.

        Returns
        -------
        list[str]
            The grid rows with axis labels added.
        """
        cells = [place(c) for c in corners]
        left_col = min(c for _, c in cells)
        bottom_row = max(r for r, _ in cells)
        # Collapse the grid's blank top-padding rows to a single spacer
        # between the vertical-axis label and the cell's top border.
        while len(lines) > 1 and not lines[0] and not lines[1]:
            lines.pop(0)
            bottom_row -= 1
        return _annotate_axes(lines, left_col, bottom_row, v_letter, h_letter)

    def render(self, scene: StructureScene, *, features: frozenset[str]) -> str:
        """
        Render a schematic ASCII view and announce 3D-only features.

        Parameters
        ----------
        scene : StructureScene
            The renderer-neutral primitives to draw.
        features : frozenset[str]
            The content-resolved feature set from the facade.

        Returns
        -------
        str
            The schematic single-cell ASCII view.
        """
        atoms = _collect_atoms(scene)
        basis = np.array(scene.cell_basis, dtype=float)
        orient = self._orient(basis)
        project = orient.project

        corners = [
            project((0, 0, 0)),
            project(orient.h_vec),
            project(orient.v_vec),
            project(orient.h_vec + orient.v_vec),
        ]
        points = [project(a[0]) for a in atoms] + corners
        grid, place = _make_grid(points)

        if 'cell' in features:
            _draw_cell(grid, place, corners)
        if 'atoms' in features and atoms:
            _draw_atoms(grid, place, atoms)

        lines = _grid_to_lines(grid)
        if 'axes' in features:
            v_letter, h_letter = 'abc'[orient.v_idx], 'abc'[orient.h_idx]
            lines = self._annotate_with_axes(lines, place, corners, v_letter, h_letter)
        text = '\n'.join(lines)
        if 'atoms' in features and atoms:
            text += '\n\n' + _legend(atoms)
        return text


def _make_grid(points: list[Point2D]) -> tuple[Grid, Place]:
    """Return an empty grid and a placement closure for points."""
    xs = [p[0] for p in points] or [0.0]
    ys = [p[1] for p in points] or [0.0]
    min_x, max_x, min_y, max_y = min(xs), max(xs), min(ys), max(ys)
    span_x = (max_x - min_x) or 1.0
    span_y = (max_y - min_y) or 1.0
    width = GRID_WIDTH
    height = max(8, int((width - 2 * PAD) * span_y / span_x * CHAR_ASPECT))
    grid: Grid = {}

    def place(point: Coords) -> Cell:
        """Map a projected point to a (row, column) grid cell."""
        col = PAD + int((point[0] - min_x) / span_x * (width - 1 - 2 * PAD))
        row = PAD + int((max_y - point[1]) / span_y * (height - 1 - 2 * PAD))
        return row, col

    grid['_size'] = (height, width)
    return grid, place


def _draw_cell(grid: Grid, place: Place, corners: list[Point2D]) -> None:
    """Draw the unit cell as an upright bounding-box rectangle."""
    # Draw the projected cell as a clean, closed rectangle (the
    # bounding box of the four projected corners). Integer-rounding
    # the corners independently otherwise leaves the borders one
    # row/column out of step. This snaps the slant of oblique cells
    # to an upright box, which the schematic accepts.
    grey = (150, 150, 150)
    cells = [place(c) for c in corners]
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    top, bottom = min(rows), max(rows)
    left, right = min(cols), max(cols)
    for col in range(left, right + 1):
        grid.setdefault((top, col), ('─', grey))
        grid.setdefault((bottom, col), ('─', grey))
    for row in range(top, bottom + 1):
        grid.setdefault((row, left), ('│', grey))
        grid.setdefault((row, right), ('│', grey))
    for cell, glyph in (
        ((top, left), '╭'),
        ((top, right), '╮'),
        ((bottom, left), '╰'),
        ((bottom, right), '╯'),
    ):
        grid[cell] = (glyph, grey)


def _draw_atoms(grid: Grid, place: Place, atoms: list[Atom]) -> None:
    """Place atom glyphs into the grid, skipping near-duplicates."""
    max_radius = max(a[1] for a in atoms) or 1.0
    placed: dict = {}
    for centre, radius, colour, _label in atoms:
        row, col = place(centre)
        # Skip near-duplicates: a same-colour atom already in this or
        # an adjacent cell (periodic images projecting to one spot).
        if any(
            placed.get((row + dr, col + dc)) == colour for dr in (-1, 0, 1) for dc in (-1, 0, 1)
        ):
            continue
        bucket = min(len(GLYPH_RAMP) - 1, int(radius / max_radius * len(GLYPH_RAMP)))
        grid[row, col] = (GLYPH_RAMP[bucket], colour)
        placed[row, col] = colour


def _grid_to_lines(grid: Grid) -> list[str]:
    """Render the grid to ANSI-tinted text rows."""
    height, width = grid['_size']
    lines = []
    for row in range(height):
        chars = []
        for col in range(width):
            cell = grid.get((row, col))
            chars.append(_tint(cell[1], cell[0]) if cell else ' ')
        lines.append(''.join(chars).rstrip())
    return lines


def _annotate_axes(
    lines: list[str],
    left_col: int,
    bottom_row: int,
    v_letter: str,
    h_letter: str,
) -> list[str]:
    """
    Add the vertical- and horizontal-axis labels to the grid.

    Stack the vertical-axis label above the cell and append the
    horizontal label at the right end of the bottom border. ANSI-safe:
    no slicing of tinted rows.
    """
    indent = ' ' * left_col
    header = ['', f'{indent}{v_letter}', f'{indent}↑']  # blank line, letter, arrow
    body = list(lines)
    if 0 <= bottom_row < len(body):
        body[bottom_row] += f'  → {h_letter}'
    return header + body


def _legend(atoms: list[Atom]) -> str:
    """Return a tinted one-line legend of element glyphs."""
    seen: dict = {}
    for _centre, radius, colour, label in atoms:
        # Keep '/' so a shared site reads 'La/Ba', not 'LaBa'; no digits
        element = ''.join(ch for ch in label if ch.isalpha() or ch == '/') or label
        seen.setdefault(element, (radius, colour))
    max_radius = max(r for r, _ in seen.values()) or 1.0
    items = []
    for element, (radius, colour) in seen.items():
        bucket = min(len(GLYPH_RAMP) - 1, int(radius / max_radius * len(GLYPH_RAMP)))
        items.append(_tint(colour, f'{GLYPH_RAMP[bucket]} {element}'))
    return 'Legend:  ' + '   '.join(items)
