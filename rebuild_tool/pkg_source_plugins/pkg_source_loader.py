import importlib

available_pkg_source_plugins = ['dnf', 'koji']

def load_plugin(name):
    return importlib.import_module('rebuild_tool.pkg_source_plugins.' + name)
