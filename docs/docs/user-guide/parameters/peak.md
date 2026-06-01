[customCIF][0]{:.label-cif}

# \_peak

This category stores peak-profile parameters used by powder diffraction
and total-scattering calculations. The active peak-profile category is
selected from the experiment:

```python
experiment.peak.type = 'pseudo-voigt'
```

## Constant-wavelength powder profiles

The constant-wavelength pseudo-Voigt profile uses Gaussian and
Lorentzian broadening parameters:

- `_peak.broad_gauss_u`
- `_peak.broad_gauss_v`
- `_peak.broad_gauss_w`
- `_peak.broad_lorentz_x`
- `_peak.broad_lorentz_y`

When empirical asymmetry is enabled, the profile also uses:

- `_peak.asym_p1`
- `_peak.asym_p2`
- `_peak.asym_p3`
- `_peak.asym_p4`

## Time-of-flight powder profiles

The time-of-flight pseudo-Voigt profiles use instrument-dependent
Gaussian broadening, back-to-back exponential rise and decay terms, and
optionally Lorentzian broadening or double-exponential asymmetry terms:

- `_peak.gauss_sigma_0`
- `_peak.gauss_sigma_1`
- `_peak.gauss_sigma_2`
- `_peak.rise_alpha_0`
- `_peak.rise_alpha_1`
- `_peak.decay_beta_0`
- `_peak.decay_beta_1`
- `_peak.lorentz_gamma_0`
- `_peak.lorentz_gamma_1`
- `_peak.lorentz_gamma_2`
- `_peak.dexp_rise_alpha_1`
- `_peak.dexp_rise_alpha_2`
- `_peak.dexp_decay_beta_00`
- `_peak.dexp_decay_beta_01`
- `_peak.dexp_decay_beta_10`

## Total-scattering profiles

Total-scattering peak parameters describe Q-space cutoff, broadening,
sharpening, and damping:

- `_peak.cutoff_q`
- `_peak.broad_q`
- `_peak.sharp_delta_1`
- `_peak.sharp_delta_2`
- `_peak.damp_q`
- `_peak.damp_particle_diameter`

<!-- prettier-ignore-start -->
[0]: #
[1]: https://www.iucr.org/resources/cif/dictionaries/browse/cif_core
[2]: https://www.iucr.org/resources/cif/dictionaries/browse/cif_pd
<!-- prettier-ignore-end -->
