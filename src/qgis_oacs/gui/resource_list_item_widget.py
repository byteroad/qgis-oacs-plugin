import functools
from pathlib import Path

import qgis.core
from qgis.PyQt.uic import loadUiType
from qgis.PyQt import (
    QtCore,
    QtGui,
    QtNetwork,
    QtSvg,
    QtWidgets,
)

from .. import (
    models,
    utils,
)
from ..settings import settings_manager

ResourceListItemWidgetUi, _ = loadUiType(
    Path(__file__).parents[1] / "ui/resource_list_item_widget.ui")


class SystemListItemWidget(QtWidgets.QWidget, ResourceListItemWidgetUi):
    name_la: QtWidgets.QLabel
    icon_la: QtWidgets.QLabel
    description_la: QtWidgets.QLabel
    feature_type_icon_la: QtWidgets.QLabel
    load_pb: QtWidgets.QPushButton
    details_pb: QtWidgets.QPushButton
    details_frame: QtWidgets.QFrame
    details_layout: QtWidgets.QVBoxLayout
    resource: models.System

    details_fetch_started = QtCore.pyqtSignal()
    details_fetch_ended = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

    _already_fetched_details: bool

    def __init__(
            self,
            resource: models.System,
            parent=None
    ):
        super().__init__(parent)
        self.setupUi(self)
        self.details_frame.setVisible(False)
        self.resource = resource
        self._already_fetched_details = False
        feature_type_icon_path = {
            models.SystemType.SENSOR: ":/plugins/qgis_oacs/sensors_krx.svg",
            models.SystemType.ACTUATOR: ":/plugins/qgis_oacs/stadia_controller.svg",
            models.SystemType.PLATFORM: ":/plugins/qgis_oacs/tools_ladder.svg",
            models.SystemType.SAMPLER: ":/plugins/qgis_oacs/labs.svg",
            models.SystemType.SYSTEM: ":/plugins/qgis_oacs/manufacturing.svg",
        }.get(self.resource.feature_type, ":/plugins/qgis_oacs/manufacturing.svg")
        target_size = 30
        scaled_pixmap = utils.create_pixmap_from_svg(
            feature_type_icon_path, target_size)
        self.icon_la.setPixmap(scaled_pixmap)
        self.icon_la.setToolTip(self.resource.feature_type.value)
        self.icon_la.setFixedSize(target_size, target_size)
        self.name_la.setText(f"<h3>{self.resource.name}</h3>")
        self.name_la.setTextFormat(QtCore.Qt.TextFormat.RichText)
        description_contents = """
            <p>{uid}</p>
        """.format(
            name=self.resource.name,
            feature_type=self.resource.feature_type,
            uid=self.resource.uid,
        )
        self.description_la.setText(description_contents)
        self.description_la.setTextFormat(QtCore.Qt.TextFormat.RichText)
        self.details_pb.clicked.connect(self.toggle_details)

    def toggle_details(self) -> None:
        if self.details_frame.isVisible():
            self.details_frame.setVisible(False)
            self.details_pb.setText("Details...")
        else:
            self.initiate_show_details()
            self.details_pb.setText("Hide details...")

    def initiate_show_details(self) -> None:
        if self._already_fetched_details:
            self.details_frame.setVisible(True)
        else:
            # fetch the details, render them, and finally show them
            test_label = QtWidgets.QLabel("hi there")
            self.details_layout.addWidget(test_label)
            self.details_layout.addStretch()
            self.details_frame.setVisible(True)
            # self.initiate_fetch_details()

    def initiate_fetch_details(self) -> None:
        current_connection = settings_manager.get_current_data_source_connection()
        request_url =QtCore.QUrl(f"{current_connection.base_url}/{self.resource.id_}")
        if current_connection.use_f_query_param:
            request_query = QtCore.QUrlQuery()
            query_items = {"f": "geojson"}
            request_query.setQueryItems(list(query_items.items()))
            request_url.setQuery(request_query)
        request = QtNetwork.QNetworkRequest(request_url)
        request.setRawHeader(b"Accept", b"application/geo+json")
        api_request_task = qgis.core.QgsNetworkContentFetcherTask(
            request=request,
            authcfg=current_connection.auth_config,
            description=f"test-oacs-plugin-fetch-system-details"
        )
        qgis.core.QgsApplication.taskManager().addTask(api_request_task)
        response_handler = functools.partial(
            self.handle_fetch_details_response,
            api_request_task,
        )
        api_request_task.fetched.connect(response_handler)
        self.details_fetch_started.emit()

    def handle_fetch_details_response(
            self,
            network_fetcher_task: qgis.core.QgsNetworkContentFetcherTask
    ) -> None:
        self.details_fetch_ended.emit()
        reply: QtNetwork.QNetworkReply | None = network_fetcher_task.reply()
        if reply and reply.error() != QtNetwork.QNetworkReply.NetworkError.NoError:
            utils.log_message(f"Connection error (error_code: {reply.error()})")
        else:
            response_payload = network_fetcher_task.contentAsString()
            utils.log_message(response_payload)
