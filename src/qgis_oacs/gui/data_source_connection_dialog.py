import functools
import json
import re
import uuid
from pathlib import Path

import qgis.core
import qgis.gui
from qgis.PyQt import (
    QtCore,
    QtNetwork,
    QtWidgets,
)
from qgis.PyQt.uic import loadUiType

from .. import models
from ..settings import (
    DataSourceConnectionSettings,
    settings_manager,
)
from ..utils import log_message

DialogUi, _ = loadUiType(Path(__file__).parents[1] / "ui/data_source_connection_dialog.ui")


class DataSourceConnectionDialog(QtWidgets.QDialog, DialogUi):
    name_le: QtWidgets.QLineEdit
    base_url_le: QtWidgets.QLineEdit
    authcfg_acs: qgis.gui.QgsAuthConfigSelect
    connect_pb: QtWidgets.QPushButton
    detected_capabilities_lw: QtWidgets.QListWidget
    button_box: QtWidgets.QDialogButtonBox
    message_bar: qgis.gui.QgsMessageBar

    data_source_connection_id: uuid.UUID
    _to_toggle_during_connection_test: tuple[QtWidgets.QWidget, ...]


    def __init__(
            self,
            parent: QtWidgets.QWidget | None = None,
            data_source_connection: DataSourceConnectionSettings | None = None
    ):
        super().__init__()
        self.setupUi(self)
        self.message_bar = qgis.gui.QgsMessageBar()
        self.message_bar.setSizePolicy(
            QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed
        )
        self.layout().insertWidget(0, self.message_bar, alignment=QtCore.Qt.AlignTop)

        self._to_toggle_during_connection_test = (
            self.connect_pb,
            self.button_box,
            self.authcfg_acs,
        )
        if data_source_connection:
            self.data_source_connection_id = data_source_connection.id
            self.populate_data_source_connection_info(data_source_connection)
        else:
            self.data_source_connection_id = uuid.uuid4()
        self.connect_pb.clicked.connect(self.test_data_source_connection)

    def accept(self):
        """Close the dialog with a success intent.

        Saves currently shown connection details in the QGIS settings and sets
        it as the current connection.
        """
        connection_settings = self.get_connection_settings()
        name_pattern = re.compile(
            fr"^{connection_settings.name}$|^{connection_settings.name}-\d+$"
        )
        duplicate_names = []
        for connection_conf in settings_manager.list_data_source_connections():
            if connection_conf.id == connection_settings.id:
                break  # we don't want to compare against ourselves
            if name_pattern.search(connection_conf.name) is not None:
                duplicate_names.append(connection_conf.name)
        if len(duplicate_names) > 0:
            connection_settings.name = (
                f"{connection_settings.name}-{len(duplicate_names)}"
            )
        settings_manager.save_data_source_connection(connection_settings)
        settings_manager.set_current_data_source_connection(connection_settings.id)
        super().accept()

    def get_connection_settings(self) -> DataSourceConnectionSettings:
        return DataSourceConnectionSettings(
            id=self.data_source_connection_id,
            name=self.name_le.text().strip(),
            base_url=self.base_url_le.text().strip(),
            auth_config=self.authcfg_acs.configId(),
        )

    def toggle_editable_widgets(self) -> None:
        for widget in self._to_toggle_during_connection_test:
            currently_enabled = widget.isEnabled()
            widget.setEnabled(not currently_enabled)

    def test_data_source_connection(self) -> None:
        self.toggle_editable_widgets()

        current_settings = self.get_connection_settings()

        connection_test_task = qgis.core.QgsNetworkContentFetcherTask(
            url=QtCore.QUrl(current_settings.base_url),
            authcfg=current_settings.auth_config,
            description=f"test-oacs-plugin-data-source-connection-{current_settings.id}"
        )
        task_manager = qgis.core.QgsApplication.taskManager()
        task_manager.addTask(connection_test_task)
        response_handler = functools.partial(self.handle_connection_test_response, connection_test_task)
        connection_test_task.fetched.connect(response_handler)

    def handle_connection_test_response(self, network_fetcher_task: qgis.core.QgsNetworkContentFetcherTask) -> None:
        reply: QtNetwork.QNetworkReply | None = network_fetcher_task.reply()
        if reply and reply.error() != QtNetwork.QNetworkReply.NetworkError.NoError:
            self.message_bar.pushMessage("Connection error", level=qgis.core.Qgis.MessageLevel.Critical)
            log_message(f"Connection error (error_code: {reply.error()})")
            self.toggle_editable_widgets()
        else:
            self.message_bar.pushMessage(
                "Connection successful", level=qgis.core.Qgis.MessageLevel.Info
            )
            landing_page = models.ApiLandingPage.from_api_response(
                json.loads(network_fetcher_task.contentAsString())
            )
            log_message(f"{landing_page.title=}")
            current_settings = self.get_connection_settings()
            conformance_request_task = qgis.core.QgsNetworkContentFetcherTask(
                url=QtCore.QUrl(landing_page.conformance_link.href),
                authcfg=current_settings.auth_config,
                description=f"test-oacs-plugin-data-source-connection-{current_settings.id}-conformance"
            )
            qgis.core.QgsApplication.taskManager().addTask(conformance_request_task)
            conformance_task_response_handler = functools.partial(
                self.handle_conformance_response,
                conformance_request_task
            )
            conformance_request_task.fetched.connect(conformance_task_response_handler)

    def handle_conformance_response(self, network_fetcher_task: qgis.core.QgsNetworkContentFetcherTask) -> None:
        self.toggle_editable_widgets()
        reply: QtNetwork.QNetworkReply | None = network_fetcher_task.reply()
        if reply and reply.error() != QtNetwork.QNetworkReply.NetworkError.NoError:
            self.message_bar.pushMessage(
                "Connection error retrieving conformance information",
                level=qgis.core.Qgis.MessageLevel.Critical
            )
            log_message(f"Connection error (error_code: {reply.error()})")
        else:
            conformance = models.Conformance.from_api_response(
                json.loads(network_fetcher_task.contentAsString())
            )
            log_message(f"{conformance=}")
            self.detected_capabilities_lw.clear()
            for conformance_item in conformance.conforms_to:
                list_item = QtWidgets.QListWidgetItem(str(conformance_item))
                list_item.setToolTip(conformance_item.conformance_url)
                self.detected_capabilities_lw.addItem(
                    list_item
                )

    def populate_data_source_connection_info(self, data_source_connection: DataSourceConnectionSettings) -> None:
        self.name_le.setText(data_source_connection.name)
        self.base_url_le.setText(data_source_connection.base_url)
        if data_source_connection.auth_config:
            self.authcfg_acs.setConfigId(data_source_connection.auth_config)
