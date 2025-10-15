from easydiffraction.sample_models.sample_models import SampleModels


def test_add_minimal_and_remove():
    models = SampleModels()
    models.add_minimal("m1")
    assert "m1" in models.names
    models.remove("m1")
    assert "m1" not in models
