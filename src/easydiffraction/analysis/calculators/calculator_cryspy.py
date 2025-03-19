try:
    import cryspy
    from cryspy.procedure_rhochi.rhochi_by_dictionary import rhochi_calc_chi_sq_by_dictionary
    from cryspy.H_functions_global.function_1_cryspy_objects import str_to_globaln
except ImportError:
    cryspy = None
    print('[CryspyCalculator] Warning: Cryspy module not found. This calculator will not work.')

from .base import CalculatorBase  # Assuming you have a base interface


class CryspyCalculator(CalculatorBase):
    """
    Cryspy-based diffraction calculator.
    Converts EasyDiffraction models into Cryspy objects and computes patterns.
    """

    def __init__(self):
        if cryspy is None:
            raise ImportError('Cryspy module is required for CryspyCalculator.')

        self._cryspy_obj = str_to_globaln('')
        self._cryspy_dict = {}  # Input dictionary for Cryspy
        self._cryspy_in_out_dict = {}
        self._cryspy_flag_use_precalculated_data = False
        self._cryspy_flag_calc_analytical_derivatives = False

    @property
    def name(self):
        return "cryspy"

    def calculate_hkl(self, sample_models, experiments):
        raise NotImplementedError("HKL calculation is not implemented for CryspyCalculator.")

    def calculate_pattern(self, sample_models, experiment):
        self._cryspy_obj = str_to_globaln('')

        cryspy_sample_models_cif = self._convert_sample_models_to_cif(sample_models)
        cryspy_sample_models_obj = str_to_globaln(cryspy_sample_models_cif)
        self._cryspy_obj.add_items(cryspy_sample_models_obj.items)

        cryspy_experiment_cif = self._convert_experiment_to_cif(experiment)
        cryspy_experiment_obj = str_to_globaln(cryspy_experiment_cif)
        self._cryspy_obj.add_items(cryspy_experiment_obj.items)

        self._cryspy_dict = self._cryspy_obj.get_dictionary()

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
            cif_lines.append(f"  {model_id}   1.0")

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