import qgis.core


def log_message(message: str, level: qgis.core.Qgis.MessageLevel = qgis.core.Qgis.MessageLevel.Info) -> None:
    qgis.core.QgsMessageLog.logMessage(message, "qgis-oacs-plugin", level=level)