import yaml

class Recipe(yaml.YAMLObject):
    yaml_tag = u'!Recipe'
    def __init__(self, recipe_file):
        self.packages = set()
        self.order = recipe_file
        self.get_packages()

    @property
    def order(self):
        return self.__order

    @order.setter
    def order(self, recipe_file):
        with open(recipe_file, 'r') as rf:
            self.__order = yaml.load(rf.read())

    def get_packages(self):
        if not hasattr(self, 'order'):
            return
        for item in self.order:
            self.packages.add(item[0])



        
