from pathlib import Path

from qgis.PyQt import QtWidgets
from qgis.PyQt.uic import loadUiType

from .. import (
    client,
    models,
    utils,
)
from ..constants import IconPath
from ..settings import settings_manager
from .list_item_widgets import ListItemWidget

SearchSamplingFeatureItemsWidgetUi, _ = loadUiType(
    Path(__file__).parents[1] / "ui/search_sampling_feature_items_widget.ui")


class SearchSamplingFeatureItemsWidget(
    QtWidgets.QWidget,
    SearchSamplingFeatureItemsWidgetUi
):
    free_text_le: QtWidgets.QLineEdit
    search_pb: QtWidgets.QPushButton
    search_results_layout: QtWidgets.QVBoxLayout

    _interactive_widgets: tuple[QtWidgets.QWidget, ...]

    oacs_client: client.OacsClient

    def __init__(
            self,
            oacs_client: client.OacsClient,
            parent: QtWidgets.QWidget=None
    ) -> None:
        super().__init__(parent)
        self.setupUi(self)
        self.oacs_client = oacs_client
        self.search_pb.setIcon(utils.create_icon_from_svg(IconPath.search))
        self._interactive_widgets = (
            self.free_text_le,
            self.search_pb,
        )
        self.search_pb.clicked.connect(self.initiate_search)
        self.oacs_client.request_started.connect(self.handle_request_started)
        self.oacs_client.request_ended.connect(self.handle_request_ended)
        self.oacs_client.system_list_fetched.connect(self.handle_search_response)

    def handle_request_started(self, metadata: client.OacsRequestMetadata) -> None:
        if metadata.request_type in (
            client.RequestType.SAMPLING_FEATURE_LIST,
            client.RequestType.SAMPLING_FEATURE_ITEM,
        ):
            self.toggle_interactive_widgets(force_state=False)

    def handle_request_ended(self, metadata: client.OacsRequestMetadata) -> None:
        if metadata.request_type in (
                client.RequestType.SAMPLING_FEATURE_LIST,
                client.RequestType.SAMPLING_FEATURE_ITEM,
        ):
            self.toggle_interactive_widgets(force_state=True)

    def toggle_interactive_widgets(self, force_state: bool | None = None) -> None:
        utils.toggle_widgets_enabled(self._interactive_widgets, force_state)

    def initiate_search(self) -> None:
        utils.clear_search_results(self.search_results_layout)
        connection = settings_manager.get_current_data_source_connection()
        self.oacs_client.initiate_sampling_feature_list_search(
            connection,
        )

    def handle_search_response(self, sampling_feature_list: models.SamplingFeatureList) -> None:
        for sampling_feature_item in sampling_feature_list.items:
            display_widget = ListItemWidget(resource=sampling_feature_item)
            self.search_results_layout.addWidget(display_widget)
        self.search_results_layout.addStretch()
