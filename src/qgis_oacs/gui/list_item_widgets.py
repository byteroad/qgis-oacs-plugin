import functools
import json
import typing
from pathlib import Path

import qgis.core
from qgis.PyQt.uic import loadUiType
from qgis.PyQt import (
    QtCore,
    QtNetwork,
    QtWidgets,
)
from rich.jupyter import display

from .. import (
    constants,
    models,
    utils,
)
from ..utils import log_message
from ..settings import settings_manager

ResourceListItemWidgetUi, _ = loadUiType(
    Path(__file__).parents[1] / "ui/resource_list_item_widget.ui")


class ListItemWidget(QtWidgets.QWidget, ResourceListItemWidgetUi):
    name_la: QtWidgets.QLabel
    icon_la: QtWidgets.QLabel
    description_la: QtWidgets.QLabel
    feature_type_icon_la: QtWidgets.QLabel
    load_pb: QtWidgets.QPushButton
    details_pb: QtWidgets.QPushButton
    details_frame: QtWidgets.QFrame
    details_properties_tw: QtWidgets.QTableWidget
    resource: models.OacsFeatureProtocol

    details_fetch_started = QtCore.pyqtSignal()
    details_fetch_ended = QtCore.pyqtSignal()

    _already_fetched_details: bool

    def __init__(
            self,
            resource: models.OacsFeatureProtocol,
            parent: QtWidgets.QWidget | None = None
    ):
        super().__init__(parent)
        self.setupUi(self)
        self.details_pb.setText("Details...")
        self.details_frame.setVisible(False)
        self.resource = resource
        self._already_fetched_details = False
        target_size = 30
        scaled_pixmap = utils.create_pixmap_from_svg(
            self.resource.icon_path, target_size)
        self.icon_la.setPixmap(scaled_pixmap)
        self.icon_la.setToolTip(self.resource.icon_tooltip)
        self.icon_la.setFixedSize(target_size, target_size)
        self.name_la.setText(f"<h3>{self.resource.name}</h3>")
        self.name_la.setTextFormat(QtCore.Qt.TextFormat.RichText)
        description_contents = """
            <p>{uid}</p>
        """.format(
            uid=self.resource.summary,
        )
        self.description_la.setText(description_contents)
        self.description_la.setTextFormat(QtCore.Qt.TextFormat.RichText)
        self.details_pb.clicked.connect(self.toggle_details)
        self.load_pb.clicked.connect(self.load_as_layer)

    def toggle_details(self) -> None:
        if self.details_frame.isVisible():
            self.details_frame.setVisible(False)
            self.details_pb.setText("Details...")
        else:
            self.details_pb.setText("Hide details...")
            self.details_frame.setVisible(True)
            if not self._already_fetched_details:
                log_message(f"About to fetch details from the server...")
                self.initiate_fetch_details()

    def load_as_layer(self):
        if self._already_fetched_details:
            ...
        else:
            ...

    def initiate_fetch_details(self) -> None:
        current_connection = settings_manager.get_current_data_source_connection()
        request_url =QtCore.QUrl(
            f"{current_connection.base_url}{self.resource.collection_search_url_fragment}/{self.resource.id_}")
        if current_connection.use_f_query_param:
            request_query = QtCore.QUrlQuery()
            query_items = {"f": self.resource.f_parameter_value}
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
        reply: QtNetwork.QNetworkReply | None = network_fetcher_task.reply()
        if reply and reply.error() != QtNetwork.QNetworkReply.NetworkError.NoError:
            utils.log_message(f"Connection error (error_code: {reply.error()})")
        else:
            response_payload = network_fetcher_task.contentAsString()
            detailed_resource = self.resource.from_api_response(
                json.loads(response_payload)
            )
            log_message(f"{response_payload=}")
            self.resource = detailed_resource
            self._already_fetched_details = True
            self.render_details()
        self.details_fetch_ended.emit()

    def render_details(self) -> None:
        table_items = [
            (QtWidgets.QTableWidgetItem(k), QtWidgets.QTableWidgetItem(v))
            for k, v in self.resource.get_renderable_properties().items()
        ]
        self.details_properties_tw.setColumnCount(2)
        self.details_properties_tw.setRowCount(len(table_items))
        self.details_properties_tw.setHorizontalHeaderLabels(["Property", "Value"])
        self.details_properties_tw.horizontalHeader().setStretchLastSection(True)
        self.details_properties_tw.verticalHeader().setVisible(False)
        self.details_properties_tw.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.details_properties_tw.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        for row_index, (prop_name, prop_value) in enumerate(table_items):
            self.details_properties_tw.setItem(row_index, 0, prop_name)
            self.details_properties_tw.setItem(row_index, 1, prop_value)
        self.details_properties_tw.resizeRowsToContents()
        total_height = (
                self.details_properties_tw.horizontalHeader().height() +
                sum(self.details_properties_tw.rowHeight(i) for i in range(len(table_items))) +
                2  # Small margin for borders
        )
        self.details_properties_tw.setMinimumHeight(total_height)
        self.details_properties_tw.setMaximumHeight(total_height)

        self.related_resources_widget = RelatedResourcesWidget(
            links=self.resource.get_relevant_links(),
        )
        self.details_frame.layout().addWidget(self.related_resources_widget)



