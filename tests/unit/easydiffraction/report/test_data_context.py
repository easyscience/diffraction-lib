# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for report data-context construction."""

from __future__ import annotations

from types import SimpleNamespace

import numpy as np


class _Descriptor:
    def __init__(self, value):
        self.value = value


def _parameter(name, value, uncertainty):
    from easydiffraction.core.validation import AttributeSpec
    from easydiffraction.core.variable import Parameter
    from easydiffraction.io.cif.handler import CifHandler

    parameter = Parameter(
        name=name,
        value_spec=AttributeSpec(default=0.0),
        cif_handler=CifHandler(names=[f'_{name}']),
    )
    parameter.value = value
    parameter.free = True
    parameter.uncertainty = uncertainty
    return parameter


def _structure() -> SimpleNamespace:
    return SimpleNamespace(
        name='phase',
        space_group=SimpleNamespace(
            name_h_m=_Descriptor('P 1'),
            crystal_system=_Descriptor('triclinic'),
        ),
        cell=SimpleNamespace(
            length_a=_parameter('length_a', 11.98509310, 0.03069505),
            length_b=_parameter('length_b', 2.0, None),
            length_c=_parameter('length_c', 3.0, None),
            angle_alpha=_parameter('angle_alpha', 90.0, None),
            angle_beta=_parameter('angle_beta', 90.0, None),
            angle_gamma=_parameter('angle_gamma', 90.0, None),
        ),
        atom_sites=[
            SimpleNamespace(
                label=_Descriptor('Si1'),
                type_symbol=_Descriptor('Si'),
                fract_x=_parameter('fract_x', 11.98509310, 0.03069505),
                fract_y=_parameter('fract_y', 0.0, None),
                fract_z=_parameter('fract_z', 0.0, None),
                occupancy=_parameter('occupancy', 1.0, None),
                adp_type=_Descriptor('Uani'),
                adp_iso=_parameter('adp_iso', 0.00658189, 0.00014),
            )
        ],
        atom_site_aniso=[
            SimpleNamespace(
                label=_Descriptor('Si1'),
                adp_11=_parameter('adp_11', 0.00658189, 0.00014),
                adp_22=_parameter('adp_22', 0.00488144, 0.00029),
                adp_33=_parameter('adp_33', 0.00488144, None),
                adp_12=_parameter('adp_12', -0.00048176, 0.00025),
                adp_13=_parameter('adp_13', 0.0, None),
                adp_23=_parameter('adp_23', 0.00188994, 0.00013),
            )
        ],
    )


def _experiment() -> SimpleNamespace:
    return SimpleNamespace(
        name='heidi',
        type=SimpleNamespace(
            sample_form=_Descriptor('single crystal'),
            beam_mode=_Descriptor('constant wavelength'),
            radiation_probe=_Descriptor('neutron'),
            scattering_type=_Descriptor('bragg'),
        ),
        calculator=SimpleNamespace(type=_Descriptor('cryspy')),
        diffrn=SimpleNamespace(),
        measured_range=None,
        refln=SimpleNamespace(
            intensity_meas=np.array([11.0, 19.0]),
            intensity_calc=np.array([10.0, 20.0]),
            intensity_meas_su=np.array([0.5, 0.7]),
        ),
    )


def _project() -> SimpleNamespace:
    return SimpleNamespace(
        name='demo',
        info=SimpleNamespace(title=_Descriptor('Demo'), description=_Descriptor(None)),
        structures={'phase': _structure()},
        experiments={'heidi': _experiment()},
        analysis=SimpleNamespace(
            fit_result=SimpleNamespace(),
            software=SimpleNamespace(),
            constraints=[],
        ),
        publication=SimpleNamespace(),
    )


def test_report_data_context_builds_fit_figure():
    from easydiffraction.report.data_context import build_report_data_context

    context = build_report_data_context(_project())

    figure = context['figures']['fit_per_experiment']['heidi']
    assert figure.data[0].name == 'Measured'
    assert list(figure.data[0].error_y.array) == [0.5, 0.7]
    assert figure.data[1].name == 'I²meas = I²calc'
    assert figure.layout.title.text == 'Measured vs calculated: heidi'


def test_report_data_context_preserves_structure_uncertainties():
    from easydiffraction.report.data_context import build_report_data_context

    context = build_report_data_context(_project())
    structure = context['structures'][0]

    assert structure['cell']['length_a'] == '11.985(31)'
    assert structure['atom_sites'][0]['fract_x'] == '11.985(31)'
    assert structure['atom_sites'][0]['adp_iso'] == '0.00658(14)'
    assert structure['atom_site_aniso'][0]['adp_12'] == '-0.00048(25)'
