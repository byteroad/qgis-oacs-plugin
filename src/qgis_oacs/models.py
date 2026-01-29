import datetime as dt
import dataclasses
import enum
import typing
from urllib.parse import urlparse

import qgis.core

from .utils import log_message


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


@dataclasses.dataclass(frozen=True)
class TimePeriod:
    start: typing.Literal["now"] | dt.datetime
    end: typing.Literal["now"] | dt.datetime

    @classmethod
    def from_api_response(cls, value: typing.Sequence[str]) -> "TimePeriod":
        return cls(
            start=dt.datetime.fromisoformat(
                raw_start) if (raw_start := value[0]) != "now" else raw_start,
            end=dt.datetime.fromisoformat(
                raw_end) if (raw_end := value[1]) != "now" else raw_end,
        )


@dataclasses.dataclass(frozen=True)
class SystemSearchFilterSet:
    system_types: list[str]
    asset_types: list[str]



@dataclasses.dataclass(frozen=True)
class Link:
    href: str
    rel: str | None
    type: str | None
    title: str | None

    @classmethod
    def from_api_response(cls, response_content: dict) -> "Link":
        return cls(**response_content)


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


@dataclasses.dataclass(frozen=True)
class System:
    id_: str
    feature_type: SystemType
    uid: str
    name: str
    asset_type: AssetType | None
    valid_time: TimePeriod
    system_kind_link: Link
    geometry: qgis.core.QgsGeometry | None = None
    bbox: qgis.core.QgsRectangle | None = None
    description: str | None = None
    links: list[Link] = dataclasses.field(default_factory=list)

    @classmethod
    def from_geojson_api_response(cls, response_content: dict) -> "System":
        return cls(
            id_=response_content["id"],
            feature_type=SystemType.from_api_response(
                response_content["properties"]["featureType"]),
            uid=response_content["properties"]["uid"],
            name=response_content["properties"]["name"],
            asset_type=(
                AssetType.from_api_response(raw_asset_type)
                if (raw_asset_type := response_content["properties"].get("assetType"))
                else None
            ),
            valid_time=(
                TimePeriod.from_api_response(raw_valid_time)
                if (raw_valid_time := response_content["properties"].get("validTime"))
                else None
            ),
        )


@dataclasses.dataclass(frozen=True)
class SystemListItem(System): ...


@dataclasses.dataclass(frozen=True)
class SystemList:
    system_items: list[SystemListItem]

    @classmethod
    def from_geojson_api_response(cls, response_content: dict) -> "SystemList":
        ...
