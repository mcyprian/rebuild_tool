import locale
from subprocess import Popen, PIPE, CalledProcessError
from collections import UserDict

import sclbuilder.exceptions as ex
from sclbuilder.pkg_source import PkgSrcArchive, set_class_attrs
from sclbuilder.utils import subprocess_popen_call, ChangeDir

class PkgsContainer(UserDict):
    @set_class_attrs
    def add(self, package, pkg_dir):
        '''
        Adds new DnfArchive object to self.data
        '''
        self[package] = DnfArchive(package, pkg_dir)

class DnfArchive(PkgSrcArchive):
    '''
    Contains methods to download from dnf, unpack, edit and pack srpm
    '''
    @property
    def dependencies(self):
        '''
        Returns all dependencies of the package found in selected repo
        '''
        proc_data = subprocess_popen_call(["dnf", "repoquery", "--arch=src",
                                          "--disablerepo=*", "--enablerepo=" + type(self).repo, 
                                          "--requires", self.package])
        if proc_data['returncode']:
            if proc_data['stderr'] == "Error: Unknown repo: '{0}'\n".format(type(self).repo):
                raise ex.UnknownRepoException('Repository {} is probably disabled'.format(type(self).repo))
        all_deps = set(proc_data['stdout'].splitlines()[1:])
        return all_deps
    
    def download(self):
        '''
        Download srpm of package from selected repo using dnf.
        '''
        proc_data = subprocess_popen_call(["dnf", "download", "--disablerepo=*", 
                                           "--enablerepo=" + type(self).repo,
                                           "--destdir", self.pkg_dir,
                                           "--source", self.package])

        if proc_data['returncode']:
            if proc_data['stderr'] == "Error: Unknown repo: '{0}'\n".format(type(self).repo):
                raise ex.UnknownRepoException('Repository {} is probably disabled'.format(type(self).repo))
        elif proc_data['stderr']:
            raise ex.DownloadFailException(proc_data['stderr'])

        self.srpm_file = self.get_file('.src.rpm')

    def unpack(self):
        '''
        Unpacks srpm archive
        '''
        with ChangeDir(self.pkg_dir):
            p1 = Popen(["rpm2cpio", self.srpm_file], stdout=PIPE, stderr=PIPE)
            p2 = Popen(["cpio", "-idmv"], stdin=p1.stdout, stdout=PIPE, stderr=PIPE)
            stream_data = p2.communicate()
            stderr_str = stream_data[1].decode(locale.getpreferredencoding())
            if p2.returncode:
                raise CalledProcessError(cmd='rpm2cpio', returncode=p2.returncode)
            self.spec_file = self.get_file('.spec') #TODO stderr to log

    def pack(self, save_dir=None):
        '''
        Builds a srpm  using rpmbuild.
        Generated srpm is stored in directory specified by save_dir."""
        '''
        if not save_dir:
            save_dir = self.pkg_dir
        try:
            msg = Popen(['rpmbuild',
                         '--define', '_sourcedir {0}'.format(save_dir),
                         '--define', '_builddir {0}'.format(save_dir),
                         '--define', '_srcrpmdir {0}'.format(save_dir),
                         '--define', '_rpmdir {0}'.format(save_dir),
                         '--define', 'scl_prefix {0}'.format(type(self).prefix),
                         '-bs', self.spec_file], stdout=PIPE,
                         stderr=PIPE).communicate()[0].strip()
        except OSError:
            print('Rpmbuild failed for specfile: {0} and save_dir: {1}'.format(
                self.spec_file, self.pkg_dir))
             #TODO log message
        self.srpm_file = self.get_file('.src.rpm')
    