import importlib

def load_plugin(name):
    return importlib.import_module('sclbuilder.pkg_source_plugins.' + name)
