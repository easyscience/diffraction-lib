from easydiffraction.sample_models.sample_model.base import SampleModelBase


def test_sample_model_base_str_and_properties():
    m = SampleModelBase(name="m1")
    m.name = "m2"
    assert m.name == "m2"
    s = str(m)
    assert "SampleModelBase" in s or "<" in s
