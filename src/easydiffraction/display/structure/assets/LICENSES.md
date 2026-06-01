# Element data provenance

`elements.py` is generated from the sources below. All are reused under
permissive licences; the underlying values are scientific data.

## Sources

| Data                                                  | Source                                                                                                                 | Licence      |
| ----------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- | ------------ |
| Jmol/CPK colours, covalent radii, van der Waals radii | EasyDiffractionBeta `easyDiffractionApp/Logic/Tables.py` `PERIODIC_TABLE` (github.com/easyscience/EasyDiffractionBeta) | BSD-3-Clause |
| Ionic (Shannon) radii                                 | pymatgen `dev_scripts/periodic_table_resources/Shannon_Radii.csv`                                                      | MIT          |
| Atomic radii                                          | pymatgen `dev_scripts/periodic_table_resources/radii.csv` (`Atomic radius`)                                            | MIT          |
| VESTA colours                                         | pymatgen `src/pymatgen/vis/ElementColorSchemes.yaml` (`VESTA`)                                                         | MIT          |
| Oxidation states (for Shannon selection)              | pymatgen `dev_scripts/periodic_table_resources/oxidation_states.yaml`                                                  | MIT          |

Primary scientific references:

- R. D. Shannon, _Revised effective ionic radii and systematic studies
  of interatomic distances in halides and chalcogenides_, Acta Cryst.
  (1976) **A32**, 751.
- K. Momma and F. Izumi, _VESTA 3_, J. Appl. Cryst. (2011) **44**, 1272
  (element colour palette).

pymatgen raw files were fetched from
`https://raw.githubusercontent.com/materialsproject/pymatgen/master/`.

## Shannon representative-radius selection

The atom-site model carries only an element symbol, so one
representative Shannon row is chosen per element by a fixed,
reproducible rule:

1. consider the element's oxidation states from `oxidation_states.yaml`,
   in listed order, keeping those that have a Shannon entry; then any
   remaining Shannon charges, lowest `|charge|` first;
2. for the first such charge, prefer coordination `VI`, else the lowest
   coordination present; prefer high-spin where a spin state is listed;
3. take the `Ionic Radius` column; skip non-physical entries (e.g. the
   negative H+ value) and fall back to the covalent radius.

Elements with no usable Shannon entry (noble gases and a few others)
carry `ionic = None` and fall back to the covalent radius at lookup
time.

## Chosen (charge / coordination) per element

```
Li:+1/VI  Be:+2/VI  B:+3/VI  C:+4/VI  N:-3/IV  O:-2/VI  F:-1/VI  Na:+1/VI
Mg:+2/VI  Al:+3/VI  Si:+4/VI  P:+3/VI  S:-2/VI  Cl:-1/VI  K:+1/VI  Ca:+2/VI
Sc:+3/VI  Ti:+2/VI  V:+2/VI  Cr:+2/VI  Mn:+2/VI  Fe:+2/VI  Co:+2/VI  Ni:+2/VI
Cu:+1/VI  Zn:+2/VI  Ga:+3/VI  Ge:+2/VI  As:+3/VI  Se:-2/VI  Br:-1/VI  Rb:+1/VI
Sr:+2/VI  Y:+3/VI  Zr:+4/VI  Nb:+3/VI  Mo:+3/VI  Tc:+4/VI  Ru:+3/VI  Rh:+3/VI
Pd:+2/VI  Ag:+1/VI  Cd:+2/VI  In:+3/VI  Sn:+4/VI  Sb:+3/VI  Te:-2/VI  I:-1/VI
Xe:+8/VI  Cs:+1/VI  Ba:+2/VI  La:+3/VI  Ce:+3/VI  Pr:+3/VI  Nd:+2/VIII
Pm:+3/VI  Sm:+2/VII  Eu:+2/VI  Gd:+3/VI  Tb:+3/VI  Dy:+2/VI  Ho:+3/VI  Er:+3/VI
Tm:+2/VI  Yb:+2/VI  Lu:+3/VI  Hf:+4/VI  Ta:+3/VI  W:+4/VI  Re:+4/VI  Os:+4/VI
Ir:+3/VI  Pt:+2/VI  Au:+1/VI  Hg:+1/VI  Tl:+1/VI  Pb:+2/VI  Bi:+3/VI  Po:+4/VI
At:+7/VI  Fr:+1/VI  Ra:+2/VIII  Ac:+3/VI  Th:+4/VI  Pa:+3/VI  U:+3/VI  Np:+3/VI
Pu:+3/VI  Am:+2/VII  Cm:+3/VI  Bk:+3/VI  Cf:+3/VI  No:+2/VI
```
