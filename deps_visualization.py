#!/usr/bin/python3

import networkx as nx
import matplotlib.pyplot as plt
import click
import locale
import re
from subprocess import Popen, PIPE, DEVNULL


class PackageGraph(object):
    def __init__(self):
        self.G = nx.MultiDiGraph()
        self.processed_packages = set()
        self.built_packages = set()

    def add_package(self, name):
        '''
        Adds new node to graph
        '''
        self.G.add_node(name)
    
    def add_edge(self, from_package, to_package):
        '''
        Adds new edge, if some of packages doesn't exists
        creates it.
        '''
        self.G.add_edge(from_package, to_package)

    def show_graph(self):
        '''
        Draws nodes, edges, labels and shows graph
        '''
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
            print(self.processed_packages)
            self.processed_packages.add(package)
            for dep in get_deps(package):
                self.add_edge(package, dep)
                if not recursive:
                    deps_of_deps = get_deps(dep)
                    for dep_of_dep in deps_of_deps:
                        self.add_edge(dep, dep_of_dep)
                if recursive:
                    self.process_deps(dep)

    def plan_building_order(self):
        self.to_build = {}
        circular_deps = []
        for node in self.G.nodes():
            if set(self.G.successors(node)) & set(self.G.predecessors(node)):
                circular_deps.append(node)
            else:
                update_dict(self.to_build, len(self.G.successors(node)), node)

        print("\nTo build:")
        for num in sorted(self.to_build.keys()):
            print("deps {}   {}".format(num, self.to_build[num]))
        print("circular dependancy: {}".format(circular_deps))
    


def update_dict(dictionary, key, value):
    if key in dictionary.keys():
        dictionary[key].append(value)
    else:
        dictionary[key] = [value]

def get_deps(package):
    '''
    Returns all dependancies of the package
    '''
    proc = Popen(["dnf", "repoquery", "--requires", package], stdout=PIPE)
    stream_data = proc.communicate()
    return deps_filter(stream_data[0].decode(locale.getpreferredencoding()).splitlines()[1:])

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

def deps_filter(deps_list):
    '''
    Removes libraries and other unwanted files from dependancies
    '''
    rules = ['^lib', '^rtld', '^/bin', '^/sbin', '^/usr', '^glibc']
    true_deps = set()
    for name in deps_list:
        name = base_name(name)
        search = False
        for rule in rules:
            if re.search(rule, name):
                search = True
        if not search:
            true_deps.add(name)
    return list(true_deps)

@click.command()
@click.argument('packages', nargs=-1)

def main(packages):
    Graph = PackageGraph()
    for package in packages:
        Graph.process_deps(package, False)
    Graph.plan_building_order()
    Graph.show_graph()

if __name__ == '__main__':
    main()
