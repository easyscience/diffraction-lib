"""
EasyDiffraction - High-level interface for diffraction data modeling and analysis.
"""

# Project management
from easydiffraction.project import Project, ProjectInfo

# Sample model management
from easydiffraction.sample_models.models import SampleModel, SampleModels

# Experiment creation and collection management
from easydiffraction.experiments.experiments import Experiment, Experiments

# Analysis and summary
from easydiffraction.analysis.analysis import Analysis
from easydiffraction.summary import Summary

# Version
__version__ = "0.1.0"

# Expose the public API
__all__ = [
    "Project",
    "ProjectInfo",
    "SampleModel",
    "SampleModels",
    "Experiment",
    "Experiments",
    "Analysis",
    "Summary",
]