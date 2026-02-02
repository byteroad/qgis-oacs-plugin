import datetime as dt
import dataclasses
import enum
import json
import typing
from urllib.parse import urlparse

import qgis.core

from .constants import (
    IconPath,
    LinkRelation,
    OgcLinkRelation,
)
from .utils import (
    log_message,
    parse_raw_rfc3339_datetime,
)


class SystemType(enum.Enum):
    SENSOR = "sensor"
    ACTUATOR = "actuator"
    PLATFORM = "platform"
    SAMPLER = "sampler"
    SYSTEM = "system"

    @classmethod
    def from_api_response(cls, value: str) -> "SystemType":
        return {
            "http://www.w3.org/ns/sosa/Sensor": SystemType.SENSOR,
            "http://www.w3.org/ns/sosa/Actuator": SystemType.ACTUATOR,
            "http://www.w3.org/ns/sosa/Platform": SystemType.PLATFORM,
            "http://www.w3.org/ns/sosa/Sampler": SystemType.SAMPLER,
            "http://www.w3.org/ns/sosa/System": SystemType.SYSTEM,
            "sosa:Sensor": SystemType.SENSOR,
            "sosa:Actuator": SystemType.ACTUATOR,
            "sosa:Platform": SystemType.PLATFORM,
            "sosa:Sampler": SystemType.SAMPLER,
            "sosa:System": SystemType.SYSTEM,
        }[value]

    def get_icon_path(self) -> str:
        return {
            self.SENSOR: IconPath.system_type_sensor,
            self.ACTUATOR: IconPath.system_type_actuator,
            self.PLATFORM: IconPath.system_type_platform,
            self.SAMPLER: IconPath.system_type_sampler,
            self.SYSTEM: IconPath.system_type_system,
        }.get(self, IconPath.system_type_system)


class AssetType(enum.Enum):
    EQUIPMENT = "equipment"
    HUMAN = "human"
    LIVING_THING = "living_thing"
    SIMULATION = "simulation"
    PROCESS = "process"
    GROUP = "group"
    OTHER = "other"

    @classmethod
    def from_api_response(cls, value: str) -> "AssetType":
        return {
            "Equipment": AssetType.EQUIPMENT,
            "Human": AssetType.HUMAN,
            "LivingThing": AssetType.LIVING_THING,
            "Simulation": AssetType.SIMULATION,
            "Process": AssetType.PROCESS,
            "Group": AssetType.GROUP,
            "Other": AssetType.OTHER,
        }[value]

    def get_icon_path(self) -> str:
        return {
            self.EQUIPMENT: IconPath.system_asset_type_equipment,
            self.HUMAN: IconPath.system_asset_type_human,
            self.LIVING_THING: IconPath.system_asset_type_living_thing,
            self.SIMULATION: IconPath.system_asset_type_simulation,
            self.PROCESS: IconPath.system_asset_type_process,
            self.GROUP: IconPath.system_asset_type_group,
            self.OTHER: IconPath.system_asset_type_other,
        }.get(self, IconPath.system_asset_type_other)


@dataclasses.dataclass(frozen=True)
class TimePeriod:
    start: typing.Literal["now"] | dt.datetime
    end: typing.Literal["now"] | dt.datetime

    @classmethod
    def from_api_response(cls, value: typing.Sequence[str]) -> "TimePeriod":
        return cls(
            start=(
                parse_raw_rfc3339_datetime(raw_start)
                if (raw_start := value[0]) != "now" else raw_start
            ),
            end=(
                parse_raw_rfc3339_datetime(raw_end)
                if (raw_end := value[1]) != "now" else raw_end
            ),
        )


@dataclasses.dataclass(frozen=True)
class SystemSearchFilterSet:
    system_types: list[str]
    asset_types: list[str]



@dataclasses.dataclass(frozen=True)
class Link:
    href: str
    rel: str | None = None
    type: str | None = None
    title: str | None = None

    @classmethod
    def from_api_response(cls, response_content: dict) -> "Link":
        return cls(
            href=response_content["href"],
            rel=response_content.get("rel"),
            type=response_content.get("type"),
            title=response_content.get("title"),
        )


