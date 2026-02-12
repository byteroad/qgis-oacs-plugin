import abc
import functools

from qgis.PyQt import QtWidgets

from ... import (
    models,
    utils,
)
from ...client import OacsRequestMetadata
from ...constants import IconPath
from ...settings import settings_manager
from ...client import oacs_client


class _AbstractQWidgetMeta(type(QtWidgets.QWidget), abc.ABCMeta):
    pass


class OacsResourceSearchWidgetBase(QtWidgets.QWidget, metaclass=_AbstractQWidgetMeta):
    free_text_le: QtWidgets.QLineEdit
    search_pb: QtWidgets.QPushButton
    search_results_layout: QtWidgets.QVBoxLayout

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.setupUi(self)
        self.search_pb.setIcon(utils.create_icon_from_svg(IconPath.search))
        self.search_pb.clicked.connect(self.initiate_search)
        oacs_client.request_started.connect(self.handle_request_started)
        oacs_client.request_ended.connect(self.handle_request_ended)

    @abc.abstractmethod
    def _initiate_search(self) -> None: ...

    @abc.abstractmethod
    def _get_interactive_widgets(self) -> tuple[QtWidgets.QWidget, ...]: ...

    @abc.abstractmethod
    def _get_display_widget(self, item: models.OacsItem) -> QtWidgets.QWidget: ...

    def toggle_interactive_widgets(
            self,
            force_state: bool | None = None
    ) -> None:
        utils.toggle_widgets_enabled(self._get_interactive_widgets(), force_state)

    def handle_request_started(self, metadata: OacsRequestMetadata) -> None:
        self.toggle_interactive_widgets(force_state=False)

    def handle_request_ended(self, metadata: OacsRequestMetadata) -> None:
        self.toggle_interactive_widgets(force_state=True)

    def initiate_search(self) -> None:
        utils.clear_search_results(self.search_results_layout)
        self._initiate_search()

    def _add_load_all_search_results_button(
            self,
            oacs_feature_list: models.OacsFeatureList,
            layer_name_prefix: str
    ) -> None:
        load_all_pb = QtWidgets.QPushButton("Load all search results")
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.setContentsMargins(9, 9, 9, 9)
        button_layout.addStretch()
        button_layout.addWidget(load_all_pb)
        load_all_pb.clicked.connect(
            functools.partial(
                utils.load_oacs_feature_list_as_layers,
                oacs_feature_list,
                name_prefix=layer_name_prefix
            )
        )
        self.search_results_layout.addLayout(button_layout)

    def handle_search_response(
            self,
            search_result: models.OacsFeatureList,
            request_metadata: OacsRequestMetadata
    ) -> None:
        if len(search_result.items) == 0:
            self.search_results_layout.addWidget(
                QtWidgets.QLabel("No items found"))
        else:
            load_all_pb = QtWidgets.QPushButton("Load all search results")
            button_layout = QtWidgets.QHBoxLayout()
            button_layout.setContentsMargins(9, 9, 9, 9)
            button_layout.addStretch()
            button_layout.addWidget(load_all_pb)
            load_all_pb.clicked.connect(
                functools.partial(
                    utils.load_oacs_feature_list_as_layers,
                    search_result,
                    name_prefix="-".join(
                        (
                            settings_manager.get_current_data_source_connection().name,
                            "systems"
                        )
                    )
                )
            )
            self.search_results_layout.addLayout(button_layout)
            for item in search_result.items:
                self.search_results_layout.addWidget(
                    self._get_display_widget(item)
                )
        self.search_results_layout.addStretch()
