import qgis.core
import qgis.gui

from qgis.PyQt import QtCore
from qgis.PyQt import QtGui
from qgis.PyQt import QtWidgets

from .data_source_widget import OacsDataSourceWidget


class OacsSourceSelectProvider(qgis.gui.QgsSourceSelectProvider):

    def createDataSourceWidget(
            self,
            parent: QtWidgets.QWidget | None = None,
            fl: QtCore.Qt.WindowFlags | QtCore.Qt.WindowType = QtCore.Qt.Widget,
            widget_mode: qgis.core.QgsProviderRegistry.WidgetMode = qgis.core.QgsProviderRegistry.WidgetMode.Embedded,
    ):
        return OacsDataSourceWidget(parent, fl, widget_mode)

    def providerKey(self):
        return "qgis_oacs_provider"

    def icon(self):
        return QtGui.QIcon(":/plugins/qgis_oacs/graph_3.svg")

    def text(self):
        return "OGC API - Connected Systems"

    def toolTip(self):
        return "Add OGC API - Connected systems layer"

    def ordering(self):
        return qgis.gui.QgsSourceSelectProvider.OrderOtherProvider
