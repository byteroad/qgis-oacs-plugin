import qgis.core
from qgis.PyQt import (
    QtCore,
    QtWidgets,
)


def log_message(message: str, level: qgis.core.Qgis.MessageLevel = qgis.core.Qgis.MessageLevel.Info) -> None:
    qgis.core.QgsMessageLog.logMessage(message, "qgis-oacs-plugin", level=level)


def show_message(
        message_bar: qgis.gui.QgsMessageBar,
        message: str,
        level: qgis.core.Qgis.MessageLevel | None = qgis.core.Qgis.MessageLevel.Info,
        add_loading_widget: bool = False,
) -> None:
    message_bar.clearWidgets()
    message_item = message_bar.createMessage(message)
    if add_loading_widget:
        progress_bar = QtWidgets.QProgressBar()
        progress_bar.setAlignment(
            QtCore.Qt.Alignment.AlignLeft | QtCore.Qt.Alignment.AlignVCenter
        )
        progress_bar.setMinimum(0)
        progress_bar.setMaximum(0)
        message_item.layout().addWidget(progress_bar)
    message_bar.pushWidget(message_item, level=level)
