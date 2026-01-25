from qgis.gui import QgisInterface

# this import is crucial for Qt to initialize the plugin's resources correctly, do not remove
from . import resources  # noqa


def classFactory(iface: QgisInterface):
    from .main import QgisOacs
    return QgisOacs(iface)
