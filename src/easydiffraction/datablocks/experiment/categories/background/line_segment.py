# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""
Line-segment background model.

Interpolate user-specified points to form a background curve.
"""

from __future__ import annotations

from typing import NamedTuple

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
from easydiffraction.io.cif.handler import TagSpec
from easydiffraction.utils.logging import console
from easydiffraction.utils.logging import log
from easydiffraction.utils.utils import render_table

_MIN_ANCHOR_POINTS = 2  # Minimum line-segment anchors (the two endpoints)


class _EstimationArrays(NamedTuple):
    """Included data arrays used by the background estimator."""

    x: np.ndarray
    intensity_meas: np.ndarray
    intensity_calc: np.ndarray
    intensity_bkg: np.ndarray


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
            tags=TagSpec(edi_names=['_background.id'], cif_names=['_pd_background.id']),
            display_handler=DisplayHandler(
                display_name='ID',
                latex_name='ID',
            ),
        )
        self._position = NumericDescriptor(
            name='position',
            description='Position used to create many straight-line segments',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            tags=TagSpec(
                edi_names=['_background.position'],
                cif_names=['_pd_background.line_segment_X', '_pd_background_line_segment_X'],
            ),
            display_handler=DisplayHandler(
                display_name='Position',
                latex_name='$x$',
            ),
        )
        self._intensity = Parameter(
            name='intensity',
            description='Intensity used to create many straight-line segments',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            tags=TagSpec(
                edi_names=['_background.intensity'],
                cif_names=[
                    '_pd_background.line_segment_intensity',
                    '_pd_background_line_segment_intensity',
                ],
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
    def position(self) -> NumericDescriptor:
        """
        Position used to create many straight-line segments.

        Reading this property returns the underlying
        ``NumericDescriptor`` object. Assigning to it updates the
        parameter value.
        """
        return self._position

    @position.setter
    def position(self, value: float) -> None:
        self._position.value = value

    @property
    def intensity(self) -> Parameter:
        """
        Intensity used to create many straight-line segments.

        Reading this property returns the underlying ``Parameter``
        object. Assigning to it updates the parameter value.
        """
        return self._intensity

    @intensity.setter
    def intensity(self, value: float) -> None:
        self._intensity.value = value


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


def _validate_overrides(
    width: float | None,
    smoothness: float | None,
    n_points: int | None,
) -> None:
    """
    Validate the public numeric overrides of ``auto_estimate``.

    Parameters
    ----------
    width : float | None
        Peak width override; must be positive when supplied.
    smoothness : float | None
        Smoothing override; must be positive when supplied.
    n_points : int | None
        Anchor cap; must be an integer ``>= 2`` when supplied.

    Raises
    ------
    ValueError
        If any supplied override is out of range.
    """
    if width is not None and width <= 0:
        msg = f'width must be positive, got {width!r}.'
        raise ValueError(msg)
    if smoothness is not None and smoothness <= 0:
        msg = f'smoothness must be positive, got {smoothness!r}.'
        raise ValueError(msg)
    if n_points is not None and (not isinstance(n_points, int) or n_points < _MIN_ANCHOR_POINTS):
        msg = f'n_points must be an integer >= 2, got {n_points!r}.'
        raise ValueError(msg)


def _model_peak_mask(peak_only: np.ndarray) -> np.ndarray:
    """
    Build a forbidden-anchor mask from a peak-only model array.

    Peaks in the peak-only model are detected and widened by their own
    full-width-at-half-maximum; Stage 2 must not place a non-endpoint
    anchor on any masked sample.

    Parameters
    ----------
    peak_only : np.ndarray
        Peak-only model intensities (``intensity_calc -
        intensity_bkg``).

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


def _sync_excluded_regions(parent: object) -> None:
    """
    Apply pending excluded-region edits before reading active arrays.
    """
    excluded_regions = getattr(parent, 'excluded_regions', None)
    update = getattr(excluded_regions, '_update', None)
    has_regions = bool(getattr(excluded_regions, '_items', ()))
    last_signature = getattr(excluded_regions, '_last_applied_signature', None)
    had_applied_regions = bool(last_signature and last_signature[1])
    if update is not None and (has_regions or had_applied_regions):
        update(called_by_minimizer=False)


def _status_included_mask(data: object, x: np.ndarray) -> np.ndarray | None:
    """
    Return a ``calc_status == 'incl'`` mask aligned with ``x``.
    """
    try:
        calc_status = np.asarray(data.calc_status)
    except AttributeError:
        return None
    if calc_status.shape != x.shape:
        return None
    return calc_status == 'incl'


def _point_descriptor_values(data: object, name: str) -> np.ndarray | None:
    """
    Return all-point descriptor values from ``data._items``.
    """
    items = getattr(data, '_items', None)
    if items is None:
        return None

    values = []
    for item in items:
        descriptor = getattr(item, name, None)
        if descriptor is None:
            return None
        values.append(descriptor.value)
    return np.asarray(values, dtype=float)


