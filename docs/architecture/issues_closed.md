# EasyDiffraction — Closed Issues

Issues that have been fully resolved. Kept for historical reference.

---

## Restore Minimiser Variant Support

Used thin subclasses (approach A) to restore lmfit algorithm variants.
`LmfitLeastsqMinimizer` and `LmfitLeastSquaresMinimizer` extend
`LmfitMinimizer`, each with its own `TypeInfo` tag. Added
`MinimizerTypeEnum` for all minimizer tags. No `FactoryBase` changes
needed — one class per tag.

---

## Implement `Project.load()`

`Project.load(dir_path)` classmethod reads `project.cif`,
`structures/*.cif`, `experiments/*.cif`, and `analysis/analysis.cif`
(with fallback to root for backward compatibility). Reconstructs full
state including alias references. Also used by `fit_sequential` workers.

---

## Eliminate Dummy `Experiments` Wrapper in Single-Fit Mode

`Fitter.fit()` and `_residual_function()` accept
`experiments: list[ExperimentBase]` directly. Removed the dummy
`Experiments` wrapper and `object.__setattr__` hack.

---

## Replace UID Map with Direct References and Auto-Apply Constraints

Eliminated `UidMapHandler` and random UID generation. Aliases store
direct object references (`Alias._param_ref`) at runtime and
deterministic `unique_name` for CIF. Added `enable()`/`disable()` on
`Constraints` with auto-enable on `create()`. Also resolved issue #4
(stale constraint state).

---

## Dirty-Flag Guard Was Disabled

Added `_set_value_from_minimizer()` on `GenericDescriptorBase`. The
guard in `DatablockItem._update_categories()` is enabled for the
user-facing path and bypassed during fitting
(`called_by_minimizer=True`).

---

## Move Calculator from Global to Per-Experiment

Each experiment owns its calculator, auto-resolved on first access from
`CalculatorFactory._default_rules` and filtered by data category
`calculator_support` metadata. Exposes the standard switchable-category
API.

---

## Add Universal Factories for All Categories

Converted every category to the `FactoryBase` pattern (package with
`factory.py`, `default.py`, `__init__.py`). Full switchable-category API
(`<cat>_type` getter+setter, `show_supported_*_types()`,
`show_current_*_type()`) on all owners.

---

## Add CIF Round-Trip Integration Test

Three integration tests in `test_cif_round_trip.py`: parameter values,
free flags, and category collection item counts survive `as_cif` →
`from_cif_str` round-trip.

---

## Refactor Peak Profiles (TOF + CWL Rename)

Replaced incorrect TOF peak profile classes with properly named ones:
`TofJorgensen` (BBE ⊗ Gaussian), `TofJorgensenVonDreele` (BBE ⊗ pV),
`TofDoubleJorgensenVonDreele` (double BBE ⊗ pV). Refactored TOF mixins
into `TofGaussianBroadeningMixin`, `TofLorentzianBroadeningMixin`,
`TofBackToBackExponentialMixin`, `TofDoubleExponentialMixin`. Renamed
CWL `CwlSplitPseudoVoigt` to `CwlPseudoVoigtEmpiricalAsymmetry`. Updated
enums, factory defaults, calculator mapping, tests, and tutorials.

---

## Implement Sequential Fitting

Added `Analysis.fit_sequential(data_dir, max_workers, ...)` for batch
fitting of thousands of data files. Features: `ProcessPoolExecutor` with
`spawn` context, chunk-based processing with parameter propagation,
crash recovery from CSV, `extract_diffrn` callback, incremental CSV
output. Unified `plot_param_series()` to read from CSV. Added
`Project.apply_params_from_csv()` for dataset replay. Single-fit mode
also writes CSV. Prerequisites included: CIF truncation fix, CIF
round-trip verification, `analysis.cif` moved into `analysis/`
directory, `extract_data_paths_from_zip` destination parameter.

---

## Make `data_type` Read-Only on Experiments

Removed the `data_type` setter, `show_supported_data_types()`, and
`show_current_data_type()` from both `ScExperimentBase` and
`PdExperimentBase`. The data collection type is now fixed at experiment
creation (resolved from `DataFactory.default_tag(...)` using the
experiment's axes), like experiment type itself. This prevents switching
to an incompatible data class and silently discarding loaded data.

---

## 78. Add `SEQUENTIAL` to `FitModeEnum` and Show Methods to Analysis

Added `SEQUENTIAL = 'sequential'` to `FitModeEnum`. `fit_sequential()`
now sets `fit_mode.mode = 'sequential'` internally so the mode is
persisted in CIF. Added `show_supported_fit_mode_types()` (filters by
experiment count: ≤1 → only `single`; >1 → all three) and
`show_current_fit_mode_type()` on `Analysis`. If `fit()` is called while
mode is `'sequential'`, it logs an error directing the user to
`fit_sequential()`. Promoted `fit_mode` from a pure single-type category
to one with show methods.
