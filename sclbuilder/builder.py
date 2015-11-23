import os
import tempfile
import shutil
from abc import ABCMeta, abstractmethod
from subprocess import CalledProcessError

from sclbuilder.graph import PackageGraph
from sclbuilder.rebuild_metadata import Recipe
from sclbuilder.exceptions import MissingRecipeException, BuildFailureException
from sclbuilder import utils

def check_build(build_fce):
    '''
    Decorator to check if build was successfull or not
    '''
    def inner(self, package, verbose=True):
        if build_fce(self, package, verbose):
            self.built_packages.add(package)
            self.built_rpms |= set(self.rpm_dict[package])
            return True
        else:
            raise BuildFailureException("Failed to build package {}.".format(package))
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
        self.path = tempfile.mkdtemp()
        self.built_packages = set()
        self.built_rpms = set()
        self.num_of_deps = {}
        self.circular_deps = []
        self.all_circular_deps = set()
        self.get_files()
        self.graph = PackageGraph(self.repo, self.pkg_source)
        try:
            self.recipes = rebuild_metadata['recipes']
        except IOError:
            print("Failed to load recipe {0}.".format(rebuild_metadata['recipes']))

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
            self.__recipes = []
            for recipe in recipe_files:
                self.__recipes.append(Recipe(recipe))

    def get_relations(self):
        '''
        Runs graph analysis and get dependance tree and circular_deps
        '''
        self.graph.make_graph()
        (self.num_of_deps, self.circular_deps) = self.graph.analyse()
        if self.circular_deps and not self.recipes:
            raise MissingRecipeException("Missing recipes to resolve circular dependencies in graph.")
        for circle in self.circular_deps:
            self.all_circular_deps |= circle


    def build_ord_gen(self):
        '''
        Iterates over num_of_deps and build package that have all deps
        satisfied
        '''
        while self.packages > self.built_packages:
            for num in sorted(self.num_of_deps.keys()):
                if num == 0:
                    continue
                for package in self.num_of_deps[num]:
                    if package not in self.built_packages and self.deps_satisfied(package):
                        yield (package, False)
 
    def build_ord_recipe_gen(self):
        '''
        Iterates over num_of_deps, building circular_deps using recipes
        '''
        while self.packages > self.built_packages:
            for num in sorted(self.num_of_deps.keys()):
                if num == 0:
                    continue
                for pkg in self.num_of_deps[num]:
                    if pkg in self.built_packages:
                        continue
                    if pkg in self.all_circular_deps and\
                        self.recipe_deps_satisfied(self.find_recipe(pkg)):
                        yield (pkg, True)
                    elif self.deps_satisfied(pkg):
                        yield (pkg, False)

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
    def build(self, package, verbose=True):
        if verbose:
            print("Building {0}...".format(package))
        return True


    def run_building(self):
        '''
        First builds all packages without deps, then iterates over num_of_deps
        and simulate building of packages in right order
        '''

        # Build and add metapackage to chroots when rebuilding scl
        if hasattr(self, 'metapackage'):
            self.build(self.metapackage)
            self.add_chroot_pkg([metapackage])

        if not self.num_of_deps:
            print("Nothing to build")
            return

        # Builds all packages without deps
        if 0 in self.num_of_deps.keys():
            for package in self.num_of_deps[0]:
                self.build(package)

        if self.recipes:
            build_ord_generator = self.build_ord_recipe_gen
        else:
            build_ord_generator = self.build_ord_gen

        for pkg, recipe in build_ord_generator():
            if recipe:
                self.build_following_recipe(self.find_recipe(pkg))
            else:
                self.build(pkg)

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
                utils.check_bootstrap_macro(self.pkg_source[name].spec_file, macro)
                utils.edit_bootstrap(self.pkg_source[name].spec_file, macro, value)
                self.pkg_source[name].pack()
            self.build(step[0], False)
 
#TODO move to PkgsContainer ?
    def get_files(self):
        '''
        Creates SrpmArchive object and downloads files for each package
        '''
        with utils.ChangeDir(self.path):
            for package in self.packages:
                pkg_dir = self.path + package
                if not os.path.exists(pkg_dir):
                    os.mkdir(pkg_dir)
                print("Getting files of {0}.".format(package))
                self.pkg_source.add(package, pkg_dir, self.repo, self.prefix)
