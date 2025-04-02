from .calculator_base import CalculatorBase  # Assuming you have a base interface
from easydiffraction.utils.formatting import warning

try:
    import cryspy
    from cryspy.procedure_rhochi.rhochi_by_dictionary import rhochi_calc_chi_sq_by_dictionary
    from cryspy.H_functions_global.function_1_cryspy_objects import str_to_globaln
except ImportError:
    print(warning("'cryspy' module not found. This calculator will not work."))
    cryspy = None


class CryspyCalculator(CalculatorBase):
    """
    Cryspy-based diffraction calculator.
    Converts EasyDiffraction models into Cryspy objects and computes patterns.
    """

    engine_imported = cryspy is not None

    @property
    def name(self):
        return "cryspy"

    def calculate_structure_factors(self, sample_models, experiments):
        raise NotImplementedError("HKL calculation is not implemented for CryspyCalculator.")

    def _calculate_single_model_pattern(self, sample_model, experiment):
        cryspy_obj = str_to_globaln('')

        # Add single sample model to cryspy_obj
        cryspy_sample_model_cif = self._convert_sample_model_to_cif(sample_model)
        cryspy_sample_model_obj = str_to_globaln(cryspy_sample_model_cif)
        cryspy_obj.add_items(cryspy_sample_model_obj.items)

        # Add single experiment to cryspy_obj
        cryspy_experiment_cif = self._convert_experiment_to_cif(experiment,
                                                                linked_phase=sample_model)
        cryspy_experiment_obj = str_to_globaln(cryspy_experiment_cif)
        cryspy_obj.add_items(cryspy_experiment_obj.items)

        # Get cryspy_dict from cryspy_obj
        cryspy_dict = cryspy_obj.get_dictionary()

        # TODO: We need to avoid re-creating the cryspy object every time.
        # Instead, we should update the cryspy_dict with the new sample model
        # and experiment. Expected to speed up the calculation 10 times!

        # Calculate pattern using cryspy
        cryspy_in_out_dict = {}
        calc_result = rhochi_calc_chi_sq_by_dictionary(
            cryspy_dict,
            dict_in_out=cryspy_in_out_dict,
            flag_use_precalculated_data=False,
            flag_calc_analytical_derivatives=False
        )

        # Get cryspy block name based on experiment type
        if experiment.type.beam_mode.value == "constant wavelength":
            cryspy_block_name = f"pd_{experiment.id}"
        elif experiment.type.beam_mode.value == "time-of-flight":
            cryspy_block_name = f"tof_{experiment.id}"
        else:
            print(f"[CryspyCalculator] Error: Unknown beam mode {experiment.type.beam_mode.value}")
            return []

        # Extract calculated pattern from cryspy_in_out_dict
        try:
            signal_plus = cryspy_in_out_dict[cryspy_block_name]['signal_plus']
            signal_minus = cryspy_in_out_dict[cryspy_block_name]['signal_minus']
            y_calc_total = signal_plus + signal_minus
        except KeyError:
            print(f"[CryspyCalculator] Error: No calculated data for {cryspy_block_name}")
            return []

        return y_calc_total

    def _convert_sample_model_to_cif(self, sample_model):
        return sample_model.as_cif()

    def _convert_experiment_to_cif(self, experiment, linked_phase):
        expt_type = getattr(experiment, "type", None)
        instrument = getattr(experiment, "instrument", None)
        peak = getattr(experiment, "peak", None)

        cif_lines = [f"data_{experiment.id}"]

        # Experiment type category
        if expt_type is not None:
            radiation_probe = expt_type.radiation_probe.value
            radiation_probe = radiation_probe.replace("neutron", "neutrons")
            radiation_probe = radiation_probe.replace("xray", "X-rays")
            cif_lines.append(f"_setup_radiation {radiation_probe}")

        # Instrument category
        if instrument:
            instrument_mapping = {
                # Constant wavelength
                "setup_wavelength": "_setup_wavelength",
                "calib_twotheta_offset": "_setup_offset_2theta",
                # Time-of-flight
                "setup_twotheta_bank": "_tof_parameters_2theta_bank",
                "calib_d_to_tof_offset": "_tof_parameters_Zero",
                "calib_d_to_tof_linear": "_tof_parameters_Dtt1",
                "calib_d_to_tof_quad": "_tof_parameters_dtt2",
            }
            for local_attr_name, engine_key_name in instrument_mapping.items():
                if hasattr(instrument, local_attr_name):
                    attr_value = getattr(instrument, local_attr_name).value
                    cif_lines.append(f"{engine_key_name} {attr_value}")

        # Peak category
        if peak:
            peak_mapping = {
                # Constant wavelength
                "broad_gauss_u": "_pd_instr_resolution_U",
                "broad_gauss_v": "_pd_instr_resolution_V",
                "broad_gauss_w": "_pd_instr_resolution_W",
                "broad_lorentz_x": "_pd_instr_resolution_X",
                "broad_lorentz_y": "_pd_instr_resolution_Y",
                # Time-of-flight
                "broad_gauss_sigma_0": "_tof_profile_sigma0",
                "broad_gauss_sigma_1": "_tof_profile_sigma1",
                "broad_gauss_sigma_2": "_tof_profile_sigma2",
                "broad_mix_beta_0": "_tof_profile_beta0",
                "broad_mix_beta_1": "_tof_profile_beta1",
                "asym_alpha_0": "_tof_profile_alpha0",
                "asym_alpha_1": "_tof_profile_alpha1",
            }
            if expt_type.beam_mode.value == "time-of-flight":
                cif_lines.append(f"_tof_profile_peak_shape Gauss")
            for local_attr_name, engine_key_name in peak_mapping.items():
                if hasattr(peak, local_attr_name):
                    attr_value = getattr(peak, local_attr_name).value
                    cif_lines.append(f"{engine_key_name} {attr_value}")

        # Linked phases category
        # Force single linked phase to be used, as we handle multiple phases
        # with their scales independently of the calculation engines
        cif_lines.append("loop_")
        cif_lines.append("_phase_label")
        cif_lines.append("_phase_scale")
        cif_lines.append(f"{linked_phase.model_id} 1.0")

        # Experiment range category
        # Extract measurement range dynamically
        x_data = experiment.datastore.pattern.x
        two_theta_min = float(x_data.min())
        two_theta_max = float(x_data.max())
        if expt_type.beam_mode.value == "constant wavelength":
            cif_lines.append(f"_range_2theta_min {two_theta_min}")
            cif_lines.append(f"_range_2theta_max {two_theta_max}")
        elif expt_type.beam_mode.value == "time-of-flight":
            cif_lines.append(f"_range_time_min {two_theta_min}")
            cif_lines.append(f"_range_time_max {two_theta_max}")

        # Background category
        # Force background to be zero, as we handle it independently of the
        # calculation engines
        if expt_type.beam_mode.value == "constant wavelength":
            cif_lines.append("loop_")
            cif_lines.append("_pd_background_2theta")
            cif_lines.append("_pd_background_intensity")
            cif_lines.append(f"{two_theta_min} 0.0")
            cif_lines.append(f"{two_theta_max} 0.0")
        elif expt_type.beam_mode.value == "time-of-flight":
            cif_lines.append("loop_")
            cif_lines.append("_tof_backgroundpoint_time")
            cif_lines.append("_tof_backgroundpoint_intensity")
            cif_lines.append(f"{two_theta_min} 0.0")
            cif_lines.append(f"{two_theta_max} 0.0")

        # Measured data category
        if expt_type.beam_mode.value == "constant wavelength":
            cif_lines.append("loop_")
            cif_lines.append("_pd_meas_2theta")
            cif_lines.append("_pd_meas_intensity")
            cif_lines.append("_pd_meas_intensity_sigma")
        elif expt_type.beam_mode.value == "time-of-flight":
            cif_lines.append("loop_")
            cif_lines.append("_tof_meas_time")
            cif_lines.append("_tof_meas_intensity")
            cif_lines.append("_tof_meas_intensity_sigma")

        y_data = experiment.datastore.pattern.meas
        sy_data = experiment.datastore.pattern.meas_su
        for x_val, y_val, sy_val in zip(x_data, y_data, sy_data):
            cif_lines.append(f"  {x_val:.5f}   {y_val:.5f}   {sy_val:.5f}")

        # Combine all lines into a single string
        cryspy_experiment_cif = "\n".join(cif_lines)

        return cryspy_experiment_cif
