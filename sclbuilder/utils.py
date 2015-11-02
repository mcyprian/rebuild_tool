import locale
import os

from subprocess import Popen, PIPE, CalledProcessError

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

def subprocess_popen_call(command):
    proc = Popen(command, stdout=PIPE, stderr=PIPE)
    stream_data = proc.communicate()
    stdout_str = stream_data[0].decode(locale.getpreferredencoding())
    stderr_str = stream_data[1].decode(locale.getpreferredencoding())
    return {'returncode' : proc.returncode, 'stdout' : stdout_str, 'stderr' : stderr_str}

class ChangeDir(object):
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

def edit_bootstrap(spec_file, macro, new_value):
    '''
    Sets edit_bootstrap macro macro to new_value in spec_file
    '''
    proc_data = subprocess_popen_call(["sed", '-i', '-e', 's/{0} [0-9]/{0} {1}/g'.format(
        macro, new_value), spec_file])
    if proc_data['returncode']:
        raise CalledProcessError(cmd='sed', returncode=proc_data['returncode'])
    #TODO log message

def check_bootstrap_macro(spec_file, macro):
    macro_definition = "%global " + macro
    proc_data = subprocess_popen_call(["grep", macro_definition, spec_file])
    if proc_data['returncode']:
        sed_data = subprocess_popen_call(["sed", "-i", '1,1s/^/{0} 1\\n/'.format(
            macro_definition), spec_file])
        if sed_data['returncode']:
            print(sed_data['stderr'])
            raise CalledProcessError(cmd='sed', returncode=sed_data['returncode'])

def base_name(name):
    '''
    Removes version and parentheses from package name
    foo >= 1.0  >>  foo
    foo(64bit)  >>  foo
    '''
    if '(' in name:
        name = name.split('(')[0]
    if '>' in name:
        name = name.split('>')[0]
    return name
