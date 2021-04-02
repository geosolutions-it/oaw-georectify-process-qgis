import os
import glob
import json
import time
from .scheduler import Scheduler
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

from qgis.PyQt.QtCore import QSettings, Qt
from qgis.PyQt.QtWidgets import QDialog, QDialogButtonBox
from qgis.core import QgsApplication, QgsMessageLog, Qgis, QgsTask


class ObserverTask(QgsTask):

    def __init__(self, desc, observer):
        QgsTask.__init__(self, desc, QgsTask.CanCancel)
        self.observer = observer
        self._continue = True
        self._interval = 2.5

    def stop(self):
        self._continue = False

    def run(self):
        time.sleep(2*self._interval)
        self.observer.start()
        try:
            while self._continue:
                QgsMessageLog.logMessage(
                    "ObserverTask -> watching...",
                    tag="OAW", level=Qgis.Info)
                if self.isCanceled():
                    self.observer.stop()
                    return True
                time.sleep(self._interval)
        except KeyboardInterrupt:
            self.observer.stop()
            self.observer.join()
        self.observer.stop()
        return True


class NewWidget:

    def __init__(self, container):
        """
        Constructor
        :param container: panel widget instance
        """
        QgsMessageLog.logMessage("Initialize NewWidget", tag="OAW", level=Qgis.Info)
        self._container = container
        self._container.lbl_slots_count.setText(
            str(self._container.get_settings().get_attribute('MaxConcurrentJobs', ''))
        )
        patterns = ["*.tif.points", "*.tif"]
        ignore_patterns = []
        ignore_directories = True
        case_sensitive = True
        self.event_handler = PatternMatchingEventHandler(patterns, ignore_patterns, ignore_directories, case_sensitive)
        self.event_handler.on_created = self.on_raster_created
        self.event_handler.on_deleted = self.on_raster_deleted
        self.event_handler.on_modified = self.on_raster_modified
        self.event_handler.on_moved = self.on_raster_moved
        self.observer = None
        self.observer_task = None
        self._raster_list = []
        self._folder = ""
        self._container.chk_watch_src_folder.stateChanged.connect(self.watch_state_changed)
        self._container.button_box_new.button(QDialogButtonBox.Apply).clicked.connect(self.queue_raster)
        self.watch_state_changed()
        self._current_settings = None

    def on_settings_changed(self, settings):
        self._current_settings = settings
        self.get_raster_list()

    def on_slots_changed(self, data):
        self._container.lbl_slots_count.setText(str(data["value"]))

    def get_folder(self):
        self._folder = self._current_settings["source_folder"]
        return self._folder

    def watch_state_changed(self):
        state = self._container.chk_watch_src_folder.checkState()
        if state == Qt.Unchecked and self.observer_task is not None:
            self.observer_task.stop()
        elif state == Qt.Checked:
            self.get_raster_list()
            self.set_observer()
            self.observer_task = ObserverTask("OAW Watcher source folder", self.observer)
            QgsApplication.taskManager().addTask(self.observer_task)
        QgsMessageLog.logMessage(
            "Watch state: " + str(state),
            tag="OAW", level=Qgis.Info)

    def set_observer(self):
        QgsMessageLog.logMessage(
            "Setting observer",
            tag="OAW", level=Qgis.Info)
        self.observer = Observer()
        self.observer.schedule(self.event_handler, self.get_folder(), recursive=False)

    def get_raster_list(self):
        """
        Get the the list of rasters (and points) from the source folder directory
        :return:
        """
        self._raster_list = []
        try:
            self._container.cbo_raster.clear()
            os.chdir(self.get_folder())
            files = sorted(glob.glob("*.tif.points"))
            for file in files:
                self.add_raster(file)
        except:
            pass

    def check_raster_file(self, file):
        pts_file = ""
        tif_file = ""
        if file.endswith(".tif.points"):
            tif_file = file.replace(".tif.points", ".tif")
            pts_file = file
        if file.endswith(".tif"):
            tif_file = file
            pts_file = file.replace(".tif", ".tif.points")
        if os.path.isfile(tif_file) and os.path.exists(pts_file):
            return tif_file
        return None

    def add_raster(self, file):
        tif_file = self.check_raster_file(file)
        if tif_file is not None:
            QgsMessageLog.logMessage(
                "add_raster => " + tif_file,
                tag="OAW", level=Qgis.Info)
            base = os.path.basename(tif_file)
            name = os.path.splitext(base)[0]
            if name not in self._raster_list:
                self._raster_list.append(name)
                self._container.cbo_raster.addItem(name)
            QgsMessageLog.logMessage(' '.join(self._raster_list), tag="OAW", level=Qgis.Info)

    def del_raster(self, file):
        tif_file = file.replace(".tif.points", ".tif")
        QgsMessageLog.logMessage(
            "del_raster => " + tif_file,
            tag="OAW", level=Qgis.Info)
        base = os.path.basename(tif_file)
        name = os.path.splitext(base)[0]
        if name in self._raster_list:
            self._raster_list.remove(name)
            index = self._container.cbo_raster.findText(name)
            self._container.cbo_raster.removeItem(index)

    def on_raster_created(self, event):
        try:
            QgsMessageLog.logMessage(
                f"NewWidget.on_raster_created => {event.src_path} has been created!",
                tag="OAW", level=Qgis.Info)
            self.add_raster(event.src_path)
        except Exception as e:
            QgsMessageLog.logMessage(
                str(e),
                tag="OAW", level=Qgis.Warning)

    def on_raster_deleted(self, event):
        try:
            QgsMessageLog.logMessage(
                f"NewWidget.on_raster_deleted => deleted {event.src_path}!",
                tag="OAW", level=Qgis.Info)
            self.del_raster(event.src_path)
        except Exception as e:
            QgsMessageLog.logMessage(
                str(e),
                tag="OAW", level=Qgis.Warning)

    def on_raster_modified(self, event):
        QgsMessageLog.logMessage(
            f"NewWidget.on_raster_modified => {event.src_path} has been modified",
            tag="OAW", level=Qgis.Info)

    def on_raster_moved(self, event):
        try:
            QgsMessageLog.logMessage(
                f"NewWidget.on_raster_moved => moved {event.src_path} to {event.dest_path}",
                tag="OAW", level=Qgis.Info)
            self.del_raster(event.src_path)
            self.add_raster(event.dest_path)
        except Exception as e:
            QgsMessageLog.logMessage(
                str(e),
                tag="OAW", level=Qgis.Warning)

    def queue_raster(self):
        raster = self._container.cbo_raster.currentText()
        if raster == "" or raster is None:
            self._container.push_message("No raster selected!", level=Qgis.Warning)
            return
        QgsMessageLog.logMessage(
            f"NewWidget.queue_raster => %s" % raster,
            tag="OAW", level=Qgis.Info)

        options = self._container.get_settings().get_dict()
        options["name"] = raster
        Scheduler.GET_INSTANCE().queue(options)
        if self._container.chk_watch_src_folder.checkState() == Qt.Unchecked:
            self.get_raster_list()
        QgsMessageLog.logMessage(
            f"NewWidget.queue_raster => %s" % json.dumps(options),
            tag="OAW", level=Qgis.Info)
        self._container.push_message("Raster %s queued!" % raster, level=Qgis.Info)
