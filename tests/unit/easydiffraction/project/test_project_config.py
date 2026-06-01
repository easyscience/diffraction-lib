# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

import datetime


def test_project_config_exposes_project_info_chart_and_table_categories():
    from easydiffraction.core.category_owner import CategoryOwner
    from easydiffraction.project.categories.rendering_plot import RenderingPlot
    from easydiffraction.project.categories.report import Report
    from easydiffraction.project.categories.rendering_table import RenderingTable
    from easydiffraction.project.project_config import ProjectConfig
    from easydiffraction.project.project_info import ProjectInfo

    config = ProjectConfig(name='beer', title='Beer title', description='Some description')

    assert isinstance(config, CategoryOwner)
    assert isinstance(config.info, ProjectInfo)
    assert isinstance(config.rendering_plot, RenderingPlot)
    assert isinstance(config.report, Report)
    assert isinstance(config.rendering_table, RenderingTable)
    assert config.info._parent is config
    assert config.rendering_plot._parent is config
    assert config.report._parent is config
    assert config.rendering_table._parent is config
    assert config.info.name == 'beer'
    assert config.info.title == 'Beer title'
    assert config.info.description == 'Some description'
    assert config.info.path is None
    assert isinstance(config.info.created, datetime.datetime)
    assert isinstance(config.info.last_modified, datetime.datetime)
    assert config.verbosity._parent is config
    assert config.verbosity.fit.value == 'full'
    assert config.categories == [
        config.info,
        config.rendering_plot,
        config.report,
        config.rendering_table,
        config.verbosity,
        config.rendering_structure,
        config.structure_view,
        config.structure_style,
    ]
    assert config.parameters == (
        config.info.parameters
        + config.rendering_plot.parameters
        + config.report.parameters
        + config.rendering_table.parameters
        + config.verbosity.parameters
        + config.rendering_structure.parameters
        + config.structure_view.parameters
        + config.structure_style.parameters
    )


def test_project_config_as_cif_has_project_chart_and_table_sections_without_data_header():
    from easydiffraction.project.project_config import ProjectConfig

    config = ProjectConfig(name='beer', title='Beer title', description='Some description')

    cif_text = config.as_cif

    assert not cif_text.startswith('data_')
    assert '_project.id               beer' in cif_text
    assert '_project.title' in cif_text
    assert '_project.description' in cif_text
    assert '_project.created' in cif_text
    assert '_project.last_modified' in cif_text
    assert '_rendering_plot.type' in cif_text
    assert '_report.cif' in cif_text
    assert '_report.html' in cif_text
    assert '_report.tex' in cif_text
    assert '_report.pdf' in cif_text
    assert '_report.html_offline' in cif_text
    assert '_rendering_table.type' in cif_text
    assert '_rendering_plot.type auto' in cif_text
    assert '_rendering_table.type auto' in cif_text
    assert '_verbosity.fit full' in cif_text
    assert '_journal.' not in cif_text
    assert '_publ_' not in cif_text


def test_project_save_and_load_use_auto_display_defaults_when_unset(tmp_path):
    from easydiffraction.project.project import Project

    project = Project(name='beer', title='Beer title', description='Some description')
    project.save_as(str(tmp_path / 'proj'))

    project_cif = (tmp_path / 'proj' / 'project.cif').read_text()

    assert not project_cif.startswith('data_')
    assert '_rendering_plot.type auto' in project_cif
    assert '_report.cif false' in project_cif
    assert '_rendering_table.type auto' in project_cif
    assert '_verbosity.fit full' in project_cif
    assert '_journal.' not in project_cif
    assert '_publ_' not in project_cif

    loaded = Project.load(str(tmp_path / 'proj'))

    assert loaded.rendering_plot.type == 'auto'
    assert loaded.rendering_table.type == 'auto'
    assert loaded.verbosity.fit.value == 'full'


def test_project_save_and_load_keep_project_config_section_format(tmp_path):
    from easydiffraction.project.project import Project

    project = Project(name='beer', title='Beer title', description='Some description')
    project.rendering_plot.type = 'asciichartpy'
    project.rendering_table.type = 'rich'
    project.save_as(str(tmp_path / 'proj'))

    project_cif = (tmp_path / 'proj' / 'project.cif').read_text()
    assert not project_cif.startswith('data_')
    assert '_project.id               beer' in project_cif
    assert '_rendering_plot.type asciichartpy' in project_cif
    assert '_report.cif false' in project_cif
    assert '_rendering_table.type rich' in project_cif
    assert '_verbosity.fit full' in project_cif

    loaded = Project.load(str(tmp_path / 'proj'))
    assert loaded.info.name == 'beer'
    assert loaded.info.title == 'Beer title'
    assert loaded.info.description == 'Some description'
    assert isinstance(loaded.info.created, datetime.datetime)
    assert isinstance(loaded.info.last_modified, datetime.datetime)
    assert loaded.rendering_plot.type == 'asciichartpy'
    assert loaded.rendering_table.type == 'rich'
    assert loaded.verbosity.fit.value == 'full'


def test_project_save_wraps_long_description_as_cif_text_field(tmp_path):
    from easydiffraction.project.project import Project

    description = (
        'This is the most minimal example of using EasyDiffraction. '
        'It shows how to load a previously saved project from a directory '
        'and run refinement in just a few lines of code.'
    )
    project = Project(name='beer', title='Beer title', description=description)
    project.save_as(str(tmp_path / 'proj'))

    project_cif = (tmp_path / 'proj' / 'project.cif').read_text()

    assert '_project.description' in project_cif
    description_tail = project_cif.split('_project.description', maxsplit=1)[1].lstrip(' ')
    assert description_tail.startswith('\n;\n')
    assert '\n;\n_project.created' in project_cif
    description_block = description_tail.split('\n;\n', maxsplit=1)[1]
    description_block = description_block.split('\n;\n_project.created', maxsplit=1)[0]
    description_lines = description_block.splitlines()

    assert len(description_lines) > 1
    assert all(not line.startswith(';') for line in description_lines)
    assert all(not line.endswith(';') for line in description_lines)
    assert description_lines[0].startswith('This is the most minimal example')
    assert description_lines[-1].endswith('lines of code.')

    loaded = Project.load(str(tmp_path / 'proj'))

    assert loaded.info.description == description
