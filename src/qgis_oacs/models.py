import abc
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
        # CSAPI specifies SOSA types (sosa:), but some servers send SSN
        # types (ssn:) instead. SSN and SOSA are closely aligned — ssn:System
        # is the parent of all SOSA system types — so we accept both.
        try:
            return {
                "http://www.w3.org/ns/sosa/Sensor": SystemType.SENSOR,
                "http://www.w3.org/ns/sosa/Actuator": SystemType.ACTUATOR,
                "http://www.w3.org/ns/sosa/Platform": SystemType.PLATFORM,
                "http://www.w3.org/ns/sosa/Sampler": SystemType.SAMPLER,
                "http://www.w3.org/ns/sosa/System": SystemType.SYSTEM,
                "http://www.w3.org/ns/ssn/System": SystemType.SYSTEM,
                "sosa:Sensor": SystemType.SENSOR,
                "sosa:Actuator": SystemType.ACTUATOR,
                "sosa:Platform": SystemType.PLATFORM,
                "sosa:Sampler": SystemType.SAMPLER,
                "sosa:System": SystemType.SYSTEM,
                "ssn:System": SystemType.SYSTEM,
            }[value]
        except KeyError as err:
            raise RuntimeError(f"System type {value!r} not supported") from err

    def get_icon_path(self) -> str:
        return {
            self.SENSOR: IconPath.system_type_sensor,
            self.ACTUATOR: IconPath.system_type_actuator,
            self.PLATFORM: IconPath.system_type_platform,
            self.SAMPLER: IconPath.system_type_sampler,
            self.SYSTEM: IconPath.system_type_system,
        }.get(self, IconPath.system_type_system)

    def to_search_query_params(self) -> list[str]:
        return [
                f"sosa:{self.value.capitalize()}",
                f"http://www.w3.org/ns/sosa/{self.value.capitalize()}",
        ]


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
        try:
            return {
                "Equipment": AssetType.EQUIPMENT,
                "Human": AssetType.HUMAN,
                "LivingThing": AssetType.LIVING_THING,
                "Simulation": AssetType.SIMULATION,
                "Process": AssetType.PROCESS,
                "Group": AssetType.GROUP,
                "Other": AssetType.OTHER,
            }[value]
        except KeyError as err:
            raise RuntimeError(f"Asset type {value!r} not supported") from err

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


class ProcedureType(enum.Enum):
    PROCEDURE = "procedure"
    OBSERVING_PROCEDURE = "observing_procedure"
    SAMPLING_PROCEDURE = "sampling_procedure"
    ACTUATING_PROCEDURE = "actuating_procedure"
    SYSTEM = "system"
    SENSOR = "sensor"
    ACTUATOR = "actuator"
    SAMPLER = "sampler"
    PLATFORM = "platform"

    @classmethod
    def from_api_response(cls, value: str) -> "ProcedureType":
        try:
            return {
                "http://www.w3.org/ns/sosa/Procedure": ProcedureType.PROCEDURE,
                "http://www.w3.org/ns/sosa/ObservingProcedure": ProcedureType.OBSERVING_PROCEDURE,

                # this below `procedure/observation` type is not strictly conformant
                # with the CSAPI document. However, some servers return it.
                # Seems likely that it comes from an older version of the standard, so
                # we map it to ObservingProcedure
                "http://www.opengis.net/def/procedure/observation": ProcedureType.OBSERVING_PROCEDURE,

                "http://www.w3.org/ns/sosa/SamplingProcedure": ProcedureType.SAMPLING_PROCEDURE,
                "http://www.w3.org/ns/sosa/ActuatingProcedure": ProcedureType.ACTUATING_PROCEDURE,
                "http://www.w3.org/ns/sosa/System": ProcedureType.SYSTEM,
                "http://www.w3.org/ns/sosa/Sensor": ProcedureType.SENSOR,
                "http://www.w3.org/ns/sosa/Actuator": ProcedureType.ACTUATOR,
                "http://www.w3.org/ns/sosa/Sampler": ProcedureType.SAMPLER,
                "http://www.w3.org/ns/sosa/Platform": ProcedureType.PLATFORM,
                "sosa:Procedure": ProcedureType.PROCEDURE,
                "sosa:ObservingProcedure": ProcedureType.OBSERVING_PROCEDURE,
                "sosa:SamplingProcedure": ProcedureType.SAMPLING_PROCEDURE,
                "sosa:ActuatingProcedure": ProcedureType.ACTUATING_PROCEDURE,
                "sosa:System": ProcedureType.SYSTEM,
                "sosa:Sensor": ProcedureType.SENSOR,
                "sosa:Actuator": ProcedureType.ACTUATOR,
                "sosa:Sampler": ProcedureType.SAMPLER,
                "sosa:Platform": ProcedureType.PLATFORM,
            }[value]
        except KeyError as err:
            raise RuntimeError(f"Procedure type {value!r} not supported") from err

    def get_icon_path(self) -> str:
        return {
            self.PROCEDURE: IconPath.procedure_type_procedure,
            self.OBSERVING_PROCEDURE: IconPath.procedure_type_procedure,
            self.SAMPLING_PROCEDURE: IconPath.procedure_type_procedure,
            self.SYSTEM: IconPath.procedure_type_procedure,
            self.SENSOR: IconPath.procedure_type_procedure,
            self.ACTUATOR: IconPath.procedure_type_procedure,
            self.SAMPLER: IconPath.procedure_type_procedure,
            self.PLATFORM: IconPath.procedure_type_procedure,
        }.get(self, IconPath.procedure_type_procedure)


