# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""
Line-segment background model.

Interpolate user-specified points to form a background curve.
"""

from __future__ import annotations

import numpy as np
from scipy.interpolate import interp1d
from scipy.signal import find_peaks
from scipy.signal import peak_widths

from easydiffraction.core.category import CategoryItem
from easydiffraction.core.display_handler import DisplayHandler
from easydiffraction.core.metadata import CalculatorSupport
from easydiffraction.core.metadata import Compatibility
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import RangeValidator
from easydiffraction.core.validation import RegexValidator
from easydiffraction.core.variable import NumericDescriptor
from easydiffraction.core.variable import Parameter
from easydiffraction.core.variable import StringDescriptor
from easydiffraction.datablocks.experiment.categories.background import enums
from easydiffraction.datablocks.experiment.categories.background import estimate
from easydiffraction.datablocks.experiment.categories.background.base import BackgroundBase
from easydiffraction.datablocks.experiment.categories.background.factory import BackgroundFactory
from easydiffraction.datablocks.experiment.item.enums import BeamModeEnum
from easydiffraction.datablocks.experiment.item.enums import CalculatorEnum
from easydiffraction.io.cif.handler import CifHandler
from easydiffraction.utils.logging import console
from easydiffraction.utils.logging import log
from easydiffraction.utils.utils import render_table


class LineSegment(CategoryItem):
    """Single background control point for interpolation."""

    _category_code = 'background'
    _category_entry_name = 'id'

    def __init__(self) -> None:
        super().__init__()

        self._id = StringDescriptor(
            name='id',
            description='Identifier for this background line segment',
            value_spec=AttributeSpec(
                default='0',
                # TODO: the following pattern is valid for dict key
                #  (keywords are not checked). CIF label is less strict.
                #  Do we need conversion between CIF and internal label?
                validator=RegexValidator(pattern=r'^[A-Za-z0-9_]*$'),
            ),
            cif_handler=CifHandler(names=['_pd_background.id']),
            display_handler=DisplayHandler(
                display_name='ID',
                latex_name='ID',
            ),
        )
        self._x = NumericDescriptor(
            name='x',
            description='X-coordinates used to create many straight-line segments',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            cif_handler=CifHandler(
                names=[
                    '_pd_background.line_segment_X',
                    '_pd_background_line_segment_X',
                ]
            ),
            display_handler=DisplayHandler(
                display_name='x',
                latex_name='$x$',
            ),
        )
        self._y = Parameter(
            name='y',  # TODO: rename to intensity
            description='Intensity used to create many straight-line segments',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),  # TODO: rename to intensity
            cif_handler=CifHandler(
                names=[
                    '_pd_background.line_segment_intensity',
                    '_pd_background_line_segment_intensity',
                ]
            ),
            display_handler=DisplayHandler(
                display_name='Intensity',
                latex_name='Intensity',
            ),
        )

    # ------------------------------------------------------------------
    #  Public properties
    # ------------------------------------------------------------------

    @property
    def id(self) -> StringDescriptor:
        """
        Identifier for this background line segment.

        Reading this property returns the underlying
        ``StringDescriptor`` object. Assigning to it updates the
        parameter value.
        """
        return self._id

    @id.setter
    def id(self, value: str) -> None:
        self._id.value = value

    @property
    def x(self) -> NumericDescriptor:
        """
        X-coordinates used to create many straight-line segments.

        Reading this property returns the underlying
        ``NumericDescriptor`` object. Assigning to it updates the
        parameter value.
        """
        return self._x

    @x.setter
    def x(self, value: float) -> None:
        self._x.value = value

    @property
    def y(self) -> Parameter:
        """
        Intensity used to create many straight-line segments.

        Reading this property returns the underlying ``Parameter``
        object. Assigning to it updates the parameter value.
        """
        return self._y

    @y.setter
    def y(self, value: float) -> None:
        self._y.value = value


def _resolve_method(method: str) -> str:
    """
    Validate a method name and resolve ``auto``.

    Parameters
    ----------
    method : str
        Requested method; one of the ``BackgroundEstimatorMethodEnum``
        values.

    Returns
    -------
    str
        The resolved Stage-1 method (``auto`` becomes ``arpls``).

    Raises
    ------
    ValueError
        If ``method`` is not a known estimator method.
    """
    try:
        chosen = enums.BackgroundEstimatorMethodEnum(method)
    except ValueError as exc:
        valid = ', '.join(member.value for member in enums.BackgroundEstimatorMethodEnum)
        msg = f'Unknown background method {method!r}. Choose one of: {valid}.'
        raise ValueError(msg) from exc
    if chosen is enums.BackgroundEstimatorMethodEnum.AUTO:
        return enums.BackgroundEstimatorMethodEnum.ARPLS.value
    return chosen.value


def _model_peak_mask(peak_only: np.ndarray) -> np.ndarray:
    """
    Build a forbidden-anchor mask from a peak-only model array.

    Peaks in the peak-only model are detected and widened by their own
    full-width-at-half-maximum; Stage 2 must not place a non-endpoint
    anchor on any masked sample.

    Parameters
    ----------
    peak_only : np.ndarray
        Peak-only model intensities (``intensity_calc - intensity_bkg``).

    Returns
    -------
    np.ndarray
        Boolean mask aligned with ``peak_only``.
    """
    mask = np.zeros(peak_only.size, dtype=bool)
    peaks, _ = find_peaks(peak_only)
    if not peaks.size:
        return mask
    widths = peak_widths(peak_only, peaks, rel_height=0.5)[0]
    for index, peak_width in zip(peaks, widths, strict=True):
        half = int(np.ceil(peak_width))
        lo = max(0, int(index) - half)
        hi = int(index) + half + 1
        mask[lo:hi] = True
    return mask


@BackgroundFactory.register
class LineSegmentBackground(BackgroundBase):
    """Linear-interpolation background between user-defined points."""

    type_info = TypeInfo(
        tag='line-segment',
        description='Linear interpolation between points',
    )
    compatibility = Compatibility(
        beam_mode=frozenset({BeamModeEnum.CONSTANT_WAVELENGTH, BeamModeEnum.TIME_OF_FLIGHT}),
    )
    calculator_support = CalculatorSupport(
        calculators=frozenset({CalculatorEnum.CRYSPY, CalculatorEnum.CRYSFML}),
    )

    def __init__(self) -> None:
        super().__init__(item_type=LineSegment)

    def _update(
        self,
        *,
        called_by_minimizer: bool = False,
    ) -> None:
        """Interpolate background points over x data."""
        del called_by_minimizer

        data = self._parent.data
        x = data.x

        if not self._items:
            log.debug('No background points found. Setting background to zero.')
            data._set_intensity_bkg(np.zeros_like(x))
            return

        segments_x = np.array([point.x.value for point in self._items])
        segments_y = np.array([point.y.value for point in self._items])
        interp_func = interp1d(
            segments_x,
            segments_y,
            kind='linear',
            bounds_error=False,
            fill_value=(segments_y[0], segments_y[-1]),
        )

        y = interp_func(x)
        data._set_intensity_bkg(y)

    def auto_estimate(
        self,
        *,
        method: str = 'auto',
        width: float | None = None,
        smoothness: float | None = None,
        n_points: int | None = None,
        use_model: bool = True,
    ) -> None:
        """
        Detect background control points from the measured pattern.

        Builds a peak-insensitive background curve and thins it to a
        sparse set of fixed line-segment points, overwriting any existing
        ones. Heights come from the de-peaked curve, clipped to the
        measured intensities so they never eat into peaks. After at least
        one calculation, ``use_model`` lets the fitted model place better
        points across overlapped regions.

        Parameters
        ----------
        method : str, optional
            Estimation method: ``auto`` (default, resolves to ``arpls``),
            ``snip``, ``arpls`` or ``fabc``.
        width : float or None, optional
            Peak width in points; measured from the data when ``None``.
        smoothness : float or None, optional
            Backend smoothing override; derived when ``None``.
        n_points : int or None, optional
            Maximum number of points; uncapped when ``None``.
        use_model : bool, optional
            When a calculation has run, subtract the fitted peaks before
            estimating so anchors land in true inter-peak gaps.
        """
        resolved = _resolve_method(method)
        data = self._parent.data
        x = np.asarray(data.x, dtype=float)
        intensity_meas = np.asarray(data.intensity_meas, dtype=float)
        intensity_calc = np.asarray(data.intensity_calc, dtype=float)

        if use_model and np.any(intensity_calc):
            peak_only = intensity_calc - np.asarray(data.intensity_bkg, dtype=float)
            y = intensity_meas - peak_only
            peaks = _model_peak_mask(peak_only)
        else:
            y = intensity_meas
            peaks = None

        result = estimate.estimate_background_curve(
            x,
            y,
            method=resolved,
            peaks=peaks,
            width=width,
            smoothness=smoothness,
            n_points=n_points,
        )

        anchor_x = result.anchors[:, 0]
        measured = np.interp(anchor_x, x, intensity_meas)
        heights = np.clip(result.anchors[:, 1], 0.0, measured)

        if len(self):
            log.info('Replacing existing background points with a new estimate.')
        self.clear()
        for index, (point_x, height) in enumerate(zip(anchor_x, heights, strict=True), start=1):
            self.create(id=str(index), x=float(point_x), y=float(height))
        for point in self._items:
            point.y.free = False

        count = len(self)
        width_pts = result.width
        summary = f'Background estimate: {resolved}, {count} points, width {width_pts:.0f} pts'
        log.info(summary)

    def show(self) -> None:
        """Print a table of control points (x, intensity)."""
        columns_headers: list[str] = ['X', 'Intensity']
        columns_alignment = ['left', 'left']
        columns_data: list[list[float]] = [[p.x.value, p.y.value] for p in self._items]

        console.paragraph('Line-segment background points')
        render_table(
            columns_headers=columns_headers,
            columns_alignment=columns_alignment,
            columns_data=columns_data,
        )
