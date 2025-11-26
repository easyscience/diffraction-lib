# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from abc import ABC
from abc import abstractmethod
from typing import Any
from typing import List

import numpy as np

from easydiffraction.core.singletons import ConstraintsHandler
from easydiffraction.experiments.experiment.base import ExperimentBase
from easydiffraction.sample_models.sample_model.base import SampleModelBase
from easydiffraction.sample_models.sample_models import SampleModels


class CalculatorBase(ABC):
    """Base API for diffraction calculation engines."""

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def engine_imported(self) -> bool:
        pass

    @abstractmethod
    def calculate_structure_factors(
        self,
        sample_model: SampleModelBase,
        experiment: ExperimentBase,
    ) -> None:
        """Calculate structure factors for a single sample model and
        experiment.
        """
        pass

    def calculate_pattern(
        self,
        sample_models: SampleModels,
        experiment: ExperimentBase,
        called_by_minimizer: bool = False,
    ) -> None:
        """Calculate the diffraction pattern for multiple sample models
        and a single experiment. The calculated pattern is stored within
        the experiment's datastore.

        Args:
            sample_models: Collection of sample models.
            experiment: The experiment object.
            called_by_minimizer: Whether the calculation is called by a
                minimizer.
        """

        # TODO: Call update for all the datablocks involved, starting
        #  with sample_models, then experiment, to ensure all data is
        #  up-to-date before calculation.
        #  * In the case of sample models:
        #    - Apply user constraints
        #    - Apply symmetry constraints
        #  * In the case of experiment:
        #    - Update background data based on the bkg category
        #    - Update data refinement status flag based on the excluded
        #      regions category

        for sample_model in sample_models:
            sample_model._update_categories()
        experiment._update_categories(called_by_minimizer=called_by_minimizer)
        return







        valid_linked_phases = self._get_valid_linked_phases(sample_models, experiment)

        # Apply user constraints to all sample models
        constraints = ConstraintsHandler.get()
        constraints.apply()

        # Update categories
        experiment._update_categories()



        ###x_data = experiment.datastore.x
        x_data = experiment.data.x
        y_bkg = experiment.data.bkg
        initial_y_calc = np.zeros_like(x_data)

        # Calculate contributions from valid linked sample models
        y_calc_scaled = initial_y_calc
        for linked_phase in valid_linked_phases:
            sample_model_id = linked_phase._identity.category_entry_name
            sample_model_scale = linked_phase.scale.value
            sample_model = sample_models[sample_model_id]

            # Apply symmetry constraints
            #sample_model._apply_symmetry_constraints()


            sample_model._update_categories()


            sample_model_y_calc = self._calculate_single_model_pattern(
                sample_model,
                experiment,
                called_by_minimizer=called_by_minimizer,
            )

            # if not sample_model_y_calc:
            #    return np.ndarray([])

            sample_model_y_calc_scaled = sample_model_scale * sample_model_y_calc
            y_calc_scaled += sample_model_y_calc_scaled



        # Calculate total pattern
        y_calc_total = y_calc_scaled + y_bkg
        ###experiment.datastore.calc = y_calc_total
        # new 'data' instead of 'datastore'
        experiment.data._set_calc(y_calc_total)

        # TODO: Calculate and set d-spacing here???
        # ...


    @abstractmethod
    def _calculate_single_model_pattern(
        self,
        sample_model: SampleModels, # TODO: SampleModelBase?
        experiment: ExperimentBase,
        called_by_minimizer: bool,
    ) -> np.ndarray:
        """Calculate the diffraction pattern for a single sample model
        and experiment.

        Args:
            sample_model: The sample model object.
            experiment: The experiment object.
            called_by_minimizer: Whether the calculation is called by a
                minimizer.

        Returns:
            The calculated diffraction pattern as a NumPy array.
        """
        pass

    def _get_valid_linked_phases(
        self,
        sample_models: SampleModels,
        experiment: ExperimentBase,
    ) -> List[Any]:
        """Get valid linked phases from the experiment.

        Args:
            sample_models: Collection of sample models.
            experiment: The experiment object.

        Returns:
            A list of valid linked phases.
        """
        if not experiment.linked_phases:
            print('Warning: No linked phases defined. Returning empty pattern.')
            return []

        valid_linked_phases = []
        for linked_phase in experiment.linked_phases:
            if linked_phase._identity.category_entry_name not in sample_models.names:
                print(
                    f"Warning: Linked phase '{linked_phase.id.value}' not "
                    f'found in Sample Models {sample_models.names}. Skipping it.'
                )
                continue
            valid_linked_phases.append(linked_phase)

        if not valid_linked_phases:
            print(
                'Warning: None of the linked phases found in Sample '
                'Models. Returning empty pattern.'
            )

        return valid_linked_phases
