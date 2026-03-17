# %%
import easydiffraction as ed
import numpy as np

# %%
project = ed.Project()

# %%
model_path = ed.download_data(id=1, destination='data')
project.structures.add_from_cif_path(cif_path=model_path)

#project.structures.add_from_scratch(name='qwe')
#project.structures['qwe'] = 6
#print(project.structures['qwe'].name.value)
#struct = project.structures['qwe']
#struct.cell = "cell"
#print(struct.cell)

#exit()



# %%
expt_path = ed.download_data(id=2, destination='data')
project.experiments.add_from_cif_path(cif_path=expt_path)
#project.experiments.add_from_cif_path(cif_path=77)

#expt = ed.ExperimentFactory.from_scratch(name='expt', scattering_type='total2')
#print(expt)
exit()

print('\nStructure:')
print(project.structures['lbco'])

print('\nExperiment:')
print(project.experiments['hrpt'])


exit()



# %%
#sample = project.sample_models.get(id=1)
#sample = project.sample_models.get(name='Fe2O3')
sample = project.sample_models['lbco']

# %%
print()
print("=== Testing cell.length_a ===")
sample.cell.length_a = 3
print(sample.cell.length_a, type(sample.cell.length_a.value))
sample.cell.length_a = np.int64(4)
print(sample.cell.length_a, type(sample.cell.length_a.value))
sample.cell.length_a = np.float64(5.5)
print(sample.cell.length_a, type(sample.cell.length_a.value))
###sample.cell.length_a = "6.0"
###sample.cell.length_a = -7.0
###sample.cell.length_a = None
print(sample.cell.length_a, type(sample.cell.length_a.value))

# %%
print()
print("=== Testing space_group ===")
sample.space_group.name_h_m = 'P n m a'
print(sample.space_group.name_h_m)
print(sample.space_group.it_coordinate_system_code)
###sample.space_group.name_h_m = 'P x y z'
print(sample.space_group.name_h_m)
###sample.space_group.name_h_m = 4500
print(sample.space_group.name_h_m)
sample.space_group.it_coordinate_system_code = 'cab'
print(sample.space_group.it_coordinate_system_code)

# %%
print()
print("=== Testing atom_sites ===")
sample.atom_sites.add(label2='O5', type_symbol='O')

# %%
sample.show_as_cif()