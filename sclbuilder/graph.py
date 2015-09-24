import networkx as nx
import matplotlib.pyplot as plt
import itertools

from sclbuilder.recipe import Recipe
from sclbuilder.utils import subprocess_popen_call
import sclbuilder.exceptions as ex

class PackageGraph(object):
    '''
    Class to make graph of packages, analyse dependancies and
    plan building order
    '''
    def __init__(self, packages, repo):
        self.packages = packages
        self.repo = repo
        self.graph = nx.DiGraph()
        self.processed_packages = set()
        self.built_packages = set()
        self.num_of_deps = {}
        self.circular_deps = []

    def make_graph(self):
        '''
        Process all the packages, finds theirs dependancies and makes 
        graph of relations
        '''
        print("Processing package:")
        for package in self.packages:
            self.process_deps(package)

    def show_graph(self):
        '''
        Draws nodes, edges, labels and shows the graph
        '''
        try:
            pos = nx.graphviz_layout(self.graph)
        except (ImportError, AttributeError):
            pos = nx.circular_layout(self.graph)
        nx.set_node_attributes(self.graph, 'pos', pos)
        nx.draw(self.graph, pos, node_size=12000, with_labels=True,
                node_color="#1F9EDE", alpha=0.9)
        plt.show()

    def process_deps(self, package, recursive=False):
        '''
        Adds edge between package and each of its dependancies,
        pacakge was not processes before. When recursive is True
        calls itself for each dependance.
        '''
        if package in self.processed_packages:
            return
        else:
            print(package)
            self.graph.add_node(package)
            self.processed_packages.add(package)
            for dep in self.get_deps(package):
                self.graph.add_edge(package, dep)
                if recursive:
                    self.process_deps(dep)

    def get_deps(self, package):
        '''
        Returns all dependancies of the package found in selected repo
        '''
        proc_data = subprocess_popen_call(["dnf", "repoquery", "--arch=src", 
            "--disablerepo=*", "--enablerepo=" + self.repo, "--requires", package])
        if proc_data['returncode']:
            if proc_data['stderr'] == "Error: Unknown repo: '{0}'\n".format(self.repo):
                raise ex.UnknownRepoException('Repository {} is probably disabled'.format(self.repo))
        all_deps = set(proc_data['stdout'].splitlines()[1:])
        return all_deps & self.packages


    def plan_building_order(self):
        '''
        Creates dictionary of packages , keys of the dictionaty are
        numbers of dependancies, values are names of the packages,
        packages with circular dependancies are stored in special set
        '''
        for node in self.graph.nodes():
            update_key(self.num_of_deps, len(self.graph.successors(node)), node)
        
        self.circular_deps = [set(x) for x in nx.simple_cycles(self.graph)]
        if self.circular_deps:
            raise ex.CircularDepsException("Can't resolve circular dependencies without recipes")

        print("\nPackages to build:")
        for num in sorted(self.num_of_deps.keys()):
            print("deps {}   {}".format(num, self.num_of_deps[num]))

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

        while self.packages > self.built_packages:
            self.num_of_deps_iter()
            
    def num_of_deps_iter(self):
        for num in sorted(self.num_of_deps.keys()):
            if num == 0:
                continue
            for package in self.num_of_deps[num]:
                if package not in self.built_packages and self.deps_satisfied(package):
                    self.build(package)
    
    def deps_satisfied(self, package):
        '''
        Compares package deps with self.build_packages to
        check if are all dependancies already built
        '''
        if set(self.graph.successors(package)) <= self.built_packages:
            return True
        return False

    def build(self, package):
        print("Building package {0}".format(package))
        self.built_packages.add(package)


class PackageRecipesGraph(PackageGraph):
    '''
    Package graph using recipes to resolve circular dependency
    build order
    '''
    def __init__(self, packages, repo, recipe_files):
        super(self.__class__, self).__init__(packages, repo)
        self.recipes = []
        try:
            for recipe in recipe_files:
                self.recipes.append(Recipe(recipe))
        except IOError:
            print("Failed to load recipe {0}.".format(recipe))

    def plan_building_order(self):
        '''
        Creates dictionary of packages, keys of the dictionaty are
        numbers of dependancies, values are names of the packages,
        packages with circular dependancies are stored in special set
        '''
        for node in self.graph.nodes():
            update_key(self.num_of_deps, len(self.graph.successors(node)), node)
        
        self.circular_deps = [set(x) for x in nx.simple_cycles(self.graph)]
        print(self.circular_deps)

        self.all_circular_deps = set()
        for circle in self.circular_deps:
            self.all_circular_deps |= circle

        # Removes subsets of other sets in self.circular_deps
        for a, b in itertools.combinations(self.circular_deps, 2):
            if a <= b:
                remove_if_present(self.circular_deps, a)
            elif b <= a:
                remove_if_present(self.circular_deps, b)

        print("\nPackages to build:")
        for num in sorted(self.num_of_deps.keys()):
            print("deps {}   {}".format(num, self.num_of_deps[num]))
        print("\nCircular dependancies: {}\n".format(self.circular_deps))

    def num_of_deps_iter(self): 
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
 
    def find_recipe(self, package):
        '''
        Search for recipe including package in self.recipes
        '''
        for recipe in self.recipes:
            if package in recipe.packages:
                return recipe
        raise ex.MissingRecipeException("Recipe for package {0} not found".format(package))

    
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


def remove_if_present(ls, value):
    if value in ls:
        ls.remove(value)

def update_key(dictionary, key, value):
    if key in dictionary.keys():
        dictionary[key].append(value)
    else:
        dictionary[key] = [value]

def base_name(name):
    '''
    Removes version and parentheses from package name
    foo >= 1.0  >>  foo
    foo(64bit)  >>  foo
    '''
    if '(' in name:
        name = name.split('(')[0]
    if '>' in name:
        name = name.split('>')[0]
    return name
