import dataclasses
import typing

import qgis.core
from qgis.PyQt import (
    QtCore,
    QtNetwork,
)

from . import models


# - do we need to get the landing page at all?
# - the standard mandates that a `/systems` path op must exist, so we can go there directly


class CollectionListNetworkRequestTask(qgis.core.QgsTask):
    authcfg_id: str | None
    network_access_manager: qgis.core.QgsNetworkAccessManager
    request_timeout_seconds: int

    def __init__(
            self,
            network_request_timeout: int,
            authcfg_id: str | None = None,
            description: str = "oacs-plugin-network-request-task",
    ):
        super().__init__(description)
        self.authcfg_id = authcfg_id
        self.network_request_timeout = network_request_timeout
        self.request = request
        self.response_contents = None
        self.network_access_manager = qgis.core.QgsNetworkAccessManager.instance()
        self.network_access_manager.setTimeout(self.network_request_timeout)
        self.network_access_manager.requestTimedOut.connect(
            self._handle_request_timed_out
        )
        self.network_access_manager.finished.connect(self._handle_request_finished)

    def run(self) -> bool:
        raise NotImplementedError
