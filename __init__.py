import os
import sys

this_dir = os.path.dirname(os.path.realpath(__file__))
lib_dir = os.path.join(this_dir, 'lib')

libs_name = ["geotiflib-1.0.7-py3-none-any.whl",
             "pycparser-2.20-py2.py3-none-any.whl",
             "cffi-1.14.5-cp37-cp37m-win_amd64.whl",
             "cryptography-3.4.7-cp36-abi3-win_amd64.whl",
             "PyNaCl-1.4.0-cp37-cp37m-win_amd64.whl",
             "bcrypt-3.2.0-cp36-abi3-win_amd64.whl",
             "paramiko-2.7.2-py2.py3-none-any.whl",
             "pysftp-0.2.9-py3-none-any.whl",
             "watchdog-2.0.2-py3-none-win_amd64.whl"]


for lib in libs_name:
    path = os.path.join(lib_dir, lib)
    sys.path.append(path)
"""
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
"""

def classFactory(iface):
    from .oawplugin import OAWPlugin
    return OAWPlugin(iface)
