# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

import datetime
import pathlib
import tempfile
from textwrap import wrap
from typing import List

from typeguard import typechecked
from varname import varname

from easydiffraction.analysis.analysis import Analysis
from easydiffraction.core.guards import GuardedBase
from easydiffraction.experiments.components.experiment_type import BeamModeEnum
from easydiffraction.experiments.experiments import Experiments
from easydiffraction.plotting.plotting import Plotter
from easydiffraction.sample_models.sample_models import SampleModels
from easydiffraction.summary import Summary
from easydiffraction.utils.formatting import error
from easydiffraction.utils.formatting import paragraph
from easydiffraction.utils.utils import render_cif
from easydiffraction.utils.utils import tof_to_d
from easydiffraction.utils.utils import twotheta_to_d


class ProjectInfo:
    """Stores metadata about the project, such as name, title,
    description, and file paths.
    """

    def __init__(self) -> None:
        self._name: str = 'untitled_project'
        self._title: str = 'Untitled Project'
        self._description: str = ''
        self._path: pathlib.Path = pathlib.Path.cwd()
        self._created: datetime.datetime = datetime.datetime.now()
        self._last_modified: datetime.datetime = datetime.datetime.now()

    @property
    def name(self) -> str:
        """Return the project name."""
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        self._name = value

    @property
    def title(self) -> str:
        """Return the project title."""
        return self._title

    @title.setter
    def title(self, value: str) -> None:
        self._title = value

    @property
    def description(self) -> str:
        """Return sanitized description with single spaces."""
        return ' '.join(self._description.split())

    @description.setter
    def description(self, value: str) -> None:
        self._description = ' '.join(value.split())

    @property
    def path(self) -> pathlib.Path:
        """Return the project path as a Path object."""
        return self._path

    @path.setter
    def path(self, value) -> None:
        # Accept str or Path; normalize to Path
        self._path = pathlib.Path(value)

    @property
    def created(self) -> datetime.datetime:
        """Return the creation timestamp."""
        return self._created

    @property
    def last_modified(self) -> datetime.datetime:
        """Return the last modified timestamp."""
        return self._last_modified

    def update_last_modified(self) -> None:
        """Update the last modified timestamp."""
        self._last_modified = datetime.datetime.now()

    def as_cif(self) -> str:
        """Export project metadata to CIF."""
        wrapped_title: List[str] = wrap(self.title, width=46)
        wrapped_description: List[str] = wrap(self.description, width=46)

        title_str: str = f"_project.title            '{wrapped_title[0]}'"
        for line in wrapped_title[1:]:
            title_str += f"\n{' ' * 27}'{line}'"

        if wrapped_description:
            base_indent: str = '_project.description      '
            indent_spaces: str = ' ' * len(base_indent)
            formatted_description: str = f"{base_indent}'{wrapped_description[0]}"
            for line in wrapped_description[1:]:
                formatted_description += f'\n{indent_spaces}{line}'
            formatted_description += "'"
        else:
            formatted_description: str = "_project.description      ''"

        return (
            f'_project.id               {self.name}\n'
            f'{title_str}\n'
            f'{formatted_description}\n'
            f"_project.created          '{self._created.strftime('%d %b %Y %H:%M:%S')}'\n"
            f"_project.last_modified    '{self._last_modified.strftime('%d %b %Y %H:%M:%S')}'\n"
        )

    def show_as_cif(self) -> None:
        cif_text: str = self.as_cif()
        paragraph_title: str = paragraph(f"Project 📦 '{self.name}' info as cif")
        render_cif(cif_text, paragraph_title)


