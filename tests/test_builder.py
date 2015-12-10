import pytest
from flexmock import flexmock
import os
import sys
from copr.client import CoprClient

from sclbuilder.builder_plugins.copr import RealBuilder
from sclbuilder.builder import Builder
from sclbuilder.graph import PackageGraph
from sclbuilder.pkg_source_plugins.dnf import DnfArchive
from sclbuilder.exceptions import MissingRecipeException
from sclbuilder import utils 

tests_dir = os.path.split(os.path.abspath(__file__))[0]

metadata = {"packages" : ['pkg1', 'pkg2', 'pkg3', 'pkg4'],
                    "repo" : 'rawhide',
                    "prefix" : "",
                    "recipes" : ["{}/test_data/recipe.yml".format(tests_dir)],
                    "koji_tag" : 'f24-python3',
                    "copr_project": "project",
                    "chroots" : 'f23'}

fake_archive = flexmock(
    full_path_spec = 'path/to/spec',
    pack = lambda: "packing"
)

pkg_source = {'pkg1' : fake_archive,
              'pkg2' : fake_archive}

def create_mocked_builder():
    flexmock(RealBuilder).should_receive('build').replace_with(lambda x: set(x))
    flexmock(Builder).should_receive('get_files').once()
    flexmock(CoprClient).should_receive('create_from_file_config').once()
    flexmock(RealBuilder).should_receive('project_is_new').and_return(False)
    return RealBuilder(metadata, pkg_source)


class TestBuilder(object):

    @pytest.mark.parametrize(('leaf_nodes', 'expected'), [
        (['pkg3', 'pkg4'], ['pkg3', 'pkg4']),
        (None, ['pkg1']),
    ])
    def test_run_building(self, leaf_nodes, expected):
        builder = create_mocked_builder()
        flexmock(PackageGraph).should_receive('get_leaf_nodes').and_return(leaf_nodes)
        if not leaf_nodes:
            flexmock(RealBuilder).should_receive('recipe_deps_satisfied').and_return(True)
            # stops function after first call of build
            flexmock(RealBuilder).should_receive('build_following_recipe').replace_with(
                lambda x: builder.built_packages.add('pkg4')) 
        else:
            flexmock(RealBuilder).should_receive('build').with_args(expected)\
            .replace_with(lambda x: builder.built_packages.add('pkg4'))
        builder.packages = {'pkg1', 'pkg2', 'pkg3'}
        builder.run_building()

    @pytest.mark.parametrize(('built_packages', 'expected'), [
        ({'pkg3'}, False),
        (set(), False),
        ({'pkg3', 'pkg4'}, True)
    ])
    def test_recipe_deps_satisfied(self, built_packages, expected):
        builder = create_mocked_builder()
        flexmock(builder.graph.G).should_receive('successors').with_args('pkg1').and_return(['pkg3'])
        flexmock(builder.graph.G).should_receive('successors').with_args('pkg2').and_return(['pkg4'])
        builder.built_packages = built_packages
        assert builder.recipe_deps_satisfied(builder.recipes[0]) == expected


    @pytest.mark.parametrize(('pkg', 'expected'), [
        ('pkg1', {'pkg1', 'pkg2'}),
        ('pkg2', {'pkg1', 'pkg2'}),
        ('pkg3', MissingRecipeException),
    ])
    def test_find_recipe(self, pkg, expected):
        builder = create_mocked_builder()
        if pkg == 'pkg3':
            with pytest.raises(expected):
                builder.find_recipe(pkg)
        else:
            assert builder.find_recipe(pkg).packages == expected
       

    def test_build_following_recipe(self):
        builder = create_mocked_builder()
        flexmock(RealBuilder).should_receive('build').times(3)
        flexmock(utils).should_receive('check_bootstrap_macro').twice()
        flexmock(utils).should_receive('edit_bootstrap').twice()
        flexmock(builder.graph.G).should_receive('remove_node').times(2)
        builder.build_following_recipe(builder.recipes[0])

