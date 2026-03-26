# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Project facade to orchestrate models, experiments, and analysis."""

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
        self._varname = varname()

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
        """
        Convenience property to access the project's name directly.
        """
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

    # ------------------------------------------
    #  Project File I/O
    # ------------------------------------------

    def load(self, dir_path: str) -> None:
        """
        Load a project from a given directory.

        Loads project info, structures, experiments, etc.
        """
        # TODO: load project components from files inside dir_path
        raise NotImplementedError('Project.load() is not implemented yet.')

    def save(self) -> None:
        """Save the project into the existing project directory."""
        if not self._info.path:
            log.error('Project path not specified. Use save_as() to define the path first.')
            return

        console.paragraph(f"Saving project 📦 '{self.name}' to")
        console.print(self.info.path.resolve())

        # Ensure project directory exists
        self._info.path.mkdir(parents=True, exist_ok=True)

        # Save project info
        with (self._info.path / 'project.cif').open('w') as f:
            f.write(self._info.as_cif())
            console.print('├── 📄 project.cif')

        # Save structures
        sm_dir = self._info.path / 'structures'
        sm_dir.mkdir(parents=True, exist_ok=True)
        # Iterate over structure objects (MutableMapping iter gives
        # keys)
        for structure in self.structures.values():
            file_name: str = f'{structure.name}.cif'
            file_path = sm_dir / file_name
            console.print('├── 📁 structures')
            with file_path.open('w') as f:
                f.write(structure.as_cif)
                console.print(f'│   └── 📄 {file_name}')

        # Save experiments
        expt_dir = self._info.path / 'experiments'
        expt_dir.mkdir(parents=True, exist_ok=True)
        for experiment in self.experiments.values():
            file_name: str = f'{experiment.name}.cif'
            file_path = expt_dir / file_name
            console.print('├── 📁 experiments')
            with file_path.open('w') as f:
                f.write(experiment.as_cif)
                console.print(f'│   └── 📄 {file_name}')

        # Save analysis
        with (self._info.path / 'analysis.cif').open('w') as f:
            f.write(self.analysis.as_cif())
            console.print('├── 📄 analysis.cif')

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
