import functools
import json
import typing
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
from ..settings import settings_manager
from .resource_list_item_widget import SystemListItemWidget

SearchSystemItemsWidgetUi, _ = loadUiType(
    Path(__file__).parents[1] / "ui/search_system_items_widget.ui")


class ResourceCollectionRetrieverProtocol(typing.Protocol):
    search_started: QtCore.pyqtSignal
    search_ended: QtCore.pyqtSignal

    def clear_search_results(self): ...


class SearchSystemItemsWidget(QtWidgets.QWidget, SearchSystemItemsWidgetUi):
    id_le: QtWidgets.QLineEdit
    free_text_le: QtWidgets.QLineEdit
    advanced_filters_gb: QtWidgets.QGroupBox
    property_name_le: QtWidgets.QLineEdit
    property_value_le: QtWidgets.QLineEdit
    search_pb: QtWidgets.QPushButton
    search_results_gb: QtWidgets.QGroupBox
    search_results_layout: QtWidgets.QVBoxLayout
    message_bar: qgis.gui.QgsMessageBar

    _interactive_widgets: tuple[QtWidgets.QWidget, ...]

    search_started = QtCore.pyqtSignal()
    search_ended = QtCore.pyqtSignal()

    def __init__(
            self,
            message_bar: qgis.gui.QgsMessageBar,
            parent: QtWidgets.QWidget=None
    ) -> None:
        super().__init__(parent)
        self.setupUi(self)
        self.search_pb.setIcon(
            utils.create_icon_from_svg(":/plugins/qgis_oacs/search.svg")
        )
        self._interactive_widgets = (
            self.free_text_le,
            self.advanced_filters_gb,
        )
        self.message_bar = message_bar
        self.search_pb.clicked.connect(self.initiate_search)
        self.search_started.connect(self.toggle_interactive_widgets)
        self.search_ended.connect(self.toggle_interactive_widgets)

    def toggle_interactive_widgets(self, force_state: bool | None = None) -> None:
        utils.toggle_widgets_enabled(self._interactive_widgets, force_state)

    def initiate_search(self) -> None:
        self.clear_search_results()
        search_query = self.prepare_query()
        request_query = QtCore.QUrlQuery()
        if search_query.query:
            request_query.setQueryItems(list(search_query.query.items()))
        current_connection = settings_manager.get_current_data_source_connection()
        request_url =QtCore.QUrl(f"{current_connection.base_url}{search_query.path}")
        if not request_query.isEmpty():
            request_url.setQuery(request_query)
        api_request_task = qgis.core.QgsNetworkContentFetcherTask(
            url=request_url,
            authcfg=current_connection.auth_config,
            description=f"test-oacs-plugin-search"
        )
        qgis.core.QgsApplication.taskManager().addTask(api_request_task)
        response_handler = functools.partial(
            self.handle_search_response,
            api_request_task,
        )
        api_request_task.fetched.connect(response_handler)
        self.toggle_interactive_widgets(False)
        self.search_started.emit()

    def handle_search_response(
            self,
            network_fetcher_task: qgis.core.QgsNetworkContentFetcherTask
    ) -> None:
        self.toggle_interactive_widgets(True)
        reply: QtNetwork.QNetworkReply | None = network_fetcher_task.reply()
        if reply and reply.error() != QtNetwork.QNetworkReply.NetworkError.NoError:
            self.message_bar.pushMessage(
                "Connection error", level=qgis.core.Qgis.MessageLevel.Critical)
            utils.log_message(f"Connection error (error_code: {reply.error()})")
        else:
            self.message_bar.pushMessage(
                "Connection successful", level=qgis.core.Qgis.MessageLevel.Info
            )
            response_payload = network_fetcher_task.contentAsString()
            # utils.log_message(response_payload)
            system_list = self.parse_geojson_response(json.loads(response_payload))
            for system_item in system_list.system_items:
                display_widget = SystemListItemWidget(resource=system_item)
                self.search_results_layout.addWidget(display_widget)
            self.search_results_layout.addStretch()
            utils.log_message(f"{system_list=}")

    def prepare_query(self) -> models.ClientSearchParams:
        query = {
            "q": raw_q if (raw_q := self.free_text_le.text()) != "" else None,
        }
        query = {k: v for k, v in query.items() if v is not None} or None

        return models.ClientSearchParams(
            path="/systems",
            query=query,
        )

    def parse_geojson_response(self, response: dict) -> models.SystemList:
        return models.SystemList.from_geojson_api_response(response)

    def clear_search_results(self) -> None:
        while self.search_results_layout.count():
            item = self.search_results_layout.takeAt(0)
            if widget := item.widget():
                widget.deleteLater()
