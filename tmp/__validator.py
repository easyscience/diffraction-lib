# %%
import easydiffraction as ed
import numpy as np

# %%
project = ed.Project()

# %%
model_path = ed.download_data(id=1, destination='data')
project.sample_models.add(cif_path=model_path)

# %%
expt_path = ed.download_data(id=2, destination='data')
project.experiments.add(cif_path=expt_path)

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