import functools
import uuid
from pathlib import Path

import qgis.core
import qgis.gui
from qgis.PyQt import (
    QtCore,
    QtWidgets,
)
from qgis.PyQt.uic import loadUiType

from .. import utils
from ..client import (
    oacs_client,
    OacsRequestMetadata,
)
from ..settings import settings_manager
from .data_source_connection_dialog import DataSourceConnectionDialog
from .search_widgets.datastream_items_widget import SearchDataStreamItemsWidget
from .search_widgets.deployment_items_widget import SearchDeploymentItemsWidget
from .search_widgets.sampling_feature_items_widget import SearchSamplingFeatureItemsWidget
from .search_widgets.system_items_widget import SearchSystemItemsWidget

DataSourceWidgetUi, _ = loadUiType(Path(__file__).parents[1] / "ui/data_source_widget.ui")


class OacsDataSourceWidget(qgis.gui.QgsAbstractDataSourceWidget, DataSourceWidgetUi):
    connection_list_cmb: QtWidgets.QComboBox
    connection_new_btn: QtWidgets.QPushButton
    connection_edit_btn: QtWidgets.QPushButton
    connection_remove_btn: QtWidgets.QPushButton
    resource_types_tw: QtWidgets.QTabWidget
    resource_type_pages: dict[str, QtWidgets.QWidget]
    button_box: QtWidgets.QDialogButtonBox
    message_bar: qgis.gui.QgsMessageBar

    _connection_controls: tuple[QtWidgets.QWidget, ...]
    _interactive_widgets: tuple[QtWidgets.QWidget, ...]

    def __init__(
            self,
            parent: QtWidgets.QWidget | None = None,
            fl: QtCore.Qt.WindowFlags | QtCore.Qt.WindowType = QtCore.Qt.Widget,
            widget_mode: qgis.core.QgsProviderRegistry.WidgetMode = qgis.core.QgsProviderRegistry.WidgetMode.Embedded,
    ):
        super().__init__(parent, fl, widget_mode)
        self.setupUi(self)

        self.grid_layout = QtWidgets.QGridLayout()
        self.message_bar = qgis.gui.QgsMessageBar()
        self.message_bar.setSizePolicy(
            QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed
        )
        self.grid_layout.addWidget(
            self.message_bar, 0, 0, 1, 1, alignment=QtCore.Qt.AlignTop
        )
        self.layout().insertLayout(4, self.grid_layout)

        self.resource_type_pages = {
            "systems": SearchSystemItemsWidget(),
            "deployments": SearchDeploymentItemsWidget(),
            "sampling features": SearchSamplingFeatureItemsWidget(),
            "datastreams": SearchDataStreamItemsWidget(),
        }
        self.resource_types_tw.clear()
        for name, page in self.resource_type_pages.items():
            self.resource_types_tw.addTab(page, name.capitalize())

        oacs_client.request_started.connect(self.handle_search_started)
        oacs_client.request_ended.connect(self.handle_search_ended)
        oacs_client.request_failed.connect(self.handle_request_failed)

        self._connection_controls = (
            self.connection_list_cmb,
            self.connection_new_btn,
            self.connection_edit_btn,
            self.connection_remove_btn,
        )
        self._interactive_widgets = (
            *self._connection_controls,
        )
        settings_manager.current_data_source_connection_changed.connect(
            self.handle_current_connection_changed)

        add_new_handler = functools.partial(self.spawn_data_source_connection_dialog, add_new=True)
        self.connection_new_btn.clicked.connect(add_new_handler)
        self.connection_edit_btn.clicked.connect(self.spawn_data_source_connection_dialog)
        self.connection_remove_btn.clicked.connect(self.remove_current_data_source_connection)
        self.connection_list_cmb.activated.connect(self.update_current_data_source_connection)
        self.update_connections_combobox()
        self.handle_current_connection_changed()

    def spawn_data_source_connection_dialog(self, add_new: bool):
        if add_new:
            dialog = DataSourceConnectionDialog(parent=self)
        else:
            dialog = DataSourceConnectionDialog(
                parent=self,
                data_source_connection=settings_manager.get_current_data_source_connection(),
            )
        dialog.exec_()
        self.update_connections_combobox()

    def update_current_data_source_connection(self, index: int) -> None:
        """Updates the current data source connection in the QGIS settings."""
        serialized_currently_selected_id = self.connection_list_cmb.itemData(index)
        settings_manager.set_current_data_source_connection(uuid.UUID(serialized_currently_selected_id))

    def remove_current_data_source_connection(self) -> None:
        current_data_source_connection = settings_manager.get_current_data_source_connection()
        if self._spawn_data_source_connection_deletion_dialog(current_data_source_connection.name):
            # choose a new current connection
            all_data_source_connections = settings_manager.list_data_source_connections()
            new_current_connection_id = None
            for idx, connection in enumerate(all_data_source_connections):
                if connection.id == current_data_source_connection.id:
                    try:
                        new_current_connection_id = all_data_source_connections[idx - 1].id
                    except IndexError:
                        try:
                            new_current_connection_id = all_data_source_connections[idx + 1].id
                        except IndexError:
                            pass  # there are no other connections to set as the new current value
                    break
            settings_manager.set_current_data_source_connection(new_current_connection_id)
            settings_manager.delete_data_source_connection(current_data_source_connection.id)
            self.update_connections_combobox()

    def update_connections_combobox(self) -> None:
        self.connection_list_cmb.clear()
        for data_source_connection in settings_manager.list_data_source_connections():
            self.connection_list_cmb.addItem(data_source_connection.name, str(data_source_connection.id))
        current_connection = settings_manager.get_current_data_source_connection()
        if current_connection:
            index = self.connection_list_cmb.findData(str(current_connection.id))
            self.connection_list_cmb.setCurrentIndex(index)

    def handle_current_connection_changed(self) -> None:
        if settings_manager.get_current_data_source_connection():
            self.connection_edit_btn.setEnabled(True)
            self.connection_remove_btn.setEnabled(True)
        else:
            self.connection_edit_btn.setEnabled(False)
            self.connection_remove_btn.setEnabled(False)
        for widget_page in self.resource_type_pages.values():
            utils.clear_search_results(widget_page.search_results_layout)

    def handle_search_started(self):
        utils.toggle_widgets_enabled(self._interactive_widgets, force_state=False)

    def handle_search_ended(self):
        utils.toggle_widgets_enabled(self._interactive_widgets, force_state=True)

    def handle_request_failed(
            self,
            task_metadata: OacsRequestMetadata,
            error_message: str
    ) -> None:
        message = f"{task_metadata.request_type.value} - {error_message}"
        utils.show_message(
            self.message_bar,
            message,
            level=qgis.core.Qgis.MessageLevel.Warning
        )

    def _spawn_data_source_connection_deletion_dialog(self, connection_name: str):
        message = f"Remove connection {connection_name!r}?"
        confirmation = QtWidgets.QMessageBox.warning(
            self,
            "QGIS OACS Plugin",
            message,
            QtWidgets.QMessageBox.Yes,
            QtWidgets.QMessageBox.No,
        )
        return confirmation == QtWidgets.QMessageBox.Yes
