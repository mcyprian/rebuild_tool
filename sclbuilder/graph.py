import networkx as nx
import matplotlib.pyplot as plt
import itertools

from sclbuilder.utils import subprocess_popen_call
import sclbuilder.exceptions as ex

class PackageGraph(object):
    '''
    Class to make graph of packages, analyse dependancies and
    plan building order
    '''
    def __init__(self, repo, packages, built_packages):
        self.repo = repo
        self.packages = packages
        self.processed_packages = set()
        self.built_packages = built_packages
        self.graph = nx.DiGraph()

    def make_graph(self):
        '''
        Process all the packages, finds theirs dependancies and makes 
        graph of relations
        '''
        print("Processing package:")
        for package in self.packages:
            self.process_deps(package)

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

    def deps_satisfied(self, package):
        '''
        Compares package deps with self.build_packages to
        check if are all dependancies already built
        '''
        if set(self.graph.successors(package)) <= self.built_packages:
            return True
        return False

    def analyse(self):
        '''
        Creates dictionary of packages, keys of the dictionaty are
        numbers of dependancies, values are names of the packages,
        packages with circular dependancies are stored in special set
        '''
        num_of_deps = {}
        for node in self.graph.nodes():
            update_key(num_of_deps, len(self.graph.successors(node)), node)
        
        circular_deps = [set(x) for x in nx.simple_cycles(self.graph)]
        print(circular_deps)

        # Removes subsets of other sets in circular_deps
        for a, b in itertools.combinations(circular_deps, 2):
            if a <= b:
                remove_if_present(circular_deps, a)
            elif b <= a:
                remove_if_present(circular_deps, b)

        print("\nPackages to build:")
        for num in sorted(num_of_deps.keys()):
            print("deps {}   {}".format(num, num_of_deps[num]))
        print("\nCircular dependancies: {}\n".format(circular_deps))
        return (num_of_deps, circular_deps)
    
    def show(self):
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

def remove_if_present(ls, value):
    if value in ls:
        ls.remove(value)

def update_key(dictionary, key, value):
    if key in dictionary.keys():
        dictionary[key].append(value)
    else:
        dictionary[key] = [value]

