---
title: data
---

# :material-chart-line: data

[pd-neut-cwl][3]{:.label-experiment}
[pd-neut-tof][3]{:.label-experiment} [pd-xray][3]{:.label-experiment}
[pd-neut-total][3]{:.label-experiment}
[pd-xray-total][3]{:.label-experiment}

## :material-tag: id { #data-id }

| Access             | Source                  |
| ------------------ | ----------------------- |
| data['ID'].id      | [code][0]{:.label-cif}  |
| \_data.id          | [Edi][0]{:.label-cif}   |
| \_pd_data.point_id | [pdCIF][0]{:.label-cif} |

Identifier for this data point in the dataset.

## :material-angle-acute: two_theta { #data-two-theta }

| Access                | Source                  |
| --------------------- | ----------------------- |
| data['ID'].two_theta  | [code][0]{:.label-cif}  |
| \_data.two_theta      | [Edi][0]{:.label-cif}   |
| \_pd_proc.2theta_scan | [pdCIF][0]{:.label-cif} |

Measured 2θ diffraction angle.

## :material-timer-outline: time_of_flight { #data-time-of-flight }

| Access                    | Source                  |
| ------------------------- | ----------------------- |
| data['ID'].time_of_flight | [code][0]{:.label-cif}  |
| \_data.time_of_flight     | [Edi][0]{:.label-cif}   |
| \_pd_meas.time_of_flight  | [pdCIF][0]{:.label-cif} |

Measured time for time-of-flight neutron measurement.

## :material-tag: d_spacing { #data-d-spacing }

| Access               | Source                  |
| -------------------- | ----------------------- |
| data['ID'].d_spacing | [code][0]{:.label-cif}  |
| \_data.d_spacing     | [Edi][0]{:.label-cif}   |
| \_pd_proc.d_spacing  | [pdCIF][0]{:.label-cif} |

d-spacing value corresponding to this data point.

## :material-arrow-collapse-up: intensity_meas { #data-intensity-meas }

| Access                    | Source                  |
| ------------------------- | ----------------------- |
| data['ID'].intensity_meas | [code][0]{:.label-cif}  |
| \_data.intensity_meas     | [Edi][0]{:.label-cif}   |
| \_pd_meas.intensity_total | [pdCIF][0]{:.label-cif} |

Intensity recorded at each measurement point (angle/time).

## :material-arrow-collapse-up: intensity_meas_su { #data-intensity-meas-su }

| Access                       | Source                  |
| ---------------------------- | ----------------------- |
| data['ID'].intensity_meas_su | [code][0]{:.label-cif}  |
| \_data.intensity_meas_su     | [Edi][0]{:.label-cif}   |
| \_pd_meas.intensity_total_su | [pdCIF][0]{:.label-cif} |

Standard uncertainty of the measured intensity at this point.

## :material-arrow-collapse-up: intensity_calc { #data-intensity-calc }

| Access                    | Source                  |
| ------------------------- | ----------------------- |
| data['ID'].intensity_calc | [code][0]{:.label-cif}  |
| \_data.intensity_calc     | [Edi][0]{:.label-cif}   |
| \_pd_calc.intensity_total | [pdCIF][0]{:.label-cif} |

Intensity of a computed diffractogram at this point.

## :material-arrow-collapse-up: intensity_bkg { #data-intensity-bkg }

| Access                   | Source                  |
| ------------------------ | ----------------------- |
| data['ID'].intensity_bkg | [code][0]{:.label-cif}  |
| \_data.intensity_bkg     | [Edi][0]{:.label-cif}   |
| \_pd_calc.intensity_bkg  | [pdCIF][0]{:.label-cif} |

Intensity of a computed background at this point.

## :material-tag: calc_status { #data-calc-status }

| Access                      | Source                  |
| --------------------------- | ----------------------- |
| data['ID'].calc_status      | [code][0]{:.label-cif}  |
| \_data.calc_status          | [Edi][0]{:.label-cif}   |
| \_pd_data.refinement_status | [pdCIF][0]{:.label-cif} |

Status code of the data point in calculation. Supported values include
`incl` and `excl`.

## :material-tag: r { #data-r }

| Access       | Source                  |
| ------------ | ----------------------- |
| data['ID'].r | [code][0]{:.label-cif}  |
| \_data.r     | [Edi][0]{:.label-cif}   |
| \_pd_proc.r  | [pdCIF][0]{:.label-cif} |

Interatomic distance in real space.

## :material-tag: g_r_meas { #data-g-r-meas }

| Access                    | Source                  |
| ------------------------- | ----------------------- |
| data['ID'].g_r_meas       | [code][0]{:.label-cif}  |
| \_data.g_r_meas           | [Edi][0]{:.label-cif}   |
| \_pd_meas.intensity_total | [pdCIF][0]{:.label-cif} |

Measured pair distribution function G(r).

## :material-tag: g_r_meas_su { #data-g-r-meas-su }

| Access                       | Source                  |
| ---------------------------- | ----------------------- |
| data['ID'].g_r_meas_su       | [code][0]{:.label-cif}  |
| \_data.g_r_meas_su           | [Edi][0]{:.label-cif}   |
| \_pd_meas.intensity_total_su | [pdCIF][0]{:.label-cif} |

Standard uncertainty of measured G(r).

## :material-tag: g_r_calc { #data-g-r-calc }

| Access                    | Source                  |
| ------------------------- | ----------------------- |
| data['ID'].g_r_calc       | [code][0]{:.label-cif}  |
| \_data.g_r_calc           | [Edi][0]{:.label-cif}   |
| \_pd_calc.intensity_total | [pdCIF][0]{:.label-cif} |

Calculated pair distribution function G(r).

<!-- prettier-ignore-start -->
[0]: #
[3]: ../../glossary.md#experiment-type-labels
<!-- prettier-ignore-end -->
