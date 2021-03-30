import os
from qgis.PyQt.uic import loadUiType
from qgis.PyQt.QtWidgets import QDockWidget, QDialogButtonBox
from .settings import SettingsWidget
from .new import NewWidget
from .monitor import MonitorWidget

FORM_CLASS, _ = loadUiType(os.path.join(os.path.dirname(__file__), 'ui/panel.ui'))


class PanelWidget(QDockWidget, FORM_CLASS):
    """
    Widget of the panel
    """
    def __init__(self, iface, parent):
        super(PanelWidget, self).__init__(parent)
        self.setupUi(self)
        self.iface = iface
        self.widget_settings = SettingsWidget(self)
        self.widget_new = NewWidget(self)
        self.widget_monitor = MonitorWidget(self)

    def get_settings(self):
        return self.widget_settings