import importlib

available_builder_plugins = ['copr']

def load_plugin(name):
    return importlib.import_module('rebuild_tool.builder_plugins.' + name)
