import sys
import click

from sclbuilder.builder import CoprBuilder
from sclbuilder import settings
from sclbuilder.recipe import get_file_data
from sclbuilder.exceptions import UnknownRepoException


CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])

@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument('packages', nargs=-1)
@click.option('-f',
              help='List of packages in file instead of arguments, newline is'
              ' a delimiter.',
              default=None,
              metavar='FILE')
@click.option('-r',
              help='Repo to search dependancies of the Packages (default: "{0}")'.format(
              settings.DEFAULT_REPO),
              default=settings.DEFAULT_REPO,
              metavar='REPO')
@click.option('--recipes',
             help='File carrying recipes of circular dependancy packages building',
             default=None,
             metavar='FILE')
@click.option('--visual / --no-visual',
              default=True,
              help='Enable / disable visualization of relations between pacakges')

def main(visual, recipes, r, f, packages):
    try:
        if f:
            packages = get_file_data(f, split=True)
        if recipes:
            recipe_files = get_file_data(recipes, split=True)
        else:
            recipe_files = None
    except IOError:
        print('No such file or directory: {}'.format(f))
        sys.exit(1)
    
    
    builder = CoprBuilder('/tmp/', r, set(packages), recipe_files)
    try:
        builder.get_relations()
    except UnknownRepoException:
        print('Repository {} is probably disabled'.format(r))
        sys.exit(1)
    builder.run_building()
    if visual:
        builder.graph.show()
