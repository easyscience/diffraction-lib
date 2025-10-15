from easydiffraction.analysis.categories.aliases import Alias, Aliases


def test_alias_creation_and_collection():
    a = Alias(label="x", param_uid="p1")
    assert a.label.value == "x"
    coll = Aliases()
    coll.add(a)
    # Collections index by entry name; check via names or direct indexing
    assert "x" in coll.names
    assert coll["x"].param_uid.value == "p1"
