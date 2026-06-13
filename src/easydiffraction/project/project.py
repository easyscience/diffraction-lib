# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Project facade to orchestrate models, experiments, and analysis."""

from __future__ import annotations

import pathlib
import shutil
import tempfile
from typing import TYPE_CHECKING
from typing import ClassVar
from typing import NoReturn

from typeguard import typechecked
from varname import varname

from easydiffraction.analysis.analysis import Analysis
from easydiffraction.core.guard import GuardedBase
from easydiffraction.datablocks.experiment.collection import Experiments
from easydiffraction.datablocks.structure.collection import Structures
from easydiffraction.io.cif.serialize import analysis_from_cif
from easydiffraction.io.cif.serialize import project_config_from_cif
from easydiffraction.io.cif.serialize import project_config_to_cif
from easydiffraction.io.cif.serialize import project_to_cif
from easydiffraction.io.edstar import edstar_body_from_text
from easydiffraction.io.edstar import section_to_edstar
from easydiffraction.io.results_sidecar import read_analysis_results_sidecar
from easydiffraction.io.results_sidecar import write_analysis_results_sidecar
from easydiffraction.project.display import ProjectDisplay
from easydiffraction.project.project_config import ProjectConfig
from easydiffraction.utils.enums import VerbosityEnum
from easydiffraction.utils.environment import resolve_artifact_path
from easydiffraction.utils.logging import console
from easydiffraction.utils.logging import log
from easydiffraction.utils.utils import display_path

if TYPE_CHECKING:
    from collections.abc import Callable

    from easydiffraction.project.categories.rendering_plot import RenderingPlot
    from easydiffraction.project.categories.rendering_structure import RenderingStructure
    from easydiffraction.project.categories.rendering_table import RenderingTable
    from easydiffraction.project.categories.structure_style import StructureStyle
    from easydiffraction.project.categories.structure_view import StructureView
    from easydiffraction.project.categories.verbosity import Verbosity
    from easydiffraction.project.project_metadata import ProjectMetadata
    from easydiffraction.report import Report


def _raise_legacy_project_cif_error(
    path: pathlib.Path,
    *,
    replacement: str,
) -> NoReturn:
    """Raise an explicit migration error for beta project CIF input."""
    msg = (
        f"Legacy beta project CIF file '{path}' is no longer supported as "
        'project persistence. Open it in an EasyDiffraction version that '
        f'can read beta project CIF, then save it again to create {replacement}.'
    )
    raise ValueError(msg)


def _apply_csv_row_to_params(
    row: object,
    columns: object,
    param_map: dict[str, object],
    meta_columns: set[str],
) -> None:
    """
    Override parameter values and uncertainties from a CSV row.

    Parameters
    ----------
    row : object
        A pandas Series representing one CSV row.
    columns : object
        The DataFrame column index.
    param_map : dict[str, object]
        Map of ``unique_name`` → live Parameter objects.
    meta_columns : set[str]
        Column names to skip (non-parameter metadata).
    """
    import pandas as pd  # noqa: PLC0415

    for col_name in columns:
        if col_name in meta_columns or col_name.startswith('diffrn.'):
            continue
        if col_name.endswith('.uncertainty'):
            base_name = col_name.removesuffix('.uncertainty')
            if base_name in param_map and pd.notna(row[col_name]):
                param_map[base_name].uncertainty = float(row[col_name])
        elif col_name in param_map and pd.notna(row[col_name]):
            param_map[col_name].value = float(row[col_name])


