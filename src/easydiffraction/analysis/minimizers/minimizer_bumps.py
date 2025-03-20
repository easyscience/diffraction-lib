from bumps.fitproblem import FitProblem
from bumps.fitters import fit as bumps_fit
from .base import MinimizerBase


class BumpsMinimizer(MinimizerBase):
    """
    Minimizer using the bumps package.
    """

    def __init__(self, method='lm'):
        self.result = None
        self.method = method

    def fit(self, sample_models, experiments, calculator):
        print("🔧 [DEBUG] Starting BumpsMinimizer.fit()")

        parameters = self._collect_free_parameters(sample_models, experiments)
        print(f"🔧 [DEBUG] Collected {len(parameters)} free parameters")

        if not parameters:
            print("⚠️ No parameters selected for refinement. Aborting fit.")
            return None

        engine_parameters = self._prepare_parameters(parameters)
        print(f"🔧 [DEBUG] Prepared {len(engine_parameters)} engine parameters")

        bumps_model = self._create_bumps_model(engine_parameters,
                                               parameters,
                                               sample_models,
                                               experiments,
                                               calculator)
        print("🔧 [DEBUG] Bumps model created")

        problem = FitProblem(bumps_model)
        print("🔧 [DEBUG] FitProblem initialized")

        method_dict = {'method': self.method}

        fit_result = bumps_fit(problem, **method_dict)
        print("✅ [DEBUG] Bumps fitting completed")

        BumpsMinimizer._sync_parameters(fit_result)  # Implemented here
        print("🔧 [DEBUG] Parameters synced after fit")

        self.result = fit_result

        return self.result

    @staticmethod
    def _sync_parameters(engine_params, parameters):
        for param in parameters:
            param_name = param.id
            if param_name in engine_params:
                param.value = engine_params[param_name].value
                param.error = engine_params[param_name].stderr
                print(f"🔧 [DEBUG] Synced parameter '{param.id}': value={param.value}, error={param.error}")

    def _objective_function(self, engine_params, parameters, sample_models, experiments, calculator):
        residuals = []
        for expt_id, experiment in experiments._items.items():
            y_calc = calculator.calculate_pattern(sample_models, experiment)
            y_meas = experiment.datastore.pattern.meas
            y_meas_su = experiment.datastore.pattern.meas_su

            diff = (y_meas - y_calc) / y_meas_su
            residuals.extend(diff)

        import numpy as np
        return np.array(residuals)