@dataclasses.dataclass(frozen=True)
class TimePeriod:
    start: dt.datetime | None
    end: dt.datetime | None

    @classmethod
    def from_api_response(cls, value: typing.Sequence[str]) -> "TimePeriod":
        return cls(
            start=(
                parse_raw_rfc3339_datetime(raw_start)
                if (raw_start := value[0]) not in ("..", "now") else None
            ),
            end=(
                parse_raw_rfc3339_datetime(raw_end)
                if (raw_end := value[1]) not in ("..", "now") else None
            ),
        )

    def as_renderable_property(self) -> str:
        return f"{self.start or ''} to {self.end or ''}"


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
        log_message(f"Processing link: {response_content=}")
        return cls(
            href=response_content["href"],
            rel=response_content.get("rel"),
            type=response_content.get("type"),
            title=response_content.get("title"),
        )

    @classmethod
    def from_inline_property(
            cls,
            prop_key: str,
            raw: dict,
            rel_override: str | None = None,
    ) -> "Link":
        """Parse a link from an inline ``prop@link`` API property.

        `rel_override` always sets the rel, overriding whatever the server
        provides.  Use it for inline properties whose resource type is defined
        by the property name, not by the server-supplied rel.  Applied before
        title derivation so the title reflects the correct type,
        e.g. ``systemKind@link`` + ``rel_override="procedure"``
        → ``"systemKind (procedure)"``.
        """
        link = cls.from_api_response(raw)
        if rel_override:
            link = dataclasses.replace(link, rel=rel_override)
        prop_label = prop_key.removesuffix("@link")
        rel_suffix = (link.rel or "").rsplit(":", 1)[-1]
        if prop_label ==  rel_suffix:
            title_prefix = prop_label
        else:
            title_prefix = f"{prop_label} ({rel_suffix})" if rel_suffix else prop_label
        if link.title:
            return dataclasses.replace(link, title=f"{title_prefix} - {link.title}")
        else:
            return dataclasses.replace(link, title=title_prefix)


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
    url_or_relative_path: str
    query: dict[str, str | float | int | bool | list[str | float | int | bool]] | None = None
    headers: dict[str, str] | None = None
    body: bytes | None = None


class OacsFeatureProtocol(typing.Protocol):
    id_: str
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


