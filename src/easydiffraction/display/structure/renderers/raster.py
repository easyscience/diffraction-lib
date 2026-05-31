# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Raster renderer: a z-buffered PNG structure image for reports.

A tiny software rasteriser with a per-pixel depth buffer, so hidden-surface
removal is exact for any structure. Spheres, bonds, cell edges, and axis
arrows are all depth-tested against the same numpy buffer; Pillow then draws
the a/b/c axis labels and the element legend on top and encodes the PNG.
"""

from __future__ import annotations

import io
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from PIL import ImageFont

_CANVAS = 1800
_SUPERSAMPLE = 2
_MARGIN_FRAC = 0.06
_BOND_RADIUS = 0.06
_AMBIENT = 0.5  # broad fill so most of each atom stays bright and saturated
_LIGHT = np.array([0.3, 0.45, 0.85])  # (right, up, toward-camera); frontal key
_LIGHT = _LIGHT / np.linalg.norm(_LIGHT)
_FILL = np.array([-0.4, -0.2, -0.45])  # back-fill, mirrors the Three.js fill light
_FILL = _FILL / np.linalg.norm(_FILL)
_HALF = _LIGHT + np.array([0.0, 0.0, 1.0])  # Blinn-Phong half-vector (view = toward camera)
_HALF = _HALF / np.linalg.norm(_HALF)
_SHININESS = 36.0  # specular exponent
_SPEC_STRENGTH = 0.28  # small, subtle highlight (not a hard white spot)
_LABEL_FRAC = 0.040  # axis-letter font size, as a fraction of the canvas
_LEGEND_FRAC = 0.032  # legend font size, as a fraction of the canvas
# Axis-arrow proportions, as fractions of the fit extent, so the arrows are a
# constant on-screen size in every cell (mirrors the Three.js defaults). The fit
# extent is ~2x the Three.js half-height reference, hence ~half its fractions.
_AXIS_SHAFT_RADIUS_FRAC = 0.0045
_AXIS_HEAD_RADIUS_FRAC = 0.014
_AXIS_HEAD_LENGTH_FRAC = 0.043
_AXIS_OVERHANG_FRAC = 0.045  # minimum overhang past the cell corner
_AXIS_GAP_FRAC = 0.02  # clear gap between a corner atom and the head base


def _unit(vector: np.ndarray) -> np.ndarray:
    """Return the unit vector, or the input when it has no length."""
    length = float(np.linalg.norm(vector))
    return vector / length if length > 1e-9 else vector


def _view_basis(scene) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return (view_dir, right, up) for the default view.

    Mirrors the Three.js default camera (by axis length): the longest axis is
    horizontal, the 2nd-longest points up, the shortest goes into depth, and the
    scene is viewed along ``0.37 longest + 0.24 middle + 0.90 shortest`` — so the
    PDF figure and the interactive view orient identically.
    """
    if scene.axes is not None:
        vectors = [np.asarray(ax.vector, dtype=float) for ax in scene.axes.axes]
        longest, middle, shortest = (
            _unit(vectors[i]) for i in sorted(range(3), key=lambda i: np.linalg.norm(vectors[i]), reverse=True)
        )
        view_up = middle
        view_dir = _unit(0.37 * longest + 0.24 * middle + 0.90 * shortest)
    else:
        view_up = np.array([0.0, 1.0, 0.0])
        view_dir = _unit(np.array([1.0, 0.8, 1.5]))
    right = _unit(np.cross(view_up, view_dir))
    up = _unit(np.cross(view_dir, right))
    return view_dir, right, up


def _diffuse_intensity(normal: np.ndarray) -> np.ndarray:
    """Lambertian key-plus-fill intensity for a unit surface-normal field."""
    key = np.clip(normal @ _LIGHT, 0.0, 1.0)
    fill = 0.4 * np.clip(normal @ _FILL, 0.0, 1.0)
    return np.clip(_AMBIENT + (1.0 - _AMBIENT) * (key + fill), 0.0, 1.0)


