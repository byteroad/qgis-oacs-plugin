from pathlib import Path

from qgis.PyQt.uic import loadUiType
from qgis.PyQt import (
    QtCore,
    QtGui,
    QtSvg,
    QtWidgets,
)

from .. import (
    models,
    utils,
)

ResourceListItemWidgetUi, _ = loadUiType(
    Path(__file__).parents[1] / "ui/resource_list_item_widget.ui")


class SystemListItemWidget(QtWidgets.QWidget, ResourceListItemWidgetUi):
    name_la: QtWidgets.QLabel
    icon_la: QtWidgets.QLabel
    description_la: QtWidgets.QLabel
    feature_type_icon_la: QtWidgets.QLabel
    load_pb: QtWidgets.QPushButton
    details_pb: QtWidgets.QPushButton
    resource: models.System

    def __init__(
            self,
            resource: models.System,
            parent=None
    ):
        super().__init__(parent)
        self.setupUi(self)
        self.resource = resource
        feature_type_icon_path = {
            models.SystemType.SENSOR: ":/plugins/qgis_oacs/sensors_krx.svg",
            models.SystemType.ACTUATOR: ":/plugins/qgis_oacs/stadia_controller.svg",
            models.SystemType.PLATFORM: ":/plugins/qgis_oacs/tools_ladder.svg",
            models.SystemType.SAMPLER: ":/plugins/qgis_oacs/labs.svg",
            models.SystemType.SYSTEM: ":/plugins/qgis_oacs/manufacturing.svg",
        }.get(self.resource.feature_type, ":/plugins/qgis_oacs/manufacturing.svg")
        target_size = 30
        scaled_pixmap = utils.create_pixmap_from_svg(
            feature_type_icon_path, target_size)
        self.icon_la.setPixmap(scaled_pixmap)
        self.icon_la.setToolTip(self.resource.feature_type.value)
        self.icon_la.setFixedSize(target_size, target_size)
        self.name_la.setText(f"<h3>{self.resource.name}</h3>")
        self.name_la.setTextFormat(QtCore.Qt.TextFormat.RichText)
        description_contents = """
            <p>{uid}</p>
        """.format(
            name=self.resource.name,
            feature_type=self.resource.feature_type,
            uid=self.resource.uid,
        )
        self.description_la.setText(description_contents)
        self.description_la.setTextFormat(QtCore.Qt.TextFormat.RichText)
