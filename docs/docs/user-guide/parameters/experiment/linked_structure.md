---
title: linked_structure
---

# :material-puzzle: linked_structure

[pd-neut-cwl][3]{:.label-experiment}
[pd-neut-tof][3]{:.label-experiment} [pd-xray][3]{:.label-experiment}
[sc-neut-cwl][3]{:.label-experiment}

## :material-identifier: structure_id { #linked-structure-structure-id }

| Access                               | Source                  |
| ------------------------------------ | ----------------------- |
| linked_structures['ID'].structure_id | [code][0]{:.label-cif}  |
| linked_structure.structure_id        | [code][0]{:.label-cif}  |
| \_linked_structure.structure_id      | [Edi][0]{:.label-cif} |
| \_pd_phase_block.id                  | [pdCIF][0]{:.label-cif} |

Identifier of the linked structure. The plural `linked_structures['ID']`
form is used for powder experiments (one or more linked phases); the
scalar `linked_structure` form is used for single-crystal experiments.

## :material-scale: scale { #linked-structure-scale }

| Access                        | Source                  |
| ----------------------------- | ----------------------- |
| linked_structures['ID'].scale | [code][0]{:.label-cif}  |
| linked_structure.scale        | [code][0]{:.label-cif}  |
| \_linked_structure.scale      | [Edi][0]{:.label-cif} |
| \_pd_phase_block.scale        | [pdCIF][0]{:.label-cif} |

Scale factor of the linked structure.

<!-- prettier-ignore-start -->
[0]: #
[3]: ../../glossary.md#experiment-type-labels
<!-- prettier-ignore-end -->
