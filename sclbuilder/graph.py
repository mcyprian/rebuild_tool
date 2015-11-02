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
    def __init__(self, repo, packages, rpm_dict):
        self.repo = repo
        self.packages = packages
        self.rpms = set()
        self.rpm_dict = rpm_dict
        self.processed_packages = set()
        self.G = nx.DiGraph()

    def make_graph(self):
        '''
        Process all the packages, finds theirs dependancies and makes
        graph of relations
        '''
        for package in self.packages:
            self.rpms |= set(self.rpm_dict[package])
        print("Processing package:")
        for package in self.packages:
            self.process_deps(package)


    def process_deps(self, package):
        '''
        Adds edge between package and each of its dependancies,
        pacakge was not processes before. When recursive is True
        calls itself for each of dependancies.
        '''
        if package in self.processed_packages:
            return
        else:
            print(package)
            self.G.add_node(package)
            self.processed_packages.add(package)
            for dep in self.get_deps(package):
                self.G.add_edge(package, self.find_package(dep))

    def get_deps(self, package):
        '''
        Returns all dependancies of the package found in selected repo
        '''
        proc_data = subprocess_popen_call(["dnf", "repoquery", "--arch=src",
                                           "--enablerepo=" + self.repo, "--requires", package])
        if proc_data['returncode']:
            if proc_data['stderr'] == "Error: Unknown repo: '{0}'\n".format(self.repo):
                raise ex.UnknownRepoException('Repository {} is probably disabled'.format(self.repo))
        all_deps = set(proc_data['stdout'].splitlines()[1:])
        return all_deps & self.rpms

    def analyse(self):
        '''
        Creates dictionary of packages, keys of the dictionaty are
        numbers of dependancies, values are names of the packages,
        packages with circular dependancies are stored in special set
        '''
        num_of_deps = {}
        for node in self.G.nodes():
            print(node)
            update_key(num_of_deps, len(self.G.successors(node)), self.find_package(node))
        cycles = [set(x) for x in nx.simple_cycles(self.G)]

        # Removes subsets of other sets in circular_deps
        for a, b in itertools.combinations(cycles, 2):
            if a > b:
                remove_if_present(cycles, b)
            elif b > a:
                remove_if_present(cycles, a)
        print(cycles)
        circular_deps = [x for n, x in enumerate(cycles) if x not in cycles[:n]]

        print("\nPackages to build:")
        for num in sorted(num_of_deps.keys()):
            print("deps {}   {}".format(num, num_of_deps[num]))
        print("\nCircular dependancies: {}")
        pp = pprint.PrettyPrinter(depth=6)
        pp.pprint(circular_deps)
        return (num_of_deps, circular_deps)

    def find_package(self, rpm):
        for package in self.packages:
            if rpm in self.rpm_dict[package]:
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

def remove_if_present(ls, value):
    if value in ls:
        ls.remove(value)

def update_key(dictionary, key, value):
    if key in dictionary.keys():
        if not value in dictionary[key]:
            dictionary[key].append(value)
    else:
        dictionary[key] = [value]

