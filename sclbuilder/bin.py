import sys
import click
import importlib
from copr.client.exceptions import CoprNoConfException

from sclbuilder import settings
from sclbuilder.recipe import get_file_data, RebuildMetadata
from sclbuilder.exceptions import UnknownRepoException, IncompleteMetadataException


CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])

def load_plugin(name):
    return importlib.import_module('sclbuilder.builder_plugins.' + name)

@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument('rebuild_file', nargs=1)
@click.option('--visual / --no-visual',
              default=True,
              help='Enable / disable visualization of relations between pacakges')

def main(rebuild_file, visual):
    try:
            rebuild_metadata = RebuildMetadata(get_file_data(rebuild_file))
    except IOError:
        print('No such file or directory: {}'.format(rebuild_file))
        sys.exit(1)
    except IncompleteMetadataException:
        print('Missing metadata needed for rebuild') # TODO tell which attribute is missing
        sys.exit(1)
    
    # Import of set builder module
    builder_module = load_plugin(rebuild_metadata.data['build_system'])

    try:
        builder = builder_module.RealBuilder(rebuild_metadata)
        builder.get_relations()
    except UnknownRepoException:
        print('Repository {} is probably disabled'.format(rebuild_metadata.data['repo']))
        sys.exit(1)
    except CoprNoConfException:
        print('Copr configuration file: ~/.config/copr not found')
        sys.exit(1)
    builder.run_building()
    if visual:
        builder.graph.show()
