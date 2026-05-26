# Plan: IUCr CIF Tag Alignment

Implementation plan for the
[`iucr-cif-tag-alignment`](../adrs/suggestions/iucr-cif-tag-alignment.md)
ADR. Follows [`AGENTS.md`](../../../AGENTS.md) — no deliberate
exceptions to those instructions.

## ADR cross-reference

- Primary ADR: `iucr-cif-tag-alignment.md` (currently in
  `suggestions/`; this plan promotes it to `accepted/` as its
  final implementation step before the Phase 1 review gate).
- Amends (per the ADR's "ADRs amended by this ADR" section):
  - [`analysis-cif-fit-state.md`](../adrs/accepted/analysis-cif-fit-state.md) —
    new `_fit_result.*` fields; topology-neutral default save.
  - [`minimizer-input-output-split.md`](../adrs/accepted/minimizer-input-output-split.md) —
    new `_fit_result.*` examples.
  - [`project-facade-and-persistence.md`](../adrs/accepted/project-facade-and-persistence.md) —
    `project.summary` removed and replaced by `project.report`;
    `summary.cif` no longer written.
  - [`help-discoverability.md`](../adrs/accepted/help-discoverability.md) —
    `project.summary.help()` → `project.report.help()`.

## Branch and PR

- Branch: `iucr-cif-tag-alignment` (already checked out, matches
  the slug).
- PR target: `develop`.
- Do not push the branch until both Phase 1 and Phase 2 review
  cycles close.

## Decisions already made (in the ADR)

These are settled by the accepted ADR — the plan does not
re-litigate them, only implements them:

- **Three-tier default save:** structure-tier IUCr alignment with
  casing fixes; analysis-tier topology-neutral `_fit_result.*`
  with dictionary-canonical *item* names (uppercase R / wR / DOI);
  experiment-tier unchanged. Per-topology category split
  (`_refine_ls.*` / `_pd_proc_ls.*` / `_reflns.*`) happens only
  in the IUCr export.
- **Reports system:** new `project.report` facade slot replaces
  the unimplemented `project.summary` placeholder; single
  `reports/<project>.cif` file with multi-datablock layout
  always starting with `data_global`. `project.save(report=True)`
  and `project.report.save()` produce the file;
  `project.report.check()` validates via gemmi against
  `cif_core.dic` / `cif_pow.dic`.
- **Handler mechanism:** per-field `iucr_name` (optional, falls
  back to `names[0]`) plus category-level
  `IucrCategoryTransformer` subclasses for wavelength,
  TOF calibration, excluded regions, symmetry operations, and
  extinction reshaping.
- **ADP single-tag emission:** emit `B_*` xor `U_*` per row based
  on `_atom_site.ADP_type`; both forms still accepted on read.
- **Loop-tag style:** dotted DDLm everywhere on write; both
  forms on read.
- **`_easydiffraction_software`** umbrella category with three
  free-text fields (`framework`, `calculator`, `minimizer`),
  plus a derived `_computing.structure_refinement` string in the
  IUCr export.
- **gemmi** is already a project dependency (`pyproject.toml:39`);
  no new dependencies needed.

## Open questions to resolve during implementation

- **Pixi env:** confirm `gemmi.cif.read_doc` and the dictionary
  validation path are available in the project's pinned gemmi
  version before P1.16 (validator implementation). If the pinned
  version is too old, bump the constraint in `pyproject.toml`
  (counts as a plan-named dependency change — pre-approved per
  AGENTS.md §Architecture because the package is already named).
- **Tutorial scope:** identify every tutorial source under
  `docs/docs/tutorials/*.py` that references `project.summary`
  and update them in P1.17. If a tutorial currently uses
  `project.summary.help()` as a discoverability example, it
  becomes `project.report.help()`; if a tutorial expects
  `summary.cif`, swap to `project.save(report=True)` and
  reference `reports/<project>.cif`.
- **Extinction transformer detail:** the `(type, model)` →
  `_refine_ls.extinction_method` descriptive string in §3 of the
  ADR uses a Becker-Coppens taxonomy table; the implementation
  needs the project's existing extinction-model selector enums
  to map cleanly. Verify enum values during P1.14.

## Concrete files likely to change

Foundation:
- `src/easydiffraction/io/cif/handler.py` — `CifHandler` gains
  `iucr_name` parameter.

Structure tier (casing):
- `src/easydiffraction/datablocks/structure/categories/atom_sites/default.py`
- `src/easydiffraction/datablocks/structure/categories/space_group/default.py`

ADP write-side:
- `src/easydiffraction/io/cif/serialize.py` (atom_site /
  atom_site_aniso write path)

Analysis tier (new `_fit_result.*` fields):
- `src/easydiffraction/analysis/categories/fit_result/lsq.py`
- `src/easydiffraction/analysis/categories/fit_result/base.py`
- `src/easydiffraction/analysis/fit/` (residual / aggregate
  computation site; exact module determined during P1.4)

Project-extension `iucr_name` settings (P1.7):
- The descriptor files enumerated in P1.7 (one `cif_handler`
  call per descriptor across the analysis / experiment
  categories — no new modules, no new packages). The software
  triple itself is built inline by the IUCr writer (P1.11) and
  does **not** introduce a new category class or
  default-save persistence.

Facade rename `project.summary` → `project.report` (P1.8):
- `src/easydiffraction/project/project.py` (replace the
  `summary` property and `summary.cif` write with the new
  `report` facade; drop the `as_cif()` caller; add the
  `report: bool = False` keyword to `Project.save()`).
- `src/easydiffraction/summary/` → migrated to
  `src/easydiffraction/report/` (either rename the package and
  class, or add a fresh `report/` package whose `Report`
  delegates to the migrated display methods —
  implementer's choice). Every live display method
  (`show_report`, `show_project_info`,
  `show_crystallographic_data`, `show_experimental_data`,
  `show_fitting_details`) is preserved verbatim; only the
  placeholder `as_cif()` is dropped.
- `src/easydiffraction/report/__init__.py`, `report.py` —
  destination of the migration.

IUCr writer:
- `src/easydiffraction/io/cif/iucr_writer.py` (new)
- `src/easydiffraction/io/cif/iucr_transformers.py` (new — holds
  `IucrCategoryTransformer` subclasses)

Validation:
- `src/easydiffraction/report/check.py` (new — wraps `gemmi`)

Amended ADRs:
- `docs/dev/adrs/accepted/analysis-cif-fit-state.md`
- `docs/dev/adrs/accepted/minimizer-input-output-split.md`
- `docs/dev/adrs/accepted/project-facade-and-persistence.md`
- `docs/dev/adrs/accepted/help-discoverability.md`

ADR promotion:
- `docs/dev/adrs/suggestions/iucr-cif-tag-alignment.md` → moved
  to `docs/dev/adrs/accepted/iucr-cif-tag-alignment.md` with
  status flipped to Accepted.
- `docs/dev/adrs/index.md` (index row updated).

Tutorials / CLI:
- `docs/docs/tutorials/*.py` (regenerate notebooks after edits
  via `pixi run notebook-prepare`).
- `src/easydiffraction/cli/` (any command that surfaces
  `project.summary`).

## Commit discipline

When an AI agent follows this plan, **every completed Phase 1
implementation step must be staged with explicit paths and
committed locally before moving to the next implementation step
or the Phase 1 review gate.** Follow the rules in
[`AGENTS.md`](../../../AGENTS.md) → **Commits**. Keep commits
atomic, single-purpose, and aligned with the plan steps. Do not
include generated artifacts (data CIFs, project directories,
benchmark CSVs) unless the step explicitly produces them — see
**Workflow** in [`AGENTS.md`](../../../AGENTS.md) for the
generated-artifact exceptions.

## Implementation steps (Phase 1)

- [x] **P1.1 — Extend `CifHandler` with `iucr_name`**
  - File: `src/easydiffraction/io/cif/handler.py`.
  - Add an optional keyword `iucr_name: str | None = None` to
    `CifHandler.__init__`.
  - Add a public property / method returning the IUCr-side tag:
    `iucr_name` when set, else `names[0]`.
  - No call sites change in this step — the default fallback
    leaves every existing handler emitting its current name.
  - Commit: `Add iucr_name to CifHandler`.

- [x] **P1.2 — Structure-tier casing fixes**
  - Files:
    `src/easydiffraction/datablocks/structure/categories/atom_sites/default.py`,
    `src/easydiffraction/datablocks/structure/categories/space_group/default.py`.
  - Rename canonical CIF tags to dictionary-canonical casing
    (`_atom_site.ADP_type`, `_atom_site.Wyckoff_symbol`,
    `_space_group.name_H-M_alt`,
    `_space_group.IT_coordinate_system_code`). Python attribute
    names stay lowercase.
  - Keep the old (lowercase / `wyckoff_letter`) forms in each
    `CifHandler.names` list as read-only aliases so loading legacy
    files still works.
  - Commit:
    `Adopt IUCr casing for atom_site and space_group CIF tags`.

- [x] **P1.3 — ADP single-tag emission per row**
  - File: `src/easydiffraction/io/cif/serialize.py` (and any
    helper called by it).
  - When emitting `_atom_site_aniso.*` and
    `_atom_site.B_iso_or_equiv` / `_atom_site.U_iso_or_equiv`,
    choose `B_*` or `U_*` per row based on `_atom_site.ADP_type`;
    omit the other family for that row.
  - Read side unchanged (both families still accepted).
  - Commit: `Emit one ADP family per atom_site row on save`.

- [x] **P1.4 — Analysis tier: new `_fit_result.*` fields**
  - Files:
    `src/easydiffraction/analysis/categories/fit_result/lsq.py`,
    `src/easydiffraction/analysis/categories/fit_result/base.py`,
    plus the fit-computation site (search for where
    `n_data_points`, `reduced_chi_square` are currently
    populated).
  - Declare new descriptors under `_fit_result.*` with
    dictionary-canonical *item* names (uppercase R / wR):
    `R_factor_all`, `wR_factor_all`, `R_factor_gt`,
    `wR_factor_gt`, `prof_R_factor`, `prof_wR_factor`,
    `prof_wR_expected`, `number_restraints`,
    `number_constraints`, `shift_over_su_max`,
    `shift_over_su_mean`, `profile_function`,
    `background_function`, `threshold_expression`,
    `number_reflns_total`, `number_reflns_gt`.
  - Wire computation: R-factors from residuals; restraint /
    constraint counts from the analysis model; profile / background
    descriptors from the active peak / background categories;
    reflns aggregates from refln data.
  - Fields not meaningful for a given fit (e.g. `prof_R_factor`
    for SC) stay unset / `None`.
  - Commit:
    `Add IUCr-canonical fit_result fields to LeastSquaresFitResult`.

- [x] **P1.5 — Amend `analysis-cif-fit-state.md`**
  - File:
    `docs/dev/adrs/accepted/analysis-cif-fit-state.md`.
  - Document the new `_fit_result.*` fields, the
    topology-neutral default-save policy, and the per-topology
    IUCr-export remapping deferred to §3 of the
    iucr-cif-tag-alignment ADR.
  - Commit: `Amend analysis-cif-fit-state ADR for new fit_result fields`.

- [x] **P1.6 — Amend `minimizer-input-output-split.md`**
  - File:
    `docs/dev/adrs/accepted/minimizer-input-output-split.md`.
  - Update the `_fit_result.*` examples in §3 to reflect the new
    field set from P1.4.
  - Commit: `Amend minimizer-input-output-split ADR examples`.

- [x] **P1.7 — Set `iucr_name` on project-extension descriptors**
  - No new category. The ADR's `_easydiffraction_software` triple
    is a **report-only projection**: it is derived inline by the
    IUCr writer in P1.11 from existing state (`easydiffraction`
    package version, `project.analysis.calculator.type`,
    `project.analysis.minimizer.type`, and per-backend version
    metadata). It is **not** persisted to `analysis/analysis.cif`
    and no new category class is added.
  - This step's actual work is the `_easydiffraction_*` prefix
    rename for existing project-extension descriptors at IUCr
    export time. For each project-extension category, set the
    matching descriptor's `cif_handler` `iucr_name` to the
    prefixed form so the IUCr writer emits
    `_easydiffraction_<category>.<field>` while the default save
    keeps the bare-category form (`_minimizer.*`, `_calculator.*`,
    etc.).
  - Touched descriptors:
    - `_minimizer.*` → `iucr_name='_easydiffraction_minimizer.*'`
      (settings only — type, tolerance, max_iter, …).
    - `_calculator.*` →
      `iucr_name='_easydiffraction_calculator.*'`.
    - `_fitting_mode.*` →
      `iucr_name='_easydiffraction_fitting_mode.*'`.
    - `_alias.*` → `iucr_name='_easydiffraction_alias.*'`.
    - `_constraint.*` →
      `iucr_name='_easydiffraction_constraint.*'`.
    - `_joint_fit.*` →
      `iucr_name='_easydiffraction_joint_fit.*'`.
    - `_sequential_fit.*`, `_sequential_fit_extract.*` →
      `iucr_name='_easydiffraction_sequential_fit*.*'`.
    - `_expt_type.*` →
      `iucr_name='_easydiffraction_experiment_type.*'`.
    - `_excluded_region.*` →
      `iucr_name='_easydiffraction_excluded_region.*'`.
    - `_peak.*` → `iucr_name='_easydiffraction_peak.*'`.
    - `_extinction.*` (project-side selectors and parameters) →
      `iucr_name='_easydiffraction_extinction.*'` (the
      transformer in P1.14 also dual-emits the coreCIF
      `_refine_ls.extinction_*` triple).
    - `_background.type` →
      `iucr_name='_easydiffraction_background.type'`.
    - `_sc_crystal_block.*` →
      `iucr_name='_easydiffraction_sc_crystal_block.*'`.
    - Bayesian-only `_fit_result.*` fields →
      `iucr_name='_easydiffraction_fit_result.*'` (project
      extensions per ADR §3.3).
  - The non-IUCr-counterpart `_diffrn.ambient_magnetic_field`
    and `_diffrn.ambient_electric_field` descriptors get
    `iucr_name='_easydiffraction_diffrn.ambient_magnetic_field'`
    / `…electric_field`.
  - Default-save behaviour is unchanged for every touched
    descriptor — only the IUCr-export emission picks up the
    new prefix.
  - Commit:
    `Set iucr_name on project-extension descriptors`.

- [x] **P1.8 — Rename `project.summary` → `project.report`, preserve display methods**
  - Files:
    `src/easydiffraction/project/project.py`,
    `src/easydiffraction/summary/` (renamed / migrated),
    `src/easydiffraction/report/` (new).
  - **Preserve every live `Summary` method.** The existing
    `Summary` class (at
    `src/easydiffraction/summary/summary.py`) has live
    user-facing display methods that tutorials call: `show_report()`,
    `show_project_info()`, `show_crystallographic_data()`,
    `show_experimental_data()`, `show_fitting_details()`.
    These are not placeholders and must not be removed. Move
    them verbatim onto the new `Report` class (rename of the
    class only, with no behavioural change), so
    `project.report.show_report()` and friends remain available
    with the same signatures and output.
  - **Drop only the placeholder CIF method.** The `as_cif()`
    method on `Summary` returns a stub string and is the only
    placeholder being removed. Its caller — the `summary.cif`
    write at `Project.save()` (currently at
    `src/easydiffraction/project/project.py:464`-ish) — is
    removed in the same commit. The real CIF emission for
    journal submission lives in `Report.save()` (writes
    `reports/<project>.cif`, real implementation lands in
    P1.15) — the two are independent: dropping `as_cif()` does
    not break any user-visible behaviour because nothing
    meaningful was being written.
  - Migration mechanics:
    - Either rename the package directory
      (`src/easydiffraction/summary/` →
      `src/easydiffraction/report/`) and class
      (`Summary` → `Report`) in one move, **or** add a new
      `src/easydiffraction/report/report.py` whose `Report`
      class inherits / delegates to the migrated display
      methods. Pick the approach that produces the smallest
      diff at review time; both keep the display behaviour
      intact.
    - Update `__init__.py` re-exports accordingly.
  - `Project` gains a `report` property returning the `Report`
    instance; the old `summary` property is removed. The
    `summary.cif` write call in `Project.save()` is removed.
  - `Project.save()` gains a `report: bool = False` keyword (no
    behaviour yet beyond passing through to `Report.save()`
    when truthy; the real `Report.save()` lands in P1.15).
  - Tutorial / CLI call sites that invoke
    `project.summary.show_report()` are updated in **P1.17**.
  - Commit: `Replace project.summary with project.report facade`.

- [x] **P1.9 — Amend `project-facade-and-persistence.md`**
  - File:
    `docs/dev/adrs/accepted/project-facade-and-persistence.md`.
  - Document the `project.report` facade slot, removal of
    `project.summary`, removal of `summary.cif` from default
    saves, and the new `reports/<project>.cif` output path.
  - Commit:
    `Amend project-facade-and-persistence ADR for project.report`.

- [x] **P1.10 — Amend `help-discoverability.md`**
  - File: `docs/dev/adrs/accepted/help-discoverability.md`.
  - Replace `project.summary.help()` with
    `project.report.help()` in the help-surface enumeration.
  - Commit:
    `Amend help-discoverability ADR for project.report`.

- [x] **P1.11 — IUCr writer foundation + `data_global` content**
  - New file: `src/easydiffraction/io/cif/iucr_writer.py`.
  - Implement the multi-datablock orchestrator skeleton:
    a `write_iucr_cif(project, path)` entry point that opens
    `reports/<project>.cif`, emits `data_global` first, then
    delegates topology-specific blocks to subordinate writers
    (added in P1.12 / P1.13).
  - Emit `data_global` content per §2.3a of the ADR:
    `_audit.creation_method` / `_audit.creation_date`,
    `_computing.structure_refinement` (derived from the
    `_easydiffraction_software` triple),
    `_easydiffraction_software.{framework, calculator,
    minimizer}`, `_journal.*` and `_publ_*` placeholders
    (written as `?`), `_chemical_formula.*` derived from atom
    sites where possible.
  - Apply the §2.4 formatting rules: blank line between
    categories, `# ---- <section> ----` headers, 80-char wrap
    on long strings, dotted DDLm form throughout, project
    extensions grouped at the end of each block.
  - Wire `Report.save()` (stubbed in P1.8) to call
    `write_iucr_cif`.
  - Commit: `Add IUCr CIF writer with data_global block`.

- [x] **P1.12 — Single-crystal block layout**
  - Same file as P1.11; add `_write_sc_block` helper.
  - Per-structure block emission per §2.3b: `_chemical_formula.*`,
    `_cell.*`, `_space_group.*` + `_space_group_symop.*` loop,
    `_diffrn.*`, `_diffrn_radiation_wavelength.*` (scalar /
    single-row category for monochromatic per the wavelength
    transformer), `_atom_site.*` + `_atom_site_aniso.*` loops
    with ADP single-tag emission, `_refine_ls.*`, `_reflns.*`,
    the `_refln.*` loop per §2.3c (`index_h/k/l`,
    `F_squared_meas`, `F_squared_calc`, `F_squared_meas_su`,
    `include_status`).
  - For SC the project-extension `_easydiffraction_extinction.*`
    block + the dual `_refine_ls.extinction_*` triple are
    emitted via the transformer (added in P1.14).
  - Commit: `Emit single-crystal blocks in IUCr CIF writer`.

- [x] **P1.13 — Powder Rietveld block layout (CWL + TOF)**
  - Same writer file; add `_write_rietveld_blocks` helper.
  - Emit `data_<project>_overall`, `data_<project>_phase_N`
    (one per phase), `data_<project>_pwd_N` (one per pattern)
    per §2.3f / §2.3g / §2.3h.
  - Profile-data loop columns: CWL form uses
    `_pd_meas.2theta_scan`; TOF form uses
    `_pd_meas.time_of_flight`. Other columns:
    `_pd_meas.intensity_total`, `_pd_calc.intensity_total`,
    `_pd_proc.intensity_bkg_calc`, `_pd_proc_ls.weight`.
  - Powder reflections loop per §2.3d:
    `_refln.{index_h/k/l, F_squared_meas, F_squared_calc,
    phase_calc, d_spacing}`.
  - Cross-block reference markers (`_pd_block_id`,
    `_pd_block_diffractogram_id`) emitted with pipe-delimited
    identifiers matching the §2.3 examples.
  - Joint Rietveld and sequential fits emit one `_pwd_N` per
    pattern / step inside the same file.
  - Commit:
    `Emit powder Rietveld blocks in IUCr CIF writer`.

- [x] **P1.14 — `IucrCategoryTransformer` subclasses**
  - New file:
    `src/easydiffraction/io/cif/iucr_transformers.py`.
  - Implement and register five transformers per §3 of the ADR:
    - **Wavelength** — monochromatic scalar /
      single-row category; multi-row loop when applicable.
    - **TOF calibration** — four-row
      `_pd_calib_d_to_tof.{id, coeff, power, coeff_su,
      diffractogram_id}` loop with EasyDiffraction attribute
      names as `id` codes (`offset`, `linear`, `quad`, `recip`)
      and powers 0, 1, 2, −1 respectively per the §2.3h
      cif_pow.dic equation.
    - **Excluded regions** — free-text rendering as
      `_pd_proc.info_excluded_regions`.
    - **Symmetry operations** — `_space_group_symop.*` loop
      derived from the active space group.
    - **Extinction** — dual emit
      `_easydiffraction_extinction.*` + the coreCIF
      `_refine_ls.extinction_{method,coef,expression}` triple,
      with the descriptive string built from the project's
      `(type, model)` selectors per the ADR §3 mapping table.
  - Wire transformers into the writer from P1.12 / P1.13 (the
    writer asks each per-block category for its IUCr
    representation, which is either a direct `iucr_name` rename
    or a transformer call).
  - Commit:
    `Add IUCr category transformers for restructured emissions`.

- [x] **P1.15 — Wire `Project.save(report=True)` end-to-end**
  - File: `src/easydiffraction/project/project.py`,
    `src/easydiffraction/report/report.py`.
  - `Project.save(report=False)` continues to write the regular
    project files. `Project.save(report=True)` additionally
    writes `reports/<project>.cif`.
  - `Project.save(report=True, check=False)` is the default for
    the report path; `check=True` is wired in P1.16.
  - Make the `reports/` directory if absent; overwrite an
    existing report file (no round-trip).
  - Commit: `Wire report=True kwarg on Project.save`.

- [x] **P1.16 — Submission-side validation via gemmi**
  - New file: `src/easydiffraction/report/check.py`.
  - Implement `Report.check()` using `gemmi.cif.read_doc`
    against the shipped (or downloaded) `cif_core.dic` and
    `cif_pow.dic`. Skip `_easydiffraction_*` from unknown-tag
    warnings.
  - Wire `Project.save(report=True, check=True)` to run
    validation after the write and surface any errors /
    warnings to the user.
  - Verify gemmi version supports the validation calls in the
    project's pinned env; if not, bump the constraint in
    `pyproject.toml` / `pixi.toml` / `pixi.lock` (pre-approved
    per AGENTS.md §Architecture because gemmi is already a
    named dependency).
  - Commit: `Add Report.check() validation via gemmi`.

- [x] **P1.17 — Update tutorials / CLI / docs references**
  - Source files in `docs/docs/tutorials/*.py` and CLI commands
    in `src/easydiffraction/cli/`.
  - Replace every `project.summary.*` call site with the
    matching `project.report.*` call:
    - `project.summary.show_report()` →
      `project.report.show_report()` (currently used by
      `docs/docs/tutorials/ed-3.py`,
      `docs/docs/tutorials/ed-5.py`,
      `docs/docs/tutorials/ed-6.py`,
      `docs/docs/tutorials/ed-8.py` — confirm the full list
      via `git grep -n 'project\.summary'` at the start of
      the step and update every match).
    - Other `project.summary.*` accessors (`show_project_info`,
      `show_crystallographic_data`, `show_experimental_data`,
      `show_fitting_details`) — replace each call with the
      `project.report.*` equivalent.
    - `project.summary.help()` in any tutorial or doc page
      becomes `project.report.help()`.
  - Demonstrate `project.save(report=True)` in at least one
    tutorial that finishes a fit; reference
    `reports/<project>.cif` in the prose.
  - Regenerate notebooks with `pixi run notebook-prepare`
    (per AGENTS.md §Tutorials).
  - Commit:
    `Update tutorials and CLI for project.report rename`.

- [x] **P1.18 — Promote ADR to `accepted/`**
  - Move
    `docs/dev/adrs/suggestions/iucr-cif-tag-alignment.md`
    to
    `docs/dev/adrs/accepted/iucr-cif-tag-alignment.md`.
  - Flip the front-matter `**Status:**` line from `Proposed`
    to `Accepted`. Update the date to today (Phase 1
    acceptance date).
  - Update `docs/dev/adrs/index.md`: the row's status column
    changes from `Suggestion` to `Accepted`, and the link
    target changes from `suggestions/` to `accepted/`.
  - Commit:
    `Promote iucr-cif-tag-alignment ADR to accepted`.

- [x] **P1.19 — Reach Phase 1 review gate**
  - No-code step. Mark every `[ ]` above as `[x]`; commit the
    plan-file update alone.
  - Commit: `Reach Phase 1 review gate`.

## Test plan (Phase 2)

Per AGENTS.md §Testing, every new module, class, and bug fix
ships with tests; unit tests mirror the source tree. Before
running the verification commands below, add or update:

- [x] **`tests/unit/easydiffraction/io/cif/test_handler.py`** —
  `CifHandler.iucr_name` resolver: explicit value used when set,
  fallback to `names[0]` when unset. P1.1 surface.
- [x] **`tests/unit/easydiffraction/io/cif/test_iucr_writer.py`** —
  fixture-driven golden tests for each topology covered in §2.3
  / §2.2 worked examples: single-crystal (Example A), single-
  experiment Rietveld CWL (Example B), joint Rietveld multi-
  experiment (Example C), sequential TOF Rietveld (Example D).
  Each golden compares the emitted file against a checked-in
  reference and asserts: block names, block order,
  `data_global` content, profile-data / reflections loop
  columns, project-extension `_easydiffraction_*` grouping at
  end of block, 80-char wrap. P1.11–P1.13 surface.
- [x] **`tests/unit/easydiffraction/io/cif/test_iucr_transformers.py`** —
  per-transformer unit tests: wavelength scalar vs loop based on
  multiplicity; TOF calibration loop with `id = offset / linear
  / quad / recip` and powers 0, 1, 2, −1; range-form excluded
  regions rendered to `_pd_proc.info_excluded_regions`;
  `_space_group_symop.*` loop derived from the active space
  group; extinction `(type, model)` →
  `_refine_ls.extinction_method` descriptive string and
  `_refine_ls.extinction_coef` value per the ADR §3 mapping
  table (Becker-Coppens type 1 / type 2 / mixed, Zachariasen).
  P1.14 surface.
- [x] **`tests/unit/easydiffraction/io/cif/test_serialize.py`** —
  update to cover ADP single-tag emission: rows with
  `ADP_type='Biso'` / `'Bani'` emit only the `B_*` family; rows
  with `ADP_type='Uiso'` / `'Uani'` emit only the `U_*` family.
  P1.3 surface.
- [x] **`tests/unit/easydiffraction/datablocks/structure/categories/atom_sites/test_default.py`** —
  update for the casing fixes from P1.2:
  `_atom_site.ADP_type` (uppercase ADP),
  `_atom_site.Wyckoff_symbol` (uppercase W, "symbol"); legacy
  lowercase forms still loadable on read.
- [x] **`tests/unit/easydiffraction/datablocks/structure/categories/space_group/test_default.py`** —
  update for `_space_group.name_H-M_alt` and
  `_space_group.IT_coordinate_system_code` casing fixes (P1.2).
- [x] **`tests/unit/easydiffraction/analysis/categories/fit_result/test_lsq.py`** —
  update for the new `_fit_result.*` fields from P1.4: each
  new descriptor (`R_factor_all`, `wR_factor_all`,
  `R_factor_gt`, `wR_factor_gt`, `prof_R_factor`,
  `prof_wR_factor`, `prof_wR_expected`, `number_restraints`,
  `number_constraints`, `shift_over_su_max`,
  `shift_over_su_mean`, `profile_function`,
  `background_function`, `threshold_expression`,
  `number_reflns_total`, `number_reflns_gt`) is read /
  written round-trip; fields unset for inapplicable
  experiment families remain `None`.
- [x] **`tests/unit/easydiffraction/report/test_report.py`** —
  new `Report` class: `save()` writes
  `reports/<project>.cif`; preserved display methods
  (`show_report`, `show_project_info`,
  `show_crystallographic_data`, `show_experimental_data`,
  `show_fitting_details`) keep their existing behaviour
  (port the relevant assertions from the current
  `tests/unit/easydiffraction/summary/`-equivalent tests if
  any exist; otherwise add coverage). P1.8 surface.
- [x] **`tests/unit/easydiffraction/report/test_check.py`** —
  `Report.check()` validates the generated CIF against
  `cif_core.dic` / `cif_pow.dic` via gemmi; surfaces unknown-
  tag warnings for non-extension categories; ignores the
  `_easydiffraction_*` namespace per the configured skip
  list. P1.16 surface.
- [x] **`tests/unit/easydiffraction/project/test_project.py`** —
  update / extend: `Project.save()` no longer writes
  `summary.cif`; `Project.save(report=True)` writes
  `reports/<project>.cif`; `Project.save(report=True,
  check=True)` runs validation; the `project.report` facade
  exposes `save`, `check`, and the preserved display
  methods. P1.8, P1.15, P1.16 surface.
- [x] **`tests/unit/easydiffraction/analysis/test_analysis.py`** —
  update for the project-extension `iucr_name` settings on
  `_minimizer.*`, `_calculator.*`, `_fitting_mode.*` (P1.7):
  default-save CIF tags unchanged; IUCr-export `iucr_name`
  resolves to `_easydiffraction_*` prefix.
- [ ] **Script / tutorial coverage.** Verify
  `pixi run script-tests` exercises at least one tutorial that
  calls `project.save(report=True)` and the resulting
  `reports/<project>.cif` is non-empty and gemmi-valid. If no
  tutorial exercises this, extend the relevant tutorial
  source per P1.17 and regenerate the notebook.

Use `pixi run test-structure-check` to confirm the
unit-test layout mirrors the source tree per AGENTS.md
§Testing.

## Verification commands (Phase 2)

Per AGENTS.md §Workflow, save any required check output with the
zsh-safe pattern. Variable names per-task:

```sh
pixi run fix > /tmp/easydiffraction-fix.log 2>&1; fix_exit_code=$?; tail -n 200 /tmp/easydiffraction-fix.log; exit $fix_exit_code
pixi run check > /tmp/easydiffraction-check.log 2>&1; check_exit_code=$?; tail -n 200 /tmp/easydiffraction-check.log; exit $check_exit_code
pixi run unit-tests > /tmp/easydiffraction-unit-tests.log 2>&1; unit_tests_exit_code=$?; tail -n 200 /tmp/easydiffraction-unit-tests.log; exit $unit_tests_exit_code
pixi run integration-tests > /tmp/easydiffraction-integration-tests.log 2>&1; integration_tests_exit_code=$?; tail -n 200 /tmp/easydiffraction-integration-tests.log; exit $integration_tests_exit_code
pixi run script-tests > /tmp/easydiffraction-script-tests.log 2>&1; script_tests_exit_code=$?; tail -n 200 /tmp/easydiffraction-script-tests.log; exit $script_tests_exit_code
```

Run in order; each must complete clean before the next. The
`pixi run script-tests` pass may surface tutorial path
collisions or stale tutorials — apply the tutorial-source fix
from AGENTS.md §Workflow ("If `pixi run script-tests` fails
because two tutorials write to the same project directory…")
rather than deleting project output. Benchmark CSVs under
`docs/dev/benchmarking/` produced by `pixi run script-tests` are
untracked verification artifacts; do not stage them.

## Suggested Pull Request

**Title:** `[scope] Align CIF tags with IUCr dictionaries and add journal-submission export`

**Description:**

EasyDiffraction now writes day-to-day project CIFs in a form that
matches the IUCr core and powder dictionaries where it makes
sense, while keeping the experiment-side names friendly for users
who edit CIFs by hand. Structure CIFs adopt the dictionary casing
(`_atom_site.ADP_type`, `_atom_site.Wyckoff_symbol`,
`_space_group.name_H-M_alt`, `_space_group.IT_coordinate_system_code`),
and atomic displacement parameters are written using a single
family per row (`B_*` or `U_*`) based on `_atom_site.ADP_type`.
Analysis CIFs gain a richer set of fit-output statistics — the
standard Rietveld R-factor family, restraint and constraint
counts, shift / σ diagnostics, profile and background function
descriptors — all under the existing topology-neutral
`_fit_result.*` category, with item names matching IUCr casing
so they are immediately recognisable to anyone familiar with
`_refine_ls.*` / `_pd_proc_ls.*` from publications.

A new `project.report` facade replaces the previously empty
`project.summary` placeholder. Calling `project.save(report=True)`
(or `project.report.save()`) generates a single
journal-submission CIF at `reports/<project>.cif` — one multi-
datablock file ready to upload to IUCr journals, with the
publication-metadata `data_global` block holding `?` placeholders
the user fills in before submission. The new `project.report.check()`
runs the generated file through `gemmi` against the IUCr
dictionaries to surface any tag, category, or type issues before
the upload.

The PR also amends four accepted ADRs (`analysis-cif-fit-state`,
`minimizer-input-output-split`, `project-facade-and-persistence`,
`help-discoverability`) to reflect the new facade and field set,
and promotes the `iucr-cif-tag-alignment` ADR from `suggestions/`
to `accepted/`.

**Scope label:** `[analysis]` or `[io]` — pick whichever the
maintainers prefer for the IUCr-export work; the field renames
in `analysis.cif` lean `[analysis]`, the new writer leans `[io]`.