def _specular(normal: np.ndarray) -> np.ndarray:
    """Blinn-Phong specular highlight for a unit surface-normal field."""
    return _SPEC_STRENGTH * np.clip(normal @ _HALF, 0.0, 1.0) ** _SHININESS


def _font(pixels: int) -> ImageFont.FreeTypeFont:
    """Return the scalable default font at the requested pixel size."""
    from PIL import ImageFont  # noqa: PLC0415

    return ImageFont.load_default(size=pixels)


def _scene_points(scene) -> np.ndarray:
    """Return all 3D anchor points used to centre and scale the view."""
    points: list[tuple[float, float, float]] = []
    points.extend(a.centre for a in scene.atoms)
    points.extend(s.centre for s in scene.occupancy_spheres)
    points.extend(e.centre for e in scene.ellipsoids)
    if scene.cell_edges is not None:
        for edge in scene.cell_edges.edges:
            points.append(edge.start)
            points.append(edge.end)
    if scene.axes is not None:
        # Only the cell origin; the axis arrows are sized from the fit extent and
        # reserved with a margin, not enclosed point-by-point.
        points.append(scene.axes.origin)
    return np.array(points, dtype=float) if points else np.zeros((1, 3))


def _max_radius(scene) -> float:
    """Return the largest drawn atom radius (for view padding)."""
    radii = [a.radius for a in scene.atoms]
    radii += [s.radius for s in scene.occupancy_spheres]
    radii += [max(e.semi_axes) for e in scene.ellipsoids]
    return max(radii) if radii else 0.0


