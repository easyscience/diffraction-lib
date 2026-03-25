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

**Resolution:** converted `Extinction` and `LinkedCrystal` from plain singleton
categories to factory-created categories. `Extinction` → `ShelxExtinction`
registered with `ExtinctionFactory` (tag `shelx`). `LinkedCrystal` registered
with `LinkedCrystalFactory` (tag `default`). Both are now packages
(`extinction/`, `linked_crystal/`) with `factory.py`, concrete class module, and
`__init__.py`. `ScExperimentBase` uses factory creation and exposes the standard
switchable-category API: `extinction_type` / `linked_crystal_type` (getter +
setter), `show_supported_extinction_types()` /
`show_supported_linked_crystal_types()`, `show_current_extinction_type()` /
`show_current_linked_crystal_type()`. Architecture §5.5 and §5.7 tables updated.
Unit tests extended with factory registration, creation, and default-tag tests.
