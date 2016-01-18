import os
import glob
import re
from subprocess import CalledProcessError
from abc import ABCMeta, abstractmethod

from sclbuilder import utils

def set_class_attrs(add_fce):
    '''
    Decorator to set class attributes repo and prefix
    before first addition of pkg source class to container
    '''
    def inner(self, package, pkg_dir, repo, prefix, koji_tag=None):
        if not PkgSrcArchive.repo:
            PkgSrcArchive.repo = repo
            PkgSrcArchive.prefix = prefix
            PkgSrcArchive.koji_tag = koji_tag
        add_fce(self, package, pkg_dir)
    return inner

class PkgSrcArchive(metaclass=ABCMeta):
    '''
    Abstract super class of pkg_source classes
    '''
    repo = None
    prefix = None
    koji_tag = None

    def __init__(self, package, pkg_dir, srpm_file=None, spec_file=None):
        self.pkg_dir = pkg_dir
        self.package = package
        self.srpm_file = srpm_file
        self.spec_file = spec_file
        self.download()
        self.unpack()
        self.pack()
        self.rpms = self.rpms_from_spec

    def __repr__(self):
        return "pacakage: {} rpms: {}".format(self.package, self.rpms)

    @property
    def pkg_dir(self):
        return self._pkg_dir

    @pkg_dir.setter
    def pkg_dir(self, path):
        if not os.path.exists(path):
            os.mkdir(path)
        if path[-1] == '/':
            self._pkg_dir = path
        else:
            self._pkg_dir = path + '/'

    @property
    def full_path_spec(self):
        return self._pkg_dir + self.spec_file

    @property
    def full_path_srpm(self):
        return self._pkg_dir + self.srpm_file

    def get_file(self, suffix):
        '''
        Checks if file self.package.suffix exists in self.pkg_dir
        returns file name on success
        '''
        name = glob.glob(self.pkg_dir + '*' + suffix)
        if not name:
            raise IOError("Failed to find {}".format(self.package + '*' + suffix))
        else:
            return name[0][len(self.pkg_dir):]

    @property
    def rpms_from_spec(self):
        '''
        Returns list of rpms created from spec_file
        '''
        rpm_pattern = re.compile("(^.*?)-\d+.\d+.*$")
        proc_data = utils.subprocess_popen_call(["rpm", "-q", "--specfile", "--define",
                                                 "scl_prefix " + type(self).prefix,
                                                 self.full_path_spec])
        if proc_data['returncode']:
            raise CalledProcessError(cmd='rpm', returncode=proc_data['returncode'])
        rpms = proc_data['stdout'].splitlines()
        return {rpm_pattern.search(x).groups()[0] for x in rpms}

    @abstractmethod
    def dependencies(self):
        pass

    @abstractmethod
    def download(self):
        pass

    @abstractmethod
    def unpack(self):
        pass
    
    @abstractmethod
    def pack(self):
        pass