@dataclasses.dataclass(frozen=True, kw_only=True)
class OacsItem(abc.ABC):
    id_: str
    name: str
    description: str | None = None

    collection_path: typing.ClassVar[str]

    @classmethod
    @abc.abstractmethod
    def from_api_response(cls, response_content: dict) -> "OacsItem": ...

    @abc.abstractmethod
    def get_icon_path(self) -> str: ...

    def get_renderable_properties(self) -> dict[str, str]:
        properties = {
            "Name": self.name,
            "Description": self.description or None
        }
        return {k: v for k, v in properties.items() if v is not None}

    def get_relevant_links(self) -> list[Link]:
        return []

    def get_detail_url(self, base_url: str) -> str:
        return f"{base_url.rstrip('/')}{self.collection_path}/{self.id_}"

    def get_type_label(self) -> str:
        return self.__class__.__name__


@dataclasses.dataclass(frozen=True, kw_only=True)
class OacsFeature(OacsItem, abc.ABC):
    uid: str
    feature_type: str | None = None
    geometry: qgis.core.QgsReferencedGeometry | None = None
    bbox: qgis.core.QgsReferencedRectangle | None = None
    links: list[Link] = dataclasses.field(default_factory=list)
    additional_properties: dict[str, str] | None = None

    def get_renderable_properties(self) -> dict[str, str]:
        properties = {
            **super().get_renderable_properties(),
            "UID": self.uid,
            **({} if self.additional_properties is None
               else {k.capitalize(): str(v) for k, v in self.additional_properties.items()}),
        }
        return {k: v for k, v in properties.items() if v is not None}

    def get_type_label(self) -> str:
        base = (self.feature_type or "").rsplit("/")[-1].rsplit(":")[-1]
        if not base or base.lower() == self.__class__.__name__.lower():
            return self.__class__.__name__
        return f"{base} ({self.__class__.__name__})"

    @staticmethod
    def _parse_api_response(
            response_content: dict,
            disregard_properties: typing.Sequence[str] | None = None
    ) -> dict:
        properties = dict(response_content["properties"])
        return {
            "id_": response_content["id"],
            "uid": properties.pop("uid"),
            "name": properties.pop("name"),
            "feature_type": properties.pop("featureType", None),
            "description": properties.pop("description", None),
            "geometry": qgis.core.QgsReferencedGeometry(
                geometry=qgis.core.QgsJsonUtils.geometryFromGeoJson(json.dumps(raw_geometry)),
                crs=qgis.core.QgsCoordinateReferenceSystem("EPSG:4326"),
            ) if (raw_geometry := response_content.get("geometry")) else None,
            "bbox": qgis.core.QgsReferencedGeometry(
                geometry=qgis.core.QgsJsonUtils.geometryFromGeoJson(json.dumps(raw_bbox)),
                crs=qgis.core.QgsCoordinateReferenceSystem("EPSG:4326"),
            ) if (raw_bbox := response_content.get("bbox")) else None,
            "links": [
                Link.from_api_response(raw_link)
                for raw_link in response_content.get("links", [])
            ],
            "additional_properties": {
                k: str(v) for k, v in properties.items()
                if k not in (disregard_properties or [])
            }
        }


@dataclasses.dataclass(frozen=True, kw_only=True)
class System(OacsFeature):
    collection_path: typing.ClassVar[str] = "/systems"
    feature_type: SystemType | None
    asset_type: AssetType | None
    valid_time: TimePeriod
    system_kind_link: Link

    @classmethod
    def from_api_response(cls, response_content: dict) -> "System":
        common = cls._parse_api_response(
            response_content,
            disregard_properties=("assetType", "validTime", "systemKind@link")
        )
        return cls(
            **{
                **common,
                "feature_type": (
                    SystemType.from_api_response(raw_type)
                    if (raw_type := response_content["properties"].get("featureType", None))
                    else SystemType.SYSTEM
                ),
                "asset_type": (
                    AssetType.from_api_response(raw_asset_type)
                    if (raw_asset_type := response_content["properties"].get("assetType", None))
                    else None
                ),
                "valid_time": (
                    TimePeriod.from_api_response(raw_valid_time)
                    if (raw_valid_time := response_content["properties"].get("validTime", None))
                    else None
                ),
                "system_kind_link": (
                    Link.from_inline_property(
                        "systemKind@link", raw_system_kind,
                        rel_override=LinkRelation.procedure,
                    )
                    if (raw_system_kind := response_content["properties"].get("systemKind@link", None))
                    else None
                ),
            },
        )

    def get_renderable_properties(self) -> dict[str, str]:
        properties = {
            **super().get_renderable_properties(),
            "Feature Type": self.feature_type.name.upper(),
            "Asset Type": self.asset_type.name.upper() if self.asset_type else "Unknown",
            "Valid Time": self.valid_time.as_renderable_property() if self.valid_time else "Unknown",
        }
        return {k: v for k, v in properties.items() if v is not None}

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
        links = [link for link in self.links if link.rel in relevant_link_rels]
        if self.system_kind_link:
            links.append(self.system_kind_link)
        return links

    def get_type_label(self) -> str:
        return (
            f"{self.feature_type.value.capitalize()} (System)" if self.feature_type else "System"
        )

    def get_icon_path(self) -> str:
        return self.feature_type.get_icon_path() if self.feature_type else IconPath.system_type_system


