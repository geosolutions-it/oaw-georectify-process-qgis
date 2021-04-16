import os
import json
import time
import pysftp
import sqlite3
import threading
from geotiflib.georectify import GeoRectifyFactory
from geotiflib.eventhook import EventHook
from qgis.PyQt.QtCore import Qt
from qgis.core import QgsApplication, QgsAuthMethodConfig, QgsMessageLog, Qgis, QgsTask
from .settings import Settings

INSTANCE = None


class GeoRectifyTask(threading.Thread):

    def __init__(self, rowid, name, options, handlers):
        threading.Thread.__init__(self)
        self.rowid = rowid
        self.name = name
        self.db_path = Settings.GET_DB_PATH()
        #desc = "OAW GeoRectify: %s" % name
        #QgsTask.__init__(self, desc, QgsTask.CanCancel)
        self.handlers = handlers
        self.options = options
        self.status = 'reserved'
        self.exception = None

    def set_status(self, status, message):
        connection = None
        try:
            time.sleep(0.1)
            self.status = status
            statement = "UPDATE oaw_tasks SET status = ?, message = ? WHERE id = ?"
            if status == 'running':
                statement = "UPDATE oaw_tasks SET status = ?, message = ?, start_date = CURRENT_TIMESTAMP WHERE id = ?"
            elif status == 'failed' or status == 'completed':
                statement = "UPDATE oaw_tasks SET status = ?, message = ?, end_date = CURRENT_TIMESTAMP WHERE id = ?"
            connection = sqlite3.connect(self.db_path)
            with connection:
                cursor = connection.cursor()
                cursor.execute(statement, (status, message, self.rowid,))
        finally:
            if connection:
                connection.close()

    def get_name(self):
        return self.name

    def get_rowid(self):
        return self.rowid

    def get_status(self):
        return self.status

    def on_progress(self, message):
        self.handlers["on_progress_changed"](self, message)

    def run(self):
        QgsMessageLog.logMessage(f"GeoRectifyTask.run, process: %s" % self.name, tag="OAW", level=Qgis.Info)
        try:
            self.set_status('running', 'started')

            input_tif = os.path.join(self.options["staging_folder"], self.name + ".tif")
            scripts_folder = os.path.join(QgsApplication.prefixPath(), "..", "Python37/Scripts")
            geo_rectify = GeoRectifyFactory.create(
                input=input_tif,
                qgis_scripts=scripts_folder,
                min_points=self.options["min_points"],
                gdal_threads=self.options["gdal_threads"]
            )
            geo_rectify.on_progress += self.on_progress
            geo_rectify.process()

            auth_id = self.options["remote_authid"]
            auth_manager = QgsApplication.authManager()
            auth_cfg = QgsAuthMethodConfig()
            auth_manager.loadAuthenticationConfig(auth_id, auth_cfg, True)
            if auth_cfg.id():
                username = auth_cfg.config('username', '')
                password = auth_cfg.config('password', '')
                uri = auth_cfg.uri()
                # call FTP task
                QgsMessageLog.logMessage(f"GeoRectifyTask.run, URI: %s" % str(uri), tag="OAW",
                                         level=Qgis.Info)
                QgsMessageLog.logMessage(f"GeoRectifyTask.run, username: %s" % str(username), tag="OAW",
                                         level=Qgis.Info)
                QgsMessageLog.logMessage(f"GeoRectifyTask.run, password: %s" % "***********", tag="OAW",
                                         level=Qgis.Info)
                # upload file via SFTP
                output_tif = input_tif.replace(".tif", "_grf_fin.tif")
                remote_folder = self.options["remote_folder"] if "remote_folder" in self.options else "public"
                cnopts = pysftp.CnOpts()
                cnopts.hostkeys = None
                with pysftp.Connection(uri, username=username, password=password, cnopts=cnopts) as sftp:
                    with sftp.cd(remote_folder):
                        sftp.put(output_tif, remotepath=self.name + ".tif")

                # Remove intermediate file (if requested)
                if self.options["remove_file_after"] == Qt.Checked:
                    os.remove(output_tif)
                    QgsMessageLog.logMessage(f"GeoRectifyTask.run, removing intermediate file: %s" % output_tif,
                                             tag="OAW", level=Qgis.Info)
            else:
                raise Exception("Failed to extract information from the QGIS authentication manager using authid: %s"
                                % auth_id)
            self.set_status('completed', 'done')
        except Exception as e:
            self.exception = e
            self.set_status('failed', str(e))
            QgsMessageLog.logMessage(f"GeoRectifyTask.run, exception: %s" % str(e), tag="OAW", level=Qgis.Warning)
        self.handlers["on_completed"](self)
        QgsMessageLog.logMessage(f"GeoRectifyTask.run, result: %s" % self.status, tag="OAW", level=Qgis.Info)
        return self.status == 'completed'


