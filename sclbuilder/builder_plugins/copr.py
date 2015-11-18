import time
from copr.client import CoprClient
from copr.client.exceptions import CoprRequestException

from sclbuilder import builder
from sclbuilder.exceptions import BuildFailureException, IncompleteMetadataException


def check_metadata(rebuild_metadata):
    '''
    Checks if rebuild_metadata dictionary has all necesary
    attributes for work with Copr build system
    '''
    for attr in ['copr_project', 'chroots']:
        if attr not in rebuild_metadata:
            raise IncompleteMetadataException(
                "Missing attribute {} necessary for Copr builds.".format(attr))


class RealBuilder(builder.Builder):
    '''
    Contains methods to rebuild packages in Copr
    '''
    def __init__(self, rebuild_metadata, pkg_source):
        super(self.__class__, self).__init__(rebuild_metadata, pkg_source)
        self.cl = CoprClient.create_from_file_config()
        self.project = rebuild_metadata['copr_project']
        self.chroots = rebuild_metadata['chroots']
        self.pkg_source = rebuild_metadata['packages_source']
        if self.project_is_new():
            self.cl.create_project(self.project, self.chroots)
            # TODO try copr.client.exceptions.CoprRequestException: Unknown
            # arguments passed (non-existing chroot probably)


        if 'chroot_pkgs' in rebuild_metadata.data:
            for chroot in self.chroots:
                self.cl.modify_project_chroot_details(self.project,
                                                      chroot,
                                                      pkgs=rebuild_metadata.data['chroot_pkgs'])
        self.make_rpm_dict()
        print(self.rpm_dict)

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
    def build(self, package, verbose=True):
        '''
        Building package using copr api, periodicaly checking
        build status while build is not finished
        '''
        if verbose:
            print("Building {}".format(package))
        result = self.cl.create_new_build(self.project,
                                          pkgs=[self.pkg_files[package].srpm_file],
                                          chroots=self.chroots)

        while True:
            status = result.builds_list[0].handle.get_build_details().status
            if status in ["skipped", "failed", "succeeded"]:
                break
            time.sleep(10)
        if status == 'succeeded':
            return True
        else:
            return False