def _apply_csv_row_to_diffrn(
    row: object,
    columns: object,
    experiment: object,
) -> None:
    """
    Override ``experiment.diffrn`` values from a CSV row.

    Parameters
    ----------
    row : object
        A pandas Series representing one CSV row.
    columns : object
        The DataFrame column index.
    experiment : object
        Live experiment whose ``diffrn`` descriptors are updated.
    """
    import pandas as pd  # noqa: PLC0415

    from easydiffraction.core.variable import NumericDescriptor  # noqa: PLC0415

    for col_name in columns:
        if not col_name.startswith('diffrn.') or pd.isna(row[col_name]):
            continue

        field_name = col_name.removeprefix('diffrn.')
        descriptor = getattr(experiment.diffrn, field_name, None)
        if isinstance(descriptor, NumericDescriptor):
            descriptor.value = float(row[col_name])


def _resolve_data_path_from_results_csv(
    project_path: pathlib.Path,
    file_path: object,
) -> pathlib.Path | None:
    """Resolve a CSV-stored data path against the project path."""
    if not isinstance(file_path, str) or not file_path:
        return None

    path = pathlib.Path(file_path)
    if path.is_absolute():
        return path
    return project_path / path


def _load_edstar_directory(
    section_dir: pathlib.Path,
    add_from_edstar_path: Callable[[str], None],
    *,
    replacement: str,
) -> None:
    """Load EdSTAR files and reject legacy-only project CIF files."""
    if not section_dir.is_dir():
        return

    edstar_files = sorted(section_dir.glob('*.edstar'))
    if edstar_files:
        for edstar_file in edstar_files:
            add_from_edstar_path(str(edstar_file))
        return

    legacy_files = sorted(section_dir.glob('*.cif'))
    if legacy_files:
        _raise_legacy_project_cif_error(
            legacy_files[0],
            replacement=replacement,
        )


def _create_loading_project(project_cls: type[Project]) -> Project:
    """Create a project instance while suppressing varname lookup."""
    project_cls._loading = True
    try:
        return project_cls()
    finally:
        project_cls._loading = False


def _load_project_metadata(project: Project, project_path: pathlib.Path) -> None:
    """
    Restore project configuration from EdSTAR.
    """
    project_edstar_path = project_path / 'project.edstar'
    if project_edstar_path.is_file():
        body = edstar_body_from_text(project_edstar_path.read_text())
        project_config_from_cif(project, body)
        return

    project_cif_path = project_path / 'project.cif'
    if project_cif_path.is_file():
        _raise_legacy_project_cif_error(
            project_cif_path,
            replacement='project.edstar',
        )

    msg = f"Project directory '{project_path}' must contain project.edstar."
    raise FileNotFoundError(msg)


def _resolved_analysis_path(project_path: pathlib.Path) -> pathlib.Path | None:
    """Return the preferred analysis path for a saved project."""
    for analysis_path in (
        project_path / 'analysis' / 'analysis.edstar',
        project_path / 'analysis.edstar',
    ):
        if analysis_path.is_file():
            return analysis_path

    for analysis_path in (
        project_path / 'analysis' / 'analysis.cif',
        project_path / 'analysis.cif',
    ):
        if analysis_path.is_file():
            _raise_legacy_project_cif_error(
                analysis_path,
                replacement='analysis/analysis.edstar',
            )
    return None


def _persistence_body_from_path(path: pathlib.Path) -> str:
    """Read EdSTAR text for a project section."""
    if path.suffix == '.edstar':
        text = path.read_text()
        return edstar_body_from_text(text)

    _raise_legacy_project_cif_error(path, replacement='a .edstar file')


def _load_project_analysis(project: Project, project_path: pathlib.Path) -> None:
    """Restore analysis categories and sidecar state from disk."""
    analysis_path = _resolved_analysis_path(project_path)
    if analysis_path is None:
        return

    analysis_from_cif(project._analysis, _persistence_body_from_path(analysis_path))
    read_analysis_results_sidecar(
        analysis=project._analysis,
        analysis_dir=analysis_path.parent,
    )
    param_map = project._build_parameter_map()
    if project._analysis.fit_parameters:
        project._analysis._restore_live_parameter_bounds_and_anchors(param_map)
    if project._analysis._has_persisted_fit_state():
        project._analysis._restore_live_parameter_posterior(param_map)


