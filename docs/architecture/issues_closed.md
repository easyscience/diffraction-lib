# EasyDiffraction — Closed Issues

Issues that have been fully resolved. Kept for historical reference.

---

## Dirty-Flag Guard Was Disabled

**Resolution:** added `_set_value_from_minimizer()` on `GenericDescriptorBase`
that writes `_value` directly (no validation) but sets the dirty flag on the
parent `DatablockItem`. Both `LmfitMinimizer` and `DfolsMinimizer` now use it.
The guard in `DatablockItem._update_categories()` is enabled and skips redundant
updates on the user-facing path (CIF export, plotting). During fitting the guard
is bypassed (`called_by_minimizer=True`) because experiment calculations depend
on structure parameters owned by a different `DatablockItem`.

---

## Move Calculator from Global to Per-Experiment

**Resolution:** removed the global calculator from `Analysis`. Each experiment
now owns its calculator, auto-resolved on first access from
`CalculatorFactory._default_rules` (maps `scattering_type` → default tag) and
filtered by the data category's `calculator_support` metadata (e.g. `PdCwlData`
→ `{CRYSPY}`, `TotalData` → `{PDFFIT}`). Calculator classes no longer carry
`compatibility` attributes — limitations are expressed on categories. The
experiment exposes the standard switchable-category API: `calculator`
(read-only, lazy), `calculator_type` (getter + setter),
`show_supported_calculator_types()`, `show_current_calculator_type()`.
Tutorials, tests, and docs updated.

---

## Add Universal Factories for All Categories

**Resolution:** converted every category to use the `FactoryBase` pattern. Each
former single-file category is now a package with `factory.py` (trivial
`FactoryBase` subclass), `default.py` (concrete class with `@register` +
`type_info`), and `__init__.py` (re-exports preserving import compatibility).

Experiment categories: `Extinction` → `ShelxExtinction` / `ExtinctionFactory`
(tag `shelx`), `LinkedCrystal` / `LinkedCrystalFactory` (tag `default`),
`ExcludedRegions` / `ExcludedRegionsFactory`, `LinkedPhases` /
`LinkedPhasesFactory`, `ExperimentType` / `ExperimentTypeFactory`.

Structure categories: `Cell` / `CellFactory`, `SpaceGroup` /
`SpaceGroupFactory`, `AtomSites` / `AtomSitesFactory`.

Analysis categories: `Aliases` / `AliasesFactory`, `Constraints` /
`ConstraintsFactory`, `JointFitExperiments` / `JointFitExperimentsFactory`.

`ShelxExtinction` and `LinkedCrystal` get the full switchable-category API on
`ScExperimentBase` (`extinction_type`, `linked_crystal_type` getter+setter,
`show_supported_*_types()`, `show_current_*_type()`). `ExcludedRegions` and
`LinkedPhases` get the same API on `PdExperimentBase`. `Cell`, `SpaceGroup`, and
`AtomSites` get it on `Structure`. `Aliases` and `Constraints` get it on
`Analysis`. Architecture §3.3, §5.5, §5.7, §9.4, §9.5 updated. Copilot
instructions updated with universal switchable-category scope and
architecture-first workflow rule. Unit tests extended with factory tests for
extinction and linked-crystal.
