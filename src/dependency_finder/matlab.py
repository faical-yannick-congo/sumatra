import os
import re
from sumatra.dependency_finder import core


class Dependency(core.BaseDependency):
    """
    Contains information about a Matlab toolbox.
    """
    module = 'matlab'
    def __init__(self, module_name, path, version='unknown', diff=''):
        self.name = module_name
        self.path = path
        self.version = version
        self.diff = diff


def find_dependencies(filename, executable):
    ifile = os.path.join(os.getcwd(), 'depfun.data')
    file_data = (open(ifile, 'r'))
    content = file_data.read()
    paths = re.split('1: ', content)[2:]
    list_deps = []
    for path in paths:
        if os.name == 'posix':
            list_data = path.split('/')
        else:
            list_data = path.split('\\')
        list_deps.append(Dependency(list_data[-2], path.split('\n')[0]))
    file_data.close()
    # TODO: find version of external toolboxes
    return list_deps