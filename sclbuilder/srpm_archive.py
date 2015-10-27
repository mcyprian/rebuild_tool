import locale
import glob
import os
from subprocess import Popen, PIPE, CalledProcessError
from collections import UserDict

import sclbuilder.exceptions as ex
from sclbuilder import settings
from sclbuilder.utils import subprocess_popen_call, change_dir

class ArchiveContainer(UserDict):
    def add(self, package, pkg_dir, repo):
        '''
        Adds new SrpmArchive object to self.data
        '''
        self.data[package] = SrpmArchive(package, pkg_dir, repo)

class SrpmArchive(object):
    '''
    Contains methods to download, unpack, edit and pack srpm
    '''
    def __init__(self, package, pkg_dir, repo, srpm_file=None):
        self.pkg_dir = pkg_dir
        self.package = package
        self.repo = repo
        self.srpm_file = srpm_file
        self.spec_file = None

    @property
    def pkg_dir(self):
        return self._pkg_dir

    @pkg_dir.setter
    def pkg_dir(self, path):
        if not os.path.exists(path):
            os.mkdir(pkg_dir)
        if path[-1] == '/':
            self._pkg_dir = path
        else:
            self._pkg_dir = path + '/'

    @property
    def spec_file(self):
        return self._pkg_dir + self.__spec_file

    @spec_file.setter
    def spec_file(self, name):
        self.__spec_file = name
    
    @property
    def srpm_file(self):
        return self._pkg_dir + self.__srpm_file

    @srpm_file.setter
    def srpm_file(self, name):
        self.__srpm_file = name

    def dnf_download(self):
        '''
        Download srpm of package from selected repo using dnf.
        '''
        proc_data = subprocess_popen_call(["dnf", "download", "--disablerepo=*", 
            "--enablerepo=" + self.repo, "--destdir",  self.pkg_dir,
            "--source",  self.package])
        
        if proc_data['returncode']:
            if proc_data['stderr'] == "Error: Unknown repo: '{0}'\n".format(self.repo):
                    raise ex.UnknownRepoException('Repository {} is probably disabled'.format(self.repo))
        elif proc_data['stderr']:
            raise ex.DownloadFailException(proc_data['stderr'])

        self.srpm_file = self.get_file('.src.rpm')
        
    def koji_download(self):
        '''
        Download srpm of package from selected repo using koji.
        '''
        with change_dir(self.pkg_dir):
            proc_data = subprocess_popen_call(["koji", "download-build",
                "--arch=src", "--latestfrom=f24-python3", self.package])
            # TODO --latestfrom= TAG
            if proc_data['returncode']:
                raise ex.DownloadFailException(proc_data['stderr'])
        
        self.srpm_file = self.get_file(".src.rpm")
      
        # koji download-build --arch=src --latestfrom=f24-python3 python3

    def unpack(self):
        '''
        Unpacks srpm archive
        '''
        with change_dir(self.pkg_dir):
            p1 = Popen(["rpm2cpio", self.srpm_file], stdout=PIPE,
                    stderr=PIPE)
            p2 = Popen(["cpio", "-idmv"], stdin=p1.stdout, stdout=PIPE, stderr=PIPE)
            stream_data = p2.communicate()
            stderr_str = stream_data[1].decode(locale.getpreferredencoding())
            if p2.returncode:
                raise CalledProcessError(cmd='rpm2cpio' ,returncode=p2.returncode)
            self.spec_file = self.get_file('.spec')

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
                         '--define', 'scl_prefix rh-python34-',
                         '-bs', self.spec_file], stdout=PIPE, 
                         stderr=PIPE).communicate()[0].strip()
        except OSError:
            print('Rpmbuild failed for specfile: {0} and save_dir: {1}'.format(
                self.spec_file, self.pkg_dir)) 
             #TODO log message
        self.srpm_file = self.get_file('.src.rpm')

    def get_file(self, suffix):
        '''
        Checks if file self.package.suffix exists in self.pkg_dir
        returns file name on success
        '''
        name = glob.glob(self.pkg_dir + '*' + suffix)
        if not name:
            raise FileNotFoundError("Failed to find {}".format(self.package
                + '*' + suffix))
        else:
            return name[0][len(self.pkg_dir):]
    
    def get(self, src="dnf"):
        if src == "dnf":
            self.dnf_download()
        elif src == "koji":
            self.koji_download()
        self.unpack()
