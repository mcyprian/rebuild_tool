import sys
import click

from sclbuilder import settings
from sclbuilder.graph import PackageGraph
from sclbuilder.exceptions import UnknownRepoException


CONTEXT_SETTINGS = dict(help_option_names = ['-h', '--help'])

@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument('packages', nargs=-1)
@click.option('-r',
            help='Repo to search dependancies of the Packages (default: "{0}")'.format(
            settings.DEFAULT_REPO),
            default=settings.DEFAULT_REPO,
            metavar='REPO')
@click.option('--visual / --no-visual',
             default=True,
             help='Enable / disable visualization of relations between pacakges')

def main(visual, r, packages):
    Graph = PackageGraph(r)
    try:
        for package in packages:
            Graph.process_deps(package, False)
    except UnknownRepoException:
        print('Repository {} is probably disabled'.format(r))
        sys.exit(1)
    Graph.plan_building_order()
    Graph.run_building()
    if visual:
        Graph.show_graph()
