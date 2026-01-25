from qgis.gui import (
    QgsGui,
    QgisInterface,
)

from .gui.data_source_select_provider import OacsSourceSelectProvider


class QgisOacs:

    def __init__(self, iface: QgisInterface) -> None:
        self.source_select_provider = OacsSourceSelectProvider()

    def initGui(self) -> None:
        QgsGui.sourceSelectProviderRegistry().addProvider(self.source_select_provider)

    def unload(self):
        QgsGui.sourceSelectProviderRegistry().removeProvider(
            self.source_select_provider
        )
