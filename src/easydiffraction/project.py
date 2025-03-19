from easydiffraction.sample_models.models import SampleModels
from easydiffraction.experiments.experiments import Experiments
from easydiffraction.analysis.analysis import Analysis
from easydiffraction.summary import Summary
import os
import datetime


class ProjectInfo:
    """
    Stores metadata about the project, such as ID, title, description, and file paths.
    """

    def __init__(self, project_id="untitled_project", title="Untitled Project", description="", path=None):
        self.id = project_id  # Short unique project identifier
        self.title = title
        self.description = description
        self.path = path or os.getcwd()
        self._created = datetime.datetime.now()
        self._last_modified = datetime.datetime.now()

    def update_last_modified(self):
        """Update the last modified timestamp."""
        self._last_modified = datetime.datetime.now()

    def as_cif(self) -> str:
        """Export project metadata to CIF."""
        return (
            f"_project_id               '{self.id}'\n"
            f"_project_title            '{self.title}'\n"
            f"_project_description      '{self.description}'\n"
            f"_project_created          '{self._created.isoformat()}'\n"
            f"_project_last_modified    '{self._last_modified.isoformat()}'\n"
        )


class Project:
    """
    Central API for managing a diffraction data analysis project.
    Provides access to sample models, experiments, analysis, and summary.
    """

    def __init__(self, project_id="untitled_project", title="Untitled Project", description=""):
        self.info = ProjectInfo(project_id=project_id, title=title, description=description)
        self.sample_models = SampleModels()
        self.experiments = Experiments()
        self.analysis = Analysis(self)
        self.summary = Summary(self)
        self._saved = False

    @property
    def id(self):
        """Convenience property to access the project's ID directly."""
        return self.info.id

    # ------------------------------------------
    #  Project File I/O
    # ------------------------------------------

    def load(self, dir_path: str):
        """
        Load a project from a given directory.
        Loads project info, sample models, experiments, etc.
        """
        print(f"Loading project from {dir_path} (stub implementation)")
        self.info.path = dir_path
        # TODO: load project components from files inside dir_path
        self._saved = True

    def save_as(self, dir_path: str):
        """
        Save the project into a new directory.
        """
        print(f"Saving project as new at {dir_path}")
        self.info.path = dir_path
        self.save()

    def save(self):
        """
        Save the project into the existing project directory.
        """
        if not self.info.path:
            raise ValueError("Project path not specified. Use save_as() to define the path first.")
        print(f"Saving project to {self.info.path}")
        # TODO: serialize project components to files
        self.info.update_last_modified()
        self._saved = True

    def reset(self):
        """
        Reset the project to its initial state.
        """
        print("Resetting project...")
        self.__init__()

    def as_cif(self) -> str:
        """
        Export the complete project (metadata + models + experiments + analysis + summary) as CIF.
        """
        return (
            self.info.as_cif() +
            "\n# Sample Models\n" +
            self.sample_models.as_cif() +
            "\n# Experiments\n" +
            self.experiments.as_cif() +
            "\n# Analysis\n" +
            self.analysis.as_cif() +
            "\n# Summary\n" +
            self.summary.as_cif()
        )

    # ------------------------------------------
    #  Sample Models API Convenience Methods
    # ------------------------------------------

    def set_sample_models(self, sample_models: SampleModels):
        """Attach a collection of sample models to the project."""
        self.sample_models = sample_models

    def set_experiments(self, experiments: Experiments):
        """Attach a collection of experiments to the project."""
        self.experiments = experiments