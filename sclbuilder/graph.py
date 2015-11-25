import networkx as nx
import matplotlib.pyplot as plt
import itertools
import pprint

from sclbuilder.utils import subprocess_popen_call
import sclbuilder.exceptions as ex

class PackageGraph(object):
    '''
    Class to make graph of packages, analyse dependancies and
    plan building order
    '''
    def __init__(self, repo, pkg_source):
        self.repo = repo
        self.rpms = set()
        self.pkg_source = pkg_source
        self.G = nx.DiGraph()

    def make_graph(self):
        '''
        Process all the packages, finds theirs dependancies and makes
        graph of relations
        '''
        for package in self.pkg_source.values():
            self.rpms |= package.rpms
        print("Processing package:")
        for package in self.pkg_source.keys():
            self.process_deps(package)


    def process_deps(self, package):
        '''
        Adds edge between package and each of its dependancies,
        pacakge was not processes before. When recursive is True
        calls itself for each of dependancies.
        '''
        print(package)
        self.G.add_node(package)
        for dep in self.pkg_source[package].dependencies & self.rpms:
            self.G.add_edge(package, self.find_package(dep))

    def get_cycles(self):
        '''
        Finds circular dependencies and returns set of all cycles
        '''
        cycles = [set(x) for x in nx.simple_cycles(self.G)]

        # Removes subsets of other sets in circular_deps
        for a, b in itertools.combinations(cycles, 2):
            if a > b:
                remove_if_present(cycles, b)
            elif b > a:
                remove_if_present(cycles, a)
        
        circular_deps = [x for n, x in enumerate(cycles) if x not in cycles[:n]]

        print("\nCircular dependancies: {}")
        pp = pprint.PrettyPrinter(depth=6)
        pp.pprint(circular_deps)
        return circular_deps

    def find_package(self, rpm):
        for package in self.pkg_source.keys():
            if rpm in self.pkg_source[package].rpms:
                return package
        print("NOT FOUND {}".format(rpm)) # TODO Handle exception if package not found

    def show(self):
        '''
        Draws nodes, edges, labels and shows the graph
        '''
        try:
            pos = nx.graphviz_layout(self.G)
        except (ImportError, AttributeError):
            pos = nx.circular_layout(self.G)
        nx.set_node_attributes(self.G, 'pos', pos)
        nx.draw(self.G, pos, node_size=12000, with_labels=True,
                node_color="#1F9EDE", alpha=0.9)
        plt.show()

    def get_leaf_nodes(self):
        '''
        Returns list of leaf nodes in graph
        '''
        return [x for x in self.G.nodes_iter() if self.G.out_degree(x) == 0]

def remove_if_present(ls, value):
    if value in ls:
        ls.remove(value)

def update_key(dictionary, key, value):
    if key in dictionary.keys():
        if not value in dictionary[key]:
            dictionary[key].append(value)
    else:
        dictionary[key] = [value]

