import json
import uuid

from qgis.PyQt import QtGui, QtWidgets

from .. import models, utils
from ..client import oacs_client
from ..settings import settings_manager


class ObservationsPanel(QtWidgets.QDockWidget):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__("CSAPI Observations", parent)
        self._datastream: models.DataStream | None = None
        self._pending_system_load_id: uuid.UUID | None = None
        self._build_ui()
        oacs_client.observations_fetched.connect(self._on_observations_fetched)
        oacs_client.system_list_fetched.connect(self._on_system_list_for_load)

    def _build_ui(self) -> None:
        container = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(container)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        header_row = QtWidgets.QHBoxLayout()
        self._header_la = QtWidgets.QLabel("")
        self._header_la.setStyleSheet("font-weight: bold;")
        self._header_la.setVisible(False)
        header_row.addWidget(self._header_la, stretch=1)
        self._load_system_pb = QtWidgets.QPushButton("Load system")
        self._load_system_pb.setVisible(False)
        self._load_system_pb.clicked.connect(self._on_load_system_clicked)
        header_row.addWidget(self._load_system_pb)
        self._clear_pb = QtWidgets.QPushButton("Clear")
        self._clear_pb.setEnabled(False)
        self._clear_pb.clicked.connect(self._on_clear_clicked)
        header_row.addWidget(self._clear_pb)
        layout.addLayout(header_row)

        self._text = QtWidgets.QPlainTextEdit()
        self._text.setReadOnly(True)
        mono = QtGui.QFontDatabase.systemFont(
            QtGui.QFontDatabase.SystemFont.FixedFont)
        self._text.setFont(mono)
        layout.addWidget(self._text)

        self.setWidget(container)

    def _on_observations_fetched(
            self,
            obs_list: models.ObservationList,
            _meta: object,
    ) -> None:
        self._datastream = obs_list.datastream
        self._pending_system_load_id = None
        if self._datastream:
            self._header_la.setText(f"DataStream: {self._datastream.name}")
            self._header_la.setVisible(True)
            self._load_system_pb.setVisible(True)
            self._load_system_pb.setEnabled(True)
        else:
            self._header_la.setVisible(False)
            self._load_system_pb.setVisible(False)
        parts = []
        for obs in obs_list.items:
            text = obs.payload.decode("utf-8", errors="replace")
            if "json" in obs.media_type.lower():
                try:
                    text = json.dumps(json.loads(text), indent=2)
                except json.JSONDecodeError:
                    pass
            parts.append(text)
        self._text.setPlainText("\n\n".join(parts))
        self._clear_pb.setEnabled(True)
        self.show()
        self.raise_()

    def _on_clear_clicked(self) -> None:
        self._datastream = None
        self._pending_system_load_id = None
        self._header_la.setVisible(False)
        self._header_la.setText("")
        self._load_system_pb.setVisible(False)
        self._text.clear()
        self._clear_pb.setEnabled(False)

    def _on_load_system_clicked(self) -> None:
        if not self._datastream:
            return
        connection = settings_manager.get_current_data_source_connection()
        if not connection:
            return
        meta = oacs_client.initiate_request_from_link(
            self._datastream.system_link, connection)
        if meta:
            self._pending_system_load_id = meta.request_id
            self._load_system_pb.setEnabled(False)

    def _on_system_list_for_load(
            self,
            system_list: models.SystemList,
            meta: object,
    ) -> None:
        if getattr(meta, "request_id", None) != self._pending_system_load_id:
            return
        self._pending_system_load_id = None
        connection = settings_manager.get_current_data_source_connection()
        for system in system_list.items:
            utils.load_oacs_feature_as_layer(system, connection=connection)
