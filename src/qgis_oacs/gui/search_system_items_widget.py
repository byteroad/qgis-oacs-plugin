import functools
from pathlib import Path

from qgis.PyQt import QtWidgets
from qgis.PyQt.uic import loadUiType

from .. import (
    models,
    utils,
)
from ..client import (
    oacs_client,
    OacsRequestMetadata,
    RequestType,
)
from ..constants import IconPath
from ..settings import settings_manager
from .list_item_widgets import SystemListItemWidget

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
        oacs_client.request_started.connect(self.handle_request_started)
        oacs_client.request_ended.connect(self.handle_request_ended)
        oacs_client.system_list_fetched.connect(self.handle_search_response)

    def handle_request_started(self, metadata: OacsRequestMetadata) -> None:
        if metadata.request_type in (
                RequestType.SYSTEM_LIST,
                RequestType.SYSTEM_ITEM,
        ):
            self.toggle_interactive_widgets(force_state=False)

    def handle_request_ended(self, metadata: OacsRequestMetadata) -> None:
        if metadata.request_type in (
            RequestType.SYSTEM_LIST,
            RequestType.SYSTEM_ITEM,
        ):
            self.toggle_interactive_widgets(force_state=True)

    def toggle_interactive_widgets(
            self,
            force_state: bool | None = None
    ) -> None:
        utils.toggle_widgets_enabled(self._interactive_widgets, force_state)

    def initiate_search(self) -> None:
        utils.clear_search_results(self.search_results_layout)
        connection = settings_manager.get_current_data_source_connection()
        oacs_client.initiate_system_list_search(
            connection,
            q_filter=self.free_text_le.text()
        )

    def handle_search_response(
            self,
            system_list: models.SystemList,
            request_metadata: OacsRequestMetadata
    ) -> None:
        if len(system_list.items) == 0:
            self.search_results_layout.addWidget(
                QtWidgets.QLabel("No systems found"))
        else:
            load_all_pb = QtWidgets.QPushButton("Load all resources")
            button_layout = QtWidgets.QHBoxLayout()
            button_layout.setContentsMargins(0, 0, 0, 0)
            button_layout.addStretch()
            button_layout.addWidget(load_all_pb)
            load_all_pb.clicked.connect(
                functools.partial(self.load_all_as_layers, system_list)
            )
            self.search_results_layout.addLayout(button_layout)
            for item in system_list.items:
                display_widget = SystemListItemWidget(item)
                self.search_results_layout.addWidget(display_widget)
        self.search_results_layout.addStretch()

    def load_all_as_layers(self, system_list: models.SystemList) -> None:
        utils.load_oacs_feature_list_as_layers(system_list)
