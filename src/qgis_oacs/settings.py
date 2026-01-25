import contextlib
import dataclasses
import json
import typing
import uuid

import qgis.core
from qgis.PyQt import QtCore

_BASE_KEY = "/PythonPlugins/qgis_oacs"
_DATA_SOURCE_CONNECTIONS_GROUP = f"data_source_connections"
_CURRENT_DATA_SOURCE_CONNECTION_KEY = f"current_data_source"
_NETWORK_TIMEOUT_SETTINGS_KEY = f"network_timeout"


@contextlib.contextmanager
def qgis_settings(sub_group: str | None = None) -> typing.Iterator[qgis.core.QgsSettings]:
    """Helper for managing our own settings in QgsSettings"""
    settings = qgis.core.QgsSettings()
    full_key = f"{_BASE_KEY}/{sub_group}" if sub_group else _BASE_KEY
    settings.beginGroup(full_key)
    try:
        yield settings
    finally:
        settings.endGroup()


def _get_default_network_requests_timeout() -> int:
    with qgis_settings() as raw_network_settings:
        return raw_network_settings.value("network_requests_timeout", type=int, defaultValue=5000)


@dataclasses.dataclass
class DataSourceConnectionSettings:
    id: uuid.UUID
    name: str
    base_url: str
    network_requests_timeout: int = dataclasses.field(default_factory=_get_default_network_requests_timeout)
    auth_config: str | None = None

    @classmethod
    def from_qgs_settings(cls, connection_identifier: uuid.UUID):
        with qgis_settings(f"{_DATA_SOURCE_CONNECTIONS_GROUP}/{str(connection_identifier)}") as raw_connection_settings:
            try:
                reported_auth_cfg = raw_connection_settings.value("auth_config").strip()
            except AttributeError:
                reported_auth_cfg = None
            return cls(
                id=connection_identifier,
                name=raw_connection_settings.value("name"),
                base_url=raw_connection_settings.value("base_url"),
                auth_config=reported_auth_cfg,
                network_requests_timeout=raw_connection_settings.value("network_requests_timeout"),
            )

    def to_json(self):
        return json.dumps(dataclasses.asdict(self))

    def to_qgis_settings(self) -> None:
        with qgis_settings(f"{_DATA_SOURCE_CONNECTIONS_GROUP}/{str(self.id)}") as raw_connection_settings:
            raw_connection_settings.setValue("name", self.name)
            raw_connection_settings.setValue("base_url", self.base_url)
            raw_connection_settings.setValue("network_requests_timeout", self.network_requests_timeout)
            if self.auth_config:
                raw_connection_settings.setValue("auth_config", self.auth_config)


class OacsPluginSettingsManager(QtCore.QObject):
    current_data_source_connection_changed = QtCore.pyqtSignal(str)
    data_source_connection_created = QtCore.pyqtSignal(str)
    data_source_connection_deleted = QtCore.pyqtSignal(str)

    @staticmethod
    def list_data_source_connection_ids() -> list[uuid.UUID]:
        with qgis_settings(_DATA_SOURCE_CONNECTIONS_GROUP) as raw_connections_settings:
            return [uuid.UUID(i) for i in raw_connections_settings.childGroups()]

    @classmethod
    def list_data_source_connections(cls) -> list[DataSourceConnectionSettings]:
        result = []
        for connection_id in cls.list_data_source_connection_ids():
            result.append(DataSourceConnectionSettings.from_qgs_settings(connection_id))
        result.sort(key=lambda obj: obj.name)
        return result

    @staticmethod
    def get_data_source_connection(data_source_connection_id: uuid.UUID) -> DataSourceConnectionSettings:
        return DataSourceConnectionSettings.from_qgs_settings(data_source_connection_id)

    @staticmethod
    def get_current_data_source_connection() -> DataSourceConnectionSettings | None:
        with qgis_settings() as raw_settings:
            current_data_source_connection_id = raw_settings.value(_CURRENT_DATA_SOURCE_CONNECTION_KEY)
        return (
            DataSourceConnectionSettings.from_qgs_settings(
                uuid.UUID(current_data_source_connection_id)
            )
            if current_data_source_connection_id else None
        )

    def set_current_data_source_connection(
            self,
            data_source_connection_id: uuid.UUID | None
    ) -> None:
        if data_source_connection_id:
            if data_source_connection_id not in self.list_data_source_connection_ids():
                raise ValueError(f"Invalid connection identifier: {data_source_connection_id!r}")
            serialized_id = str(data_source_connection_id)
        else:
            serialized_id = None
        with qgis_settings() as raw_settings:
            raw_settings.setValue(_CURRENT_DATA_SOURCE_CONNECTION_KEY, serialized_id)
        self.current_data_source_connection_changed.emit(serialized_id)

    def clear_current_data_source_connection(self):
        with qgis_settings() as raw_settings:
            raw_settings.setValue(_CURRENT_DATA_SOURCE_CONNECTION_KEY, None)
        self.current_data_source_connection_changed.emit("")

    def save_data_source_connection(self, data_source_connection: DataSourceConnectionSettings) -> None:
        data_source_connection.to_qgis_settings()
        self.data_source_connection_created.emit(str(data_source_connection.id))

    def delete_data_source_connection(self, data_source_connection_id: uuid.UUID) -> None:
        serialized_id = str(data_source_connection_id)
        with qgis_settings() as raw_settings:
            current_serialized_id = raw_settings.value(_CURRENT_DATA_SOURCE_CONNECTION_KEY)
        if serialized_id == current_serialized_id:
            self.clear_current_data_source_connection()
        with qgis_settings(_DATA_SOURCE_CONNECTIONS_GROUP) as raw_connections_settings:
            raw_connections_settings.remove(serialized_id)
        self.data_source_connection_deleted.emit(serialized_id)


settings_manager = OacsPluginSettingsManager()