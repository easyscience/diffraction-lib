# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""
Raster renderer: a z-buffered PNG structure image for reports.

A tiny software rasteriser with a per-pixel depth buffer, so
hidden-surface removal is exact for any structure. Spheres, bonds, cell
edges, and axis arrows are all depth-tested against the same numpy
buffer; Pillow then draws the a/b/c axis labels and the element legend
on top and encodes the PNG.
"""

from __future__ import annotations

import io
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from PIL import ImageDraw
    from PIL import ImageFont

    from easydiffraction.display.structure.scene import AdpEllipsoid
    from easydiffraction.display.structure.scene import AxisTriad
    from easydiffraction.display.structure.scene import LegendEntry
    from easydiffraction.display.structure.scene import OccupancyWedge
    from easydiffraction.display.structure.scene import Rgb
    from easydiffraction.display.structure.scene import StructureScene
    from easydiffraction.display.structure.scene import Vec3

# A 3D point projected to (screen_x, screen_y, view_depth).
Projector = Callable[[object], 'tuple[float, float, float]']
# Camera basis vectors (right, up, view_dir) as unit numpy arrays.
Basis = 'tuple[np.ndarray, np.ndarray, np.ndarray]'
# Inclusive-exclusive pixel tile bounds (y0, y1, x0, x1).
Region = 'tuple[int, int, int, int]'

_CANVAS = 1800
_SUPERSAMPLE = 2
_MARGIN_FRAC = 0.06
_BOND_RADIUS = 0.06
_EDGE_RADIUS = 0.012
_AMBIENT = 0.5  # broad fill so most of each atom stays bright and saturated
_LIGHT = np.array([0.3, 0.45, 0.85])  # (right, up, toward-camera); frontal key
_LIGHT /= np.linalg.norm(_LIGHT)
_FILL = np.array([-0.4, -0.2, -0.45])  # back-fill, mirrors the Three.js fill light
_FILL /= np.linalg.norm(_FILL)
_HALF = _LIGHT + np.array([0.0, 0.0, 1.0])  # Blinn-Phong half-vector (view = camera)
_HALF /= np.linalg.norm(_HALF)
_SHININESS = 36.0  # specular exponent
_SPEC_STRENGTH = 0.28  # small, subtle highlight (not a hard white spot)
_LABEL_FRAC = 0.040  # axis-letter font size, as a fraction of the canvas
_LEGEND_FRAC = 0.032  # legend font size, as a fraction of the canvas
# Axis-arrow proportions, as fractions of the fit extent, so the arrows
# are a constant on-screen size in every cell (mirrors the Three.js
# defaults). The fit extent is ~2x the Three.js half-height reference,
# hence ~half its fractions.
_AXIS_SHAFT_RADIUS_FRAC = 0.0045
_AXIS_HEAD_RADIUS_FRAC = 0.014
_AXIS_HEAD_LENGTH_FRAC = 0.043
_AXIS_OVERHANG_FRAC = 0.045  # minimum overhang past the cell corner
_AXIS_GAP_FRAC = 0.02  # clear gap between a corner atom and the head base
_AXIS_LABEL_GAP_FRAC = 0.025  # label centre beyond the rendered arrow tip
_AXIS_SEGMENTS = 32  # tessellation of the shaft cylinder and head cone
_AXIS_RESERVE = 1.24  # extent multiplier reserving room for the arrows
_AXIS_PERP_THRESHOLD = 0.9  # pick a fallback up-vector when nearly vertical
_VERTICAL_SHIFT_FRAC = 0.025  # nudge structure down in report frame

_EPS = 1e-9  # degenerate length / denominator guard
_EPS_NORM = 1e-12  # surface-normal renormalisation guard
_MIN_SPHERE_PX = 0.5  # skip spheres smaller than this radius in pixels
_MIN_CAPSULE_PX = 0.6  # floor on the capsule radius in pixels
_BOND_SPLIT = 0.5  # parametric midpoint where a bond changes colour
_FILL_GAIN = 0.4  # weight of the back-fill light in the diffuse term


def _unit(vector: np.ndarray) -> np.ndarray:
    """Return the unit vector, or the input when it has no length."""
    length = float(np.linalg.norm(vector))
    return vector / length if length > _EPS else vector


def _view_basis(scene: StructureScene) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Return (view_dir, right, up) for the default view.

    Mirrors the Three.js default camera (by axis length): the longest
    axis is horizontal, the 2nd-longest points up, the shortest goes
    into depth, and the scene is viewed along ``0.37 longest + 0.24
    middle + 0.90 shortest`` — so the PDF figure and the interactive
    view orient identically.
    """
    if scene.axes is not None:
        vectors = [np.asarray(ax.vector, dtype=float) for ax in scene.axes.axes]
        order = sorted(range(3), key=lambda i: np.linalg.norm(vectors[i]), reverse=True)
        longest, middle, shortest = (_unit(vectors[i]) for i in order)
        view_up = middle
        view_dir = _unit(0.37 * longest + 0.24 * middle + 0.90 * shortest)
    else:
        view_up = np.array([0.0, 1.0, 0.0])
        view_dir = _unit(np.array([1.0, 0.8, 1.5]))
    right = _unit(np.cross(view_up, view_dir))
    up = _unit(np.cross(view_dir, right))
    return view_dir, right, up


