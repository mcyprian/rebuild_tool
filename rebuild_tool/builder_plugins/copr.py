import time
import pprint
import logging
from copr.client import CoprClient

from rebuild_tool import builder
from rebuild_tool.exceptions import IncompleteMetadataException

logger = logging.getLogger(__name__)

def check_metadata(rebuild_metadata):
    '''
    Checks if rebuild_metadata dictionary has all necesary
    attributes for work with Copr build system
    '''
    for attr in ['copr_project', 'chroots']:
        if attr not in rebuild_metadata:
            raise IncompleteMetadataException(
                "Missing Rebuild file attribute: {} necessary for Copr builds.".format(attr))


class RealBuilder(builder.Builder):
    '''
    Contains methods to rebuild packages in Copr
    '''
    def __init__(self, rebuild_metadata, pkg_source):
        super(self.__class__, self).__init__(rebuild_metadata, pkg_source)
        self.cl = CoprClient.create_from_file_config()
        check_metadata(rebuild_metadata)
        self.project = rebuild_metadata['copr_project']
        self.chroots = rebuild_metadata['chroots']
        if self.project_is_new():
            self.cl.create_project(self.project, self.chroots)
        
        if 'chroot_pkgs' in rebuild_metadata:
            self.add_chroot_pkg(rebuild_metadata['chroot_pkgs'])


    def add_chroot_pkg(self, chroot_pkgs):
        '''
        Method to add packages to minimal buildroot
        '''
        if not isinstance(chroot_pkgs, list):
            chroot_pkgs = [chroot_pkgs]

        for chroot in self.chroots:
            self.cl.modify_project_chroot_details(self.project, chroot, pkgs=chroot_pkgs)

    def project_is_new(self):
        '''
        Checks if project already exists in Copr
        '''
        result = self.cl.get_projects_list().projects_list
        for proj in result:
            if proj.projectname == self.project:
                return False
        return True

    @builder.check_build
    def build(self, pkgs, verbose=True):
        '''
        Building package using copr api, periodicaly checking
        build status while build is not finished
        '''
        srpms = [self.pkg_source[x].full_path_srpm for x in pkgs]
        results = []

        if verbose:
            print("Building {}".format(pkgs))
        
        for pkg in srpms:
            results.append(self.cl.create_new_build(self.project, pkgs=[pkg],
                                                       chroots=self.chroots))
        watched = []
        for result in results:
            watched += result.builds_list

        watched = set(watched)
        done = {}

        while watched != set(done.keys()):
            for bw in watched - set(done.keys()):
                status = bw.handle.get_build_details().status
                if status in ["skipped", "failed", "succeeded"]:
                    done[bw] = status
            time.sleep(1)

        logger.debug(done)
        for status in done.values():
            if status != 'succeeded':
                return False
        return True
