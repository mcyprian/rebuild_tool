import yaml

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

class Recipe(yaml.YAMLObject):
    '''
    Class to store order of building recipe, reads data from
    yml file in format:
        - ['package1', with_var n]
        - ['package2']
        - ['package1', 'with_var n']
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
        Fills packages set with all packages names present in 
        recipe
        '''
        if not hasattr(self, 'order'):
            return
        for item in self.order:
            self.packages.add(item[0])



        
