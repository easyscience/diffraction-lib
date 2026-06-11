# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Bragg powder diffraction experiment datablock."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from easydiffraction.core.metadata import Compatibility
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.datablocks.experiment.categories.background.factory import BackgroundFactory
from easydiffraction.datablocks.experiment.categories.instrument.factory import InstrumentFactory
from easydiffraction.datablocks.experiment.categories.pref_orient.factory import PrefOrientFactory
from easydiffraction.datablocks.experiment.categories.refln.factory import ReflnFactory
from easydiffraction.datablocks.experiment.item.base import PdExperimentBase
from easydiffraction.datablocks.experiment.item.enums import BeamModeEnum
from easydiffraction.datablocks.experiment.item.enums import CalculatorEnum
from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum
from easydiffraction.datablocks.experiment.item.enums import ScatteringTypeEnum
from easydiffraction.datablocks.experiment.item.factory import ExperimentFactory
from easydiffraction.io.ascii import load_numeric_block
from easydiffraction.io.cif.parse import read_cif_str
from easydiffraction.utils.logging import log

if TYPE_CHECKING:
    from easydiffraction.datablocks.experiment.categories.experiment_type import ExperimentType

# Minimum number of columns required in an ASCII data file
_MIN_COLUMNS_XY = 2
_MIN_COLUMNS_XY_SY = 3

# Uncertainty values below this threshold are replaced with 1.0
_MIN_UNCERTAINTY = 0.0001


@ExperimentFactory.register
class BraggPdExperiment(PdExperimentBase):
    """Standard Bragg powder diffraction experiment."""

    type_info = TypeInfo(
        tag='bragg-pd',
        description='Bragg powder diffraction experiment',
    )
    compatibility = Compatibility(
        scattering_type=frozenset({ScatteringTypeEnum.BRAGG}),
        sample_form=frozenset({SampleFormEnum.POWDER}),
        beam_mode=frozenset({BeamModeEnum.CONSTANT_WAVELENGTH, BeamModeEnum.TIME_OF_FLIGHT}),
    )

    def __init__(
        self,
        *,
        name: str,
        type: ExperimentType,
    ) -> None:
        super().__init__(name=name, type=type)

        self._instrument_type: str = InstrumentFactory.default_tag(
            scattering_type=self.type.scattering_type.value,
            beam_mode=self.type.beam_mode.value,
            sample_form=self.type.sample_form.value,
        )
        self._instrument = InstrumentFactory.create(self._instrument_type)
        self._background = BackgroundFactory.create(BackgroundFactory.default_tag())
        self._pref_orient = PrefOrientFactory.create(PrefOrientFactory.default_tag())
        self._refln = None
        self._sync_refln_category()
        self._attach_category_parents()

    def _refln_collection_tag(self) -> str:
        """
        Return the reflection-collection tag for this beam mode.
        """
        return ReflnFactory.default_tag(
            sample_form=self.type.sample_form.value,
            beam_mode=self.type.beam_mode.value,
            scattering_type=self.type.scattering_type.value,
        )

    def _refln_collection_type(self) -> type[object]:
        """
        Return the reflection-collection type for this beam mode.
        """
        refln_tag = self._refln_collection_tag()
        return ReflnFactory._supported_map()[refln_tag]

    def _sync_refln_category(self) -> None:
        """Create or remove ``refln`` for the active calculator."""
        calculator_tag = self.calculator.type
        refln_collection_type = self._refln_collection_type()
        calculator = CalculatorEnum(calculator_tag)
        if refln_collection_type.calculator_support.supports(calculator):
            if not isinstance(self._refln, refln_collection_type):
                self._refln = ReflnFactory.create(self._refln_collection_tag())
            return

        self._refln = None

    def _swap_calculator(
        self,
        tag: str,
        *,
        announce: bool = True,
        strict: bool = True,
    ) -> None:
        """Switch calculator backend and sync ``refln`` availability."""
        super()._swap_calculator(tag, announce=announce, strict=strict)
        self._sync_refln_category()

    def _load_ascii_data_to_experiment(
        self,
        data_path: str,
    ) -> int:
        """
        Load (x, y, sy) data from an ASCII file into the data category.

        The file format is space/column separated with 2 or 3 columns:
        ``x y [sy]``. If ``sy`` is missing, it is approximated as
        ``sqrt(y)``.

        If ``sy`` has values smaller than ``0.0001``, they are replaced
        with ``1.0``.

        Parameters
        ----------
        data_path : str
            Path to the ASCII data file.

        Returns
        -------
        int
            Number of loaded data points.
        """
        data = load_numeric_block(data_path)

        if data.shape[1] < _MIN_COLUMNS_XY:
            log.error(
                'Data file must have at least two columns: x and y.',
                exc_type=ValueError,
            )
            return 0

        if data.shape[1] < _MIN_COLUMNS_XY_SY:
            log.warning('No uncertainty (sy) column provided. Defaulting to sqrt(y).')

        # Extract x, y data
        x = data[:, 0]
        y = data[:, 1]

        # Round x to 4 decimal places
        x = np.round(x, 4)

        # Determine sy from column 3 if available, otherwise use sqrt(y)
        sy = data[:, 2] if data.shape[1] > _MIN_COLUMNS_XY else np.sqrt(y)

        # Replace values smaller than _MIN_UNCERTAINTY with 1.0
        # TODO: Not used if loading from cif file?
        sy = np.where(sy < _MIN_UNCERTAINTY, 1.0, sy)

        # Set the experiment data
        self.data._create_items_set_xcoord_and_id(x)
        self.data._set_intensity_meas(y)
        self.data._set_intensity_meas_su(sy)

        return len(x)

    # ------------------------------------------------------------------
    #  Instrument (fixed at creation)
    # ------------------------------------------------------------------

    @property
    def instrument(self) -> object:
        """Active instrument model for this experiment."""
        return self._instrument

    @property
    def refln(self) -> object | None:
        """Calculated reflection metadata when supported."""
        return self._refln

    # ------------------------------------------------------------------
    #  Background (switchable-category pattern)
    # ------------------------------------------------------------------

    @property
    def background(self) -> object:
        """Active background model for this experiment."""
        return self._background

    # ------------------------------------------------------------------
    #  Preferred orientation (Bragg powder only)
    # ------------------------------------------------------------------

    @property
    def preferred_orientation(self) -> object:
        """Per-phase March-Dollase preferred-orientation corrections."""
        return self._pref_orient

    def _restore_switchable_types(self, block: object) -> None:
        """
        Restore Bragg powder switchable category types from CIF.
        """
        super()._restore_switchable_types(block)
        background_tag = read_cif_str(block, '_background.type')
        if background_tag is not None:
            self._replace_background(background_tag, announce=False, strict=False)
