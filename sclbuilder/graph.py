import networkx as nx
import matplotlib.pyplot as plt
import locale
from subprocess import Popen, PIPE

import sclbuilder.settings
from sclbuilder.exceptions import UnknownRepoException

class PackageGraph(object):
    def __init__(self, repo):
        self.repo = repo
        self.G = nx.MultiDiGraph()
        self.processed_packages = set()
        self.built_packages = set()

    def show_graph(self):
        '''
        Draws nodes, edges, labels and shows graph
        '''
        try: 
            pos = nx.graphviz_layout(self.G)
        except (ImportError, AttributeError):
            pos = nx.circular_layout(self.G)
        nx.set_node_attributes(self.G, 'pos', pos)
        nx.draw(self.G, pos, node_size=10000, with_labels=True, node_color="#CDE0F0")
        plt.show()
     
    def process_deps(self, package, recursive=True):
        '''
        Adds edge between package and each of its dependancies, if 
        pacakge was not processes before. When recursive is True
        calls itself for each dependance.
        '''
        if package in self.processed_packages:
            return
        else:
            print(package)
            self.G.add_node(package)
            self.processed_packages.add(package)
            for dep in get_deps(package, self.repo):
                self.G.add_edge(package, dep)
                if recursive:
                    self.process_deps(dep)

    def plan_building_order(self):
        '''
        creates dictionary of packages , keys of the dictionaty are
        numbers of dependancies, values are names of the packages, 
        packages with circular dependancies are stored in special set
        '''
        self.num_of_deps = {}
        self.circular_deps = set()
        for node in self.G.nodes():
            if set(self.G.successors(node)) & set(self.G.predecessors(node)):
                self.circular_deps.add(node)
            else:
                update_dict(self.num_of_deps, len(self.G.successors(node)), node)

        print("\nTo build:")
        for num in sorted(self.num_of_deps.keys()):
            print("deps {}   {}".format(num, self.num_of_deps[num]))
        print("circular dependancy: {}".format(self.circular_deps))
    
    def run_building(self):
        '''
        Simulate building of packages in right order, first builds all packages with no deps, 
        than iterate over others and builds packages which have satisfied all their deps
        '''
        if not self.num_of_deps:
            print("Nothing to build")
            return
        for package in self.num_of_deps[0]:      # First we build package with no deps
            self.build(package)
        all_packages = set()
        for node in self.G.nodes():
            all_packages.add(node)

        packages_to_build =  all_packages - self.circular_deps
        while packages_to_build != self.built_packages:
            for num in sorted(self.num_of_deps.keys())[1:]:
                for package in self.num_of_deps[num]:
                    if package not in self.built_packages and self.deps_satisfied(package):
                        self.build(package)

    def deps_satisfied(self, package):
        '''
        Compares package deps with self.build_packages to
        check if are all dependancies already built
        '''
        if (set(self.G.successors(package)) - self.circular_deps) <= self.built_packages:
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

def get_deps(package, repo):
    '''
    Returns all dependancies of the package found in selected repo
    '''
    proc = Popen(["dnf", "repoquery", "--arch=src", "--disablerepo=*", 
        "--enablerepo=" + repo, "--requires", package], stdout=PIPE, stderr=PIPE)
    stream_data = proc.communicate()
    if proc.returncode:
        if stream_data[1].decode(locale.getpreferredencoding()) ==\
                "Error: Unknown repo: '{0}'\n".format(repo):
                    raise UnknownRepoException('Repository {} is probably disabled'.format(repo))
    return stream_data[0].decode(locale.getpreferredencoding()).splitlines()[1:]

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
