import numpy as np

from abc import ABC, abstractmethod

class CalculatorBase(ABC):
    """
    Base API for diffraction calculation engines.
    """

    @property
    @abstractmethod
    def name(self):
        pass

    @property
    @abstractmethod
    def engine_imported(self):
        pass

    @abstractmethod
    def calculate_structure_factors(self, sample_model, experiment):
        # Single sample model, single experiment
        pass

    def calculate_pattern(self,
                          sample_models,
                          experiment,
                          called_by_minimizer=False):
        # Multiple sample models, single experiment

        x_data = experiment.datastore.pattern.x
        y_calc_zeros = np.zeros_like(x_data)

        valid_linked_phases = self._get_valid_linked_phases(sample_models, experiment)

        # Calculate contributions from valid linked sample models
        y_calc_scaled = y_calc_zeros
        for linked_phase in valid_linked_phases:
            sample_model_id = linked_phase.id.value
            sample_model_scale = linked_phase.scale.value
            sample_model = sample_models[sample_model_id]

            sample_model_y_calc = self._calculate_single_model_pattern(sample_model,
                                                                       experiment,
                                                                       called_by_minimizer=called_by_minimizer)

            sample_model_y_calc_scaled = sample_model_scale * sample_model_y_calc
            y_calc_scaled += sample_model_y_calc_scaled

        # Calculate background contribution
        y_bkg = experiment.background.calculate(x_data)
        experiment.datastore.pattern.bkg = y_bkg

        # Calculate total pattern
        y_calc_total = y_calc_scaled + y_bkg
        experiment.datastore.pattern.calc = y_calc_total

        return y_calc_total

    @abstractmethod
    def _calculate_single_model_pattern(self,
                                        sample_model,
                                        experiment,
                                        called_by_minimizer):
        pass

    def _get_valid_linked_phases(self, sample_models, experiment):
        if not experiment.linked_phases:
            print('Warning: No linked phases found. Returning empty pattern.')
            return []

        valid_linked_phases = []
        for linked_phase in experiment.linked_phases:
            if linked_phase.id.value not in sample_models.get_ids():
                print(f"Warning: Linked phase '{linked_phase.id.value}' not found in Sample Models {sample_models.get_ids()}")
                continue
            valid_linked_phases.append(linked_phase)

        if not valid_linked_phases:
            print('Warning: None of the linked phases found in Sample Models. Returning empty pattern.')

        return valid_linked_phases