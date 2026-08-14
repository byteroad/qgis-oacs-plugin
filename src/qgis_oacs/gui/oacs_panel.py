"""Dockable panel for navigating loaded CSAPI resources and their associations."""

import uuid

import qgis.gui
from qgis.PyQt import (
    QtCore,
    QtWidgets,
)

from .. import models, utils
from ..client import oacs_client, OacsRequestMetadata
from ..constants import (
    IconPath,
    LINK_REL_TO_ICON,
    SPATIAL_COLOR,
)
from ..registry import (
    layer_registry,
    OacsLayerEntry,
)
from ..settings import settings_manager
from .detail_panel import ResourceDetailPanel


# ---------------------------------------------------------------------------
# Tree item type constants
# ---------------------------------------------------------------------------

_CONNECTION_ITEM_TYPE = 2001
_LOADED_RESOURCE_TYPE = 2002
_BROWSED_RESOURCE_TYPE = 2003
_GROUP_ITEM_TYPE = 2004
_PLACEHOLDER_TYPE = 2005

# Custom Qt data roles
_ITEM_DATA_ROLE = QtCore.Qt.UserRole          # OacsItem (for browsed items)
_DETAILS_FETCHED_ROLE = QtCore.Qt.UserRole + 1   # bool
_LINK_ROLE = QtCore.Qt.UserRole + 2           # Link (for group items)
_CONN_ID_ROLE = QtCore.Qt.UserRole + 3        # uuid.UUID (connection_id)
_ENTRY_ROLE = QtCore.Qt.UserRole + 4          # OacsLayerEntry (for loaded resource items)


def _connection_label(conn_id: uuid.UUID, fallback_url: str) -> str:
    for conn in settings_manager.list_data_source_connections():
        if conn.id == conn_id:
            return conn.name
    return fallback_url


