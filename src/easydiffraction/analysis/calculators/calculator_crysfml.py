from .calculator_base import CalculatorBase
from easydiffraction.utils.formatting import warning

try:
    from pycrysfml import cfml_py_utilities
except ImportError:
    print(warning('"pycrysfml" module not found. This calculator will not work.'))
    cfml_py_utilities = None


class CrysfmlCalculator(CalculatorBase):
    """
    Wrapper for Crysfml library.
    """

    engine_imported = cfml_py_utilities is not None

    @property
    def name(self):
        return "crysfml"

    def calculate_structure_factors(self, sample_models, experiments):
        # Call Crysfml to calculate structure factors
        raise NotImplementedError("HKL calculation is not implemented for CryspyCalculator.")

    def _calculate_single_model_pattern(self,
                                        sample_model,
                                        experiment):
        """
        Calculates the diffraction pattern using Crysfml for the given sample model and experiment.
        """
        crysfml_dict = self._crysfml_dict(sample_model, experiment)
        try:
            _, y = cfml_py_utilities.cw_powder_pattern_from_dict(crysfml_dict)
            y = self._adjust_pattern_length(y, len(experiment.datastore.pattern.x))
        except KeyError:
            print(f"[CrysfmlCalculator] Error: No calculated data")
            y = []
        return y

    def _adjust_pattern_length(self, pattern, target_length):
        # TODO: Check the origin of this discrepancy coming from PyCrysFML
        if len(pattern) > target_length:
            return pattern[:target_length]
        return pattern

    def _crysfml_dict(self, sample_model, experiment):
        sample_model_dict = self._convert_sample_model_to_dict(sample_model)
        experiment_dict = self._convert_experiment_to_dict(experiment)
        return {
            "phases": [sample_model_dict],
            "experiments": [experiment_dict]
        }

    def _convert_sample_model_to_dict(self, sample_model):
        sample_model_dict = {
            sample_model.model_id: {
                "_space_group_name_H-M_alt": sample_model.space_group.name.value,
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
            sample_model_dict[sample_model.model_id]["_atom_site"].append(atom_site)

        return sample_model_dict

    def _convert_experiment_to_dict(self, experiment):
        expt_type = getattr(experiment, "type", None)
        instrument = getattr(experiment, "instrument", None)
        peak = getattr(experiment, "peak", None)

        x_data = experiment.datastore.pattern.x
        two_theta_min = float(x_data.min())
        two_theta_max = float(x_data.max())

        exp_dict = {
            "NPD": {
                "_diffrn_radiation_probe": expt_type.radiation_probe.value if expt_type else "neutron",
                "_diffrn_radiation_wavelength": instrument.setup_wavelength.value if instrument else 1.0,
                "_pd_instr_resolution_u": peak.broad_gauss_u.value if peak else 0.0,
                "_pd_instr_resolution_v": peak.broad_gauss_v.value if peak else 0.0,
                "_pd_instr_resolution_w": peak.broad_gauss_w.value if peak else 0.0,
                "_pd_instr_resolution_x": peak.broad_lorentz_x.value if peak else 0.0,
                "_pd_instr_resolution_y": peak.broad_lorentz_y.value if peak else 0.0,
                #"_pd_instr_reflex_s_l": peak_asymm.s_l.value if peak_asymm else 0.0,
                #"_pd_instr_reflex_d_l": peak_asymm.d_l.value if peak_asymm else 0.0,
                "_pd_meas_2theta_offset": instrument.calib_twotheta_offset.value if instrument else 0.0,
                "_pd_meas_2theta_range_min": two_theta_min,
                "_pd_meas_2theta_range_max": two_theta_max,
                "_pd_meas_2theta_range_inc": (two_theta_max - two_theta_min) / len(x_data)
            }
        }

        return exp_dict
