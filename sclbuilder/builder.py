import os
import tempfile
import shutil
import logging
from abc import ABCMeta, abstractmethod

from sclbuilder.graph import PackageGraph
from sclbuilder.rebuild_metadata import Recipe
from sclbuilder.exceptions import MissingRecipeException, BuildFailureException
from sclbuilder import utils

logger = logging.getLogger(__name__)

def check_build(build_fce):
    '''
    Decorator to check if build was successfull or not,
    updates attributes and removes package from graph
    '''
    def inner(self, pkgs, verbose=True):
        if not isinstance(pkgs, list):
            pkgs = [pkgs]
        if build_fce(self, pkgs, verbose):
            for pkg in pkgs:
                if verbose: # not building recipe
                    self.graph.G.remove_node(pkg)
                self.built_packages.add(pkg)
            return True
        else:
            raise BuildFailureException("Failed to build packages {}.".format(pkgs))
    return inner


class Builder(metaclass=ABCMeta):
    '''
    Abstract superclass of builder classes.
    '''
    def __init__(self, rebuild_metadata, pkg_source):
        self.pkg_source = pkg_source
        self.packages = set(rebuild_metadata['packages'])
        if 'metapackage' in rebuild_metadata:
            self.metapackage = rebuild_metadata['metapackage']
        self.repo = rebuild_metadata['repo']
        self.prefix = rebuild_metadata['prefix']
        self.koji_tag = rebuild_metadata['koji_tag']
        self.path = tempfile.mkdtemp()
        self.built_packages = set()
        self.num_of_deps = {}
        self.circular_deps = []
        self.get_files()
        self.graph = PackageGraph(self.repo, self.pkg_source)
        try:
            self.recipes = rebuild_metadata['recipes']
        except IOError:
            logger.error("Failed to load recipe {0}.".format(rebuild_metadata['recipes']))

    def __del__(self):
        shutil.rmtree(self.path)
        shutil.rmtree(self.__tempdir)

    @property
    def path(self):
        return self.__path

    @path.setter
    def path(self, value):
        self.__tempdir = value
        value += '/sclbuilder-{0}/'.format(self.repo)
        if not os.path.isdir(value):
            os.makedirs(value)
        self.__path = value

    @property
    def recipes(self):
        return self.__recipes

    @recipes.setter
    def recipes(self, recipe_files):
        if not recipe_files:
            self.__recipes = None
        else:
            self.__recipes = [Recipe(recipe) for recipe in recipe_files]

    def get_relations(self):
        '''
        Runs graph analysis and get dependance tree and circular_deps
        '''
        self.graph.make_graph()
        self.circular_deps = self.graph.get_cycles()
        if self.circular_deps and not self.recipes:
            raise MissingRecipeException("Missing recipes to resolve circular dependencies in graph.")

    def deps_satisfied(self, package):
        '''
        Compares package deps with self.build_packages to
        check if are all dependancies already built
        '''
        if set(self.graph.G.successors(package)) <= self.built_packages:
            return True
        return False

    def recipe_deps_satisfied(self, recipe):
        '''
        Checks if all packages in recipe have satisfied their
        dependencies on packages that are not in recipe
        '''
        deps = set()
        for pkg in recipe.packages:
            if not pkg in self.packages:
                raise KeyError("Package {} from recipe missing in packages list".format(
                    pkg, recipe))
            deps |= set(self.graph.G.successors(pkg))

        if (deps - recipe.packages) <= self.built_packages:
            return True
        return False

    @abstractmethod
    def add_chroot_pkg(self, chroot_pkgs):
        '''
        Method to add packages to minimal buildroot
        '''
        pass

    @check_build
    def build(self, pkgs, verbose=True):
        for pkg in pkgs:
            if verbose:
                print("Building {0}...".format(pkg))
        return True


    def run_building(self):
        '''
        First builds all packages without deps, then iterates over num_of_deps
        and simulate building of packages in right order
        '''

        # Build and add metapackage to chroots when rebuilding scl
        if hasattr(self, 'metapackage'):
            self.build([self.metapackage])
            self.add_chroot_pkg([self.metapackage])

        while self.packages > self.built_packages:
            zero_deps = self.graph.get_leaf_nodes()
            if zero_deps:
                self.build(zero_deps)
            else:
                for recipe in self.recipes:
                    if self.recipe_deps_satisfied(recipe):
                        self.build_following_recipe(recipe)

    def find_recipe(self, package):
        '''
        Search for recipe including package in self.recipes
        '''
        for recipe in self.recipes:
            if package in recipe.packages:
                return recipe
        raise MissingRecipeException("Recipe for package {0} not found".format(package))

    def build_following_recipe(self, recipe):
        '''
        Builds packages in order and macro values discribed in given
        recipe.
        '''
        for step in recipe.order:
            if len(step) == 1:
                print("Building package {0}".format(step[0]))
            else:
                (name, macro_value) = step
                print("Building package {0} {1}".format(name, macro_value))
                (macro, value) = macro_value.split(' ')
                utils.check_bootstrap_macro(self.pkg_source[name].full_path_spec, macro)
                utils.edit_bootstrap(self.pkg_source[name].full_path_spec, macro, value)
                self.pkg_source[name].pack()
            self.build([step[0]], False)
        for pkg in {step[0] for step in recipe.order}:
            self.graph.G.remove_node(pkg)
        self.recipes.remove(recipe)

    def get_files(self):
        '''
        Creates SrpmArchive object and downloads files for each package
        '''
        with utils.ChangeDir(self.path):
            for package in self.packages:
                pkg_dir = self.path + package + "_files/"
                if not os.path.exists(pkg_dir):
                    os.mkdir(pkg_dir)
                print("Getting files of {0}.".format(package))
                logger.debug("Getting files of {0}.".format(package))
                self.pkg_source.add(package, pkg_dir, self.repo, self.prefix, self.koji_tag)
