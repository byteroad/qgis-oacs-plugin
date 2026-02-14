import abc

from qgis.PyQt import QtWidgets


class AbstractQWidgetMeta(type(QtWidgets.QWidget), abc.ABCMeta):
    """Metaclass that inherits from both QWidget and ABCMeta.

    This exists so that we can create abstract base classes that are also QWidgets.
    In order for this to be possible Python requires that there is a common base abc.
    """
    pass
