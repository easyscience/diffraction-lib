[customCIF][0]{:.label-cif}

# \_instr

This category stores instrument setup and calibration parameters used by
EasyDiffraction experiments. Constant-wavelength and time-of-flight
experiments use different subsets of the category.

## \_instr.wavelength

Incident neutron or X-ray wavelength for constant-wavelength
experiments. In Python this is accessed as:

```python
experiment.instrument.setup_wavelength
```

## \_instr.2theta_offset

Two-theta zero offset for constant-wavelength powder experiments. In
Python this is accessed as:

```python
experiment.instrument.calib_twotheta_offset
```

## \_instr.2theta_bank

Detector-bank two-theta angle for time-of-flight powder experiments. In
Python this is accessed as:

```python
experiment.instrument.setup_twotheta_bank
```

## \_instr.d_to_tof

Time-of-flight calibration terms converting d-spacing to time of flight.
In Python these are accessed as:

- `experiment.instrument.calib_d_to_tof_reciprocal`
- `experiment.instrument.calib_d_to_tof_offset`
- `experiment.instrument.calib_d_to_tof_linear`
- `experiment.instrument.calib_d_to_tof_quadratic`

They serialize to the following CIF tags:

- `_instr.d_to_tof_recip`
- `_instr.d_to_tof_offset`
- `_instr.d_to_tof_linear`
- `_instr.d_to_tof_quad`

<!-- prettier-ignore-start -->
[0]: #
[1]: https://www.iucr.org/resources/cif/dictionaries/browse/cif_core
[2]: https://www.iucr.org/resources/cif/dictionaries/browse/cif_pd
<!-- prettier-ignore-end -->
