import copy
import numpy as np
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

    def __init__(self):
        super().__init__()
        self._cryspy_dicts = {}

    def calculate_structure_factors(self, sample_models, experiments):
        raise NotImplementedError("HKL calculation is not implemented for CryspyCalculator.")

    def _calculate_single_model_pattern(self,
                                        sample_model,
                                        experiment):
        # TODO: We need to avoid re-creating the cryspy object every time.
        # Instead, we should update the cryspy_dict with the new sample model
        # and experiment. Expected to speed up the calculation 10 times!

        #_cryspy_expt_id = experiment.id
        #_is_cryspy_dict = bool(self._cryspy_dict)

        if self._cryspy_dicts and experiment.id in self._cryspy_dicts:
            cryspy_dict = self._recreate_cryspy_dict(sample_model, experiment)
        else:
            cryspy_obj = self._recreate_cryspy_obj(sample_model, experiment)
            cryspy_dict = cryspy_obj.get_dictionary()

        self._cryspy_dicts[experiment.id] = copy.deepcopy(cryspy_dict)

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

    def _recreate_cryspy_dict(self, sample_model, experiment):
        cryspy_dict = copy.deepcopy(self._cryspy_dicts[experiment.id])

        # ---------- Update sample model parameters ----------

        cryspy_model_id = f'crystal_{sample_model.model_id}'
        cryspy_model_dict = cryspy_dict[cryspy_model_id]

        # Apply symmetry constraints
        sample_model.apply_symmetry_constraints()

        # Cell
        cryspy_cell = cryspy_model_dict['unit_cell_parameters']
        cryspy_cell[0] = sample_model.cell.length_a.value
        cryspy_cell[1] = sample_model.cell.length_b.value
        cryspy_cell[2] = sample_model.cell.length_c.value
        cryspy_cell[3] = np.deg2rad(sample_model.cell.angle_alpha.value)
        cryspy_cell[4] = np.deg2rad(sample_model.cell.angle_beta.value)
        cryspy_cell[5] = np.deg2rad(sample_model.cell.angle_gamma.value)

        # Atomic coordinates
        cryspy_xyz = cryspy_model_dict['atom_fract_xyz']
        for idx, atom_site in enumerate(sample_model.atom_sites):
            cryspy_xyz[0][idx] = atom_site.fract_x.value
            cryspy_xyz[1][idx] = atom_site.fract_y.value
            cryspy_xyz[2][idx] = atom_site.fract_z.value

        # Atomic occupancies
        cryspy_occ =cryspy_model_dict['atom_occupancy']
        for idx, atom_site in enumerate(sample_model.atom_sites):
            cryspy_occ[idx] = atom_site.occupancy.value

        # Atomic ADPs - Biso only for now
        cryspy_biso = cryspy_model_dict['atom_b_iso']
        for idx, atom_site in enumerate(sample_model.atom_sites):
            cryspy_biso[idx] = atom_site.b_iso.value

        # ---------- Update experiment parameters ----------

        if experiment.type.beam_mode.value == 'constant wavelength':
            cryspy_expt_id = f'pd_{experiment.id}'  # TODO: use expt_id as in the SampleModel? Or change there for id instead of model_id?
            cryspy_expt_dict = cryspy_dict[cryspy_expt_id]

            # Instrument
            cryspy_expt_dict['offset_ttheta'][0] = np.deg2rad(experiment.instrument.calib_twotheta_offset.value)
            cryspy_expt_dict['wavelength'][0] = experiment.instrument.setup_wavelength.value

            # Peak
            cryspy_resolution = cryspy_expt_dict['resolution_parameters']
            cryspy_resolution[0] = experiment.peak.broad_gauss_u.value
            cryspy_resolution[1] = experiment.peak.broad_gauss_v.value
            cryspy_resolution[2] = experiment.peak.broad_gauss_w.value
            cryspy_resolution[3] = experiment.peak.broad_lorentz_x.value
            cryspy_resolution[4] = experiment.peak.broad_lorentz_y.value

        elif experiment.type.beam_mode.value == 'time-of-flight':
            cryspy_expt_id = f'tof_{experiment.id}'  # TODO: use expt_id as in the SampleModel? Or change there for id instead of model_id?
            cryspy_expt_dict = cryspy_dict[cryspy_expt_id]

            # Instrument
            cryspy_expt_dict['zero'][0] = experiment.instrument.calib_d_to_tof_offset.value
            cryspy_expt_dict['dtt1'][0] = experiment.instrument.calib_d_to_tof_linear.value
            cryspy_expt_dict['dtt2'][0] = experiment.instrument.calib_d_to_tof_quad.value
            cryspy_expt_dict['ttheta_bank'] = np.deg2rad(experiment.instrument.setup_twotheta_bank.value)

            # Peak
            cryspy_sigma = cryspy_expt_dict['profile_sigmas']
            cryspy_sigma[0] = experiment.peak.broad_gauss_sigma_0.value
            cryspy_sigma[1] = experiment.peak.broad_gauss_sigma_1.value
            cryspy_sigma[2] = experiment.peak.broad_gauss_sigma_2.value

            cryspy_beta = cryspy_expt_dict['profile_betas']
            cryspy_beta[0] = experiment.peak.broad_mix_beta_0.value
            cryspy_beta[1] = experiment.peak.broad_mix_beta_1.value

            cryspy_alpha = cryspy_expt_dict['profile_alphas']
            cryspy_alpha[0] = experiment.peak.asym_alpha_0.value
            cryspy_alpha[1] = experiment.peak.asym_alpha_1.value

        return cryspy_dict


    def _recreate_cryspy_obj(self, sample_model, experiment):
        cryspy_obj = str_to_globaln('')

        # Add single sample model to cryspy_obj
        cryspy_sample_model_cif = self._convert_sample_model_to_cryspy_cif(sample_model)
        cryspy_sample_model_obj = str_to_globaln(cryspy_sample_model_cif)
        cryspy_obj.add_items(cryspy_sample_model_obj.items)

        # Add single experiment to cryspy_obj
        cryspy_experiment_cif = self._convert_experiment_to_cryspy_cif(experiment,
                                                                       linked_phase=sample_model)
        cryspy_experiment_obj = str_to_globaln(cryspy_experiment_cif)
        cryspy_obj.add_items(cryspy_experiment_obj.items)

        return cryspy_obj

    def _convert_sample_model_to_cryspy_cif(self, sample_model):
        return sample_model.as_cif()

    def _convert_experiment_to_cryspy_cif(self, experiment, linked_phase):
        expt_type = getattr(experiment, "type", None)
        instrument = getattr(experiment, "instrument", None)
        peak = getattr(experiment, "peak", None)

        cif_lines = [f"data_{experiment.id}"]

        # STANDARD CATEGORIES

        # Experiment type category
        if expt_type is not None:
            cif_lines.append("")
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
            cif_lines.append("")
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
            cif_lines.append("")
            if expt_type.beam_mode.value == "time-of-flight":
                cif_lines.append(f"_tof_profile_peak_shape Gauss")
            for local_attr_name, engine_key_name in peak_mapping.items():
                if hasattr(peak, local_attr_name):
                    attr_value = getattr(peak, local_attr_name).value
                    cif_lines.append(f"{engine_key_name} {attr_value}")

        # Experiment range category
        # Extract measurement range dynamically
        x_data = experiment.datastore.pattern.x
        two_theta_min = float(x_data.min())
        two_theta_max = float(x_data.max())
        cif_lines.append("")
        if expt_type.beam_mode.value == "constant wavelength":
            cif_lines.append(f"_range_2theta_min {two_theta_min}")
            cif_lines.append(f"_range_2theta_max {two_theta_max}")
        elif expt_type.beam_mode.value == "time-of-flight":
            cif_lines.append(f"_range_time_min {two_theta_min}")
            cif_lines.append(f"_range_time_max {two_theta_max}")

        # ITERABLE CATEGORIES (LOOPS)

        # Linked phases category
        # Force single linked phase to be used, as we handle multiple phases
        # with their scales independently of the calculation engines
        cif_lines.append("")
        cif_lines.append("loop_")
        cif_lines.append("_phase_label")
        cif_lines.append("_phase_scale")
        cif_lines.append(f"{linked_phase.model_id} 1.0")

        # Background category
        # Force background to be zero, as we handle it independently of the
        # calculation engines
        if expt_type.beam_mode.value == "constant wavelength":
            cif_lines.append("")
            cif_lines.append("loop_")
            cif_lines.append("_pd_background_2theta")
            cif_lines.append("_pd_background_intensity")
            cif_lines.append(f"{two_theta_min} 0.0")
            cif_lines.append(f"{two_theta_max} 0.0")
        elif expt_type.beam_mode.value == "time-of-flight":
            cif_lines.append("")
            cif_lines.append("loop_")
            cif_lines.append("_tof_backgroundpoint_time")
            cif_lines.append("_tof_backgroundpoint_intensity")
            cif_lines.append(f"{two_theta_min} 0.0")
            cif_lines.append(f"{two_theta_max} 0.0")

        # Measured data category
        if expt_type.beam_mode.value == "constant wavelength":
            cif_lines.append("")
            cif_lines.append("loop_")
            cif_lines.append("_pd_meas_2theta")
            cif_lines.append("_pd_meas_intensity")
            cif_lines.append("_pd_meas_intensity_sigma")
        elif expt_type.beam_mode.value == "time-of-flight":
            cif_lines.append("")
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
