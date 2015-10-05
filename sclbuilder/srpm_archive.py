import locale
import glob
from subprocess import Popen, PIPE, CalledProcessError

import sclbuilder.exceptions as ex
from sclbuilder import settings
from sclbuilder.utils import subprocess_popen_call, change_dir


class SrpmArchive(object):
    '''
    Contains methods to work with srpm archive.
    '''
    def __init__(self, temp_dir, package, repo=settings.DEFAULT_REPO, srpm_name=None):
        self.temp_dir = temp_dir
        self.package = package
        self.repo = repo
        self.srpm_name = srpm_name

    @property
    def temp_dir(self):
        return self._temp_dir

    @temp_dir.setter
    def temp_dir(self, path):
        if path[-1] == '/':
            self._temp_dir = path
        else:
            self._temp_dir = path + '/'
    
    def download(self):
        '''
        Download srpm of package from selected repo.
        '''
        proc_data = subprocess_popen_call(["dnf", "download", "--disablerepo=*", 
            "--enablerepo=" + self.repo, "--destdir",  self.temp_dir,
            "--source",  self.package])
        
        if proc_data['returncode']:
            if proc_data['stderr'] == "Error: Unknown repo: '{0}'\n".format(self.repo):
                    raise ex.UnknownRepoException('Repository {} is probably disabled'.format(self.repo))
        elif proc_data['stderr']:
            raise ex.DownloadFailException(proc_data['stderr'])

        self.srpm_name = self.get_file('.src.rpm')
        
        
    def unpack(self):
        '''
        Unpacks srpm archive
        '''
        with change_dir(self.temp_dir):
            p1 = Popen(["rpm2cpio", self.temp_dir + self.srpm_name], stdout=PIPE,
                    stderr=PIPE)
            p2 = Popen(["cpio", "-idmv"], stdin=p1.stdout, stdout=PIPE, stderr=PIPE)
            stream_data = p2.communicate()
            stderr_str = stream_data[1].decode(locale.getpreferredencoding())
            if p2.returncode:
                raise CalledProcessError(cmd='rpm2cpio' ,returncode=p2.returncode)
            self.spec_file = self.get_file('.spec')

    def get_file(self, suffix):
        '''
        Checks if file self.package.suffix exists in self.temp_dir
        returns file name on success
        '''
        name = glob.glob(self.temp_dir + '*' + suffix)
        if not name:
            raise FileNotFoundError("Failed to find {}".format(self.package
                + '*' + suffix))
        else:
            return name[0][len(self.temp_dir):]
    
    def get(self):
        self.download()
        self.unpack()