class OacsResourcePanel(QtWidgets.QDockWidget):
    """Dockable panel showing CSAPI resources loaded on the canvas.

    Three tree levels:
      Connection → Loaded resource → Link-rel groups → Browsed related resources
    """

    def __init__(
            self,
            iface: qgis.gui.QgisInterface,
            parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__("CSAPI Resources", parent)
        self._iface = iface
        self._pending_link_requests: dict[uuid.UUID, QtWidgets.QTreeWidgetItem] = {}
        self._pending_detail_requests: dict[uuid.UUID, QtWidgets.QTreeWidgetItem] = {}

        self._build_ui()
        self._connect_signals()

    # ------------------------------------------------------------------ UI --

    def _build_ui(self) -> None:
        container = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)

        self._tree = QtWidgets.QTreeWidget()
        self._tree.setHeaderLabels(["Name / Resource", "Type"])
        self._tree.header().setStretchLastSection(False)
        self._tree.header().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        self._tree.header().setSectionResizeMode(
            1, QtWidgets.QHeaderView.ResizeToContents)
        self._tree.setUniformRowHeights(True)
        splitter.addWidget(self._tree)

        self._detail = ResourceDetailPanel()
        splitter.addWidget(self._detail)
        splitter.setSizes([230, 370])

        layout.addWidget(splitter)
        self.setWidget(container)
        self.setMinimumWidth(280)

    def _connect_signals(self) -> None:
        layer_registry.registry_changed.connect(self._rebuild_tree)

        # All list signals feed _populate_group (same pattern as the search tree)
        oacs_client.system_list_fetched.connect(self._on_system_list_fetched)
        oacs_client.deployment_list_fetched.connect(self._on_dep_list_fetched)
        oacs_client.sampling_feature_list_fetched.connect(self._on_sf_list_fetched)
        oacs_client.procedure_list_fetched.connect(self._on_procedure_list_fetched)
        oacs_client.datastream_list_fetched.connect(self._on_ds_list_fetched)

        # All item signals update browsed nodes that have been expanded
        oacs_client.system_item_fetched.connect(self._on_resource_item_fetched)
        oacs_client.deployment_item_fetched.connect(self._on_resource_item_fetched)
        oacs_client.sampling_feature_item_fetched.connect(self._on_resource_item_fetched)
        oacs_client.procedure_item_fetched.connect(self._on_resource_item_fetched)
        oacs_client.datastream_item_fetched.connect(self._on_resource_item_fetched)

        self._tree.itemExpanded.connect(self._on_item_expanded)
        self._tree.itemSelectionChanged.connect(self._on_selection_changed)

    # ----------------------------------------------------------- tree build --

    def _rebuild_tree(self) -> None:
        self._tree.clear()
        self._pending_link_requests.clear()
        self._pending_detail_requests.clear()

        entries_by_conn = layer_registry.entries_by_connection()
        if not entries_by_conn:
            placeholder = QtWidgets.QTreeWidgetItem(
                ["No CSAPI resources loaded", ""], _PLACEHOLDER_TYPE)
            placeholder.setFlags(placeholder.flags() & ~QtCore.Qt.ItemIsSelectable)
            self._tree.addTopLevelItem(placeholder)
            return

        for conn_id, entries in entries_by_conn.items():
            # Use first entry for fallback URL (all have same server for a given conn_id)
            label = _connection_label(conn_id, entries[0].connection_base_url)
            conn_item = QtWidgets.QTreeWidgetItem([label, "Connection"], _CONNECTION_ITEM_TYPE)
            conn_item.setIcon(0, utils.create_icon_from_svg(IconPath.main_logo, 16))
            conn_item.setData(0, _CONN_ID_ROLE, conn_id)
            for entry in entries:
                conn_item.addChild(self._make_loaded_resource_item(entry))
            self._tree.addTopLevelItem(conn_item)
            conn_item.setExpanded(True)

    def _make_loaded_resource_item(
            self, entry: OacsLayerEntry) -> QtWidgets.QTreeWidgetItem:
        item = QtWidgets.QTreeWidgetItem(
            [entry.layer_name, entry.get_type_label()], _LOADED_RESOURCE_TYPE)
        item.setIcon(
            0,
            utils.create_icon_from_svg(
                entry.get_icon_path(),
                16,
                colorize_with=(
                    SPATIAL_COLOR if entry.has_spatial_representation() else None)
            )
        )
        item.setData(0, _CONN_ID_ROLE, entry.connection_id)
        item.setData(0, _ENTRY_ROLE, entry)
        item.setData(0, _DETAILS_FETCHED_ROLE, False)
        item.setToolTip(0, entry.self_link)
        bold_font = item.font(0)
        bold_font.setBold(True)
        item.setFont(0, bold_font)
        item.setChildIndicatorPolicy(QtWidgets.QTreeWidgetItem.ShowIndicator)
        return item

    def _make_group_item(
            self,
            link: models.Link,
            conn_id: uuid.UUID,
    ) -> QtWidgets.QTreeWidgetItem:
        title = link.title or link.rel or "Related"
        item = QtWidgets.QTreeWidgetItem([title, ""], _GROUP_ITEM_TYPE)
        item.setData(0, _LINK_ROLE, link)
        item.setData(0, _CONN_ID_ROLE, conn_id)
        item.setData(0, _DETAILS_FETCHED_ROLE, False)
        icon_path = LINK_REL_TO_ICON.get(link.rel, IconPath.search)
        item.setIcon(0, utils.create_icon_from_svg(icon_path, 14))
        item.addChild(QtWidgets.QTreeWidgetItem(["…", ""], _PLACEHOLDER_TYPE))
        return item

    def _make_browsed_item(
            self,
            oacs_item: models.OacsItem,
            conn_id: uuid.UUID,
    ) -> QtWidgets.QTreeWidgetItem:
        item = QtWidgets.QTreeWidgetItem(
            [oacs_item.name, oacs_item.get_type_label()],
            _BROWSED_RESOURCE_TYPE
        )
        icon_color = None
        if isinstance(oacs_item, models.OacsFeature):
            if oacs_item.geometry:
                icon_color = SPATIAL_COLOR
        item.setIcon(
            0,
            utils.create_icon_from_svg(
                oacs_item.get_icon_path(),
                14,
                colorize_with=icon_color
            )
        )
        item.setData(0, _ITEM_DATA_ROLE, oacs_item)
        item.setData(0, _CONN_ID_ROLE, conn_id)
        item.setData(0, _DETAILS_FETCHED_ROLE, False)
        item.setChildIndicatorPolicy(QtWidgets.QTreeWidgetItem.ShowIndicator)
        if isinstance(oacs_item, models.OacsFeature):
            item.setToolTip(0, oacs_item.uid)
        return item

    # --------------------------------------------------------- expansion -----

    def _on_item_expanded(self, item: QtWidgets.QTreeWidgetItem) -> None:
        itype = item.type()

        if itype == _LOADED_RESOURCE_TYPE:
            if not item.data(0, _DETAILS_FETCHED_ROLE):
                entry: OacsLayerEntry = item.data(0, _ENTRY_ROLE)
                conn_id: uuid.UUID = item.data(0, _CONN_ID_ROLE)
                while item.childCount():
                    item.removeChild(item.child(0))
                if entry.links:
                    item.setData(0, _DETAILS_FETCHED_ROLE, True)
                    for link in entry.links:
                        item.addChild(self._make_group_item(link, conn_id))
                else:
                    item.addChild(QtWidgets.QTreeWidgetItem(
                        ["Loading…", ""], _PLACEHOLDER_TYPE))
                    self._fetch_loaded_resource_details(item, entry)

        elif itype == _BROWSED_RESOURCE_TYPE:
            if not item.data(0, _DETAILS_FETCHED_ROLE):
                item.addChild(QtWidgets.QTreeWidgetItem(
                    ["Loading…", ""], _PLACEHOLDER_TYPE))
                oacs_item: models.OacsItem = item.data(0, _ITEM_DATA_ROLE)
                self._fetch_browsed_item_details(item, oacs_item)

        elif itype == _GROUP_ITEM_TYPE:
            if not item.data(0, _DETAILS_FETCHED_ROLE):
                link: models.Link = item.data(0, _LINK_ROLE)
                self._fetch_group_contents(item, link)

    def _fetch_group_contents(
            self,
            group_item: QtWidgets.QTreeWidgetItem,
            link: models.Link,
    ) -> None:
        if group_item in self._pending_link_requests.values():
            return
        conn_id: uuid.UUID = group_item.data(0, _CONN_ID_ROLE)
        connection = self._get_connection(conn_id)
        if not connection:
            self._replace_children_with_placeholder(
                group_item, "Connection not found")
            group_item.setData(0, _DETAILS_FETCHED_ROLE, True)
            return
        meta = oacs_client.initiate_request_from_link(link, connection)
        if meta:
            self._pending_link_requests[meta.request_id] = group_item
        else:
            self._replace_children_with_placeholder(
                group_item, "Not supported yet")
            group_item.setData(0, _DETAILS_FETCHED_ROLE, True)

    def _fetch_browsed_item_details(
            self,
            tree_item: QtWidgets.QTreeWidgetItem,
            item: models.OacsItem,
    ) -> None:
        if tree_item in self._pending_detail_requests.values():
            return
        conn_id: uuid.UUID = tree_item.data(0, _CONN_ID_ROLE)
        connection = self._get_connection(conn_id)
        if not connection:
            self._replace_children_with_placeholder(
                tree_item, "Connection not found")
            tree_item.setData(0, _DETAILS_FETCHED_ROLE, True)
            return
        if isinstance(item, models.System):
            meta = oacs_client.initiate_system_item_fetch(item.id_, connection)
        elif isinstance(item, models.Deployment):
            meta = oacs_client.initiate_deployment_item_fetch(item.id_, connection)
        elif isinstance(item, models.SamplingFeature):
            meta = oacs_client.initiate_sampling_feature_item_fetch(item.id_, connection)
        elif isinstance(item, models.Procedure):
            meta = oacs_client.initiate_procedure_item_fetch(item.id_, connection)
        elif isinstance(item, models.DataStream):
            meta = oacs_client.initiate_datastream_item_fetch(item.id_, connection)
        else:
            tree_item.setData(0, _DETAILS_FETCHED_ROLE, True)
            tree_item.setChildIndicatorPolicy(
                QtWidgets.QTreeWidgetItem.DontShowIndicator)
            return
        self._pending_detail_requests[meta.request_id] = tree_item

    def _fetch_loaded_resource_details(
            self,
            tree_item: QtWidgets.QTreeWidgetItem,
            entry: OacsLayerEntry,
    ) -> None:
        """Fetch a loaded resource's full record from the server when links_json is empty."""
        if tree_item in self._pending_detail_requests.values():
            return
        connection = self._get_connection(entry.connection_id)
        if not connection:
            self._replace_children_with_placeholder(tree_item, "Connection not found")
            tree_item.setData(0, _DETAILS_FETCHED_ROLE, True)
            return
        resource_id = entry.self_link.rstrip("/").rsplit("/", 1)[-1]
        dispatch = {
            "System": oacs_client.initiate_system_item_fetch,
            "Deployment": oacs_client.initiate_deployment_item_fetch,
            "SamplingFeature": oacs_client.initiate_sampling_feature_item_fetch,
            "Procedure": oacs_client.initiate_procedure_item_fetch,
            "DataStream": oacs_client.initiate_datastream_item_fetch,
        }
        fetch_fn = dispatch.get(entry.resource_type)
        if not fetch_fn:
            self._replace_children_with_placeholder(
                tree_item, f"Unsupported resource type: {entry.resource_type}")
            tree_item.setData(0, _DETAILS_FETCHED_ROLE, True)
            return
        meta = fetch_fn(resource_id, connection)
        self._pending_detail_requests[meta.request_id] = tree_item

    # ---------------------------------------------------- response handlers --

    def _on_system_list_fetched(
            self, system_list: models.SystemList, meta: OacsRequestMetadata) -> None:
        self._populate_group(meta.request_id, system_list.items)

    def _on_dep_list_fetched(
            self, dep_list: models.DeploymentList, meta: OacsRequestMetadata) -> None:
        self._populate_group(meta.request_id, dep_list.items)

    def _on_sf_list_fetched(
            self, sf_list: models.SamplingFeatureList, meta: OacsRequestMetadata) -> None:
        self._populate_group(meta.request_id, sf_list.items)

    def _on_procedure_list_fetched(
            self, pl: models.ProcedureList, meta: OacsRequestMetadata) -> None:
        self._populate_group(meta.request_id, pl.items)

    def _on_ds_list_fetched(
            self, ds_list: models.DataStreamList, meta: OacsRequestMetadata) -> None:
        self._populate_group(meta.request_id, ds_list.items)

    def _populate_group(
            self,
            request_id: uuid.UUID,
            items: list[models.OacsItem],
    ) -> None:
        group_item = self._pending_link_requests.pop(request_id, None)
        if group_item is None:
            return
        group_item.setData(0, _DETAILS_FETCHED_ROLE, True)
        while group_item.childCount():
            group_item.removeChild(group_item.child(0))
        if not items:
            group_item.addChild(
                QtWidgets.QTreeWidgetItem(["(none)", ""], _PLACEHOLDER_TYPE))
            return
        conn_id: uuid.UUID = group_item.data(0, _CONN_ID_ROLE)
        count = len(items)
        group_item.setText(
            0,
            f"{group_item.text(0).split(' (')[0]} ({count})"
        )
        for oacs_item in items:
            group_item.addChild(self._make_browsed_item(oacs_item, conn_id))

    def _on_resource_item_fetched(
            self,
            item: models.OacsItem,
            meta: OacsRequestMetadata,
    ) -> None:
        tree_item = self._pending_detail_requests.pop(meta.request_id, None)
        if tree_item is None:
            return
        tree_item.setData(0, _ITEM_DATA_ROLE, item)
        tree_item.setData(0, _DETAILS_FETCHED_ROLE, True)
        while tree_item.childCount():
            tree_item.removeChild(tree_item.child(0))
        links = item.get_relevant_links()
        conn_id: uuid.UUID = tree_item.data(0, _CONN_ID_ROLE)
        if links:
            for link in links:
                tree_item.addChild(self._make_group_item(link, conn_id))
        else:
            tree_item.setChildIndicatorPolicy(
                QtWidgets.QTreeWidgetItem.DontShowIndicator)
        selected = self._tree.selectedItems()
        if selected and selected[0] is tree_item and tree_item.type() == _BROWSED_RESOURCE_TYPE:
            connection = self._get_connection(conn_id)
            self._detail.show_item(item, connection=connection)

    # ---------------------------------------------------- selection / detail --

    def _on_selection_changed(self) -> None:
        selected = self._tree.selectedItems()
        if not selected:
            self._detail.clear()
            return
        item = selected[0]
        itype = item.type()

        if itype == _LOADED_RESOURCE_TYPE:
            entry: OacsLayerEntry = item.data(0, _ENTRY_ROLE)
            self._detail.show_entry(entry)

        elif itype == _BROWSED_RESOURCE_TYPE:
            oacs_item = item.data(0, _ITEM_DATA_ROLE)
            if oacs_item is not None:
                conn_id: uuid.UUID = item.data(0, _CONN_ID_ROLE)
                connection = self._get_connection(conn_id)
                self._detail.show_item(oacs_item, connection=connection)
            else:
                self._detail.clear()

        else:
            self._detail.clear()

    # ------------------------------------------------------------ helpers ----

    @staticmethod
    def _get_connection(conn_id: uuid.UUID):
        try:
            return settings_manager.get_data_source_connection(conn_id)
        except Exception:
            return None

    @staticmethod
    def _replace_children_with_placeholder(
            item: QtWidgets.QTreeWidgetItem,
            message: str,
    ) -> None:
        while item.childCount():
            item.removeChild(item.child(0))
        item.addChild(
            QtWidgets.QTreeWidgetItem([message, ""], _PLACEHOLDER_TYPE))