@dataclasses.dataclass(frozen=True)
class ApiLandingPage:
    title: str
    conformance_link: Link
    service_description_link: Link
    service_provider_info: dict | None
    collections_link: Link | None

    systems_link: Link | None
    deployments_link: Link | None
    procedures_link: Link | None
    sampling_features_link: Link | None

    datastreams_link: Link | None
    observations_link: Link | None

    @classmethod
    def from_api_response(cls, response_content: dict) -> "ApiLandingPage":
        links_map = {
            parsed.rel: parsed
            for parsed in [
                Link.from_api_response(link_) for link_ in response_content["links"]
            ]
        }

        return cls(
            title=response_content["title"],
            service_provider_info=response_content.get(
                "serviceProvider", {}
            ).copy(),
            conformance_link=links_map.get("conformance"),
            service_description_link=links_map.get("service-desc"),
            collections_link=links_map.get("collections"),
            systems_link=links_map.get("systems"),
            deployments_link=links_map.get("deployments"),
            procedures_link=links_map.get("procedures"),
            sampling_features_link=links_map.get("samplingFeatures"),
            datastreams_link=links_map.get("datastreams"),
            observations_link=links_map.get("observations"),
        )


@dataclasses.dataclass(frozen=True)
class ConformanceItem:
    conformance_url: str

    @property
    def standard_name(self) -> str | None:
        if parsed := self._parse_conformance_url():
            return parsed[0]
        return None

    @property
    def standard_version(self) -> str | None:
        if parsed := self._parse_conformance_url():
            return parsed[1]
        return None

    @property
    def conformance_class(self) -> str | None:
        if parsed := self._parse_conformance_url():
            return parsed[2]
        return None

    def __str__(self) -> str:
        if all((self.standard_name, self.standard_version, self.conformance_class)):
            return f"{self.standard_name} (v{self.standard_version}) - {self.conformance_class}"
        else:
            return self.conformance_url

    def _parse_conformance_url(self) -> tuple[str, str, str] | None:
        parsed = urlparse(self.conformance_url)
        components = parsed.path.split("/")
        log_message(f"{components=}")
        try:
            standard_name, version, _, conformance_class = components[2:]
            return standard_name, version, conformance_class
        except ValueError:
            return None


@dataclasses.dataclass(frozen=True)
class Conformance:
    conforms_to: list[ConformanceItem]

    @classmethod
    def from_api_response(cls, response_content: dict) -> "Conformance":
        return cls(
            conforms_to=[ConformanceItem(i) for i in response_content["conformsTo"]]
        )


@dataclasses.dataclass(frozen=True)
class ClientSearchParams:
    path: str
    query: dict[str, str | float | int | bool | list[str | float | int | bool]] | None = None
    headers: dict[str, str] | None = None
    body: bytes | None = None


class OacsFeatureProtocol(typing.Protocol):
    name: str
    summary: str
    icon_tooltip: str
    icon_path: str
    collection_search_url_fragment: str
    f_parameter_value: str

    @classmethod
    def from_api_response(cls, response_content: dict) -> "OacsFeatureProtocol": ...

    def get_renderable_properties(self) -> dict[str, str]: ...

    def get_relevant_links(self) -> list[Link]: ...


