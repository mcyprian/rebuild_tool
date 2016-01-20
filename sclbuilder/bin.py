import sys
import click
import logging
import getpass
import threading
from copr.client.exceptions import CoprNoConfException, CoprRequestException

from sclbuilder.rebuild_metadata import get_file_data, RebuildMetadata
from sclbuilder.builder_plugins import builder_loader
from sclbuilder.pkg_source_plugins import pkg_source_loader
from sclbuilder.logger import register_file_log_handler
import sclbuilder.exceptions as exc


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
    except (exc.IncompleteMetadataException, exc.UnknownPluginException, IOError) as e:
        logger.error('Failed and exiting:', exc_info=True)
        logger.info('Rebuild failed.')
        sys.exit(e)

    # Import of selected builder module
    builder_module = builder_loader.load_plugin(rebuild_metadata['build_system'])
    logger.info("Builder plugin {} loaded.".format(builder_module))

    # Import selected pkg_source module and create Container object
    pkg_source_module = pkg_source_loader.load_plugin(rebuild_metadata['packages_source'])
    pkg_source = pkg_source_module.PkgsContainer()
    logger.info("Package source plugin {} loaded.".format(pkg_source_module))

    try:
        builder = builder_module.RealBuilder(rebuild_metadata, pkg_source)
        builder.get_relations()
    except (exc.UnknownRepoException, exc.IncompleteMetadataException, 
            exc.MissingRecipeException) as e:
        logger.error('Failed and exiting:', exc_info=True)
        logger.info('Rebuild failed.')
        sys.exit(e)
    except CoprNoConfException:
        print("Copr config file ~/.config/copr is missing.", file=sys.stderr)
        sys.exit(1)
   
    try:
        if analyse:
            builder.graph.show()

        elif visual:
            t = threading.Thread(target=builder.run_building)
            t.start()
            builder.graph.show()
        
        else:
            builder.run_building()
            logger.info("Rebuild successfully completed.")
    except (KeyError, CoprRequestException) as e:
        logger.error('Failed and exiting:', exc_info=True)
        logger.info('Rebuild failed.')
        sys.exit(e)
