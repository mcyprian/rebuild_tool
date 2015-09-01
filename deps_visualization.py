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

    def add_package(self, name):
        self.G.add_node(self.ord_num)
        self.G.node[self.ord_num]['name'] = name
        self.ord_num += 1
        return self.ord_num - 1
    
    def find_package(self, package):
        for node, data in self.G.nodes_iter(data=True):
            if data['name'] == package:
                return node
        return None

    def add_edge(self, from_package, to_package):
        p1 = self.find_package(from_package)
        p2 = self.find_package(to_package)
        if p1 == None:
            p1 = self.add_package(from_package)
        if p2 == None:
            p2 = self.add_package(to_package)
        self.G.add_edge(p1, p2)

    def show_graph(self):
        pos = nx.circular_layout(self.G)
        node_labels = nx.get_node_attributes(self.G, 'name')
        nx.set_node_attributes(self.G, 'pos', pos)
        nx.draw(self.G, pos, node_size=10000, node_color="#CDE0F0")
        nx.draw_networkx_edges(self.G, pos, alpha=0.4, node_size=10000, arrows=True)
        nx.draw_networkx_labels(self.G, pos, labels = node_labels)
        plt.show()
     
    def process_deps(self, package):
        if package in self.processed_packages:
            return
        else:
            print(package)
            print(self.processed_packages)
            self.processed_packages.add(package)
            for dep in get_deps(package):
                self.add_edge(package, dep)
                self.process_deps(dep)


def get_deps(package):
    proc = Popen(["dnf", "repoquery", "--requires", package], stdout=PIPE)
    stream_data = proc.communicate()
    return deps_filter(stream_data[0].decode(locale.getpreferredencoding()).splitlines()[1:])

def base_name(name):
    if '(' in name:
        name = name.split('(')[0]
    if '>' in name:
        name = name.split('>')[0]
    return name

def deps_filter(deps_list):
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
        G.process_deps(package)

    G.show_graph()

if __name__ == '__main__':
    main()
