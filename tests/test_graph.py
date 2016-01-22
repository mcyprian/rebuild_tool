import pytest
from flexmock import flexmock

from rebuild_tool.graph import PackageGraph

class TestGraph(object):
    fake_python = flexmock(
        package = 'python3',
        rpms = {'python3-devel', 'python3-test', 'python3-debug', 'python3',
                'python3-debuginfo', 'python3-tools', 'python3-tkinter',
                'python3-libs'},
        dependencies =  {'valgrind-devel', 'python-macros', 'tk-devel', 
                         'gdbm-devel', 'python3-pip', 'tar', 'tix-devel', 
                         'python3-setuptools'}
    )
    fake_setuptools = flexmock(
        package = 'python-setuptools',
        rpms = {'python3-setuptools', 'python-setuptools'},
        dependencies = {'python3-pytest', 'python3-mock',
                        'python3-pip', 'python-mock', 'python-pip', 
                        'python2-devel', 'pytest', 'python3-devel'}  
    )
    fake_pip = flexmock(
        package = 'python_pip',
        rpms = {'python-pip', 'python3-pip'},
        dependencies = {'python3-pip', 'python-pip', 'python-wheel', 
                        'python-devel', 'python3-wheel', 'python-setuptools', 
                        'python3-devel', 'python3-setuptools'}
    )
    fake_nodeps = flexmock(
        package = 'python_six',
        rpms = {'python-nodeps', 'python3-six'},
        dependencies =  set()
    )
    class_pkg_source =  {'python3' : fake_python,
                         'python-setuptools' : fake_setuptools,
                         'python-pip' : fake_pip,
                         'python-nodeps': fake_nodeps}

    class_graph = PackageGraph("rawhide", class_pkg_source)
    class_graph.make_graph()

    @pytest.mark.parametrize(('pkg_source', 'expected'), [
        (class_pkg_source, 
          {'python3-devel', 'python3-test', 'python3-debug', 'python3',
           'python3-debuginfo', 'python3-tools', 'python3-tkinter',
           'python3-libs', 'python3-setuptools', 'python-setuptools',
           'python-pip', 'python3-pip',
           'python-nodeps', 'python3-six'}),
          ({}, set()),
          ({'python-setuptools': fake_setuptools}, 
           {'python3-setuptools', 'python-setuptools'})
    ])
    def test_rpms(self, pkg_source, expected):
        graph = PackageGraph("rawhide", pkg_source)
        graph.make_graph()
        assert graph.rpms == expected
 
      
    @pytest.mark.parametrize(('pkg', 'expected'), [
        ('python3', {'python-pip', 'python-setuptools'}),
        ('python-setuptools', {'python3', 'python-pip'}),
        ('python-pip', {'python-pip', 'python3', 'python-setuptools'}),
        ('python-nodeps', set())
    ])
    def test_successors(self, pkg, expected):
       assert set(TestGraph.class_graph.G.successors(pkg)) == expected

    @pytest.mark.parametrize(('pkg', 'expected'), [
        ('python3', {'python-pip', 'python-setuptools'}),
        ('python-setuptools', {'python3', 'python-pip'}),
        ('python-pip', {'python-pip', 'python3', 'python-setuptools'}),
        ('python-nodeps', set())
    ])
    def test_predecessors(self, pkg, expected):
       assert set(TestGraph.class_graph.G.predecessors(pkg)) == expected

    @pytest.mark.parametrize(('pkg_source', 'expected'), [
        (class_pkg_source, {'python-nodeps'}),
        ({}, set()),
        ({'python-setuptools': fake_setuptools,
          'python-pip': fake_pip,
          'python3' : fake_python}, set())
    ])
    def test_get_leaf_nodes(self, pkg_source, expected):
        graph = PackageGraph("rawhide", pkg_source)
        graph.make_graph()
        assert set(graph.get_leaf_nodes()) == expected

    @pytest.mark.parametrize(('pkg_source', 'expected'), [
        (class_pkg_source, [{'python3', 'python-setuptools', 'python-pip'}]),
        ({}, []),
        ({'python-setuptools': fake_setuptools,
          'python-pip': fake_pip},  [{'python-pip', 'python-setuptools'}])
    ])
    def tests_get_cycles(self, pkg_source, expected):
        graph = PackageGraph("rawhide", pkg_source)
        graph.make_graph()
        assert graph.get_cycles() == expected


