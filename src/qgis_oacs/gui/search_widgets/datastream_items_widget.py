import typing
from pathlib import Path

from qgis.PyQt import QtWidgets
from qgis.PyQt.uic import loadUiType

from ... import models
from ...client import oacs_client
from ...settings import settings_manager
from .. import list_item_widgets
from .base import OacsResourceSearchWidgetBase

SearchDataStreamItemsWidgetUi, _ = loadUiType(
    Path(__file__).parents[2] / "ui/search_datastream_items_widget.ui")


class SearchDataStreamItemsWidget(
    OacsResourceSearchWidgetBase,
    SearchDataStreamItemsWidgetUi
):

    def __init__(
            self,
            parent: QtWidgets.QWidget=None
    ) -> None:
        super().__init__(parent)
        oacs_client.datastream_list_fetched.connect(self.handle_search_response)

    def _get_interactive_widgets(self) -> tuple[QtWidgets.QWidget, ...]:
        return (
            self.free_text_le,
            self.search_pb,
        )

    def _initiate_search(self) -> None:
        connection = settings_manager.get_current_data_source_connection()
        oacs_client.initiate_datastream_list_search(connection)

    def _get_display_widget(self, item: models.OacsItem) -> QtWidgets.QWidget:
        item = typing.cast(models.DataStream, item)
        return list_item_widgets.DataStreamListItemWidget(item)
