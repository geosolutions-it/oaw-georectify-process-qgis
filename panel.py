import os
from qgis.PyQt.uic import loadUiType
from qgis.PyQt.QtWidgets import QDockWidget, QDialogButtonBox
from qgis.PyQt.QtCore import QSettings, Qt


FORM_CLASS, _ = loadUiType(os.path.join(os.path.dirname(__file__), 'ui/panel.ui'))


class PanelWidget(QDockWidget, FORM_CLASS):
    """
    Widget of the panel
    """
    def __init__(self, iface, parent):
        super(PanelWidget, self).__init__(parent)
        self.setupUi(self)
        self.iface = iface
