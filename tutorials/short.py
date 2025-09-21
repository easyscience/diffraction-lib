from easydiffraction import Experiment
from easydiffraction import Logger
from easydiffraction import SampleModel
from easydiffraction import SampleModels
from easydiffraction.sample_models.collections.atom_sites import AtomSite
from easydiffraction.sample_models.collections.atom_sites import AtomSites
from easydiffraction.sample_models.components.cell import Cell
from easydiffraction.sample_models.components.space_group import SpaceGroup

Logger.configure(mode=Logger.Mode.LOG, level=Logger.Level.DEBUG)
# Logger.configure(mode=Logger.Mode.RAISE, level=Logger.Level.DEBUG)

sg = SpaceGroup()
sg.name_h_m = 'P n m a'
sg.it_coordinate_system_code = 'cab'

cell = Cell()
cell.length_a = 5.4603

site = AtomSite()
site.type_symbol = 'Si'

sites = AtomSites()
sites.add(site)

model = SampleModel(name='mdl')
model.space_group = sg
model.cell = cell
model.atom_sites = sites

print(model.parameters)

models = SampleModels()
models.add(model)

print(models)
print(models.parameters)
print(models.as_cif)

exp = Experiment(name='exp1', data_path='data/hrpt_lbco.xye')

print(exp)
