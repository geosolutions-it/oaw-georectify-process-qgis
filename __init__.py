try:
    import geotiflib
except ImportError:
    import sys
    import os
    this_dir = os.path.dirname(os.path.realpath(__file__))
    path = os.path.join(this_dir, 'lib', 'geotiflib-1.0.7-py3-none-any.whl')
    sys.path.append(path)
    import geotiflib


def classFactory(iface):
    from .oawplugin import OAWPlugin
    return OAWPlugin(iface)