class RasterStructureRenderer:
    """Render a structure scene as a z-buffered PNG image."""

    SUPPORTED = frozenset({'atoms', 'bonds', 'cell', 'axes'})

    def render_png(self, scene, *, features: frozenset[str]) -> bytes:
        """Return PNG bytes of the scene rendered with a per-pixel z-buffer."""
        view_dir, right, up = _view_basis(scene)
        points = _scene_points(scene)
        target = points.mean(axis=0)

        size = _CANVAS * _SUPERSAMPLE
        relative = points - target
        screen = np.column_stack((relative @ right, relative @ up))
        pad = _max_radius(scene)
        lo = screen.min(axis=0) - pad
        hi = screen.max(axis=0) + pad
        content_extent = float((hi - lo).max()) or 1.0
        # Reserve room for the axis arrows (drawn beyond the cell, sized from the
        # extent below) so their heads and letters stay inside the frame.
        extent = content_extent * (1.24 if scene.axes is not None else 1.0)
        scale = (size * (1.0 - 2.0 * _MARGIN_FRAC)) / extent
        centre2d = (lo + hi) / 2.0

        def project(point: object) -> tuple[float, float, float]:
            rel = np.asarray(point, dtype=float) - target
            sx = (float(rel @ right) - centre2d[0]) * scale + size / 2.0
            sy = size / 2.0 - (float(rel @ up) - centre2d[1]) * scale
            return sx, sy, float(rel @ view_dir)

        colour = np.ones((size, size, 3), dtype=np.float32)
        depth = np.full((size, size), -np.inf, dtype=np.float32)

        if 'cell' in features and scene.cell_edges is not None:
            for edge in scene.cell_edges.edges:
                self._capsule(colour, depth, project, scale, edge.start, edge.end,
                              0.012, (90, 90, 90), (90, 90, 90))
        if 'axes' in features and scene.axes is not None:
            self._axes(colour, depth, project, (right, up, view_dir), scene.axes, extent, pad)
        if 'bonds' in features:
            for bond in scene.bonds:
                self._capsule(colour, depth, project, scale, bond.start, bond.end,
                              _BOND_RADIUS, bond.start_colour, bond.end_colour)
        if 'atoms' in features:
            for atom in scene.atoms:
                self._sphere(colour, depth, project, scale, atom.centre, atom.radius, atom.colour)
            for sphere in scene.occupancy_spheres:
                self._sphere(colour, depth, project, scale, sphere.centre, sphere.radius,
                             (128, 128, 128), wedges=sphere.wedges)
            for ellipsoid in scene.ellipsoids:
                self._ellipsoid(colour, depth, project, scale, (right, up, view_dir), ellipsoid)

        downsampled = (
            colour.reshape(_CANVAS, _SUPERSAMPLE, _CANVAS, _SUPERSAMPLE, 3).mean(axis=(1, 3))
        )
        rgb = np.clip(downsampled * 255.0, 0, 255).astype(np.uint8)
        return self._compose_png(rgb, scene, project, features)

    @staticmethod
    def _compose_png(rgb, scene, project, features) -> bytes:
        """Draw axis labels and the legend with Pillow, then encode the PNG."""
        from PIL import Image  # noqa: PLC0415
        from PIL import ImageDraw  # noqa: PLC0415

        image = Image.fromarray(rgb, mode='RGB')
        draw = ImageDraw.Draw(image)
        if 'axes' in features and scene.axes is not None:
            RasterStructureRenderer._draw_axis_labels(draw, scene.axes, project)
        if scene.legend:
            RasterStructureRenderer._draw_legend(draw, scene.legend)
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        return buffer.getvalue()

    @staticmethod
    def _draw_axis_labels(draw, axes, project) -> None:
        """Place each axis letter just beyond its arrow tip, always on top."""
        font = _font(int(_CANVAS * _LABEL_FRAC))
        inset = int(_CANVAS * 0.02)
        origin = np.asarray(axes.origin, dtype=float)
        ox, oy, _od = project(axes.origin)
        for arrow in axes.axes:
            tip = origin + np.asarray(arrow.vector, dtype=float)
            tx, ty, _td = project(tuple(tip))
            lx = float(np.clip((ox + (tx - ox) * 1.08) / _SUPERSAMPLE, inset, _CANVAS - inset))
            ly = float(np.clip((oy + (ty - oy) * 1.08) / _SUPERSAMPLE, inset, _CANVAS - inset))
            draw.text((lx, ly), arrow.letter, font=font, fill=tuple(arrow.colour), anchor='mm')

    @staticmethod
    def _draw_legend(draw, legend) -> None:
        """Draw element colour swatches and symbols in a top-left panel."""
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
            radius=int(_CANVAS * 0.01), fill=(255, 255, 255), outline=(170, 170, 170),
            width=max(1, int(_CANVAS * 0.0015)),
        )
        for index, entry in enumerate(legend):
            cx = margin + pad
            cy = margin + pad + radius + index * pitch
            draw.ellipse(
                (cx, cy - radius, cx + 2 * radius, cy + radius),
                fill=tuple(entry.colour), outline=(60, 60, 60), width=max(1, int(_CANVAS * 0.0012)),
            )
            draw.text((cx + 2 * radius + gap, cy), entry.symbol,
                      font=font, fill=(40, 40, 40), anchor='lm')

    @staticmethod
    def _sphere(colour, depth, project, scale, centre, radius, base, *, wedges=None) -> None:
        size = colour.shape[0]
        cx, cy, cd = project(centre)
        r_px = radius * scale
        if r_px < 0.5:
            return
        x0, x1 = max(0, int(cx - r_px)), min(size, int(cx + r_px) + 1)
        y0, y1 = max(0, int(cy - r_px)), min(size, int(cy + r_px) + 1)
        if x0 >= x1 or y0 >= y1:
            return
        ys, xs = np.mgrid[y0:y1, x0:x1]
        dx = (xs - cx) / r_px
        dy = (ys - cy) / r_px
        rho2 = dx * dx + dy * dy
        inside = rho2 <= 1.0
        if not inside.any():
            return
        nz = np.sqrt(np.clip(1.0 - rho2, 0.0, 1.0))
        surf_depth = cd + nz * radius
        sub = depth[y0:y1, x0:x1]
        update = inside & (surf_depth > sub)
        if not update.any():
            return
        # Matte (Lambertian) shading to match the Three.js MeshStandardMaterial:
        # normal in (right, up, toward-camera) space; image y is down.
        normal = np.stack((dx, -dy, nz), axis=-1)
        intensity = _diffuse_intensity(normal)[..., None]
        base_rgb = RasterStructureRenderer._base_colours(dx, dy, base, wedges)
        shade = np.clip(base_rgb * intensity + _specular(normal)[..., None], 0, 1)
        sub[update] = surf_depth[update]
        colour[y0:y1, x0:x1][update] = shade[update]

    @staticmethod
    def _base_colours(dx, dy, base, wedges) -> np.ndarray:
        """Per-pixel base colour: a flat tint, or azimuthal occupancy wedges."""
        if not wedges:
            flat = np.asarray(base, dtype=np.float32) / 255.0
            return np.broadcast_to(flat, dx.shape + (3,))
        # Pie slices by screen-space azimuth measured clockwise from the top, so
        # a two-way split reads as a vertical seam (image y is down -> negate dy).
        angle = (np.arctan2(dx, -dy) / (2.0 * np.pi)) % 1.0
        base_rgb = np.empty(dx.shape + (3,), dtype=np.float32)
        lo = 0.0
        for wedge in wedges:
            mask = (angle >= lo) & (angle < lo + wedge.fraction)
            base_rgb[mask] = np.asarray(wedge.colour, dtype=np.float32) / 255.0
            lo += wedge.fraction
        base_rgb[angle >= lo] = np.asarray(wedges[-1].colour, dtype=np.float32) / 255.0
        return base_rgb

    @staticmethod
    def _ellipsoid(colour, depth, project, scale, basis, ell) -> None:
        """Z-tested, shaded oriented ADP ellipsoid (exact ray cast per pixel)."""
        right, up, view_dir = basis
        centre = np.asarray(ell.centre, dtype=float)
        semi = np.maximum(np.asarray(ell.semi_axes, dtype=float), 1e-9)
        axes = [np.asarray(vec, dtype=float) for vec in ell.orientation]
        cx, cy, cd = project(centre)
        half_x = scale * float(np.sqrt(sum((semi[k] * (axes[k] @ right)) ** 2 for k in range(3))))
        half_y = scale * float(np.sqrt(sum((semi[k] * (axes[k] @ up)) ** 2 for k in range(3))))
        size = colour.shape[0]
        x0, x1 = max(0, int(cx - half_x)), min(size, int(cx + half_x) + 1)
        y0, y1 = max(0, int(cy - half_y)), min(size, int(cy + half_y) + 1)
        if x0 >= x1 or y0 >= y1:
            return
        # Camera-frame components of each principal axis.
        r = [float(axes[k] @ right) for k in range(3)]
        u = [float(axes[k] @ up) for k in range(3)]
        v = [float(axes[k] @ view_dir) for k in range(3)]
        a_coeff = sum((v[k] / semi[k]) ** 2 for k in range(3))
        if a_coeff <= 0.0:
            return
        # Solve |S^-1 R^T (q)|^2 = 1 along the view ray q = image-plane + t*view_dir.
        ys, xs = np.mgrid[y0:y1, x0:x1]
        offset_right = (xs - cx) / scale
        offset_up = -(ys - cy) / scale
        base = [offset_right * r[k] + offset_up * u[k] for k in range(3)]
        b_coeff = sum(2.0 * base[k] * v[k] / semi[k] ** 2 for k in range(3))
        c_coeff = sum((base[k] / semi[k]) ** 2 for k in range(3)) - 1.0
        disc = b_coeff * b_coeff - 4.0 * a_coeff * c_coeff
        inside = disc >= 0.0
        if not inside.any():
            return
        t = (-b_coeff + np.sqrt(np.clip(disc, 0.0, None))) / (2.0 * a_coeff)
        surf_depth = cd + t
        sub = depth[y0:y1, x0:x1]
        update = inside & (surf_depth > sub)
        if not update.any():
            return
        local = [(base[k] + t * v[k]) / semi[k] for k in range(3)]
        nx = sum(local[k] / semi[k] * axes[k][0] for k in range(3))
        ny = sum(local[k] / semi[k] * axes[k][1] for k in range(3))
        nz = sum(local[k] / semi[k] * axes[k][2] for k in range(3))
        norm = np.sqrt(nx * nx + ny * ny + nz * nz)
        norm = np.where(norm > 1e-12, norm, 1.0)
        normal = np.stack((
            (nx * right[0] + ny * right[1] + nz * right[2]) / norm,
            (nx * up[0] + ny * up[1] + nz * up[2]) / norm,
            (nx * view_dir[0] + ny * view_dir[1] + nz * view_dir[2]) / norm,
        ), axis=-1)
        intensity = _diffuse_intensity(normal)[..., None]
        base_rgb = RasterStructureRenderer._base_colours(xs - cx, ys - cy, ell.colour, ell.wedges)
        shade = np.clip(base_rgb * intensity + _specular(normal)[..., None], 0, 1)
        sub[update] = surf_depth[update]
        colour[y0:y1, x0:x1][update] = shade[update]

    @staticmethod
    def _capsule(colour, depth, project, scale, p0, p1, radius, colour0, colour1) -> None:
        size = colour.shape[0]
        ax, ay, ad = project(p0)
        bx, by, bd = project(p1)
        r_px = max(radius * scale, 0.6)
        x0 = max(0, int(min(ax, bx) - r_px))
        x1 = min(size, int(max(ax, bx) + r_px) + 1)
        y0 = max(0, int(min(ay, by) - r_px))
        y1 = min(size, int(max(ay, by) + r_px) + 1)
        if x0 >= x1 or y0 >= y1:
            return
        ys, xs = np.mgrid[y0:y1, x0:x1]
        seg = np.array([bx - ax, by - ay], dtype=float)
        length2 = float(seg @ seg) or 1.0
        t = np.clip(((xs - ax) * seg[0] + (ys - ay) * seg[1]) / length2, 0.0, 1.0)
        proj_x = ax + t * seg[0]
        proj_y = ay + t * seg[1]
        dist = np.hypot(xs - proj_x, ys - proj_y)
        inside = dist <= r_px
        if not inside.any():
            return
        nz = np.sqrt(np.clip(1.0 - (dist / r_px) ** 2, 0.0, 1.0))
        surf_depth = ad + t * (bd - ad) + nz * radius
        sub = depth[y0:y1, x0:x1]
        update = inside & (surf_depth > sub)
        if not update.any():
            return
        # Directional cylinder shading: normal perpendicular to the projected
        # axis (image y is down), with the bulge as the toward-camera component.
        normal = np.stack(((xs - proj_x) / r_px, -(ys - proj_y) / r_px, nz), axis=-1)
        intensity = _diffuse_intensity(normal)[..., None]
        c0 = np.asarray(colour0, dtype=np.float32) / 255.0
        c1 = np.asarray(colour1, dtype=np.float32) / 255.0
        base = np.where((t < 0.5)[..., None], c0, c1)
        shade = np.clip(base * intensity, 0, 1)
        sub[update] = surf_depth[update]
        colour[y0:y1, x0:x1][update] = shade[update]

    @staticmethod
    def _triangle(colour, depth, v0, v1, v2, shade) -> None:
        """Z-test and fill one flat-shaded triangle from projected vertices."""
        size = colour.shape[0]
        (x0, y0, d0), (x1, y1, d1), (x2, y2, d2) = v0, v1, v2
        min_x = max(0, int(min(x0, x1, x2)))
        max_x = min(size, int(max(x0, x1, x2)) + 1)
        min_y = max(0, int(min(y0, y1, y2)))
        max_y = min(size, int(max(y0, y1, y2)) + 1)
        if min_x >= max_x or min_y >= max_y:
            return
        denom = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
        if abs(denom) < 1e-9:
            return
        ys, xs = np.mgrid[min_y:max_y, min_x:max_x]
        w0 = ((y1 - y2) * (xs - x2) + (x2 - x1) * (ys - y2)) / denom
        w1 = ((y2 - y0) * (xs - x2) + (x0 - x2) * (ys - y2)) / denom
        w2 = 1.0 - w0 - w1
        inside = (w0 >= 0.0) & (w1 >= 0.0) & (w2 >= 0.0)
        if not inside.any():
            return
        tri_depth = w0 * d0 + w1 * d1 + w2 * d2
        sub = depth[min_y:max_y, min_x:max_x]
        update = inside & (tri_depth > sub)
        if not update.any():
            return
        sub[update] = tri_depth[update]
        colour[min_y:max_y, min_x:max_x][update] = shade

    def _arrow(self, colour, depth, project, basis, origin, vector, extent, rgb) -> None:
        """Draw a shaft cylinder and head cone as 3D triangles (orientation-safe).

        Thickness and head size are fractions of ``extent`` (the fit extent), so
        the arrow is a constant on-screen size in every cell. ``vector`` already
        runs to the arrow tip (cell edge plus overhang).
        """
        right, up, view_dir = basis
        length = float(np.linalg.norm(vector))
        if length < 1e-9:
            return
        axis = vector / length
        perp = np.array([0.0, 0.0, 1.0]) if abs(axis[2]) < 0.9 else np.array([0.0, 1.0, 0.0])
        u = _unit(np.cross(perp, axis))
        v = np.cross(axis, u)
        shaft_r = _AXIS_SHAFT_RADIUS_FRAC * extent
        head_r = _AXIS_HEAD_RADIUS_FRAC * extent
        base = origin + axis * max(length - _AXIS_HEAD_LENGTH_FRAC * extent, 1e-3)
        tip = origin + vector
        flat = np.asarray(rgb, dtype=np.float32) / 255.0

        def shade_for(world_normal: np.ndarray) -> np.ndarray:
            cam = np.array([world_normal @ right, world_normal @ up, world_normal @ view_dir])
            return np.clip(flat * float(_diffuse_intensity(cam)), 0.0, 1.0)

        segments = 32
        ring = [np.cos(angle) * u + np.sin(angle) * v
                for angle in (2.0 * np.pi * i / segments for i in range(segments))]
        for i in range(segments):
            d0 = ring[i]
            d1 = ring[(i + 1) % segments]
            shaft_shade = shade_for(_unit(d0 + d1))
            o0 = project(tuple(origin + shaft_r * d0))
            o1 = project(tuple(origin + shaft_r * d1))
            s0 = project(tuple(base + shaft_r * d0))
            s1 = project(tuple(base + shaft_r * d1))
            self._triangle(colour, depth, o0, o1, s1, shaft_shade)
            self._triangle(colour, depth, o0, s1, s0, shaft_shade)
            b0 = base + head_r * d0
            b1 = base + head_r * d1
            normal = _unit(np.cross(b1 - b0, tip - b0))
            if normal @ (d0 + d1) < 0.0:
                normal = -normal
            self._triangle(colour, depth, project(tuple(b0)), project(tuple(b1)),
                           project(tuple(tip)), shade_for(normal))
            self._triangle(colour, depth, project(tuple(base)), project(tuple(b1)),
                           project(tuple(b0)), shade_for(-axis))

    def _axes(self, colour, depth, project, basis, axes, extent, max_atom_r) -> None:
        origin = np.asarray(axes.origin, dtype=float)
        vectors = [np.asarray(a.vector, dtype=float) for a in axes.axes]
        # Recover the longest cell edge (the builder adds a 0.3*max overhang).
        max_axis = max((float(np.linalg.norm(v)) for v in vectors), default=1.0) / 1.3
        head_len = _AXIS_HEAD_LENGTH_FRAC * extent
        # Overhang clears the largest atom (so corner atoms never hide the head),
        # plus the head length and a small gap.
        overhang = max(_AXIS_OVERHANG_FRAC * extent, max_atom_r + head_len + _AXIS_GAP_FRAC * extent)
        for arrow, vector in zip(axes.axes, vectors):
            length = float(np.linalg.norm(vector))
            if length < 1e-9:
                continue
            axis = vector / length
            axis_len = max(length - 0.3 * max_axis, 1e-3)
            self._arrow(colour, depth, project, basis, origin,
                        axis * (axis_len + overhang), extent, arrow.colour)
