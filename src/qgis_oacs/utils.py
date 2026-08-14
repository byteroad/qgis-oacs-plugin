import dataclasses
import datetime as dt
import json
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

from .constants import (
    OACS_SCHEMA_VERSION_KEY,
    OACS_SCHEMA_VERSION,
    OACS_CONNECTION_ID_KEY,
    OACS_CONNECTION_BASE_URL_KEY,
    OACS_RESOURCE_TYPE_KEY,
    OACS_SELF_LINK_KEY,
    OACS_LINKS_JSON_KEY,
)

if typing.TYPE_CHECKING:
    from . import models
    from .settings import DataSourceConnectionSettings


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


def create_pixmap_from_svg(
        svg_path: str,
        target_size: int,
        colorize_with: QtGui.QColor | None = None
) -> QtGui.QPixmap:
    scale_factor = 3
    render_size = target_size * scale_factor

    renderer = QtSvg.QSvgRenderer(svg_path)
    pixmap = QtGui.QPixmap(render_size, render_size)
    pixmap.fill(QtCore.Qt.GlobalColor.transparent)
    painter = QtGui.QPainter(pixmap)
    renderer.render(painter)

    if colorize_with is not None:
        painter.setCompositionMode(
            QtGui.QPainter.CompositionMode.CompositionMode_SourceIn)
        painter.fillRect(pixmap.rect(), colorize_with)

    painter.end()
    return pixmap.scaled(
        target_size, target_size,
        QtCore.Qt.AspectRatioMode.KeepAspectRatio,
        QtCore.Qt.TransformationMode.SmoothTransformation
    )


def create_icon_from_svg(
        svg_path: str,
        target_size: int = 16,
        colorize_with: QtGui.QColor | None = None,
) -> QtGui.QIcon:
    scaled_pixmap = create_pixmap_from_svg(svg_path, target_size, colorize_with)
    return QtGui.QIcon(scaled_pixmap)



def clear_search_results(layout_displayer: QtWidgets.QLayout) -> None:
    while layout_displayer.count():
        item = layout_displayer.takeAt(0)
        if widget := item.widget():
            widget.deleteLater()
        elif layout := item.layout():
            clear_search_results(layout)


def set_oacs_layer_properties(
        layer: qgis.core.QgsMapLayer,
        connection: "DataSourceConnectionSettings",
        resource: "models.OacsItem",
) -> None:
    """Write CSAPI context onto a QGIS layer's custom properties."""
    self_link = resource.get_detail_url(connection.base_url)
    layer.setCustomProperty(OACS_SCHEMA_VERSION_KEY, OACS_SCHEMA_VERSION)
    layer.setCustomProperty(OACS_CONNECTION_ID_KEY, str(connection.id))
    layer.setCustomProperty(OACS_CONNECTION_BASE_URL_KEY, connection.base_url)
    layer.setCustomProperty(OACS_RESOURCE_TYPE_KEY, type(resource).__name__)
    layer.setCustomProperty(OACS_SELF_LINK_KEY, self_link)
    layer.setCustomProperty(
        OACS_LINKS_JSON_KEY,
        json.dumps([dataclasses.asdict(lnk) for lnk in resource.get_relevant_links()]),
    )


def _build_vector_layer(
        oacs_feat: "models.OacsFeature",
        connection: "DataSourceConnectionSettings | None" = None,
) -> qgis.core.QgsVectorLayer:
    """Create a single-feature QgsVectorLayer without adding it to the project."""
    if oacs_feat.geometry:
        geom_type = qgis.core.QgsWkbTypes.displayString(
            oacs_feat.geometry.wkbType())
        crs = oacs_feat.geometry.crs()
    else:
        geom_type = "None"
        crs = qgis.core.QgsCoordinateReferenceSystem("EPSG:4326")
    vector_layer = qgis.core.QgsVectorLayer(
        f"{geom_type}?crs={crs.authid()}", oacs_feat.name, "memory")
    provider = vector_layer.dataProvider()
    properties = oacs_feat.get_renderable_properties()
    provider.addAttributes(
        [qgis.core.QgsField(k, QtCore.QVariant.Type.String) for k in properties]
    )
    vector_layer.updateFields()
    qgis_feature = qgis.core.QgsFeature(vector_layer.fields())
    if oacs_feat.geometry:
        qgis_feature.setGeometry(oacs_feat.geometry)
    qgis_feature.setAttributes(list(properties.values()))
    provider.addFeatures([qgis_feature])
    vector_layer.updateExtents()
    if connection:
        set_oacs_layer_properties(vector_layer, connection, oacs_feat)
    return vector_layer


def load_oacs_feature_as_layer(
        oacs_feat: "models.OacsFeature",
        connection: "DataSourceConnectionSettings | None" = None,
) -> None:
    qgis.core.QgsProject.instance().addMapLayer(
        _build_vector_layer(oacs_feat, connection)
    )


def load_oacs_feature_list_as_layers(
        oacs_feature_list: "models.OacsFeatureList",
        name_prefix: str = "",
        connection: "DataSourceConnectionSettings | None" = None,
) -> None:
    layers = [
        _build_vector_layer(feat, connection)
        for feat in oacs_feature_list.items
    ]
    qgis.core.QgsProject.instance().addMapLayers(layers)
