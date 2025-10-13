# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause
from __future__ import annotations

from typing import TYPE_CHECKING

from easydiffraction.experiments.datastore_types.pd import PowderDatastore
from easydiffraction.experiments.datastore_types.sg import SingleCrystalDatastore
from easydiffraction.experiments.experiment_types.enums import BeamModeEnum
from easydiffraction.experiments.experiment_types.enums import SampleFormEnum

if TYPE_CHECKING:
    from easydiffraction.experiments.datastore_types.base import BaseDatastore


class DatastoreFactory:
    _supported = {
        'powder': PowderDatastore,
        'single crystal': SingleCrystalDatastore,
    }

    @classmethod
    def create(
        cls,
        sample_form: str = SampleFormEnum.default(),
        beam_mode: str = BeamModeEnum.default(),
    ) -> BaseDatastore:
        """Create and return a datastore object for the given sample
        form.

        Args:
            sample_form (str): Sample form type, e.g. 'powder' or
                'single crystal'.
            beam_mode (str): Beam mode for powder sample form.

        Returns:
            BaseDatastore: Instance of a datastore class corresponding
                to sample form.

        Raises:
            ValueError: If the sample_form or beam_mode is not
                supported.
        """
        supported_sample_forms = list(cls._supported.keys())
        if sample_form not in supported_sample_forms:
            raise ValueError(
                f"Unsupported sample form: '{sample_form}'.\n"
                f'Supported sample forms: {supported_sample_forms}'
            )

        supported_beam_modes = ['time-of-flight', 'constant wavelength']
        if beam_mode not in supported_beam_modes:
            raise ValueError(
                f"Unsupported beam mode: '{beam_mode}'.\n"
                f'Supported beam modes: {supported_beam_modes}'
            )

        datastore_class = cls._supported[sample_form]
        if sample_form == 'powder':
            datastore_obj = datastore_class(beam_mode=beam_mode)
        else:
            datastore_obj = datastore_class()

        return datastore_obj
