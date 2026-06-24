# 38. Fix `@typechecked` / gemmi Interaction in Factories

**Priority:** `[priority] medium`

**Type:** Bug

Both `StructureFactory` and `ExperimentFactory` have `from_cif_str`
methods where `@typechecked` is commented out because it "fails to find
gemmi". They also share TODOs about adding minimal default configuration
for missing parameters and reading content from files.

**TODOs:**

- [factory.py](src/easydiffraction/datablocks/structure/item/factory.py#L41)
- [factory.py](src/easydiffraction/datablocks/structure/item/factory.py#L91)
- [factory.py](src/easydiffraction/datablocks/structure/item/factory.py#L115)
- [factory.py](src/easydiffraction/datablocks/experiment/item/factory.py#L59)
  — `Add to core/factory.py?`
- [factory.py](src/easydiffraction/datablocks/experiment/item/factory.py#L108)
- [factory.py](src/easydiffraction/datablocks/experiment/item/factory.py#L177)
- [factory.py](src/easydiffraction/datablocks/experiment/item/factory.py#L201)

**Depends on:** nothing.