@dataclasses.dataclass(frozen=True)
class System:
    id_: str
    feature_type: SystemType
    uid: str
    name: str
    asset_type: AssetType | None
    valid_time: TimePeriod
    system_kind_link: Link
    geometry: qgis.core.QgsReferencedGeometry | None = None
    bbox: qgis.core.QgsReferencedRectangle | None = None
    description: str | None = None
    links: list[Link] = dataclasses.field(default_factory=list)
    additional_properties: dict[str, str] | None = None

    collection_search_url_fragment: str = "/systems"
    f_parameter_value = "geojson"

    @property
    def icon_path(self) -> str:
        return self.feature_type.get_icon_path()

    @property
    def icon_tooltip(self) -> str:
        return self.feature_type.value.upper()

    @property
    def summary(self) -> str:
        return self.uid

    @classmethod
    def from_api_response(cls, response_content: dict) -> "System":
        properties = dict(response_content["properties"])
        return cls(
            id_=response_content["id"],
            feature_type=SystemType.from_api_response(properties.pop("featureType")),
            uid=properties.pop("uid"),
            name=properties.pop("name"),
            asset_type=(
                AssetType.from_api_response(raw_asset_type)
                if (raw_asset_type := properties.pop("assetType", None))
                else None
            ),
            valid_time=(
                TimePeriod.from_api_response(raw_valid_time)
                if (raw_valid_time := properties.pop("validTime", None))
                else None
            ),
            system_kind_link=(
                Link.from_api_response(raw_system_kind)
                if (raw_system_kind := properties.pop("systemKind@link", None))
                else None
            ),
            geometry=qgis.core.QgsReferencedGeometry(
                geometry=qgis.core.QgsJsonUtils.geometryFromGeoJson(json.dumps(raw_geometry)),
                crs=qgis.core.QgsCoordinateReferenceSystem("EPSG:4326"),
            ) if (raw_geometry := response_content.get("geometry")) else None,
            bbox=qgis.core.QgsReferencedGeometry(
                geometry=qgis.core.QgsJsonUtils.geometryFromGeoJson(json.dumps(raw_bbox)),
                crs=qgis.core.QgsCoordinateReferenceSystem("EPSG:4326"),
            ) if (raw_bbox := response_content.get("bbox")) else None,
            description=properties.pop("description", None),
            links=[
                Link.from_api_response(raw_link)
                for raw_link in response_content.get("links", [])
            ],
            additional_properties={k: str(v) for k, v in properties.items()}
        )

    def get_renderable_properties(self) -> dict[str, str]:
        return {
            "Name": self.name,
            "UID": self.uid,
            "Feature Type": self.feature_type.name.upper(),
            "Asset Type": self.asset_type.name.upper() if self.asset_type else "Unknown",
            "Valid Time": str(self.valid_time) if self.valid_time else "Unknown",
            **{k.capitalize(): str(v) for k, v in self.additional_properties.items()}
        }

    def get_relevant_links(self) -> list[Link]:
        # we look for both `rel=<name>` and `rel=ogc-rel:<name>` because of:
        #
        # https://github.com/opengeospatial/ogcapi-connected-systems/issues/173
        #
        relevant_link_rels = (
            LinkRelation.sub_systems,
            LinkRelation.sampling_features,
            LinkRelation.deployments,
            LinkRelation.procedures,
            LinkRelation.data_streams,
            LinkRelation.control_streams,
            OgcLinkRelation.sub_systems,
            OgcLinkRelation.sampling_features,
            OgcLinkRelation.deployments,
            OgcLinkRelation.procedures,
            OgcLinkRelation.data_streams,
            OgcLinkRelation.control_streams,

        )
        return [link for link in self.links if link.rel in relevant_link_rels]


