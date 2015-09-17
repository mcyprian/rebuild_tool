import networkx as nx
import matplotlib.pyplot as plt
import locale
from subprocess import Popen, PIPE

from sclbuilder.exceptions import UnknownRepoException

class PackageGraph(object):
    def __init__(self, packages, repo):
        self.packages = packages
        self.repo = repo
        self.graph = nx.MultiDiGraph()
        self.processed_packages = set()
        self.built_packages = set()
        self.num_of_deps = {}
        self.circular_deps = []

    def make_graph(self):
        '''
        Process all the packages, finds their dependancies and makes graph of
        relations
        '''
        for package in self.packages:
            self.process_deps(package)

    def show_graph(self):
        '''
        Draws nodes, edges, labels and shows graph
        '''
        try:
            pos = nx.graphviz_layout(self.graph)
        except (ImportError, AttributeError):
            pos = nx.circular_layout(self.graph)
        nx.set_node_attributes(self.graph, 'pos', pos)
        nx.draw(self.graph, pos, node_size=10000, with_labels=True, node_color="#CDE0F0")
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

    def plan_building_order(self):
        '''
        creates dictionary of packages , keys of the dictionaty are
        numbers of dependancies, values are names of the packages,
        packages with circular dependancies are stored in special set
        '''
        for node in self.graph.nodes():
            circular = set(self.graph.successors(node)) & set(self.graph.predecessors(node))
            if circular:
                new_set = circular | {node}
                if not new_set in self.circular_deps:
                    self.circular_deps.append(new_set)
            else:
                update_dict(self.num_of_deps, len(self.graph.successors(node)), node)

        print("\nTo build:")
        for num in sorted(self.num_of_deps.keys()):
            print("deps {}   {}".format(num, self.num_of_deps[num]))
        print("circular dependancy: {}".format(self.circular_deps))

    def run_building(self):
        '''
        Simulate building of packages in right order, first builds all packages
        with no deps,
        than iterate over others and builds packages which have satisfied all their deps
        '''
        if not self.num_of_deps:
            print("Nothing to build")
            return
        
        all_packages = set()
        for node in self.graph.nodes():
            all_packages.add(node)
        
        if 0 in self.num_of_deps.keys():
            for package in self.num_of_deps[0]:      # First we build package with no deps
                self.build(package)

        self.all_circular_deps = set()
        for circle in self.circular_deps:
            self.all_circular_deps |= circle
        packages_to_build = all_packages - self.all_circular_deps   # circular deps
        while packages_to_build != self.built_packages:
            for num in sorted(self.num_of_deps.keys()):
                if num == 0:
                    continue
                for package in self.num_of_deps[num]:
                    if package not in self.built_packages and self.deps_satisfied(package):
                       self.build(package)

    def get_deps(self, package):
        '''
        Returns all dependancies of the package found in selected repo
        '''
        proc = Popen(["dnf", "repoquery", "--arch=src", "--disablerepo=*",
                      "--enablerepo=" + self.repo, "--requires", package], stdout=PIPE, stderr=PIPE)
        stream_data = proc.communicate()
        if proc.returncode:
            if stream_data[1].decode(locale.getpreferredencoding()) ==\
                "Error: Unknown repo: '{0}'\n".format(self.repo):
                raise UnknownRepoException('Repository {} is probably disabled'.format(self.repo))
        all_deps = set(stream_data[0].decode(locale.getpreferredencoding()).splitlines()[1:])
        return all_deps & self.packages



    def deps_satisfied(self, package):
        '''
        Compares package deps with self.build_packages to
        check if are all dependancies already built
        '''
        if (set(self.graph.successors(package)) - self.all_circular_deps) <= self.built_packages:
            return True         # TODO resolve circular deps
        return False

    def build(self, package):
        print("Building package {}.... DONE".format(package))
        self.built_packages.add(package)


def update_dict(dictionary, key, value):
    if key in dictionary.keys():
        dictionary[key].append(value)
    else:
        dictionary[key] = [value]

def base_name(name):
    '''
    Removes version and parentheses from package name if present
    foo >= 1.0  >>>  foo
    foo(64bit)  >>>  foo
    '''
    if '(' in name:
        name = name.split('(')[0]
    if '>' in name:
        name = name.split('>')[0]
    return name
