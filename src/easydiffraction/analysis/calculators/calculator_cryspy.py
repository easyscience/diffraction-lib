try:
    import cryspy
    from cryspy.procedure_rhochi.rhochi_by_dictionary import rhochi_calc_chi_sq_by_dictionary
    from cryspy.H_functions_global.function_1_cryspy_objects import str_to_globaln
except ImportError:
    print('Warning: cryspy module not found. This calculator will not work.')

from .base import CalculatorBase  # Assuming you have a base interface


class CryspyCalculator(CalculatorBase):
    """
    Cryspy-based diffraction calculator.
    Converts EasyDiffraction models into Cryspy objects and computes patterns.
    """

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
        instr_setup = getattr(experiment, "instr_setup", None)
        instr_calib = getattr(experiment, "instr_calib", None)
        peak_broad = getattr(experiment, "peak_broad", None)
        peak_asymm = getattr(experiment, "peak_asymm", None)

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

        # Force single linked phase to be used, as we handle multiple phases
        # with their scales independently of the calculation engines
        cif_lines.append("\nloop_")
        cif_lines.append("  _phase_label")
        cif_lines.append("  _phase_scale")
        cif_lines.append(f"  {linked_phase.id}   1.0")

        # Force background to be zero, as we handle it independently of the
        # calculation engines
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