@dataclasses.dataclass(frozen=True)
class SamplingFeature:
    id_: str
    feature_type: str
    uid: str
    name: str
    valid_time: TimePeriod
    sampled_feature_link: Link
    geometry: qgis.core.QgsReferencedGeometry | None = None
    bbox: qgis.core.QgsReferencedRectangle | None = None
    description: str | None = None
    links: list[Link] = dataclasses.field(default_factory=list)
    additional_properties: dict[str, str] | None = None

    collection_search_url_fragment: str = "/samplingFeatures"
    f_parameter_value = "geojson"

    @property
    def icon_path(self) -> str:
        return IconPath.sampling_feature

    @property
    def icon_tooltip(self) -> str:
        return self.feature_type

    @property
    def summary(self) -> str:
        return self.uid

    # TODO: Check required and optional properties
    @classmethod
    def from_api_response(cls, response_content: dict) -> "SamplingFeature":
        properties = dict(response_content["properties"])
        return cls(
            id_=response_content["id"],
            feature_type=properties.pop("featureType"),
            uid=properties.pop("uid"),
            name=properties.pop("name"),
            valid_time=(
                TimePeriod.from_api_response(raw_valid_time)
                if (raw_valid_time := properties.pop("validTime", None))
                else None
            ),
            sampled_feature_link=(
                Link.from_api_response(raw_system_kind)
                if (raw_system_kind := properties.pop("systemKind@link", None))
                else None
            ),
            geometry=qgis.core.QgsReferencedGeometry(
                geometry=qgis.core.QgsJsonUtils.geometryFromGeoJson(json.dumps(raw_geometry)),
                crs=qgis.core.QgsCoordinateReferenceSystem("EPSG:4326"),
            ) if (raw_geometry := response_content.get("geometry")) else None,
            bbox=qgis.core.QgsReferencedGeometry(
                geometry=qgis.core.QgsJsonUtils.geometryFromGeoJson(json.dumps(raw_bbox)),
                crs=qgis.core.QgsCoordinateReferenceSystem("EPSG:4326"),
            ) if (raw_bbox := response_content.get("bbox")) else None,
            description=properties.pop("description", None),
            links=[
                Link.from_api_response(raw_link)
                for raw_link in response_content.get("links", [])
            ],
            additional_properties={k: str(v) for k, v in properties.items()}
        )

    def get_renderable_properties(self) -> dict[str, str]:
        return {
            "Name": self.name,
            "UID": self.uid,
            "Feature Type": self.feature_type.upper(),
            "Valid Time": str(self.valid_time) if self.valid_time else "Unknown",
            **{k.capitalize(): str(v) for k, v in self.additional_properties.items()}
        }

    def get_relevant_links(self) -> list[Link]:
        relevant_link_rels = (
            LinkRelation.sampled_feature,
            LinkRelation.parent_system,
            LinkRelation.sample_of,
            LinkRelation.data_streams,
            LinkRelation.control_streams,
            OgcLinkRelation.sampled_feature,
            OgcLinkRelation.parent_system,
            OgcLinkRelation.sample_of,
            OgcLinkRelation.data_streams,
            OgcLinkRelation.control_streams,
        )
        # we look for both `rel=<name>` and `rel=ogc-rel:<name>` because of:
        #
        # https://github.com/opengeospatial/ogcapi-connected-systems/issues/173
        #
        return [link for link in self.links if link.rel in relevant_link_rels]


class DataStreamType(enum.Enum):
    STATUS = "status"
    OBSERVATION = "observation"

    def get_icon_path(self) -> str:
        return {
            self.STATUS: IconPath.datastream_type_status,
            self.OBSERVATION: IconPath.datastream_type_observation,
        }.get(self, IconPath.datastream)


class DataStreamResultType(enum.Enum):
    MEASURE = "measure"
    VECTOR = "vector"
    RECORD = "record"
    COVERAGE = "coverage"
    COMPLEX = "complex"

    def get_icon_path(self) -> str:
        return {
            self.MEASURE: IconPath.system_type_sensor,
            self.VECTOR: IconPath.system_type_sensor,
            self.RECORD: IconPath.system_type_sensor,
            self.COVERAGE: IconPath.system_type_sensor,
            self.COMPLEX: IconPath.system_type_sensor,
        }.get(self, IconPath.system_type_sensor)


@dataclasses.dataclass(frozen=True)
class ObservationSchemaJson:
    parameters_schema: dict  # not modeling this, for now
    result_schema: dict  # not modeling this, for now
    title: str
    format_: str = "application/json"
    result_link_media_type: str | None = None


@dataclasses.dataclass(frozen=True)
class DataStreamObservedProperty:
    definition: str | None = None
    label: str | None = None
    description: str | None = None

    @classmethod
    def from_api_response(cls, response_content: dict) -> "DataStreamObservedProperty":
        return cls(**response_content)


