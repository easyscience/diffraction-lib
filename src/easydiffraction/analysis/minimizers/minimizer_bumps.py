import numpy as np
from bumps.fitproblem import FitProblem
from bumps.fitters import fit as bumps_fit
from bumps.parameter import Parameter as BumpsParameter
from .minimizer_base import MinimizerBase


class BumpsMinimizer(MinimizerBase):
    """
    Minimizer using the bumps package.
    """

    def __init__(self, method='lm'):
        self.result = None
        self.method = method
        self.fitness = None  # Initialize fitness object

    def fit(self, sample_models, experiments, calculator):
        print("🚀 [DEBUG] Starting BumpsMinimizer.fit()")

        # Collect free parameters
        parameters = self._collect_free_parameters(sample_models, experiments)
        print(f"🔧 [DEBUG] Collected {len(parameters)} free parameters")

        if not parameters:
            print("⚠️ [DEBUG] No parameters selected for refinement. Aborting fit.")
            return None

        # Prepare parameters for the engine
        engine_parameters, parinfo = self._prepare_parameters(parameters)
        print(f"🔧 [DEBUG] Prepared {len(engine_parameters)} engine parameters")
        print(f"🔧 [DEBUG] Engine parameters: {engine_parameters}")
        print(f"🔧 [DEBUG] Parinfo: {parinfo}")

        # Ensure experiments is not empty and contains the expected data
        if not experiments:
            print("⚠️ [DEBUG] No experiments found. Aborting fit.")
            return None

        # Get the experiment data (x, y, dy)
        experiment = list(experiments._items.values())[0]  # Assuming there's at least one experiment
        x = experiment.datastore.pattern.x  # Independent variable (e.g., 2θ or Q)
        y = experiment.datastore.pattern.meas  # Measured diffraction data
        dy = experiment.datastore.pattern.meas_su  # Measurement uncertainty (standard deviation)

        # Debug print for x, y, dy values
        print(f"🔧 [DEBUG] x: {x[:5]}... y: {y[:5]}... dy: {dy[:5]}...")  # Show first 5 values for debugging

        # Create the bumps model
        bumps_model = self._create_bumps_model(parameters, sample_models, experiments, calculator)
        print("🔧 [DEBUG] Bumps model created")

        # Wrap the bumps model in a fitness object
        self.fitness = BumpsModel(bumps_model, x, y, dy, engine_parameters)  # Pass parameters to the BumpsModel

        # Create the fit problem and execute the fitting
        problem = FitProblem(self.fitness)
        print(f"🔧 [DEBUG] FitProblem initialized")

        # Debugging FitProblem details
        print(f"🔧 [DEBUG] FitProblem details: {problem}")

        # Check attributes of FitProblem object to ensure it's correct
        print(f"🔧 [DEBUG] FitProblem type: {type(problem)}")
        print(f"🔧 [DEBUG] Problem parameters: {problem._parameters}")

        #tol = 1e-1
        #method_dict = {'method': self.method, 'xtol': tol, 'ftol': tol}
        method_dict = {'method': self.method}

        #from bumps.fitters import FitDriver

        #driver = FitDriver(problem, method=self.method, xtol=tol, ftol=tol)

        # After fitting is complete, inside BumpsMinimizer.fit():
        try:
            print(f"🔧 [DEBUG] Calling bumps_fit with method {self.method}")
            fit_result = bumps_fit(problem, **method_dict)
            #fit_result = driver.fit()

            print("✅ [DEBUG] Bumps fitting completed")

            # ✅ Compute redchi manually
            residuals = problem.residuals()
            dof = problem.dof
            redchi = np.sum(residuals ** 2) / dof
            print(f"🔧 [DEBUG] Computed redchi: {redchi}")

            # ✅ Attach redchi to result for consistency
            fit_result.redchi = redchi

        except Exception as e:
            print(f"⚠️ [DEBUG] Error during bumps_fit: {e}")
            return None

        self.result = fit_result
        return self.result

    def results(self):
        return self.result

    def display_results(self, result=None):
        result = result or self.result
        print(f"🔧 [DEBUG] Displaying results of type: {type(result)}")

        if result:
            # Show reduced chi-square if present
            redchi = getattr(result, "redchi", None)
            if redchi is not None:
                print(f"Reduced Chi-square: {redchi:.4f}")

            # Extract parameters and errors from bumps result
            if hasattr(result, 'x') and hasattr(result, 'dx'):
                print("\nRefined Parameters:")
                print("+--------------------+--------------+-------------+")
                print("| Parameter          | Value        | Error       |")
                print("+--------------------+--------------+-------------+")
                for idx, param in enumerate(self.fitness.parameters()):
                    param_name = param.name
                    param_value = result.x[idx]
                    param_error = result.dx[idx] if hasattr(result, 'dx') else None
                    print(f"🔧 [DEBUG] Parameter '{param_name}' refined value: {param_value}, error: {param_error}")
                    print(
                        f"| {param_name:<18} | {param_value:<12.6g} | {param_error if param_error is not None else 'N/A':<11} |")
                print("+--------------------+--------------+-------------+")
            else:
                print("✅ Refined parameters successfully retrieved and displayed above.")

        else:
            print("⚠️ [DEBUG] No fitting results available.")

    def _prepare_parameters(self, input_parameters):
        engine_parameters = []
        parinfo = []

        for param in input_parameters:
            print(f"🔧 [DEBUG] Preparing parameter: {param.id} with value: {param.value}")

            # Ensure the name is a string
            bumps_param = BumpsParameter(
                name=str(param.id),  # Ensure it's a string
                value=param.value,
                min=param.min if param.min is not None else -np.inf,
                max = param.max if param.max is not None else np.inf,
                fixed=not param.free,
                vary=param.free  # Set vary based on 'free'
                #scale = 0.01  # Try different values like 0.1, 10.0
            )

            engine_parameters.append(bumps_param)
            parinfo.append({
                'value': bumps_param.value,
                'min': bumps_param.min,
                'max': bumps_param.max,
                'vary': bumps_param.vary
            })

        print(f"🔧 [DEBUG] Engine parameters structure: {engine_parameters}")
        print(f"🔧 [DEBUG] Parinfo structure: {parinfo}")

        if not engine_parameters or not parinfo:
            raise ValueError("No valid parameters found for the fit.")

        print(f"🔧 [DEBUG] Final prepared {len(engine_parameters)} engine parameters")
        return engine_parameters, parinfo

    def _create_bumps_model(self, parameters, sample_models, experiments, calculator):
        def bumps_model(params):
            print(f"🔧 [DEBUG] Inside bumps_model with params: {params}")
            residuals = self._objective_function(params, parameters, sample_models, experiments, calculator)
            return residuals

        return bumps_model

    def _objective_function(self, engine_params, parameters, sample_models, experiments, calculator):
        print(f"🔧 [DEBUG] Calling _sync_parameters with engine_params: {engine_params}")
        BumpsMinimizer._sync_parameters(engine_params, parameters)

        residuals = []
        for expt_id, experiment in experiments._items.items():
            y_calc = calculator.calculate_pattern(sample_models, experiment)
            y_meas = experiment.datastore.pattern.meas
            y_meas_su = experiment.datastore.pattern.meas_su
            diff = (y_meas - y_calc) / y_meas_su
            residuals.extend(diff)

        residuals = np.array(residuals)

        print(f"🔧 [DEBUG] Residuals calculated: {residuals[:5]} ...")
        print(f"🔧 [DEBUG] Objective function residual sum of squares: {np.sum(residuals ** 2)}")
        return residuals

    @staticmethod
    def _sync_parameters(engine_params, parameters):
        print(f"🔧 [DEBUG] Syncing parameters with engine_params: {engine_params}")
        # engine_params is a list of floats representing parameter values
        for idx, param in enumerate(parameters):
            new_value = engine_params[idx]
            print(f"🔧 [DEBUG] Updating parameter '{param.id}' from {param.value} to {new_value}")
            param.value = new_value

# Wrapper class that includes 'parameters()' method
class BumpsModel:
    def __init__(self, model_function, x, y, weights, parameters):
        self.model_function = model_function
        self.x = x
        self.y = y
        self.dy = weights
        self._parameters = parameters  # ← list of BumpsParameter instances
        print(f"🔧 [DEBUG] BumpsModel initialized with {len(parameters)} parameters.")

    def parameters(self):
        print(f"🔧 [DEBUG] Returning {len(self._parameters)} parameters from BumpsModel.parameters()")
        return self._parameters  # ← return BumpsParameter instances, not names!

    def numpoints(self):
        num_points = len(self.y)
        print(f"🔧 [DEBUG] Returning number of points: {num_points}")
        return num_points

    def residuals(self):
        print(f"🔧 [DEBUG] Calling residuals() in BumpsModel...")
        params = [p.value for p in self._parameters]
        print(f"🔧 [DEBUG] Current parameter values in residuals(): {params}")
        res = self.model_function(params)
        print(f"🔧 [DEBUG] Residuals returned from model_function: {res[:5]} ...")  # Show first few residuals
        return res