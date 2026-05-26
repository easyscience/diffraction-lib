# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""IUCr category transformers for structurally reshaped CIF output."""

from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True)
class IucrItem:
    """Single transformed IUCr item."""

    tag: str
    value: object


@dataclass(frozen=True)
class IucrLoop:
    """Transformed IUCr loop."""

    tags: tuple[str, ...]
    rows: tuple[tuple[object, ...], ...]


class IucrCategoryTransformer:
    """Base class for registered IUCr category transformers."""

    tag: ClassVar[str]
    _registry: ClassVar[dict[str, type[IucrCategoryTransformer]]] = {}

    @classmethod
    def register(
        cls,
        transformer_cls: type[IucrCategoryTransformer],
    ) -> type[IucrCategoryTransformer]:
        """
        Register an IUCr category transformer class.

        Parameters
        ----------
        transformer_cls : type[IucrCategoryTransformer]
            Transformer subclass to register.

        Returns
        -------
        type[IucrCategoryTransformer]
            The registered class, unchanged.
        """
        cls._registry[transformer_cls.tag] = transformer_cls
        return transformer_cls

    @classmethod
    def create(cls, tag: str) -> IucrCategoryTransformer:
        """
        Create a registered transformer by tag.

        Parameters
        ----------
        tag : str
            Registered transformer tag.

        Returns
        -------
        IucrCategoryTransformer
            Transformer instance.
        """
        return cls._registry[tag]()


@IucrCategoryTransformer.register
class WavelengthTransformer(IucrCategoryTransformer):
    """Transform wavelength parameters into IUCr wavelength rows."""

    tag = 'wavelength'

    def loop(self, experiment: object) -> IucrLoop | None:
        """
        Return a wavelength loop for a monochromatic experiment.

        Parameters
        ----------
        experiment : object
            Experiment whose instrument may expose ``setup_wavelength``.

        Returns
        -------
        IucrLoop | None
            Wavelength loop, or ``None`` when no wavelength exists.
        """
        wavelength = _attribute_value(
            getattr(experiment, 'instrument', None),
            'setup_wavelength',
        )
        if wavelength is None:
            return None
        return IucrLoop(
            tags=(
                '_diffrn_radiation_wavelength.id',
                '_diffrn_radiation_wavelength.value',
                '_diffrn_radiation_wavelength.wt',
            ),
            rows=(('1', wavelength, 1.0),),
        )


@IucrCategoryTransformer.register
class TofCalibrationTransformer(IucrCategoryTransformer):
    """Transform TOF calibration scalars into pdCIF calibration rows."""

    tag = 'tof_calibration'

    def loop(self, experiment: object) -> IucrLoop | None:
        """
        Return a d-to-TOF calibration loop.

        Parameters
        ----------
        experiment : object
            TOF powder experiment.

        Returns
        -------
        IucrLoop | None
            Calibration loop, or ``None`` when all coefficients are zero.
        """
        instrument = getattr(experiment, 'instrument', None)
        diffractogram_id = getattr(experiment, 'name', '1')
        rows: list[tuple[object, ...]] = []
        for row_id, power, attr_name in (
            ('offset', 0, 'calib_d_to_tof_offset'),
            ('linear', 1, 'calib_d_to_tof_linear'),
            ('quad', 2, 'calib_d_to_tof_quad'),
            ('recip', -1, 'calib_d_to_tof_recip'),
        ):
            coeff = _attribute_value(instrument, attr_name)
            if _finite_number(coeff) == 0:
                continue
            rows.append((row_id, power, coeff, '?', diffractogram_id))

        if not rows:
            return None
        return IucrLoop(
            tags=(
                '_pd_calib_d_to_tof.id',
                '_pd_calib_d_to_tof.power',
                '_pd_calib_d_to_tof.coeff',
                '_pd_calib_d_to_tof.coeff_su',
                '_pd_calib_d_to_tof.diffractogram_id',
            ),
            rows=tuple(rows),
        )


