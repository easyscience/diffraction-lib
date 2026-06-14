---
title: instrument
---

# :material-microscope: instrument

[pd-neut-cwl][3]{:.label-experiment}
[pd-neut-tof][3]{:.label-experiment} [pd-xray][3]{:.label-experiment}
[sc-neut-cwl][3]{:.label-experiment}
[pd-neut-total][3]{:.label-experiment}
[pd-xray-total][3]{:.label-experiment}

### :material-wrench: setup_wavelength { #instrument-setup-wavelength }

| Access                                                                                                                                                                          | Source                    |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------- |
| instrument.setup_wavelength                                                                                                                                                     | [code][0]{:.label-cif}    |
| \_instrument.setup_wavelength                                                                                                                                                   | [Edi][0]{:.label-cif}   |
| \_diffrn_radiation_wavelength.value [:material-open-in-new:](https://www.iucr.org/__data/iucr/cifdic_html/3/CORE_DIC/Idiffrn_radiation_wavelength.value.html 'IUCr definition') | [coreCIF][0]{:.label-cif} |

Incident neutron or X-ray wavelength.

### :material-tune: calib_twotheta_offset { #instrument-calib-twotheta-offset }

| Access                             | Source                  |
| ---------------------------------- | ----------------------- |
| instrument.calib_twotheta_offset   | [code][0]{:.label-cif}  |
| \_instrument.calib_twotheta_offset | [Edi][0]{:.label-cif} |
| \_pd_calib.2theta_offset           | [pdCIF][0]{:.label-cif} |

Instrument misalignment offset.

### :material-wrench: setup_twotheta_bank { #instrument-setup-twotheta-bank }

| Access                           | Source                     |
| -------------------------------- | -------------------------- |
| instrument.setup_twotheta_bank   | [code][0]{:.label-cif}     |
| \_instrument.setup_twotheta_bank | [Edi][0]{:.label-cif}    |
| \_instr.2theta_bank              | [coreCIF][0]{:.label-cif} |

Detector bank position.

### :material-tune: calib_d_to_tof_reciprocal { #instrument-calib-d-to-tof-reciprocal }

| Access                                 | Source                     |
| -------------------------------------- | -------------------------- |
| instrument.calib_d_to_tof_reciprocal   | [code][0]{:.label-cif}     |
| \_instrument.calib_d_to_tof_reciprocal | [Edi][0]{:.label-cif}    |
| \_instr.d_to_tof_recip                 | [coreCIF][0]{:.label-cif} |

TOF reciprocal velocity correction.

### :material-tune: calib_d_to_tof_offset { #instrument-calib-d-to-tof-offset }

| Access                             | Source                     |
| ---------------------------------- | -------------------------- |
| instrument.calib_d_to_tof_offset   | [code][0]{:.label-cif}     |
| \_instrument.calib_d_to_tof_offset | [Edi][0]{:.label-cif}    |
| \_instr.d_to_tof_offset            | [coreCIF][0]{:.label-cif} |

TOF offset.

### :material-tune: calib_d_to_tof_linear { #instrument-calib-d-to-tof-linear }

| Access                             | Source                     |
| ---------------------------------- | -------------------------- |
| instrument.calib_d_to_tof_linear   | [code][0]{:.label-cif}     |
| \_instrument.calib_d_to_tof_linear | [Edi][0]{:.label-cif}    |
| \_instr.d_to_tof_linear            | [coreCIF][0]{:.label-cif} |

TOF linear conversion.

### :material-tune: calib_d_to_tof_quadratic { #instrument-calib-d-to-tof-quadratic }

| Access                                | Source                     |
| ------------------------------------- | -------------------------- |
| instrument.calib_d_to_tof_quadratic   | [code][0]{:.label-cif}     |
| \_instrument.calib_d_to_tof_quadratic | [Edi][0]{:.label-cif}    |
| \_instr.d_to_tof_quad                 | [coreCIF][0]{:.label-cif} |

TOF quadratic correction.

## Additional Edi Keys

### :material-tag: calib_sample_displacement { #instrument-calib-sample-displacement }

| Access                                 | Source                  |
| -------------------------------------- | ----------------------- |
| \_instrument.calib_sample_displacement | [Edi][0]{:.label-cif} |

Specimen displacement from the diffractometer axis.

### :material-tag: calib_sample_transparency { #instrument-calib-sample-transparency }

| Access                                 | Source                  |
| -------------------------------------- | ----------------------- |
| \_instrument.calib_sample_transparency | [Edi][0]{:.label-cif} |

Sample transparency (beam penetration) shift.

<!-- prettier-ignore-start -->
[0]: #
[3]: ../../glossary.md#experiment-type-labels
<!-- prettier-ignore-end -->
