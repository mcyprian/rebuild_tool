import locale
import glob
from subprocess import Popen, PIPE, CalledProcessError

import sclbuilder.exceptions as ex
from sclbuilder.utils import subprocess_popen_call


class SrpmArchive(object):
    '''
    Contains methods to work with srpm archive.
    '''
    def __init__(self, temp_dir, package, repo, srpm_name=''):
        self.temp_dir = temp_dir         #TODO check if ends with '/'
        self.package = package
        self.repo = repo
        self.srpm_name = srpm_name

    def download_srpm(self):
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
        
        srpm_name = glob.glob(self.temp_dir + self.package + '*.src.rpm')
        if not srpm_name:
            raise ex.SrpmNotFoundException("Failed to find srpm of package {}".format(
                self.package))
        else:
            self.srpm_name = srpm_name[0][len(self.temp_dir):]

    def unpack_srpm(self):        #TODO cd temp ... 
        '''
        Unpacks srpm archive
        '''
        p1 = Popen(["rpm2cpio", self.temp_dir + self.srpm_name], stdout=PIPE,
                stderr=PIPE)
        p2 = Popen(["cpio", "-idmv"], stdin=p1.stdout, stdout=PIPE, stderr=PIPE)
        stream_data = p2.communicate()
        stderr_str = stream_data[1].decode(locale.getpreferredencoding())
        if p2.returncode:
            raise CalledProcessError(cmd='rpm2cpio' ,returncode=p2.returncode)
