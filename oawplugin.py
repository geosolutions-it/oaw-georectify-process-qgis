import os
import webbrowser
from qgis.PyQt.QtCore import Qt, QUrl
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
from .panel import PanelWidget
from .executor import Executor
from .scheduler import Scheduler

CODE = "OAW"


class OAWPlugin:

    def __init__(self, iface):
        self.iface = iface
        self.canvas = iface.mapCanvas()
        self.toolbar = self.iface.addToolBar(CODE + ' Toolbar')
        self.toolbar.setObjectName('oaw_toolbar')
        self.help_action = None
        self.dialog = None
        self.executor = Executor.GET_INSTANCE()
        self.scheduler = Scheduler.GET_INSTANCE()

    def initGui(self):
        self.dialog = PanelWidget(self.iface, self.iface.mainWindow())
        self.iface.addDockWidget(Qt.LeftDockWidgetArea, self.dialog)
        self.dialog.hide()

        self.executor.on_slots_changed += self.dialog.widget_new.on_slots_changed
        self.dialog.widget_settings.on_changed += self.executor.on_settings_changed
        self.dialog.widget_settings.init_widget()

        # Help
        icon = QIcon(os.path.dirname(__file__) + '/images/help-icon.png')
        self.help_action = QAction(icon, "Help", self.iface.mainWindow())
        self.help_action.setObjectName('oaw_help')
        self.help_action.triggered.connect(self.help)
        self.iface.addPluginToMenu(CODE, self.help_action)

    def unload(self):
        self.iface.removePluginMenu(CODE, self.help_action)
        self.iface.removeDockWidget(self.dialog)
        del self.toolbar
        self.dialog = None

    def help(self):
        """
        Display a help page
        :return:
        """
        self.show_dialog()
        url = QUrl.fromLocalFile(os.path.dirname(__file__) + "/index.html").toString()
        webbrowser.open(url, new=2)

    def show_dialog(self):
        """
        Show the plugin docked widget.
        """
        self.dialog.show()
