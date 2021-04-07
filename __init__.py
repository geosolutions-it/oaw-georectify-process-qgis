import os
import sys

this_dir = os.path.dirname(os.path.realpath(__file__))
lib_dir = os.path.join(this_dir, 'lib')

try:
    import geotiflib
except ImportError:
    path = os.path.join(lib_dir, 'geotiflib-1.0.7-py3-none-any.whl')
    sys.path.append(path)
    import geotiflib

try:
    import paramiko
except ImportError:
    path = os.path.join(lib_dir, 'paramiko-2.7.2-py2.py3-none-any.whl')
    sys.path.append(path)
    import paramiko

try:
    import pysftp
except ImportError:
    path = os.path.join(lib_dir, 'pysftp-0.2.9-py3-none-any.whl')
    sys.path.append(path)
    import pysftp

try:
    import watchdog
except ImportError:
    path = os.path.join(lib_dir, 'watchdog-2.0.2-py3-none-win_amd64.whl')
    sys.path.append(path)
    import watchdog


def classFactory(iface):
    from .oawplugin import OAWPlugin
    return OAWPlugin(iface)
