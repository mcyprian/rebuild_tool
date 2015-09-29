import locale
import os

from subprocess import Popen, PIPE

def add_prefix(name, prefix):   #TODO remove prefix functions??
    if prefix in name:
        return name
    else:
        return prefix + name

def remove_prefix(name, prefix):
    if not prefix in name:
        return name
    else:
        return name[len(prefix):]

def subprocess_popen_call(command=[]):
    proc = Popen(command, stdout=PIPE, stderr=PIPE)
    stream_data = proc.communicate()
    stdout_str = stream_data[0].decode(locale.getpreferredencoding())
    stderr_str = stream_data[1].decode(locale.getpreferredencoding())
    return {'returncode' : proc.returncode, 'stdout' : stdout_str, 'stderr' : stderr_str}

class change_dir(object):
    '''
    With statement class to store current dir change it and return
    to previous path.
    '''
    def __init__(self, new_path):
        self.primary_path = os.getcwd()
        self.new_path = new_path

    def __enter__(self):
        os.chdir(self.new_path)
        return self

    def __exit__(self, type, value, traceback): #TODO handle exception
        os.chdir(self.primary_path)