@dataclasses.dataclass(frozen=True, kw_only=True)
class Deployment(OacsFeature):
    collection_path: typing.ClassVar[str] = "/deployments"
    valid_time: TimePeriod
    platform_link: Link | None = None
    deployed_systems_link: list[Link] | None = None

    @classmethod
    def from_api_response(cls, response_content: dict) -> "Deployment":
        common = cls._parse_api_response(
            response_content,
            disregard_properties=("validTime", "platform@link", "deployedSystems@link")
        )
        try:
            deployed_systems_link = [
                Link.from_inline_property(
                    "deployedSystems@link", raw_system_link,
                    rel_override=LinkRelation.system,
                )
                for raw_system_link in response_content["properties"].get("deployedSystems@link", [])
            ]
        except (TypeError, KeyError) as err:
            deployed_systems_link = None
            log_message(
                f"Could not parse deployed systems links: {str(err)}",
                level=qgis.core.Qgis.MessageLevel.Warning
            )
        return cls(
            **common,
            valid_time=(
                TimePeriod.from_api_response(raw_valid_time)
                if (raw_valid_time := response_content["properties"].get("validTime", None))
                else None
            ),
            platform_link=(
                Link.from_inline_property(
                    "platform@link", raw_system_kind,
                    rel_override=LinkRelation.platform,
                )
                if (raw_system_kind := response_content["properties"].get("platform@link", None))
                else None
            ),
            deployed_systems_link=deployed_systems_link
        )

    def get_icon_path(self) -> str:
        return IconPath.deployment

    def get_renderable_properties(self) -> dict[str, str]:
        properties = {
            **super().get_renderable_properties(),
            "Feature Type": (self.feature_type or "deployment").upper(),
            "Valid Time": self.valid_time.as_renderable_property() if self.valid_time else "Unknown",
        }
        return {k: v for k, v in properties.items() if v is not None}

    def get_relevant_links(self) -> list[Link]:
        relevant_link_rels = (
            LinkRelation.platform,
            LinkRelation.deployed_systems,
            LinkRelation.sub_deployments,
            LinkRelation.features_of_interest,
            LinkRelation.sampling_features,
            LinkRelation.data_streams,
            LinkRelation.control_streams,
            OgcLinkRelation.platform,
            OgcLinkRelation.deployed_systems,
            OgcLinkRelation.sub_deployments,
            OgcLinkRelation.features_of_interest,
            OgcLinkRelation.sampling_features,
            OgcLinkRelation.data_streams,
            OgcLinkRelation.control_streams,
        )
        # we look for both `rel=<name>` and `rel=ogc-rel:<name>` because of:
        #
        # https://github.com/opengeospatial/ogcapi-connected-systems/issues/173
        #
        links = [link for link in self.links if link.rel in relevant_link_rels]
        if self.platform_link:
            links.append(self.platform_link)
        if self.deployed_systems_link:
            links.extend(self.deployed_systems_link)
        return links


