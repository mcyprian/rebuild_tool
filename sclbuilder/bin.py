import sys
import click

from sclbuilder import settings
from sclbuilder.graph import PackageGraph
from sclbuilder.exceptions import UnknownRepoException


CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])

@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument('packages', nargs=-1)
@click.option('-f',
              help='List of packages in file instead of arguments, newline is'
              ' a delimiter.',
              metavar='FILE')
@click.option('-r',
              help='Repo to search dependancies of the Packages (default: "{0}")'.format(
              settings.DEFAULT_REPO),
              default=settings.DEFAULT_REPO,
              metavar='REPO')
@click.option('--visual / --no-visual',
              default=True,
              help='Enable / disable visualization of relations between pacakges')

def main(visual, r, f, packages):
    if f:
        try:
            with open(f, 'r') as fi:
                packages = fi.read().splitlines()
        except FileNotFoundError:
            print('No such file or directory: {}'.format(f))

    pg = PackageGraph(set(packages), r)
    try:
        pg.make_graph()
    except UnknownRepoException:
        print('Repository {} is probably disabled'.format(r))
        sys.exit(1)
    pg.plan_building_order()
    pg.run_building()
    if visual:
        pg.show_graph()
