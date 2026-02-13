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

if typing.TYPE_CHECKING:
    from . import models


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
        elif layout := item.layout():
            clear_search_results(layout)


def load_oacs_feature_as_layer(oacs_feat: "models.OacsFeature") -> None:
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
        [
            qgis.core.QgsField(k, QtCore.QVariant.Type.String)
            for k in properties
        ]
    )
    vector_layer.updateFields()
    qgis_feature = qgis.core.QgsFeature(vector_layer.fields())
    if oacs_feat.geometry:
        qgis_feature.setGeometry(oacs_feat.geometry)
    qgis_feature.setAttributes(list(properties.values()))
    provider.addFeatures([qgis_feature])
    vector_layer.updateExtents()
    qgis.core.QgsProject.instance().addMapLayer(vector_layer)


def load_oacs_feature_list_as_layers(
        oacs_feature_list: "models.OacsFeatureList",
        name_prefix: str = ""
) -> None:
    # - some features may have geometry, others not
    # - features that have geometry may have different geometry types
    feats_to_render = {
        qgis.core.Qgis.WkbType.Point: [],
        qgis.core.Qgis.WkbType.MultiPoint: [],
        qgis.core.Qgis.WkbType.LineString: [],
        qgis.core.Qgis.WkbType.MultiLineString: [],
        qgis.core.Qgis.WkbType.Polygon: [],
        qgis.core.Qgis.WkbType.MultiPolygon: [],
        None: [],
    }
    for oacs_feat in oacs_feature_list.items:
        container = feats_to_render[geom.wkbType() if (geom := oacs_feat.geometry) else None]
        container.append(oacs_feat)
    qgis_layers = []
    for wkb_type, oacs_features in feats_to_render.items():
        if len(oacs_features) == 0:
            continue
        if wkb_type is None:
            geom_type = "None"
            crs = qgis.core.QgsCoordinateReferenceSystem("EPSG:4326")
            layer_name = "-".join((name_prefix, "no_geometry"))
        else:
            geom_type = qgis.core.QgsWkbTypes.displayString(wkb_type)
            layer_name = "-".join((name_prefix, geom_type.lower()))
            # assumes all feats have the same CRS
            crs = qgis.core.QgsCoordinateReferenceSystem(oacs_features[0].geometry.crs())
        vector_layer = qgis.core.QgsVectorLayer(
            f"{geom_type}?crs={crs.authid()}", layer_name, "memory")
        provider = vector_layer.dataProvider()
        _names = set()
        for oacs_feat in oacs_features:
            for property_name in oacs_feat.get_renderable_properties().keys():
                _names.add(property_name)
        property_names = list(_names)
        provider.addAttributes(
            [
                qgis.core.QgsField(k, QtCore.QVariant.Type.String)
                for k in property_names
            ]
        )
        vector_layer.updateFields()
        qgis_features = [
        ]
        for oacs_feat in oacs_features:
            qgis_feature = qgis.core.QgsFeature(vector_layer.fields())
            if oacs_feat.geometry:
                qgis_feature.setGeometry(oacs_feat.geometry)
            feat_attributes = []
            rendered_properties = oacs_feat.get_renderable_properties()
            for idx, name in enumerate(property_names):
                feat_attributes.append(rendered_properties.get(name, ""))
            qgis_feature.setAttributes(feat_attributes)
            qgis_features.append(qgis_feature)
        provider.addFeatures(qgis_features)
        vector_layer.updateExtents()
        qgis_layers.append(vector_layer)
    qgis.core.QgsProject.instance().addMapLayers(qgis_layers)
