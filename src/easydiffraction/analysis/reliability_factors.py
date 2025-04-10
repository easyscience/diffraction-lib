import numpy as np


def calculate_r_factor(y_obs, y_calc):
    y_obs = np.asarray(y_obs)
    y_calc = np.asarray(y_calc)
    numerator = np.sum(np.abs(y_obs - y_calc))
    denominator = np.sum(np.abs(y_obs))
    return numerator / denominator if denominator != 0 else np.nan

def calculate_weighted_r_factor(y_obs, y_calc, weights):
    y_obs = np.asarray(y_obs)
    y_calc = np.asarray(y_calc)
    weights = np.asarray(weights)
    numerator = np.sum(weights * (y_obs - y_calc) ** 2)
    denominator = np.sum(weights * y_obs ** 2)
    return np.sqrt(numerator / denominator) if denominator != 0 else np.nan

def calculate_rb_factor(y_obs, y_calc):
    y_obs = np.asarray(y_obs)
    y_calc = np.asarray(y_calc)
    numerator = np.sum(np.abs(y_obs - y_calc))
    denominator = np.sum(y_obs)
    return numerator / denominator if denominator != 0 else np.nan

def calculate_r_factor_squared(y_obs, y_calc):
    y_obs = np.asarray(y_obs)
    y_calc = np.asarray(y_calc)
    numerator = np.sum((y_obs - y_calc) ** 2)
    denominator = np.sum(y_obs ** 2)
    return np.sqrt(numerator / denominator) if denominator != 0 else np.nan

def calculate_reduced_chi_square(residuals, num_parameters):
    residuals = np.asarray(residuals)
    chi_square = np.sum(residuals ** 2)
    n_points = len(residuals)
    dof = n_points - num_parameters
    if dof > 0:
        return chi_square / dof
    else:
        return np.nan

def get_reliability_inputs(sample_models, experiments, calculator):
    y_obs_all = []
    y_calc_all = []
    y_err_all = []
    for expt_name, experiment in experiments._items.items():
        y_calc = calculator.calculate_pattern(sample_models, experiment)
        y_meas = experiment.datastore.pattern.meas
        y_meas_su = experiment.datastore.pattern.meas_su

        if y_meas is not None and y_calc is not None:
            y_obs_all.extend(y_meas)
            y_calc_all.extend(y_calc)
            y_err_all.extend(y_meas_su if y_meas_su is not None else np.ones_like(y_meas))

    return (
        np.array(y_obs_all),
        np.array(y_calc_all),
        np.array(y_err_all) if y_err_all else None
    )