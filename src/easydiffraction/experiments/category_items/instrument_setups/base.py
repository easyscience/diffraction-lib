# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

from typing import Optional
from typing import Type

from easydiffraction.core.categories import CategoryItem
from easydiffraction.experiments.experiment_types.enums import BeamModeEnum
from easydiffraction.experiments.experiment_types.enums import ScatteringTypeEnum


class InstrumentBase(CategoryItem):
    def __init__(self) -> None:
        super().__init__()
        self._identity.category_code = 'instrument'


class InstrumentFactory:
    ST = ScatteringTypeEnum
    BM = BeamModeEnum

    @classmethod
    def _supported_map(cls) -> dict:
        # Lazy import to avoid circulars
        from easydiffraction.experiments.category_items.instrument_setups.cw import (
            ConstantWavelengthInstrument,
        )
        from easydiffraction.experiments.category_items.instrument_setups.tof import (
            TimeOfFlightInstrument,
        )

        return {
            cls.ST.BRAGG: {
                cls.BM.CONSTANT_WAVELENGTH: ConstantWavelengthInstrument,
                cls.BM.TIME_OF_FLIGHT: TimeOfFlightInstrument,
            }
        }

    @classmethod
    def create(
        cls,
        scattering_type: Optional[ScatteringTypeEnum] = None,
        beam_mode: Optional[BeamModeEnum] = None,
    ) -> InstrumentBase:
        if beam_mode is None:
            beam_mode = BeamModeEnum.default()
        if scattering_type is None:
            scattering_type = ScatteringTypeEnum.default()

        supported = cls._supported_map()

        supported_scattering_types = list(supported.keys())
        if scattering_type not in supported_scattering_types:
            raise ValueError(
                f"Unsupported scattering type: '{scattering_type}'.\n "
                f'Supported scattering types: {supported_scattering_types}'
            )

        supported_beam_modes = list(supported[scattering_type].keys())
        if beam_mode not in supported_beam_modes:
            raise ValueError(
                f"Unsupported beam mode: '{beam_mode}' for scattering type: "
                f"'{scattering_type}'.\n "
                f'Supported beam modes: {supported_beam_modes}'
            )

        instrument_class: Type[InstrumentBase] = supported[scattering_type][beam_mode]
        return instrument_class()
