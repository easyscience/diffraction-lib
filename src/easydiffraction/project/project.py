# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Project facade to orchestrate models, experiments, and analysis."""

from __future__ import annotations

import pathlib
import tempfile

from typeguard import typechecked
from varname import varname

from easydiffraction.analysis.analysis import Analysis
from easydiffraction.core.guard import GuardedBase
from easydiffraction.datablocks.experiment.collection import Experiments
from easydiffraction.datablocks.structure.collection import Structures
from easydiffraction.display.plotting import Plotter
from easydiffraction.display.tables import TableRenderer
from easydiffraction.io.cif.serialize import project_to_cif
from easydiffraction.project.project_info import ProjectInfo
from easydiffraction.summary.summary import Summary
from easydiffraction.utils.enums import VerbosityEnum
from easydiffraction.utils.logging import console
from easydiffraction.utils.logging import log


class Project(GuardedBase):
    """
    Central API for managing a diffraction data analysis project.

    Provides access to structures, experiments, analysis, and summary.
    """

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------
    # Class-level sentinel: True while load() is constructing a project.
    _loading: bool = False

    def __init__(
        self,
        name: str = 'untitled_project',
        title: str = 'Untitled Project',
        description: str = '',
    ) -> None:
        super().__init__()

        self._info: ProjectInfo = ProjectInfo(name, title, description)
        self._structures = Structures()
        self._experiments = Experiments()
        self._tabler = TableRenderer.get()
        self._plotter = Plotter()
        self._analysis = Analysis(self)
        self._summary = Summary(self)
        self._saved = False
        self._varname = 'project' if type(self)._loading else varname()
        self._verbosity: VerbosityEnum = VerbosityEnum.FULL

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
    def info(self) -> ProjectInfo:
        """Project metadata container."""
        return self._info

    @property
    def name(self) -> str:
        """Convenience property for the project name."""
        return self._info.name

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
    def plotter(self) -> Plotter:
        """Plotting facade bound to the project."""
        return self._plotter

    @property
    def tabler(self) -> TableRenderer:
        """Tables rendering facade bound to the project."""
        return self._tabler

    @property
    def analysis(self) -> Analysis:
        """Analysis entry-point bound to the project."""
        return self._analysis

    @property
    def summary(self) -> Summary:
        """Summary report builder bound to the project."""
        return self._summary

    @property
    def parameters(self) -> list:
        """Return parameters from all structures and experiments."""
        return self.structures.parameters + self.experiments.parameters

    @property
    def as_cif(self) -> str:
        """Export whole project as CIF text."""
        # Concatenate sections using centralized CIF serializers
        return project_to_cif(self)

    @property
    def verbosity(self) -> str:
        """
        Project-wide console output verbosity.

        Returns
        -------
        str
            One of ``'full'``, ``'short'``, or ``'silent'``.
        """
        return self._verbosity.value

    @verbosity.setter
    def verbosity(self, value: str) -> None:
        """
        Set project-wide console output verbosity.

        Parameters
        ----------
        value : str
            ``'full'`` for multi-line output, ``'short'`` for one-line
            status messages, or ``'silent'`` for no output.
        """
        self._verbosity = VerbosityEnum(value)

    # ------------------------------------------
    #  Project File I/O
    # ------------------------------------------

    @classmethod
    def load(cls, dir_path: str) -> Project:
        """
        Load a project from a saved directory.

        Reads ``project.cif``, ``structures/*.cif``,
        ``experiments/*.cif``, and ``analysis.cif`` from *dir_path* and
        reconstructs the full project state.

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
        from easydiffraction.io.cif.serialize import analysis_from_cif  # noqa: PLC0415
        from easydiffraction.io.cif.serialize import project_info_from_cif  # noqa: PLC0415

        project_path = pathlib.Path(dir_path)
        if not project_path.is_dir():
            msg = f"Project directory not found: '{dir_path}'"
            raise FileNotFoundError(msg)

        # Create a minimal project.
        # Use _loading sentinel to skip varname() inside __init__.
        cls._loading = True
        try:
            project = cls()
        finally:
            cls._loading = False
        project._saved = True

        # 1. Load project info
        project_cif_path = project_path / 'project.cif'
        if project_cif_path.is_file():
            cif_text = project_cif_path.read_text()
            project_info_from_cif(project._info, cif_text)

        project._info.path = project_path

        # 2. Load structures
        structures_dir = project_path / 'structures'
        if structures_dir.is_dir():
            for cif_file in sorted(structures_dir.glob('*.cif')):
                project._structures.add_from_cif_path(str(cif_file))

        # 3. Load experiments
        experiments_dir = project_path / 'experiments'
        if experiments_dir.is_dir():
            for cif_file in sorted(experiments_dir.glob('*.cif')):
                project._experiments.add_from_cif_path(str(cif_file))

        # 4. Load analysis
        #    Check analysis/analysis.cif first (future layout), then
        #    fall back to analysis.cif at root (current layout).
        analysis_cif_path = project_path / 'analysis' / 'analysis.cif'
        if not analysis_cif_path.is_file():
            analysis_cif_path = project_path / 'analysis.cif'
        if analysis_cif_path.is_file():
            cif_text = analysis_cif_path.read_text()
            analysis_from_cif(project._analysis, cif_text)

        # 5. Resolve alias param references
        project._resolve_alias_references()

        # 6. Apply symmetry constraints and update categories
        for structure in project._structures:
            structure._update_categories()

        log.info(f"Project '{project.name}' loaded from '{dir_path}'.")
        return project

    def _resolve_alias_references(self) -> None:
        """
        Resolve alias ``param_unique_name`` strings to live objects.

        After loading structures and experiments from CIF, aliases only
        contain the ``param_unique_name`` string.  This method builds a
        ``{unique_name: param}`` map from all project parameters and
        wires each alias's ``_param_ref``.
        """
        aliases = self._analysis.aliases
        if not aliases._items:
            return

        # Build unique_name → parameter map
        all_params = self._structures.parameters + self._experiments.parameters
        param_map: dict[str, object] = {}
        for p in all_params:
            uname = getattr(p, 'unique_name', None)
            if uname is not None:
                param_map[uname] = p

        for alias in aliases:
            uname = alias.param_unique_name.value
            if uname in param_map:
                alias._set_param(param_map[uname])
            else:
                log.warning(
                    f"Alias '{alias.label.value}' references unknown "
                    f"parameter '{uname}'. Reference not resolved."
                )

    def save(self) -> None:
        """Save the project into the existing project directory."""
        if self._info.path is None:
            log.error('Project path not specified. Use save_as() to define the path first.')
            return

        console.paragraph(f"Saving project 📦 '{self.name}' to")
        console.print(self.info.path.resolve())

        # Apply constraints so dependent parameters are flagged
        # before serialization (constrained params are written
        # without brackets).
        self._analysis._update_categories()

        # Ensure project directory exists
        self._info.path.mkdir(parents=True, exist_ok=True)

        # Save project info
        with (self._info.path / 'project.cif').open('w') as f:
            f.write(self._info.as_cif())
            console.print('├── 📄 project.cif')

        # Save structures
        sm_dir = self._info.path / 'structures'
        sm_dir.mkdir(parents=True, exist_ok=True)
        console.print('├── 📁 structures/')
        for structure in self.structures.values():
            file_name: str = f'{structure.name}.cif'
            file_path = sm_dir / file_name
            with file_path.open('w') as f:
                f.write(structure.as_cif)
                console.print(f'│   └── 📄 {file_name}')

        # Save experiments
        expt_dir = self._info.path / 'experiments'
        expt_dir.mkdir(parents=True, exist_ok=True)
        console.print('├── 📁 experiments/')
        for experiment in self.experiments.values():
            file_name: str = f'{experiment.name}.cif'
            file_path = expt_dir / file_name
            with file_path.open('w') as f:
                f.write(experiment.as_cif)
                console.print(f'│   └── 📄 {file_name}')

        # Save analysis
        analysis_dir = self._info.path / 'analysis'
        analysis_dir.mkdir(parents=True, exist_ok=True)
        with (analysis_dir / 'analysis.cif').open('w') as f:
            f.write(self.analysis.as_cif())
            console.print('├── 📁 analysis/')
            console.print('│   └── 📄 analysis.cif')

        # Save summary
        with (self._info.path / 'summary.cif').open('w') as f:
            f.write(self.summary.as_cif())
            console.print('└── 📄 summary.cif')

        self._info.update_last_modified()
        self._saved = True

    def save_as(
        self,
        dir_path: str,
        temporary: bool = False,
    ) -> None:
        """Save the project into a new directory."""
        if temporary:
            tmp: str = tempfile.gettempdir()
            dir_path = pathlib.Path(tmp) / dir_path
        self._info.path = dir_path
        self.save()

    def apply_params_from_csv(self, row_index: int) -> None:
        """
        Load a single CSV row and apply its parameters to the project.

        Reads the row at *row_index* from ``analysis/results.csv``,
        overrides parameter values in the live project, and (for
        sequential-fit results where ``file_path`` points to a real
        file) reloads the measured data into the template experiment.

        After calling this method, ``plot_meas_vs_calc()`` will show the
        fit for that specific dataset.

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

        if self.info.path is None:
            msg = 'Project has no saved path. Save the project first.'
            raise FileNotFoundError(msg)

        csv_path = pathlib.Path(self.info.path) / 'analysis' / 'results.csv'
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

        # 1. Reload data if file_path points to a real file
        file_path = row.get('file_path', '')
        if file_path and pathlib.Path(file_path).is_file():
            experiment = list(self.experiments.values())[0]
            experiment._load_ascii_data_to_experiment(file_path)

        # 2. Override parameter values
        all_params = self.structures.parameters + self.experiments.parameters
        param_map = {
            p.unique_name: p
            for p in all_params
            if isinstance(p, Parameter) and hasattr(p, 'unique_name')
        }

        skip_cols = set(_META_COLUMNS)
        for col_name in df.columns:
            if col_name in skip_cols:
                continue
            if col_name.startswith('diffrn.'):
                continue
            if col_name.endswith('.uncertainty'):
                continue
            if col_name in param_map and pd.notna(row[col_name]):
                param_map[col_name].value = float(row[col_name])

        # 3. Apply uncertainties
        for col_name in df.columns:
            if not col_name.endswith('.uncertainty'):
                continue
            base_name = col_name.removesuffix('.uncertainty')
            if base_name in param_map and pd.notna(row[col_name]):
                param_map[base_name].uncertainty = float(row[col_name])

        # 4. Force recalculation: data was replaced directly (bypassing
        #    value setters), so the dirty flag may not be set.
        for structure in self.structures:
            structure._need_categories_update = True
        for experiment in self.experiments.values():
            experiment._need_categories_update = True

        log.info(f'Applied parameters from CSV row {row_index} (file: {file_path}).')

    # ------------------------------------------
    # Plotting
    # ------------------------------------------

    def _update_categories(self, expt_name: str) -> None:
        for structure in self.structures:
            structure._update_categories()
        self.analysis._update_categories()
        experiment = self.experiments[expt_name]
        experiment._update_categories()

    def plot_meas(
        self,
        expt_name: str,
        x_min: float | None = None,
        x_max: float | None = None,
        x: object | None = None,
    ) -> None:
        """
        Plot measured diffraction data for an experiment.

        Parameters
        ----------
        expt_name : str
            Name of the experiment to plot.
        x_min : float | None, default=None
            Lower bound for the x-axis range.
        x_max : float | None, default=None
            Upper bound for the x-axis range.
        x : object | None, default=None
            Optional explicit x-axis data to override stored values.
        """
        self._update_categories(expt_name)
        experiment = self.experiments[expt_name]

        self.plotter.plot_meas(
            experiment.data,
            expt_name,
            experiment.type,
            x_min=x_min,
            x_max=x_max,
            x=x,
        )

    def plot_calc(
        self,
        expt_name: str,
        x_min: float | None = None,
        x_max: float | None = None,
        x: object | None = None,
    ) -> None:
        """
        Plot calculated diffraction pattern for an experiment.

        Parameters
        ----------
        expt_name : str
            Name of the experiment to plot.
        x_min : float | None, default=None
            Lower bound for the x-axis range.
        x_max : float | None, default=None
            Upper bound for the x-axis range.
        x : object | None, default=None
            Optional explicit x-axis data to override stored values.
        """
        self._update_categories(expt_name)
        experiment = self.experiments[expt_name]

        self.plotter.plot_calc(
            experiment.data,
            expt_name,
            experiment.type,
            x_min=x_min,
            x_max=x_max,
            x=x,
        )

    def plot_meas_vs_calc(
        self,
        expt_name: str,
        x_min: float | None = None,
        x_max: float | None = None,
        show_residual: bool = False,
        x: object | None = None,
    ) -> None:
        """
        Plot measured vs calculated data for an experiment.

        Parameters
        ----------
        expt_name : str
            Name of the experiment to plot.
        x_min : float | None, default=None
            Lower bound for the x-axis range.
        x_max : float | None, default=None
            Upper bound for the x-axis range.
        show_residual : bool, default=False
            When ``True``, include the residual (difference) curve.
        x : object | None, default=None
            Optional explicit x-axis data to override stored values.
        """
        self._update_categories(expt_name)
        experiment = self.experiments[expt_name]

        self.plotter.plot_meas_vs_calc(
            experiment.data,
            expt_name,
            experiment.type,
            x_min=x_min,
            x_max=x_max,
            show_residual=show_residual,
            x=x,
        )

    def plot_param_series(self, param: object, versus: object | None = None) -> None:
        """
        Plot a parameter's value across sequential fit results.

        When a ``results.csv`` file exists in the project's
        ``analysis/`` directory, data is read from CSV.  Otherwise,
        falls back to in-memory parameter snapshots (produced by
        ``fit()`` in single mode).

        Parameters
        ----------
        param : object
            Parameter descriptor whose ``unique_name`` identifies the
            values to plot.
        versus : object | None, default=None
            A diffrn descriptor (e.g.
            ``expt.diffrn.ambient_temperature``) whose value is used as
            the x-axis for each experiment.  When ``None``, the
            experiment sequence number is used instead.
        """
        unique_name = param.unique_name

        # Try CSV first (produced by fit_sequential or future fit)
        csv_path = None
        if self.info.path is not None:
            candidate = pathlib.Path(self.info.path) / 'analysis' / 'results.csv'
            if candidate.is_file():
                csv_path = str(candidate)

        if csv_path is not None:
            self.plotter.plot_param_series(
                csv_path=csv_path,
                unique_name=unique_name,
                param_descriptor=param,
                versus_descriptor=versus,
            )
        else:
            # Fallback: in-memory snapshots from fit() single mode
            versus_name = versus.name if versus is not None else None
            self.plotter.plot_param_series_from_snapshots(
                unique_name,
                versus_name,
                self.experiments,
                self.analysis._parameter_snapshots,
            )
