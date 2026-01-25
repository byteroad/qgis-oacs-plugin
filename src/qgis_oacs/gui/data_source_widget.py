from pathlib import Path

import qgis.core
import qgis.gui
from qgis.PyQt import QtCore
from qgis.PyQt import QtWidgets
from qgis.PyQt.uic import loadUiType

WidgetUi, _ = loadUiType(Path(__file__).parents[1] / "ui/data_source_widget.ui")


class OacsDataSourceWidget(qgis.gui.QgsAbstractDataSourceWidget, WidgetUi):

    def __init__(
            self,
            parent: QtWidgets.QWidget | None = None,
            fl: QtCore.Qt.WindowFlags | QtCore.Qt.WindowType = QtCore.Qt.Widget,
            widget_mode: qgis.core.QgsProviderRegistry.WidgetMode = qgis.core.QgsProviderRegistry.WidgetMode.Embedded,
    ):
        super().__init__(parent, fl, widget_mode)
        self.setupUi(self)