@dataclasses.dataclass(frozen=True, kw_only=True)
class SamplingFeature(OacsFeature):
    collection_path: typing.ClassVar[str] = "/samplingFeatures"
    valid_time: TimePeriod
    sampled_feature_link: Link

    @classmethod
    def from_api_response(cls, response_content: dict) -> "SamplingFeature":
        common = cls._parse_api_response(
            response_content,
            disregard_properties=("validTime", "sampledFeature@link")
        )
        return cls(
            **common,
            valid_time=(
                TimePeriod.from_api_response(raw_valid_time)
                if (raw_valid_time := response_content["properties"].get("validTime", None))
                else None
            ),
            sampled_feature_link=(
                Link.from_inline_property(
                    "sampledFeature@link", raw_system_kind,
                    rel_override=LinkRelation.sampled_feature,
                )
                if (raw_system_kind := response_content["properties"].pop("sampledFeature@link", None))
                else None
            )
        )

    def get_icon_path(self) -> str:
        return IconPath.sampling_feature

    def get_renderable_properties(self) -> dict[str, str]:
        properties = {
            **super().get_renderable_properties(),
            "Feature Type": (self.feature_type or "sampling_feature").upper(),
            "Valid Time": self.valid_time.as_renderable_property() if self.valid_time else "Unknown",
        }
        return {k: v for k, v in properties.items() if v is not None}

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
        links = [link for link in self.links if link.rel in relevant_link_rels]
        if self.sampled_feature_link:
            links.append(self.sampled_feature_link)
        return links


@dataclasses.dataclass(frozen=True, kw_only=True)
class Procedure(OacsFeature):
    collection_path: typing.ClassVar[str] = "/procedures"
    geometry: None
    feature_type: ProcedureType
    valid_time: TimePeriod | None

    @classmethod
    def from_api_response(cls, response_content: dict) -> "Procedure":
        common = cls._parse_api_response(
            response_content,
            disregard_properties=("featureType", "validTime")
        )
        feature_type = (
            ProcedureType.from_api_response(raw_type)
            if (raw_type := response_content["properties"].get("featureType", None))
            else ProcedureType.PROCEDURE
        )
        return cls(
            **{
                **common,
                "feature_type": feature_type,
                "valid_time": (
                    TimePeriod.from_api_response(raw_valid_time)
                    if (raw_valid_time := response_content["properties"].get("validTime", None))
                    else None
                ),
                "geometry": None
            }
        )

    def get_icon_path(self) -> str:
        return self.feature_type.get_icon_path()

    def get_type_label(self) -> str:
        return self.feature_type.value.replace("_", " ").title()

    def get_renderable_properties(self) -> dict[str, str]:
        properties = {
            **super().get_renderable_properties(),
            "Feature Type": self.feature_type.name.upper(),
            "Valid Time": self.valid_time.as_renderable_property() if self.valid_time else "Unknown",
        }
        return {k: v for k, v in properties.items() if v is not None}

    def get_relevant_links(self) -> list[Link]:
        relevant_link_rels = (
            LinkRelation.implementing_systems,
            OgcLinkRelation.implementing_systems,
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


@dataclasses.dataclass(frozen=True, kw_only=True)
class DataStream(OacsItem):
    collection_path: typing.ClassVar[str] = "/datastreams"
    formats: list[str]
    system_link: Link
    observed_properties: list[DataStreamObservedProperty] | None = None
    phenomenon_time: TimePeriod | None = None
    result_time: TimePeriod | None = None
    result_type: DataStreamResultType | None = None
    live: bool = False
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
    links: list[Link] = dataclasses.field(default_factory=list)

    @classmethod
    def from_api_response(cls, response_content: dict) -> "DataStream":
        return cls(
            id_=response_content["id"],
            name=response_content["name"],
            formats=response_content["formats"],
            system_link=Link.from_api_response(
                {"rel": LinkRelation.system, **response_content["system@link"]}),
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
                Link.from_api_response({"rel": LinkRelation.procedure, **procedure_raw_link})
                if (procedure_raw_link := response_content.get("procedure@link")) else None
            ),
            deployment_link=(
                Link.from_api_response({"rel": LinkRelation.deployment, **deployment_raw_link})
                if (deployment_raw_link := response_content.get("deployment@link")) else None
            ),
            feature_of_interest_link=(
                Link.from_api_response({"rel": LinkRelation.feature_of_interest, **foi_raw_link})
                if (foi_raw_link := response_content.get("featureOfInterest@link")) else None
            ),
            sampling_feature_link=(
                Link.from_api_response({"rel": LinkRelation.sampling_feature, **sampling_feat_raw_link})
                if (sampling_feat_raw_link := response_content.get("samplingFeature@link")) else None
            ),
            schema=None,
            links=[
                Link.from_api_response(raw_link)
                for raw_link in response_content.get("links", [])
            ],
        )

    def get_icon_path(self) -> str:
        return self.datastream_type.get_icon_path() if self.datastream_type else IconPath.datastream

    def get_type_label(self) -> str:
        return self.datastream_type.value.capitalize() if self.datastream_type else "Datastream"

    def get_renderable_properties(self) -> dict[str, str]:
        properties = {
            "Name": self.name,
            "Formats": ", ".join(format_ for format_ in self.formats),
        }
        return {k: v for k, v in properties.items() if v is not None}

    def get_relevant_links(self) -> list[Link]:
        return [
            link for link in (
                self.system_link,
                self.procedure_link,
                self.deployment_link,
                self.sampling_feature_link,
                self.feature_of_interest_link,
            )
            if link is not None
        ]

    def get_observations_link(self) -> "Link | None":
        for link in self.links:
            if link.rel in (LinkRelation.observations, OgcLinkRelation.observations):
                return link
        return None


