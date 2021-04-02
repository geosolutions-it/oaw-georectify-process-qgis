import os
from qgis.core import Qgis
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
        self.message_bar = self.iface.messageBar()
        self.widget_settings = SettingsWidget(self)
        self.widget_new = NewWidget(self)
        self.widget_monitor = MonitorWidget(self)
        self.widget_settings.on_changed += self.widget_new.on_settings_changed

    def get_settings(self):
        return self.widget_settings

    def push_message(self, message, level=Qgis.Info):
        self.message_bar.pushMessage(message, level=level)
