from easydiffraction import Experiment
from easydiffraction import Experiments
from easydiffraction import Logger
from easydiffraction import Project
from easydiffraction import SampleModel
from easydiffraction import SampleModels
from easydiffraction.experiments.collections.linked_phases import LinkedPhase
from easydiffraction.experiments.collections.linked_phases import LinkedPhases
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
# models.add(model)
models.add_from_cif_path('data/lbco.cif')

print(models)
for p in models.parameters:
    print(p)
print(models.as_cif)

exp = Experiment(name='exp1', data_path='data/hrpt_lbco.xye')
print(exp)

linked_phases = LinkedPhases()
linked_phase = LinkedPhase(id='lbco', scale=1.0)
linked_phases.add(linked_phase)

exp.linked_phases = linked_phases


experiments = Experiments()
print(experiments)

experiments.add(exp)
print(experiments)
for p in experiments.parameters:
    print(p)
# print(experiments.as_cif)


proj = Project(name='PROJ')
print(proj)

proj.sample_models = models
proj.experiments = experiments


# proj.plotter.engine = 'plotly'

proj.plot_meas_vs_calc(expt_name='exp1', x_min=38, x_max=41)