class Project(GuardedBase):  # noqa: PLR0904
    """
    Central API for managing a diffraction data analysis project.

    Provides access to structures, experiments, analysis, and reports.
    """

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------
    # Class-level sentinel: True while load() is constructing a project.
    _loading: bool = False
    _current_project: ClassVar[Project | None] = None

    def __init__(
        self,
        name: str = 'untitled_project',
        title: str = 'Untitled Project',
        description: str = '',
    ) -> None:
        super().__init__()

        self._config = ProjectConfig(name, title, description)
        object.__setattr__(self, '_metadata', self._config.metadata)
        self._structures = Structures()
        self._experiments = Experiments()
        object.__setattr__(self, '_rendering_plot', self._config.rendering_plot)
        object.__setattr__(self, '_rendering_table', self._config.rendering_table)
        object.__setattr__(self, '_verbosity', self._config.verbosity)
        object.__setattr__(self, '_rendering_structure', self._config.rendering_structure)
        object.__setattr__(self, '_structure_view', self._config.structure_view)
        object.__setattr__(self, '_structure_style', self._config.structure_style)
        object.__setattr__(self, '_report', self._config.report)
        self._display = ProjectDisplay(self)
        self._analysis = Analysis(self)
        self._saved = False
        self._varname = 'project' if type(self)._loading else varname()
        type(self)._current_project = self
        self._attach_category_parents()

    def _attach_category_parents(self) -> None:
        """Link directly owned project sections back to this project."""
        self._structures._parent = self
        self._experiments._parent = self
        self._analysis._parent = self
        self._rendering_plot._parent = self
        self._rendering_table._parent = self
        self._rendering_structure._parent = self
        self._structure_view._parent = self
        self._structure_style._parent = self
        self._report._parent = self

    @staticmethod
    def _supported_filters_for(category: object) -> dict[str, object]:
        """Return owner context filters for a switchable category."""
        del category
        return {}

    def _swap_rendering_plot(self, new_type: str, *, strict: bool = True) -> None:
        """Switch the active chart renderer."""
        self._rendering_plot._set_type(new_type, strict=strict)

    def _swap_rendering_table(self, new_type: str, *, strict: bool = True) -> None:
        """Switch the active table renderer."""
        self._rendering_table._set_type(new_type, strict=strict)

    def _swap_rendering_structure(self, new_type: str, *, strict: bool = True) -> None:
        """Switch the active structure-view renderer."""
        self._rendering_structure._set_type(new_type, strict=strict)

    @classmethod
    def current_project_path(cls) -> pathlib.Path | None:
        """Return the saved path of the current project, if any."""
        current_project = cls._current_project
        if current_project is None:
            return None
        return current_project.metadata.path

    # ------------------------------------------------------------------
    # Dunder methods
    # ------------------------------------------------------------------
    def __str__(self) -> str:
        """Human-readable representation."""
        class_name = self.__class__.__name__
        project_name = self.name
        structures_count = len(self.structures)
        experiments_count = len(self.experiments)
        return (
            f"{class_name} '{project_name}' "
            f'({structures_count} structures, '
            f'{experiments_count} experiments)'
        )

    # ------------------------------------------------------------------
    # Public read-only properties
    # ------------------------------------------------------------------

    @property
    def metadata(self) -> ProjectMetadata:
        """Project metadata container."""
        return self._metadata

    @property
    def name(self) -> str:
        """Convenience property for the project name."""
        return self._metadata.name

    @property
    def full_name(self) -> str:
        """
        Return the full project name (alias for :attr:`name`).

        Returns
        -------
        str
            The project name.
        """
        return self.name

    @property
    def structures(self) -> Structures:
        """Collection of structures in the project."""
        return self._structures

    @structures.setter
    @typechecked
    def structures(self, structures: Structures) -> None:
        self._structures = structures

    @property
    def experiments(self) -> Experiments:
        """Collection of experiments in the project."""
        return self._experiments

    @experiments.setter
    @typechecked
    def experiments(self, experiments: Experiments) -> None:
        self._experiments = experiments

    @property
    def rendering_plot(self) -> RenderingPlot:
        """Chart configuration bound to the project."""
        return self._rendering_plot

    @property
    def rendering_table(self) -> RenderingTable:
        """Table configuration bound to the project."""
        return self._rendering_table

    @property
    def rendering_structure(self) -> RenderingStructure:
        """Structure-view configuration bound to the project."""
        return self._rendering_structure

    @property
    def structure_view(self) -> StructureView:
        """Structure-view content and region bound to the project."""
        return self._structure_view

    @property
    def structure_style(self) -> StructureStyle:
        """Structure-view appearance bound to the project."""
        return self._structure_style

    @property
    def display(self) -> ProjectDisplay:
        """Current display entry-point bound to the project."""
        return self._display

    @property
    def analysis(self) -> Analysis:
        """Analysis entry-point bound to the project."""
        return self._analysis

    @property
    def report(self) -> Report:
        """Submission report builder bound to the project."""
        return self._report

    @property
    def parameters(self) -> list:
        """Return parameters from all structures and experiments."""
        return self.structures.parameters + self.experiments.parameters

    @property
    def free_parameters(self) -> list:
        """Return free parameters from structures and experiments."""
        return self.structures.free_parameters + self.experiments.free_parameters

    @property
    def as_cif(self) -> str:
        """Serialize the whole project as EasyDiffraction STAR text."""
        return project_to_cif(self)

    @property
    def verbosity(self) -> Verbosity:
        """Verbosity configuration bound to the project."""
        return self._verbosity

    @verbosity.setter
    def verbosity(self, value: str) -> None:
        """
        Set fitting process output verbosity.

        Parameters
        ----------
        value : str
            ``'full'`` for multi-line output, ``'short'`` for one-line
            status messages, or ``'silent'`` for no output.
        """
        self._verbosity.fit = VerbosityEnum(value).value

    # ------------------------------------------
    #  Project File I/O
    # ------------------------------------------

    @classmethod
    def load(cls, dir_path: str) -> Project:
        """
        Load a project from a saved directory.

        Reads EdSTAR project files from *dir_path* and reconstructs the
        full project state, including project-level display
        configuration. Legacy beta CIF project files are rejected with
        an explicit migration error.

        Parameters
        ----------
        dir_path : str
            Path to the project directory previously created by
            :meth:`save_as`.

        Returns
        -------
        Project
            A fully reconstructed project instance.

        Raises
        ------
        FileNotFoundError
            If *dir_path* does not exist.
        """
        project_path = pathlib.Path(dir_path)
        if not project_path.is_dir():
            msg = f"Project directory not found: '{dir_path}'"
            raise FileNotFoundError(msg)

        project = _create_loading_project(cls)
        project._saved = True

        _load_project_metadata(project, project_path)
        project.metadata.path = project_path
        _load_edstar_directory(
            project_path / 'structures',
            project._structures.add_from_edstar_path,
            replacement='structures/<structure>.edstar',
        )
        _load_edstar_directory(
            project_path / 'experiments',
            project._experiments.add_from_edstar_path,
            replacement='experiments/<experiment>.edstar',
        )
        _load_project_analysis(project, project_path)

        # 5. Resolve alias param references
        project._resolve_alias_references()

        # 6. Apply symmetry constraints and update categories
        for structure in project._structures:
            structure._update_categories()

        log.info(f"Project '{project.name}' loaded from '{dir_path}'.")
        return project

    def _resolve_alias_references(self) -> None:
        """
        Resolve alias ``parameter_unique_name`` strings to live objects.

        After loading structures and experiments from CIF, aliases only
        contain the ``parameter_unique_name`` string.  This method builds a
        ``{unique_name: param}`` map from all project parameters and
        wires each alias's ``_param_ref``.
        """
        aliases = self._analysis.aliases
        if not aliases._items:
            return

        param_map = self._build_parameter_map()

        for alias in aliases:
            uname = alias.parameter_unique_name.value
            if uname in param_map:
                alias._set_param(param_map[uname])
            else:
                log.warning(
                    f"Alias '{alias.id.value}' references unknown "
                    f"parameter '{uname}'. Reference not resolved."
                )

    def _build_parameter_map(self) -> dict[str, object]:
        """
        Return a ``unique_name`` to live parameter mapping.

        The map combines structure and experiment parameters and is
        reused by CIF restore steps that need to reconnect persisted
        names to live parameter objects.
        """
        all_params = self._structures.parameters + self._experiments.parameters
        param_map: dict[str, object] = {}
        for param in all_params:
            unique_name = getattr(param, 'unique_name', None)
            if unique_name is not None:
                param_map[unique_name] = param
        return param_map

    def save(self) -> None:
        """
        Save the project into the existing project directory.
        """
        if self.metadata.path is None:
            log.error('Project path not specified. Use save_as() to define the path first.')
            return

        console.paragraph(
            f"Saving project 📦 '{self.name}' to '{display_path(self.metadata.path)}'"
        )

        # Apply constraints so dependent parameters are flagged
        # before serialization (user-constrained params are written
        # without brackets).
        self._analysis._update_categories()

        # Ensure project directory exists
        self.metadata.path.mkdir(parents=True, exist_ok=True)

        # Save project-level configuration
        with (self.metadata.path / 'project.edstar').open('w') as f:
            f.write(section_to_edstar(project_config_to_cif(self)))
            console.print('├── 📄 project.edstar')

        # Save structures
        sm_dir = self.metadata.path / 'structures'
        sm_dir.mkdir(parents=True, exist_ok=True)
        console.print('├── 📁 structures/')
        for structure in self.structures.values():
            file_name: str = f'{structure.name}.edstar'
            file_path = sm_dir / file_name
            with file_path.open('w') as f:
                f.write(section_to_edstar(structure.as_cif))
                console.print(f'│   └── 📄 {file_name}')

        # Save experiments
        expt_dir = self.metadata.path / 'experiments'
        expt_dir.mkdir(parents=True, exist_ok=True)
        console.print('├── 📁 experiments/')
        for experiment in self.experiments.values():
            file_name: str = f'{experiment.name}.edstar'
            file_path = expt_dir / file_name
            with file_path.open('w') as f:
                f.write(section_to_edstar(experiment.as_cif))
                console.print(f'│   └── 📄 {file_name}')

        # Save analysis
        analysis_dir = self.metadata.path / 'analysis'
        analysis_dir.mkdir(parents=True, exist_ok=True)
        with (analysis_dir / 'analysis.edstar').open('w') as f:
            f.write(section_to_edstar(self.analysis.as_cif))
            console.print('├── 📁 analysis/')
        write_analysis_results_sidecar(
            analysis=self.analysis,
            analysis_dir=analysis_dir,
        )

        analysis_file_names = sorted(
            path.name
            for path in analysis_dir.iterdir()
            if path.is_file() and path.suffix in {'.edstar', '.csv', '.h5'}
        )
        for index, file_name in enumerate(analysis_file_names):
            branch = '└──' if index == len(analysis_file_names) - 1 else '├──'
            console.print(f'│   {branch} 📄 {file_name}')

        report_paths = self.report._save_configured()
        if report_paths:
            reports_dir = self.metadata.path / 'reports'
            console.print('└── 📁 reports/')
            for index, report_path in enumerate(report_paths):
                branch = '└──' if index == len(report_paths) - 1 else '├──'
                relative_path = report_path.relative_to(reports_dir)
                console.print(f'    {branch} 📄 {relative_path}')

        self.metadata.update_last_modified()
        self._saved = True

    def save_as(
        self,
        dir_path: str,
        *,
        temporary: bool = False,
        overwrite: bool = True,
    ) -> None:
        """
        Save the project into a directory.

        Parameters
        ----------
        dir_path : str
            Destination directory for the saved project.
        temporary : bool, default=False
            Whether to save beneath the system temporary directory.
        overwrite : bool, default=True
            Whether to remove an existing target directory before
            saving.
        """
        if temporary:
            tmp: str = tempfile.gettempdir()
            project_dir = pathlib.Path(tmp) / dir_path
        else:
            project_dir = resolve_artifact_path(dir_path)

        if overwrite and project_dir.is_dir():
            current_working_directory = pathlib.Path.cwd().resolve()
            resolved_project_dir = project_dir.resolve()
            if resolved_project_dir == current_working_directory:
                for child_path in resolved_project_dir.iterdir():
                    if child_path.is_dir():
                        shutil.rmtree(child_path)
                    else:
                        child_path.unlink()
            else:
                shutil.rmtree(project_dir)

        self.metadata.path = project_dir
        self.save()

    def apply_params_from_csv(self, row_index: int) -> None:
        """
        Load a single CSV row and apply its parameters to the project.

        Reads the row at *row_index* from ``analysis/results.csv``,
        overrides parameter values in the live project, and (for
        sequential-fit results where ``file_path`` points to a real
        file) reloads the measured data into the template experiment.

        After calling this method,
        ``display.plotter.plot_meas_vs_calc()`` will fit for that
        specific dataset.

        Parameters
        ----------
        row_index : int
            Row index in the CSV file. Supports Python-style negative
            indexing (e.g. ``-1`` for the last row).

        Raises
        ------
        FileNotFoundError
            If ``analysis/results.csv`` does not exist.
        IndexError
            If *row_index* is out of range.
        """
        import pandas as pd  # noqa: PLC0415

        from easydiffraction.analysis.sequential import _META_COLUMNS  # noqa: PLC0415
        from easydiffraction.core.variable import Parameter  # noqa: PLC0415

        if self.metadata.path is None:
            msg = 'Project has no saved path. Save the project first.'
            raise FileNotFoundError(msg)

        csv_path = pathlib.Path(self.metadata.path) / 'analysis' / 'results.csv'
        if not csv_path.is_file():
            msg = f"Results CSV not found: '{csv_path}'"
            raise FileNotFoundError(msg)

        df = pd.read_csv(csv_path)
        n_rows = len(df)

        # Support Python-style negative indexing
        if row_index < 0:
            row_index += n_rows

        if row_index < 0 or row_index >= n_rows:
            msg = f'Row index {row_index} out of range (CSV has {n_rows} rows).'
            raise IndexError(msg)

        row = df.iloc[row_index]

        experiment = next(iter(self.experiments.values()))

        # 1. Reload data if file_path points to a real file
        file_path = row.get('file_path', '')
        data_path = _resolve_data_path_from_results_csv(self.metadata.path, file_path)
        if data_path is not None and data_path.is_file():
            experiment._load_ascii_data_to_experiment(str(data_path))

        # 2. Restore extracted diffrn metadata from the CSV row.
        _apply_csv_row_to_diffrn(row, df.columns, experiment)

        # 3. Override parameter values and uncertainties
        all_params = self.structures.parameters + self.experiments.parameters
        param_map = {
            p.unique_name: p
            for p in all_params
            if isinstance(p, Parameter) and hasattr(p, 'unique_name')
        }
        _apply_csv_row_to_params(row, df.columns, param_map, set(_META_COLUMNS))

        # 4. Force recalculation: data was replaced directly (bypassing
        #    value setters), so the dirty flag may not be set.
        for structure in self.structures:
            structure._need_categories_update = True
        for experiment in self.experiments.values():
            experiment._need_categories_update = True

        log.info(f'Applied parameters from CSV row {row_index} (file: {file_path}).')