def _aligned_intensity_array(
    data: object,
    name: str,
    public_values: np.ndarray,
    full_shape: tuple[int, ...],
) -> np.ndarray | None:
    """
    Return an array aligned with the full grid, if available.
    """
    values = _point_descriptor_values(data, name)
    if values is None:
        values = public_values
    if values.shape != full_shape:
        return None
    return values


def _active_estimation_arrays(
    data: object,
) -> _EstimationArrays:
    """
    Return included arrays for background estimation.

    Powder data properties are already included-only after
    ``calc_status`` has been applied. When a full-grid status array is
    available, use it directly so excluded points cannot leak into
    background anchors.
    """
    public_x = np.asarray(data.x, dtype=float)
    public_meas = np.asarray(data.intensity_meas, dtype=float)
    public_calc = np.asarray(data.intensity_calc, dtype=float)
    public_bkg = np.asarray(data.intensity_bkg, dtype=float)

    full_x = np.asarray(getattr(data, 'unfiltered_x', public_x), dtype=float)
    included = _status_included_mask(data, full_x)
    if included is None:
        return _EstimationArrays(public_x, public_meas, public_calc, public_bkg)

    full_meas = _aligned_intensity_array(data, 'intensity_meas', public_meas, full_x.shape)
    full_calc = _aligned_intensity_array(data, 'intensity_calc', public_calc, full_x.shape)
    full_bkg = _aligned_intensity_array(data, 'intensity_bkg', public_bkg, full_x.shape)
    if full_meas is None or full_calc is None or full_bkg is None:
        return _EstimationArrays(public_x, public_meas, public_calc, public_bkg)

    return _EstimationArrays(
        full_x[included],
        full_meas[included],
        full_calc[included],
        full_bkg[included],
    )


def _estimate_curve_inputs(
    arrays: _EstimationArrays,
    *,
    use_model: bool,
) -> tuple[np.ndarray, np.ndarray | None]:
    """
    Return estimator y-values and a forbidden-peak mask.
    """
    if use_model and np.any(arrays.intensity_calc):
        peak_only = arrays.intensity_calc - arrays.intensity_bkg
        return arrays.intensity_meas - peak_only, _model_peak_mask(peak_only)
    return arrays.intensity_meas, None


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

        segments_x = np.array([point.position.value for point in self._items])
        segments_y = np.array([point.intensity.value for point in self._items])
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
        sparse set of fixed line-segment points, overwriting any
        existing ones. Heights come from the de-peaked curve, clipped to
        the measured intensities so they never eat into peaks. After at
        least one calculation, ``use_model`` lets the fitted model place
        better points across overlapped regions.

        Parameters
        ----------
        method : str, default='auto'
            Estimation method: ``auto`` (default, resolves to
            ``arpls``), ``snip``, ``arpls`` or ``fabc``.
        width : float | None, default=None
            Peak width in points; measured from the data when ``None``.
        smoothness : float | None, default=None
            Backend smoothing override; derived when ``None``.
        n_points : int | None, default=None
            Maximum number of points; uncapped when ``None``.
        use_model : bool, default=True
            When a calculation has run, subtract the fitted peaks before
            estimating so anchors land in true inter-peak gaps.
        """
        resolved = _resolve_method(method)
        _validate_overrides(width, smoothness, n_points)
        _sync_excluded_regions(self._parent)
        data = self._parent.data
        arrays = _active_estimation_arrays(data)
        if arrays.x.size == 0:
            log.warning('No active data points; cannot estimate a background.')
            return

        y, peaks = _estimate_curve_inputs(arrays, use_model=use_model)

        result = estimate.estimate_background_curve(
            arrays.x,
            y,
            method=resolved,
            peaks=peaks,
            width=width,
            smoothness=smoothness,
            n_points=n_points,
        )

        anchor_x = result.anchors[:, 0]
        measured = np.interp(anchor_x, arrays.x, arrays.intensity_meas)
        heights = np.clip(result.anchors[:, 1], 0.0, measured)

        if len(self):
            log.info('Replacing existing background points with a new estimate.')
        self.clear()
        for index, (point_x, height) in enumerate(zip(anchor_x, heights, strict=True), start=1):
            self.create(id=str(index), position=float(point_x), intensity=float(height))
        for point in self._items:
            point.intensity.free = False

        log.info(
            f'Background estimate: {resolved}, {len(self)} points, width {result.width:.0f} pts'
        )

    def show(self) -> None:
        """Print a table of control points (position, intensity)."""
        columns_headers: list[str] = ['Position', 'Intensity']
        columns_alignment = ['left', 'left']
        columns_data: list[list[float]] = [
            [p.position.value, p.intensity.value] for p in self._items
        ]

        console.paragraph('Line-segment background points')
        render_table(
            columns_headers=columns_headers,
            columns_alignment=columns_alignment,
            columns_data=columns_data,
        )
