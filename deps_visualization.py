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
        self.ord_num = 0
        self.processed_packages = set()
        self.built_packages = set()

    def add_package(self, name):
        '''
        Checks if node with label name already exists, if not adds new
        node and retutns its number
        '''
        exists = self.find_package(name)
        if exists:
            return exists
        self.G.add_node(self.ord_num)
        self.G.node[self.ord_num]['name'] = name
        self.ord_num += 1
        return self.ord_num - 1
    
    def find_package(self, name):
        '''
        Search for package with label given as argument name
        '''
        for node, data in self.G.nodes_iter(data=True):
            if data['name'] == name:
                return node
        return None

    def add_edge(self, from_package, to_package):
        '''
        Adds new edge, if some of packages doesn't exists
        creates it.
        '''
        p1 = self.find_package(from_package)
        p2 = self.find_package(to_package)
        if p1 == None:
            p1 = self.add_package(from_package)
        if p2 == None:
            p2 = self.add_package(to_package)
        self.G.add_edge(p1, p2)

    def show_graph(self):
        '''
        Draws nodes, edges, labels and shows graph
        '''
        pos = nx.circular_layout(self.G)
        node_labels = nx.get_node_attributes(self.G, 'name')
        nx.set_node_attributes(self.G, 'pos', pos)
        nx.draw(self.G, pos, node_size=10000, node_color="#CDE0F0")
        nx.draw_networkx_edges(self.G, pos, alpha=0.4, node_size=10000, arrows=True)
        nx.draw_networkx_labels(self.G, pos, labels = node_labels)
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

    def to_packages(self, nodes):
        '''
        Converts list of nodes number to list of packages names
        '''
        nodes_attr = nx.get_node_attributes(self.G, 'name')
        return [nodes_attr[x] for x in nodes] 

    def plan_building_order(self):
        self.to_build = {}
        circular_deps = []
        for node, data in self.G.nodes_iter(data=True):
            print("node {} data {}".format(node, data))
        for node in self.G.nodes():
            self.G[node]['deps'] = set(self.G.successors(node))
            if set(self.G.successors(node)) & set(self.G.predecessors(node)):
                circular_deps.append(node)
            else:
                update_dict(self.to_build, len(self.G.successors(node)), node)
        print("\nTo build:")
        for num in sorted(self.to_build.keys()):
            print("deps {}   {}".format(num, self.to_packages(self.to_build[num])))
        print("circular dependancy: {}".format(self.to_packages(circular_deps)))
    
    def build_packages(self):
        for node in self.G.nodes():
            print("{}   {}", node, self.G[node]['deps'])

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
    G = PackageGraph()
    for package in packages:
        G.process_deps(package, False)
    G.plan_building_order()
    G.build_packages()
   # G.show_graph()

if __name__ == '__main__':
    main()
