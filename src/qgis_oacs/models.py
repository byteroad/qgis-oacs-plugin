from urllib.parse import urlparse
import dataclasses

from .settings import DataSourceConnectionSettings
from .utils import log_message


@dataclasses.dataclass(frozen=True)
class SystemSearchFilterSet:
    system_types: list[str]
    asset_types: list[str]



@dataclasses.dataclass(frozen=True)
class Link:
    rel: str
    title: str
    href: str
    type: str

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


@dataclasses.dataclass
class RuntimeConnection:
    connection_settings: DataSourceConnectionSettings
    landing_page: ApiLandingPage | None = None
    conformance: Conformance | None = None