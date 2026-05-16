# SPDX-FileCopyrightText: 2025 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from easydiffraction.analysis.categories.joint_fit import JointFitCollection
from easydiffraction.analysis.categories.joint_fit import JointFitItem


def test_joint_fit_item_and_collection():
    j = JointFitItem()
    j.experiment_id = 'ex1'
    j.weight = 0.5
    assert j.experiment_id.value == 'ex1'
    assert j.weight.value == 0.5
    coll = JointFitCollection()
    coll.create(experiment_id='ex1', weight=0.5)
    assert 'ex1' in coll.names
    assert coll['ex1'].weight.value == 0.5
