# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

import pytest


def test_uid_map_handler_singleton_and_add_and_replace_uid():
    from easydiffraction.core.parameters import NumericDescriptor
    from easydiffraction.core.singletons import UidMapHandler
    from easydiffraction.core.validation import AttributeSpec
    from easydiffraction.core.validation import DataTypes
    from easydiffraction.io.cif.handler import CifHandler

    h1 = UidMapHandler.get()
    h2 = UidMapHandler.get()
    assert h1 is h2

    # Clean slate for test
    h1.get_uid_map().clear()

    d = NumericDescriptor(
        name='p',
        value_spec=AttributeSpec(value=1.0, type_=DataTypes.NUMERIC, default=0.0),
        cif_handler=CifHandler(names=['_x.p']),
    )
    h1.add_to_uid_map(d)
    assert d.uid in h1.get_uid_map()

    # replace_uid: bad key
    with pytest.raises(KeyError):
        h1.replace_uid('missing', 'new')

    # replace_uid: success path
    old_uid = d.uid
    new_uid = old_uid + 'x'
    h1.replace_uid(old_uid, new_uid)
    assert new_uid in h1.get_uid_map() and old_uid not in h1.get_uid_map()


def test_uid_map_handler_rejects_non_descriptor():
    from easydiffraction.core.singletons import UidMapHandler

    h = UidMapHandler.get()
    with pytest.raises(TypeError):
        h.add_to_uid_map(object())
