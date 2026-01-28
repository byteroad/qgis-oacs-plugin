import typing
from pathlib import Path

from qgis.PyQt import QtWidgets
from qgis.PyQt.uic import loadUiType

from .. import models

SearchFiltersSystemWidgetUi, _ = loadUiType(Path(__file__).parents[1] / "ui/search_filters_system_widget.ui")

class QueryPreparatorProtocol(typing.Protocol):

    def prepare_query(self) -> models.ClientSearchParams: ...


class SearchFiltersSystemWidget(QtWidgets.QWidget, SearchFiltersSystemWidgetUi):
    id_le: QtWidgets.QLineEdit
    free_text_le: QtWidgets.QLineEdit
    property_name_le: QtWidgets.QLineEdit
    property_value_le: QtWidgets.QLineEdit

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

    def prepare_query(self) -> models.ClientSearchParams:
        return models.ClientSearchParams(
            path="/systems"
        )
