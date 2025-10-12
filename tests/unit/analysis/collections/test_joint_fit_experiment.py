from easydiffraction.analysis.category_collections.joint_fit_experiments import JointFitExperiment

# filepath: src/easydiffraction/analysis/category_collections/test_joint_fit_experiments.py


def test_joint_fit_experiment_initialization():
    # Test initialization of JointFitExperiment
    expt = JointFitExperiment(id='exp1', weight=1.5)
    assert expt.id.value == 'exp1'
    assert expt.id.name == 'id'
    assert expt.id.full_cif_names == ['_joint_fit_experiment.id']
    assert expt.weight.value == 1.5
    assert expt.weight.name == 'weight'
    assert expt.weight.full_cif_names == ['_joint_fit_experiment.weight']


def test_joint_fit_experiment_properties():
    # Test properties of JointFitExperiment
    expt = JointFitExperiment(id='exp2', weight=2.0)
    assert expt.category_key == 'joint_fit_experiment'
    assert expt.id.value == 'exp2'
