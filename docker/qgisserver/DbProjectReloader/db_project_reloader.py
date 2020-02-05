from qgis.PyQt.QtCore import QObject

from qgis.core import QgsMessageLog, QgsProject, QgsTask, QgsApplication
from qgis.server import QgsServerInterface

import psycopg2
import psycopg2.extensions
import os
from time import sleep


class ListenTask(QgsTask):
    def run(self):
        try:
            QgsMessageLog.logMessage(f"Initializing the thread", level=4)
            while True:
                self.reload_project()
                sleep(5)
            return False
        except Exception as e:
            QgsMessageLog.logMessage(str(e), level=4)
            return False

    def reload_project(self) -> None:
        project: QgsProject = QgsProject.instance()
        # if the project is not loaded, then return, we'll try next time.
        if not project.fileName():
            QgsMessageLog.logMessage(f"Project filename is empty not executing", level=4)
            return
        QgsMessageLog.logMessage(f"See if project is {project.baseName()} newer in db", level=4)
        # it will pick the env var itself.
        pgdatabase = os.getenv("PGDATABASE")
        pgport = os.getenv("PGPORT", 5432)
        pghost = os.getenv("PGHOST", "localhost")
        pgpassword = os.getenv("PGPASSWORD")
        pguser = os.getenv("PGUSER")
        with psycopg2.connect(f"postgresql://{pguser}:{pgpassword}@{pghost}:{pgport}/{pgdatabase}") as conn:
            with conn.cursor() as curs:
                curs.execute(
                    "SELECT (metadata->>'last_modified_time')::timestamp from qgis_projects WHERE name=%s",
                    (project.baseName(),),
                )
                res = curs.fetchone()[0]

        QgsMessageLog.logMessage(f"res: {res}, project {project.lastModified().toPyDateTime()}", level=4)
        if res > project.lastModified().toPyDateTime():
            QgsMessageLog.logMessage(f"project date change, reloading", level=4)
            project.read(project.fileName())


class QgsListenPgProjectChangePlugin(QObject):
    """
    This plugin checks if the project is loaded via postgresql.
    it then check periodically if the project needs to be reloaded.
    """

    def __init__(self, server_iface: QgsServerInterface) -> None:
        try:
            super().__init__()
            task = ListenTask()
            QgsApplication.taskManager().addTask(task)

        except Exception as e:
            QgsMessageLog.logMessage(str(e), level=4)
