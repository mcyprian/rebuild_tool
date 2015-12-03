import pytest
import sys
import os

from sclbuilder import rebuild_metadata
from sclbuilder.exceptions import IncompleteMetadataException, UnknownPluginException

tests_dir = os.path.split(os.path.abspath(__file__))[0]

class TestRebuildMetadata(object):

    @pytest.mark.parametrize(('yaml_data', 'expected'), [
        ("build_system: copr\npackages_source: koji\nrepo: rawhide",
         IncompleteMetadataException),
         ("packages_source: koji\nrepo: rawhide\npackages: [pkg1, pkg2]",
         IncompleteMetadataException),
         ("build_system: copr\nrepo: rawhide\npackages: [pkg1]",
         IncompleteMetadataException),
         ("build_system: copr\npackages_source: dnf\npackages: [pkg1]",
         IncompleteMetadataException),
         ("build_system: bsys\npackages_source: dnf\npackages: [pkg1]\nrepo: rawhide",
         UnknownPluginException),
         ("build_system: copr\npackages_source: pkg_src\npackages: [pkg1]\nrepo: rawhide",
         UnknownPluginException)
    ])
    def test_incomplete_data(self, yaml_data, expected):
        with pytest.raises(expected):
            metadata = rebuild_metadata.RebuildMetadata(yaml_data)

    @pytest.mark.parametrize(('key', 'value'), [
        ('build_system', 'copr'),
        ('packages_source', 'koji'),
        ('repo', 'rawhide'),
        ('packages', ['pkg1', 'pkg2', 'metapkg']),
        ('recipes', ['path/recipe']),
        ('prefix', ''),
    ])
    def test_good_data(self, key, value):
        yaml_data = '''
            build_system: copr
            packages_source: koji
            repo: rawhide
            recipes: path/recipe
            packages: [pkg1, pkg2]
            metapackage: metapkg
                    '''
        metadata = rebuild_metadata.RebuildMetadata(yaml_data)
        assert metadata[key] == value

class TestRecipe(object):
    
    @pytest.mark.parametrize(('attr', 'value'), [
        ('packages', {'pkg1', 'pkg2'}),
        ('order', [['pkg1', 'bootstrap 0'], ['pkg2'], ['pkg1', 'bootstrap 1']])
    ])
    def test_get_packages(self, attr, value):
        r = rebuild_metadata.Recipe("{}/test_data/recipe.yml".format(tests_dir))
        assert getattr(r, attr) == value
