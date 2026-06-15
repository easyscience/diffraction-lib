---
title: refln
---

# :material-diamond-outline: refln

[pd-neut-cwl][3]{:.label-experiment}
[pd-neut-tof][3]{:.label-experiment} [pd-xray][3]{:.label-experiment}
[sc-neut-cwl][3]{:.label-experiment}

## :material-tag: d_spacing { #refln-d-spacing }

| Access                | Source                 |
| --------------------- | ---------------------- |
| refln['ID'].d_spacing | [code][0]{:.label-cif} |
| \_refln.d_spacing     | [Edi][0]{:.label-cif}  |

Distance between lattice planes for this reflection.

## :material-tag: f_calc { #refln-f-calc }

| Access             | Source                 |
| ------------------ | ---------------------- |
| refln['ID'].f_calc | [code][0]{:.label-cif} |
| \_refln.f_calc     | [Edi][0]{:.label-cif}  |

Calculated structure-factor amplitude for this reflection.

## :material-tag: f_squared_calc { #refln-f-squared-calc }

| Access                     | Source                 |
| -------------------------- | ---------------------- |
| refln['ID'].f_squared_calc | [code][0]{:.label-cif} |
| \_refln.f_squared_calc     | [Edi][0]{:.label-cif}  |

Calculated structure-factor amplitude squared for this reflection.

## :material-tag: id { #refln-id }

| Access         | Source                 |
| -------------- | ---------------------- |
| refln['ID'].id | [code][0]{:.label-cif} |
| \_refln.id     | [Edi][0]{:.label-cif}  |

Identifier of the reflection.

## :material-tag: index_h { #refln-index-h }

| Access              | Source                 |
| ------------------- | ---------------------- |
| refln['ID'].index_h | [code][0]{:.label-cif} |
| \_refln.index_h     | [Edi][0]{:.label-cif}  |

Miller index h of a measured reflection.

## :material-tag: index_k { #refln-index-k }

| Access              | Source                 |
| ------------------- | ---------------------- |
| refln['ID'].index_k | [code][0]{:.label-cif} |
| \_refln.index_k     | [Edi][0]{:.label-cif}  |

Miller index k of a measured reflection.

## :material-tag: index_l { #refln-index-l }

| Access              | Source                 |
| ------------------- | ---------------------- |
| refln['ID'].index_l | [code][0]{:.label-cif} |
| \_refln.index_l     | [Edi][0]{:.label-cif}  |

Miller index l of a measured reflection.

## :material-arrow-collapse-up: intensity_calc { #refln-intensity-calc }

| Access                     | Source                 |
| -------------------------- | ---------------------- |
| refln['ID'].intensity_calc | [code][0]{:.label-cif} |
| \_refln.intensity_calc     | [Edi][0]{:.label-cif}  |

Intensity of the reflection calculated from atom site data.

## :material-arrow-collapse-up: intensity_meas { #refln-intensity-meas }

| Access                     | Source                 |
| -------------------------- | ---------------------- |
| refln['ID'].intensity_meas | [code][0]{:.label-cif} |
| \_refln.intensity_meas     | [Edi][0]{:.label-cif}  |

The intensity of the reflection derived from the measurements.

## :material-arrow-collapse-up: intensity_meas_su { #refln-intensity-meas-su }

| Access                        | Source                 |
| ----------------------------- | ---------------------- |
| refln['ID'].intensity_meas_su | [code][0]{:.label-cif} |
| \_refln.intensity_meas_su     | [Edi][0]{:.label-cif}  |

Standard uncertainty of the measured intensity.

## :material-tag: sin_theta_over_lambda { #refln-sin-theta-over-lambda }

| Access                            | Source                 |
| --------------------------------- | ---------------------- |
| refln['ID'].sin_theta_over_lambda | [code][0]{:.label-cif} |
| \_refln.sin_theta_over_lambda     | [Edi][0]{:.label-cif}  |

The sin(θ)/λ value for this reflection.

## :material-arrow-left-right: sin_theta_over_lambda_range_max { #refln-sin-theta-over-lambda-range-max }

| Access                                  | Source                 |
| --------------------------------------- | ---------------------- |
| data_range.sin_theta_over_lambda_max    | [code][0]{:.label-cif} |
| \_refln.sin_theta_over_lambda_range_max | [Edi][0]{:.label-cif}  |

Upper sinθ/λ bound of the calculation range.

## :material-arrow-left-right: sin_theta_over_lambda_range_min { #refln-sin-theta-over-lambda-range-min }

| Access                                  | Source                 |
| --------------------------------------- | ---------------------- |
| data_range.sin_theta_over_lambda_min    | [code][0]{:.label-cif} |
| \_refln.sin_theta_over_lambda_range_min | [Edi][0]{:.label-cif}  |

Lower sinθ/λ bound of the calculation range.

## :material-tag: structure_id { #refln-structure-id }

| Access                   | Source                    |
| ------------------------ | ------------------------- |
| refln['ID'].structure_id | [code][0]{:.label-cif}    |
| \_refln.structure_id     | [Edi][0]{:.label-cif}     |
| \_refln.phase_id         | [coreCIF][0]{:.label-cif} |

Identifier of the linked structure for this reflection.

## :material-timer-outline: time_of_flight { #refln-time-of-flight }

| Access                     | Source                 |
| -------------------------- | ---------------------- |
| refln['ID'].time_of_flight | [code][0]{:.label-cif} |
| \_refln.time_of_flight     | [Edi][0]{:.label-cif}  |

Calculated time-of-flight position for this reflection.

## :material-angle-acute: two_theta { #refln-two-theta }

| Access                | Source                 |
| --------------------- | ---------------------- |
| refln['ID'].two_theta | [code][0]{:.label-cif} |
| \_refln.two_theta     | [Edi][0]{:.label-cif}  |

Calculated 2theta position for this reflection.

## :material-sine-wave: wavelength { #refln-wavelength }

| Access                 | Source                 |
| ---------------------- | ---------------------- |
| refln['ID'].wavelength | [code][0]{:.label-cif} |
| \_refln.wavelength     | [Edi][0]{:.label-cif}  |

Mean wavelength of radiation for this reflection.

<!-- prettier-ignore-start -->
[0]: #
[3]: ../../glossary.md#experiment-type-labels
<!-- prettier-ignore-end -->
