import os
import json
from qgis.PyQt.QtCore import QSettings, Qt
from qgis.PyQt.QtWidgets import QDialog, QDialogButtonBox
from qgis.core import QgsMessageLog, Qgis


class Settings:

    def __init__(self):
        """"
        Constructor.
        Initialize variable from the OAW QSettings
        """
        self._prefix = "/OAW/"
        self._settings = QSettings()
        self.max_concurrent_jobs = int(self._settings.value(self._prefix + 'MaxConcurrentJobs', 2))
        self.gdal_threads = int(self._settings.value(self._prefix + 'GdalThreads', 4))
        self.min_gcp = int(self._settings.value(self._prefix + 'MinGCP', 20))
        self.source_folder = self._settings.value(self._prefix + 'SourceFolder', "")
        self.staging_folder = self._settings.value(self._prefix + 'StagingFolder', "")
        self.remove_file_after = int(self._settings.value(self._prefix + 'RemoveFileAfter', Qt.Unchecked))
        self.remote_address = self._settings.value(self._prefix + 'RemoteAddress', "")
        self.remote_authid = self._settings.value(self._prefix + 'RemoteAuthID', "")

    def save(self):
        """
        Save the information in the OAW settings
        :return:
        """
        QgsMessageLog.logMessage("Settings.save()...", tag="OAW", level=Qgis.Info)
        self._settings.setValue(self._prefix + 'MaxConcurrentJobs', self.max_concurrent_jobs)
        self._settings.setValue(self._prefix + 'GdalThreads', self.gdal_threads)
        self._settings.setValue(self._prefix + 'MinGCP', self.min_gcp)
        self._settings.setValue(self._prefix + 'SourceFolder', self.source_folder)
        self._settings.setValue(self._prefix + 'StagingFolder', self.staging_folder)
        self._settings.setValue(self._prefix + 'RemoveFileAfter', self.remove_file_after)
        self._settings.setValue(self._prefix + 'RemoteAddress', self.remote_address)
        self._settings.setValue(self._prefix + 'RemoteAuthID', self.remote_authid)
        QgsMessageLog.logMessage("Settings.save(). Done!", tag="OAW", level=Qgis.Info)

    def get_attribute(self, attribute, default):
        return self._settings.value(self._prefix + attribute, default)

    def __str__(self):
        return self.get_string()

    def get_string(self):
        return json.dumps(self.get_dict())

    def get_dict(self):
        return {
            "max_concurrent_jobs": self.max_concurrent_jobs,
            "gdal_threads": self.gdal_threads,
            "min_gcp": self.min_gcp,
            "source_folder": self.source_folder,
            "staging_folder": self.staging_folder,
            "remove_file_after": self.remove_file_after,
            "remote_address": self.remote_address,
            "remote_authid": self.remote_authid
        }


class SettingsWidget:
    """
    Class to hook UI with the settings
    """

    def __init__(self, container):
        """
        COnstructor
        :param container: panel widget instance
        """
        QgsMessageLog.logMessage("Initialize SettingsWidget", tag="OAW", level=Qgis.Info)
        self._settings = Settings()
        self._container = container
        self.init_widget()

    def init_widget(self):
        """
        initialize the settings tab of the widget with values stored in settings
        :return:
        """
        self._container.button_box_settings.button(QDialogButtonBox.Save).clicked.connect(self.on_click_save)
        self._container.spn_max_jobs.setValue(self._settings.max_concurrent_jobs)
        self._container.spn_gdal_threads.setValue(self._settings.gdal_threads)
        self._container.spn_min_gcp.setValue(self._settings.min_gcp)
        self._container.src_folder.setFilePath(self._settings.source_folder)
        self._container.stg_folder.setFilePath(self._settings.staging_folder)
        self._container.chk_remove_tif_after_upload.setCheckState(self._settings.remove_file_after)
        self._container.txt_remote_address.setText(self._settings.remote_address)
        self._container.txt_remote_authid.setText(self._settings.remote_authid)

    def on_click_save(self):
        """
        On click callback
        Read the information from the UI and store them in the settings
        :return:
        """
        self._settings.max_concurrent_jobs = int(self._container.spn_max_jobs.value())
        self._settings.gdal_threads = int(self._container.spn_gdal_threads.value())
        self._settings.min_gcp = int(self._container.spn_min_gcp.value())
        self._settings.source_folder = self._container.src_folder.filePath()
        self._settings.staging_folder = self._container.stg_folder.filePath()
        self._settings.remove_file_after = self._container.chk_remove_tif_after_upload.checkState()
        self._settings.remote_address = self._container.txt_remote_address.text()
        self._settings.remote_authid = self._container.txt_remote_authid.text()
        self._settings.save()

    def get_attribute(self, attribute, default):
        return self._settings.get_attribute(attribute, default)

    def get_string(self):
        return self._settings.get_string()

    def get_dict(self):
        return self._settings.get_dict()