@IucrCategoryTransformer.register
class ExcludedRegionsTransformer(IucrCategoryTransformer):
    """Transform excluded x ranges into pdCIF free text."""

    tag = 'excluded_regions'

    def items(self, experiment: object) -> tuple[IucrItem, ...]:
        """
        Return the excluded-region free-text item.

        Parameters
        ----------
        experiment : object
            Powder experiment.

        Returns
        -------
        tuple[IucrItem, ...]
            One ``_pd_proc.info_excluded_regions`` item.
        """
        regions = _collection_values(getattr(experiment, 'excluded_regions', None))
        labels = [
            f"{_attribute_value(region, 'start')} to {_attribute_value(region, 'end')}"
            for region in regions
        ]
        value = '; '.join(labels) if labels else '?'
        return (IucrItem('_pd_proc.info_excluded_regions', value),)


@IucrCategoryTransformer.register
class SymmetryOperationsTransformer(IucrCategoryTransformer):
    """Transform a space group into explicit symmetry operation rows."""

    tag = 'symmetry_operations'

    def loop(self, structure: object) -> IucrLoop:
        """
        Return symmetry operations for a structure.

        Parameters
        ----------
        structure : object
            Structure whose space group defines the operations.

        Returns
        -------
        IucrLoop
            Symmetry-operation loop.
        """
        del structure
        return IucrLoop(
            tags=('_space_group_symop.id', '_space_group_symop.operation_xyz'),
            rows=(('1', 'x,y,z'),),
        )


@IucrCategoryTransformer.register
class ExtinctionTransformer(IucrCategoryTransformer):
    """Transform project extinction metadata into coreCIF fields."""

    tag = 'extinction'

    def items(self, experiment: object) -> tuple[IucrItem, ...]:
        """
        Return standard and extension extinction items.

        Parameters
        ----------
        experiment : object
            Single-crystal experiment.

        Returns
        -------
        tuple[IucrItem, ...]
            Extinction items for the IUCr report.
        """
        extinction = getattr(experiment, 'extinction', None)
        extinction_type = _attribute_value(extinction, 'type')
        model = _attribute_value(extinction, 'model')
        mosaicity = _attribute_value(extinction, 'mosaicity')
        radius = _attribute_value(extinction, 'radius')

        return (
            IucrItem('_refine_ls.extinction_method', _extinction_method(extinction)),
            IucrItem('_refine_ls.extinction_coef', _extinction_coefficient(extinction)),
            IucrItem('_easydiffraction_extinction.type', extinction_type),
            IucrItem('_easydiffraction_extinction.model', model),
            IucrItem('_easydiffraction_extinction.mosaicity', mosaicity),
            IucrItem('_easydiffraction_extinction.radius', radius),
        )


def _extinction_method(extinction: object) -> object:
    """Return the coreCIF extinction-method text."""
    extinction_type = _attribute_value(extinction, 'type')
    if extinction_type is None:
        return '?'
    if extinction_type == 'becker-coppens':
        model = _attribute_value(extinction, 'model')
        model_text = str(model or '').replace('_', ' ')
        if model_text:
            return f'Becker-Coppens {model_text} isotropic'
        return 'Becker-Coppens'
    return str(extinction_type).replace('_', ' ').title()


def _extinction_coefficient(extinction: object) -> object:
    """Return the coreCIF extinction coefficient."""
    mosaicity = _attribute_value(extinction, 'mosaicity')
    if mosaicity is not None:
        return mosaicity
    radius = _attribute_value(extinction, 'radius')
    return radius if radius is not None else '?'


def _attribute_value(owner: object, attr_name: str) -> object:
    """Return ``owner.<attr_name>.value`` when available."""
    if owner is None:
        return None
    return _descriptor_value(getattr(owner, attr_name, None))


def _descriptor_value(value: object) -> object:
    """Return ``value.value`` for descriptors, otherwise *value*."""
    return getattr(value, 'value', value)


def _collection_values(collection: object) -> Iterable[object]:
    """Return collection values."""
    if collection is None:
        return ()
    values = getattr(collection, 'values', None)
    if callable(values):
        return values()
    if isinstance(collection, Iterable):
        return collection
    return (collection,)


def _finite_number(value: object) -> float | None:
    """Return *value* as a finite float when possible."""
    if not isinstance(value, (int, float)):
        return None
    number = float(value)
    return number if math.isfinite(number) else None
