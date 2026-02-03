import datetime as dt
import re
import sys
import typing

import qgis.core
from qgis.PyQt import (
    QtCore,
    QtGui,
    QtSvg,
    QtWidgets,
)


def log_message(
        message: str,
        level: qgis.core.Qgis.MessageLevel = qgis.core.Qgis.MessageLevel.Info
) -> None:
    qgis.core.QgsMessageLog.logMessage(
        message, "qgis-oacs-plugin", level=level)


def show_message(
        message_bar: qgis.gui.QgsMessageBar,
        message: str,
        level: qgis.core.Qgis.MessageLevel | None = qgis.core.Qgis.MessageLevel.Info,
        add_loading_widget: bool = False,
) -> None:
    message_bar.clearWidgets()
    message_item = message_bar.createMessage(message)
    if add_loading_widget:
        progress_bar = QtWidgets.QProgressBar()
        progress_bar.setAlignment(
            QtCore.Qt.Alignment.AlignLeft | QtCore.Qt.Alignment.AlignVCenter
        )
        progress_bar.setMinimum(0)
        progress_bar.setMaximum(0)
        message_item.layout().addWidget(progress_bar)
    message_bar.pushWidget(message_item, level=level)


def toggle_widgets_enabled(
        widgets: typing.Sequence[QtWidgets.QWidget],
        force_state: bool | None = None
) -> None:
    for widget in widgets:
        if force_state is not None:
            widget.setEnabled(force_state)
        else:
            currently_enabled = widget.isEnabled()
            widget.setEnabled(not currently_enabled)


def parse_raw_rfc3339_datetime(value: str) -> dt.datetime:
    """Parse a string containing an RFC3339 datetime. This code is
    lightly adapted from:

    https://github.com/kurtraschke/pyRFC3339/blob/main/pyrfc3339/parser.py

    """
    # Python does not recognize "Z" as an alias for "+00:00", so we perform the
    # substitution here.
    value = re.sub("Z$", "+00:00", value, flags=re.IGNORECASE)

    # Python releases prior to 3.11 only support three or six digits of fractional
    # seconds. RFC 3339 is more lenient, so pad to six digits and truncate any
    # excessive digits.
    # This can be removed in October 2026, once Python 3.10 and earlier
    # have been retired.
    if sys.version_info < (3, 11):
        value = re.sub(
            r"(\.)([0-9]+)(?=[+\-][0-9]{2}:[0-9]{2}$)",
            lambda match: match.group(1) + match.group(2).ljust(6, "0")[:6],
            value,
        )

    dt_out = dt.datetime.fromisoformat(value)
    dt_out = dt_out.astimezone(dt.timezone.utc)
    return dt_out


def create_pixmap_from_svg(svg_path: str, target_size: int) -> QtGui.QPixmap:
    scale_factor = 3
    render_size = target_size * scale_factor

    renderer = QtSvg.QSvgRenderer(svg_path)
    pixmap = QtGui.QPixmap(render_size, render_size)
    pixmap.fill(QtCore.Qt.GlobalColor.transparent)
    painter = QtGui.QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return pixmap.scaled(
        target_size, target_size,
        QtCore.Qt.AspectRatioMode.KeepAspectRatio,
        QtCore.Qt.TransformationMode.SmoothTransformation
    )


def create_icon_from_svg(svg_path: str, target_size: int = 16) -> QtGui.QIcon:
    scaled_pixmap = create_pixmap_from_svg(svg_path, target_size)
    return QtGui.QIcon(scaled_pixmap)


def set_up_icon(
        label_widget: QtWidgets.QLabel,
        icon_path: str,
        tooltip: str
) -> None:
    target_size = 30
    scaled_pixmap = create_pixmap_from_svg(icon_path, target_size)
    label_widget.setPixmap(scaled_pixmap)
    label_widget.setToolTip(tooltip)
    label_widget.setFixedSize(target_size, target_size)


def clear_search_results(layout_displayer: QtWidgets.QLayout) -> None:
    while layout_displayer.count():
        item = layout_displayer.takeAt(0)
        if widget := item.widget():
            widget.deleteLater()
