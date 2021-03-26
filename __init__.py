def classFactory(iface):
    from .oawplugin import OAWPlugin
    return OAWPlugin(iface)
