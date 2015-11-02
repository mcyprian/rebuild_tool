import logging
import os

logger = logging.getLogger('sclbuilder')
logger.setLevel(logging.DEBUG)

file_formatter = logging.Formatter(u'%(asctime)s::%(name)s::%(levelname)s::%(message)s')

def register_file_log_handler(log_file, level=logging.DEBUG, fmt=file_formatter):
    dirname = os.path.dirname(log_file)
    try:
        if not os.path.exists(dirname):
            os.makedirs(dirname)
    except (OSError, IOError):
        return False
    try:
        file_handler = logging.FileHandler(log_file, 'a')
        file_handler.setLevel(level)
        file_handler.setFormatter(fmt)
        logger.addHandler(file_handler)
    except (OSError, IOError):
        return False
    return True

