import os
import sys
from qgis.core import QgsApplication

dll_dir = os.path.join(QgsApplication.prefixPath(), "..", "Python37/DLLs")
this_dir = os.path.dirname(os.path.realpath(__file__))
lib_dir = os.path.join(this_dir, 'lib')

sys.path.append(dll_dir)

libs_name = ["geotiflib-1.0.99-py3-none-any"]

for lib in libs_name:
    path = os.path.join(lib_dir, lib)
    sys.path.append(path)


def classFactory(iface):
    from .oawplugin import OAWPlugin
    return OAWPlugin(iface)
