import dataclasses
import json
import uuid

import qgis.core
from qgis.PyQt import QtCore

from .constants import (
    IconPath,
    OACS_SCHEMA_VERSION_KEY,
    OACS_CONNECTION_ID_KEY,
    OACS_CONNECTION_BASE_URL_KEY,
    OACS_RESOURCE_TYPE_KEY,
    OACS_SELF_LINK_KEY,
    OACS_LINKS_JSON_KEY,
)
from . import models
from .utils import log_message


@dataclasses.dataclass
class OacsLayerEntry:
    layer_id: str
    layer_name: str
    connection_id: uuid.UUID
    connection_base_url: str
    resource_type: str
    self_link: str
    links: list[models.Link]

    @property
    def entry_key(self) -> tuple[uuid.UUID, str]:
        return (self.connection_id, self.self_link)

    def get_type_label(self) -> str:
        return self.resource_type

    def get_layer(self) -> qgis.core.QgsMapLayer | None:
        return qgis.core.QgsProject.instance().mapLayer(self.layer_id)

    def has_spatial_representation(self) -> bool:
        qgis_layer = self.get_layer()
        return qgis_layer.isSpatial() if qgis_layer else False

    def get_icon_path(self) -> str:
        return {
            "System": IconPath.system_type_system,
            "Deployment": IconPath.deployment,
            "SamplingFeature": IconPath.sampling_feature,
            "Procedure": IconPath.procedure_type_procedure,
            "DataStream": IconPath.datastream,
        }.get(self.resource_type, IconPath.main_logo)


def _parse_layer(layer: qgis.core.QgsMapLayer) -> OacsLayerEntry | None:
    if not layer.customProperty(OACS_SCHEMA_VERSION_KEY):
        return None
    try:
        raw_links = json.loads(layer.customProperty(OACS_LINKS_JSON_KEY) or "[]")
        return OacsLayerEntry(
            layer_id=layer.id(),
            layer_name=layer.name(),
            connection_id=uuid.UUID(layer.customProperty(OACS_CONNECTION_ID_KEY)),
            connection_base_url=layer.customProperty(OACS_CONNECTION_BASE_URL_KEY),
            resource_type=layer.customProperty(OACS_RESOURCE_TYPE_KEY),
            self_link=layer.customProperty(OACS_SELF_LINK_KEY),
            links=[models.Link(**lnk) for lnk in raw_links],
        )
    except Exception as err:
        log_message(f"Could not parse CSAPI layer properties from {layer.name()!r}: {err}")
        return None


class OacsLayerRegistry(QtCore.QObject):
    """Tracks QGIS layers that were loaded from a CSAPI resource."""

    registry_changed = QtCore.pyqtSignal()

    def __init__(self, parent: QtCore.QObject | None = None) -> None:
        super().__init__(parent)
        self._entries: dict[tuple[uuid.UUID, str], OacsLayerEntry] = {}
        project = qgis.core.QgsProject.instance()
        project.layersAdded.connect(self._on_layers_added)
        project.layersWillBeRemoved.connect(self._on_layers_will_be_removed)
        project.cleared.connect(self._on_project_cleared)
        project.readProject.connect(self.rebuild_from_project)

    def rebuild_from_project(self) -> None:
        self._entries.clear()
        for layer in qgis.core.QgsProject.instance().mapLayers().values():
            entry = _parse_layer(layer)
            if entry:
                self._entries[entry.entry_key] = entry
        self.registry_changed.emit()

    def get_all_entries(self) -> list[OacsLayerEntry]:
        return list(self._entries.values())

    def entries_by_connection(self) -> dict[uuid.UUID, list[OacsLayerEntry]]:
        result: dict[uuid.UUID, list[OacsLayerEntry]] = {}
        for entry in self._entries.values():
            result.setdefault(entry.connection_id, []).append(entry)
        return result

    def _on_layers_added(self, layers: list) -> None:
        changed = False
        for layer in layers:
            entry = _parse_layer(layer)
            if entry:
                self._entries[entry.entry_key] = entry
                changed = True
        if changed:
            self.registry_changed.emit()

    def _on_layers_will_be_removed(self, layer_ids: list) -> None:
        changed = False
        for key, entry in list(self._entries.items()):
            if entry.layer_id in layer_ids:
                del self._entries[key]
                changed = True
        if changed:
            self.registry_changed.emit()

    def _on_project_cleared(self) -> None:
        self._entries.clear()
        self.registry_changed.emit()


layer_registry = OacsLayerRegistry()
