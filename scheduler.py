import os
import sqlite3
from qgis.core import QgsMessageLog, Qgis

INSTANCE = None


class Scheduler:

    def __init__(self):
        self.db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database", "oaw.db")
        QgsMessageLog.logMessage(
            f"Scheduler.__init__ => %s" % str(self.db_path),
            tag="OAW", level=Qgis.Info)

    @staticmethod
    def GET_INSTANCE():
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
        connection = sqlite3.connect(self.db_path)
        try:
            extensions = ["tif", "tif.points"]
            for extension in extensions:
                src_file = os.path.join(task_info["source_folder"], task_info["name"] + "." + extension)
                stg_file = os.path.join(task_info["staging_folder"], task_info["name"] + "." + extension)
                os.rename(src_file, stg_file)
            with connection:
                connection.execute("INSERT INTO oaw_tasks(name, options, status) values (?, ?, ?)",
                                   (task_info["name"], str(task_info), 'waiting'))
        except Exception as e:
            QgsMessageLog.logMessage(
                f"Scheduler.queue, exception: %s" % str(e),
                tag="OAW", level=Qgis.Warning)
        connection.close()

