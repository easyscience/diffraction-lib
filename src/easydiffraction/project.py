import os
import datetime
from textwrap import wrap

from easydiffraction.utils.formatting import paragraph, error
from easydiffraction.sample_models.sample_models import SampleModels
from easydiffraction.experiments.experiments import Experiments
from easydiffraction.analysis.analysis import Analysis
from easydiffraction.summary import Summary


class ProjectInfo:
    """
    Stores metadata about the project, such as ID, title, description, and file paths.
    """

    def __init__(self):
        self._id = "untitled_project"  # Short unique project identifier
        self._title = "Untitled Project"
        self._description = ""
        self._path = os.getcwd()
        self._created = datetime.datetime.now()
        self._last_modified = datetime.datetime.now()

    @property
    def id(self):
        """Return the project ID."""
        return self._id

    @property
    def title(self):
        """Return the project title."""
        return self._title

    @title.setter
    def title(self, value):
        self._title = value

    @property
    def description(self):
        """Return sanitized description with single spaces."""
        return ' '.join(self._description.split())

    @description.setter
    def description(self, value):
        self._description = ' '.join(value.split())

    @property
    def path(self):
        """Return the project path."""
        return self._path

    @path.setter
    def path(self, value):
        self._path = value

    @property
    def created(self):
        """Return the creation timestamp."""
        return self._created

    @property
    def last_modified(self):
        """Return the last modified timestamp."""
        return self._last_modified

    def update_last_modified(self):
        """Update the last modified timestamp."""
        self._last_modified = datetime.datetime.now()

    def as_cif(self) -> str:
        """Export project metadata to CIF."""
        wrapped_title = wrap(self.title, width=60)
        wrapped_description = wrap(self.description, width=60)

        title_str = f"_project.title            '{wrapped_title[0]}'"
        for line in wrapped_title[1:]:
            title_str += f"\n{' ' * 27}'{line}'"

        if wrapped_description:
            base_indent = "_project.description      "
            indent_spaces = " " * len(base_indent)
            formatted_description = f"{base_indent}'{wrapped_description[0]}"
            for line in wrapped_description[1:]:
                formatted_description += f"\n{indent_spaces}{line}"
            formatted_description += "'"
        else:
            formatted_description = "_project.description      ''"

        return (
            f"_project.id               {self.id}\n"
            f"{title_str}\n"
            f"{formatted_description}\n"
            f"_project.created          '{self._created.strftime('%d %b %Y %H:%M:%S')}'\n"
            f"_project.last_modified    '{self._last_modified.strftime('%d %b %Y %H:%M:%S')}'\n"
        )

    def show_as_cif(self):
        cif_text = self.as_cif()
        lines = cif_text.splitlines()
        max_width = max(len(line) for line in lines)
        padded_lines = [f"│ {line.ljust(max_width)} │" for line in lines]
        top = f"╒{'═' * (max_width + 2)}╕"
        bottom = f"╘{'═' * (max_width + 2)}╛"

        print(paragraph(f"Project 📦 '{self.id}' info as cif"))
        print(top)
        print("\n".join(padded_lines))
        print(bottom)


class Project:
    """
    Central API for managing a diffraction data analysis project.
    Provides access to sample models, experiments, analysis, and summary.
    """

    def __init__(self, project_id="untitled_project", title="Untitled Project", description=""):
        self.info = ProjectInfo()
        self.info._id = project_id
        self.info.title = title
        self.info.description = description
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
        print(paragraph(f"Loading project 📦 from {dir_path}"))
        print(dir_path)
        self.info.path = dir_path
        # TODO: load project components from files inside dir_path
        print('Loading project is not implemented yet.')
        self._saved = True

    def save_as(self, dir_path: str):
        """
        Save the project into a new directory.
        """
        self.info.path = dir_path
        self.save()

    def save(self):
        """
        Save the project into the existing project directory.
        """
        if not self.info.path:
            print(error("Project path not specified. Use save_as() to define the path first."))
            return

        print(paragraph(f"Saving project 📦 '{self.id}' to"))
        print(os.path.abspath(self.info.path))

        os.makedirs(self.info.path, exist_ok=True)

        # Save project info
        with open(os.path.join(self.info.path, "project.cif"), "w") as f:
            f.write(self.info.as_cif())
            print("✅ project.cif")

        # Save sample models
        sm_dir = os.path.join(self.info.path, "sample_models")
        os.makedirs(sm_dir, exist_ok=True)
        for model in self.sample_models:
            file_name = f"{model.model_id}.cif"
            file_path = os.path.join(sm_dir, file_name)
            with open(file_path, "w") as f:
                f.write(model.as_cif())
                print(f"✅ sample_models/{file_name}")

        # Save experiments
        expt_dir = os.path.join(self.info.path, "experiments")
        os.makedirs(expt_dir, exist_ok=True)
        for experiment in self.experiments:
            file_name = f"{experiment.id}.cif"
            file_path = os.path.join(expt_dir, file_name)
            with open(file_path, "w") as f:
                f.write(experiment.as_cif())
                print(f"✅ sample_models/{file_name}")

        # Save analysis
        with open(os.path.join(self.info.path, "analysis.cif"), "w") as f:
            f.write(self.analysis.as_cif())
            print("✅ analysis.cif")

        # Save summary
        with open(os.path.join(self.info.path, "summary.cif"), "w") as f:
            f.write(self.summary.as_cif())
            print("✅ summary.cif")

        self.info.update_last_modified()
        self._saved = True

    # ------------------------------------------
    #  Sample Models API Convenience Methods
    # ------------------------------------------

    def set_sample_models(self, sample_models: SampleModels):
        """Attach a collection of sample models to the project."""
        self.sample_models = sample_models

    def set_experiments(self, experiments: Experiments):
        """Attach a collection of experiments to the project."""
        self.experiments = experiments