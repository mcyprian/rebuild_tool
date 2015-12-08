import sys
import click
import logging
import getpass
from copr.client.exceptions import CoprNoConfException

from sclbuilder.rebuild_metadata import get_file_data, RebuildMetadata
from sclbuilder.exceptions import UnknownRepoException, IncompleteMetadataException
from sclbuilder.builder_plugins import builder_loader
from sclbuilder.pkg_source_plugins import pkg_source_loader
from sclbuilder.logger import register_file_log_handler


CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])

@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument('rebuild_file', nargs=1)
@click.option('--visual / --no-visual',
              default=False,
              help='Enable / disable visualization of relations between pacakges')
@click.option('--analyse',
              is_flag=True,
              help='Analyse relations between packages and print circular '
              'dependencies, disable execution of builds')

def main(rebuild_file, visual, analyse):
    register_file_log_handler('/tmp/sclbulider-{0}.log'.format(getpass.getuser()))

    logger = logging.getLogger(__name__)

    logger.info('Sclbuilder initialized')

    try:
        rebuild_metadata = RebuildMetadata(get_file_data(rebuild_file))
    except IOError:
        print('No such file or directory: {}'.format(rebuild_file))
        sys.exit(1)
    except IncompleteMetadataException:
        print('Missing metadata needed for rebuild') # TODO tell user which attribute is missing
        sys.exit(1)

    # TODO catch KeyError
    # Import of selected builder module
    builder_module = builder_loader.load_plugin(rebuild_metadata['build_system'])
    logger.info("Builder plugin {0} loaded.".format(builder_module))
    # Import selected pkg_source module and create Container object
    pkg_source_module = pkg_source_loader.load_plugin(rebuild_metadata['packages_source'])
    pkg_source = pkg_source_module.PkgsContainer()
    logger.info("Package source plugin {0} loaded.".format(pkg_source_module))

    try:
        builder = builder_module.RealBuilder(rebuild_metadata, pkg_source)
        builder.get_relations()
    except UnknownRepoException:
        print('Repository {} is probably disabled'.format(rebuild_metadata.data['repo']))
        sys.exit(1)
    except CoprNoConfException:
        print('Copr configuration file: ~/.config/copr not found')
        sys.exit(1)
    if visual or analyse:
        builder.graph.show()
    if not analyse:
        builder.run_building()
