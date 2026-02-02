import dataclasses
import enum
import functools
import json
import typing
import uuid

import qgis.core
from qgis.PyQt import (
    QtCore,
    QtNetwork,
)

from . import models
from . import settings
from .utils import log_message


class RequestType(enum.Enum):
    SYSTEM_LIST = "system-list"
    SYSTEM_ITEM = "system-item"
    SAMPLING_FEATURE_LIST = "sampling-feature-list"
    SAMPLING_FEATURE_ITEM = "sampling-feature-item"
    DATASTREAM_LIST = "datastream-list"
    DATASTREAM_ITEM = "datastream-item"


@dataclasses.dataclass(frozen=True)
class OacsRequestMetadata:
    request_type: RequestType
    request_id: uuid.UUID = dataclasses.field(default_factory=uuid.uuid4)


class OacsClient(QtCore.QObject):
    request_started = QtCore.pyqtSignal(OacsRequestMetadata)
    request_ended = QtCore.pyqtSignal(OacsRequestMetadata)
    request_failed = QtCore.pyqtSignal(OacsRequestMetadata, str)
    system_list_fetched = QtCore.pyqtSignal(models.SystemList)
    system_item_fetched = QtCore.pyqtSignal(models.System)
    sampling_feature_list_fetched = QtCore.pyqtSignal(models.SamplingFeatureList)
    sampling_feature_item_fetched = QtCore.pyqtSignal(models.SamplingFeature)
    datastream_list_fetched = QtCore.pyqtSignal(models.DataStreamList)
    datastream_item_fetched = QtCore.pyqtSignal(models.DataStream)

    def initiate_system_list_search(
            self,
            connection: settings.DataSourceConnectionSettings,
            q_filter: str | None = None
    ) -> OacsRequestMetadata:
        query = {
            "f": "geojson" if connection.use_f_query_param else None,
            "q": q_filter,
        }
        meta = OacsRequestMetadata(request_type=RequestType.SYSTEM_LIST)
        self.dispatch_network_request(
            search_params=models.ClientSearchParams(
                "/systems",
                query={k: v for k, v in query.items() if v} or None,
                headers={"Accept": "application/geo+json"},
            ),
            connection=connection,
            task_metadata=meta,
            response_handler=functools.partial(
                self.handle_network_response,
                parser=models.SystemList.from_api_response,
                to_emit=self.system_list_fetched,
            )
        )
        self.request_started.emit(meta)
        return meta

    def initiate_sampling_feature_list_search(
            self,
            connection: settings.DataSourceConnectionSettings
    ) -> OacsRequestMetadata:
        query = {
            "f": "geojson" if connection.use_f_query_param else None
        }
        meta = OacsRequestMetadata(request_type=RequestType.SAMPLING_FEATURE_LIST)
        self.dispatch_network_request(
            search_params=models.ClientSearchParams(
                "/samplingFeatures",
                query={k: v for k, v in query.items()} if query else None,
                headers={"Accept": "application/geo+json"},
            ),
            connection=connection,
            task_metadata=meta,
            response_handler=functools.partial(
                self.handle_network_response,
                parser=models.SamplingFeatureList.from_api_response,
                to_emit=self.sampling_feature_list_fetched
            )
        )
        self.request_started.emit(meta)
        return meta

    def initiate_datastream_list_search(
            self,
            connection: settings.DataSourceConnectionSettings
    ) -> OacsRequestMetadata:
        query = {
            "f": "json" if connection.use_f_query_param else None
        }
        meta = OacsRequestMetadata(request_type=RequestType.DATASTREAM_LIST)
        self.dispatch_network_request(
            search_params=models.ClientSearchParams(
                "/datastreams",
                query={k: v for k, v in query.items()} if query else None,
                headers={"Accept": "application/json"},
            ),
            connection=connection,
            task_metadata=meta,
            response_handler=functools.partial(
                self.handle_network_response,
                parser=models.DataStreamList.from_api_response,
                to_emit=self.datastream_list_fetched
            )
        )
        self.request_started.emit(meta)
        return meta

    def initiate_system_item_fetch(
            self,
            system_id: str,
            connection: settings.DataSourceConnectionSettings
    ) -> OacsRequestMetadata:
        query = {
            "f": "geojson" if connection.use_f_query_param else None
        }
        meta = OacsRequestMetadata(request_type=RequestType.SYSTEM_ITEM)
        self.dispatch_network_request(
            search_params=models.ClientSearchParams(
                f"/systems/{system_id}",
                query={k: v for k, v in query.items()} if query else None,
                headers={"Accept": "application/geo+json"},
            ),
            connection=connection,
            task_metadata=meta,
            response_handler=functools.partial(
                self.handle_network_response,
                parser=models.System.from_api_response,
                to_emit=self.system_item_fetched
            )
        )
        self.request_started.emit(meta)
        return meta

    def initiate_sampling_feature_item_fetch(
            self,
            sampling_feature_id: str,
            connection: settings.DataSourceConnectionSettings
    ) -> OacsRequestMetadata:
        query = {
            "f": "geojson" if connection.use_f_query_param else None
        }
        meta = OacsRequestMetadata(request_type=RequestType.SAMPLING_FEATURE_ITEM)
        self.dispatch_network_request(
            search_params=models.ClientSearchParams(
                f"/samplingFeatures/{sampling_feature_id}",
                query={k: v for k, v in query.items()} if query else None,
                headers={"Accept": "application/geo+json"},
            ),
            connection=connection,
            task_metadata=meta,
            response_handler=functools.partial(
                self.handle_network_response,
                parser=models.SamplingFeature.from_api_response,
                to_emit=self.sampling_feature_item_fetched
            )
        )
        self.request_started.emit(meta)
        return meta

    def initiate_datastream_item_fetch(
            self,
            datastream_id: str,
            connection: settings.DataSourceConnectionSettings
    ) -> OacsRequestMetadata:
        query = {
            "f": "json" if connection.use_f_query_param else None
        }
        meta = OacsRequestMetadata(request_type=RequestType.DATASTREAM_ITEM)
        self.dispatch_network_request(
            search_params=models.ClientSearchParams(
                f"/datastreams/{datastream_id}",
                query={k: v for k, v in query.items()} if query else None,
                headers={"Accept": "application/json"},
            ),
            connection=connection,
            task_metadata=meta,
            response_handler=functools.partial(
                self.handle_network_response,
                parser=models.DataStream.from_api_response,
                to_emit=self.datastream_item_fetched
            )
        )
        self.request_started.emit(meta)
        return meta

    def handle_network_response(
            self,
            response: qgis.core.QgsNetworkContentFetcherTask,
            parser: typing.Callable,
            to_emit: QtCore.pyqtSignal,
            target_task_metadata: OacsRequestMetadata
    ) -> None:
        reply: QtNetwork.QNetworkReply | None = response.reply()
        if not reply:
            return None
        if not (task_metadata := getattr(response, "oacs_metadata", None)):
            return None
        elif task_metadata.request_id != target_task_metadata.request_id:
            return None
        try:
            if (request_error := reply.error()) != QtNetwork.QNetworkReply.NetworkError.NoError:
                error_message = reply.errorString()
                self.request_failed.emit(task_metadata, error_message)
                log_message(f"Connection error {error_message} - (code: {request_error})")
            else:
                response_payload = response.contentAsString()
                parsed_payload = parser(json.loads(response_payload))
                to_emit.emit(parsed_payload)
        except json.JSONDecodeError as err:
            error_message = f"Could not parse response to JSON: {str(err)}"
            log_message(error_message)
            self.request_failed.emit(task_metadata, error_message)
        except Exception as err:
            error_message = f"Unexpected error: {str(err)}"
            log_message(error_message)
            import traceback
            log_message(traceback.format_exc())
            self.request_failed.emit(task_metadata, error_message)
        finally:
            self.request_ended.emit(task_metadata)

    @typing.overload
    def dispatch_network_request(
            self,
            search_params: models.ClientSearchParams,
            connection: settings.DataSourceConnectionSettings,
            task_metadata: OacsRequestMetadata,
            response_handler: typing.Callable[[qgis.core.QgsNetworkContentFetcherTask], None]
    ) -> None: ...

    @typing.overload
    def dispatch_network_request(
            self,
            search_params: str,
            connection: settings.DataSourceConnectionSettings,
            task_metadata: OacsRequestMetadata,
            response_handler: typing.Callable[[qgis.core.QgsNetworkContentFetcherTask], None]
    ) -> None: ...

    def dispatch_network_request(
            self,
            search_params: models.ClientSearchParams,
            connection: settings.DataSourceConnectionSettings,
            task_metadata: OacsRequestMetadata,
            response_handler: typing.Callable[
                [qgis.core.QgsNetworkContentFetcherTask], None]
    ) -> None:
        if isinstance(search_params, str):
            request_url = QtCore.QUrl(search_params)
            request = QtNetwork.QNetworkRequest(request_url)
            request.setRawHeader(b"Accept", b"application/json")
        else:
            request_query = QtCore.QUrlQuery()
            query_items = {
                **(search_params.query or {})
            }
            if len(query_items) > 0:
                request_query.setQueryItems(list(query_items.items()))
            request_url = QtCore.QUrl(f"{connection.base_url}{search_params.path}")
            if not request_query.isEmpty():
                request_url.setQuery(request_query)
            request = QtNetwork.QNetworkRequest(request_url)
            for header_name, header_value in search_params.headers.items():
                request.setRawHeader(
                    header_name.capitalize().encode(),
                    header_value.encode()
                )
        api_request_task = qgis.core.QgsNetworkContentFetcherTask(
            request=request,
            authcfg=connection.auth_config,
            description=f"test-oacs-plugin-search"
        )
        api_request_task.oacs_metadata = task_metadata
        qgis.core.QgsApplication.taskManager().addTask(api_request_task)
        handler = functools.partial(
            response_handler,
            api_request_task,
            target_task_metadata=task_metadata
        )
        api_request_task.fetched.connect(handler)