ItemType = typing.TypeVar("ItemType", bound=OacsItem)


@dataclasses.dataclass(frozen=True)
class OacsFeatureList(typing.Generic[ItemType]):
    item_type: typing.ClassVar[typing.Type[OacsFeature]] = typing.Type[ItemType]
    items: list[ItemType]

    @classmethod
    def from_api_response(cls, response_content: dict) -> "OacsFeatureList[ItemType]":
        items = []
        for raw_feature in response_content.get("features", []):
            try:
                items.append(cls.item_type.from_api_response(raw_feature))
            except (RuntimeError, ValueError) as err:
                log_message(
                    f"Could not parse {raw_feature!r} - {str(err)}",
                    level=qgis.core.Qgis.MessageLevel.Warning
                )
        return cls(items=items)


@dataclasses.dataclass(frozen=True)
class SystemList(OacsFeatureList):
    item_type = System


@dataclasses.dataclass(frozen=True)
class DeploymentList(OacsFeatureList):
    item_type = Deployment


@dataclasses.dataclass(frozen=True)
class SamplingFeatureList(OacsFeatureList):
    item_type = SamplingFeature


@dataclasses.dataclass(frozen=True)
class ProcedureList(OacsFeatureList):
    item_type = Procedure


@dataclasses.dataclass(frozen=True)
class OacsItemList(typing.Generic[ItemType]):
    item_type: typing.ClassVar[typing.Type[OacsItem]] = typing.Type[ItemType]
    items: list[ItemType]

    @classmethod
    def from_api_response(cls, response_content: dict) -> "OacsItemList[ItemType]":
        items = []
        for raw_item in response_content.get("items", []):
            try:
                items.append(cls.item_type.from_api_response(raw_item))
            except ValueError as err:
                log_message(
                    f"Could not parse {raw_item!r} - {str(err)}",
                    level=qgis.core.Qgis.MessageLevel.Warning
                )
        return cls(items=items)


@dataclasses.dataclass(frozen=True)
class DataStreamList(OacsItemList):
    item_type = DataStream


@dataclasses.dataclass(frozen=True)
class Observation:
    """A single observation record.

    ``media_type`` is taken from the Content-Type of the enclosing response so
    callers can branch on format (JSON, OM+JSON, CSV, …) without re-inspecting
    the payload.
    """
    payload: bytes
    media_type: str


@dataclasses.dataclass(frozen=True)
class ObservationList:
    items: list[Observation]
    datastream: "DataStream | None" = None
