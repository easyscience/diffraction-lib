# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""TikZ renderer: a static, vector 2D structure figure for LaTeX/PDF reports."""

from __future__ import annotations

import numpy as np

from easydiffraction.display.structure.renderers.base import StructureRendererBase
from easydiffraction.display.structure.scene import StructureScene

_FIGURE_SIZE_CM = 6.0
_BOND_RADIUS = 0.06  # matches the Three.js bond cylinder radius (angstrom)
_PREAMBLE = (
    '\\documentclass[border=2pt]{standalone}\n'
    '\\usepackage{tikz}\n'
    '\\usetikzlibrary{shadings,arrows.meta}\n'
    '\\begin{document}\n'
)


def _rgb(colour: tuple[int, int, int]) -> str:
    """Return an inline xcolor expression for an RGB triple."""
    return f'{{rgb,255:red,{colour[0]};green,{colour[1]};blue,{colour[2]}}}'


def _unit(vector: np.ndarray) -> np.ndarray:
    """Return the unit vector, or the input when it has no length."""
    length = float(np.linalg.norm(vector))
    return vector / length if length > 1e-9 else vector


def _view_basis(scene: StructureScene) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return (view_dir, right, up) for a trimetric, c-axis-up projection."""
    if scene.axes is not None:
        a_hat = _unit(np.asarray(scene.axes.axes[0].vector, dtype=float))
        b_hat = _unit(np.asarray(scene.axes.axes[1].vector, dtype=float))
        c_hat = _unit(np.asarray(scene.axes.axes[2].vector, dtype=float))
        view_up = c_hat
        view_dir = _unit(1.0 * a_hat + 0.45 * b_hat + 0.55 * c_hat)
    else:
        view_up = np.array([0.0, 1.0, 0.0])
        view_dir = _unit(np.array([1.0, 0.8, 1.5]))
    right = _unit(np.cross(view_up, view_dir))
    up = _unit(np.cross(view_dir, right))
    return view_dir, right, up


def _scene_points(scene: StructureScene) -> np.ndarray:
    """Return all 3D anchor points used to centre and scale the figure."""
    points: list[tuple[float, float, float]] = []
    points.extend(a.centre for a in scene.atoms)
    points.extend(s.centre for s in scene.occupancy_spheres)
    points.extend(e.centre for e in scene.ellipsoids)
    if scene.cell_edges is not None:
        for edge in scene.cell_edges.edges:
            points.append(edge.start)
            points.append(edge.end)
    if scene.axes is not None:
        origin = np.asarray(scene.axes.origin, dtype=float)
        points.append(scene.axes.origin)
        for arrow in scene.axes.axes:
            points.append(tuple(origin + np.asarray(arrow.vector, dtype=float)))
    return np.array(points, dtype=float) if points else np.zeros((1, 3))


class TikzStructureRenderer(StructureRendererBase):
    """Render a structure scene as a standalone TikZ/LaTeX document."""

    SUPPORTED = frozenset({'atoms', 'bonds', 'cell', 'axes'})

    def supported_features(self) -> frozenset[str]:
        """Return the features the TikZ engine can draw."""
        return self.SUPPORTED

    def render(self, scene: StructureScene, *, features: frozenset[str]) -> str:
        """
        Render the scene as a standalone TikZ document.

        Parameters
        ----------
        scene : StructureScene
            The renderer-neutral primitives to draw.
        features : frozenset[str]
            The content-resolved feature set; ``atoms``/``bonds``/``cell``/
            ``axes`` are drawn, others (moments, labels) are skipped.

        Returns
        -------
        str
            A complete ``standalone`` LaTeX document with one tikzpicture.
        """
        view_dir, right, up = _view_basis(scene)
        points = _scene_points(scene)
        target = points.mean(axis=0)

        def project(point: object) -> tuple[float, float, float]:
            rel = np.asarray(point, dtype=float) - target
            return float(rel @ right), float(rel @ up), float(rel @ view_dir)

        scale = self._scale(points, right, up, target)
        bond_width = 2.0 * _BOND_RADIUS * scale
        drawables: list[tuple[float, str]] = []
        if 'cell' in features:
            drawables.extend(self._cell_commands(scene, project))
        if 'axes' in features:
            drawables.extend(self._axis_commands(scene, project))
        if 'bonds' in features:
            drawables.extend(self._bond_commands(scene, project, bond_width))
        if 'atoms' in features:
            drawables.extend(self._atom_commands(scene, project))

        drawables.sort(key=lambda item: item[0])
        body = '\n'.join(command for _depth, command in drawables)
        return (
            f'{_PREAMBLE}'
            f'\\begin{{tikzpicture}}[scale={scale:.4f}]\n'
            f'{body}\n'
            f'\\end{{tikzpicture}}\n'
            f'\\end{{document}}\n'
        )

    @staticmethod
    def _scale(points: np.ndarray, right: np.ndarray, up: np.ndarray, target: np.ndarray) -> float:
        """Return a tikzpicture scale that fits the figure to a fixed size."""
        rel = points - target
        projected = np.column_stack((rel @ right, rel @ up))
        extent = float((projected.max(axis=0) - projected.min(axis=0)).max())
        return _FIGURE_SIZE_CM / extent if extent > 1e-6 else 1.0

    @staticmethod
    def _cell_commands(scene, project) -> list[tuple[float, str]]:
        commands = []
        if scene.cell_edges is None:
            return commands
        for edge in scene.cell_edges.edges:
            x1, y1, d1 = project(edge.start)
            x2, y2, d2 = project(edge.end)
            commands.append((
                (d1 + d2) / 2,
                f'\\draw[line width=0.4pt,black!55] ({x1:.4f},{y1:.4f}) -- ({x2:.4f},{y2:.4f});',
            ))
        return commands

    @staticmethod
    def _axis_commands(scene, project) -> list[tuple[float, str]]:
        commands = []
        if scene.axes is None:
            return commands
        origin = np.asarray(scene.axes.origin, dtype=float)
        ox, oy, _od = project(scene.axes.origin)
        for arrow in scene.axes.axes:
            colour = _rgb(arrow.colour)
            tip = tuple(origin + np.asarray(arrow.vector, dtype=float))
            tx, ty, td = project(tip)
            commands.append((
                td,
                f'\\draw[-{{Stealth[length=2.4mm]}},line width=1pt,color={colour}] '
                f'({ox:.4f},{oy:.4f}) -- ({tx:.4f},{ty:.4f});',
            ))
            lx = ox + (tx - ox) * 1.1
            ly = oy + (ty - oy) * 1.1
            commands.append((
                td,
                f'\\node[color={colour},font=\\bfseries] at ({lx:.4f},{ly:.4f}) {{{arrow.letter}}};',
            ))
        return commands

    @staticmethod
    def _bond_commands(scene, project, bond_width: float) -> list[tuple[float, str]]:
        commands = []
        for bond in scene.bonds:
            sx, sy, sd = project(bond.start)
            ex, ey, ed = project(bond.end)
            mx, my = (sx + ex) / 2, (sy + ey) / 2
            depth = (sd + ed) / 2
            for x0, y0, x1, y1, colour in (
                (sx, sy, mx, my, bond.start_colour),
                (mx, my, ex, ey, bond.end_colour),
            ):
                commands.append((
                    depth,
                    f'\\draw[line width={bond_width:.4f}cm,line cap=round,color={_rgb(colour)}] '
                    f'({x0:.4f},{y0:.4f}) -- ({x1:.4f},{y1:.4f});',
                ))
        return commands

    @staticmethod
    def _atom_commands(scene, project) -> list[tuple[float, str]]:
        commands = []
        for atom in scene.atoms:
            x, y, depth = project(atom.centre)
            commands.append((
                depth,
                f'\\shade[ball color={_rgb(atom.colour)}] ({x:.4f},{y:.4f}) circle ({atom.radius:.4f});',
            ))
        for sphere in scene.occupancy_spheres:
            x, y, depth = project(sphere.centre)
            colour = sphere.wedges[0].colour if sphere.wedges else (128, 128, 128)
            commands.append((
                depth,
                f'\\shade[ball color={_rgb(colour)}] ({x:.4f},{y:.4f}) circle ({sphere.radius:.4f});',
            ))
        for ellipsoid in scene.ellipsoids:
            x, y, depth = project(ellipsoid.centre)
            radius = max(ellipsoid.semi_axes)
            commands.append((
                depth,
                f'\\shade[ball color={_rgb(ellipsoid.colour)}] ({x:.4f},{y:.4f}) circle ({radius:.4f});',
            ))
        return commands
