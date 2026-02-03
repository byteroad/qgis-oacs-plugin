import typing
import uuid
from pathlib import Path

from qgis.PyQt.uic import loadUiType
from qgis.PyQt import (
    QtCore,
    QtWidgets,
)

from .. import (
    constants,
    models,
    utils,
)
from ..client import (
    oacs_client,
    OacsRequestMetadata,
)
from ..utils import log_message
from ..settings import settings_manager

ResourceListItemWidgetUi, _ = loadUiType(
    Path(__file__).parents[1] / "ui/resource_list_item_widget.ui")


class SystemListItemWidget(QtWidgets.QWidget, ResourceListItemWidgetUi):
    name_la: QtWidgets.QLabel
    icon_la: QtWidgets.QLabel
    description_la: QtWidgets.QLabel
    load_pb: QtWidgets.QPushButton
    details_pb: QtWidgets.QPushButton
    details_frame: QtWidgets.QFrame
    details_properties_tw: QtWidgets.QTableWidget
    system_item: models.System

    _already_fetched_details: bool

    def __init__(
            self,
            system_item: models.System,
            parent: QtWidgets.QWidget | None = None
    ):
        super().__init__(parent)
        self.setupUi(self)
        self.details_pb.setText("Details...")
        self.details_frame.setVisible(False)
        self.system_item = system_item
        self._already_fetched_details = False
        utils.set_up_icon(
            self.icon_la,
            self.system_item.icon_path,
            self.system_item.icon_tooltip
        )
        self.name_la.setText(f"<h3>{self.system_item.name}</h3>")
        self.name_la.setTextFormat(QtCore.Qt.TextFormat.RichText)
        description_contents = """
            <p>{summary}</p>
        """.format(
            summary=self.system_item.summary,
        )
        self.description_la.setText(description_contents)
        self.description_la.setTextFormat(QtCore.Qt.TextFormat.RichText)
        self.details_pb.clicked.connect(self.toggle_details)
        self.load_pb.clicked.connect(self.load_as_layer)
        oacs_client.system_item_fetched.connect(self.handle_fetch_details_response)

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
            raise NotImplementedError
        else:
            raise NotImplementedError

    def initiate_fetch_details(self) -> None:
        oacs_client.initiate_system_item_fetch(
            self.system_item.id_,
            settings_manager.get_current_data_source_connection()
        )

    def handle_fetch_details_response(
            self,
            system_item: models.System,
            request_metadata: OacsRequestMetadata
    ) -> None:
        if self.system_item.id_ != system_item.id_:
            return None
        self.system_item = system_item
        self._already_fetched_details = True
        table_items = [
            (QtWidgets.QTableWidgetItem(k), QtWidgets.QTableWidgetItem(v))
            for k, v in self.system_item.get_renderable_properties().items()
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
            links=self.system_item.get_relevant_links(),
        )
        self.details_frame.layout().addWidget(self.related_resources_widget)


class SamplingFeatureListItemWidget(QtWidgets.QWidget, ResourceListItemWidgetUi):
    name_la: QtWidgets.QLabel
    icon_la: QtWidgets.QLabel
    description_la: QtWidgets.QLabel
    load_pb: QtWidgets.QPushButton
    details_pb: QtWidgets.QPushButton
    details_frame: QtWidgets.QFrame
    details_properties_tw: QtWidgets.QTableWidget
    sampling_feature_item: models.SamplingFeature

    _already_fetched_details: bool

    def __init__(
            self,
            sampling_feature_item: models.SamplingFeature,
            parent: QtWidgets.QWidget | None = None
    ):
        super().__init__(parent)
        self.setupUi(self)
        self.details_pb.setText("Details...")
        self.details_frame.setVisible(False)
        self.sampling_feature_item = sampling_feature_item
        self._already_fetched_details = False
        utils.set_up_icon(
            self.icon_la,
            self.sampling_feature_item.icon_path,
            self.sampling_feature_item.icon_tooltip
        )
        self.name_la.setText(f"<h3>{self.sampling_feature_item.name}</h3>")
        self.name_la.setTextFormat(QtCore.Qt.TextFormat.RichText)
        description_contents = """
            <p>{summary}</p>
        """.format(
            summary=self.sampling_feature_item.summary,
        )
        self.description_la.setText(description_contents)
        self.description_la.setTextFormat(QtCore.Qt.TextFormat.RichText)
        self.details_pb.clicked.connect(self.toggle_details)
        self.load_pb.clicked.connect(self.load_as_layer)
        oacs_client.sampling_feature_item_fetched.connect(
            self.handle_fetch_details_response)

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
            raise NotImplementedError
        else:
            raise NotImplementedError

    def initiate_fetch_details(self) -> None:
        oacs_client.initiate_sampling_feature_item_fetch(
            self.sampling_feature_item.id_,
            settings_manager.get_current_data_source_connection()
        )

    def handle_fetch_details_response(
            self,
            sampling_feature_item: models.SamplingFeature,
            request_metadata: OacsRequestMetadata
    ) -> None:
        if self.sampling_feature_item.id_ != sampling_feature_item.id_:
            return None
        self.sampling_feature_item = sampling_feature_item
        self._already_fetched_details = True
        table_items = [
            (QtWidgets.QTableWidgetItem(k), QtWidgets.QTableWidgetItem(v))
            for k, v in self.sampling_feature_item.get_renderable_properties().items()
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
            links=self.sampling_feature_item.get_relevant_links(),
        )
        self.details_frame.layout().addWidget(self.related_resources_widget)


