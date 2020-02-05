from qgis.core import QgsMessageLog


def serverClassFactory(serverIface):  # noqa
    QgsMessageLog.logMessage("Starting DB project reloader...", level=4)
    try:
        from .db_project_reloader import QgsListenPgProjectChangePlugin

        return QgsListenPgProjectChangePlugin(serverIface)
    except Exception as e:
        QgsMessageLog.logMessage(str(e))
