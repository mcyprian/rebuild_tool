from sclbuilder.graph import PackageGraph
from sclbuilder.recipe import Recipe
from sclbuilder.exceptions import MissingRecipeException

class CoprBuilder(object):
    '''
    Class containing methods to rebuild software collection in Copr.
    '''
    def __init__(self, repo, packages, recipe_files = None):
        self.packages = packages
        self.built_packages = set()
        self.graph = PackageGraph(repo, self.packages, self.built_packages)
        self.num_of_deps = {}
        self.circular_deps = []
        self.all_circular_deps  = set()
        if recipe_files:
            try:
                self.recipes = recipe_files
            except IOError:
                print("Failed to load recipe {0}.".format(recipe))

    @property
    def recipes(self):
        return self._recipes

    @recipes.setter
    def recipes(self, recipe_files):
        self._recipes = []
        for recipe in recipe_files:
            self._recipes.append(Recipe(recipe))

    def get_relations(self):
        '''
        Runs graph analysis and get dependance tree and circular_deps
        '''
        self.graph.make_graph()
        (self.num_of_deps, self.circular_deps) = self.graph.analyse()
        if self.circular_deps and not self.recipes:
            raise ex.MissingRecipeException("Missing recipes to resolve circular dependencies in graph.")
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
                elif self.graph.deps_satisfied(package):
                   self.build(package)


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

    def build(self, package):
        print("Building package {0}".format(package))
        self.built_packages.add(package)

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

