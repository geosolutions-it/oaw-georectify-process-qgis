import os
from qgis.PyQt.QtCore import QSettings, Qt
from qgis.PyQt.QtWidgets import QDialog, QDialogButtonBox
from qgis.core import QgsMessageLog, Qgis


class MonitorWidget:

    def __init__(self, container):
        """
        Constructor
        :param container: panel widget instance
        """
        QgsMessageLog.logMessage("Initialize MonitorWidget", tag="OAW", level=Qgis.Info)
