import os
import json
import sqlite3
from qgis.core import QgsApplication, QgsMessageLog, Qgis, QgsTask
from .settings import Settings

INSTANCE = None


class InsertDbTask(QgsTask):
    """
    Async task execution using the task manager of QGIS
    """
    def __init__(self, desc, db_path, statement, parameters, callback):
        """
        Constructor
        :param desc: description of the task
        :param db_path: path to the sqlite database
        :param statement: statement template  to be executed
        :param parameters: parameters to use with the statement template
        :param callback: callback to call at the end of the task
        """
        QgsTask.__init__(self, desc, QgsTask.CanCancel)
        self.db_path = db_path
        self.statement = statement
        self.parameters = parameters
        self.callback = callback

    def run(self):
        """
        Start the task
        :return:
        """
        QgsMessageLog.logMessage(f"InsertDbTask.run...", tag="OAW", level=Qgis.Info)
        result = {
            "status": False,
            "message": None,
            "info": {}
        }
        try:
            connection = sqlite3.connect(self.db_path)
            with connection:
                cursor = connection.cursor()
                cursor.execute(self.statement, self.parameters)
                result["info"]["id"] = cursor.lastrowid
            result["status"] = True
        except Exception as e:
            QgsMessageLog.logMessage(f"InsertDbTask.run, exception: " + str(e), tag="OAW", level=Qgis.Warning)
            result["message"] = str(e)
        connection.close()
        self.callback(result)
        return result["status"]


class Scheduler:
    """
    Scheduler for new task to put in the queue of the system (sqlite table)
    """
    def __init__(self):
        """
        Constructor of the class
        """
        self.db_path = Settings.GET_DB_PATH()
        QgsMessageLog.logMessage(
            f"Scheduler.__init__ => %s" % str(self.db_path),
            tag="OAW", level=Qgis.Info)

    @staticmethod
    def GET_INSTANCE():
        """
        Return the singleton
        :return:
        """
        global INSTANCE
        if INSTANCE is None:
            INSTANCE = Scheduler()
        return INSTANCE

    def queue(self, task_info):
        """
        Put the task information in a new record of the database
        :param task_info: json string containing all the options necessary for the task (when it will be executed)
        :return:
        """
        QgsMessageLog.logMessage(
            f"Scheduler.queue => %s" % str(task_info),
            tag="OAW", level=Qgis.Info)
        try:

            extensions = ["tif", "tif.points"]
            for extension in extensions:
                src_file = os.path.join(task_info["source_folder"], task_info["name"] + "." + extension)
                stg_file = os.path.join(task_info["staging_folder"], task_info["name"] + "." + extension)
                os.rename(src_file, stg_file)
            QgsMessageLog.logMessage(
                f"Scheduler.queue => moved files from source to staging",
                tag="OAW", level=Qgis.Info)

            task_info["source_folder"] = task_info["source_folder"].replace("\\", "/")
            task_info["staging_folder"] = task_info["staging_folder"].replace("\\", "/")
            options = json.dumps(task_info)
            statement = "INSERT INTO oaw_tasks(name, options, status) VALUES (?, ?, ?)"
            parameters = (task_info["name"], options, 'waiting',)
            task = InsertDbTask("OAW queue task", self.db_path, statement, parameters, self.on_queued_task)
            QgsApplication.taskManager().addTask(task)
            QgsMessageLog.logMessage(
                f"Scheduler.queue => created InsertDbTask",
                tag="OAW", level=Qgis.Info)
        except Exception as e:
            QgsMessageLog.logMessage(
                f"Scheduler.queue, exception: %s" % str(e),
                tag="OAW", level=Qgis.Warning)

    def on_queued_task(self, result):
        """
        Callback called when a task is queued.
        It logs in the QGIS log panel
        :param result: object containing information of the process queue
        :return:
        """
        QgsMessageLog.logMessage(f"Scheduler.on_queued_task: %s" % str(result), tag="OAW", level=Qgis.Info)
