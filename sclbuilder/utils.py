import locale

from subprocess import Popen, PIPE

def subprocess_popen_call(command=[]):
    proc = Popen(command, stdout=PIPE, stderr=PIPE)
    stream_data = proc.communicate()
    stdout_str = stream_data[0].decode(locale.getpreferredencoding())
    stderr_str = stream_data[1].decode(locale.getpreferredencoding())
    return {'returncode' : proc.returncode, 'stdout' : stdout_str, 'stderr' : stderr_str}