def _diffuse_intensity(normal: np.ndarray) -> np.ndarray:
    """Lambertian key-plus-fill intensity for a unit-normal field."""
    key = np.clip(normal @ _LIGHT, 0.0, 1.0)
    fill = _FILL_GAIN * np.clip(normal @ _FILL, 0.0, 1.0)
    return np.clip(_AMBIENT + (1.0 - _AMBIENT) * (key + fill), 0.0, 1.0)


def _specular(normal: np.ndarray) -> np.ndarray:
    """Blinn-Phong specular highlight for a unit-normal field."""
    return _SPEC_STRENGTH * np.clip(normal @ _HALF, 0.0, 1.0) ** _SHININESS


def _font(pixels: int) -> ImageFont.FreeTypeFont:
    """Return the scalable default font at the requested pixel size."""
    from PIL import ImageFont  # noqa: PLC0415

    return ImageFont.load_default(size=pixels)


def _scene_points(scene: StructureScene) -> np.ndarray:
    """Return all 3D anchor points used to centre and scale the view."""
    points: list[Vec3] = []
    points.extend(a.centre for a in scene.atoms)
    points.extend(s.centre for s in scene.occupancy_spheres)
    points.extend(e.centre for e in scene.ellipsoids)
    if scene.cell_edges is not None:
        for edge in scene.cell_edges.edges:
            points.extend((edge.start, edge.end))
    if scene.axes is not None:
        # Only the cell origin; the axis arrows are sized from the fit
        # extent and reserved with a margin, not enclosed per-point.
        points.append(scene.axes.origin)
    return np.array(points, dtype=float) if points else np.zeros((1, 3))


def _max_radius(scene: StructureScene) -> float:
    """Return the largest drawn atom radius (for view padding)."""
    radii = [a.radius for a in scene.atoms]
    radii += [s.radius for s in scene.occupancy_spheres]
    radii += [max(e.semi_axes) for e in scene.ellipsoids]
    return max(radii) if radii else 0.0


def _base_colours(
    dx: np.ndarray,
    dy: np.ndarray,
    base: Rgb,
    wedges: tuple[OccupancyWedge, ...] | None,
) -> np.ndarray:
    """Per-pixel colour: flat tint, or azimuthal occupancy wedges."""
    if not wedges:
        flat = np.asarray(base, dtype=np.float32) / 255.0
        return np.broadcast_to(flat, (*dx.shape, 3))
    # Pie slices by screen-space azimuth measured clockwise from the
    # top, so a two-way split reads as a vertical seam (image y is down,
    # hence negate dy).
    angle = (np.arctan2(dx, -dy) / (2.0 * np.pi)) % 1.0
    base_rgb = np.empty((*dx.shape, 3), dtype=np.float32)
    lo = 0.0
    for wedge in wedges:
        mask = (angle >= lo) & (angle < lo + wedge.fraction)
        base_rgb[mask] = np.asarray(wedge.colour, dtype=np.float32) / 255.0
        lo += wedge.fraction
    base_rgb[angle >= lo] = np.asarray(wedges[-1].colour, dtype=np.float32) / 255.0
    return base_rgb


@dataclass(frozen=True, slots=True)
class _Canvas:
    """Pixel buffers and the 3D-to-screen projection for one frame."""

    colour: np.ndarray
    depth: np.ndarray
    project: Projector
    scale: float

    def depth_tile(self, region: Region) -> np.ndarray:
        """Return a view of the depth buffer over one pixel tile."""
        y0, y1, x0, x1 = region
        return self.depth[y0:y1, x0:x1]

    def composite(
        self,
        region: Region,
        update: np.ndarray,
        surf_depth: np.ndarray,
        shade: np.ndarray,
    ) -> None:
        """Z-test one tile: keep nearer pixels and write their shade."""
        y0, y1, x0, x1 = region
        self.depth[y0:y1, x0:x1][update] = surf_depth[update]
        self.colour[y0:y1, x0:x1][update] = shade[update]

    def composite_flat(
        self,
        region: Region,
        update: np.ndarray,
        surf_depth: np.ndarray,
        shade: np.ndarray,
    ) -> None:
        """Z-test one tile, writing a single flat colour everywhere."""
        y0, y1, x0, x1 = region
        self.depth[y0:y1, x0:x1][update] = surf_depth[update]
        self.colour[y0:y1, x0:x1][update] = shade