class DeQueueTask(QgsTask):
    """
    Retrieve runnable task from the (database) queue
    """
    def __init__(self, desc, callback):
        QgsTask.__init__(self, desc, QgsTask.CanCancel)
        self.db_path = Settings.GET_DB_PATH()
        self._interval = 10
        self.available_slots = 5
        self.statement_1 = "UPDATE oaw_tasks SET status = ? WHERE id in (" \
                           "   SELECT id FROM oaw_tasks WHERE status=? order by id ASC LIMIT ?" \
                           ")"
        self.statement_2 = "SELECT id, name, options FROM oaw_tasks WHERE status = ? ORDER BY id ASC LIMIT ?"
        self.callback = callback

    def set_available_slots(self, slots):
        self.available_slots = 0
        if slots > 0:
            self.available_slots = slots

    def check_for_tasks(self):
        QgsMessageLog.logMessage(f"DeQueueTask.check_for_tasks...", tag="OAW", level=Qgis.Info)
        if self.available_slots <= 0:
            return
        result = {
            "status": False,
            "message": None,
            "info": {
                "rows": []
            }
        }
        try:
            connection = sqlite3.connect(self.db_path)
            with connection:
                cursor = connection.cursor()
                cursor.execute(self.statement_1, ('reserved', 'waiting', self.available_slots,))
                cursor.execute(self.statement_2, ('reserved', self.available_slots,))
                result["info"]["rows"] = cursor.fetchall()
            result["status"] = True
        except Exception as e:
            QgsMessageLog.logMessage(f"ExecuteDbTask.run, exception: " + str(e), tag="OAW", level=Qgis.Warning)
            result["message"] = str(e)
        connection.close()
        if len(result["info"]["rows"]):
            self.callback(result["info"]["rows"])

    def run(self):
        time.sleep(self._interval)
        try:
            while True:
                QgsMessageLog.logMessage("DeQueueTask -> checking...", tag="OAW", level=Qgis.Info)
                if self.isCanceled():
                    return True
                self.check_for_tasks()
                time.sleep(self._interval)
        except Exception as e:
            QgsMessageLog.logMessage(
                "DeQueueTask -> exception: %s" % str(e),
                tag="OAW", level=Qgis.Warning)
            return False
        return True


class Executor:
    """
    The executor class has in charge to start Jobs according to the available slots
    """
    def __init__(self):
        self.lock = threading.Lock()
        self.max_slots = 4
        self.running_tasks = 0
        self.slots = {}
        self._container = None
        self.on_slots_changed = EventHook()
        self.task = DeQueueTask("OAW Executor", self.on_tasks_to_start)
        QgsMessageLog.logMessage(f"Scheduler.queue => created InsertDbTask", tag="OAW", level=Qgis.Info)
        QgsApplication.taskManager().addTask(self.task)

    @staticmethod
    def GET_INSTANCE():
        global INSTANCE
        if INSTANCE is None:
            INSTANCE = Executor()
        return INSTANCE

    def on_settings_changed(self, settings):
        self.lock.acquire()
        self.max_slots = settings["max_concurrent_jobs"]
        self.update_available_slots(0)
        self.lock.release()

    def update_available_slots(self, delta):
        """
        Update status of available slots to execute concurrent tasks
        :param delta: number of slots to update (negative: new tasks started, positive: existing tasks finieshed)
        :return:
        """
        self.running_tasks -= delta
        available_tasks = self.max_slots - self.running_tasks
        if available_tasks < 0:
            available_tasks = 0
        self.on_slots_changed.fire({"value": available_tasks})
        self.task.set_available_slots(available_tasks)

    def start_new_task(self, task_info):
        self.lock.acquire()
        task = None
        try:
            self.update_available_slots(-1)
            task = GeoRectifyTask(rowid=task_info[0], name=task_info[1], options=json.loads(task_info[2]), handlers={
                    "on_progress_changed": self.on_task_progress_changed,
                    "on_completed": self.on_task_completed
                })
            self.slots["_%d_" % task_info[0]] = task
        finally:
            self.lock.release()
        #QgsApplication.taskManager().addTask(task)
        if task is not None:
            task.start()
            #self._container.push_message("Processing started: %s" % task_info[1], level=Qgis.Info)

    def on_tasks_to_start(self, task_info_list):
        for task_info in task_info_list:
            QgsMessageLog.logMessage(f"Executor.on_tasks_to_start => %s" % str(task_info), tag="OAW", level=Qgis.Info)
            self.start_new_task(task_info)

    def on_task_progress_changed(self, task, message):
        QgsMessageLog.logMessage(f"Executor.on_task_progress_changed => %s (%s)" %
                                 (task.get_name(), str(message)), tag="OAW", level=Qgis.Info)

    def on_task_completed(self, task):
        QgsMessageLog.logMessage(f"Executor.on_task_completed => %s" %
                                 task.get_name(), tag="OAW", level=Qgis.Info)
        self.lock.acquire()
        try:
            task_key = "_%d_" % task.get_rowid()
            if task_key in self.slots:
                del self.slots[task_key]
            self.update_available_slots(1)
        finally:
            self.lock.release()

