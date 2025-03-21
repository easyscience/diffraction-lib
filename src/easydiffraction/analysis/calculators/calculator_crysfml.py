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

    def calculate_hkl(self, sample_models, experiments):
        # Call Crysfml to calculate structure factors
        raise NotImplementedError("HKL calculation is not implemented for CryspyCalculator.")

    def calculate_pattern(self, sample_models, experiments):
        # Call Crysfml to calculate diffraction pattern
        crysfml_dict = self._crysfml_dict(sample_models, experiments)
        #import json
        #print(json.dumps(crysfml_dict, indent=4))
        #exit()

        _, y = cfml_py_utilities.cw_powder_pattern_from_dict(crysfml_dict)
        y = y[:-1] # Remove the last point (it's a duplicate)

        scale = 1.4602
        y = y * scale

        return y

    def _crysfml_dict(self, sample_models, experiment):
        phases = self._convert_sample_models_to_dict(sample_models)
        experiments_list = []
        experiments_list.append(self._convert_experiment_to_dict(experiment))
        return {
            "phases": phases,
            "experiments": experiments_list
        }

    def _convert_sample_models_to_dict(self, sample_models):
        phases = []
        for model_id, model in sample_models._models.items():
            phase_dict = {
                model_id: {
                    "_space_group_name_H-M_alt": model.space_group.name,
                    "_cell_length_a": model.cell.length_a.value,
                    "_cell_length_b": model.cell.length_b.value,
                    "_cell_length_c": model.cell.length_c.value,
                    "_cell_angle_alpha": model.cell.angle_alpha.value,
                    "_cell_angle_beta": model.cell.angle_beta.value,
                    "_cell_angle_gamma": model.cell.angle_gamma.value,
                    "_atom_site": []
                }
            }

            for atom in model.atom_sites:
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
                phase_dict[model_id]["_atom_site"].append(atom_site)

            phases.append(phase_dict)

        return phases

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