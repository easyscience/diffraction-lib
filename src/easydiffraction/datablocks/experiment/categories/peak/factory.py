# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Peak profile factory — delegates to ``FactoryBase``."""

from __future__ import annotations

from typing import ClassVar

from easydiffraction.core.factory import FactoryBase
from easydiffraction.datablocks.experiment.item.enums import BeamModeEnum
from easydiffraction.datablocks.experiment.item.enums import PeakProfileTypeEnum
from easydiffraction.datablocks.experiment.item.enums import ScatteringTypeEnum
from easydiffraction.utils.logging import console
from easydiffraction.utils.utils import render_table


class PeakFactory(FactoryBase):
    """Factory for creating peak profile objects."""

    _default_rules: ClassVar[dict] = {
        frozenset({
            ('scattering_type', ScatteringTypeEnum.BRAGG),
            ('beam_mode', BeamModeEnum.CONSTANT_WAVELENGTH),
        }): PeakProfileTypeEnum.CWL_PSEUDO_VOIGT,
        frozenset({
            ('scattering_type', ScatteringTypeEnum.BRAGG),
            ('beam_mode', BeamModeEnum.TIME_OF_FLIGHT),
        }): PeakProfileTypeEnum.TOF_JORGENSEN,
        frozenset({
            ('scattering_type', ScatteringTypeEnum.TOTAL),
        }): PeakProfileTypeEnum.TOTAL_GAUSSIAN_DAMPED_SINC,
    }

    _local_alias_rules: ClassVar[dict] = {
        frozenset({
            ('scattering_type', ScatteringTypeEnum.BRAGG),
            ('beam_mode', BeamModeEnum.CONSTANT_WAVELENGTH),
        }): {
            'pseudo-voigt': PeakProfileTypeEnum.CWL_PSEUDO_VOIGT,
            'pseudo-voigt + empirical asymmetry': (
                PeakProfileTypeEnum.CWL_PSEUDO_VOIGT_EMPIRICAL_ASYMMETRY
            ),
            'thompson-cox-hastings': PeakProfileTypeEnum.CWL_THOMPSON_COX_HASTINGS,
        },
        frozenset({
            ('scattering_type', ScatteringTypeEnum.BRAGG),
            ('beam_mode', BeamModeEnum.TIME_OF_FLIGHT),
        }): {
            'pseudo-voigt': PeakProfileTypeEnum.TOF_PSEUDO_VOIGT,
            'jorgensen': PeakProfileTypeEnum.TOF_JORGENSEN,
            'jorgensen-von-dreele': PeakProfileTypeEnum.TOF_JORGENSEN_VON_DREELE,
            'double-jorgensen-von-dreele': (PeakProfileTypeEnum.TOF_DOUBLE_JORGENSEN_VON_DREELE),
        },
        frozenset({
            ('scattering_type', ScatteringTypeEnum.TOTAL),
        }): {
            'gaussian-damped-sinc': PeakProfileTypeEnum.TOTAL_GAUSSIAN_DAMPED_SINC,
        },
    }

    @classmethod
    def _local_aliases_for(cls, **conditions: object) -> dict[str, str]:
        """Return context-local aliases for peak profile tags."""
        condition_set = frozenset(conditions.items())
        best_match_aliases: dict[str, str] = {}
        best_match_size = -1

        for rule_key, aliases in cls._local_alias_rules.items():
            if rule_key <= condition_set and len(rule_key) > best_match_size:
                best_match_aliases = aliases
                best_match_size = len(rule_key)

        return best_match_aliases

    @classmethod
    def _canonical_tag_for(cls, tag: str, **conditions: object) -> str:
        """Resolve a canonical tag or context-local alias to a tag."""
        if tag in cls._supported_map():
            return str(tag)
        aliases = cls._local_aliases_for(**conditions)
        canonical_tag = aliases.get(tag)
        if canonical_tag is None:
            return tag
        return str(canonical_tag)

    @classmethod
    def _local_alias_for(cls, tag: str, **conditions: object) -> str:
        """Return the context-local alias for a canonical tag."""
        aliases = cls._local_aliases_for(**conditions)
        for alias, canonical_tag in aliases.items():
            if canonical_tag == tag:
                return alias
        return str(tag)

    @classmethod
    def show_supported(
        cls,
        *,
        calculator: object = None,
        sample_form: object = None,
        scattering_type: object = None,
        beam_mode: object = None,
        radiation_probe: object = None,
    ) -> None:
        """
        Pretty-print supported peak profiles with context-local aliases.

        Parameters
        ----------
        calculator : object, default=None
            Optional ``CalculatorEnum`` value.
        sample_form : object, default=None
            Optional ``SampleFormEnum`` value.
        scattering_type : object, default=None
            Optional ``ScatteringTypeEnum`` value.
        beam_mode : object, default=None
            Optional ``BeamModeEnum`` value.
        radiation_probe : object, default=None
            Optional ``RadiationProbeEnum`` value.
        """
        matching = cls.supported_for(
            calculator=calculator,
            sample_form=sample_form,
            scattering_type=scattering_type,
            beam_mode=beam_mode,
            radiation_probe=radiation_probe,
        )
        conditions = {
            'sample_form': sample_form,
            'scattering_type': scattering_type,
            'beam_mode': beam_mode,
            'radiation_probe': radiation_probe,
        }
        columns_headers = ['Type', 'Description']
        columns_alignment = ['left', 'left']
        columns_data = [
            [
                cls._local_alias_for(klass.type_info.tag, **conditions),
                klass.type_info.description,
            ]
            for klass in matching
        ]
        console.paragraph('Supported types')
        render_table(
            columns_headers=columns_headers,
            columns_alignment=columns_alignment,
            columns_data=columns_data,
        )