class DataStreamListItemWidget(QtWidgets.QWidget, ResourceListItemWidgetUi):
    name_la: QtWidgets.QLabel
    icon_la: QtWidgets.QLabel
    description_la: QtWidgets.QLabel
    load_pb: QtWidgets.QPushButton
    details_pb: QtWidgets.QPushButton
    details_frame: QtWidgets.QFrame
    details_properties_tw: QtWidgets.QTableWidget
    datastream_item: models.DataStream

    _already_fetched_details: bool

    def __init__(
            self,
            datastream_item: models.DataStream,
            parent: QtWidgets.QWidget | None = None
    ):
        super().__init__(parent)
        self.setupUi(self)
        self.details_pb.setText("Details...")
        self.details_frame.setVisible(False)
        self.datastream_item = datastream_item
        self._already_fetched_details = False
        utils.set_up_icon(
            self.icon_la,
            self.datastream_item.icon_path,
            self.datastream_item.icon_tooltip
        )
        self.name_la.setText(f"<h3>{self.datastream_item.name}</h3>")
        self.name_la.setTextFormat(QtCore.Qt.TextFormat.RichText)
        description_contents = """
            <p>{summary}</p>
        """.format(
            summary=self.datastream_item.summary,
        )
        self.description_la.setText(description_contents)
        self.description_la.setTextFormat(QtCore.Qt.TextFormat.RichText)
        self.details_pb.clicked.connect(self.toggle_details)
        self.load_pb.clicked.connect(self.load_as_layer)
        oacs_client.datastream_item_fetched.connect(self.handle_fetch_details_response)

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
            raise NotImplementedError
        else:
            raise NotImplementedError

    def initiate_fetch_details(self) -> None:
        oacs_client.initiate_datastream_item_fetch(
            self.datastream_item.id_,
            settings_manager.get_current_data_source_connection()
        )

    def handle_fetch_details_response(
            self,
            datastream_item: models.DataStream,
            request_metadata: OacsRequestMetadata
    ) -> None:
        if self.datastream_item.id_ != datastream_item.id_:
            return None
        self.datastream_item = datastream_item
        self._already_fetched_details = True
        table_items = [
            (QtWidgets.QTableWidgetItem(k), QtWidgets.QTableWidgetItem(v))
            for k, v in self.datastream_item.get_renderable_properties().items()
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
            links=self.datastream_item.get_relevant_links(),
        )
        self.details_frame.layout().addWidget(self.related_resources_widget)


class ExpandableSection(QtWidgets.QFrame):
    """A collapsible section with a toggle button and content area."""

    _pending_request_id: uuid.UUID | None

    def __init__(
            self,
            title: str,
            link: models.Link,
            parent: QtWidgets.QWidget | None = None
    ):
        super().__init__(parent)
        self.link = link
        self._pending_request_id = None

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
            "QPushButton:pressed { background-color: palette(window); }"
        )
        self.toggle_button.clicked.connect(self.toggle)
        layout.addWidget(self.toggle_button)

        self.content_widget = QtWidgets.QWidget()
        self.content_layout = QtWidgets.QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(16, 8, 8, 8)
        self.content_widget.setVisible(False)
        layout.addWidget(self.content_widget)

        oacs_client.sampling_feature_list_fetched.connect(
            self.handle_sampling_feature_list_response)
        oacs_client.datastream_list_fetched.connect(
            self.handle_datastream_list_response)

    def toggle(self):
        title = self.toggle_button.text().split(" ", 1)[1]
        if self.content_widget.isVisible():  # need to hide
            icon = "▶"
            self.content_widget.setVisible(False)
        else:  # need to show
            icon = "▼"
            self.content_widget.setVisible(True)
            if self._pending_request_id is None and self.content_layout.count() == 0:
                self.load_content()
        self.toggle_button.setText(f"{icon} {title}")

    def load_content(self):
        """Load content from the link."""
        connection = settings_manager.get_current_data_source_connection()
        request_metadata = oacs_client.initiate_request_from_link(
            self.link, connection)
        if request_metadata is not None:
            self._pending_request_id = request_metadata.request_id
        else:
            log_message(f"Unsupported link relation: {self.link.rel}")

    def handle_sampling_feature_list_response(
            self,
            sampling_feature_list: models.SamplingFeatureList,
            request_metadata: OacsRequestMetadata
    ) -> None:
        if self._pending_request_id != request_metadata.request_id:
            return
        self._pending_request_id = None
        for sampling_feature_item in sampling_feature_list.items:
            display_widget = SamplingFeatureListItemWidget(sampling_feature_item)
            self.content_layout.addWidget(display_widget)
        self.content_layout.addStretch()

    def handle_datastream_list_response(
            self,
            datastream_list: models.DataStreamList,
            request_metadata: OacsRequestMetadata
    ) -> None:
        if self._pending_request_id != request_metadata.request_id:
            return
        self._pending_request_id = None
        for datastream_item in datastream_list.items:
            display_widget = DataStreamListItemWidget(datastream_item)
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