class Project(GuardedBase):
    """Central API for managing a diffraction data analysis project.

    Provides access to sample models, experiments, analysis, and
    summary.
    """

    # ------------------------------------------------------------------
    # Class configuration
    # ------------------------------------------------------------------
    _class_public_attrs = {
        'name',
        'info',
        'sample_models',
        'experiments',
        'analysis',
        'summary',
        'plotter',
    }

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------
    def __init__(
        self,
        name: str = 'untitled_project',
        title: str = 'Untitled Project',
        description: str = '',
    ) -> None:
        self.info: ProjectInfo = ProjectInfo()
        self.info.name = name
        self.info.title = title
        self.info.description = description
        self._sample_models = SampleModels()
        self._experiments = Experiments()
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
        sample_models_count = len(self.sample_models)
        experiments_count = len(self.experiments)
        return (
            f"{class_name} '{project_name}' "
            f'({sample_models_count} sample models, '
            f'{experiments_count} experiments)'
        )

    # ------------------------------------------------------------------
    # Public read-only properties
    # ------------------------------------------------------------------

    @property
    def name(self) -> str:
        """Convenience property to access the project's name
        directly.
        """
        return self.info.name

    @property
    def full_name(self) -> str:
        return self.name

    @property
    def sample_models(self):
        return self._sample_models

    @sample_models.setter
    @typechecked
    def sample_models(self, sample_models: SampleModels):
        self._sample_models = sample_models

    @property
    def experiments(self):
        return self._experiments

    @experiments.setter
    @typechecked
    def experiments(self, experiments: Experiments):
        self._experiments = experiments

    @property
    def plotter(self):
        return self._plotter

    @property
    def analysis(self):
        return self._analysis

    @property
    def summary(self):
        return self._summary

    # ------------------------------------------
    #  Project File I/O
    # ------------------------------------------

    def load(self, dir_path: str) -> None:
        """Load a project from a given directory.

        Loads project info, sample models, experiments, etc.
        """
        print(paragraph(f'Loading project 📦 from {dir_path}'))
        print(dir_path)
        self.info.path = dir_path
        # TODO: load project components from files inside dir_path
        print('Loading project is not implemented yet.')
        self._saved = True

    def save(self) -> None:
        """Save the project into the existing project directory."""
        if not self.info.path:
            print(error('Project path not specified. Use save_as() to define the path first.'))
            return

        print(paragraph(f"Saving project 📦 '{self.name}' to"))
        print(self.info.path.resolve())

        # Ensure project directory exists
        self.info.path.mkdir(parents=True, exist_ok=True)

        # Save project info
        with (self.info.path / 'project.cif').open('w') as f:
            f.write(self.info.as_cif())
            print('✅ project.cif')

        # Save sample models
        sm_dir = self.info.path / 'sample_models'
        sm_dir.mkdir(parents=True, exist_ok=True)
        # Iterate over sample model objects (MutableMapping iter gives
        # keys)
        for model in self.sample_models.values():
            file_name: str = f'{model.name}.cif'
            file_path = sm_dir / file_name
            with file_path.open('w') as f:
                f.write(model.as_cif())
                print(f'✅ sample_models/{file_name}')

        # Save experiments
        expt_dir = self.info.path / 'experiments'
        expt_dir.mkdir(parents=True, exist_ok=True)
        for experiment in self.experiments.values():
            file_name: str = f'{experiment.name}.cif'
            file_path = expt_dir / file_name
            with file_path.open('w') as f:
                f.write(experiment.as_cif())
                print(f'✅ experiments/{file_name}')

        # Save analysis
        with (self.info.path / 'analysis.cif').open('w') as f:
            f.write(self.analysis.as_cif())
            print('✅ analysis.cif')

        # Save summary
        with (self.info.path / 'summary.cif').open('w') as f:
            f.write(self.summary.as_cif())
            print('✅ summary.cif')

        self.info.update_last_modified()
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
        self.info.path = dir_path
        self.save()

    # ------------------------------------------
    # Plotting
    # ------------------------------------------

    def plot_meas(
        self,
        expt_name,
        x_min=None,
        x_max=None,
        d_spacing=False,
    ):
        experiment = self.experiments[expt_name]
        datastore = experiment.datastore
        expt_type = experiment.type

        # Update d-spacing if necessary
        # TODO: This is done before every plot, and not when parameters
        #  needed for d-spacing conversion are changed. The reason is
        #  to minimize the performance impact during the fitting
        #  process. Need to find a better way to handle this.
        if d_spacing:
            self.update_pattern_d_spacing(expt_name)

        # Plot measured pattern
        self.plotter.plot_meas(
            datastore,
            expt_name,
            expt_type,
            x_min=x_min,
            x_max=x_max,
            d_spacing=d_spacing,
        )

    def plot_calc(
        self,
        expt_name,
        x_min=None,
        x_max=None,
        d_spacing=False,
    ):
        self.analysis.calculate_pattern(expt_name)  # Recalculate pattern
        experiment = self.experiments[expt_name]
        datastore = experiment.datastore
        expt_type = experiment.type

        # Update d-spacing if necessary
        # TODO: This is done before every plot, and not when parameters
        #  needed for d-spacing conversion are changed. The reason is
        #  to minimize the performance impact during the fitting
        #  process. Need to find a better way to handle this.
        if d_spacing:
            self.update_pattern_d_spacing(expt_name)

        # Plot calculated pattern
        self.plotter.plot_calc(
            datastore,
            expt_name,
            expt_type,
            x_min=x_min,
            x_max=x_max,
            d_spacing=d_spacing,
        )

    def plot_meas_vs_calc(
        self,
        expt_name,
        x_min=None,
        x_max=None,
        show_residual=False,
        d_spacing=False,
    ):
        self.analysis.calculate_pattern(expt_name)  # Recalculate pattern
        experiment = self.experiments[expt_name]
        datastore = experiment.datastore
        expt_type = experiment.type

        # Update d-spacing if necessary
        # TODO: This is done before every plot, and not when parameters
        #  needed for d-spacing conversion are changed. The reason is
        #  to minimize the performance impact during the fitting
        #  process. Need to find a better way to handle this.
        if d_spacing:
            self.update_pattern_d_spacing(expt_name)

        # Plot measured vs calculated
        self.plotter.plot_meas_vs_calc(
            datastore,
            expt_name,
            expt_type,
            x_min=x_min,
            x_max=x_max,
            show_residual=show_residual,
            d_spacing=d_spacing,
        )

    def update_pattern_d_spacing(self, expt_name: str) -> None:
        """Update the pattern's d-spacing based on the experiment's beam
        mode.
        """
        experiment = self.experiments[expt_name]
        datastore = experiment.datastore
        expt_type = experiment.type
        beam_mode = expt_type.beam_mode.value

        if beam_mode == BeamModeEnum.TIME_OF_FLIGHT:
            datastore.d = tof_to_d(
                datastore.x,
                experiment.instrument.calib_d_to_tof_offset.value,
                experiment.instrument.calib_d_to_tof_linear.value,
                experiment.instrument.calib_d_to_tof_quad.value,
            )
        elif beam_mode == BeamModeEnum.CONSTANT_WAVELENGTH:
            datastore.d = twotheta_to_d(
                datastore.x,
                experiment.instrument.setup_wavelength.value,
            )
        else:
            print(error(f'Unsupported beam mode: {beam_mode} for d-spacing update.'))