def _tile_bounds(size: int, lo_x: float, hi_x: float, lo_y: float, hi_y: float) -> Region | None:
    """Clamp a screen-space box to the canvas, or None if empty."""
    x0, x1 = max(0, int(lo_x)), min(size, int(hi_x) + 1)
    y0, y1 = max(0, int(lo_y)), min(size, int(hi_y) + 1)
    if x0 >= x1 or y0 >= y1:
        return None
    return y0, y1, x0, x1


def _disc_grid(
    region: Region,
    cx: float,
    cy: float,
    r_px: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Return unit pixel offsets, hemisphere height, and coverage."""
    y0, y1, x0, x1 = region
    ys, xs = np.mgrid[y0:y1, x0:x1]
    dx = (xs - cx) / r_px
    dy = (ys - cy) / r_px
    rho2 = dx * dx + dy * dy
    nz = np.sqrt(np.clip(1.0 - rho2, 0.0, 1.0))
    return dx, dy, nz, rho2 <= 1.0


def _capsule_coverage(
    region: Region,
    a: tuple[float, float],
    b: tuple[float, float],
    r_px: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Parametric position, surface normal, and segment coverage."""
    y0, y1, x0, x1 = region
    ys, xs = np.mgrid[y0:y1, x0:x1]
    seg = np.array([b[0] - a[0], b[1] - a[1]], dtype=float)
    length2 = float(seg @ seg) or 1.0
    t = np.clip(((xs - a[0]) * seg[0] + (ys - a[1]) * seg[1]) / length2, 0.0, 1.0)
    proj_x = a[0] + t * seg[0]
    proj_y = a[1] + t * seg[1]
    dist = np.hypot(xs - proj_x, ys - proj_y)
    nz = np.sqrt(np.clip(1.0 - (dist / r_px) ** 2, 0.0, 1.0))
    return t, (xs - proj_x) / r_px, -(ys - proj_y) / r_px, nz, dist <= r_px


def _capsule_shade(colour0: Rgb, colour1: Rgb, t: np.ndarray, normal: np.ndarray) -> np.ndarray:
    """Diffuse-shaded capsule colour, split at the bond midpoint."""
    c0 = np.asarray(colour0, dtype=np.float32) / 255.0
    c1 = np.asarray(colour1, dtype=np.float32) / 255.0
    base = np.where((t < _BOND_SPLIT)[..., None], c0, c1)
    return np.clip(base * _diffuse_intensity(normal)[..., None], 0, 1)


def _barycentric(
    region: Region,
    v0: tuple[float, float, float],
    v1: tuple[float, float, float],
    v2: tuple[float, float, float],
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray] | None:
    """Barycentric weights and inside-mask over a triangle's tile."""
    # Vertices as (sx, sy, depth); only sx, sy enter the weights.
    denom = (v1[1] - v2[1]) * (v0[0] - v2[0]) + (v2[0] - v1[0]) * (v0[1] - v2[1])
    if abs(denom) < _EPS:
        return None
    min_y, max_y, min_x, max_x = region
    ys, xs = np.mgrid[min_y:max_y, min_x:max_x]
    w0 = ((v1[1] - v2[1]) * (xs - v2[0]) + (v2[0] - v1[0]) * (ys - v2[1])) / denom
    w1 = ((v2[1] - v0[1]) * (xs - v2[0]) + (v0[0] - v2[0]) * (ys - v2[1])) / denom
    w2 = 1.0 - w0 - w1
    return w0, w1, w2, (w0 >= 0.0) & (w1 >= 0.0) & (w2 >= 0.0)


def _screen_fit(
    points: np.ndarray,
    target: np.ndarray,
    right: np.ndarray,
    up: np.ndarray,
    pad: float,
    *,
    reserve_axes: bool,
) -> tuple[float, np.ndarray, float]:
    """Return (scale, screen-centre, extent) that fit the points."""
    size = _CANVAS * _SUPERSAMPLE
    relative = points - target
    screen = np.column_stack((relative @ right, relative @ up))
    lo = screen.min(axis=0) - pad
    hi = screen.max(axis=0) + pad
    content_extent = float((hi - lo).max()) or 1.0
    # Reserve room for the axis arrows (drawn beyond the cell) so their
    # heads and letters stay inside the frame.
    extent = content_extent * (_AXIS_RESERVE if reserve_axes else 1.0)
    scale = (size * (1.0 - 2.0 * _MARGIN_FRAC)) / extent
    return scale, (lo + hi) / 2.0, extent


def _axis_tip_vectors(
    vectors: list[np.ndarray],
    extent: float,
    max_atom_r: float,
) -> list[np.ndarray | None]:
    """Return rendered axis-tip vectors from the triad origin."""
    # Recover the longest cell edge from the builder's 0.3*max overhang.
    max_axis = max((float(np.linalg.norm(v)) for v in vectors), default=1.0) / 1.3
    head_len = _AXIS_HEAD_LENGTH_FRAC * extent
    # Overhang clears the largest atom (so corner atoms never hide the
    # head), plus the head length and a small gap.
    overhang = max(
        _AXIS_OVERHANG_FRAC * extent,
        max_atom_r + head_len + _AXIS_GAP_FRAC * extent,
    )
    tips: list[np.ndarray | None] = []
    for vector in vectors:
        length = float(np.linalg.norm(vector))
        if length < _EPS:
            tips.append(None)
            continue
        axis = vector / length
        axis_len = max(length - 0.3 * max_axis, 1e-3)
        tips.append(axis * (axis_len + overhang))
    return tips


class RasterStructureRenderer:
    """Render a structure scene as a z-buffered PNG image."""

    SUPPORTED = frozenset({'atoms', 'bonds', 'cell', 'axes'})

    def render_png(self, scene: StructureScene, *, features: frozenset[str]) -> bytes:
        """Return PNG bytes of the scene with a per-pixel z-buffer."""
        view_dir, right, up = _view_basis(scene)
        canvas, project, extent, pad = self._make_canvas(scene, view_dir, right, up)
        basis = (right, up, view_dir)
        self._draw_features(canvas, scene, features, basis, extent, pad)
        downsampled = canvas.colour.reshape(_CANVAS, _SUPERSAMPLE, _CANVAS, _SUPERSAMPLE, 3).mean(
            axis=(1, 3)
        )
        rgb = np.clip(downsampled * 255.0, 0, 255).astype(np.uint8)
        return self._compose_png(rgb, scene, project, features, extent, pad)

    @staticmethod
    def _make_canvas(
        scene: StructureScene,
        view_dir: np.ndarray,
        right: np.ndarray,
        up: np.ndarray,
    ) -> tuple[_Canvas, Projector, float, float]:
        """Build the pixel buffers and the fitted projection closure."""
        points = _scene_points(scene)
        target = points.mean(axis=0)
        size = _CANVAS * _SUPERSAMPLE
        pad = _max_radius(scene)
        scale, centre2d, extent = _screen_fit(
            points, target, right, up, pad, reserve_axes=scene.axes is not None
        )

        def project(point: object) -> tuple[float, float, float]:
            rel = np.asarray(point, dtype=float) - target
            sx = (float(rel @ right) - centre2d[0]) * scale + size / 2.0
            sy = size / 2.0 - (float(rel @ up) - centre2d[1]) * scale + size * _VERTICAL_SHIFT_FRAC
            return sx, sy, float(rel @ view_dir)

        colour = np.ones((size, size, 3), dtype=np.float32)
        depth = np.full((size, size), -np.inf, dtype=np.float32)
        return _Canvas(colour, depth, project, scale), project, extent, pad

    def _draw_features(
        self,
        canvas: _Canvas,
        scene: StructureScene,
        features: frozenset[str],
        basis: Basis,
        extent: float,
        pad: float,
    ) -> None:
        """Depth-test every requested primitive into the canvas."""
        if 'cell' in features and scene.cell_edges is not None:
            for edge in scene.cell_edges.edges:
                self._capsule(
                    canvas, edge.start, edge.end, _EDGE_RADIUS, (90, 90, 90), (90, 90, 90)
                )
        if 'axes' in features and scene.axes is not None:
            self._axes(canvas, basis, scene.axes, extent, pad)
        if 'bonds' in features:
            for bond in scene.bonds:
                self._capsule(
                    canvas, bond.start, bond.end, _BOND_RADIUS, bond.start_colour, bond.end_colour
                )
        if 'atoms' in features:
            for atom in scene.atoms:
                self._sphere(canvas, atom.centre, atom.radius, atom.colour)
            for sphere in scene.occupancy_spheres:
                self._sphere(
                    canvas, sphere.centre, sphere.radius, (128, 128, 128), wedges=sphere.wedges
                )
            for ellipsoid in scene.ellipsoids:
                self._ellipsoid(canvas, basis, ellipsoid)

    @staticmethod
    def _compose_png(
        rgb: np.ndarray,
        scene: StructureScene,
        project: Projector,
        features: frozenset[str],
        extent: float,
        max_atom_r: float,
    ) -> bytes:
        """Draw axis labels and the legend with Pillow, then encode."""
        from PIL import Image  # noqa: PLC0415
        from PIL import ImageDraw  # noqa: PLC0415

        image = Image.fromarray(rgb, mode='RGB')
        draw = ImageDraw.Draw(image)
        if 'axes' in features and scene.axes is not None:
            RasterStructureRenderer._draw_axis_labels(
                draw, scene.axes, project, extent, max_atom_r
            )
        if scene.legend:
            RasterStructureRenderer._draw_legend(draw, scene.legend)
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        return buffer.getvalue()

    @staticmethod
    def _draw_axis_labels(
        draw: ImageDraw.ImageDraw,
        axes: AxisTriad,
        project: Projector,
        extent: float,
        max_atom_r: float,
    ) -> None:
        """Place each axis letter just beyond its tip, always on top."""
        font = _font(int(_CANVAS * _LABEL_FRAC))
        inset = int(_CANVAS * 0.02)
        origin = np.asarray(axes.origin, dtype=float)
        vectors = [np.asarray(a.vector, dtype=float) for a in axes.axes]
        tip_vectors = _axis_tip_vectors(vectors, extent, max_atom_r)
        for arrow, tip_vector in zip(axes.axes, tip_vectors, strict=True):
            if tip_vector is None:
                continue
            label = origin + tip_vector + _unit(tip_vector) * (_AXIS_LABEL_GAP_FRAC * extent)
            lx, ly, _ld = project(tuple(label))
            lx = float(np.clip(lx / _SUPERSAMPLE, inset, _CANVAS - inset))
            ly = float(np.clip(ly / _SUPERSAMPLE, inset, _CANVAS - inset))
            draw.text((lx, ly), arrow.letter, font=font, fill=tuple(arrow.colour), anchor='mm')

    @staticmethod
    def _draw_legend(draw: ImageDraw.ImageDraw, legend: tuple[LegendEntry, ...]) -> None:
        """Draw element colour swatches and labels in a panel."""
        font = _font(int(_CANVAS * _LEGEND_FRAC))
        margin = int(_CANVAS * 0.025)
        pad = int(_CANVAS * 0.014)
        radius = int(_CANVAS * 0.015)
        pitch = int(_CANVAS * 0.048)
        gap = int(_CANVAS * 0.012)
        text_width = max((draw.textlength(e.symbol, font=font) for e in legend), default=0.0)
        panel_width = 2 * pad + 2 * radius + gap + int(text_width)
        panel_height = pad + len(legend) * pitch
        draw.rounded_rectangle(
            (margin, margin, margin + panel_width, margin + panel_height),
            radius=int(_CANVAS * 0.01),
            fill=(255, 255, 255),
            outline=(170, 170, 170),
            width=max(1, int(_CANVAS * 0.0015)),
        )
        for index, entry in enumerate(legend):
            cx = margin + pad
            cy = margin + pad + radius + index * pitch
            draw.ellipse(
                (cx, cy - radius, cx + 2 * radius, cy + radius),
                fill=tuple(entry.colour),
                outline=(60, 60, 60),
                width=max(1, int(_CANVAS * 0.0012)),
            )
            draw.text(
                (cx + 2 * radius + gap, cy),
                entry.symbol,
                font=font,
                fill=(40, 40, 40),
                anchor='lm',
            )

    @staticmethod
    def _sphere(
        canvas: _Canvas,
        centre: Vec3,
        radius: float,
        base: Rgb,
        *,
        wedges: tuple[OccupancyWedge, ...] | None = None,
    ) -> None:
        """Z-test and shade one matte sphere of the given radius."""
        size = canvas.colour.shape[0]
        cx, cy, cd = canvas.project(centre)
        r_px = radius * canvas.scale
        if r_px < _MIN_SPHERE_PX:
            return
        region = _tile_bounds(size, cx - r_px, cx + r_px, cy - r_px, cy + r_px)
        if region is None:
            return
        dx, dy, nz, inside = _disc_grid(region, cx, cy, r_px)
        if not inside.any():
            return
        surf_depth = cd + nz * radius
        update = inside & (surf_depth > canvas.depth_tile(region))
        if not update.any():
            return
        # Matte (Lambertian) shading to match the Three.js
        # MeshStandardMaterial: normal in (right, up, toward-camera)
        # space; image y is down.
        normal = np.stack((dx, -dy, nz), axis=-1)
        shade = _shade_normals(normal, _base_colours(dx, dy, base, wedges))
        canvas.composite(region, update, surf_depth, shade)

    @staticmethod
    def _ellipsoid(
        canvas: _Canvas,
        basis: Basis,
        ell: AdpEllipsoid,
    ) -> None:
        """Z-tested, shaded ADP ellipsoid (exact ray cast per pixel)."""
        semi = np.maximum(np.asarray(ell.semi_axes, dtype=float), _EPS)
        axes = [np.asarray(vec, dtype=float) for vec in ell.orientation]
        cx, cy, cd = canvas.project(ell.centre)
        region = _ellipsoid_bounds(canvas, semi, axes, basis, cx, cy)
        if region is None:
            return
        cast = _ellipsoid_raycast(region, semi, axes, basis, canvas.scale, (cx, cy))
        if cast is None:
            return
        result = _ellipsoid_update(canvas, region, cd, basis, (semi, axes), cast)
        if result is None:
            return
        update, surf_depth, normal = result
        ys, xs = np.mgrid[region[0] : region[1], region[2] : region[3]]
        base_rgb = _base_colours(xs - cx, ys - cy, ell.colour, ell.wedges)
        canvas.composite(region, update, surf_depth, _shade_normals(normal, base_rgb))

    @staticmethod
    def _capsule(
        canvas: _Canvas, p0: Vec3, p1: Vec3, radius: float, colour0: Rgb, colour1: Rgb
    ) -> None:
        """Z-test and shade one split-coloured cylindrical capsule."""
        size = canvas.colour.shape[0]
        a = canvas.project(p0)
        b = canvas.project(p1)
        r_px = max(radius * canvas.scale, _MIN_CAPSULE_PX)
        region = _tile_bounds(
            size,
            min(a[0], b[0]) - r_px,
            max(a[0], b[0]) + r_px,
            min(a[1], b[1]) - r_px,
            max(a[1], b[1]) + r_px,
        )
        if region is None:
            return
        t, nx, ny, nz, inside = _capsule_coverage(region, a[:2], b[:2], r_px)
        if not inside.any():
            return
        surf_depth = a[2] + t * (b[2] - a[2]) + nz * radius
        update = inside & (surf_depth > canvas.depth_tile(region))
        if not update.any():
            return
        # Directional cylinder shading: normal perpendicular to the
        # projected axis (image y is down), with the bulge as the
        # toward-camera component.
        shade = _capsule_shade(colour0, colour1, t, np.stack((nx, ny, nz), axis=-1))
        canvas.composite(region, update, surf_depth, shade)

    @staticmethod
    def _triangle(
        canvas: _Canvas,
        v0: tuple[float, float, float],
        v1: tuple[float, float, float],
        v2: tuple[float, float, float],
        shade: np.ndarray,
    ) -> None:
        """Z-test and fill one flat-shaded triangle from projections."""
        size = canvas.colour.shape[0]
        region = _tile_bounds(
            size,
            min(v0[0], v1[0], v2[0]),
            max(v0[0], v1[0], v2[0]),
            min(v0[1], v1[1], v2[1]),
            max(v0[1], v1[1], v2[1]),
        )
        if region is None:
            return
        bary = _barycentric(region, v0, v1, v2)
        if bary is None:
            return
        w0, w1, w2, inside = bary
        if not inside.any():
            return
        tri_depth = w0 * v0[2] + w1 * v1[2] + w2 * v2[2]
        update = inside & (tri_depth > canvas.depth_tile(region))
        if not update.any():
            return
        canvas.composite_flat(region, update, tri_depth, shade)

    def _arrow(
        self,
        canvas: _Canvas,
        basis: Basis,
        origin: np.ndarray,
        vector: np.ndarray,
        extent: float,
        rgb: Rgb,
    ) -> None:
        """
        Draw a shaft cylinder and head cone as 3D triangles.

        Thickness and head size are fractions of ``extent`` (the fit
        extent), so the arrow is a constant on-screen size in every
        cell. ``vector`` already runs to the arrow tip (cell edge plus
        overhang).
        """
        geometry = _arrow_geometry(origin, vector, extent)
        if geometry is None:
            return
        axis, u, v, base, tip = geometry
        radii = (_AXIS_SHAFT_RADIUS_FRAC * extent, _AXIS_HEAD_RADIUS_FRAC * extent)
        flat = np.asarray(rgb, dtype=np.float32) / 255.0
        ring = [
            np.cos(angle) * u + np.sin(angle) * v
            for angle in (2.0 * np.pi * i / _AXIS_SEGMENTS for i in range(_AXIS_SEGMENTS))
        ]
        for i in range(_AXIS_SEGMENTS):
            self._arrow_segment(canvas, ring, i, (origin, base, tip), radii, (axis, basis, flat))

    def _arrow_segment(
        self,
        canvas: _Canvas,
        ring: list[np.ndarray],
        i: int,
        anchors: tuple[np.ndarray, np.ndarray, np.ndarray],
        radii: tuple[float, float],
        shading: tuple[np.ndarray, Basis, np.ndarray],
    ) -> None:
        """Emit the shaft and head triangles for one ring segment."""
        origin, base, tip = anchors
        shaft_r, head_r = radii
        _axis, basis, flat = shading
        pair = (ring[i], ring[(i + 1) % _AXIS_SEGMENTS])
        shaft_shade = _arrow_shade(_unit(pair[0] + pair[1]), basis, flat)
        self._arrow_shaft(canvas, origin, base, shaft_r, pair, shaft_shade)
        self._arrow_head(canvas, base, tip, head_r, pair, shading)

    def _arrow_shaft(
        self,
        canvas: _Canvas,
        origin: np.ndarray,
        base: np.ndarray,
        shaft_r: float,
        pair: tuple[np.ndarray, np.ndarray],
        shade: np.ndarray,
    ) -> None:
        """Emit the two shaft-cylinder triangles for one segment."""
        d0, d1 = pair
        project = canvas.project
        o0 = project(tuple(origin + shaft_r * d0))
        o1 = project(tuple(origin + shaft_r * d1))
        s0 = project(tuple(base + shaft_r * d0))
        s1 = project(tuple(base + shaft_r * d1))
        self._triangle(canvas, o0, o1, s1, shade)
        self._triangle(canvas, o0, s1, s0, shade)

    def _arrow_head(
        self,
        canvas: _Canvas,
        base: np.ndarray,
        tip: np.ndarray,
        head_r: float,
        pair: tuple[np.ndarray, np.ndarray],
        shading: tuple[np.ndarray, Basis, np.ndarray],
    ) -> None:
        """Emit the cone-face and base triangles for one segment."""
        axis, basis, flat = shading
        d0, d1 = pair
        project = canvas.project
        b0 = base + head_r * d0
        b1 = base + head_r * d1
        normal = _unit(np.cross(b1 - b0, tip - b0))
        if normal @ (d0 + d1) < 0.0:
            normal = -normal
        self._triangle(
            canvas,
            project(tuple(b0)),
            project(tuple(b1)),
            project(tuple(tip)),
            _arrow_shade(normal, basis, flat),
        )
        self._triangle(
            canvas,
            project(tuple(base)),
            project(tuple(b1)),
            project(tuple(b0)),
            _arrow_shade(-axis, basis, flat),
        )

    def _axes(
        self,
        canvas: _Canvas,
        basis: Basis,
        axes: AxisTriad,
        extent: float,
        max_atom_r: float,
    ) -> None:
        """Draw the a/b/c arrow triad beyond the cell corners."""
        origin = np.asarray(axes.origin, dtype=float)
        vectors = [np.asarray(a.vector, dtype=float) for a in axes.axes]
        for arrow, tip_vector in zip(
            axes.axes, _axis_tip_vectors(vectors, extent, max_atom_r), strict=True
        ):
            if tip_vector is None:
                continue
            self._arrow(canvas, basis, origin, tip_vector, extent, arrow.colour)


def _shade_normals(normal: np.ndarray, base_rgb: np.ndarray) -> np.ndarray:
    """Combine diffuse and specular terms over a base-colour field."""
    intensity = _diffuse_intensity(normal)[..., None]
    return np.clip(base_rgb * intensity + _specular(normal)[..., None], 0, 1)


def _camera_components(
    axes: list[np.ndarray],
    basis: Basis,
) -> tuple[list[float], list[float], list[float]]:
    """Camera-frame (right, up, view) components of each axis."""
    right, up, view_dir = basis
    return (
        [float(axes[k] @ right) for k in range(3)],
        [float(axes[k] @ up) for k in range(3)],
        [float(axes[k] @ view_dir) for k in range(3)],
    )


def _ellipsoid_bounds(
    canvas: _Canvas,
    semi: np.ndarray,
    axes: list[np.ndarray],
    basis: Basis,
    cx: float,
    cy: float,
) -> Region | None:
    """Screen-space bounding tile of a projected ADP ellipsoid."""
    right, up = basis[0], basis[1]
    size = canvas.colour.shape[0]
    half_x = canvas.scale * float(
        np.sqrt(sum((semi[k] * (axes[k] @ right)) ** 2 for k in range(3)))
    )
    half_y = canvas.scale * float(np.sqrt(sum((semi[k] * (axes[k] @ up)) ** 2 for k in range(3))))
    return _tile_bounds(size, cx - half_x, cx + half_x, cy - half_y, cy + half_y)


def _ellipsoid_offsets(
    region: Region,
    scale: float,
    centre2d: tuple[float, float],
) -> tuple[np.ndarray, np.ndarray]:
    """Image-plane right/up offsets (world units) over a pixel tile."""
    cx, cy = centre2d
    y0, y1, x0, x1 = region
    ys, xs = np.mgrid[y0:y1, x0:x1]
    return (xs - cx) / scale, -(ys - cy) / scale


def _ellipsoid_raycast(
    region: Region,
    semi: np.ndarray,
    axes: list[np.ndarray],
    basis: Basis,
    scale: float,
    centre2d: tuple[float, float],
) -> tuple[np.ndarray, list[np.ndarray], np.ndarray] | None:
    """Solve the view-ray/ellipsoid intersection over a pixel tile."""
    r, u, v = _camera_components(axes, basis)
    a_coeff = sum((v[k] / semi[k]) ** 2 for k in range(3))
    if a_coeff <= 0.0:
        return None
    # Solve |S^-1 R^T q|^2 = 1 along the ray q = image-plane + t*view.
    offset_right, offset_up = _ellipsoid_offsets(region, scale, centre2d)
    base = [offset_right * r[k] + offset_up * u[k] for k in range(3)]
    b_coeff = sum(2.0 * base[k] * v[k] / semi[k] ** 2 for k in range(3))
    c_coeff = sum((base[k] / semi[k]) ** 2 for k in range(3)) - 1.0
    disc = b_coeff * b_coeff - 4.0 * a_coeff * c_coeff
    inside = disc >= 0.0
    if not inside.any():
        return None
    t = (-b_coeff + np.sqrt(np.clip(disc, 0.0, None))) / (2.0 * a_coeff)
    return t, base, inside


def _ellipsoid_update(
    canvas: _Canvas,
    region: Region,
    cd: float,
    basis: Basis,
    geom: tuple[np.ndarray, list[np.ndarray]],
    cast: tuple[np.ndarray, list[np.ndarray], np.ndarray],
) -> tuple[np.ndarray, np.ndarray, np.ndarray] | None:
    """Depth-test the cast hits and return (update, depth, normal)."""
    semi, axes = geom
    local_t, base, inside = cast
    surf_depth = cd + local_t
    update = inside & (surf_depth > canvas.depth_tile(region))
    if not update.any():
        return None
    normal = _ellipsoid_normals(base, local_t, semi, axes, basis)
    return update, surf_depth, normal


def _ellipsoid_normals(
    base: list[np.ndarray],
    t: np.ndarray,
    semi: np.ndarray,
    axes: list[np.ndarray],
    basis: Basis,
) -> np.ndarray:
    """Camera-frame unit surface normals on the ellipsoid hit points."""
    right, up, view_dir = basis
    v = [float(axes[k] @ view_dir) for k in range(3)]
    local = [(base[k] + t * v[k]) / semi[k] for k in range(3)]
    nx = sum(local[k] / semi[k] * axes[k][0] for k in range(3))
    ny = sum(local[k] / semi[k] * axes[k][1] for k in range(3))
    nz = sum(local[k] / semi[k] * axes[k][2] for k in range(3))
    norm = np.sqrt(nx * nx + ny * ny + nz * nz)
    norm = np.where(norm > _EPS_NORM, norm, 1.0)
    return np.stack(
        (
            (nx * right[0] + ny * right[1] + nz * right[2]) / norm,
            (nx * up[0] + ny * up[1] + nz * up[2]) / norm,
            (nx * view_dir[0] + ny * view_dir[1] + nz * view_dir[2]) / norm,
        ),
        axis=-1,
    )


def _arrow_geometry(
    origin: np.ndarray,
    vector: np.ndarray,
    extent: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray] | None:
    """Axis frame, shaft base, and tip for one arrow, or None."""
    length = float(np.linalg.norm(vector))
    if length < _EPS:
        return None
    axis = vector / length
    perp = (
        np.array([0.0, 0.0, 1.0])
        if abs(axis[2]) < _AXIS_PERP_THRESHOLD
        else np.array([0.0, 1.0, 0.0])
    )
    u = _unit(np.cross(perp, axis))
    v = np.cross(axis, u)
    base = origin + axis * max(length - _AXIS_HEAD_LENGTH_FRAC * extent, 1e-3)
    tip = origin + vector
    return axis, u, v, base, tip


def _arrow_shade(
    world_normal: np.ndarray,
    basis: Basis,
    flat: np.ndarray,
) -> np.ndarray:
    """Flat colour scaled by the diffuse term for one arrow facet."""
    right, up, view_dir = basis
    cam = np.array([world_normal @ right, world_normal @ up, world_normal @ view_dir])
    return np.clip(flat * float(_diffuse_intensity(cam)), 0.0, 1.0)
