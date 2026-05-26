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

    def items(self, experiment: object) -> tuple[IucrItem, ...] | None:
        """
        Return wavelength items for a monochromatic experiment.

        Parameters
        ----------
        experiment : object
            Experiment whose instrument may expose ``setup_wavelength``.

        Returns
        -------
        tuple[IucrItem, ...] | None
            Wavelength items, or ``None`` when no wavelength exists.
        """
        wavelength = _attribute_value(
            getattr(experiment, 'instrument', None),
            'setup_wavelength',
        )
        if wavelength is None:
            return None
        return (
            IucrItem('_diffrn_radiation_wavelength.id', '1'),
            IucrItem('_diffrn_radiation_wavelength.value', wavelength),
            IucrItem('_diffrn_radiation_wavelength.wt', 1.0),
        )

    def loop(self, experiment: object) -> IucrLoop | None:
        """
        Return a wavelength loop for multi-wavelength experiments.

        Parameters
        ----------
        experiment : object
            Experiment whose instrument may expose multiple wavelengths.

        Returns
        -------
        IucrLoop | None
            Wavelength loop, or ``None`` for monochromatic experiments.
        """
        del experiment
        return None


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
            Calibration loop, or ``None`` when all coefficients are
            zero.
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

        extension_items = _iucr_items(
            extinction,
            (
                ('type', extinction_type),
                ('model', model),
                ('mosaicity', mosaicity),
                ('radius', radius),
            ),
        )

        return (*_standard_extinction_items(extinction), *extension_items)


def _standard_extinction_items(extinction: object) -> tuple[IucrItem, ...]:
    """Return coreCIF extinction items."""
    items = [
        IucrItem('_refine_ls.extinction_method', _extinction_method(extinction)),
        IucrItem('_refine_ls.extinction_coef', _extinction_coefficient(extinction)),
    ]
    special_details = _extinction_special_details(extinction)
    if special_details is not None:
        items.append(IucrItem('_refine.special_details', special_details))
    return tuple(items)


def _extinction_method(extinction: object) -> object:
    """Return the coreCIF extinction-method text."""
    extinction_type = _attribute_value(extinction, 'type')
    if extinction_type is None:
        return '?'
    extinction_name = _normalised_text(extinction_type)
    if extinction_name == 'becker coppens':
        return _becker_coppens_method(extinction)
    if extinction_name == 'zachariasen':
        return 'Zachariasen'
    return str(extinction_type).replace('_', ' ').replace('-', ' ').title()


def _extinction_coefficient(extinction: object) -> object:
    """Return the coreCIF extinction coefficient."""
    mosaicity = _attribute_value(extinction, 'mosaicity')
    radius = _attribute_value(extinction, 'radius')
    if _is_becker_coppens(extinction) and _is_mixed_extinction(extinction):
        return '?'
    if _becker_coppens_kind(extinction) == 'type 2' and radius is not None:
        return radius
    if mosaicity is not None:
        return mosaicity
    return radius if radius is not None else '?'


def _extinction_special_details(extinction: object) -> object | None:
    """Return mixed Becker-Coppens extinction details."""
    if not _is_becker_coppens(extinction):
        return None
    if not _is_mixed_extinction(extinction):
        return None
    mosaicity = _attribute_value(extinction, 'mosaicity')
    radius = _attribute_value(extinction, 'radius')
    return (
        'Becker-Coppens mixed extinction with '
        f'mosaicity={mosaicity} and radius={radius}.'
    )


def _becker_coppens_method(extinction: object) -> str:
    """Return Becker-Coppens method text."""
    kind = _becker_coppens_kind(extinction)
    distribution = _becker_coppens_distribution(extinction)
    anisotropy = _becker_coppens_anisotropy(extinction)
    return f'Becker-Coppens {kind} {distribution} {anisotropy}'


def _becker_coppens_kind(extinction: object) -> str:
    """Return the Becker-Coppens type marker."""
    model_text = _normalised_text(_attribute_value(extinction, 'model'))
    if 'mixed' in model_text:
        return 'mixed'
    if 'type2' in model_text or 'type 2' in model_text:
        return 'type 2'
    if 'type1' in model_text or 'type 1' in model_text:
        return 'type 1'
    if _is_mixed_extinction(extinction):
        return 'mixed'
    if _attribute_value(extinction, 'radius') is not None:
        return 'type 2'
    return 'type 1'


def _becker_coppens_distribution(extinction: object) -> str:
    """Return the Becker-Coppens distribution text."""
    model = _attribute_value(extinction, 'model')
    model_text = _normalised_text(model)
    if 'lorentz' in model_text:
        return 'Lorentzian'
    if 'gauss' in model_text:
        return 'Gaussian'
    if model is not None:
        return str(model).replace('_', ' ').replace('-', ' ').title()
    return 'Gaussian'


def _becker_coppens_anisotropy(extinction: object) -> str:
    """Return the Becker-Coppens isotropy marker."""
    model_text = _normalised_text(_attribute_value(extinction, 'model'))
    if 'anisotropic' in model_text:
        return 'anisotropic'
    return 'isotropic'


def _is_becker_coppens(extinction: object) -> bool:
    """Return whether the extinction category is Becker-Coppens."""
    extinction_type = _attribute_value(extinction, 'type')
    return _normalised_text(extinction_type) == 'becker coppens'


def _is_mixed_extinction(extinction: object) -> bool:
    """Return whether both Becker-Coppens coefficient channels exist."""
    mosaicity = _attribute_value(extinction, 'mosaicity')
    radius = _attribute_value(extinction, 'radius')
    return mosaicity is not None and radius is not None


def _normalised_text(value: object) -> str:
    """Return a normalized lower-case token string."""
    return str(value or '').replace('_', ' ').replace('-', ' ').lower()


def _attribute_value(owner: object, attr_name: str) -> object:
    """Return ``owner.<attr_name>.value`` when available."""
    if owner is None:
        return None
    return _descriptor_value(getattr(owner, attr_name, None))


def _descriptor_value(value: object) -> object:
    """Return ``value.value`` for descriptors, otherwise *value*."""
    return getattr(value, 'value', value)


def _iucr_items(
    owner: object,
    values: tuple[tuple[str, object], ...],
) -> tuple[IucrItem, ...]:
    """Return IUCr-tagged descriptor values from *owner*."""
    if owner is None:
        return ()
    items: list[IucrItem] = []
    for attr_name, value in values:
        descriptor = getattr(owner, attr_name, None)
        if descriptor is not None:
            items.append(_iucr_item(descriptor, value))
    return tuple(items)


def _iucr_item(descriptor: object, value: object) -> IucrItem:
    """Return one IUCr-tagged item for a descriptor."""
    return IucrItem(descriptor._cif_handler.iucr_name, value)


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
