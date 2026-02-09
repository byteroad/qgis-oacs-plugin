import typing
import uuid
from pathlib import Path

from qgis.PyQt.uic import loadUiType
from qgis.PyQt import (
    QtCore,
    QtGui,
    QtWidgets,
)

from .. import (
    models,
    utils,
)
from ..client import (
    oacs_client,
    OacsRequestMetadata,
)
from ..constants import IconPath
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
    item: models.System

    _already_fetched_details: bool
    _layer_load_has_been_requested: bool

    def __init__(
            self,
            item: models.System,
            parent: QtWidgets.QWidget | None = None
    ):
        super().__init__(parent)
        self.setupUi(self)
        self.item = item
        self.details_pb.setText("Details...")
        self.load_pb.setIcon(
            QtGui.QIcon(
                IconPath.feature_has_geospatial_location
                if self.item.geometry
                else IconPath.feature_does_not_have_geospatial_location
            )
        )
        self.details_frame.setVisible(False)
        self._already_fetched_details = False
        self._layer_load_has_been_requested = False
        utils.set_up_icon(
            self.icon_la,
            icon_path=(
                self.item.feature_type.get_icon_path()
                if self.item.feature_type
                else models.IconPath.system_type_system
            ),
            tooltip=(
                self.item.feature_type.value.upper()
                if self.item.feature_type
                else models.SystemType.SYSTEM.value.upper()
            )
        )
        self.name_la.setText(f"<h3>{self.item.name}</h3>")
        self.name_la.setTextFormat(QtCore.Qt.TextFormat.RichText)
        description_contents = """
            <p>{uid}</p>
        """.format(
            uid=self.item.uid,
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
            self.initiate_layer_loading()
        else:
            self._layer_load_has_been_requested = True
            self.initiate_fetch_details()


    def initiate_layer_loading(self) -> None:
        utils.load_oacs_feature_as_layer(self.item)

    def initiate_fetch_details(self) -> None:
        oacs_client.initiate_system_item_fetch(
            self.item.id_,
            settings_manager.get_current_data_source_connection()
        )

    def handle_fetch_details_response(
            self,
            item: models.System,
            request_metadata: OacsRequestMetadata
    ) -> None:
        if self.item.id_ != item.id_:
            return None
        self.item = item
        self._already_fetched_details = True

        if self._layer_load_has_been_requested:
            self._layer_load_has_been_requested = False
            return self.initiate_layer_loading()

        table_items = [
            (QtWidgets.QTableWidgetItem(k), QtWidgets.QTableWidgetItem(v))
            for k, v in self.item.get_renderable_properties().items()
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
            links=self.item.get_relevant_links(),
        )
        self.details_frame.layout().addWidget(self.related_resources_widget)


class DeploymentListItemWidget(QtWidgets.QWidget, ResourceListItemWidgetUi):
    name_la: QtWidgets.QLabel
    icon_la: QtWidgets.QLabel
    description_la: QtWidgets.QLabel
    load_pb: QtWidgets.QPushButton
    details_pb: QtWidgets.QPushButton
    details_frame: QtWidgets.QFrame
    details_properties_tw: QtWidgets.QTableWidget
    item: models.Deployment

    _already_fetched_details: bool
    _layer_load_has_been_requested: bool

    def __init__(
            self,
            item: models.Deployment,
            parent: QtWidgets.QWidget | None = None
    ):
        super().__init__(parent)
        self.setupUi(self)
        self.item = item
        self.details_pb.setText("Details...")
        self.load_pb.setIcon(
            QtGui.QIcon(
                IconPath.feature_has_geospatial_location
                if self.item.geometry
                else IconPath.feature_does_not_have_geospatial_location
            )
        )
        self.details_frame.setVisible(False)
        self._already_fetched_details = False
        self._layer_load_has_been_requested = False
        utils.set_up_icon(
            self.icon_la,
            icon_path=models.IconPath.deployment,
            tooltip=(
                self.item.feature_type.upper()
                if self.item.feature_type
                else "DEPLOYMENT"
            )
        )
        self.name_la.setText(f"<h3>{self.item.name}</h3>")
        self.name_la.setTextFormat(QtCore.Qt.TextFormat.RichText)
        description_contents = """
            <p>{uid}</p>
        """.format(
            uid=self.item.uid,
        )
        self.description_la.setText(description_contents)
        self.description_la.setTextFormat(QtCore.Qt.TextFormat.RichText)
        self.details_pb.clicked.connect(self.toggle_details)
        self.load_pb.clicked.connect(self.load_as_layer)
        oacs_client.deployment_item_fetched.connect(self.handle_fetch_details_response)

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
            self.initiate_layer_loading()
        else:
            self._layer_load_has_been_requested = True
            self.initiate_fetch_details()

    def initiate_layer_loading(self) -> None:
        utils.load_oacs_feature_as_layer(self.item)

    def initiate_fetch_details(self) -> None:
        oacs_client.initiate_deployment_item_fetch(
            self.item.id_,
            settings_manager.get_current_data_source_connection()
        )

    def handle_fetch_details_response(
            self,
            item: models.Deployment,
            request_metadata: OacsRequestMetadata
    ) -> None:
        if self.item.id_ != item.id_:
            return None
        self.item = item
        self._already_fetched_details = True

        if self._layer_load_has_been_requested:
            self._layer_load_has_been_requested = False
            return self.initiate_layer_loading()

        table_items = [
            (QtWidgets.QTableWidgetItem(k), QtWidgets.QTableWidgetItem(v))
            for k, v in self.item.get_renderable_properties().items()
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
            links=self.item.get_relevant_links(),
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
    item: models.SamplingFeature

    _already_fetched_details: bool
    _layer_load_has_been_requested: bool

    def __init__(
            self,
            item: models.SamplingFeature,
            parent: QtWidgets.QWidget | None = None
    ):
        super().__init__(parent)
        self.setupUi(self)
        self.item = item
        self.details_pb.setText("Details...")
        self.load_pb.setIcon(
            QtGui.QIcon(
                IconPath.feature_has_geospatial_location
                if self.item.geometry
                else IconPath.feature_does_not_have_geospatial_location
            )
        )
        self.details_frame.setVisible(False)
        self._already_fetched_details = False
        self._layer_load_has_been_requested = False
        utils.set_up_icon(
            self.icon_la,
            icon_path=models.IconPath.sampling_feature,
            tooltip=self.item.feature_type.upper()
        )
        self.name_la.setText(f"<h3>{self.item.name}</h3>")
        self.name_la.setTextFormat(QtCore.Qt.TextFormat.RichText)
        description_contents = """
            <p>{uid}</p>
        """.format(
            uid=self.item.uid,
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
            self.initiate_layer_loading()
        else:
            self._layer_load_has_been_requested = True
            self.initiate_fetch_details()

    def initiate_layer_loading(self) -> None:
        utils.load_oacs_feature_as_layer(self.item)

    def initiate_fetch_details(self) -> None:
        oacs_client.initiate_sampling_feature_item_fetch(
            self.item.id_,
            settings_manager.get_current_data_source_connection()
        )

    def handle_fetch_details_response(
            self,
            item: models.SamplingFeature,
            request_metadata: OacsRequestMetadata
    ) -> None:
        if self.item.id_ != item.id_:
            return None
        self.item = item
        self._already_fetched_details = True

        if self._layer_load_has_been_requested:
            self._layer_load_has_been_requested = False
            return self.initiate_layer_loading()

        table_items = [
            (QtWidgets.QTableWidgetItem(k), QtWidgets.QTableWidgetItem(v))
            for k, v in self.item.get_renderable_properties().items()
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
            links=self.item.get_relevant_links(),
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
    item: models.DataStream

    _already_fetched_details: bool

    def __init__(
            self,
            item: models.DataStream,
            parent: QtWidgets.QWidget | None = None
    ):
        super().__init__(parent)
        self.setupUi(self)
        self.details_pb.setText("Details...")
        self.details_frame.setVisible(False)
        self.item = item
        self._already_fetched_details = False
        utils.set_up_icon(
            self.icon_la,
            icon_path=(
                self.item.datastream_type.get_icon_path()
                if self.item.datastream_type
                else models.IconPath.datastream
            ),
            tooltip=(
                self.item.datastream_type.value.upper()
                if self.item.datastream_type
                else "DATASTREAM"
            ),
        )
        self.name_la.setText(f"<h3>{self.item.name}</h3>")
        self.name_la.setTextFormat(QtCore.Qt.TextFormat.RichText)
        description_contents = """
            <p>{description}</p>
        """.format(
            description=self.item.description or "",
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
            self.item.id_,
            settings_manager.get_current_data_source_connection()
        )

    def handle_fetch_details_response(
            self,
            item: models.DataStream,
            request_metadata: OacsRequestMetadata
    ) -> None:
        if self.item.id_ != item.id_:
            return None
        self.item = item
        self._already_fetched_details = True
        table_items = [
            (QtWidgets.QTableWidgetItem(k), QtWidgets.QTableWidgetItem(v))
            for k, v in self.item.get_renderable_properties().items()
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
            links=self.item.get_relevant_links(),
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
        for item in datastream_list.items:
            display_widget = DataStreamListItemWidget(item)
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
