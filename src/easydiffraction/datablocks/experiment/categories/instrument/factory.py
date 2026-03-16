# SPDX-FileCopyrightText: 2021-2026 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause
"""Factory for instrument category items.

Provides a stable entry point for creating instrument objects from the
experiment's scattering type and beam mode.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Optional
from typing import Type

from easydiffraction.datablocks.experiment.item.enums import BeamModeEnum
from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum
from easydiffraction.datablocks.experiment.item.enums import ScatteringTypeEnum

if TYPE_CHECKING:
    from easydiffraction.datablocks.experiment.categories.instrument.base import InstrumentBase


class InstrumentFactory:
    """Create instrument instances for supported modes.

    The factory hides implementation details and lazy-loads concrete
    instrument classes to avoid circular imports.
    """

    ST = ScatteringTypeEnum
    BM = BeamModeEnum
    SF = SampleFormEnum

    @classmethod
    def _supported_map(cls) -> dict:
        # Lazy import to avoid circulars
        from easydiffraction.datablocks.experiment.categories.instrument.cwl import CwlPdInstrument
        from easydiffraction.datablocks.experiment.categories.instrument.cwl import CwlScInstrument
        from easydiffraction.datablocks.experiment.categories.instrument.tof import TofPdInstrument
        from easydiffraction.datablocks.experiment.categories.instrument.tof import TofScInstrument

        return {
            cls.ST.BRAGG: {
                cls.BM.CONSTANT_WAVELENGTH: {
                    cls.SF.POWDER: CwlPdInstrument,
                    cls.SF.SINGLE_CRYSTAL: CwlScInstrument,
                },
                cls.BM.TIME_OF_FLIGHT: {
                    cls.SF.POWDER: TofPdInstrument,
                    cls.SF.SINGLE_CRYSTAL: TofScInstrument,
                },
            }
        }

    @classmethod
    def create(
        cls,
        scattering_type: Optional[ScatteringTypeEnum] = None,
        beam_mode: Optional[BeamModeEnum] = None,
        sample_form: Optional[SampleFormEnum] = None,
    ) -> InstrumentBase:
        if beam_mode is None:
            beam_mode = BeamModeEnum.default()
        if scattering_type is None:
            scattering_type = ScatteringTypeEnum.default()
        if sample_form is None:
            sample_form = SampleFormEnum.default()

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

        supported_sample_forms = list(supported[scattering_type][beam_mode].keys())
        if sample_form not in supported_sample_forms:
            raise ValueError(
                f"Unsupported sample form: '{sample_form}' for scattering type: "
                f"'{scattering_type}' and beam mode: '{beam_mode}'.\n "
                f'Supported sample forms: {supported_sample_forms}'
            )

        instrument_class: Type[InstrumentBase] = supported[scattering_type][beam_mode][sample_form]
        return instrument_class()
