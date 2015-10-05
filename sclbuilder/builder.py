import os
from abc import ABCMeta
from subprocess import CalledProcessError

from sclbuilder.graph import PackageGraph
from sclbuilder.recipe import Recipe
from sclbuilder.srpm_archive import SrpmArchive
from sclbuilder.utils import change_dir, subprocess_popen_call
from sclbuilder.exceptions import MissingRecipeException

class Builder(metaclass=ABCMeta):
    '''
    Abstract superclass of builder classes.
    '''
    def __init__(self, path, repo, packages, recipe_files = None):
        self.packages = packages
        self.repo = repo
        self.path = path
        self.built_packages = set()
        self.graph = PackageGraph(repo, self.packages)
        self.num_of_deps = {}
        self.circular_deps = []
        self.all_circular_deps  = set()
        try:
            self.recipes = recipe_files
        except IOError:
            print("Failed to load recipe {0}.".format(recipe))

    @property
    def path(self):
        return self.__path

    @path.setter
    def path(self, value):
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


    def num_of_deps_iter(self):
        '''
        Iterates over num_of_deps and build package that have all deps
        satisfied
        '''
        for num in sorted(self.num_of_deps.keys()):
            if num == 0:
                continue
            for package in self.num_of_deps[num]:
                if package not in self.built_packages and self.deps_satisfied(package):
                    self.build(package)

    def num_of_deps_recipe_iter(self):
        '''
        Iterates over num_of_deps, building circular_deps using recipes
        '''
        for num in sorted(self.num_of_deps.keys()):
            if num == 0:
                continue
            for package in self.num_of_deps[num]:
                if package in self.built_packages:
                    continue
                if package in self.all_circular_deps:
                    self.build_following_recipe(self.find_recipe(package))
                elif self.deps_satisfied(package):
                   self.build(package)

    def deps_satisfied(self, package):
        '''
        Compares package deps with self.build_packages to
        check if are all dependancies already built
        '''
        if set(self.graph.G.successors(package)) <= self.built_packages:
            return True
        return False

    def build(self, package):
        self.built_packages.add(package)
        print("Building {0}...".format(package))
    
    def run_building(self):
        '''
        First builds all packages without deps, then iterates over num_of_deps
        and simulate building of packages in right order
        '''
        if not self.num_of_deps:
            print("Nothing to build")
            return
        
        # Builds all packages without deps
        if 0 in self.num_of_deps.keys():
            for package in self.num_of_deps[0]:
                self.build(package)

        if self.recipes:
            iter_fce = self.num_of_deps_recipe_iter
        else:
            iter_fce = self.num_of_deps_iter

        while self.packages > self.built_packages:
            iter_fce()

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
        Builds packages in order and variables values discribed in given
        recipe
        '''
        for step in recipe.order:
            if len(step) == 1:
                print("Building package {0}".format(step[0]))
            else:
                print("Building package {0} {1}".format(step[0], step[1])) 
            self.built_packages.add(step[0])


class CoprBuilder(Builder):
    '''
    Contians methods to rebuild packages in Copr
    '''
    def __init__(self, path, repo, packages, recipe_files=None):
        super(self.__class__, self).__init__(path, repo, packages, recipe_files)
        self.pkg_files = {}
        self.rpm_dict = {}
        self.make_rpm_dict()

    def get_files(self):
        '''
        Creates SrpmArchive object and downloads files for each package
        '''
        with change_dir(self.path):
            for package in self.packages:
                pkg_dir = self.path + package
                if not os.path.exists(pkg_dir):
                    os.mkdir(pkg_dir)
                self.pkg_files[package] = SrpmArchive(pkg_dir, package, self.repo)
                print("Getting files of {0}.".format(package))
                self.pkg_files[package].get()
    
    def make_rpm_dict(self):
        '''
        Makes dictionary of rpms created from srpm of each package.
        '''
        if not self.pkg_files:
            self.get_files()
        for package in self.packages:
            self.rpm_dict[package] = get_rpms(self.pkg_files[package].spec_file)


    def build(self, package):
        self.built_packages.add(package)
        print("Building {0}...".format(package))


def get_rpms(spec_file):
    '''
    Returns list of rpms created from spec_file
    '''
    proc_data = subprocess_popen_call(["rpm", "-q", "--specfile", spec_file])
    if proc_data['returncode']:
        raise CalledProcessError(cmd='rpm', returncode=proc_data['returncode'])
    rpms =  proc_data['stdout'].splitlines()
    return ['-'.join(x.split('-')[:2]) for x in rpms]      #TODO regex