class ExpandableSection(QtWidgets.QFrame):
    """A collapsible section with a toggle button and content area."""

    def __init__(
            self,
            title: str,
            link: models.Link,
            parent: QtWidgets.QWidget | None = None
    ):
        super().__init__(parent)
        self.link = link
        self.is_expanded = False
        self.content_loaded = False

        self.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.setFrameShadow(QtWidgets.QFrame.Raised)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.toggle_button = QtWidgets.QPushButton()
        self.toggle_button.setText(f"▶ {title}")
        self.toggle_button.setFlat(True)
        self.toggle_button.setStyleSheet(
            "QPushButton { text-align: left; padding: 8px; font-weight: bold; }"
            "QPushButton:hover { background-color: palette(midlight); }"
        )
        self.toggle_button.clicked.connect(self.toggle)
        layout.addWidget(self.toggle_button)

        self.content_widget = QtWidgets.QWidget()
        self.content_layout = QtWidgets.QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(16, 8, 8, 8)
        self.content_widget.setVisible(False)
        layout.addWidget(self.content_widget)

    def toggle(self):
        title = self.toggle_button.text().split(" ", 1)[1]
        if self.content_widget.isVisible():  # need to hide
            icon = "▶"
            self.content_widget.setVisible(False)
        else:  # need to show
            icon = "▼"
            self.content_widget.setVisible(True)
            if not self.content_loaded:
                self.load_content()
        self.toggle_button.setText(f"{icon} {title}")

    def load_content(self):
        """Load content from the link. Override or connect to this method."""
        self.content_loaded = True
        if self.link.rel in (
            constants.LinkRelation.sampling_features,
            constants.OgcLinkRelation.sampling_features,
            constants.LinkRelation.data_streams,
            constants.OgcLinkRelation.data_streams,
        ):
            utils.dispatch_network_search_request(
                search_query=self.link.href,
                response_handler=self.render_details
            )
        else:
            ...  # not implemented yet

    def render_details(self, network_fetcher_task: qgis.core.QgsNetworkContentFetcherTask):
        reply: QtNetwork.QNetworkReply | None = network_fetcher_task.reply()
        if reply and reply.error() != QtNetwork.QNetworkReply.NetworkError.NoError:
            utils.log_message(f"Connection error (error_code: {reply.error()})")
        else:
            response_payload = json.loads(network_fetcher_task.contentAsString())
            if self.link.rel in (
                constants.LinkRelation.sampling_features,
                constants.OgcLinkRelation.sampling_features
            ):
                self.render_related_sampling_features(
                    models.SamplingFeatureList.from_api_response(response_payload)
                )
            elif self.link.rel in (
                constants.LinkRelation.data_streams,
                constants.OgcLinkRelation.data_streams,
            ):
                self.render_related_datastreams(
                    models.DataStreamList.from_api_response(response_payload)
                )
            else:
                ...  # not implemented yet

    def render_related_sampling_features(self, sampling_feature_list: models.SamplingFeatureList) -> None:
        for sampling_feature_item in sampling_feature_list.items:
            display_widget = ListItemWidget(resource=sampling_feature_item)
            self.content_layout.addWidget(display_widget)
        self.content_layout.addStretch()

    def render_related_datastreams(self, datastream_list: models.DataStreamList) -> None:
        for datastream_item in datastream_list.items:
            display_widget = ListItemWidget(resource=datastream_item)
            self.content_layout.addWidget(display_widget)
        self.content_layout.addStretch()


class RelatedResourcesWidget(QtWidgets.QWidget):

    def __init__(
            self,
            links: typing.Sequence[models.Link],
            parent: QtWidgets.QWidget | None = None
    ):
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        header = QtWidgets.QLabel("Related Resources")
        header.setStyleSheet("font-weight: bold; font-size: 12pt; padding: 8px;")
        layout.addWidget(header)

        self.sections_layout = QtWidgets.QVBoxLayout()
        self.sections_layout.setSpacing(2)

        for link in links:
            title = link.title or link.rel or "Unknown"
            section = ExpandableSection(title, link)
            self.sections_layout.addWidget(section)

        layout.addLayout(self.sections_layout)
        layout.addStretch()
