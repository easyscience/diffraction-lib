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
        cryspy_experiment_cif = self._convert_experiment_to_cif(experiment, linked_phase=sample_model)
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

        # Extract calculated pattern from cryspy_in_out_dict
        cryspy_block_name = f"pd_{experiment.id}"
        try:
            signal_plus = cryspy_in_out_dict[cryspy_block_name]['signal_plus']
            signal_minus = cryspy_in_out_dict[cryspy_block_name]['signal_minus']
            y_calc_total = signal_plus + signal_minus
        except KeyError:
            print(f"[CryspyCalculator] Error: No calculated data for {cryspy_block_name}")
            y_calc_total = []

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
            cif_lines.append(f"_setup_wavelength {instrument.setup_wavelength.value}")
            cif_lines.append(f"_setup_offset_2theta {instrument.calib_twotheta_offset.value}")

        # Peak category
        if peak:
            cif_lines.append(f"_pd_instr_resolution_U {peak.broad_gauss_u.value}")
            cif_lines.append(f"_pd_instr_resolution_V {peak.broad_gauss_v.value}")
            cif_lines.append(f"_pd_instr_resolution_W {peak.broad_gauss_w.value}")
            cif_lines.append(f"_pd_instr_resolution_X {peak.broad_lorentz_x.value}")
            cif_lines.append(f"_pd_instr_resolution_Y {peak.broad_lorentz_y.value}")

        # Linked phases category
        # Force single linked phase to be used, as we handle multiple phases
        # with their scales independently of the calculation engines
        cif_lines.append("loop_")
        cif_lines.append("_phase_label")
        cif_lines.append("_phase_scale")
        cif_lines.append(f"{linked_phase.model_id} 1.0")

        # Extract measurement range dynamically
        x_data = experiment.datastore.pattern.x
        two_theta_min = float(x_data.min())
        two_theta_max = float(x_data.max())

        cif_lines.append(f"_range_2theta_min {two_theta_min}")
        cif_lines.append(f"_range_2theta_max {two_theta_max}\n")

        # Background category
        # Force background to be zero, as we handle it independently of the
        # calculation engines
        cif_lines.append("loop_")
        cif_lines.append("_pd_background_2theta")
        cif_lines.append("_pd_background_intensity")
        cif_lines.append(f"{two_theta_min} 0.0")
        cif_lines.append(f"{two_theta_max} 0.0")

        # Measured data category
        cif_lines.append("loop_")
        cif_lines.append("_pd_meas_2theta")
        cif_lines.append("_pd_meas_intensity")
        cif_lines.append("_pd_meas_intensity_sigma")

        y_data = experiment.datastore.pattern.meas
        sy_data = experiment.datastore.pattern.meas_su
        for x_val, y_val, sy_val in zip(x_data, y_data, sy_data):
            cif_lines.append(f"  {x_val:.5f}   {y_val:.5f}   {sy_val:.5f}")

        # Combine all lines into a single string
        cryspy_experiment_cif = "\n".join(cif_lines)

        return cryspy_experiment_cif
