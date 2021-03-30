import os
import time
from qgis.core import QgsApplication, QgsMessageLog, Qgis, QgsTask


class GeoRectifyTask(QgsTask):

    def __init__(self, desc, options):
        QgsTask.__init__(self, desc, QgsTask.CanCancel)
        self.options = options
        self._continue = True

    def stop(self):
        self._continue = False

    def canContinue(self):
        return self._continue and not self.isCanceled()

    def run(self):
        QgsMessageLog.logMessage(
            "GeoRectifyTask started",
            tag="OAW", level=Qgis.Info)
        try:
            time.sleep(5)
            if not self.canContinue():
                self.stopped()
                return False
            time.sleep(5)
        except Exception as e:
            QgsMessageLog.logMessage(
                "GeoRectifyTask exception: %s" % str(e),
                tag="OAW", level=Qgis.Warning)
            return False
        return True
