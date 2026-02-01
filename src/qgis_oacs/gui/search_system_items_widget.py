import json
from pathlib import Path

import qgis.core
import qgis.gui
from qgis.PyQt import (
    QtCore,
    QtNetwork,
    QtWidgets,
)
from qgis.PyQt.uic import loadUiType

from .. import (
    models,
    utils,
)
from ..constants import IconPath
from ..settings import settings_manager
from .list_item_widgets import ListItemWidget

SearchSystemItemsWidgetUi, _ = loadUiType(
    Path(__file__).parents[1] / "ui/search_system_items_widget.ui")


class SearchSystemItemsWidget(QtWidgets.QWidget, SearchSystemItemsWidgetUi):
    id_le: QtWidgets.QLineEdit
    free_text_le: QtWidgets.QLineEdit
    advanced_filters_gb: QtWidgets.QGroupBox
    property_name_le: QtWidgets.QLineEdit
    property_value_le: QtWidgets.QLineEdit
    search_pb: QtWidgets.QPushButton
    search_results_layout: QtWidgets.QVBoxLayout

    _interactive_widgets: tuple[QtWidgets.QWidget, ...]

    search_started = QtCore.pyqtSignal()
    search_ended = QtCore.pyqtSignal()

    def __init__(
            self,
            parent: QtWidgets.QWidget=None
    ) -> None:
        super().__init__(parent)
        self.setupUi(self)
        self.search_pb.setIcon(utils.create_icon_from_svg(IconPath.search))
        self._interactive_widgets = (
            self.free_text_le,
            self.search_pb,
            self.advanced_filters_gb,
        )
        self.search_pb.clicked.connect(self.initiate_search)
        self.search_started.connect(self.toggle_interactive_widgets)
        self.search_ended.connect(self.toggle_interactive_widgets)

    def toggle_interactive_widgets(self, force_state: bool | None = None) -> None:
        utils.toggle_widgets_enabled(self._interactive_widgets, force_state)

    def initiate_search(self) -> None:
        utils.clear_search_results(self.search_results_layout)
        utils.dispatch_network_search_request(
            search_query=self.prepare_query(),
            response_handler=self.handle_search_response,
        )
        self.search_started.emit()

    def handle_search_response(
            self,
            network_fetcher_task: qgis.core.QgsNetworkContentFetcherTask
    ) -> None:
        # self.toggle_interactive_widgets(True)
        reply: QtNetwork.QNetworkReply | None = network_fetcher_task.reply()
        if reply and reply.error() != QtNetwork.QNetworkReply.NetworkError.NoError:
            utils.log_message(f"Connection error (error_code: {reply.error()})")
        else:
            response_payload = network_fetcher_task.contentAsString()
            # utils.log_message(response_payload)
            system_list = models.SystemList.from_api_response(json.loads(response_payload))
            for system_item in system_list.items:
                display_widget = ListItemWidget(resource=system_item)
                self.search_results_layout.addWidget(display_widget)
            self.search_results_layout.addStretch()
            self.search_ended.emit()

    def prepare_query(self) -> models.ClientSearchParams:
        query = {
            "q": raw_q if (raw_q := self.free_text_le.text()) != "" else None,
            "f": (
                models.System.f_parameter_value
                if settings_manager.get_current_data_source_connection().use_f_query_param
                else None
            )
        }
        query = {k: v for k, v in query.items() if v is not None} or None

        return models.ClientSearchParams(
            path=models.System.collection_search_url_fragment,
            query=query,
        )
