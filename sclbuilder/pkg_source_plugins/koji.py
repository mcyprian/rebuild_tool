from collections import UserDict

from sclbuilder.pkg_source_plugins.dnf import DnfArchive
from sclbuilder.utils import change_dir, subprocess_popen_call

class PkgsContainer(UserDict):
    def add(self, package, pkg_dir, repo):
        '''
        Adds new KojiArchive object to self.data
        '''
        self[package] = KojiArchive(package, pkg_dir, repo)

class KojiArchive(DnfArchive):
    '''
    Overriding DnfArchive download method to use koji download
    '''

    def download(self):
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
