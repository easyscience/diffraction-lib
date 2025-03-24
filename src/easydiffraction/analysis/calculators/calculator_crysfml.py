import numpy as np
from scipy.interpolate import interp1d

try:
    from pycrysfml import cfml_py_utilities
except ImportError:
    #pycrysfml = None
    print('Warning: pycrysfml module not found. This calculator will not work.')

from .base import CalculatorBase


class CrysfmlCalculator(CalculatorBase):
    """
    Adapter for Crysfml library.
    """

    #def __init__(self):
        #if pycrysfml is None:
        #    raise ImportError('pycrysfml module is required for CryspyCalculator.')

    @property
    def name(self):
        return "crysfml"

    def calculate_structure_factors(self, sample_models, experiments):
        # Call Crysfml to calculate structure factors
        raise NotImplementedError("HKL calculation is not implemented for CryspyCalculator.")

    def calculate_pattern(self, sample_models, experiment):
        """
        Calculates the diffraction pattern using Crysfml for the given sample models and experiment.
        """
        x_data = experiment.datastore.pattern.x
        y_calc_scaled = np.zeros_like(x_data)

        # Validate linked phases
        if not experiment.linked_phases:
            print('Warning: No linked phases found. Returning empty pattern.')
            return y_calc_scaled

        valid_linked_phases = []
        for linked_phase in experiment.linked_phases:
            if linked_phase.id.value not in sample_models.get_ids():
                print(f'Warning: Linked phase {linked_phase.id.value} not found in Sample Models {sample_models.get_ids()}')
                continue
            valid_linked_phases.append(linked_phase)

        if not valid_linked_phases:
            print('Warning: None of the linked phases found in Sample Models. Returning empty pattern.')
            return y_calc_scaled

        # Calculate contributions from valid linked sample models
        for linked_phase in valid_linked_phases:
            sample_model_id = linked_phase.id.value
            sample_model_scale = linked_phase.scale.value
            sample_model = sample_models[sample_model_id]

            crysfml_dict = self._crysfml_dict(sample_model, experiment)
            _, sample_model_y_calc = cfml_py_utilities.cw_powder_pattern_from_dict(crysfml_dict)

            # Match Crysfml output length with x_data if necessary
            # TODO: Find the reason for the mismatch from Crysfml!
            if len(sample_model_y_calc) > len(x_data):
                sample_model_y_calc = sample_model_y_calc[:len(x_data)]
            elif len(sample_model_y_calc) < len(x_data):
                padding = len(x_data) - len(sample_model_y_calc)
                sample_model_y_calc = np.pad(sample_model_y_calc, (0, padding), 'constant')

            sample_model_y_calc_scaled = sample_model_scale * sample_model_y_calc
            y_calc_scaled += sample_model_y_calc_scaled

        # Calculate background
        if experiment.background.points:
            background_points = np.array(experiment.background.points)
            bg_x, bg_y = background_points[:, 0], background_points[:, 1]

            interp_func = interp1d(
                bg_x, bg_y,
                kind='linear',
                bounds_error=False,
                fill_value=(bg_y[0], bg_y[-1])
            )
            y_bkg = interp_func(x_data)
        else:
            print('Warning: No background points found. Setting background to zero.')
            y_bkg = np.zeros_like(x_data)

        experiment.datastore.pattern.bkg = y_bkg

        y_calc_total = y_calc_scaled + y_bkg

        experiment.datastore.pattern.calc = y_calc_total

        return y_calc_total

    def _crysfml_dict(self, sample_model, experiment):
        sample_model_dict = self._convert_sample_model_to_dict(sample_model)
        experiment_dict = self._convert_experiment_to_dict(experiment)
        return {
            "phases": [sample_model_dict],
            "experiments": [experiment_dict]
        }

    def _convert_sample_model_to_dict(self, sample_model):
        sample_model_dict = {
            sample_model.id: {
                "_space_group_name_H-M_alt": sample_model.space_group.name,
                "_cell_length_a": sample_model.cell.length_a.value,
                "_cell_length_b": sample_model.cell.length_b.value,
                "_cell_length_c": sample_model.cell.length_c.value,
                "_cell_angle_alpha": sample_model.cell.angle_alpha.value,
                "_cell_angle_beta": sample_model.cell.angle_beta.value,
                "_cell_angle_gamma": sample_model.cell.angle_gamma.value,
                "_atom_site": []
            }
        }

        for atom in sample_model.atom_sites:
            atom_site = {
                "_label": atom.label.value,
                "_type_symbol": atom.type_symbol.value,
                "_fract_x": atom.fract_x.value,
                "_fract_y": atom.fract_y.value,
                "_fract_z": atom.fract_z.value,
                "_occupancy": atom.occupancy.value,
                "_adp_type": "Biso",  # Assuming Biso for simplicity
                "_B_iso_or_equiv": atom.b_iso.value
            }
            sample_model_dict[sample_model.id]["_atom_site"].append(atom_site)

        return sample_model_dict

    def _convert_experiment_to_dict(self, experiment):
        instr_setup = getattr(experiment, "instr_setup", None)
        instr_calib = getattr(experiment, "instr_calib", None)
        peak_broad = getattr(experiment, "peak_broad", None)
        peak_asymm = getattr(experiment, "peak_asymm", None)

        x_data = experiment.datastore.pattern.x
        two_theta_min = float(x_data.min())
        two_theta_max = float(x_data.max())

        exp_dict = {
            "NPD": {
                "_diffrn_radiation_probe": "neutron",
                "_diffrn_radiation_wavelength": instr_setup.wavelength.value if instr_setup else 1.0,
                "_pd_instr_resolution_u": peak_broad.gauss_u.value if peak_broad else 0.0,
                "_pd_instr_resolution_v": peak_broad.gauss_v.value if peak_broad else 0.0,
                "_pd_instr_resolution_w": peak_broad.gauss_w.value if peak_broad else 0.0,
                "_pd_instr_resolution_x": peak_broad.lorentz_x.value if peak_broad else 0.0,
                "_pd_instr_resolution_y": peak_broad.lorentz_y.value if peak_broad else 0.0,
                "_pd_instr_reflex_s_l": peak_asymm.s_l.value if peak_asymm else 0.0,
                "_pd_instr_reflex_d_l": peak_asymm.d_l.value if peak_asymm else 0.0,
                "_pd_meas_2theta_offset": instr_calib.twotheta_offset.value if instr_calib else 0.0,
                "_pd_meas_2theta_range_min": two_theta_min,
                "_pd_meas_2theta_range_max": two_theta_max,
                "_pd_meas_2theta_range_inc": (two_theta_max - two_theta_min) / len(x_data)
            }
        }

        return exp_dict
