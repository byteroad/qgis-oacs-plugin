"""Shared detail panel widget for displaying CSAPI resource metadata."""

import typing

import qgis.core
from qgis.PyQt import (
    QtCore,
    QtGui,
    QtWidgets,
)

from .. import models, utils
from ..client import oacs_client
from ..constants import IconPath
from ..settings import settings_manager

if typing.TYPE_CHECKING:
    from ..registry import OacsLayerEntry
    from ..settings import DataSourceConnectionSettings


class ResourceDetailPanel(QtWidgets.QWidget):
    """Shows metadata and actions for the currently selected tree node.

    Used both by the data source selector tree widgets and the CSAPI resource
    panel. Pass a ``connection`` explicitly when the active connection may
    differ from ``settings_manager.get_current_data_source_connection()``
    (e.g. in the panel where each entry has its own connection).
    """

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self._current_item: models.OacsItem | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        self._header_la = QtWidgets.QLabel("No item selected")
        self._header_la.setStyleSheet("font-weight: bold; font-size: 11pt;")
        self._header_la.setWordWrap(True)
        layout.addWidget(self._header_la)

        self._sub_la = QtWidgets.QLabel("")
        self._sub_la.setWordWrap(True)
        self._sub_la.setStyleSheet("color: palette(dark);")
        layout.addWidget(self._sub_la)

        self._props_tw = QtWidgets.QTableWidget()
        self._props_tw.setColumnCount(2)
        self._props_tw.setHorizontalHeaderLabels(["Property", "Value"])
        self._props_tw.horizontalHeader().setStretchLastSection(True)
        self._props_tw.verticalHeader().setVisible(False)
        self._props_tw.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self._props_tw.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self._props_tw.setAlternatingRowColors(True)
        layout.addWidget(self._props_tw, stretch=1)

        btn_row = QtWidgets.QHBoxLayout()
        btn_row.addStretch()
        self._action_pb = QtWidgets.QPushButton()
        self._action_pb.setEnabled(False)
        btn_row.addWidget(self._action_pb)
        layout.addLayout(btn_row)

    # ---------------------------------------------------------------- public --

    def clear(self) -> None:
        self._current_item = None
        self._header_la.setText("No item selected")
        self._sub_la.setText("")
        self._props_tw.clearContents()
        self._props_tw.setRowCount(0)
        self._action_pb.setEnabled(False)
        self._action_pb.setText("")

    def show_item(
            self,
            item: models.OacsItem,
            connection: "DataSourceConnectionSettings | None" = None,
    ) -> None:
        """Display a full OacsItem — used for both search-tree and panel browsed nodes."""
        self._current_item = item
        self._header_la.setText(item.name)
        if connection is None:
            connection = settings_manager.get_current_data_source_connection()
        if isinstance(item, models.OacsFeature):
            self._sub_la.setText(item.uid)
            self._fill_properties(self._properties_for_item(item, connection))
            self._configure_load_button(item, connection)
        elif isinstance(item, models.DataStream):
            self._sub_la.setText(item.description or "")
            self._fill_properties(self._properties_for_item(item, connection))
            obs_link = (
                item.get_observations_link()
                or models.Link(href=f"/datastreams/{item.id_}/observations")
            )
            if connection:
                self._configure_observations_button(
                    obs_link, connection, datastream=item)
            else:
                self._action_pb.setEnabled(False)
                self._action_pb.setText("")
        else:
            self._sub_la.setText(item.description or "")
            self._fill_properties(self._properties_for_item(item, connection))
            self._action_pb.setEnabled(False)
            self._action_pb.setText("")

    def show_entry(self, entry: "OacsLayerEntry") -> None:
        """Display properties for a loaded layer, read directly from its feature attributes."""
        self._current_item = None
        self._header_la.setText(entry.layer_name)
        self._sub_la.setText(entry.resource_type.upper())

        layer = qgis.core.QgsProject.instance().mapLayer(entry.layer_id)
        props: dict[str, str] = {}
        if layer:
            try:
                feature = next(layer.getFeatures())
                fields = layer.fields()
                for i in range(fields.count()):
                    val = feature[i]
                    if val is not None and str(val).strip():
                        props[fields[i].name()] = str(val)
            except StopIteration:
                pass
        props["URL"] = entry.self_link
        self._fill_properties(props)
        self._action_pb.setEnabled(False)
        self._action_pb.setText("")

    # --------------------------------------------------------------- private --

    @staticmethod
    def _properties_for_item(
            item: models.OacsItem,
            connection: "DataSourceConnectionSettings | None",
    ) -> dict[str, str]:
        props = item.get_renderable_properties()
        if connection and hasattr(type(item), "collection_path"):
            props["URL"] = item.get_detail_url(connection.base_url)
        return props

    def _configure_load_button(
            self,
            item: models.OacsFeature,
            connection: "DataSourceConnectionSettings | None",
    ) -> None:
        has_geometry = bool(item.geometry)
        self._action_pb.setText("Add to Map" if has_geometry else "Add as Layer")
        self._action_pb.setIcon(QtGui.QIcon(
            IconPath.feature_has_geospatial_location
            if has_geometry
            else IconPath.feature_does_not_have_geospatial_location
        ))
        self._action_pb.setEnabled(True)
        try:
            self._action_pb.clicked.disconnect()
        except (RuntimeError, TypeError):
            pass
        self._action_pb.clicked.connect(
            lambda: utils.load_oacs_feature_as_layer(item, connection=connection))

    def _configure_observations_button(
            self,
            link: models.Link,
            connection: "DataSourceConnectionSettings",
            datastream: "models.DataStream | None" = None,
    ) -> None:
        self._action_pb.setText("View observations")
        self._action_pb.setIcon(QtGui.QIcon(IconPath.datastream_type_observation))
        self._action_pb.setEnabled(True)
        try:
            self._action_pb.clicked.disconnect()
        except (RuntimeError, TypeError):
            pass
        self._action_pb.clicked.connect(
            lambda: oacs_client.initiate_observations_fetch(
                link, connection, datastream=datastream))

    def _fill_properties(self, properties: dict[str, str]) -> None:
        self._props_tw.clearContents()
        self._props_tw.setRowCount(len(properties))
        for row, (k, v) in enumerate(properties.items()):
            self._props_tw.setItem(row, 0, QtWidgets.QTableWidgetItem(str(k)))
            if k == "URL":
                link_label = QtWidgets.QLabel(f'<a href="{v}">{v}</a>')
                link_label.setOpenExternalLinks(True)
                link_label.setTextInteractionFlags(
                    QtCore.Qt.TextBrowserInteraction)
                link_label.setContentsMargins(4, 2, 4, 2)
                self._props_tw.setCellWidget(row, 1, link_label)
            else:
                self._props_tw.setItem(row, 1, QtWidgets.QTableWidgetItem(str(v)))
        self._props_tw.resizeColumnToContents(0)
        self._props_tw.resizeRowsToContents()

