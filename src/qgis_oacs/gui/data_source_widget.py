import functools
import typing
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

from ..settings import settings_manager
from ..utils import (
    log_message,
    show_message,
)
from . import search_filters
from .data_source_connection_dialog import DataSourceConnectionDialog

DataSourceWidgetUi, _ = loadUiType(Path(__file__).parents[1] / "ui/data_source_widget.ui")


class OacsDataSourceWidget(qgis.gui.QgsAbstractDataSourceWidget, DataSourceWidgetUi):
    connection_list_cmb: QtWidgets.QComboBox
    connection_new_btn: QtWidgets.QPushButton
    connection_edit_btn: QtWidgets.QPushButton
    connection_remove_btn: QtWidgets.QPushButton
    search_pb: QtWidgets.QPushButton
    search_filters_tw: QtWidgets.QTabWidget
    search_filter_pages: dict[str, search_filters.QueryPreparatorProtocol]
    search_filters_system_page: search_filters.SearchFiltersSystemWidget
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

        self.search_filter_pages = {
            "systems": search_filters.SearchFiltersSystemWidget()
        }
        self.search_filters_tw.clear()
        for name, page in self.search_filter_pages.items():
            self.search_filters_tw.addTab(page, name.capitalize())
        self._connection_controls = (
            self.connection_list_cmb,
            self.connection_new_btn,
            self.connection_edit_btn,
            self.connection_remove_btn,
        )
        self._interactive_widgets = (
            *self._connection_controls,
            self.search_pb,
        )
        settings_manager.current_data_source_connection_changed.connect(self.toggle_modifier_buttons)
        add_new_handler = functools.partial(self.spawn_data_source_connection_dialog, add_new=True)
        self.connection_new_btn.clicked.connect(add_new_handler)
        self.connection_edit_btn.clicked.connect(self.spawn_data_source_connection_dialog)
        self.connection_remove_btn.clicked.connect(self.remove_current_data_source_connection)
        self.connection_list_cmb.activated.connect(self.update_current_data_source_connection)
        self.search_pb.clicked.connect(self.initiate_search)
        self.update_connections_combobox()
        self.toggle_modifier_buttons()

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

    def toggle_modifier_buttons(self) -> None:
        if settings_manager.get_current_data_source_connection():
            self.connection_edit_btn.setEnabled(True)
            self.connection_remove_btn.setEnabled(True)
            self.search_pb.setEnabled(True)
        else:
            self.connection_edit_btn.setEnabled(False)
            self.connection_remove_btn.setEnabled(False)
            self.search_pb.setEnabled(False)

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

    def initiate_search(self) -> None:
        try:
            search_filters_page = self._get_current_search_filter_page()
        except RuntimeError as err:
            log_message(str(err))
            return

        search_query = search_filters_page.prepare_query()
        current_connection = settings_manager.get_current_data_source_connection()
        api_request_task = qgis.core.QgsNetworkContentFetcherTask(
            url=QtCore.QUrl(f"{current_connection.base_url}{search_query.path}"),
            authcfg=current_connection.auth_config,
            description=f"test-oacs-plugin-search"
        )
        qgis.core.QgsApplication.taskManager().addTask(api_request_task)
        response_handler = functools.partial(
            self.handle_search_response,
            api_request_task,
        )
        api_request_task.fetched.connect(response_handler)
        self.toggle_interactive_widgets()

    def _get_current_search_filter_page(self) -> search_filters.QueryPreparatorProtocol:
        if (current_tab_index := self.search_filters_tw.currentIndex()) == -1:
            raise RuntimeError("there is no current tab index")
        tab_title = self.search_filters_tw.tabText(current_tab_index)
        if not (
                search_filters_page := self.search_filter_pages.get(
                    tab_title.lower())
        ):
            raise RuntimeError("Could not find the current tab page")
        return search_filters_page

    def toggle_interactive_widgets(self, force_state: bool | None = None) -> None:
        try:
            current_search_filter_page = self._get_current_search_filter_page()
            relevant_widgets = self._interactive_widgets + (current_search_filter_page,)
        except RuntimeError as err:
            log_message(str(err))
            relevant_widgets = self._interactive_widgets
        for widget in relevant_widgets:
            if force_state is not None:
                widget.setEnabled(force_state)
            else:
                currently_enabled = widget.isEnabled()
                widget.setEnabled(not currently_enabled)


    def handle_search_response(
            self,
            network_fetcher_task: qgis.core.QgsNetworkContentFetcherTask
    ) -> None:
        self.toggle_interactive_widgets()
        reply: QtNetwork.QNetworkReply | None = network_fetcher_task.reply()
        if reply and reply.error() != QtNetwork.QNetworkReply.NetworkError.NoError:
            self.message_bar.pushMessage(
                "Connection error", level=qgis.core.Qgis.MessageLevel.Critical)
            log_message(f"Connection error (error_code: {reply.error()})")
        else:
            self.message_bar.pushMessage(
                "Connection successful", level=qgis.core.Qgis.MessageLevel.Info
            )
            log_message(network_fetcher_task.contentAsString())
