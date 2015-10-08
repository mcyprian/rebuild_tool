import os
import re
import time
from abc import ABCMeta
from subprocess import CalledProcessError
from copr.client import CoprClient

from sclbuilder import settings
from sclbuilder.graph import PackageGraph
from sclbuilder.recipe import Recipe
from sclbuilder.srpm_archive import SrpmArchive
from sclbuilder.utils import change_dir, subprocess_popen_call, edit_bootstrap
from sclbuilder.exceptions import MissingRecipeException

class Builder(object): # metaclass=ABCMeta python3
    '''
    Abstract superclass of builder classes.
    '''
    def __init__(self, path, repo, packages, recipe_files = None):
        self.packages = packages
        self.repo = repo
        self.rpm_dict = {}
        self.path = path
        self.built_packages = set()
        self.built_rpms = set()
        self.graph = PackageGraph(repo, self.packages, self.rpm_dict)
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


    def num_of_deps_iter(self):            # TODO rewrite as iterators
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
        self.built_rpms |= set(self.rpm_dict[package])
        print("Building {0}...".format(package))

    def run_building(self):                      # TODO threading flags?
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
                (macro, value) = step[1].split(' ')
                edit_bootstrap(self.pkg_files[step[0]].spec_file, macro, value)
                self.pkg_files[step[0]].pack()
            self.build(step[0], False)
        time.sleep(240)


class CoprBuilder(Builder):
    '''
    Contians methods to rebuild packages in Copr
    '''
    def __init__(self, path, repo, packages, project=settings.DEFAULT_COPR, 
            recipe_files=None):
        super(self.__class__, self).__init__(path, repo, packages, recipe_files)
        self.cl = CoprClient.create_from_file_config()
        self.pkg_files = {}
        self.make_rpm_dict()
        self.project = project

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

    def build(self, package, verbose=True):
        if verbose:
            print("Building {}".format(package))
        result = self.cl.create_new_build(self.project,
                pkgs=[self.pkg_files[package].srpm_file])
        self.built_packages.add(package)
        self.built_rpms |= set(self.rpm_dict[package])
        time.sleep(240)
 

def get_rpms(spec_file):
    '''
    Returns list of rpms created from spec_file
    '''
    rpm_pattern = re.compile("(^.*)-\d+.\d+.\d+.*$")
    proc_data = subprocess_popen_call(["rpm", "-q", "--specfile", "--define",
                                      "scl_prefix rh-python34-", spec_file])
    #TODO get prefix of scl
    if proc_data['returncode']:
        print(proc_data['stderr'])
        raise CalledProcessError(cmd='rpm', returncode=proc_data['returncode'])
    #TODO stderr to log
    rpms =  proc_data['stdout'].splitlines()
    return [rpm_pattern.search(x).groups()[0] for x in rpms]
