import importlib

available_builder_plugins = ['copr']

def load_plugin(name):
    return importlib.import_module('sclbuilder.builder_plugins.' + name)
