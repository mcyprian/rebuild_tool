import yaml
from collections import UserDict

from sclbuilder.exceptions import IncompleteMetadataException, UnknownPluginException
from sclbuilder.builder_plugins.builder_loader import available_builder_plugins
from sclbuilder.pkg_source_plugins.pkg_source_loader import available_pkg_source_plugins

def get_file_data(input_file, split=False):
    '''
    Opens given file and reads it,
    returns string datai, can cause IOError exception
    '''
    with open(input_file, 'r') as fi:
        data = fi.read()
        if split:
            return data.splitlines()
        else:
            return data

class RebuildMetadata(UserDict):
    '''
    Class to load, check and store all rebuild metadata
    '''
    def __init__(self, yaml_data):
        super(self.__class__, self).__init__()
        self.data = yaml.load(yaml_data)

        for attr in ['build_system', 'packages_source', 'repo', 'packages']:
            if attr not in self:
                raise IncompleteMetadataException("Missing attribute {}.".format(attr))

        if self['build_system'] not in available_builder_plugins:
            raise UnknownPluginException("Builder plugin {} not available.".format(
                                         self['build_system']))
        
        if self['packages_source'] not in available_pkg_source_plugins:
            raise UnknownPluginException("Packages source  plugin {} not available.".format(
                                         self['packages_source']))

        if 'metapackage' in self:
            self['packages'].append(self['metapackage'])

        if not 'prefix' in self:
            self['prefix'] = ""

        for attr in ["chroots", "recipes", "chroot_pkgs", "packages"]:
            if attr in self:
                if not isinstance(self[attr], list):
                    self[attr] = [self[attr]]

        if self['packages_source'] == 'koji': 
            if 'koji_tag' not in self:
                raise IncompleteMetadataException("Missing attribute koji_tag necesary to get srpms from koji.")
        else:
            self['koji_tag'] = None


class Recipe(yaml.YAMLObject):
    '''
    Class to store order of building recipe, reads data from
    yml file in format:
        - ['package1', 'bootstrap 0']
        - ['package2']
        - ['package1', 'bootstrap 1']
        ...
    '''
    def __init__(self, recipe_file):
        self.packages = set()
        self.order = get_file_data(recipe_file)
        self.get_packages()

    @property
    def order(self):
        return self.__order

    @order.setter
    def order(self, recipe_data):
        self.__order = yaml.load(recipe_data)

    def get_packages(self):
        '''
        Fills packages set with all packages names present in recipe
        '''
        if not hasattr(self, 'order'):
            return
        for item in self.order:
            self.packages.add(item[0])

