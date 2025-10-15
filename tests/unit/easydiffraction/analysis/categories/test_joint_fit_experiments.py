from easydiffraction.analysis.categories.joint_fit_experiments import (
    JointFitExperiment,
    JointFitExperiments,
)


def test_joint_fit_experiment_and_collection():
    j = JointFitExperiment(id="ex1", weight=0.5)
    assert j.id.value == "ex1"
    assert j.weight.value == 0.5
    coll = JointFitExperiments()
    coll.add(j)
    assert "ex1" in coll.names
    assert coll["ex1"].weight.value == 0.5
