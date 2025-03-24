try:
    import cryspy
    from cryspy.procedure_rhochi.rhochi_by_dictionary import rhochi_calc_chi_sq_by_dictionary
    from cryspy.H_functions_global.function_1_cryspy_objects import str_to_globaln
except ImportError:
    cryspy = None
    print('Warning: cryspy module not found. This calculator will not work.')

from .base import CalculatorBase  # Assuming you have a base interface


class CryspyCalculator(CalculatorBase):
    """
    Cryspy-based diffraction calculator.
    Converts EasyDiffraction models into Cryspy objects and computes patterns.
    """

    def __init__(self):
        if cryspy is None:
            raise ImportError('cryspy module is required for CryspyCalculator.')

        self._cryspy_obj = str_to_globaln('')
        self._cryspy_dict = {}  # Input dictionary for Cryspy
        self._cryspy_in_out_dict = {}
        self._cryspy_flag_use_precalculated_data = False
        self._cryspy_flag_calc_analytical_derivatives = False

    @property
    def name(self):
        return "cryspy"

    def calculate_structure_factors(self, sample_models, experiments):
        raise NotImplementedError("HKL calculation is not implemented for CryspyCalculator.")

    def calculate_pattern(self, sample_models, experiment):
        self._cryspy_obj = str_to_globaln('')

        # TODO: Temporary workaround to avoid re-creating the cryspy object every time!
        # Speed up the calculation 10 times!

        if not self._cryspy_dict:
            cryspy_sample_models_cif = self._convert_sample_models_to_cif(sample_models)
            cryspy_sample_models_obj = str_to_globaln(cryspy_sample_models_cif)
            self._cryspy_obj.add_items(cryspy_sample_models_obj.items)

            cryspy_experiment_cif = self._convert_experiment_to_cif(experiment)
            cryspy_experiment_obj = str_to_globaln(cryspy_experiment_cif)
            self._cryspy_obj.add_items(cryspy_experiment_obj.items)

            self._cryspy_dict = self._cryspy_obj.get_dictionary()

        else:
            cell = self._cryspy_dict['crystal_pbso4']['unit_cell_parameters']
            cell[0] = sample_models['pbso4'].cell.length_a.value
            cell[1] = sample_models['pbso4'].cell.length_b.value
            cell[2] = sample_models['pbso4'].cell.length_c.value

        calc_result = rhochi_calc_chi_sq_by_dictionary(
            self._cryspy_dict,
            dict_in_out=self._cryspy_in_out_dict,
            flag_use_precalculated_data=self._cryspy_flag_use_precalculated_data,
            flag_calc_analytical_derivatives=self._cryspy_flag_calc_analytical_derivatives
        )

        cryspy_block_name = f"pd_{experiment.id}"
        try:
            signal_plus = self._cryspy_in_out_dict[cryspy_block_name]['signal_plus']
            signal_minus = self._cryspy_in_out_dict[cryspy_block_name]['signal_minus']
            y_calc_total = signal_plus + signal_minus
        except KeyError:
            print(f"[CryspyCalculator] Error: No calculated data for {cryspy_block_name}")
            y_calc_total = []

        return y_calc_total

    def _calculate_single_model_pattern(self, sample_model, experiment):
        # TODO: Implement this method as in CrysfmlCalculator
        pass

    def _convert_sample_models_to_dict(self, sample_models):
        phases = []
        for model_id, model in sample_models._models.items():
            phase_dict = {
                model_id: {
                    "_space_group_name_H-M_alt": model.symmetry.space_group_name,
                    "_cell_length_a": model.cell.length_a.value,
                    "_cell_length_b": model.cell.length_b.value,
                    "_cell_length_c": model.cell.length_c.value,
                    "_cell_angle_alpha": model.cell.angle_alpha.value,
                    "_cell_angle_beta": model.cell.angle_beta.value,
                    "_cell_angle_gamma": model.cell.angle_gamma.value,
                    "_atom_site": []
                }
            }

            for atom in model.atoms:
                atom_site = {
                    "_label": atom.label,
                    "_type_symbol": atom.type_symbol,
                    "_fract_x": atom.fract_x,
                    "_fract_y": atom.fract_y,
                    "_fract_z": atom.fract_z,
                    "_occupancy": atom.occupancy,
                    "_adp_type": "Biso",  # Assuming Biso for simplicity
                    "_B_iso_or_equiv": atom.b_iso
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

    def _convert_sample_models_to_cif(self, sample_models):
        cif_strings = []
        for model_id, model in sample_models._models.items():
            cif_string = model.as_cif()
            cif_strings.append(cif_string)
        return "\n".join(cif_strings)

    def _convert_experiment_to_cif(self, experiment):
        instr_setup = getattr(experiment, "instr_setup", None)
        instr_calib = getattr(experiment, "instr_calib", None)
        peak_broad = getattr(experiment, "peak_broad", None)
        peak_asymm = getattr(experiment, "peak_asymm", None)
        background = getattr(experiment, "background", None)

        cif_lines = []
        cif_lines.append(f"data_{experiment.id}\n")

        # Extract measurement range dynamically
        x_data = experiment.datastore.pattern.x
        two_theta_min = float(x_data.min())
        two_theta_max = float(x_data.max())
        cif_lines.append(f"_range_2theta_min   {two_theta_min}")
        cif_lines.append(f"_range_2theta_max   {two_theta_max}\n")

        if instr_setup:
            wavelength = instr_setup.wavelength.value
            cif_lines.append(f"_setup_wavelength   {wavelength}")

        if instr_calib:
            twotheta_offset = instr_calib.twotheta_offset.value
            cif_lines.append(f"_setup_offset_2theta   {twotheta_offset}")

        if peak_broad:
            cif_lines.append(f"_pd_instr_resolution_U   {peak_broad.gauss_u.value}")
            cif_lines.append(f"_pd_instr_resolution_V   {peak_broad.gauss_v.value}")
            cif_lines.append(f"_pd_instr_resolution_W   {peak_broad.gauss_w.value}")
            cif_lines.append(f"_pd_instr_resolution_X   {peak_broad.lorentz_x.value}")
            cif_lines.append(f"_pd_instr_resolution_Y   {peak_broad.lorentz_y.value}")

        cif_lines.append("\nloop_")
        cif_lines.append("  _phase_label")
        cif_lines.append("  _phase_scale")

        for model_id in self._get_phase_labels(experiment):
            cif_lines.append(f"  {model_id}   1.4602")  # TODO: Replace with actual scale

        cif_lines.append("\nloop_")
        cif_lines.append("  _pd_background_2theta")
        cif_lines.append("  _pd_background_intensity")
        cif_lines.append(f"  {two_theta_min}   0.0")
        cif_lines.append(f"  {two_theta_max}   0.0")

        cif_lines.append("\nloop_")
        cif_lines.append("  _pd_meas_2theta")
        cif_lines.append("  _pd_meas_intensity")
        cif_lines.append("  _pd_meas_intensity_sigma")

        y_data = experiment.datastore.pattern.meas
        sy_data = experiment.datastore.pattern.meas_su

        for x_val, y_val, sy_val in zip(x_data, y_data, sy_data):
            cif_lines.append(f"  {x_val:.5f}   {y_val:.5f}   {sy_val:.5f}")

        cryspy_experiment_cif = "\n".join(cif_lines)
        return cryspy_experiment_cif

    def _get_phase_labels(self, experiment):
        if hasattr(self, 'sample_models'):
            return [model.id for model in self.sample_models._models.values()]
        return ['pbso4']

    def set_sample_models(self, sample_models):
        self.sample_models = sample_models