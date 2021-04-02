import os
import math
import time
import threading
import sqlite3
from .settings import Settings
from geotiflib.eventhook import EventHook
from qgis.core import QgsMessageLog, Qgis
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtWidgets import QTableWidgetItem


class MonitorThread(threading.Thread):

    def __init__(self, what="count", name="", delay=10, rows_per_page=10):
        threading.Thread.__init__(self)
        self.name = name
        self.lock = threading.Lock()
        self.db_path = Settings.GET_DB_PATH()
        self.rows_per_page = rows_per_page
        self.current_page = 1
        self.what = what
        self.delay_seconds = delay
        self.on_result = EventHook()

    def get_sql_count(self):
        """
        Return the SQL statement to obtain the number of record from the table
        :return:
        """
        return "select count(0) as count from oaw_tasks"

    def get_sql_page(self):
        """
        Returns the SQL statement to obtain the rows of the specific page from the table
        :return:
        """
        offset = 10 * (self.current_page - 1)
        return "SELECT id, name, status, " \
               "strftime('%d-%m-%Y %H:%M:%S', start_date) as start, " \
               "strftime('%d-%m-%Y %H:%M:%S', end_date) as end, " \
               "options, message " \
               "FROM oaw_tasks LIMIT " + str(offset) + ", " + str(self.rows_per_page)

    def set_current_page(self, page):
        """
        Set the current page to monitor
        :param page: page number to monitor
        :return:
        """
        self.lock.acquire()
        try:
            self.current_page = page
            self.read_values()
        except:
            pass
        self.lock.release()

    def read_values(self):
        if self.what == "count":
            sql = self.get_sql_count()
        else:
            sql = self.get_sql_page()
        connection = sqlite3.connect(self.db_path)
        with connection:
            cursor = connection.cursor()
            cursor.execute(sql)
            result = cursor.fetchall()
        if connection:
            connection.close()
        self.on_result.fire(result)

    def run(self):
        while True:
            try:
                QgsMessageLog.logMessage("MonitorThread.run: %s" % self.name, tag="OAW", level=Qgis.Info)
                self.read_values()
            except Exception as e:
                QgsMessageLog.logMessage("MonitorThread.run: %s, exception: %s" % (self.name, str(e)), tag="OAW", level=Qgis.Warning)
            time.sleep(self.delay_seconds)


class MonitorWidget:

    def __init__(self, container):
        """
        Constructor
        :param container: panel widget instance
        """
        self._container = container
        self.current_page = 1
        self.total_pages = 1
        self.total_rows = 0
        self.rows_per_page = 10
        self.thread_count = MonitorThread(name="count", what="count", delay=30)
        self.thread_count.on_result += self.on_count_result
        self.thread_details = MonitorThread(name="details", what="details", delay=10)
        self.thread_details.on_result += self.on_details_result
        self.thread_count.start()
        self.thread_details.start()
        self._container.btn_page_first.clicked.connect(self.on_first_page)
        self._container.btn_page_before.clicked.connect(self.on_previous_page)
        self._container.btn_page_after.clicked.connect(self.on_next_page)
        self._container.btn_page_last.clicked.connect(self.on_last_page)
        QgsMessageLog.logMessage("Initialize MonitorWidget", tag="OAW", level=Qgis.Info)

    def on_count_result(self, result):
        num_rows = result[0][0]
        self._container.lbl_monitor_records_count.setText(str(num_rows))
        self.total_pages = math.ceil(num_rows/self.rows_per_page)
        if self.total_pages == 0:
            self.total_pages = 1
        self._container.lbl_page_current.setText("%d of %d" % (self.current_page, self.total_pages))
        if self.total_rows != num_rows:
            self.total_rows = num_rows
            self.goto_page(self.current_page)

    def on_details_result(self, result):
        self._container.lbl_page_current.setText("%d of %d" % (self.current_page, self.total_pages))
        QgsMessageLog.logMessage("MonitorWidget.on_details_result: %d" % len(result), tag="OAW", level=Qgis.Info)
        row_number = 0
        for i in range(self.rows_per_page-len(result)):
            result.append(("", "", "", "", "", "", "",))
        for row_data in result:
            for column_number, data in enumerate(row_data):
                value = str(data) if data is not None else ""
                cell = QTableWidgetItem(value)
                if column_number == 2:
                    if value == "completed":
                        cell.setBackground(QColor(0, 200, 50))
                    elif value == "failed":
                        cell.setBackground(QColor(200, 0, 50))
                    elif value == "running":
                        cell.setBackground(QColor(50, 0, 200))
                    elif value == "running":
                        cell.setBackground(QColor(255, 255, 255))
                self._container.table_monitor.setItem(row_number, column_number, cell)
            row_number += 1
        self._container.table_monitor.viewport().update()

    def goto_page(self, page):
        self.current_page = page
        self.thread_details.set_current_page(page)

    def on_previous_page(self):
        page = self.current_page - 1
        if page < 1:
            page = 1
        self.goto_page(page)

    def on_next_page(self):
        page = self.current_page + 1
        if page > self.total_pages:
            page = self.total_pages
        self.goto_page(page)

    def on_first_page(self):
        self.goto_page(1)

    def on_last_page(self):
        self.goto_page(self.total_pages)
