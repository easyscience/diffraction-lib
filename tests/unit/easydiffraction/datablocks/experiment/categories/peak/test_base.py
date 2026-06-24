# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from easydiffraction.core.metadata import TypeInfo
from easydiffraction.core.variable import StringDescriptor
from easydiffraction.datablocks.experiment.categories.peak.base import PeakBase


def test_peak_base_identity_code():
    class DummyPeak(PeakBase):
        def __init__(self):
            super().__init__()

    p = DummyPeak()
    assert p._identity.category_code == 'peak'


def test_peak_base_profile_type_defaults_to_empty_without_type_info():
    class DummyPeak(PeakBase):
        def __init__(self):
            super().__init__()

    p = DummyPeak()
    assert isinstance(p._type, StringDescriptor)
    assert p.type == ''


def test_peak_base_profile_type_reflects_type_info_tag():
    class TaggedPeak(PeakBase):
        type_info = TypeInfo(tag='my-profile', description='test profile')

        def __init__(self):
            super().__init__()

    p = TaggedPeak()
    assert p.type == 'my-profile'


def test_peak_base_profile_type_in_parameters():
    class TaggedPeak(PeakBase):
        type_info = TypeInfo(tag='my-profile', description='test profile')

        def __init__(self):
            super().__init__()

    p = TaggedPeak()
    param_names = {param.name for param in p.parameters}
    assert 'type' in param_names