@dataclasses.dataclass(frozen=True)
class DataStream:
    id_: str
    name: str
    formats: list[str]
    system_link: Link
    observed_properties: list[DataStreamObservedProperty] | None = None
    phenomenon_time: TimePeriod | None = None
    result_time: TimePeriod | None = None
    result_type: DataStreamResultType | None = None
    live: bool = False
    description: str | None = None
    validTime: TimePeriod | None = None
    datastream_type: DataStreamType | None = None
    phenomenon_interval: str | None = None
    result_time_interval: str | None = None
    output_name: str | None = None
    procedure_link: Link | None = None
    deployment_link: Link | None = None
    feature_of_interest_link: Link | None = None
    sampling_feature_link: Link | None = None
    schema: ObservationSchemaJson | None = None

    collection_search_url_fragment: str = "/datastreams"
    f_parameter_value = "json"

    @property
    def icon_path(self) -> str:
        return self.datastream_type.get_icon_path() if self.datastream_type else IconPath.datastream

    @property
    def icon_tooltip(self) -> str:
        return self.datastream_type.value.upper() if self.datastream_type else "DATASTREAM"

    @property
    def summary(self) -> str:
        return self.description or ""

    @classmethod
    def from_api_response(cls, response_content: dict) -> "DataStream":
        return cls(
            id_=response_content["id"],
            name=response_content["name"],
            formats=response_content["formats"],
            system_link=Link.from_api_response(response_content["system@link"]),
            observed_properties=[
                DataStreamObservedProperty.from_api_response(prop)
                for prop in raw_observed_props
            ] if (raw_observed_props := response_content.get("observedProperties")) else None,
            phenomenon_time=(
                TimePeriod.from_api_response(phen_time)
                if (phen_time:=response_content.get("phenomenonTime")) else None
            ),
            result_time=(
                TimePeriod.from_api_response(result_time)
                if (result_time:=response_content.get("resultTime")) else None
            ),
            result_type=DataStreamResultType(response_content["resultType"]),
            live=response_content.get("live", False),
            description=response_content.get("description"),
            datastream_type=DataStreamType(ds_type) if (ds_type :=response_content.get("type")) else None,
            phenomenon_interval=response_content.get("phenomenonInterval"),
            result_time_interval=response_content.get("resultTimeInterval"),
            output_name=response_content.get("outputName"),
            procedure_link=(
                Link.from_api_response(procedure_raw_link)
                if (procedure_raw_link := response_content.get("procedure@link")) else None
            ),
            deployment_link=(
                Link.from_api_response(deployment_raw_link)
                if (deployment_raw_link := response_content.get("deployment@link")) else None
            ),
            feature_of_interest_link=(
                Link.from_api_response(foi_raw_link)
                if (foi_raw_link := response_content.get("featureOfInterest@link")) else None
            ),
            sampling_feature_link=(
                Link.from_api_response(sampling_feat_raw_link)
                if (sampling_feat_raw_link := response_content.get("samplingFeature@link")) else None
            ),
            schema=None,
        )

    def get_renderable_properties(self) -> dict[str, str]:
        return {
            "Name": self.name,
            "Formats": ", ".join(format_ for format_ in self.formats),
        }

    def get_relevant_links(self) -> list[Link]:
        return []


@dataclasses.dataclass(frozen=True)
class SystemList:
    items: list[System]

    @classmethod
    def from_api_response(cls, response_content: dict) -> "SystemList":
        items = []
        for raw_system in response_content.get("features", []):
            try:
                items.append(System.from_api_response(raw_system))
            except ValueError as err:
                log_message(
                    f"Could not parse {raw_system!r} - {str(err)}",
                    level=qgis.core.Qgis.MessageLevel.Warning
                )
        return cls(items=items)


@dataclasses.dataclass(frozen=True)
class SamplingFeatureList:
    items: list[SamplingFeature]

    @classmethod
    def from_api_response(cls, response_content: dict) -> "SamplingFeatureList":
        items = []
        for raw in response_content.get("features", []):
            try:
                items.append(SamplingFeature.from_api_response(raw))
            except ValueError as err:
                log_message(f"Could not parse {raw!r} - {str(err)}")
        return cls(items=items)


@dataclasses.dataclass(frozen=True)
class DataStreamList:
    items: list[DataStream]
    links: list[Link] | None = None

    @classmethod
    def from_api_response(cls, response_content: dict) -> "DataStreamList":
        items = []
        for raw_item in response_content["items"]:
            try:
                items.append(DataStream.from_api_response(raw_item))
            except ValueError as err:
                log_message(f"Could not parse {raw_item!r} - {str(err)}")
        return cls(items=items)
